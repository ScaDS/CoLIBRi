from datetime import datetime

from preprocessor.src.flask.converter.image_rotation import (
    get_image_rotation,
    rotate_image_multiple_of_90,
    rotate_separation_outputs,
)
from preprocessor.src.flask.converter.image_std import convert_cv2_to_bytestring, load_and_standardize
from preprocessor.src.flask.converter.shape_extract import init_unet, remove_dimension_arrows_and_lines
from preprocessor.src.flask.converter.table_extract import separate
from preprocessor.src.flask.converter.utils import grayscale_to_rgb
from preprocessor.src.flask.ocr.context_merger import merge_text_in_image
from preprocessor.src.flask.ocr.extraction import extract
from preprocessor.src.flask.ocr.paddle_ocr_engine import OCREngine
from preprocessor.src.flask.ocr.vectorizer import vectorize_extraction
from preprocessor.src.flask.shapes.vectorizer import choose_representative_embedding, generate_embeddings


def stopwatch(func, *args, **kwargs):
    """
    Times to execution of a function.
    Args:
        func: the function to execute
        *args: arguments for the function
        **kwargs: keyword arguments for the function

    Returns: time in seconds, result of the function

    """
    start = datetime.now()
    result = func(*args, **kwargs)
    end = datetime.now()
    return (end - start).total_seconds(), result


def paddle_ocr(image, paddleocr_engine):
    """
    Helper function to be able to call stopwatch() on the text extraction.
    Args:
        image: image to extract text from
        paddleocr_engine: instance of OCREngine

    Returns: bounding boxes, texts

    """
    return paddleocr_engine.ocr(image)


def apply_preprocessing(file_content, file_name, scale):
    """
    Applies the preprocessing steps to a file.
    Args:
        file_content: b64 encoded file content
        file_name: name of the file, used to check if pdf or image
        scale: int, what the image gets resized to. we usually use 2048

    Returns: dictionary with extracted features and timings

    """
    # =========
    # CONVERTER
    # =========
    # standardize image
    std_time, (std_img, original_img) = stopwatch(load_and_standardize, file_content, file_name, scale)
    # separate into info block and drawing
    sep_time, (drawing, info_block_img, cleaned_drawing, burnt_rects, inner_frame, info_blocks_mask, drawing_mask) = (
        stopwatch(separate, std_img)
    )
    if len(info_block_img) > 0:  # if info block was found
        # fix image rotation if present
        get_rot_time, rotation = stopwatch(get_image_rotation, info_block_img)
        if rotation is not None and rotation != 0:
            rot_img_time, std_img = stopwatch(rotate_image_multiple_of_90, std_img, 360 - rotation)
            rot_sep_results_time, rotated_outputs = stopwatch(
                rotate_separation_outputs,
                drawing,
                info_block_img,
                cleaned_drawing,
                burnt_rects,
                inner_frame,
                info_blocks_mask,
                drawing_mask,
                360 - rotation,
            )
            (
                drawing,
                info_block_img,
                cleaned_drawing,
                burnt_rects,
                inner_frame,
                info_blocks_mask,
                drawing_mask,
            ) = rotated_outputs
        else:
            rot_img_time = 0
            rot_sep_results_time = 0
    else:
        get_rot_time = 0
        rot_img_time = 0
        rot_sep_results_time = 0

    # =========
    #   OCR
    # =========
    # init ocr model
    ocr_init_time, ocr_engine = stopwatch(OCREngine)
    # make sure the ocr image is rgb, as paddle cant handle grayscale images
    ocr_time, (text_bbs, texts) = stopwatch(paddle_ocr, grayscale_to_rgb(std_img), ocr_engine)
    # merge text into chunks, such as cells in a table or text blocks
    merge_time, [ocr_bbs, ocr_texts, is_texts] = stopwatch(
        merge_text_in_image, text_bbs, texts, [burnt_rects, inner_frame], [info_blocks_mask, drawing_mask]
    )
    # extract features from the text
    extraction_time, (drawing_data, text_classification) = stopwatch(extract, ocr_bbs, ocr_texts, is_texts)
    # convert features into a vector
    vectorize_time, ocr_vector = stopwatch(vectorize_extraction, drawing_data)

    # =========
    #   SHAPES
    # =========
    # init unet
    unet_init_time, predictor = stopwatch(init_unet)
    # remove lines and arrows to get a cleaned image that can be given to CLIP
    remove_dim_arrows_time, shape_image = stopwatch(
        remove_dimension_arrows_and_lines, cleaned_drawing, unet=True, predictor=predictor
    )
    # generate CLIP embeddings from cleaned image
    emb_time, embeddings = stopwatch(generate_embeddings, shape_image)
    # choose the most average embedding
    choose_rep_emb_time, shape_vector = stopwatch(choose_representative_embedding, embeddings)

    return {
        "drawing_data": drawing_data,
        "ocr_vector": list(ocr_vector),
        "shape_vector": shape_vector.tolist(),
        "original_drawing": convert_cv2_to_bytestring(std_img),
        "ocr_text": ocr_texts,
        "ocr_bbs": ocr_bbs,
        "ocr_classes": text_classification,
        "timings": {
            "std_time": std_time,
            "sep_time": sep_time,
            "get_rot_time": get_rot_time,
            "rot_img_time": rot_img_time,
            "rot_sep_results_time": rot_sep_results_time,
            "ocr_init_time": ocr_init_time,
            "ocr_time": ocr_time,
            "merge_time": merge_time,
            "extraction_time": extraction_time,
            "vectorize_time": vectorize_time,
            "unet_init_time": unet_init_time,
            "remove_dim_arrows_time": remove_dim_arrows_time,
            "emb_time": emb_time,
            "choose_rep_emb_time": choose_rep_emb_time,
        },
    }
