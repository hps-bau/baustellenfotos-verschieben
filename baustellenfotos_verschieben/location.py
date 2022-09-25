from fileinput import filename
import os
from tkinter.messagebox import NO
from PIL.ExifTags import TAGS, GPSTAGS
from geopy import Point, distance
from geopy.geocoders import GoogleV3
from PIL import Image
from pillow_heif import register_heif_opener
from dotenv import load_dotenv

register_heif_opener() # register pillow_heif as PIL plugin
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
RADIUS = 150 # in meter

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
    image.verify()

    if path.lower().endswith('heic'):
        return _get_coordinates_from_heic(image)
    else:
        return _get_coordinates_from_not_heic(image)

# source: https://stackoverflow.com/questions/72522522/how-to-extract-gps-location-from-heic-files
def _get_coordinates_from_heic(image):
    # get exif
    exif_data = image.getexif().get_ifd(0x8825)
    if exif_data is None:
        return None

    gps_info = {}
    if not exif_data:
        raise ValueError("No EXIF metadata found")
    else:
        gps_keys = ['GPSVersionID', 'GPSLatitudeRef', 'GPSLatitude', 'GPSLongitudeRef', 'GPSLongitude',
                    'GPSAltitudeRef', 'GPSAltitude', 'GPSTimeStamp', 'GPSSatellites', 'GPSStatus', 'GPSMeasureMode',
                    'GPSDOP', 'GPSSpeedRef', 'GPSSpeed', 'GPSTrackRef', 'GPSTrack', 'GPSImgDirectionRef',
                    'GPSImgDirection', 'GPSMapDatum', 'GPSDestLatitudeRef', 'GPSDestLatitude', 'GPSDestLongitudeRef',
                    'GPSDestLongitude', 'GPSDestBearingRef', 'GPSDestBearing', 'GPSDestDistanceRef', 'GPSDestDistance',
                    'GPSProcessingMethod', 'GPSAreaInformation', 'GPSDateStamp', 'GPSDifferential']

        for k, v in exif_data.items():
            try:
                gps_info[gps_keys[k]] = str(v)
            except IndexError:
                pass

        lat_ref = gps_info["GPSLatitudeRef"]
        lat_degrees_str = gps_info["GPSLatitude"].replace('(', '').replace(')', '') # format (xx, xx, xx)
        lat_degrees = tuple(map(float, lat_degrees_str.split(', ')))
        lat_decimal = Point.parse_degrees(*lat_degrees, lat_ref)

        long_ref = gps_info["GPSLongitudeRef"]
        long_degrees_str = gps_info["GPSLongitude"].replace('(', '').replace(')', '') # format (xx, xx, xx)
        long_degress = tuple(map(float, long_degrees_str.split(', ')))
        long_decimal = Point.parse_degrees(*long_degress, long_ref)

        return (lat_decimal, long_decimal)

def _get_coordinates_from_not_heic(image):
    # get exif data
    exif_data = image._getexif()
    if exif_data is None:
        return None

    # get coordinates
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