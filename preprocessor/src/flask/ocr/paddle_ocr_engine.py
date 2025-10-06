from importlib.resources import files

import numpy as np
import paddle
from paddleocr import PaddleOCR

import preprocessor.src.flask.ocr.resources.paddleocr_files as paddleocr_dir


class OCREngine:
    def __init__(self):
        """
        Class encapsulating a PaddleOCR engine instance
        :param device: "gpu" or "cpu"
        """
        self.ocr_engine = PaddleOCR(
            text_detection_model_dir=str(files(paddleocr_dir).joinpath("./PP-OCRv5_server_det/")),
            text_recognition_model_dir=str(files(paddleocr_dir).joinpath("./PP-OCRv5_server_rec/")),
            device="gpu" if paddle.is_compiled_with_cuda() else "cpu",
            use_doc_unwarping=False,
            use_doc_orientation_classify=False,
        )

    def ocr(self, image):
        """
        uses the instance of the model to ocr an image.
        :param image: image to apply ocr to
        return: list of bbs [x,y,w,h] and a list of corresponding recognized texts
        """
        result = self.ocr_engine.predict(image)[0]  # always first page

        # get polygons, which are represented as four points
        res_bbs = result["dt_polys"]
        # convert them to [x, y, w, h]
        converted_bbs = []
        for bb in res_bbs:
            bb = np.asarray(bb)

            # get the x, y vals from each point
            x_vals = bb[:, 0]
            y_vals = bb[:, 1]

            # get the min and max values
            # make sure to convert to int, so that the values are json serializable
            xmin = int(x_vals.min())
            xmax = int(x_vals.max())

            ymin = int(y_vals.min())
            ymax = int(y_vals.max())

            # calculate the result
            converted_bbs.append([xmin, ymin, xmax - xmin, ymax - ymin])

        texts = result["rec_texts"]
        return converted_bbs, texts
