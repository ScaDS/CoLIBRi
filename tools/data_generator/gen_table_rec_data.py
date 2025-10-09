import os
import string
import sys
from helpers import *
import numpy as np
import pandas as pd
import random
import string
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import matplotlib.pyplot as plt
import json
from perlin_noise import PerlinNoise
import time

class TechDrawMeasurementGenerator(object):
    def __init__(self):
        '''
        Class to generate random measurements (that look like they can be) used in technical drawings.
        '''
        pass
    def __iter__(self):
        return self
    # Python 3 compatibility
    def __next__(self):
        '''
        Calls the .next() function.
        '''
        return self.next()
    @staticmethod
    def random_float(min, max, gauss = True):
        '''
        Generates a random float in range [min, max]. If gauss sample from gaussian, else equal distribution
        :param min: Minimum
        :param max: Maximum
        :param gauss: Whether to sample from gaussian
        :return: A random float.
        '''
        if gauss:
            #random float from gauss
            nr = random.gauss(mu=min, sigma = max) % max
            #round to reasonable amount of digits
            digits = random.randint(1,3)
            nr *= 10**digits
            nr = round(nr)
            nr /= 10**digits
        else:
            nr = random.randint(min, max)
            nr /= 10**random.randint(0,len(str(nr)))
        return nr

    def next(self):
        '''
        Generates random text that might show up in technical drawings in order to train a character recognizer.
        Text could be:
            * Random smaller 0 <= float <= 3 and a random prefix of "R", "Ra ", "Rz ", "+", "-", "±"
            * Random bigger 0 <= float <= 90 and a random prefix of "R", "Ra ", "Rz ", "+", "-", "±" and sometimes postfix of °
            * Random Integer <= 9999 and a random prefix of "R", "+", "-", "±" and sometimes postfix of °
            * Random Phrases with 1 - 4 words
            * Random Char
            * Random Char + Random Int
            * Random Int + ":" + Random Int
            * G + Random Int + "/" + Random Int
            * DIN + numbers-string
            * ISO + numbers-string
        '''
        text = " " # empty text.
        template = abs(int(random.gauss(mu=0, sigma=4)))%5
        #smaller floats
        if template == 0:
            #random float
            f = random.random() * 3
            #random number of digits
            digits = random.randint(1,3)
            f *= 10**digits
            f = round(f)
            f /= 10**digits
            text = str(f)
            #add random prefix
            prefix = random.choice([""] * 10 +["R", "Ra ", "Rz ", "+", "-", "±"])
            text = prefix + text
        #bigger floats
        elif template == 1:
            #random float
            text = str(self.random_float(0, 90))
            #random prefix
            prefix = random.choice([""] * 10 +["R", "Ra ", "Rz ", "+", "-", "±"])
            text = prefix + text
            #random ° at the end
            if random.random() > 0.9:
                text = text + "°"
        # integers
        elif template == 2:
            #generate random digits
            text = str(random.randint(0, 9))
            j = 1
            # 50% chance to append a new integer
            while random.random() < 0.5 and j < 4:
                nr = random.randint(0, 9)
                text += str(nr)
                j += 1
            #postfix
            if random.random() > 0.9:
                text = text + "°"
            #prefixes
            prefix = random.choice([""] * 10 +["R", "+", "-", "±"])
            text = prefix + text
        #chars
        elif template == 3:
            text = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        # char + int, x:x, Gx/x
        elif template == 4:
            secondary_template = random.choice(["CharInt","scale","threads"])
            if secondary_template == "CharInt":
                text = random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNOPQRSTUVWXYZ")
                text += random.choice("0123456789")
            elif secondary_template == "scale":
                text = random.choice("123456789")
                text += ":"
                text += random.choice("123456789")
            elif secondary_template == "threads":
                text = "G"
                text += random.choice("123456789")
                text += "/"
                text += random.choice("123456789")
        return text


class TextGenerator(object):
    def __init__(self, dictionary, norms, materials, probabilities=[0.4,0.55,0.7,0.8,0.9]):
        '''
        Implements a generator for text used in information blocks in technical drawings.
        :param dictionary: words to use for the generator
        :param norms: names of the norms to use in the generator
        :param materials: names of the materials to use in the generator
        :param probabilities: cumulative probabilities for choosing: word, norm, material, measurement, date, sequence
        '''
        self.dictionary = dictionary
        self.norms = norms
        self.materials = materials
        self.measurement_gen = TechDrawMeasurementGenerator()
        self.probabilities = probabilities
    def __iter__(self):
        return self
    # Python 3 compatibility
    def __next__(self):
        '''
        Calls the .next() function.
        '''
        return self.next()

    def generate_random_word(self):
        '''
        Generates a random word by randomly sampling self.dictionary
        :return: A randomly generated word.
        '''
        #no word found yet
        return random.choice(self.dictionary)

    def generate_random_norm(self):
        '''
        Generates a random norm by randomly sampling self.norms
        :return: A randomly generated norm.
        '''
        return random.choice(self.norms)

    def generate_random_material(self):
        '''
        Generates a random material by randomly sampling self.materials
        :return: A randomly generated material.
        '''
        return random.choice(self.materials)

    def generate_random_date(self):
        '''
        Generates a random date in either ANSI or ISO format.
        :return: Random date string
        '''

        # random day, month, year
        day = str(random.choice(list(range(1,32))))
        month = str(random.choice(list(range(1,13))))
        year = str(random.choice(list(range(1980,2030))))

        # randomly add 0 if only one digit
        if int(day) < 10 and random.choice([True, False]):
            day += "0"

        if int(month) < 10 and random.choice([True, False]):
            month += "0"

        # randomly cutoff year to last 2 digits
        if random.choice([True, False]):
            year = year[2:]

        # choose from 2 formats
        if random.choice([True, False]):
            date = day + "." + month + "." + year
        else:
            date = year + "-" + month + "-" + day

        return date

    def generate_gibberish_number_char_seq(self):
        '''
        Generates a random string of numbers, capital letters and some special chars == ".-:_></()"
        :return: random string
        '''

        all_chars = string.ascii_uppercase + "0123456789" * 10 + ".-:_></"

        text = random.choice(all_chars)

        while random.random() < 0.75:
            text += random.choice(all_chars)

        if random.random() > 0.9 and len(text) > 5:
            # insert () randomly
            start = random.randint(0, len(text)-1)
            end = start
            while end == start: # while they are the same, search new end
                end = random.randint(0, len(text)-1)

            text = text[:start] + "(" + text[start:]
            text = text[:end + 1] + ")" + text[end + 1:] # +1 since char was inserted above

        return text

    def next(self):
        '''
        Generates a random word that might be present in the information block of a technical drawing
        :return: random word
        '''
        r = random.random()

        if r < self.probabilities[0]:
            text = self.generate_random_word()
        elif r < self.probabilities[1]:
            text = self.generate_random_norm()
        elif r < self.probabilities[2]:
            text = self.generate_random_material()
        elif r < self.probabilities[3]:
            text = next(self.measurement_gen)
        elif r < self.probabilities[4]:
            text = self.generate_random_date()
        else:
            text = self.generate_gibberish_number_char_seq()
        return text


class ImagePairGenerator(object):
    def __init__(self, tokens, norms, materials, base_font_path="../resources/fonts/", add_noise = True, probabilities= [0.4,0.55,0.7,0.8,0.9]):
        '''
        Generates a random word (or bigram of words) and creates an image using that word and one of 4 Fonts:
        * Arial
        * usicpeui
        * osifont
        * seguisym
        Also randomly applies transformations to the image:
        * randomly shifts the borders
        * stretches the image horizontally
        * applies salt and pepper noise (5% and 2% chance each)
        * applies perlin noise to the background (5% chance)
        * applies smoothing to the image (40% chance)
        :param tokens: list of words to give to the text generator
        :param norms: list of norms to give the text generator
        :param materials: list of materials to give the text generator
        :param probabilities: cumulative probabilities for choosing: word, norm, material, measurement, date, sequence
        '''
        self.text_gen = TextGenerator(tokens, norms, materials, probabilities)
        self.fonts_paths = []
        self.extended_fonts_paths = []
        self.add_noise = add_noise
        for font in os.listdir(base_font_path):
            if not "GDT" in font and not "Bungee" in font:
                self.fonts_paths.append(os.path.join(base_font_path, font))
                self.extended_fonts_paths.append(os.path.join(base_font_path, font))
            elif not "GDT" in font:
                self.extended_fonts_paths.append(os.path.join(base_font_path, font))
    def __iter__(self):
        return self
    # Python 3 compatibility
    def __next__(self):
        '''
        Calls the .next() function. Does not support exact font sizes.
        '''
        return self.next()

    @staticmethod
    def salt(image: Image, probability, rgb = False):
        '''
        Randomly sets (prob * amount of pixels) pixels in image to 255
        :param image: PIL image
        :param probability: chance that a given pixel will be set to 255
        :param rgb: image mode, either puts 3d or 1d color in chosen pixel
        :return: transformed PIL image
        '''
        out_image = image.copy()
        w, h = image.size
        n_pixels = int(w * h * probability)

        for _ in range(n_pixels): # salt
            out_image.putpixel([random.randint(0,w-1), random.randint(0, h-1)], (255,255,255) if rgb else 255)

        return out_image

    @staticmethod
    def pepper(image: Image, probability, rgb = False):
        '''
        Randomly sets (prob * amount of pixels) pixels in image to a random value between 0 and 80
        :param image: PIL image
        :param probability: chance that a given pixel will be set to a random value between 0 and 80
        :param rgb: image mode, either puts 3d or 1d color in chosen pixel
        :return: transformed PIL image
        '''
        out_image = image.copy()
        w, h = image.size
        n_pixels = int(w * h * probability)
        for _ in range(n_pixels): # pepper
            color = random.randint(0, 80)
            out_image.putpixel([random.randint(0,w-1), random.randint(0, h-1)], (color, color, color) if rgb else color)

        return out_image

    @staticmethod
    def random_borders(image, max_offset_factor = 0.15, random_range_factor = 1.5):
        '''
        Randomly pads / cuts of the image on each side. How much depends on the size of the image in that dimensions.
        :param image: PIL image to offset
        :param max_offset_factor: used to calculate the maximum possible offset in this dimension. The image is first expanded on each side by this value.
        :param random_range_factor: After the expansion using max_offset_factor, the image is then reduced by a random amount. This maximum is calculated using this factor. If > 1 this reduction can be greater than the expansion.
        :return: transformed PIL image
        '''
        w,h = image.size

        # expand image
        offset_x = int(w * max_offset_factor)
        offset_y = int(h * max_offset_factor)

        np_image = np.asarray(image)
        np_image = np.pad(np_image, [(offset_y, offset_y), (offset_x, offset_x)], 'constant', constant_values=(255,255))

        # reduce image by a (potentially larger factor)

        left = random.randint(0, int(offset_x * random_range_factor))
        right = random.randint(0, int(offset_x * random_range_factor))
        top = random.randint(0, int(offset_y * random_range_factor))
        bottom = random.randint(0, int(offset_y * random_range_factor))
        np_image = np_image[top:np_image.shape[0]-bottom, left:np_image.shape[1]-right]

        return Image.fromarray(np_image)

    @staticmethod
    def get_random_font_size(sigma=6, min=10, max = 45):
        '''
        Randomly samples a gaussian distribution with mu and sigma. Tries until it gets a value within [min, max]
        :return: Value between min, max
        '''
        mu = (max + min)/2
        found = False
        while not found:
            size = int(random.gauss(mu,sigma))
            if min < size < max:
                return size

    @staticmethod
    def add_perlin_noise(image: Image, downsample_size = None, alpha = 0.1):
        '''
        Adds perlin noise to an image.
        :param image: PIL image
        :param downsample_size: if None, use image size to sample perlin noise (depending on size this could take a while). if not None, sample with this size and upsacle to image size later
        :param alpha: alpha for image blending
        :return: PIL image
        '''
        if downsample_size is not None:
            width, height = downsample_size
        else:
            width, height = image.size
        noise = PerlinNoise(octaves=4, seed=random.randint(1, 10000))
        noise_img = [[noise([i / width, j / height]) for j in range(height)] for i in range(width)]
        noise_img = Image.fromarray(np.array(noise_img) * 255).convert('L').transpose(Image.ROTATE_90)
        if downsample_size is not None:
            noise_img = noise_img.resize(image.size)
        noise_img = noise_img.convert(image.mode)
        image = Image.blend(image, noise_img, alpha=alpha)
        return image
    def next(self, font_size=None, font_path = None, stretch_factor = None, extra_kerning = 0, text_color = (0,0,0), crop_y = False):
        '''
        Generates a random word and creates an image using that word and one of 4 Fonts:
        * Arial
        * usicpeui
        * osifont
        * seguisym
        Also randomly applies transformations to the image:
        * randomly shifts the borders
        * stretches the image horizontally
        * applies salt and pepper noise (5% and 2% chance each)
        * applies perlin noise to the background (5% chance)
        * applies smoothing to the image (40% chance)
        :param font_size: if None, use random one, else use this size
        :param font_path: path to the font to use, iuf None use random font
        :param stretch_factor: float to stretch image horizontally by, if None do not stretch
        :param extra_kerning: additional spacing between the chars in pixels
        :param text_color: color of the text
        :param crop_y: whether to crop the text in y direction
        :return: PIL image
        '''
        text = next(self.text_gen)
        # if random.random() > 0.9:
        #     text += " " + next(self.text_gen)
        if font_path is None:
            font_path = random.choice(self.extended_fonts_paths)
        if font_size is None:
            typeface = ImageFont.truetype(font_path, self.get_random_font_size())
        else:
            typeface = ImageFont.truetype(font_path, font_size)
        image = get_image_from_text(text, typeface, extra_kerning, text_color, crop_y = crop_y)

        if stretch_factor is not None:
            image = image.resize((int(image.size[0] * stretch_factor), image.size[1]))

        if self.add_noise:
            # random padding
            image = self.random_borders(image)

            # apply salt and pepper noise in distinct steps
            if random.random() > 0.95: # salt noise foreground
                image = self.salt(image, 0.05)

            if random.random() > 0.98: # pepper noise foreground
                image = self.pepper(image, 0.02)

            if random.random() > 0.95: # perlin noise background
                image = self.add_perlin_noise(image)

            if random.random() > 0.6: # smooth image
                image = image.filter(ImageFilter.SMOOTH)

        return image, text


def convert_text(text: str):
    '''
    Removes german chars and replaces them with ansi equivalents. i.e. Umlaute äöü would become aou. Also replaces ± with +-
    '''
    umlaute = "üöäÜÖÄ"
    vokale = "uoaUOA"
    for umlaut, vokal in zip(umlaute, vokale):
        text = text.replace(umlaut, vokal)
    text = text.replace("ß", "ss")
    text = text.replace("±", "+-")
    return text

def load_data(token_path, norm_path, material_path):
    '''
    Loads all paths to pickle files and returns the needed data
    :return: tokens, norms, materials, materials_flat
    '''
    tokens = load_pickle_file(token_path)
    norms = load_pickle_file(norm_path)
    materials = load_pickle_file(material_path)
    materials_flat = []
    for mat_class in materials:
        for material in mat_class:
            materials_flat.append(material)
    return tokens, norms, materials, materials_flat

def generate_and_save_rec_data(image_pair_gen, base_path, n, split, info_interval):
    '''
    Generates n images using image_pair_gen, splits them into a testing and training set using split and saves everything for mmocr in base_path.
    During generation, every info_interval images the approx. remaining time is printed.
    '''
    # ready the dictionaries
    data_dict_train = {
        "metainfo": {
            "dataset_type": "TextRecogDataset",
            "task_name": "textrecog"
        },
        "data_list": []
    }

    data_dict_test = {
        "metainfo": {
            "dataset_type": "TextRecogDataset",
            "task_name": "textrecog"
        },
        "data_list": []
    }

    # create dirs and stuff
    image_train_path = os.path.join(base_path, "train")
    image_test_path = os.path.join(base_path, "test")
    os.makedirs(image_train_path, exist_ok=True)
    os.makedirs(image_test_path, exist_ok=True)
    dict_train_path = os.path.join(base_path, "rec_train.json")
    dict_test_path = os.path.join(base_path, "rec_test.json")

    last_cp_time = time.time()
    times = []
    # run thru all annotated images
    for i in range(n):

        # print out info every info_interval images
        if (i + 1) % info_interval == 0 and i > 1:
            to_do = n - i - 1
            new_cp_time = time.time()
            delta_t = new_cp_time - last_cp_time
            times.append(delta_t)
            avg_time = sum(times) / len(times)
            last_cp_time = new_cp_time
            print(f"{to_do} images left. ETA: {round(avg_time * (to_do / info_interval))} seconds.")

        # get next pair
        img, text = next(image_pair_gen)
        # convert text to not include germany chars
        text = convert_text(text)

        # train set
        if i < n * split:
            img_path = os.path.join(image_train_path, str(i) + ".png")
            # save image
            img.save(img_path)
            # save data in train json
            img_dict = {
                "instances": [{"text": text}],
                "img_path": "./train/" + str(i) + ".png"
            }
            data_dict_train["data_list"].append(img_dict)
        # test set
        else:
            img_path = os.path.join(image_test_path, str(i) + ".png")
            # save image
            img.save(img_path)
            # save data in test json
            img_dict = {
                "instances": [{"text": text}],
                "img_path": "./test/" + str(i) + ".png"
            }
            data_dict_test["data_list"].append(img_dict)

    # save both json files
    with open(dict_train_path, 'w') as f:
        json.dump(data_dict_train, f, ensure_ascii=False, indent=4)

    with open(dict_test_path, 'w') as f:
        json.dump(data_dict_test, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # get input vars
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1250000
    split = float(sys.argv[2]) if len(sys.argv) > 2 else 4/5
    base_path = sys.argv[3] if len(sys.argv) > 3 else "../data/fake_rec_data/"
    token_path = sys.argv[4] if len(sys.argv) > 4 else "../resources/pickle/dictionary.pickle"
    norm_path = sys.argv[5] if len(sys.argv) > 5 else "../resources/pickle/common_norms.pkl"
    material_path = sys.argv[6] if len(sys.argv) > 6 else "../resources/pickle/materials.pkl"
    info_interval = int(sys.argv[7]) if len(sys.argv) > 7 else 1000


    # load all the pickled data
    tokens, norms, materials, materials_flat = load_data(token_path, norm_path, material_path)

    # instantiate the Generator
    image_pair_gen = ImagePairGenerator(tokens, norms, materials_flat)

    generate_and_save_rec_data(image_pair_gen, base_path, n, split, info_interval)
