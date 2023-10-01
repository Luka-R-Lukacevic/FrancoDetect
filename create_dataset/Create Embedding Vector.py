from transformers import CLIPProcessor, CLIPModel
import numpy as np
from PIL import Image
import os
import torch
import random
from torchvision import datasets
from tqdm import tqdm
import argparse

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", help="The path to the save directory", required=True, type=str)
    parser.add_argument("--root", help="The path of the root directory", required=True, type=str)
    parser.add_argument("--descriptions", help="The path to the folder with all country images", required=True, type=str)
    return parser.parse_args()

args = get_args()


# Load the fine-tuned CLIP model and processor
processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14-336")
model = CLIPModel.from_pretrained("geolocal/StreetCLIP")

root_directory = args.root

# Load the dataset
dataset = datasets.ImageFolder(root=root_directory)
random.shuffle(dataset.samples)

# Create a list to store image paths and labels
image_paths = []
labels = []
descriptions = os.listdir(args.descriptions)
dict = {city: 0 for city in descriptions}

# Specify batch size
batch_size = 4

# Initialize a list to store feature vectors
features = []

# Process the dataset in batches
for image_path, label in tqdm(dataset.samples):
    city = os.path.basename(os.path.dirname(image_path))
    if dict[city] < 300:
        ind = descriptions.index(city)
        labels.append(descriptions[ind])
        image_paths.append(image_path)
        dict[city] += 1

        # Process images in batches
        if len(image_paths) == batch_size:
            images = [Image.open(image_path) for image_path in image_paths]
            image_arrays = [np.array(image, dtype=np.float32) for image in images]

            inputs = processor("", images=image_arrays, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Store feature vectors
            features.extend(outputs['image_embeds'].tolist())

            # Clear lists to free memory
            image_paths.clear()

features = np.array(features)

np.save( args.save + "\\StreetCLIP_features.npy", features)

with open( args.save + "\\StreetCLIP_labels.txt", "w") as label_file:
    label_file.write("\n".join(labels[:len(features)]))