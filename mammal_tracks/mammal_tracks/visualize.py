import csv
import base64
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

csv.field_size_limit(10 * 1024 * 1024)  # Par exemple, 10 Mo

def is_base64_encoded(data):
    try:
        # Vérifier si la chaîne peut être décodée
        base64.b64decode(data, validate=True)
        return True
    except Exception:
        return False

def display_image_from_base64(base64_string):
    try:
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        plt.imshow(image)
        plt.axis('off')  # Masquer les axes
        plt.show()
        return image
    except Exception as e:
        print(f"Erreur lors de l'affichage de l'image : {e}")
        return None

def validate_or_remove_image(image, index, ax, row, valid_rows):
    while True:
        plt.imshow(image)
        plt.axis('off')
        plt.show()
        choice = input(f"Image {index + 1}: Valider (v) ou Supprimer (d) ? ").strip().lower()
        if choice == 'v':
            valid_rows.append(row)
            print(f"Image {index + 1} validée.")
            plt.close()
            break
        elif choice == 'd':
            print(f"Image {index + 1} supprimée.")
            plt.close()
            break
        else:
            print("Choix non valide, veuillez entrer 'v' pour valider ou 'd' pour supprimer.")

# Fonction pour visualiser et valider les images
def validate_images(csv_file):
    with open(csv_file, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)  # Lire toutes les lignes du fichier CSV
        valid_rows = []  # Liste pour stocker les lignes validées

        # Préparez une figure pour afficher les images
        plt.figure(figsize=(8, 8))
        
        for index, row in enumerate(rows):
            base64_image = row.get('image_url')

            # Vérifier si le contenu base64 est valide
            if not base64_image or not is_base64_encoded(base64_image):
                print(f"Ligne {index + 1} ignorée : données base64 invalides ou manquantes.")
                continue

            # Afficher l'image
            image = display_image_from_base64(base64_image)
            if image:
                # Afficher l'image et demander la validation ou suppression
                ax = plt.subplot(1, 1, 1)
                validate_or_remove_image(image, index, ax, row, valid_rows)
            
        # Sauvegarder un dossier avec des sous-dossiers pour chaque classe d'images
        save_images(valid_rows)

        print(f"Validation terminée. {len(valid_rows)} images validées sur {len(rows)} lignes.")

def save_images(valid_rows):
    for row in valid_rows:
        # Supposons que la colonne contenant l'ID soit 'id' et la colonne contenant l'image en base64 soit 'image_url'
        animal_name = row.get('animal', '')
        base64_image = row.get('image_url', '')
        
        if animal_name and base64_image:
            try:
                image_data = base64.b64decode(base64_image)
                image = Image.open(BytesIO(image_data))
                image.save(f"images/{animal_name}.jpg")
                print(f"Image {animal_name} sauvegardée.")
            except Exception as e:
                print(f"Erreur lors de la sauvegarde de l'image {animal_name}: {e}")

# Exemple d'utilisation
csv_file = 'tracks_with_image.csv'  # Nom de votre fichier CSV avec les images en base64
validate_images(csv_file)