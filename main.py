from datetime import datetime, timedelta 
from logzero import logger, logfile 
from sense_hat import SenseHat 
from ephem import readtle, degree 
from picamera import PiCamera 
from time import sleep
from pathlib import Path
import random
import os
import csv
import cv2
import numpy as np

dir_path = Path(__file__).parent.resolve()

logfile(dir_path/"cvnteam.log") 

name = "ISS (ZARYA)"
line1 = "1 25544U 98067A   19336.91239465 -.00004070  00000-0 -63077-4 0  9991" 
line2 = "2 25544  51.6431 244.7958 0006616 354.0287  44.0565 15.50078860201433" 
iss = readtle(name, line1, line2) 

sense_hat = SenseHat()

camera = PiCamera() 
camera.resolution = (1296, 972) 
camera.start_preview()
sleep(2)
camera.capture(f"{dir_path}/image.jpg")

def create_csv_file(data_file): 
    """Create a new CSV file and add the header row""" 
    with open(data_file, 'w') as f: 
        writer = csv.writer(f)
        header = ("Date/time", "Temperature", "Humidity") 
        writer.writerow(header) 
 
def add_csv_data(data_file, data):
    """Add a row of data to the data_file CSV"""  
    with open(data_file, 'a') as f: 
        writer = csv.writer(f) 
        writer.writerow(data)  

def get_lation():
    """Return the current latitude and longitude, in degrees"""
    iss.compute()
    return (iss.sublat / degree, iss.sublong / degree)

def convert(angle):
    """
    Convert an ephem angle (degrees:minutes:seconds) to
    an EXIF-appropriate representation (rationals)
    e.g. '51:35:19.7' to '51/1,35/1,197/10'
    Return a tuple containing a boolean and the converted angle,
    with the boolean indicating if the angle is negative.
    """
    degrees, minutes, seconds = (float(field) for field in str(angle).split(":"))
    exif_angle = f'{abs(degrees):.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return degrees < 0, exif_angle

def capture(camera, image):
    """Use `camera` to capture an `image` file with lat/long EXIF data."""
    iss.compute() 
    south, exif_latitude = convert(iss.sublat)
    west, exif_longitude = convert(iss.sublong)
    camera.exif_tags['GPS.GPSLatitude'] = exif_latitude
    camera.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
    camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
    camera.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"
    camera.capture(image)
    capture(camera, dir_path/"gps1.jpg")


data_file = dir_path/'date.csv'
create_csv_file(data_file)
photo_counter = 1 
start_time = datetime.now() 
now_time = datetime.now()


while (now_time < start_time + timedelta(minutes=2)): 
    print("Doing stuff")
    sleep(1)
    now_time = datetime.now() 
 
while (now_time < start_time + timedelta(minutes=178)):
    try:
        logger.info("{} iteration {}".format(datetime.now(), photo_counter))
        humidity = round(sense_hat.humidity, 4)
        temperature = round(sense_hat.temperature, 4)
        latitude, longitude = get_latlong()
        data = (
            datetime.now(), 
            photo_counter, 
            humidity, 
            temperature, 
            latitude, 
            longitude
        ) 
        add_csv_data(data_file, data)
        pathImage = dir_path + "/photo_" + str(photo_counter).zfill(3) + ".jpg"
        if (-7 <= latitude <= 12 and 8 <= longitude <= 29) or (-13 <= latitude <= 8.5 and -50 <= longitude <= 78) or (-4.5 <= latitude <= 6.9 and 108 <= longitude <= 115):
            print("je prends la photo")
            camera.capture(pathImage) 
            # lecture de l'image en noir et blanc    
            image = cv2.imread(pathImage,0) 
            # dimensions de l'image
            height, width, channels = image.shape
            #width, height = image.size
            centre_width = int(width/2)
            centre_height = int(height/2)
            pixel_central = image.getpixel(centre_width,centre_height)
            if pixel_central == (0, 0, 0):
                image_jour_nuit = 0 
                print("image de nuit : je ne l'enregistre pas. Je fixe mon parametre image_jour_nuit à 0  ")
            else:
                image_jour_nuit = 1
                print("image de jour : je l'enregistre. Je fixe mon parametre image_jour_nuit à 1  ")
        else :
            print ("je ne prends pas la photo") 
            photo_counter += 1
            sleep(15)
            now_time = datetime.now() 
    except Exception as e:
        logger.error('{}: {})'.format(e.__class__.__name__, e)) 
