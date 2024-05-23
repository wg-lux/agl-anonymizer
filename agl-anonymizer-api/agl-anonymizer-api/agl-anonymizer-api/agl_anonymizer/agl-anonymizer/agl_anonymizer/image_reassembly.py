import cv2
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
