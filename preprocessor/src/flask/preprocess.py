from datetime import datetime

import clip
import numpy as np

from src.flask.converter.image_std import convert_cv2_to_bytestring, load_and_standardize
from src.flask.converter.shape_extract import init_unet, remove_dimension_arrows_and_lines
from src.flask.converter.table_extract import separate
from src.flask.converter.utils import grayscale_to_rgb
from src.flask.ocr.context_merger import merge_text_in_image
from src.flask.ocr.extraction import extract
from src.flask.ocr.paddle_ocr_engine import OCREngine
from src.flask.ocr.vectorizer import vectorize_extraction
from src.flask.shapes.vectorizer import (
    choose_representative_embedding,
    generate_embedding_full_image,
    generate_embeddings,
)

# load the models
# ocr model
OCR_ENGINE = OCREngine()
# unet
UNET_PREDICTOR = init_unet()
# clip
CLIP_PREDICTOR = clip.load("ViT-B/32", device="cpu")


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


def apply_preprocessing(file_content, file_name, scale, embedding_type):
    """
    Applies the preprocessing steps to a file.
    Args:
        file_content: b64 encoded file content
        file_name: name of the file, used to check if pdf or image
        scale: int, what the image gets resized to. we usually use 2048
        embedding_type: string, either "colibri", "clip" or "both"

    Returns: dictionary with extracted features and timings

    """
    # =========
    # CONVERTER
    # =========
    # standardize image
    std_time, (std_img, original_img) = stopwatch(load_and_standardize, file_content, file_name, scale)
    if embedding_type == "clip" or embedding_type == "both":
        # =========
        #   CLIP
        # =========
        complete_clip_time, clip_vector = stopwatch(generate_embedding_full_image, std_img, CLIP_PREDICTOR)
    else:
        complete_clip_time = 0
        clip_vector = np.asarray([])

    if embedding_type == "colibri" or embedding_type == "both":
        # =========
        #   OCR
        # =========
        # make sure the ocr image is rgb, as paddle cant handle grayscale images
        ocr_time, (text_bbs, texts) = stopwatch(paddle_ocr, grayscale_to_rgb(std_img), OCR_ENGINE)

        # =========
        #   SEP
        # =========
        # separate into info block and drawing
        (
            sep_time,
            (drawing, info_block_img, cleaned_drawing, burnt_rects, inner_frame, info_blocks_mask, drawing_mask),
        ) = stopwatch(separate, std_img)

        # =========
        #  OCR PT2
        # =========
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
        # remove lines and arrows to get a cleaned image that can be given to CLIP
        remove_dim_arrows_time, shape_image = stopwatch(
            remove_dimension_arrows_and_lines, cleaned_drawing, unet=True, predictor=UNET_PREDICTOR
        )
        # generate CLIP embeddings from cleaned image
        emb_time, embeddings = stopwatch(generate_embeddings, shape_image, CLIP_PREDICTOR)
        # choose the most average embedding
        choose_rep_emb_time, shape_vector = stopwatch(choose_representative_embedding, embeddings)
    else:
        drawing_data = None
        ocr_vector = []
        shape_vector = np.asarray([])
        ocr_texts = []
        ocr_bbs = []
        text_classification = []
        sep_time = 0
        ocr_time = 0
        merge_time = 0
        extraction_time = 0
        vectorize_time = 0
        remove_dim_arrows_time = 0
        emb_time = 0
        choose_rep_emb_time = 0

    return {
        "drawing_data": drawing_data,
        "ocr_vector": list(ocr_vector),
        "shape_vector": shape_vector.tolist(),
        "original_drawing": convert_cv2_to_bytestring(std_img),
        "ocr_text": ocr_texts,
        "ocr_bbs": ocr_bbs,
        "ocr_classes": text_classification,
        "clip_vector": clip_vector.tolist(),
        "timings": {
            "std_time": std_time,
            "complete_clip_time": complete_clip_time,
            "sep_time": sep_time,
            "ocr_time": ocr_time,
            "merge_time": merge_time,
            "extraction_time": extraction_time,
            "vectorize_time": vectorize_time,
            "remove_dim_arrows_time": remove_dim_arrows_time,
            "emb_time": emb_time,
            "choose_rep_emb_time": choose_rep_emb_time,
        },
    }
