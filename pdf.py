"""
Handling with pdf files
By: quanvh11
"""

# convert pdf pages to images
import fitz  # PyMuPDF
from PIL import Image

def pdf_page_to_image(pdf_path, page_number, output_image_path, zoom=2):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    
    # Ensure the page number is within the valid range
    if page_number < 1 or page_number > pdf_document.page_count:
        return 0
    
    # Get the specified page
    page = pdf_document.load_page(page_number - 1)  # Page numbers are 0-indexed in PyMuPDF
    
    # Set the zoom level for better quality (higher DPI)
    zoom_x = zoom    # horizontal zoom
    zoom_y = zoom    # vertical zoom
    mat = fitz.Matrix(zoom_x, zoom_y)  # transformation matrix for zooming
    
    # Render the page to a pixmap (image) with the specified matrix
    pix = page.get_pixmap(matrix=mat)
    
    # Convert the pixmap to a PIL Image
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # Save the image
    image.save(output_image_path)

    print(f"Page {page_number} saved as {output_image_path} with zoom level {zoom}")
    return 1

