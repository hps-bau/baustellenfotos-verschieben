from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS
import os, shutil
import sys
from datetime import date
from geopy import distance, Point
from geopy.geocoders import GoogleV3
import inquirer
import pickle
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SOURCE_PATH = os.getenv("SOURCE_PATH")
DESTINATION_PATH = os.getenv("DESTINATION_PATH")
CURRENT_YEAR = str(date.today().year)

def clear_folder(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

# reads a specific field from Exif data
def get_exif_field (exif,field) :
  for (k,v) in exif.items():
     if ExifTags.TAGS.get(k) == field:
        return v

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

def save_location_point(center_point, path):
    dataset = [*center_point]
    output_file = os.path.join(path, ".meta.data")
    fw = open(output_file, "wb")
    pickle.dump(dataset, fw)
    fw.close()

def read_location_point(path):
    input_file = os.path.join(path, ".meta.data")

    try:
        fd = open(input_file, "rb")
        dataset = pickle.load(fd)
        return tuple(dataset)
    except:
        return None


questions = [
    inquirer.List("operation", 
        message="Neues BV anlegen oder BV auswählen?",
        choices=["Auswählen", "Neu"])
]
answers = inquirer.prompt(questions)

match answers["operation"].lower():
    case "auswählen":
        questions = [
            inquirer.List("selection", 
                message="Ordner auswählen",
                choices=[CURRENT_YEAR, "Anderes"])
        ]
        answers = inquirer.prompt(questions)

        selection = answers["selection"].lower()
        if selection == CURRENT_YEAR:
            path = os.path.join(DESTINATION_PATH, CURRENT_YEAR)
            directories = [folder for folder in os.listdir(path) if os.path.isdir(os.path.join(path, folder))]

            questions = [
                inquirer.List("project_name", 
                    message="Welches BV?",
                    choices=directories)
            ]
            answers = inquirer.prompt(questions)
            project_name = answers["project_name"]

            center_point = read_location_point(os.path.join(path, project_name))
            
            if center_point is None:
                print("Fehler! Ortsangaben konnten nicht gefunden werden.")
                exit()

        if selection == "anderes":
            # select parent folder
            path = DESTINATION_PATH
            directories = [folder for folder in os.listdir(path) if os.path.isdir(os.path.join(path, folder))]

            questions = [
                inquirer.List("directory", 
                    message="Ordner auswählen",
                    choices=directories)
            ]
            answers = inquirer.prompt(questions)
            parent_directory = answers["directory"]

            # select child folder
            path = os.path.join(DESTINATION_PATH, parent_directory)
            directories = [folder for folder in os.listdir(path) if os.path.isdir(os.path.join(path, folder))]

            if not directories:
                print("Ordner enthält keine BVs")
                sys.exit()

            questions = [
                inquirer.List("project_name", 
                    message="Welches BV?",
                    choices=directories)
            ]
            answers = inquirer.prompt(questions)
            project_name = answers["project_name"]

    case "neu":
        print("BV wird im Ordner '{}' angelegt:".format(CURRENT_YEAR))

        questions = [
            inquirer.Text("project_name", message="Wie lautet das Bauvorhaben (BV)?")
        ]
        
        answers = inquirer.prompt(questions)
        project_name = answers["project_name"]

        # ask for address - repeat if input invalid
        center_point = None        
        while center_point is None:
            questions = [
                inquirer.Text("street_name", message="Straße", validate=lambda _, c: all(x.isalpha() or x.isspace() for x in c)),
                inquirer.Text("house_number", message="Hausnummer", validate=lambda _, c: c.isnumeric()),
                inquirer.Text("zip_code", message="Postleitzahl", validate=lambda _, c: c.isnumeric()),
                inquirer.Text("city_name", message="Ort", validate=lambda _, c: all(x.isalpha() or x.isspace() for x in c))
            ]

            for key,value in answers.items():
                answers[key] = value.strip()
            answers = inquirer.prompt(questions)
            address = ' '.join(map(str, answers.values()))
            center_point = get_pos_by_name(address)
            
            if center_point is None:
                print("Es konnte keine Adresse zu deinen Angaben gefunden werden. Erneut versuchen.")

radius = 150 # in meter

child_source_path = os.path.join(SOURCE_PATH, CURRENT_YEAR)
images = [file for file in os.listdir(child_source_path) if file.endswith(('jpeg', 'png', 'jpg'))]

if len(images) == 0:
    print("No images have been found!")
    sys.exit()

# create "year" folder
output_path = os.path.join(DESTINATION_PATH, CURRENT_YEAR)

output_exists = os.path.exists(output_path)
if not output_exists:
    # create output folder if not existend
    os.makedirs(output_path) 

# create "construction" project folder
output_path = os.path.join(output_path, project_name)

output_exists = os.path.exists(output_path)
if not output_exists:
    # create output folder if not existend
    os.makedirs(output_path)

# resize images
counter = 0
for image_str in images:
    image_path = os.path.join(child_source_path, image_str)
    image = Image.open(image_path)
    exif_data = image._getexif()

    if exif_data is not None:
        image_point = get_coordinates(exif_data)

        if image_point is None:
            continue

        dis = distance.distance(center_point, image_point).m

        if dis <= radius:
            # print("{} Distance: {}".format(image, dis))
            # shutil.copy2(image_path, output_path) # copy for debug purposes
            shutil.move(image_path, os.path.join(output_path, image_str))
            counter+=1

    print(counter, " Fotos verschoben", end="\r")

save_location_point(center_point, output_path)
print("Prozess abgeschlossen - {} Foto(s) verschoben".format(counter))