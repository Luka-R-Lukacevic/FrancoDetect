from time import sleep
import pyautogui
from PIL import ImageGrab
from collections import Counter
import joblib
import numpy as np
from PIL import Image
from StreetCLIP_Predict import franco_predict
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="my_geocoder")

def crop_upper_pixels(image_path, num_pixels_to_cut):
    # Open the image
    original_image = Image.open(image_path)

    # Get the width and height of the original image
    width, height = original_image.size

    # Crop the image to remove the upper num_pixels_to_cut pixels
    cropped_image = original_image.crop((0, num_pixels_to_cut, width, height))

    # Save the cropped image
    cropped_image.save(image_path)


for i in range(5):
    # adjust to screen loading time
    sleep(5)
    screenshot = ImageGrab.grab()
    screenshot.save("screenshot.png")
    # cut the upper 200 pixels to remove irrelevant information (such as open tabs or geoguessr logo)
    num_pixels_to_cut = 200
    crop_upper_pixels("screenshot.png", num_pixels_to_cut)
    # apply model
    prediction = franco_predict(Image.open("screenshot.png"))
    print(prediction)
    # get coordinates of predicted place
    predicted_coordinates = geolocator.geocode(prediction + ", France")
    xcoordinate = predicted_coordinates.latitude
    ycoordinate = predicted_coordinates.longitude
    print(xcoordinate, ycoordinate)
    # translate coordinates to place on the screen, this highly depends
    # on your device as well as the browser you're using and the exact map
    # you're playing
    x = 500 + (45.1644 - xcoordinate)*39.7614
    y = 1000 + (ycoordinate - 8.6186)*27.217
    pyautogui.moveTo(1800, 900)
    # use this time to calibrate your map
    sleep(10)
    # place guess
    pyautogui.click(y, x)
    sleep(1)
    pyautogui.click()
    sleep(1)
    pyautogui.press("space")
    sleep(4)
    pyautogui.press("space")
