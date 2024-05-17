# import the necessary packages
from imutils.object_detection import non_max_suppression
import numpy as np
import time
import cv2
from box_operations import extend_boxes_if_needed

'''
This module implements argman's EAST Text Detection in a function. The model thats being used is specified by the east_path variable. This is the starting point for the anonymization pipeline.

'''

def east_text_detection(image_path, east_path='frozen_east_text_detection.pb', min_confidence=0.5, width=320, height=320):
    # load the input image and grab the image dimensions
    orig = cv2.imread(image_path)
    #orig = image.copy()
    (origH, origW) = orig.shape[:2]

    # set the new width and height and then determine the ratio in change
    # for both the width and height
    (newW, newH) = (width, height)
    rW = origW / float(newW)
    rH = origH / float(newH)

    # resize the image and grab the new image dimensions
    image = cv2.resize(orig, (newW, newH))
    (H, W) = image.shape[:2]

    # define the two output layer names for the EAST detector model that
    # we are interested in
    layerNames = [
        "feature_fusion/Conv_7/Sigmoid",
        "feature_fusion/concat_3"]

    # load the pre-trained EAST text detector
    print("[INFO] loading EAST text detector...")
    net = cv2.dnn.readNet("frozen_east_text_detection.pb")

    blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
                                (123.68, 116.78, 103.94), swapRB=True, crop=False)
    start = time.time()
    net.setInput(blob)
    (scores, geometry) = net.forward(layerNames)
    end = time.time()

    # grab the number of rows and columns from the scores volume, then
    # initialize our set of bounding box rectangles and corresponding
    # confidence scores
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    # loop over the number of rows and columns
    for y in range(0, numRows):
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        # loop over the number of columns
        for x in range(0, numCols):
            # check for minimum confidence before continuing
            if scoresData[x] < min_confidence:
                continue
            # compute the offset factor as our resulting feature maps will
            # be 4x smaller than the input image
            (offsetX, offsetY) = (x * 4.0, y * 4.0)
            
            
        # extract the rotation angle for the prediction and then
            # compute the sin and cosine
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)

            # use the geometry volume to derive the width and height of
            # the bounding box
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            # compute both the starting and ending (x, y)-coordinates for
            # the text prediction bounding box
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            # add the bounding box coordinates and probability score to
            # our respective lists
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])

    # apply non-maxima suppression to suppress weak, overlapping bounding
    # boxes
    # initialize the list of bounding boxes that will be returned
    boxes = non_max_suppression(np.array(rects), probs=confidences)

    output_boxes = []

    # Loop over the bounding boxes and scale them
    for (startX, startY, endX, endY) in boxes:
        # Scale the bounding box coordinates based on the respective ratios
        startX = int(startX * rW)
        startY = int(startY * rH)
        endX = int(endX * rW)
        endY = int(endY * rH)

        # Draw the bounding box on the original image
        cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)

        
        # append the scaled bounding box to the list of output boxes
        output_boxes.append((startX, startY, endX, endY))

    # return the scaled bounding boxes
    #cv2.imshow("Text Detection", orig)
    #cv2.waitKey(0)
    output_boxes = sort_boxes(output_boxes)
    
    output_boxes = extend_boxes_if_needed(orig, output_boxes)

    return output_boxes

def sort_boxes(boxes):
    # Define a threshold to consider boxes on the same line
    vertical_threshold = 10

    # Sort boxes by y coordinate, then by x coordinate if y coordinates are similar
    boxes.sort(key=lambda b: (round(b[1] / vertical_threshold), b[0]))

    return boxes



# if this script is the main script being run, parse command line args and run
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", type=str, required=True,
                    help="path to input image")
    ap.add_argument("-east", "--east", type=str, required=True,
                    help="path to input EAST text detector")
    ap.add_argument("-c", "--min-confidence", type=float, default=0.5,
                    help="minimum probability required to inspect a region")
    ap.add_argument("-w", "--width", type=int, default=320,
                    help="resized image width (should be multiple of 32)")
    ap.add_argument("-e", "--height", type=int, default=320,
                    help="resized image height (should be multiple of 32)")
    args = vars(ap.parse_args())

