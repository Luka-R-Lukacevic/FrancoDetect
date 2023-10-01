import requests
from tqdm import tqdm
import os
import json
from random import randint
import argparse
from time import sleep



def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--regions", help="The folder full of addresses per region to read and extract GPS coordinates from", required=True, type=str)
    parser.add_argument("--output", help="The output folder where the images will be stored, (defaults to: images/)", default='images/', type=str)
    parser.add_argument("--key", help="Your Google Street View API Key", type=str, required=True)
    return parser.parse_args()

args = get_args()
url = 'https://maps.googleapis.com/maps/api/streetview?'
meta_url = 'https://maps.googleapis.com/maps/api/streetview/metadata?'



region_names = os.listdir(args.regions) 
region_data_dict = {region: [] for region in region_names}
region_data_dict_retry = {region: [] for region in region_names}


def load_cities(): #This function adds all (!) the coordinates from the city files to our dictionary
    for region_name in os.listdir(args.regions):
        region_folder = os.path.join(args.regions, region_name)
        if os.path.isdir(region_folder):
            coordinates = []
            print(f'Loading coordinates from {region_name}...')
            region_file = os.path.join(region_folder, f'{region_name}.txt')
            if os.path.exists(region_file):
                with open(region_file) as f:
                    for line in tqdm(f):
                        lat_str, lng_str = line.strip('()\n').split(', ')
                        latitude = float(lat_str)
                        longitude = float(lng_str)
                        coordinates.append((latitude, longitude))
                region_data_dict[region_name].append(coordinates)
            else:
                print(f"Warning: No coordinates file found for {region_name}")




def main():
    # Open and create all the necessary files & folders
    os.makedirs(args.output, exist_ok=True)
    
    load_cities()
    
    for region in region_data_dict:  # Traverse all regions and then all coordinates for the images
        os.makedirs(os.path.join(args.output, region), exist_ok=True)
        if region_data_dict[region] != []:
            coordinates = region_data_dict[region].pop()
        else:
            coordinates = []
        for tup in coordinates:
            x = tup[0]
            y = tup[1]
            for heading_degrees in [0, 90, 180, 270]:
                heading_letter = 'NESW'[heading_degrees // 90]  # Map degrees to letters
                params = {
                    'size': '640x640',
                    'location': str(x) + ',' + str(y),
                    'heading': str(heading_degrees),
                    'pitch': '20',
                    'key': args.key
                }
                meta_params = {
                    'key': args.key,
                    'location': str(x) + ',' + str(y)
                }
                meta_response = requests.get(meta_url, params=meta_params).json()
                if meta_response['status'] == 'REQUEST_DENIED':
                    region_data_dict_retry[region].append(tup)
                elif meta_response['status'] == 'OK':
                    response = requests.get(url, params)
                    image_filename = os.path.join(args.output, region, f'{heading_letter}_{x},{y}.jpg')
                    with open(image_filename, "wb") as file:
                        file.write(response.content)
                    sleep(0.75)

        
        
        coordinates = region_data_dict_retry[region]
        for tup in coordinates:
            x = tup[0]
            y = tup[1]
            for heading_degrees in [0, 90, 180, 270]:
                heading_letter = 'NESW'[heading_degrees // 90]  # Map degrees to letters
                params = {
                    'size': '640x640',
                    'location': str(x) + ',' + str(y),
                    'heading': str(heading_degrees),
                    'pitch': '20',
                    'key': args.key
                }
                meta_params = {'key': args.key,
                                'location': str(x) + ',' + str(y)
                }
                meta_response = requests.get(meta_url, params=meta_params).json()
                if meta_response['status'] == 'OK':
                    response = requests.get(url, params)
                    image_filename = os.path.join(args.output, region, f'{heading_letter}_{x},{y}.jpg')
                    with open(image_filename, "wb") as file:
                        file.write(response.content)
                    sleep(1)

if __name__ == '__main__':
    main()