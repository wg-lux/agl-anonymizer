import cv2
from east_text_detection import east_text_detection
#from for_blurring.censor import blur_function
from PIL import Image
from ocr_pipeline_manager import process_images_with_OCR_and_NER
from names_generator import gender_and_handle_names
import uuid
import os
import fitz
import tempfile
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import uuid


def convert_pdf_page_to_image(page):
    """
    Convert a single PDF page into an image using PyMuPDF and then encode it using OpenCV.
    """
    pix = page.get_pixmap()
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    return img

def merge_pdfs(pdf_paths, output_path):
    """Merge multiple PDFs into a single PDF."""
    pdf_writer = PdfWriter()
    for path in pdf_paths:
        pdf_reader = PdfReader(path)
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
    with open(output_path, 'wb') as out:
        pdf_writer.write(out)

def convert_image_to_pdf(image_path, pdf_path):
    """Converts an image to a PDF."""
    c = canvas.Canvas(pdf_path, pagesize=letter)
    img = Image.open(image_path)
    c.drawImage(image_path, 0, 0, width=img.width, height=img.height)
    c.showPage()
    c.save()
    

import cv2
import numpy as np
import os
import uuid

def reassemble_image(modified_images_map, output_dir, id):
    curr_image_path = None
    original_image = None

    for (box, original_image_path), modified_image_path in modified_images_map.items():
        if curr_image_path is None or original_image_path != curr_image_path:
            original_image = cv2.imread(original_image_path)
            curr_image_path = original_image_path

            if original_image is None:
                print(f"Warning: Could not load original image from {original_image_path}. Skipping this image.")
                continue

        modified_image = cv2.imread(modified_image_path)
        if modified_image is None:
            print(f"Warning: Could not load modified image from {modified_image_path}. Skipping this modification.")
            continue

        (startX, startY, endX, endY) = box
        bbox_width = endX - startX
        bbox_height = endY - startY

        scale_width = bbox_width / modified_image.shape[1]
        scale_height = bbox_height / modified_image.shape[0]
        scale_factor = min(scale_width, scale_height)

        resized_width = int(modified_image.shape[1] * scale_factor)
        resized_height = int(modified_image.shape[0] * scale_factor)
        resized_modified_image = cv2.resize(modified_image, (resized_width, resized_height))

        x_offset = startX + (bbox_width - resized_width) // 2
        y_offset = startY + (bbox_height - resized_height) // 2

        # Calculate the effective overlay dimensions
        overlay_height = min(original_image.shape[0] - y_offset, resized_height)
        overlay_width = min(original_image.shape[1] - x_offset, resized_width)

        # Overlay the resized modified image onto the original image within the effective dimensions
        original_image[y_offset:y_offset + overlay_height, x_offset:x_offset + overlay_width] = resized_modified_image[:overlay_height, :overlay_width]

    if original_image is not None:
        final_image_path = os.path.join(output_dir, f"reassembled_image_{id}_{uuid.uuid4()}.jpg")
        cv2.imwrite(final_image_path, original_image)
        print(f"Reassembled image saved to: {final_image_path}")
    else:
        print("No modifications were made, or no original image was successfully loaded.")




def process_image(image_path, east_path, min_confidence, width, height, results_dir, temp_dir):
    print(f"Processing file: {image_path}")
    unique_id = str(uuid.uuid4())[:8]
 
# searching the pattern
    id = f"image_{unique_id}"
    # Load the image using OpenCV
    original_image = cv2.imread(image_path)
    if original_image is None:
        raise ValueError(f"Could not load image at {image_path}")
    # Image processing logic here
    modified_images_map, boxes = process_images_with_OCR_and_NER(image_path, east_path, min_confidence, width, height)
    print("Images processed")
    # Print out the modified images map
    print("Modified Images Map:")
    reassembled_image_path=image_path
    reassembled_image_path = reassemble_image(modified_images_map, results_dir, id)

    return reassembled_image_path

def get_image_paths(image_or_pdf_path, temp_dir):
    image_paths = []

    if image_or_pdf_path.endswith('.pdf'):
        # Open the PDF
        doc = fitz.open(image_or_pdf_path)

        for i, page in enumerate(doc):
            img = convert_pdf_page_to_image(page)
            # Save the image to a temporary file using OpenCV
            temp_img_path = os.path.join(temp_dir, f"page_{i}.png")
            cv2.imwrite(temp_img_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            image_paths.append(temp_img_path)
    else:
        # If it's a single image, just append the original path
        image_paths.append(image_or_pdf_path)

    return image_paths

def main(image_or_pdf_path, east_path='frozen_east_text_detection.pb', min_confidence=0.5, width=320, height=320):
    results_dir = os.path.join(os.path.dirname(image_or_pdf_path), "results")
    os.makedirs(results_dir, exist_ok=True)
    temp_dir = tempfile.mkdtemp()
    image_paths = get_image_paths(image_or_pdf_path, temp_dir)
    
    processed_pdf_paths = []  # This will store paths of PDFs (either directly processed or converted from images)
    try:
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = [executor.submit(process_image, img_path, east_path, min_confidence, width, height, results_dir, temp_dir) for img_path in image_paths]
            for future in as_completed(futures):
                processed_image_path = future.result()
                # Convert processed images to PDF if original input was a PDF
                if image_or_pdf_path.endswith('.pdf'):
                    temp_pdf_path = os.path.join(temp_dir, f"processed_{uuid.uuid4()}.pdf")
                    convert_image_to_pdf(processed_image_path, temp_pdf_path)
                    processed_pdf_paths.append(temp_pdf_path)
                else:
                    processed_pdf_paths.append(processed_image_path)
        
        # Merge processed PDFs into a final document if original was a PDF
        if image_or_pdf_path.endswith('.pdf'):
            final_pdf_path = os.path.join(results_dir, "final_document.pdf")
            merge_pdfs(processed_pdf_paths, final_pdf_path)
            output_path = final_pdf_path
        else:
            # If the original was not a PDF, processed paths are directly the images
            output_path = processed_pdf_paths
        
    finally:
        # Cleanup
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)
    
    return output_path
    
def crop_and_save(image_path, boxes):
    cropped_image_paths = []
    image_texts = {}  # Dictionary to store image paths and their corresponding texts with unique IDs

    with Image.open(image_path) as img:
        for idx, (startX, startY, endX, endY) in enumerate(boxes):
            # Crop the image using the box coordinates
            cropped_img = img.crop((startX, startY, endX, endY))
            
            # Extract the file extension and create a new file name with it
            file_extension = os.path.splitext(image_path)[1]
            cropped_img_name = f"cropped_{idx}{file_extension}"  # Append index and keep original extension
            
            # Ensure the file name is valid
            cropped_img_name = ''.join(c for c in cropped_img_name if c.isalnum() or c in '._-')
            
            # Construct the full path to save the cropped image
            cropped_img_path = os.path.join(image_path, cropped_img_name)

            cropped_img.save(cropped_img_path)
            cropped_image_paths.append(image_path)

            # Generate a unique ID for the extracted text
            unique_id = str(uuid.uuid4())

            # Save the extracted text and its unique ID in the dictionary
            image_texts[unique_id] = {'path': cropped_img_path}

            # Optionally, print or save the image path, text, and unique ID to a file
            print(f"Cropped image saved to: {cropped_img_path}, ID: {unique_id}")

    # Return both the paths and the text with unique IDs
    return cropped_image_paths


if __name__ == "__main__":
    import argparse

    # Set up argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", type=str, required=True,
                    help="path to input image")
    ap.add_argument("-east", "--east", type=str, required=False,
                    help="path to input EAST text detector")
    ap.add_argument("-c", "--min-confidence", type=float, default=0.5,
                    help="minimum probability required to inspect a region")
    ap.add_argument("-w", "--width", type=int, default=320,
                    help="resized image width (should be multiple of 32)")
    ap.add_argument("-e", "--height", type=int, default=320,
                    help="resized image height (should be multiple of 32)")
    args = vars(ap.parse_args())

    # Call the main function with parsed arguments
    main(args["image"], args["east"], args["min_confidence"], args["width"], args["height"])