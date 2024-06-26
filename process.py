"""
Main processing steps
By: quanvh11

"""
import os
import cv2
from utils import get_filename
from utils.image import plot_image_with_boxes, get_best_ocr_result, image_preprocessing
from utils.text import (table_reconstruction, get_insurance_balance, clean_numeric_text, human_number,
                        clean_table, image_quality_map)
from utils.pdf import pdf_page_to_image

def get_results_image(image_path, requested_date, save_image=True):

    image_raw = cv2.imread(image_path) 

    # Apply preprocessing to remove stamp and clear noises
    image = image_preprocessing( image_raw )

    # TEXT EXTRACTION
    text_boxes, prob, image_ = get_best_ocr_result(image, threshold=0.5, angles=[-90,90,180])
    print("Extracted text from image: ", prob)

    # Construct a table
    table, metadata_inds, additional_info = table_reconstruction(text_boxes)
    date_ind, interest_ind, principal_ind = metadata_inds
    print("Payment schedule: number of row: ", table.shape)

    # Clean values to best candidates of dates, numbers (money amount)
    table = clean_table(table)

    # CALCULATING INSURANCE BALANCE
    got_inf = get_insurance_balance(table, requested_date)
    print("Number of row that matched requested date: ", got_inf.shape)

    if len(got_inf)>0:
        prev_principal = got_inf["prev_principal"].values[0]
        interest = got_inf["interest"].values[0]
        topay_date = got_inf["date"].values[0]

        # get coordinates
        interest_coordinates, prev_principal_coordinates, date_coordinates = None, None, None
        if type(got_inf["metadata"].values[0]) == list:
            interest_coordinates = got_inf["metadata"].values[0][interest_ind][0]
        if type(got_inf["prev_metadata"].values[0]) == list:
            prev_principal_coordinates = got_inf["prev_metadata"].values[0][principal_ind][0]
        if type(got_inf["metadata"].values[0]) == list:
            date_coordinates = got_inf["metadata"].values[0][date_ind][0]

        prev_principal = clean_numeric_text(prev_principal)
        interest = clean_numeric_text(interest)
        insurance_deposit = int(prev_principal) + int(interest)

        msg = f"""Insurance event date: {requested_date}; Insurance deposit = previous_principal + interest = {human_number(prev_principal)} + {human_number(interest)} = {human_number(insurance_deposit)}"""
        if save_image:
            print("Saving image")
            plot_image_with_boxes(image=image_,
                            boxes=[interest_coordinates, prev_principal_coordinates, date_coordinates],
                            texts=[ "This period interest: " + human_number(interest),
                                    "Previous period principal: "+human_number(prev_principal),
                                    "This period: "+ topay_date],
                            title=msg, 
                            is_save=save_image, 
                            is_plot=False)
        out = {
            "event_date": requested_date,
            "insurance": {
                "interest": interest,
                "principal": prev_principal,
                "insurance_balance": insurance_deposit
            },
            "image_quality": {"score": prob, "level": image_quality_map(prob)},
            "detail_inf": additional_info
        }
    else:
        print("No row detected")
        if save_image:
            plot_image_with_boxes(image_path=image_,
                              boxes=[],
                            title="NGÀY PHÁT SINH SỰ KIỆN BẢO HIỂM KHÔNG NHẬN DIỆN ĐƯỢC", 
                            is_save=save_image, 
                            is_plot=False)
        out = None
    return out

def get_results_pdf(pdf_path, requested_date, save_image=True, temp_path="temp", inplace_img=False, page_limit=10):
    """
    Process with input is a multi-page pdf payment schedule
    inplace_img: bool: replace a image already in temp_path?
    """
    for page in range(1, page_limit, 1):
        # Save image to temp
        pdf_file_name = get_filename(pdf_path)
        output_img_path = os.path.join(temp_path, pdf_file_name+"_"+str(page)+".png")

        is_saved=True
        if (not os.path.isfile(output_img_path)) or inplace_img:
            # only replace image if inplace_img=True
            is_saved = pdf_page_to_image(pdf_path, page, output_img_path, zoom=2)

        # If the page <= pagecount => image is saved => perform OCR extracting
        if is_saved:
            try:
                results = get_results_image(output_img_path, requested_date, save_image)

                # If extracted numbers => return the numbers
                # Otherwise, try with next page
                if results is not None:    
                    return results
            except:
                print(f"Cannot extract info from {pdf_file_name} page {page}")
                pass
