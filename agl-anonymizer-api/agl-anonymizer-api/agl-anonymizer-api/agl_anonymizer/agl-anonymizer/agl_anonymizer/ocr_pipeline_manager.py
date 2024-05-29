from transformers import pipeline
from transformers import ViTImageProcessor, VisionEncoderDecoderModel
from PIL import Image
from flair_NER import NER_German
from names_generator import gender_and_handle_names
import fitz
import tempfile
from east_text_detection import east_text_detection
import os
import cv2
import numpy as np
import re
import torch

processor = ViTImageProcessor.from_pretrained('microsoft/trocr-large-str')
model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-large-str')
pipe = pipeline("image-to-text", model="microsoft/trocr-large-str")

def ocr_on_boxes(image_path, boxes):
    image = Image.open(image_path).convert("RGB")
    extracted_text_with_boxes = []
    confidences = []

    for box in boxes:
        (startX, startY, endX, endY) = box
        cropped_image = image.crop((startX, startY, endX, endY))
        pixel_values = processor(cropped_image, return_tensors="pt").pixel_values
        outputs = model.generate(pixel_values, output_scores=True, return_dict_in_generate=True)
        
        scores = outputs.scores

        # Simplified confidence score calculation
        confidence_score = torch.nn.functional.softmax(scores[-1], dim=-1).max().item()
                # Process cropped image with the OCR pipeline
        ocr_results = pipe(cropped_image, max_new_tokens=50)

        # Initialize an empty string to store concatenated text
        concatenated_text = ''

        # Iterate over each result and concatenate the 'generated_text'
        for result in ocr_results:
            if 'generated_text' in result:
                concatenated_text += ' ' + result['generated_text']

        # Append the concatenated text and corresponding box to the list
        extracted_text_with_boxes.append((concatenated_text.strip(), box))
        # Append the confidence score to the confidences list
        confidences.append(confidence_score)

    return extracted_text_with_boxes, confidences

def process_images_with_OCR_and_NER(file_path, east_path='frozen_east_text_detection.pb', device="olympus_cv_1500", min_confidence=0.5, width=320, height=320):
    print("Processing file:", file_path)

    # Initialize variables
    modified_images_map = {}
    combined_results = []
    names_detected = []
    extracted_text = ''

    # Determine the file type
    file_extension = file_path.split('.')[-1].lower()
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'tiff': 'image/tiff',
    }
    file_type = mime_types.get(file_extension, 'application/octet-stream').split('/')[-1]

    if file_type not in ['jpg', 'jpeg', 'png', 'tiff']:
        raise ValueError('Invalid file type.')

    # Check file existence
    if os.path.exists(file_path):
        print(f"Processing {file_path}.")
    else:
        raise ValueError("File does not exist or could not be found.")

    # Detect text boxes
    boxes, east_confidences = east_text_detection(file_path, east_path, min_confidence, width, height)
    print("Text boxes detected")

    # Perform OCR on detected boxes
    extracted_text_with_boxes, ocr_confidences = ocr_on_boxes(file_path, boxes)

    for (phrase, phrase_box), ocr_confidence in zip(extracted_text_with_boxes, ocr_confidences):
        processed_text = process_text(phrase)
        entities = NER_German(processed_text)
        if entities is None:
            entities = []

        entity_info = [(entity.text, entity.tag) for entity in entities if entity.tag == 'PER']

        combined_results.append((phrase, phrase_box, ocr_confidence, entity_info))

        for entity in entity_info:
            names_detected.append(entity[0])
            box_to_image_map = gender_and_handle_names([entity[0]], phrase_box, file_path, device)
            modified_images_map.update(box_to_image_map)

    # Prepare and print the result
    result = {
        'filename': file_path,
        'file_type': file_type,
        'extracted_text': extracted_text,
        'names_detected': names_detected,
        'combined_results': combined_results,
        'east_confidences': east_confidences
    }

    print("Processing completed:", combined_results)
    return modified_images_map, result

def process_text(extracted_text):
    # Replace two or more consecutive "\n" characters with a single "\n"
    cleaned_text = re.sub(r'\n{2,}', '\n', extracted_text)
    # Replace remaining "\n" characters with a space
    cleaned_text = cleaned_text.replace("\n", " ")
    return cleaned_text

# Example usage
if __name__ == "__main__":
    file_path = "your_file_path.jpg"
    modified_images_map, result = process_images_with_OCR_and_NER(file_path)
    for res in result['combined_results']:
        print(res)
