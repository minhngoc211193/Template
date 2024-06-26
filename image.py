"""
IMAGE PROCESSING AND OCR PERFORMING
By: quanvh11
"""

import os
import cv2
import numpy as np
from easyocr import Reader
from skimage.color import rgb2gray
from skimage.transform import rotate
from deskew import determine_skew

import pytesseract
from PIL import Image

def plot_image_with_boxes(boxes, image=None, image_path=None, texts=None, title=None, is_save=False, is_plot=False):
    '''Visualized an image with boxes and texts
    Args:
        image_path: str
        boxes: list of co-ordinators
    '''
    if image is None:
        image = cv2.imread(image_path)

    for ind, box in enumerate(boxes):
        try:
            (x1, y1), (x2, y2) = box[0], box[2]

            # Draw bounding box (adjusted for OpenCV convention)
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 1)

            if texts is not None:
                text = texts[ind]    
                cv2.putText(image, text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 225), 1)
        except:
            pass
    
    # Put title
    if title is not None:
        cv2.putText(image, title, (50, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 225), 1)
    
    if is_save:
        output_path = "static\output_img.png"
        if os.path.isfile(output_path):
            os.remove(output_path)
        cv2.imwrite(output_path, image)
        print("Output image has been saved")

    # Display the image with bounding boxes and text labels
    if is_plot:
        cv2.imshow("Image with Text Detection", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

def get_orientation_PSM(img_path):
    # Load your image
    image = Image.open(img_path)

    # Set the PSM to detect orientation (PSM 0 is for orientation and script detection)
    custom_config = r'--psm 0'

    # To get the orientation information
    orientation_data = pytesseract.image_to_osd(image, config=custom_config)

    print(orientation_data)

def get_orientation_textbox(coodinators):
    (x0, y0), (x1, y1) = coodinators[0], coodinators[1]
    (x2, y2), (x3, y3) = coodinators[0], coodinators[1]
    return (y1-y0)/(x1-x0)#, (y2-y3)/(x2-x3)

def get_orient_cv2(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply threshold to get a binary image
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Assume the largest contour is the page
    contour = max(contours, key=cv2.contourArea)

    # Get the minimum area rectangle
    rect = cv2.minAreaRect(contour)

    # Get the angle
    angle = rect[-1]

    # Adjust the angle
    if angle < -45:
        angle = 90 + angle
    return angle

def deskew(image):
    "Deskew an image (read from cv2)"
    # Read image using cv2
    # image = cv2.imread(_img)
    
    # Convert from BGR to RGB since cv2.imread reads in BGR format
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Convert to grayscale
    grayscale = rgb2gray(image)
    
    # Determine the skew angle
    angle = determine_skew(grayscale)
    print("The skew angle is: ", angle)
    
    # Rotate the image to deskew
    if angle is not None:
        rotated = rotate(image, angle, resize=True)
        
        # Convert rotated image to uint8
        # rotated = img_as_ubyte(rotated)
        rotated = (rotated * 255).astype(np.uint8)
    else:
        rotated = image
    
    return rotated

def get_ocr_text_boxes(image_path):
    reader = Reader(["en", "vi"], model_storage_directory="model/", download_enabled=False)
    results = reader.readtext(image_path, width_ths=0.7)
    return results

def get_ocr_at_angle(image, angle=0):
    image_ = np.copy(image)
    rotated = rotate(image_, angle, resize=True)
    rotated = (rotated * 255).astype(np.uint8)
    # Deskew
    deskewed_image = deskew(rotated)
    # TEXT EXTRACTION
    text_boxes = get_ocr_text_boxes(deskewed_image)
    prob = np.mean([i[-1] for i in text_boxes])

    return text_boxes, prob, rotated
    
def get_best_ocr_result(image, threshold=0.5, angles=[-90, 90, 180]):
    # Perform OCR at angle 0 first
    text_boxes_0, prob_0, image_ = get_ocr_at_angle(image, angle=0)
    
    # If the probability at angle 0 is satisfactory, return the results
    if prob_0 >= threshold:
        return text_boxes_0, prob_0, image_
    
    # Check other angles
    for angle in angles:
        text_boxes, prob, image_ = get_ocr_at_angle(image, angle)
        if prob >= threshold:
            print("OCR best angle: ", angle )
            return text_boxes, prob, image_
    
    # If none of the other angles are satisfactory, return the results of angle 0
    print("OCR best angle: ", 0 )
    return text_boxes_0, prob_0, image_

def increase_sharpness(image):
    kernel = np.array([[0, -1, 0],
                   [-1, 5, -1],
                   [0, -1, 0]])
    return cv2.filter2D(image, -1, kernel)

def otsu_thresholding(image):
  """
  Enhances an image for OCR by converting to grayscale, applying thresholding,
  and removing noise.
  """
  # Convert to grayscale
  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

  # Apply Otsu's thresholding to convert to black and white
  thresh, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

  return bw

def remove_red_stamp(image, hue_threshold=10, sat_threshold=120, val_threshold=70):
    # Convert the image from BGR to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the lower and upper bounds of the color in HSV
    # For example, let's filter the color red
    lower_bound = np.array([0, sat_threshold, val_threshold])
    upper_bound = np.array([hue_threshold, 255, 255])

    # Create a mask using the color range
    mask = cv2.inRange(hsv_image, lower_bound, upper_bound)

    # Optionally, you can also filter another range for the same color (e.g., for red)
    # This is because red wraps around the hue value (0 and 180 are both red in HSV)
    lower_bound2 = np.array([180-hue_threshold, sat_threshold, val_threshold])
    upper_bound2 = np.array([180, 255, 255])
    mask2 = cv2.inRange(hsv_image, lower_bound2, upper_bound2)

    # Combine the two masks
    full_mask = cv2.bitwise_or(mask, mask2)

    # Create a copy of the original image to modify
    result = image.copy()

    result[full_mask > 0] = [255, 255, 255]
    return result

def image_preprocessing(image):

    # Remove stamp
    '''
    Tham khảo các ngưỡng: hue_threshold=30, sat_threshold=10
        => mất toàn bộ dấu đỏ, nhưng một số chữ đen cũng sẽ bị mất
    '''
    image_ = remove_red_stamp(image, hue_threshold=30, sat_threshold=40, val_threshold=70)

    # Increase sharpness
    # image_ = increase_sharpness(image_)

    # Convert to gray and remove noise
    # image_ = otsu_thresholding(image_)

    return image #image_