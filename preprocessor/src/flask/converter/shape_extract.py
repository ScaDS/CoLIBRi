import math
import os

import cv2
import numpy as np
import torch
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
from skimage.feature import blob_log

from src.flask.converter.consts import LINE_WIDTH, MAX_CONTOUR_AREA, MAX_RECT_AREA, MIN_TRI_INTER_RATIO
from src.flask.converter.table_extract import validate_rectangle
from src.flask.converter.utils import binarize, create_mask, find_contours, get_cropped_views


def validate_line(coords, other_coords, image):
    """
    Validates if a line between two coordinate points overlaps with black pixels in the (binarized) image.

    :param coords: Tuple (x, y) for the starting point of the line
    :param other_coords: Tuple (other_x, other_y) for the ending point of the line
    :param image: Original image (cv2 image) where the line validation occurs
    :return: Boolean value indicating if the line is fully clear of foreground
             content (True) or intersects with it (False)
    """
    line_mask = np.zeros_like(image)
    (
        x,
        y,
    ) = coords
    (
        other_x,
        other_y,
    ) = other_coords
    cv2.line(line_mask, (int(y), int(x)), (int(other_y), int(other_x)), 255, 1)

    binary_image = binarize(image)

    intersection = cv2.bitwise_and(cv2.bitwise_not(binary_image), line_mask)
    intersection_ratio = np.sum(intersection) / np.sum(line_mask)

    return intersection_ratio >= 1


def remove_text_and_tables(drawing):
    """
    Removes small contours, such as text snippets and table structures, from an image

    :param drawing: Original drawing image from which text and tables will be removed
    :return: Modified drawing image with text and tables removed
    """
    # Binarize the image
    binary_image = binarize(drawing)

    # Find contours in the binary image and return the contour hierarchy
    contours, hierarchy = find_contours(binary_image, return_hierarchy=True)

    # Remove text snippets and tables from drawing
    if hierarchy is not None:
        for i, h in enumerate(hierarchy[0]):
            # Process top-level contours
            if h[3] == -1:
                contour_area = cv2.contourArea(contours[i])

                # Remove small contours classified as text
                if contour_area < MAX_CONTOUR_AREA:
                    cv2.drawContours(drawing, contours, i, 255, cv2.FILLED)

                # Remove larger rectangles classified as tables
                elif contour_area < MAX_RECT_AREA:
                    rect = cv2.boundingRect(contours[i])
                    if validate_rectangle(rect, binary_image, threshold=MIN_TRI_INTER_RATIO):
                        cv2.drawContours(drawing, contours, i, 255, cv2.FILLED)

    return drawing


def remove_dimension_arrows_and_lines(drawing, remove_gdt=True, unet=False, predictor=None):
    """
    Removes dimension arrows, lines, and optionally GD&T text and tables from an image.
    If `unet` is set to True, a custom trained UNet is used for the removal process, otherwise a CV-based approach.

    :param drawing: Drawing image containing dimensions and annotations
    :param remove_gdt: Boolean indicating if GD&T text and tables should be removed (default: True)
    :param unet: Boolean indicating if UNet-based processing should be applied (default: False)
    :return: Processed image with dimension arrows, lines, and optionally GD&T elements removed
    """
    if unet:
        return view_wise_apply_unet(drawing, predictor)

    arrows_mask = np.zeros_like(drawing)

    # Process each view individually for optimized execution
    for view in get_cropped_views(drawing):
        # Detect blobs representing arrowheads
        blobs = blob_log(cv2.bitwise_not(view.image), min_sigma=2, max_sigma=16, num_sigma=14, threshold=0.5, overlap=0)

        arrows = []

        # Detect arrows by identifying straight lines between detected blobs
        for i, blob in enumerate(blobs):
            x, y, area = blob

            for other_blob in blobs[i + 1 :]:
                other_x, other_y, other_area = other_blob

                if validate_line((x, y), (other_x, other_y), view.image):
                    new_x = view.y + x
                    new_y = view.x + y
                    new_other_x = view.y + other_x
                    new_other_y = view.x + other_y

                    # Draw arrowheads on the mask
                    cv2.circle(arrows_mask, (int(new_y), int(new_x)), int(area * np.sqrt(2)) + LINE_WIDTH, 255, -1)
                    cv2.circle(
                        arrows_mask, (int(new_other_y), int(new_other_x)), int(area * np.sqrt(2)) + LINE_WIDTH, 255, -1
                    )

                    arrows.append(
                        (
                            int(new_y),
                            int(new_x),
                            int(new_other_y),
                            int(new_other_x),
                            int(area * np.sqrt(2)) + LINE_WIDTH,
                        )
                    )

        # Analyse arrows to exclude arrows inside of parts from mask
        horizontal_arrows = []
        horizontal_y_values = []

        vertical_arrows = []
        vertical_x_values = []

        # Classify arrows based on orientation (horizontal or vertical)
        for arrow in arrows:
            y1, x1, y2, x2, thickness = arrow

            angle = math.degrees(math.atan2((x1 - x2), (y1 - y2))) % 360
            limit = 5
            if (not limit < angle <= 360 - limit) or (180 - limit <= angle < 180 + limit):
                horizontal_arrows.append(arrow)
                horizontal_y_values += [y1, y2]
            elif (90 - limit < angle < 90 + limit) or (270 - limit < angle < 270 + limit):
                vertical_arrows.append(arrow)
                vertical_x_values += [x1, x2]

        # Determine bounds for vertical and horizontal arrows
        if len(vertical_arrows) > 0:
            min_x = min(vertical_x_values)
            max_x = max(vertical_x_values)
        else:
            min_x = float("inf")
            max_x = 0

        if len(horizontal_arrows) > 0:
            min_y = min(horizontal_y_values)
            max_y = max(horizontal_y_values)
        else:
            min_y = float("inf")
            max_y = 0

        def scale_line(x1, x2, y1, y2):
            line_length = np.sqrt(abs(x1 - x2) ** 2 + abs(y1 - y2) ** 2)
            new_line_length = line_length + 30
            scale_factor = new_line_length / line_length

            new_x1 = int(x1 * (1 + scale_factor) / 2 + x2 * (1 - scale_factor) / 2)
            new_y1 = int(y1 * (1 + scale_factor) / 2 + y2 * (1 - scale_factor) / 2)
            new_x2 = int(x2 * (1 + scale_factor) / 2 + x1 * (1 - scale_factor) / 2)
            new_y2 = int(y2 * (1 + scale_factor) / 2 + y1 * (1 - scale_factor) / 2)

            return new_x1, new_y1, new_x2, new_y2

        def process_arrows(arrows, min_val, max_val, is_horizontal):
            for arrow in arrows:
                y1, x1, y2, x2, thickness = arrow

                if is_horizontal:
                    val_1, val_2 = x1, x2
                else:
                    val_1, val_2 = y1, y2

                if not (min_val <= val_1 <= max_val or min_val <= val_2 <= max_val):
                    new_x1, new_y1, new_x2, new_y2 = scale_line(x1, x2, y1, y2)
                    cv2.line(arrows_mask, (new_y1, new_x1), (new_y2, new_x2), 255, thickness)

        process_arrows(horizontal_arrows, min_x, max_x, is_horizontal=True)
        process_arrows(vertical_arrows, min_y, max_y, is_horizontal=False)

    # Remove arrows
    intersection = cv2.bitwise_and(cv2.bitwise_not(drawing), arrows_mask)
    arrows_image = cv2.bitwise_not(intersection)

    image_without_arrows = cv2.bitwise_not(cv2.absdiff(drawing, arrows_image))

    # Apply flood fill to remove remaining dimension lines
    mask = create_mask(image_without_arrows)
    mask = cv2.bitwise_not(mask)

    image_without_outer_lines = cv2.bitwise_or(drawing, mask)

    if not remove_gdt:
        return image_without_outer_lines

    # Optionally further clean the drawing by removing GD&T (top-level text and tables after removing dimension lines)
    cleaned_drawing = remove_text_and_tables(image_without_outer_lines)

    biggest_components_image = np.ones_like(cleaned_drawing) * 255

    # Keep only the largest components in each view
    for view in get_cropped_views(drawing):
        view_h, view_w = view.image.shape[:2]
        cleaned_view_image = cleaned_drawing[view.y : view.y + view_h + 1, view.x : view.x + view_w + 1]

        components = get_cropped_views(cleaned_view_image)

        if len(components) > 0:
            component = components[0]
            component_h, component_w = component.image.shape[:2]

            for y in range(view.y + component.y, view.y + component.y + component_h):
                for x in range(view.x + component.x, view.x + component.x + component_w):
                    biggest_components_image[y][x] = cleaned_drawing[y][x]

    # Final cleaning step to remove residual text and tables
    biggest_components_image = remove_text_and_tables(biggest_components_image)

    return biggest_components_image


def init_unet():
    # Load and prepare UNet model for predictions
    current_dir = os.path.dirname(__file__)
    nnUNet_results = os.path.join(current_dir, "resources/nnUNet_results")

    device = "cuda" if torch.cuda.is_available() else "cpu"

    predictor = nnUNetPredictor(
        tile_step_size=0.5,
        use_gaussian=True,
        use_mirroring=False,
        perform_everything_on_device=True,
        device=torch.device(device),
        verbose=False,
        verbose_preprocessing=False,
        allow_tqdm=True,
    )

    predictor.initialize_from_trained_model_folder(
        os.path.join(nnUNet_results, "Dataset001_ViewSegmentation/nnUNetTrainer__nnUNetPlans__2d"),
        use_folds=["all"],
        checkpoint_name="checkpoint_final.pth",
    )

    return predictor


def view_wise_apply_unet(drawing, predictor):
    """
    Applies a custom trained UNet model to each view in the image for segmentation-based
    removal of dimension arrows and lines.

    :param drawing: Drawing image containing dimensions and annotations
    :return: Processed image with dimension arrows, lines, and optionally GD&T elements removed
    """
    shape_image = np.ones_like(drawing) * 255

    for view in get_cropped_views(drawing):
        x, y = view.x, view.y
        w, h = view.image.shape

        # Leave 3D models unchanged
        from src.flask.converter.thumb_gen import is_3d_model

        if is_3d_model(view.image):
            clean_view = view.image

        else:
            # Calculate new dimensions capped at 512 pixels
            new_w = min(w, 512)
            new_h = min(h, 512)

            # Resize the image with aspect ratio preserved
            if h > w:
                scale = new_h / h
                new_w = int(w * scale)
            else:
                scale = new_w / w
                new_h = int(h * scale)

            resized_image = cv2.resize(view.image, (new_h, new_w), interpolation=cv2.INTER_AREA)

            # Prepare the image for UNet processing
            img = cv2.cvtColor(resized_image, cv2.COLOR_GRAY2RGB)
            img = np.moveaxis(img, -1, 0)
            img = img[:, np.newaxis, ...]
            img = img.astype(np.float32) / 255.0

            props = {"spacing": (999, 1, 1)}

            # Perform inference of the UNet model
            ret = predictor.predict_single_npy_array(img, props, None, None, False)
            prediction = np.squeeze(ret, axis=0)

            # Convert to cv2 image format
            clean_view = prediction.astype(np.uint8)
            clean_view[clean_view < 1.5] = 0
            clean_view[clean_view > 1.5] = 255
            clean_view = cv2.bitwise_not(clean_view)

            # Resize the image back to the original dimensions
            clean_view = cv2.resize(clean_view, (h, w), interpolation=cv2.INTER_LINEAR)

        # Merge cleand view into drawing
        temp_image = np.ones_like(shape_image) * 255
        temp_image[y : y + w, x : x + h] = clean_view
        shape_image = cv2.bitwise_and(shape_image, temp_image)

    # Remove remaining text and tables (GD&T)
    shape_image = remove_text_and_tables(shape_image)

    return shape_image
