import cv2
import numpy as np
import random
import gender_guesser.detector as gender
import time
import uuid
import json
#from color_picker_avg import get_dominant_color

# Load the names from the files
with open('names_dict/first_and_last_name_female.txt', 'r') as file:
    female_names = [line.strip() for line in file]

with open('names_dict/first_and_last_name_male.txt', 'r') as file:
    male_names = [line.strip() for line in file]


import json
import cv2
import numpy as np
import uuid
import time

def add_name_to_image(name, gender_par, device, font=None, text_size=None, background_color=(0, 0, 0), font_color=(255, 255, 255)):
    
    def parse_color(color_str):
        # Convert color string "(0, 0, 0)" to tuple (0, 0, 0)
        return tuple(map(int, color_str.strip('()').split(',')))

    def format_name(full_name, format_string):
        names = full_name.split()
        if len(names) < 2:
            return full_name
        first_name = names[0]
        last_name = ' '.join(names[1:])
        formatted_name = format_string.replace("first_name", first_name).replace("last_name", last_name)
        return formatted_name

    try:
        with open(f'devices/{device}.json') as json_parameters:
            data = json.load(json_parameters)
            keys_to_check = ["background_color", "text_color", "font", "font_size", "text_formatting"]
            for key in data["fields"]:
                if key in keys_to_check:
                    if key == "background_color":
                        background_color = parse_color(data["fields"][key])
                    elif key == "text_color":
                        font_color = parse_color(data["fields"][key])
                    elif key == "font":
                        font = getattr(cv2, data["fields"][key])
                    elif key == "font_size":
                        font_size = data["fields"][key]
                        font_scale = font_size / 20  # Assuming 20 is the default size
                        font_thickness = 2
                    elif key == "text_formatting":
                        name = format_name(name, data["fields"][key])
    except FileNotFoundError:
        print("Device not found")
        return None

    # Define the font, scale, and thickness
    if font is None:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_thickness = 2
    
    if text_size is not None:
        font_scale = text_size[0]
        font_thickness = text_size[1]
    else:
        text_size = cv2.getTextSize(name, font, font_scale, font_thickness)[0]
        text_width, text_height = text_size[0], text_size[1]

    # Add some padding around the text
    padding = 10
    text_width_with_padding = text_width + 2 * padding
    text_height_with_padding = text_height + 2 * padding

    # Create a new image with a white background just enough to fit the text and padding
    text_img = np.full((text_height_with_padding, text_width_with_padding, 3), background_color, dtype=np.uint8)

    # Calculate the position to draw the text (approximately center)
    text_x = padding
    text_y = padding + text_height  # Vertical alignment by the baseline of the text

    # Draw the text onto the new image
    for i, line in enumerate(name.split("\n")):
        cv2.putText(text_img, line, (text_x, text_y + i * (text_height + padding)), font, font_scale, font_color, font_thickness)

    # Save the new image with the name text
    unique_id = str(uuid.uuid4())[:8]
    output_filename = f"{gender_par}_{int(time.time())}_{unique_id}.png"  # Using .png to preserve background
    output_image_path = f"temp/{output_filename}"
    cv2.imwrite(output_image_path, text_img)

    return output_image_path




def gender_and_handle_names(words, box, image_path, device="olympus_cv_1500"):
    print("Finding out Gender and Name")
    first_name = words[0]
    
    d = gender.Detector()
    gender_guess = d.get_gender(first_name)
    box_to_image_map = {}

    if gender_guess in ['male', 'mostly_male']:
        output_image_path = add_name_to_image(random.choice(male_names), "male", device)
    elif gender_guess in ['female', 'mostly_female']:
        output_image_path = add_name_to_image(random.choice(female_names), "female", device)
    else:  # 'unknown' or 'andy'
        output_image_path = add_name_to_image(random.choice(female_names + male_names), "neutral", device)

    # Include the image_path in the key
    box_to_image_map[(box, image_path)] = output_image_path
    return box_to_image_map
