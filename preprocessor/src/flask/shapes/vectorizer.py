import clip
import numpy as np
import torch
from PIL import Image

from preprocessor.src.flask.converter.utils import get_cropped_views


def generate_embeddings(shape_image):
    """
    Generate embeddings for all views of a shape image using a pre-trained CLIP model.

    param shape_image: The input shape image for which embeddings are to be generated.
    return: A tensor containing the image embeddings for each view.
    """
    # Load CLIP model and preprocess function
    model, preprocess = clip.load("ViT-B/32", device="cpu")

    # List to store preprocessed image views
    view_images = []

    # Get cropped views from the shape image
    for view in get_cropped_views(shape_image):
        view_image = Image.fromarray(view.image)
        view_images.append(preprocess(view_image))

    # Handle empty shape_image
    if len(view_images) == 0:
        return []

    # Stack the preprocessed images into a batch
    view_images = torch.stack(view_images)

    # Generate embeddings with the CLIP model
    with torch.no_grad():
        embeddings = model.encode_image(view_images).float()

    return embeddings


def choose_representative_embedding(embeddings, return_index=False):
    """
    Choose the most representative embedding from a set of embeddings based on distance to the mean.

    param embeddings: A tensor or array containing multiple embeddings.
    param return_index: Boolean flag to indicate if the index of the chosen embedding should be returned.
                        Default is False, in which case the embedding is returned.

    return: The most representative embedding (as a numpy array) that is closest to the mean, or the index of this
            embedding if return_index is True.
    """
    # Handle empty embeddings
    if len(embeddings) == 0:
        if return_index:
            return None
        else:
            return torch.zeros(512)
    else:
        # Convert tensor to numpy array if necessary
        if isinstance(embeddings, torch.Tensor):
            embeddings = embeddings.cpu().numpy()

        # Calculate the mean embedding
        mean_embedding = embeddings.mean(axis=0)

        # Compute Euclidean distances from each embedding to the mean embedding
        distances = np.linalg.norm(embeddings - mean_embedding, axis=1)

        # Find the index of the embedding with the smallest distance to the mean
        most_representative_idx = np.argmin(distances)

        if return_index:
            return most_representative_idx
        else:
            return embeddings[most_representative_idx]
