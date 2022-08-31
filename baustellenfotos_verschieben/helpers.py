import os
import platform
import pickle
import inquirer
from PIL import ExifTags

# reads a specific field from Exif data
def get_exif_field (exif,field) :
  for (k,v) in exif.items():
     if ExifTags.TAGS.get(k) == field:
        return v

def save_location_point(center_point, path):
    dataset = [*center_point]
    output_file = os.path.join(path, ".meta.data")
    fw = open(output_file, "wb")
    pickle.dump(dataset, fw)
    fw.close()

    # hide file in Windows file explorer
    if platform.system() == "Windows":
        os.system( "attrib +h {}".format(output_file) ) 

def read_location_point(path):
    input_file = os.path.join(path, ".meta.data")

    try:
        fd = open(input_file, "rb")
        dataset = pickle.load(fd)
        return tuple(dataset)
    except:
        return None

def present_list_selection(variable_name, message, choices):
    questions = [
    inquirer.List(variable_name, 
        message=message,
        choices=choices)
    ]
    
    return inquirer.prompt(questions)[variable_name]

def present_text_input(variable_name, message):
    questions = [
        inquirer.Text(variable_name, message=message)
    ]
    
    return inquirer.prompt(questions)[variable_name]

def query_address():
    questions = [
        inquirer.Text("street_name", message="Straße", validate=lambda _, c: all(x.isalpha() or x.isspace() for x in c)),
        inquirer.Text("house_number", message="Hausnummer", validate=lambda _, c: c.isnumeric()),
        inquirer.Text("zip_code", message="Postleitzahl", validate=lambda _, c: c.isnumeric()),
        inquirer.Text("city_name", message="Ort", validate=lambda _, c: all(x.isalpha() or x.isspace() for x in c))
    ]

    answers = inquirer.prompt(questions)

    for key,value in answers.items():
        answers[key] = value.strip()
    return ' '.join(map(str, answers.values()))

def get_directories(path):
    return [folder for folder in os.listdir(path) if os.path.isdir(os.path.join(path, folder))]

def get_images(path):
    return [file for file in os.listdir(path) if file.endswith(('jpeg', 'png', 'jpg'))]

def create_directory(path):
    directory_exists = os.path.exists(path)
    if not directory_exists:
        # create output folder if not existend
        os.makedirs(path)