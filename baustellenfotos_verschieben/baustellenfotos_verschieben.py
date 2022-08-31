import os, shutil
import sys
from datetime import date
from dotenv import load_dotenv
import helpers
import location

load_dotenv()

SOURCE_PATH = os.getenv("SOURCE_PATH")
DESTINATION_PATH = os.getenv("DESTINATION_PATH")
CURRENT_YEAR = str(date.today().year)

operation = helpers.present_list_selection("operation", "Neues BV anlegen oder BV auswählen?", ["Auswählen", "Neu"])

match operation.lower():
    case "auswählen":
        selection = helpers.present_list_selection("selection", "Ordner auswählen", [CURRENT_YEAR, "Anderes"]).lower()

        if selection == CURRENT_YEAR:
            path = os.path.join(DESTINATION_PATH, CURRENT_YEAR)
            directories = helpers.get_directories(path)
            project_name = helpers.present_list_selection("project_name", "Welches BV?", directories)
        elif selection == "anderes":
            # select parent folder
            directories = helpers.get_directories(DESTINATION_PATH)
            parent_directory = helpers.present_list_selection("directory", "Ordner auswählen", directories)

            # select child folder
            path = os.path.join(DESTINATION_PATH, parent_directory)
            directories = helpers.get_directories(path)

            if not directories:
                print("Ordner enthält keine BVs")
                sys.exit()

            project_name = helpers.present_list_selection("project_name", "Welches BV?", directories)

        center_point = helpers.read_location_point(os.path.join(path, project_name))
        if center_point is None:
            print("Fehler! Ortsangaben konnten nicht gefunden werden.")
            sys.exit()

    case "neu":
        print("BV wird im Ordner '{}' angelegt:".format(CURRENT_YEAR))
        project_name = helpers.present_text_input("project_name", "Wie lautet das Bauvorhaben (BV)?")

        # ask for address - repeat if input invalid
        center_point = None        
        while center_point is None:
            address = helpers.query_address()
            center_point = location.get_pos_by_name(address)
            
            if center_point is None:
                print("Es konnte keine Adresse zu deinen Angaben gefunden werden. Erneut versuchen.")

# import image filenames
child_source_path = os.path.join(SOURCE_PATH, CURRENT_YEAR)
images = helpers.get_images(child_source_path)

if len(images) == 0:
    print("No images have been found!")
    sys.exit()

# create "year" folder
output_path = os.path.join(DESTINATION_PATH, CURRENT_YEAR)
helpers.create_directory(output_path)

# create "construction" project folder
output_path = os.path.join(output_path, project_name)
helpers.create_directory(output_path)

# check every image if within range
counter = 0
for image_str in images:
    image_path = os.path.join(child_source_path, image_str)
    image_point = location.get_image_point(image_path)

    if image_point is None:
        continue

    if location.is_within_radius(center_point, image_point):
        # print("{} Distance: {}".format(image, dis))
        # shutil.copy2(image_path, output_path) # copy for debug purposes
        shutil.move(image_path, os.path.join(output_path, image_str))
        counter+=1

    print(counter, " Fotos verschoben", end="\r")

helpers.save_location_point(center_point, output_path)
print("Prozess erfolgreich abgeschlossen - {} Foto(s) verschoben".format(counter))

input("\nEnter drücken um Programm zu beenden...")