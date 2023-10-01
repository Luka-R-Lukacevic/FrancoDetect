import os
from PIL import Image
import numpy as np
import torch
from torchvision import datasets
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm
import random
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


import time
# Create a list to store image paths and labels
image_paths = []
descriptions = os.listdir("C:\\Users\\lluka\\Downloads\\country_images")
text_description = [f'A Street View photo in the region of {region} in France.' for region in descriptions]
dict = {city: 0 for city in descriptions}


batch_size = 4
features = []
current_images = []

# Initialize a dictionary to group images by coordinates and direction
coordinate_direction_images = {}

for image_path, label in tqdm(dataset.samples):

    city = os.path.basename(os.path.dirname(image_path))
    if dict[city] < 1200:
        ind = descriptions.index(city)
        image_paths.append(image_path)
        dict[city] += 1

        # Extract direction and coordinates from the filename
        filename = os.path.basename(image_path)
        coords,direction = filename.split('_')[0], filename.split('_')[1].split('.jpg')[0]

        # Create a key for grouping images
        key = f"{coords}_{direction}"
    
        # Append images and labels to the current batch
        imo = Image.open(image_path)
        current_images.append(np.array(imo, dtype=np.float32))
        imo.close()

        # If the current batch is complete, add it to the dictionary
        if len(current_images) == batch_size:
            inputs = processor("", images=current_images, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = model(**inputs)
            batch_embedding = torch.mean(outputs['image_embeds'], dim=0).tolist()
            features.append((np.array(batch_embedding), city))
            current_images = []


random.shuffle(features)
labels = [features[i][1] for i in range(len(features))]
features = np.array([np.array(features[i][0]) for i in range(len(features))])


np.save( args.save + "\\StreetCLIP_4features.npy", features)

with open( args.save + "\\StreetCLIP_4labels.txt", "w") as label_file:
    label_file.write("\n".join(labels[:len(features)]))