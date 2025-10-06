import base64
import math

import cv2
import numpy as np
import pdf2image
from PIL import Image

from preprocessor.src.flask.converter.consts import LINE_WIDTH
from preprocessor.src.flask.converter.utils import binarize, rgb_to_grayscale, rotate_image

# to prevent error due to images being too large
Image.MAX_IMAGE_PIXELS = 10000000000


def resize_to(img, scale):
    """
    Resizes the image so that largest dimension of the image becomes scale
    :return: CV2 grayscale image (2d numpy array)
    """
    h, w = img.shape
    if w > h:
        factor = scale / w
        img = cv2.resize(img, (scale, int(h * factor)))
    else:
        factor = scale / h
        img = cv2.resize(img, (int(w * factor), scale))
    return img


def pad_to(img, scale):
    """
    Pads the smallest dimension of img to scale
    :return: CV2 grayscale image (2d numpy array)
    """
    h, w = img.shape
    if w > h:
        img = cv2.copyMakeBorder(img, scale - h, 0, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    else:
        img = cv2.copyMakeBorder(img, 0, 0, scale - w, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    return img


def detect_horizontal_lines(image):
    """
    Highlights the horizontal lines of the image by applying an opening using a very long kernel
    :param image: 2d np array
    :return: 2d numpy array containing a heatmap for the horizontal lines
    """
    kernel = np.ones((LINE_WIDTH, 500), np.uint8)
    horizontal_lines = cv2.morphologyEx(cv2.bitwise_not(binarize(image)), cv2.MORPH_OPEN, kernel)

    return horizontal_lines


def detect_vertical_lines(image):
    """
    Highlights the vertical lines of the image by applying an opening using a very long kernel
    :param image: 2d np array
    :return: 2d numpy array containing a heatmap for the vertical lines
    """
    kernel = np.ones((500, LINE_WIDTH), np.uint8)
    horizontal_lines = cv2.morphologyEx(cv2.bitwise_not(binarize(image)), cv2.MORPH_OPEN, kernel)

    return horizontal_lines


def get_angle(gray_img, dimension):
    """
    Rotates the image by an angle in [-5, -4.5, ..., 5] degrees and determines the angle that has most straight lines
    in the given dimension
    :param gray_img: 2d numpy array of an grayscale image
    :param dimension: either "v" or "h"
    :return: best angle -> float
    """
    max_value = 0
    best_angle = 0
    # plan:
    # check iteratively in positive and negative direction
    # stop checking if at any point a zero is found in any direction
    # stop is independent from other direction
    check_negative = True
    check_positive = True
    # choose the correction function based on the direction
    if dimension == "v":
        detect_lines = detect_vertical_lines
    elif dimension == "h":
        detect_lines = detect_horizontal_lines
    else:
        raise Exception("Invalid direction")

    # get value for 0
    value = np.sum(detect_lines(gray_img))
    really_big_angle = (
        value == 0.0
    )  # for some images that are rotated by a large angle, the initial value might be zero
    # in that case the approach of stopping the search once you find an angle with value zero in
    # any direction is flawed, because it might just stop at the first iteration.
    # so in that case just check all angles

    # for -5 to 5 degrees get the image with the highest sum of all pixels (which correlates with the most lines)
    for i in range(1, 11):
        angle = i / 2
        # positive direction
        if check_positive or really_big_angle:  # only if not stopped or checking all angles due to really big angle
            rot_img = rotate_image(gray_img, angle)  # rotate the image by that angle
            value = np.sum(detect_lines(rot_img))  # sum the pixel values
            if value == 0.0:  # stop checking in this direction if no lines found
                check_positive = False
            if value > max_value:  # update best angle if new best angle found
                max_value = value
                best_angle = angle
        # negative direction
        if check_negative or really_big_angle:  # only if not stopped or checking all angles due to really big angle
            rot_img = rotate_image(gray_img, -angle)  # rotate the image by that angle
            value = np.sum(detect_lines(rot_img))  # sum the pixel values
            if value == 0.0:  # stop checking in this direction if no lines found
                check_negative = False
            if value > max_value:  # update best angle if new best angle found
                max_value = value
                best_angle = -angle
    return best_angle


def align_image(image):
    """
    Aligns the image using rotation and shearing,
    so that horizontal and vertical lines are parallel to the image borders
    :param image: cv2 image to align
    :return: aligned cv2 image
    """
    v_angle = get_angle(image, "v")
    h_angle = get_angle(image, "h")
    print("angles:", h_angle, v_angle)
    print("img shape b4 rot:", image.shape)
    # first rotate so that horizontal lines are parallel to viewport
    if h_angle != 0.0:
        # rotate the image by h_angle
        image = rotate_image(image, h_angle)
        print("img shape after rot:", image.shape)

    # de-shear the image
    if v_angle != h_angle:  # shear only present if horizontal and vertical lines are not rotated by same angle
        # shear factor is tan of angle,
        # factor is how much the image should be shifted to the right/ left per pixel from the center of the shearing
        # thus this is the opposite leg of a right triangle with angle shear_angle
        # this would mean factor = tan(shear_angle) * 1
        shear_angle = v_angle - h_angle  # h_angle was already corrected by rotation
        factor = math.tan(np.radians(shear_angle))

        w = image.shape[1]
        h = image.shape[0]

        # apply affine transformation using matrix
        shear_matrix = np.float32([[1, -factor, 0], [0, 1, 0]])
        shear_matrix[0, 2] = -shear_matrix[0, 1] * w / 2
        shear_matrix[1, 2] = -shear_matrix[1, 0] * h / 2
        image = cv2.warpAffine(image, shear_matrix, (w, h))
    return image


def convert_pdf_bytestring_to_img(bytestring):
    """
    Converts a pdf bytestring to a cv2 image. Will only return the first page of the pdf
    :param bytestring: bytestring of a pdf file
    :return: np array
    """
    images = pdf2image.convert_from_bytes(base64.b64decode(bytestring))
    ret_img = images[0]
    return rgb_to_grayscale(np.array(ret_img))


def convert_bytestring_to_cv2(bytestring):
    """
    Converts an image bytestring to a cv2 image
    :param bytestring: bytestring of an image file
    :return: np array
    """
    bytestring = str(bytestring).replace("b'", "").replace("'", "")
    arr = np.frombuffer(base64.b64decode(bytestring), dtype=np.uint8)
    return rgb_to_grayscale(cv2.imdecode(arr, flags=1))


def convert_cv2_to_bytestring(image):
    """
    Converts a cv2 image to a base64 encoded bytestring.
    :param image: cv2 image
    :return: base64 encoded bytestring (utf-8)
    """
    # Convert the image to a byte stream
    _, buffer = cv2.imencode(".png", image)
    # Encode the byte stream to base64
    base64_str = base64.b64encode(buffer).decode("utf-8")
    return base64_str


def load_and_standardize(bytestream, filename: str, scale: int):
    """
    Loads an image from a bytestream and applies the image standardization to it.
    :param bytestream: bytestream of the uploaded file
    :param filename: name of file. should contain either .pdf, .png, .jpg or .jpeg
    :param scale: scale to resize the image to
    :return: standardized image
    """
    filename = filename.lower()
    if ".png" in filename or ".jpg" in filename or ".jpeg" in filename:
        original_img = convert_bytestring_to_cv2(bytestream)
    elif ".pdf" in filename:
        original_img = convert_pdf_bytestring_to_img(bytestream)
    else:
        raise Exception("File type not supported")
    if scale > 0:
        img = resize_to(original_img, scale)
        img = align_image(img)
        # cv2 function used for padding only works if img is smaller than scale in any dimension
        if img.shape[0] < scale or img.shape[1] < scale:
            img = pad_to(img, scale)
        return img, original_img
    else:
        raise Exception("Scale factor must be > 0")
