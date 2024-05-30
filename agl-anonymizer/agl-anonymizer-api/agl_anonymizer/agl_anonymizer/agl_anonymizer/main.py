import cv2
from ocr_pipeline_manager import process_images_with_OCR_and_NER
import uuid
import os
import fitz
import tempfile
from pdf_operations import convert_pdf_page_to_image, merge_pdfs, convert_image_to_pdf
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
from image_reassembly import reassemble_image


def process_image(image_path, east_path, device, min_confidence, width, height, results_dir, temp_dir):
    print(f"Processing file: {image_path}")
    unique_id = str(uuid.uuid4())[:8]
 
# searching the pattern
    id = f"image_{unique_id}"
    # Load the image using OpenCV
    original_image = cv2.imread(image_path)
    if original_image is None:
        raise ValueError(f"Could not load image at {image_path}")
    # Image processing logic here
    modified_images_map, stats = process_images_with_OCR_and_NER(image_path, east_path, device, min_confidence, width, height)
    print("Images processed")
    # Print out the modified images map
    print("Modified Images Map:")
    reassembled_image_path=image_path
    reassembled_image_path = reassemble_image(modified_images_map, results_dir, id)

    return reassembled_image_path, stats

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


def main(image_or_pdf_path, east_path='frozen_east_text_detection.pb', device="olympus_cv_1500", min_confidence=0.5, width=320, height=320):
    results_dir = os.path.join(os.path.dirname(image_or_pdf_path), "results")
    os.makedirs(results_dir, exist_ok=True)
    temp_dir = tempfile.mkdtemp()
    image_paths = get_image_paths(image_or_pdf_path, temp_dir)
    
    processed_pdf_paths = []  # This will store paths of PDFs (either directly processed or converted from images)
    try:
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = [executor.submit(process_image, img_path, east_path, device, min_confidence, width, height, results_dir, temp_dir) for img_path in image_paths]
            for future in as_completed(futures):
                processed_image_path, stats = future.result()
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

if __name__ == "__main__":
    import argparse

    # Set up argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", type=str, required=True,
                    help="path to input image")
    ap.add_argument("-east", "--east", type=str, required=False,
                    help="path to input EAST text detector")
    ap.add_argument("-d", "--device", type=str, default="olympus_cv_1500",
                    help="device name is required to set the correct text settings")
    ap.add_argument("-c", "--min-confidence", type=float, default=0.5,
                    help="minimum probability required to inspect a region")
    ap.add_argument("-w", "--width", type=int, default=320,
                    help="resized image width (should be multiple of 32)")
    ap.add_argument("-e", "--height", type=int, default=320,
                    help="resized image height (should be multiple of 32)")
    args = vars(ap.parse_args())

    # Call the main function with parsed arguments
    main(args["image"], args["east"], args["device"], args["min_confidence"], args["width"], args["height"])