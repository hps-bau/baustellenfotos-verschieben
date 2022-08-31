import os
from PIL.ExifTags import TAGS, GPSTAGS
from geopy import Point, distance
from geopy.geocoders import GoogleV3
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
RADIUS = 150 # in meter

def get_coordinates(exif_data):
    exif_table = {}
    for tag, value in exif_data.items():
        decoded = TAGS.get(tag, tag)
        exif_table[decoded] = value

    if 'GPSInfo' not in exif_table:
        return None

    gps_info = {}
    for key in exif_table['GPSInfo'].keys():
        decode = GPSTAGS.get(key,key)
        gps_info[decode] = exif_table['GPSInfo'][key]
    
    lat_ref = gps_info["GPSLatitudeRef"]
    lat_degrees = gps_info["GPSLatitude"]
    lat_decimal = Point.parse_degrees(*lat_degrees, lat_ref)

    long_ref = gps_info["GPSLongitudeRef"]
    long_degrees = gps_info["GPSLongitude"]
    long_decimal = Point.parse_degrees(*long_degrees, long_ref)
    
    return (lat_decimal, long_decimal)

def get_pos_by_name(location_name):
    geolocator = GoogleV3(api_key=GOOGLE_API_KEY)
    loc = geolocator.geocode(location_name)
    if not loc:
        return None

    return (loc.latitude, loc.longitude)

def is_within_radius(point1 ,point2):
    dis = distance.distance(point1, point2).m
    return dis <= RADIUS

def get_image_point(path):
    image = Image.open(path)
    exif_data = image._getexif()

    if exif_data is not None:
        return get_coordinates(exif_data)

    return None