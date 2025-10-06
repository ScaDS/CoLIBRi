import random
from collections import Counter
from importlib.resources import files

import cv2
import numpy as np
import pytesseract
from pytesseract import TesseractError

import preprocessor.src.flask.converter.resources as resource_dir
from preprocessor.src.flask.converter.consts import BIN_THRESH
from preprocessor.src.flask.converter.utils import binarize, find_rectangles


def rotate_image_multiple_of_90(image, rotation):
    """
    Rotates the image COUNTER-CLOCKWISE by rotation degrees
    :param image: cv2 image
    :param rotation: rotation in degrees. one of 90, 180, or 270
    :return: rotated image
    """
    rotation_codes = {270: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 90: cv2.ROTATE_90_COUNTERCLOCKWISE}
    return cv2.rotate(image, rotation_codes[rotation])


def rotate_rect(x, y, w, h, image_width, image_height, rotation):
    """
    Rotates the position and dimensions of a rectangle defined by (x, y, w, h)
    according to the specified rotation in degrees.

    :param x: X-coordinate of the top-left corner of the rectangle
    :param y: Y-coordinate of the top-left corner of the rectangle
    :param w: Width of the rectangle
    :param h: Height of the rectangle
    :param image_width: Width of the image containing the rectangle
    :param image_height: Height of the image containing the rectangle
    :param rotation: Rotation angle in degrees (one of 90, 180, or 270)
    :return: Tuple (new_x, new_y, new_w, new_h) representing the rotated rectangle
    """
    if rotation == 90:
        new_x = y
        new_y = image_width - x - w
        return new_x, new_y, h, w
    elif rotation == 180:
        new_x = image_width - x - w
        new_y = image_height - y - h
        return new_x, new_y, w, h
    elif rotation == 270:
        new_x = image_height - y - h
        new_y = x
        return new_x, new_y, h, w
    else:
        # No rotation case
        return x, y, w, h


def rotate_separation_outputs(
    drawing, info_blocks, cleaned_drawing, burnt_rects, inner_frame, info_blocks_mask, drawing_mask, rotation
):
    """
    Rotates the output of the separate(image) function according to the specified rotation in degrees.

    :param drawing: Drawing image with info blocks removed
    :param info_blocks: Image of info blocks
    :param cleaned_drawing: Cleaned drawing with texts and tables removed
    :param burnt_rects: List of rectangles (tuples of x, y, w, h) that correspond to cells of info blocks
    :param inner_frame: Tuple (x, y, w, h) representing the inner frame rectangle
    :param info_blocks_mask: Mask image for the information blocks
    :param drawing_mask: Mask image for the drawing
    :param rotation: Rotation angle in degrees (one of 90, 180, or 270)
    :return: Tuple containing rotated images, burnt rectangles, inner frame,
             and updated masks in the following order:
             (drawing, info_blocks, cleaned_drawing, burnt_rects, inner_frame,
              info_blocks_mask, drawing_mask)
    """
    # rotate images
    images = [drawing, info_blocks, cleaned_drawing]
    for i, image in enumerate(images):
        images[i] = rotate_image_multiple_of_90(image, rotation)
    drawing, info_blocks, cleaned_drawing = images

    # rotate masks
    masks = [info_blocks_mask, drawing_mask]
    for i, mask in enumerate(masks):
        mask = mask.astype(np.uint8)
        mask = rotate_image_multiple_of_90(mask, rotation)
        masks[i] = mask.astype(bool)
    info_blocks_mask, drawing_mask = masks

    # Get the image dimensions for rectangle rotation calculations
    image_height, image_width = drawing.shape[:2]

    # Rotate rectangles
    burnt_rects = [rotate_rect(x, y, w, h, image_width, image_height, rotation) for x, y, w, h in burnt_rects]
    inner_frame = rotate_rect(
        inner_frame[0], inner_frame[1], inner_frame[2], inner_frame[3], image_width, image_height, rotation
    )

    return drawing, info_blocks, cleaned_drawing, burnt_rects, inner_frame, info_blocks_mask, drawing_mask


def osd(image):
    """
    Uses tesseract OSD to determine the orientation of an image
    :param image: grayscale image
    :return: rotation in degrees (counter-clockwise) and a multiple of 90°
    """
    tessdata_dir = str(files(resource_dir).joinpath("tesseract"))
    try:
        result = pytesseract.image_to_osd(
            image,
            output_type=pytesseract.Output.DICT,
            config="-c min_characters_to_try=5 --tessdata-dir " + tessdata_dir,
        )
        rotation = result["rotate"]
    except TesseractError as e:
        print(e)
        rotation = None
    return rotation


def crop_to_contents(image):
    """
    Crops a grayscale image with a white background to its black contents.
    :param image: cv2 image
    :return: cropped image
    """
    # Convert the image to binary (foreground is black, background is white)
    binary = binarize(image)

    # Invert the image: black text becomes white, and white background becomes black
    inverted_image = cv2.bitwise_not(binary)

    # Find all non-zero points (text)
    coords = cv2.findNonZero(inverted_image)

    # Get the bounding box of the non-zero points
    x, y, w, h = cv2.boundingRect(coords)

    # Crop the image to the bounding box
    cropped_image = image[y : y + h, x : x + w]

    return cropped_image


def crop_is_empty(crop_img) -> bool:
    """
    Checks if the given image is empty (contains > 99% white pixels)
    Args:
        crop_img: cv2 image

    Returns: boolean

    """
    # Find all non-white pixels
    non_white_pixels = np.where(crop_img < BIN_THRESH)
    h, w = crop_img.shape
    return not len(non_white_pixels[0] > h * w * 0.01)


def compose_image(is_horizontal, crops):
    """
    Creates a composite image of a set of crops by stacking them either vertically or horizontally
    :param is_horizontal: whether the original image is horizontal. determines the stacking direction
    :param crops: list of crops of the original image
    :return: cv2 composed image
    """
    # get dimensions for the background
    sum_compose_h = 0
    max_compose_w = 0
    max_compose_h = 0
    sum_compose_w = 0

    non_empty_crops = []

    for crop in crops:
        if not crop_is_empty(crop):
            non_empty_crops.append(crop)
            (height, width) = crop.shape
            sum_compose_h += height
            sum_compose_w += width
            if height > max_compose_h:
                max_compose_h = height
            if width > max_compose_w:
                max_compose_w = width
    # create empty composite image
    if is_horizontal:
        composite_image = np.ones((sum_compose_h, max_compose_w), np.uint8) * 255
    else:
        composite_image = np.ones((max_compose_h, sum_compose_w), np.uint8) * 255

    # add crops to the composite image
    curr = 0
    for crop in non_empty_crops:
        h, w = crop.shape
        if is_horizontal and w >= h:  # only add if crop is horizontal
            composite_image[curr : curr + h, 0:w] = crop
            curr += h
        elif not is_horizontal and h >= w:  # only add if crop is vertical
            composite_image[0:h, curr : curr + w] = crop
            curr += w
    return composite_image


def rotate_and_determine_angles(img):
    """
    Finds rectangles in a given img and creates a composite image using those crops. This composite image is rotated
    by 90, 180 and 270 (and 0) degrees. For all rotations the orientation detection is called and the results are
    returned. The goal of this is to minimize the variance and the error that is caused by using pre-trained tesseract
    models. By analyzing the detected orientations a common angle should be able to be determined.
    :param img: grayscale image
    :return: rot_0, rot_90, rot_180, rot_270
    """
    # sample 25 random rectangle in the image
    rects = find_rectangles(img)
    random_rects = random.sample(rects, min(50, len(rects)))  # nosec B311
    crops = []  # to keep track of the crops that will be used in the puzzle image

    # counters for determining if image is horizontal
    vertical_crops = 0
    horizontal_crops = 0

    for rect in random_rects:
        x, y, w, h = rect
        if w > 1000 and h > 1000:  # too big, probably the frame
            continue
        # count horizontal and vertical rects
        if w > h:
            horizontal_crops += 1
        else:
            vertical_crops += 1
        # save crop
        crop = img[y : y + h, x : x + w]
        crops.append(crop)

    # determine whether image is vertical or horizontal
    is_horizontal = horizontal_crops >= vertical_crops

    # stitch together image from crops
    composite_image_initial = compose_image(is_horizontal, crops)
    # remove blank space
    composite_image = crop_to_contents(composite_image_initial)

    # orientation detection from tesseract
    rot_0 = osd(composite_image)
    rot_90 = osd(rotate_image_multiple_of_90(composite_image, 90))
    rot_180 = osd(rotate_image_multiple_of_90(composite_image, 180))
    rot_270 = osd(rotate_image_multiple_of_90(composite_image, 270))
    return rot_0, rot_90, rot_180, rot_270


def angle_diff(angle1, angle2):
    """
    Calculates the difference (angle1 - angle2) between two angles
    :param angle1: angle in degrees
    :param angle2: angles in degrees
    :return: 0 < (angle1 - angle2) < 360
    """
    return (angle1 - angle2) % 360


def dominant_angle(angles):
    """
    Determines the dominant angle of the output of the rotate_and_determine_angles function. Each element of the angles
    tuple is first subtracted of its initial rotation (applied before osd). Then the most common angle is determined.
    If the list only consists of None values, None is returned.
    :param angles: tuple of angles -> (rot_0, rot_90, rot_180, rot_270)
    :return: most likely angle of rotation of the original image. If input only consists of None values, None.
    """
    rot_0, rot_90, rot_180, rot_270 = angles
    # subtract the rotation for the rotated puzzle images
    converted_angles = [
        rot_0,
        angle_diff(rot_90, 90) if rot_90 is not None else None,
        angle_diff(rot_180, 180) if rot_180 is not None else None,
        angle_diff(rot_270, 270) if rot_270 is not None else None,
    ]
    # remove None values
    angles_without_nones = []
    for angle in converted_angles:
        if angle is not None:
            angles_without_nones.append(angle)
    # if there are values that are not None
    if len(angles_without_nones) > 0:
        # return the most common
        angle_counts = Counter(angles_without_nones)  # count the occurences
        [(most_common_angle, _)] = angle_counts.most_common(1)
        return most_common_angle
    else:
        return None


def get_image_rotation(img):
    """
    Determines the likely rotation angle of an image using its textual contents.
    :param img: grayscale image
    :return: likely angle of rotation. If it can't be determined, None is returned.
    """
    rot_0, rot_90, rot_180, rot_270 = rotate_and_determine_angles(img)
    return dominant_angle((rot_0, rot_90, rot_180, rot_270))
