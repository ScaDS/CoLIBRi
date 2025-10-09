import os
import shutil
import sys
import numpy as np
from gen_complete_technical_drawings import TechDrawGenerator
import random
from gen_3d_views import View3DGenerator
from helpers import *
from data_gen.gen_table_rec_data import load_data
import json

def jitter_image(xmin, ymin, W, H):
    max_y_jitter = int(round(H*0.1))
    max_x_jitter = int(round(W*0.1))
    return  [xmin + random.choice(range(-max_x_jitter, max_x_jitter)),
             ymin + random.choice(range(-max_y_jitter, max_y_jitter)),
             xmin + W + random.choice(range(-max_x_jitter, max_x_jitter)),
             ymin + H + random.choice(range(-max_y_jitter, max_y_jitter))]

new_base_path = "../data/generated_rec_data"
os.makedirs(new_base_path, exist_ok=True)

token_path = sys.argv[4] if len(sys.argv) > 4 else "../resources/pickle/dictionary.pickle"
norm_path = sys.argv[5] if len(sys.argv) > 5 else "../resources/pickle/common_norms.pkl"
material_path = sys.argv[6] if len(sys.argv) > 6 else "../resources/pickle/materials.pkl"
models_path = sys.argv[7] if len(sys.argv) > 7 else "../resources/3d_models"
# load all the pickled data
tokens, norms, materials, materials_flat = load_data(token_path, norm_path, material_path)
view_gen = View3DGenerator(models_path)
draw_gen = TechDrawGenerator(tokens, norms, materials_flat,view_gen, base_font_path="../resources/fonts")

# TRAINING HAS SAME IMAGES, BUT GETS EXPANDED
train_image_dir = os.path.join(new_base_path, "train")
os.makedirs(train_image_dir, exist_ok=True)

num_new_images = 0
target_num = 100000

data_dict_train = {
  "metainfo": {
      "dataset_type": "TextRecogDataset",
      "task_name": "textrecog"
  },
  "data_list": []
}

while num_new_images < target_num:
    print(num_new_images, " / ", target_num)
    # generate whole drawing
    img, texts = next(draw_gen)
    for text in texts:
        if text[0] is not None and (text[2] == "measure" or text[2] == "surface"):
            [xmin, ymin, W, H] = text[1]
            xmin = int(xmin)
            ymin = int(ymin)
            W = int(W)
            H = int(H)
            img_dict = {
                "instances": [
                    {"text": text[0]}
                ],
                "img_path": f"./train/{num_new_images}.png"
            }
            # save that image
            crop = img.crop(box=jitter_image(xmin, ymin, W, H))
            crop.save(os.path.join(train_image_dir, f"{num_new_images}.png"))
            num_new_images += 1

            data_dict_train["data_list"].append(img_dict)
# save both json files
with open(os.path.join(new_base_path, 'train.json'), 'w', encoding='utf-8') as f:
    json.dump(data_dict_train, f, ensure_ascii=True, indent=4)