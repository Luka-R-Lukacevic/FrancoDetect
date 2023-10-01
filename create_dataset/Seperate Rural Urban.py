
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import os
import torch
import argparse

# Load the fine-tuned CLIP model and processor
processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14-336")
model = CLIPModel.from_pretrained("geolocal/StreetCLIP")

classes = ['urban', 'rural']
training_descriptions = [f'A Street View photo from an {classe} location in France.'for classe in classes]

def classify(image_path):

    image = Image.open(image_path)
    inputs = processor(training_descriptions, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
        if probs[0] > 0.25:
            return classes[0]
        return classes[1]
    



def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", help="The path of the source directory", required=True, type=str)
    parser.add_argument("--output", help="The path to the image folder with urban and rural images separated", required=True, type=str)
    parser.add_argument("--destination", help="The path of the destination directory", required=True, type=str)
    return parser.parse_args()

args = get_args()

city_folder = args.output

os.makedirs( city_folder + '\\urban', exist_ok=True)
os.makedirs(city_folder + '\\rural', exist_ok=True)


source_directory = args.source

destination_base_directory = args.destination

for city in os.listdir(source_directory):
    city_path = os.path.join(source_directory,city)
    print("Current city: ", city)
    for image_name in os.listdir(city_path):
        
        image_path = os.path.join(city_path, image_name)

        classification = classify(image_path)

        destination_directory = os.path.join(destination_base_directory, classification, city)

        os.makedirs(destination_directory, exist_ok=True)

        shutil.copy(image_path, os.path.join(destination_directory, image_name))

print("Classification and copying completed.")

    

