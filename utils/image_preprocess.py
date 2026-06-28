import cv2
import numpy as np


def preprocess_image(image_path):

    image = cv2.imread(image_path)

    if image is None:
        raise Exception("Image not found.")

    # Auto Rotate (Notebook images)
    h, w = image.shape[:2]

    if h > w:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Remove Noise
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # Increase Contrast
    gray = cv2.equalizeHist(gray)

    # Adaptive Threshold
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        21,
        10
    )

    return image, thresh