import cv2
import numpy as np

from preprocessor.src.flask.converter.consts import LINE_WIDTH
from preprocessor.src.flask.converter.shape_extract import remove_dimension_arrows_and_lines, remove_text_and_tables
from preprocessor.src.flask.converter.table_extract import validate_rectangle
from preprocessor.src.flask.converter.utils import View, binarize, create_mask, find_contours, get_cropped_views
from preprocessor.src.flask.shapes.vectorizer import choose_representative_embedding, generate_embeddings


def get_representative_view(shape_image, most_representative_idx):
    """
    Retrieve the most representative view from the segmented shape views.

    param shape_image: Shape image with segmented views.
    param most_representative_idx: Index of the most representative view.

    return: Cropped image of the most representative shape view.
    """
    # Handle empty shape_image
    if most_representative_idx is None:
        return shape_image

    shape_view = get_cropped_views(shape_image)[most_representative_idx]

    return shape_view.image


def rotate_bound(image, angle):
    """
    Rotate an image by a given angle while keeping all pixels within the frame.

    param image: Input image to be rotated.
    param angle: Angle in degrees to rotate the image counterclockwise.

    return: Rotated image with adjusted boundaries to include all original content.
    """
    (h, w) = image.shape[:2]
    (cx, cy) = (w // 2, h // 2)

    m = cv2.getRotationMatrix2D((cx, cy), -angle, 1.0)
    cos = np.abs(m[0, 0])
    sin = np.abs(m[0, 1])

    nw = int((h * sin) + (w * cos))
    nh = int((h * cos) + (w * sin))

    m[0, 2] += (nw / 2) - cx
    m[1, 2] += (nh / 2) - cy

    return cv2.warpAffine(image, m, (nw, nh), borderValue=255)


def pad_image(image):
    """
    Add a white border around an image.

    param image: Input image to be padded.

    return: Padded image with an added white border of 256 pixels on each side.
    """
    border_size = 256

    height, width = image.shape[:2]

    padded_image = np.zeros((height + 2 * border_size, width + 2 * border_size), dtype=np.uint8)
    padded_image[:, :] = 255
    padded_image[border_size : border_size + height, border_size : border_size + width] = image

    return padded_image


def is_stadium(view_image):
    """
    Determine whether a given view image resembles a stadium structure based on contour and rectangle validation.

    param view_image: Input view image to be evaluated as a potential stadium shape.

    return: Boolean indicating whether the view image resembles a stadium structure.
    """
    view_image = pad_image(view_image)
    binary_image = binarize(view_image)
    contours = find_contours(binary_image)

    if len(contours) == 0:
        return False

    rect = cv2.minAreaRect(contours[0])

    # Handle rotation
    angle = rect[2]
    rotated_view_image = rotate_bound(view_image, angle)
    binary_image = binarize(rotated_view_image)
    contours, hierarchy = find_contours(binary_image, return_hierarchy=True)
    rect = cv2.boundingRect(contours[0])

    # Check if shape approximately resembles a rectangle
    if validate_rectangle(rect, binary_image, threshold=0.5):
        # Process each top-level contour
        for i, contour in enumerate(contours):
            if hierarchy[0][i][3] == -1:
                # Gather areas for child contours of the top-level contour (boundary of the potential stadium)
                areas = []

                for j, child_index in enumerate(hierarchy[0]):
                    if child_index[3] == i:
                        area = cv2.contourArea(contours[j])
                        areas.append((area, j))

                areas.sort(key=lambda x: x[0], reverse=True)

                # Check if all child contours are small (likely text)
                for _, index in areas[1:]:
                    if cv2.contourArea(contours[index]) > 0.1 * cv2.contourArea(contour):
                        return False

        return True

    return False


def is_3d_model(view_image):
    """
    Determine whether a given view image represents a 3D model (rendered or wireframe).

    param view_image: Input view image to evaluate as a potential 3D model.
    return: Boolean indicating whether the view image is likely a 3D model.
    """
    # Check if view image resembles rendered 3D model
    mask = create_mask(view_image, keep_borders=False)
    mask_pixels = cv2.countNonZero(mask)

    if mask_pixels == 0:
        return False

    masked_image = cv2.bitwise_or(view_image, cv2.bitwise_not(mask))
    binary_image = binarize(masked_image)
    dark_pixels = cv2.countNonZero(cv2.bitwise_not(binary_image))

    # Calculate the dark-to-total pixel ratio; high ratios suggest a 3D model
    ratio = dark_pixels / mask_pixels

    if ratio > 0.75:
        return True

    # Check if view image resembles wireframe 3D model
    cleaned_view_image = remove_dimension_arrows_and_lines(view_image)

    # Calculate difference between original image and image with dimension arrows and lines removed
    difference = cv2.bitwise_or(cv2.bitwise_not(cleaned_view_image), view_image)

    binary_image = cv2.bitwise_not(binarize(difference))
    different_pixels = cv2.countNonZero(binary_image)

    # Check if difference is low (no dimensioning) and the view is not a stadium (likely a wireframe 3D model)
    if different_pixels < LINE_WIDTH**2 and not is_stadium(view_image):
        binary_image = binarize(pad_image(view_image))
        contours = find_contours(binary_image)

        return len(contours) != 0

    return False


def create_thumbnail(image, drawing, info_blocks, cleaned_drawing, shape_image, burnt_rects):
    """
    Generate a thumbnail by extracting a 3D model view from the image or cropping the drawing if no 3D model is found.

    param image: The original input image from which the thumbnail is to be created.
    param drawing: The drawing image.
    param info_blocks: The information blocks image.
    param cleaned_drawing: The drawing with text and tables removed.
    param shape_image: Processed image with dimension arrows and lines removed.
    param burnt_rects: List of burnt rectangles (information blocks) from fire propagation.
    return: Extracted 3D model view or a cropped drawing if no 3D model is found.
    """
    cleaned_drawing = remove_text_and_tables(cleaned_drawing)

    # Search 3d model in drawing
    opened_image = cleaned_drawing.copy()
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    for _ in range(LINE_WIDTH + 1):
        opened_image = cv2.erode(opened_image, kernel)
    for _ in range(LINE_WIDTH + 1):
        opened_image = cv2.dilate(opened_image, kernel)

    opened_views = get_cropped_views(opened_image)
    views = []

    for view in opened_views:
        h, w = view.image.shape
        cleaned_view_image = image[view.y : view.y + h + 1, view.x : view.x + w + 1]
        main_view = get_cropped_views(cleaned_view_image)[0]

        views.append(View(main_view.image, view.x + main_view.x, view.y + main_view.y))

    if len(views) > 0 and not np.array_equal(image, drawing):
        for view in views:
            if is_3d_model(view.image):
                return view.image

    # Search 3d model in information blocks
    for rect in burnt_rects:
        x, y, w, h = rect
        view_image = info_blocks[y + LINE_WIDTH : y + h - LINE_WIDTH, x + LINE_WIDTH : x + w - LINE_WIDTH].copy()
        if min(view_image.shape[:2]) > 0:
            view_image = remove_text_and_tables(view_image)
            non_white_pixels = np.argwhere(view_image < 255)
            x, y, w, h = cv2.boundingRect(non_white_pixels)
            view_image = view_image[x : x + w, y : y + h]

            if min(view_image.shape[:2]) > 0 and is_3d_model(view_image):
                return view_image

    # If no 3d model is found return representative view
    embeddings = generate_embeddings(shape_image)
    idx = choose_representative_embedding(embeddings, return_index=True)
    representative_view = get_representative_view(shape_image, idx)

    return representative_view
