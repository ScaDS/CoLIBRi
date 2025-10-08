import cv2
import numpy as np

from src.flask.converter.utils import binarize, find_rectangles, validate_rectangle
from src.flask.converter.consts import (
    DIST_THRESH,
    LINE_WIDTH,
    MAX_CONTOUR_AREA,
    MAX_RECT_AREA,
    MIN_IF_AREA_RATIO,
)


def find_inner_frame(image, rects):
    """
    Finds the inner frame rectangle within an image, defined as the smallest rectangle
    that meets a minimum area ratio criterion.

    :param image: The input image where the frame needs to be found.
    :param rects: A list of rectangles (each as a tuple of (x, y, w, h)) representing potential frame candidates.
    :return: The selected inner frame rectangle as a tuple (x, y, w, h).
             Returns an empty list if no rectangle meets the criteria.
    """
    # Find the bounding rectangle of the non-zero region in the image
    x, y, w, h = cv2.boundingRect(cv2.findNonZero(image))

    # Calculate the area of the entire non-zero region in the image
    image_area = w * h
    smallest_area = image_area

    inner_frame = []

    for rect in rects:
        x, y, w, h = rect
        area = h * w

        # Update inner frame if this rectangle has a smaller area than the current smallest_area
        # and meets the minimum area ratio requirement
        if smallest_area > area > image_area * MIN_IF_AREA_RATIO:
            inner_frame = rect
            smallest_area = area

    return inner_frame


def is_corner_cell(rect, inner_frame, image):
    """
    Determines if a given rectangle is a corner cell relative to the inner frame of an image.
    Corner cells are (often L-shaped) cells overlapping one or two corners of the inner frame.

    :param rect: A tuple (x, y, w, h) representing the coordinates and dimensions of potential corner cell.
    :param inner_frame: A tuple (x, y, w, h) representing the coordinates and dimensions of the inner frame.
    :param image: The input image.
    :return: A boolean value indicating whether the rectangle qualifies as a corner cell.
    """

    x1, y1, w1, h1 = inner_frame
    x2, y2, w2, h2 = rect

    # Initialize the counter for corners of the inner frame that fall within the rectangle
    corners_inside = 0
    # Define the four corners of the inner frame
    corners = [(x1, y1), (x1 + w1, y1), (x1, y1 + h1), (x1 + w1, y1 + h1)]

    # Check each corner to see if it falls within the rectangle
    for corner in corners:
        x, y = corner
        if x2 <= x <= x2 + w2 and y2 <= y <= y2 + h2:
            corners_inside += 1

    # Calculate the center of the rectangle
    x = x2 + w2 // 2
    y = y2 + h2 // 2
    # Check if the rectangle's center falls within the inner frame
    center_in_inner_frame = x1 <= x <= x1 + w1 and y1 <= y <= y1 + h1

    binary_image = binarize(image)

    # For corner cell candidates, validate_rectangle is called with a higher threshold
    # to avoid wrongly classifying them as rectangles
    return (
        (corners_inside == 1 or corners_inside == 2)
        and center_in_inner_frame
        and not validate_rectangle(rect, binary_image, threshold=0.9)
    )


def handle_corner_cells(rects, inner_frame, image):
    """
    Adjusts the inner frame by identifying and processing corner cells in the list of rectangles.
    The function updates the inner frame if a larger rectangle is identified as a corner cell
    and removes all other rectangles that qualify as corner cells relative to the updated inner frame.

    :param rects: A list of rectangles (each as a tuple (x, y, w, h)) to be checked against the inner frame.
    :param inner_frame: A tuple (x, y, w, h) representing the current inner frame dimensions and position.
    :param image: The input image.
    :return: A tuple (rects, inner_frame) where:
             - `rects` is the modified list of rectangles, with corner cells removed.
             - `inner_frame` is the potentially updated inner frame.
    """
    if len(inner_frame) > 0:
        # Iterate through rectangles
        for i, rect in enumerate(rects):
            w1, h1 = inner_frame[2:]
            area1 = w1 * h1
            w2, h2 = rect[2:]
            area2 = w2 * h2

            # Update the inner frame if a larger rectangle qualifies as a corner cell
            if area1 < area2 and is_corner_cell(inner_frame, rect, image):
                inner_frame = rect
                del rects[i]

        # Filter out all rectangles that qualify as corner cells for the updated inner frame
        rects = [rect for rect in rects if not is_corner_cell(rect, inner_frame, image)]

    return rects, inner_frame


class Rectangle:
    """
    Represents a rectangle with spatial properties and a status used in a fire propagation algorithm.

    Attributes:
        x (int): The x-coordinate of the rectangle's top-left corner.
        y (int): The y-coordinate of the rectangle's top-left corner.
        w (int): The width of the rectangle.
        h (int): The height of the rectangle.
        status (str): The current fire propagation status of the rectangle. Default is "green".
    """

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.status = "green"

    def intersects(self, other):
        """
        Checks if the current rectangle intersects with another rectangle.

        :param other: Another Rectangle instance to check for intersection.
        :return: True if rectangles intersect, False otherwise.
        """
        return not (
            (self.x > other.x + other.w)
            or (self.x + self.w < other.x)
            or (self.y > other.y + other.h)
            or (self.y + self.h < other.y)
        )

    def propagate_fire(self):
        """
        Changes the rectangle's status to "on fire".
        """
        self.status = "on fire"

    def burn(self):
        """
        Changes the rectangle's status to "burnt".
        """
        self.status = "burnt"


def propagate_fire(rects, inner_frame):
    """
    Simulates fire propagation through a collection of rectangles, beginning from a specified inner frame.

    :param rects: A list of tuples, where each tuple (x, y, w, h) represents a rectangle's coordinates and dimensions.
    :param inner_frame: A tuple (x, y, w, h) specifying the inner frame's position and size, which initiates the fire.
    :return: A list of tuples representing burnt rectangles' positions and sizes after the fire propagation.
    """
    if len(inner_frame) == 0:
        return []

    # Convert the given rectangles to Rectangle objects with default "green" status
    rectangles = [Rectangle(*rect) for rect in rects]

    # Set the inner frame on fire, initializing fire propagation from this rectangle
    on_fire_rectangles = [Rectangle(*inner_frame)]

    # Fire propagation loop: checks neighboring rectangles within a specified distance and propagates fire accordingly
    while on_fire_rectangles:
        new_on_fire_rectangles = []

        for rectangle in on_fire_rectangles:
            for other in rectangles:
                if other.status == "green":
                    edges = [
                        (rectangle.x, rectangle.y, rectangle.w, 0),
                        (rectangle.x + rectangle.w, rectangle.y, 0, rectangle.h),
                        (rectangle.x, rectangle.y + rectangle.h, rectangle.w, 0),
                        (rectangle.x, rectangle.y, 0, rectangle.h),
                    ]

                    # Check if other rectangles intersect with any expanded edges within the DIST_THRESH
                    for edge in edges:
                        x, y, w, h = edge
                        edge_rectangle = Rectangle(
                            x - DIST_THRESH / 2, y - DIST_THRESH / 2, w + DIST_THRESH, h + DIST_THRESH
                        )

                        if other.intersects(edge_rectangle):
                            other.propagate_fire()
                            on_fire_rectangles.append(other)

            rectangle.burn()

        on_fire_rectangles = new_on_fire_rectangles

    # Collect all rectangles that ended up "burnt" after propagation
    burnt_rects = []

    for rectangle in rectangles:
        if rectangle.status == "burnt":
            burnt_rects.append((rectangle.x, rectangle.y, rectangle.w, rectangle.h))

    return burnt_rects


def expand_inner_frame(inner_frame, burnt_rects):
    """
    Expands the inner frame by checking and merging adjacent burnt rectangles with matching dimensions.
    After the expansion, re-propagates fire through the updated list of burnt rectangles.

    :param inner_frame: A tuple (x, y, w, h) representing the coordinates and dimensions of the inner frame.
    :param burnt_rects: A list of tuples, where each tuple (x, y, w, h) represents a burnt rectangle's position
                        and dimensions.

    :return: A tuple with the updated inner frame and the modified list of burnt rectangles.
    """
    # Remove the current inner frame from burnt_rects to avoid redundant processing
    del burnt_rects[burnt_rects.index(inner_frame)]
    x1, y1, w1, h1 = inner_frame

    # TODO: Sort/prefilter burnt_rects, handle multiple expansions

    # Check adjacent burnt rectangles to expand the inner frame
    # Expansions are done by checking alignment of edges within LINE_WIDTH tolerance
    for i, rect in enumerate(burnt_rects):
        x2, y2, w2, h2 = rect
        if abs(x1 - (x2 + w2)) < LINE_WIDTH and abs(y1 - y2) < LINE_WIDTH and abs(h1 - h2) < LINE_WIDTH:
            inner_frame = (x2, y1, w1 + w2, h1)
            del burnt_rects[i]
            break
        if abs((x1 + w1) - x2) < LINE_WIDTH and abs(y1 - y2) < LINE_WIDTH and abs(h1 - h2) < LINE_WIDTH:
            inner_frame = (x1, y1, w1 + w2, h1)
            del burnt_rects[i]
            break
        if abs(y1 - (y2 + h2)) < LINE_WIDTH and abs(x1 - x2) < LINE_WIDTH and abs(w1 - w2) < LINE_WIDTH:
            inner_frame = (x1, y2, w1, h1 + h2)
            del burnt_rects[i]
            break
        if abs((y1 + h1) - y2) < LINE_WIDTH and abs(x1 - x2) < LINE_WIDTH and abs(w1 - w2) < LINE_WIDTH:
            inner_frame = (x1, y1, w1, h1 + h2)
            del burnt_rects[i]
            break

    # Re-propagate fire to the updated list of burnt rectangles after expansion
    burnt_rects = propagate_fire(burnt_rects, inner_frame)

    return inner_frame, burnt_rects


def clean_results(drawing, info_blocks, inner_frame):
    """
    Cleans up the drawing and info blocks images by correcting misplaced text snippets.

    :param drawing: The drawing image.
    :param info_blocks: The information blocks image.
    :param inner_frame: A tuple (x, y, w, h) defining the coordinates and dimensions of the inner frame.

    :return: A tuple of two images:
        - cleaned_drawing: The drawing with extraneous contours and areas outside the inner frame removed
        - cleaned_info_blocks: The information blocks with unwanted contours removed.
    """
    binary_image = binarize(info_blocks)

    # Identify contours in the inverted binary info blocks image
    contours, hierarchy = cv2.findContours(cv2.bitwise_not(binary_image), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    cleaned_info_blocks = info_blocks.copy()
    text_mask = np.zeros_like(info_blocks)

    # Remove small top-level contours representing text snippets
    if hierarchy is not None:
        for i, h in enumerate(hierarchy[0]):
            if h[3] == -1 and cv2.contourArea(contours[i]) < MAX_CONTOUR_AREA:
                # Remove contours in cleaned info blocks and text mask for text snippet areas
                cv2.drawContours(cleaned_info_blocks, contours, i, 255, cv2.FILLED)
                cv2.drawContours(text_mask, contours, i, 255, cv2.FILLED)

    # Isolate and retain text snippets by masking areas marked in text_mask
    text = cv2.bitwise_and(info_blocks, info_blocks, mask=text_mask)
    cleaned_drawing = cv2.bitwise_or(drawing, text)

    # Create a mask to exclude areas outside the inner frame
    drawing_mask = np.ones_like(drawing, dtype=bool)
    x, y, w, h = inner_frame
    drawing_mask[y + LINE_WIDTH : y + h - LINE_WIDTH, x + LINE_WIDTH : x + w - LINE_WIDTH] = False

    # Apply the mask to set pixels outside the inner frame to white in the cleaned drawing
    cleaned_drawing[drawing_mask] = 255

    return cleaned_drawing, cleaned_info_blocks


def extract_results(image, inner_frame, burnt_rects):
    """
    Extract the drawing and information block images of an input image after the fire propagation algorithm.

    :param image: The input image from which drawing and information blocks are to be extracted.
    :param inner_frame: A tuple (x, y, w, h) representing the coordinates and dimensions of the inner frame.
    :param burnt_rects: A list of rectangles (tuples) representing information blocks that were burnt during
                        the fire propagation algorithm.

    :return: A tuple of four images:
        - cleaned_drawing: The drawing image with areas outside the inner frame and information blocks removed.
        - cleaned_info_blocks: The information blocks image, with unwanted text and contours removed.
        - info_blocks_mask: Boolean mask of the information blocks region within the image.
        - drawing_mask: Boolean mask of the drawing region within the image.
    """
    # inner_frame, burnt_rects = expand_inner_frame(inner_frame, burnt_rects)

    if len(inner_frame) == 0:
        return image, [], np.zeros_like(image), np.zeros_like(image)

    inner_frame = np.array(inner_frame)
    burnt_rects = np.array(burnt_rects)

    # Initialize a mask for the burnt rectangles (information blocks) inside the inner frame
    burnt_mask = np.zeros_like(image, dtype=bool)
    for rect in burnt_rects:
        x, y, w, h = rect
        _, _, inner_frame_w, inner_frame_h = inner_frame
        if w * h < inner_frame_w * inner_frame_h:
            burnt_mask[y - LINE_WIDTH : y + h + LINE_WIDTH, x - LINE_WIDTH : x + w + LINE_WIDTH] = True

    # Initialize mask for the main drawing to remove everything outside the inner frame
    drawing_mask = np.ones_like(image, dtype=bool)
    x, y, w, h = inner_frame
    drawing_mask[y + LINE_WIDTH : y + h - LINE_WIDTH, x + LINE_WIDTH : x + w - LINE_WIDTH] = False

    # Remove information blocks
    drawing_mask[burnt_mask] = True

    drawing = image.copy()
    drawing[drawing_mask] = 255

    # Prepare a mask for extracting the information blocks to include only burnt areas
    info_blocks_mask = np.ones_like(image, dtype=bool)
    info_blocks_mask[burnt_mask] = False

    info_blocks = image.copy()
    info_blocks[info_blocks_mask] = 255

    # Correct misplaced text snippets
    cleaned_drawing, cleaned_info_blocks = clean_results(drawing, info_blocks, inner_frame)

    return cleaned_drawing, cleaned_info_blocks, info_blocks_mask, drawing_mask


def remove_text_and_tables(drawing):
    """
    Remove text snippets and tables from the drawing image.
    This function processes the input drawing to eliminate unwanted textual and tabular elements.

    :param drawing: The input drawing image from which text and tables are to be removed.

    :return: The cleaned drawing image with text and tables removed.
    """
    binary_image = binarize(drawing)

    # Find contours in the thresholded image
    contours, hierarchy = cv2.findContours(cv2.bitwise_not(binary_image), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    cleaned_drawing = drawing.copy()

    # Remove text snippets and tables from drawing
    if hierarchy is not None:
        for i, h in enumerate(hierarchy[0]):
            # Only consider top-level contours
            if h[3] == -1:
                # Remove small text snippets
                if cv2.contourArea(contours[i]) < MAX_CONTOUR_AREA:
                    cv2.drawContours(cleaned_drawing, contours, i, 255, cv2.FILLED)
                # Remove rectangular areas
                elif cv2.contourArea(contours[i]) < MAX_RECT_AREA:
                    rect = cv2.boundingRect(contours[i])
                    if validate_rectangle(rect, binary_image):
                        cv2.drawContours(cleaned_drawing, contours, i, 255, cv2.FILLED)

    return cleaned_drawing


def separate(image):
    """
    Separate the drawing into its components.

    This function processes a standardized drawing image to identify and extract various elements,
    including the drawing, the information blocks, and a version of the drawing with text and tables removed.

    :param image: The standardized drawing image to be processed.

    :return: A tuple containing:
        - drawing: The drawing image.
        - info_blocks: An image of the extracted information blocks.
        - cleaned_drawing: The drawing image with text and tables removed.
        - burnt_rects (list): A list of rectangles representing cells of information blocks.
        - inner_frame (tuple): A tuple (x, y, w, h) representing the coordinates and dimensions of the inner frame.
        - info_blocks_mask: A mask indicating the areas of the information blocks.
        - drawing_mask: A mask indicating the areas of the original drawing.
    """
    rects = find_rectangles(image)
    inner_frame = find_inner_frame(image, rects)
    rects, inner_frame = handle_corner_cells(rects, inner_frame, image)
    burnt_rects = propagate_fire(rects, inner_frame)
    drawing, info_blocks, info_blocks_mask, drawing_mask = extract_results(image, inner_frame, burnt_rects)
    cleaned_drawing = remove_text_and_tables(drawing)

    return drawing, info_blocks, cleaned_drawing, burnt_rects, inner_frame, info_blocks_mask, drawing_mask
