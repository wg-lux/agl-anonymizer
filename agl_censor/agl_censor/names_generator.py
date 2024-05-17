import cv2
import numpy as np
import random
import gender_guesser.detector as gender
import time
import uuid
#from color_picker_avg import get_dominant_color

# Load the names from the files
with open('names_dict/first_and_last_name_female.txt', 'r') as file:
    female_names = [line.strip() for line in file]

with open('names_dict/first_and_last_name_male.txt', 'r') as file:
    male_names = [line.strip() for line in file]
    
def add_name_to_image(name, gender_par):
    # Define the font, scale, and thickness
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_thickness = 2

    # Get the text size
    text_size = cv2.getTextSize(name, font, font_scale, font_thickness)[0]
    text_width, text_height = text_size[0], text_size[1]

    # Add some padding around the text
    padding = 10
    text_width_with_padding = text_width + 2 * padding
    text_height_with_padding = text_height + 2 * padding

    # Create a new image with a white background just enough to fit the text and padding
    text_img = np.full((text_height_with_padding, text_width_with_padding, 3), (255, 255, 255), dtype=np.uint8)

    # Calculate the position to draw the text (approximately center)
    text_x = padding
    text_y = padding + text_height  # Vertical alignment by the baseline of the text

    # Draw the text onto the new image
    cv2.putText(text_img, name, (text_x, text_y), font, font_scale, (0, 0, 0), font_thickness)

    # Save the new image with the name text
    unique_id = str(uuid.uuid4())[:8]
    output_filename = f"{gender_par}_{int(time.time())}_{unique_id}.png"  # Using .png to preserve background
    output_image_path = f"temp/{output_filename}"
    cv2.imwrite(output_image_path, text_img)

    return output_image_path


def gender_and_handle_names(words, box, image_path):
    print("Finding out Gender and Name")
    first_name = words[0]
    
    d = gender.Detector()
    gender_guess = d.get_gender(first_name)
    box_to_image_map = {}

    if gender_guess in ['male', 'mostly_male']:
        output_image_path = add_name_to_image(random.choice(male_names), "male")
    elif gender_guess in ['female', 'mostly_female']:
        output_image_path = add_name_to_image(random.choice(female_names), "female")
    else:  # 'unknown' or 'andy'
        output_image_path = add_name_to_image(random.choice(female_names + male_names), "neutral")

    # Include the image_path in the key
    box_to_image_map[(box, image_path)] = output_image_path
    return box_to_image_map
