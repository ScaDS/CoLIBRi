import cv2
import numpy as np

from src.flask.converter.consts import BIN_THRESH, LINE_WIDTH, MIN_RECT_AREA, MIN_RECT_INTER_RATIO


def rgb_to_grayscale(rgb_image):
    """
    Converts a cv2 RGB image to grayscale.
    """
    gray_img = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    return gray_img


def grayscale_to_rgb(grayscale_image):
    """
    Converts a cv2 grayscale image to RGB.
    """
    rgb_image = cv2.cvtColor(grayscale_image, cv2.COLOR_GRAY2RGB)
    return rgb_image


def read(image_path):
    """
    Reads an image from disk  as grayscale for the given path.
    """
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    return image


def binarize(image):
    """
    Binarize the given image using BIN_THRESH from consts.py.
    """
    binary_image = cv2.threshold(image, BIN_THRESH, 255, cv2.THRESH_BINARY)[1]

    return binary_image


def erode(image, kernel_size=3, iterations=1):
    """
    Erode the given image using cv2.
    Args:
        image: image to erode
        kernel_size: kernel size for erosion. will use kernel of size [kernel_size, kernel_size]
        iterations: how many times to run the erosion

    Returns: eroded cv2 image

    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    eroded_image = cv2.erode(image, kernel, iterations)

    return eroded_image


def find_contours(binary_image, return_hierarchy=False, external_only=True):
    """
    Find contours in the given binary image using cv2.
    Args:
        binary_image: cv2 binary image
        return_hierarchy: if hierarchy should be computed
        external_only: if only external contours should be found

    Returns: countours, (hierarchy)

    """
    if not return_hierarchy:
        if external_only:
            contours, _ = cv2.findContours(cv2.bitwise_not(binary_image), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        else:
            contours, _ = cv2.findContours(binary_image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

        return contours
    else:
        contours, hierarchy = cv2.findContours(cv2.bitwise_not(binary_image), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        return contours, hierarchy


def rotate_image(image, angle):
    """
    Rotates an image by angle. Caution: might crop its contents
    :param image: 2d numpy array
    :param angle: angle in degrees
    :return: 2d numpy array
    """
    rotation_matrix = cv2.getRotationMatrix2D((image.shape[0] / 2, image.shape[1] / 2), -angle, 1)
    rotated_image = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]), borderValue=255)
    return rotated_image


def validate_rectangle(rect, binary_image, threshold=MIN_RECT_INTER_RATIO):
    """
    Validate whether the edges of a rectangle correspond to actual edges in an image based on intersection ratio.

    Args:
        rect (tuple): A tuple (x, y, w, h) representing the rectangle coordinates and dimensions.
        binary_image (numpy.ndarray): A binary image used for validation.
        threshold (float): Threshold for intersection ratio.
    Returns:
        bool: True if the rectangle intersects with the binary image with a sufficient ratio above threshold.
    """
    # Create a mask of the rectangle
    edge_mask = np.zeros_like(binary_image)
    x, y, w, h = rect
    cv2.rectangle(edge_mask, (x, y), (x + w, y + h), 255, 1)

    # Erode the binary image to account for potential gaps
    binary_image = erode(binary_image, kernel_size=5)

    # Compute the intersection between the rectangle and edge image
    inter = cv2.bitwise_and(cv2.bitwise_not(binary_image), edge_mask)
    inter_ratio = np.sum(inter) / np.sum(edge_mask)

    return inter_ratio >= threshold


def find_rectangles(image):
    """
    Find potential rectangles (cells and inner frame) in the input image.

    Args:
        image (numpy.ndarray): The input image to find rectangles in.

    Returns:
        list: A list of rectangles (tuples) found in the image.
    """
    binary_image = binarize(image)
    contours = find_contours(binary_image, external_only=False)

    rects = []

    for contour in contours:
        if cv2.contourArea(contour) < MIN_RECT_AREA:
            continue

        rect = cv2.boundingRect(contour)
        if validate_rectangle(rect, binary_image):
            rects.append(rect)

        else:
            # If the rectangle does not pass validation, try approximate the contour and validate again
            for eps in np.linspace(0.001, 0.05, 10):
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, eps * peri, True)

                rect = cv2.boundingRect(approx)
                if validate_rectangle(rect, binary_image):
                    rects.append(rect)
                    break

    return rects


class View:
    def __init__(self, image, x, y):
        """
        Class representing a view in a technical drawing.
        Args:
            image: the cropped image with the view
            x: top left x coordinate in the original image
            y: top left y coordinate in the original image
        """
        self.image = image
        self.x = x
        self.y = y


def get_cropped_views(image):
    """
    For a shape image, get the countours (should be the part outlines for each view) and crops them.
    Args:
        image: grayscale image

    Returns: a list of cropped views (grayscale images)

    """
    # find contours in image
    binary_image = binarize(image)
    contours = find_contours(binary_image)

    cropped_views = []
    areas = []

    for contour in contours:
        # draw the contours on a mask image
        mask = np.zeros_like(image)
        cv2.drawContours(mask, [contour], 0, 255, thickness=cv2.FILLED)
        component = cv2.bitwise_and(cv2.bitwise_not(image), mask)

        # crop the contour using its bounding box
        x, y, w, h = cv2.boundingRect(contour)
        cropped_view = component[y : y + h, x : x + w]

        cropped_views.append(View(cv2.bitwise_not(cropped_view), x, y))
        areas.append(w * h)

    cropped_views = [
        view for _, _, view in sorted(zip(areas, list(range(len(areas))), cropped_views, strict=True), reverse=True)
    ]

    return cropped_views


def create_mask(drawing, keep_borders=False):
    # TODO: documentation
    if keep_borders:
        flood_filled_image = drawing.copy()
        cv2.floodFill(flood_filled_image, None, (0, 0), (255, 0, 0))

        mask = np.zeros_like(flood_filled_image)
        mask[np.where(np.all(flood_filled_image == (255, 0, 0), axis=-1))] = (255, 255, 255)
    else:
        binary_image = cv2.bitwise_not(binarize(drawing))
        mask = np.zeros_like(binary_image)
        contours, hierarchy = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            cv2.drawContours(mask, [contour], 0, 255, -1)
            cv2.drawContours(mask, [contour], 0, 0, LINE_WIDTH)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        for _ in range(LINE_WIDTH + 1):
            mask = cv2.dilate(mask, kernel)

    return mask
