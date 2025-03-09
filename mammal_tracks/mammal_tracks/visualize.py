import csv
import base64
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
import os

csv.field_size_limit(10 * 1024 * 1024)  # Augmentation de la limite de taille pour les fichiers CSV

def is_base64_encoded(data):
    try:
        base64.b64decode(data, validate=True)
        return True
    except Exception:
        return False

def display_image_from_base64(base64_string):
    try:
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        plt.imshow(image)
        plt.axis('off')
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
            print("Choix non valide. Veuillez entrer 'v' ou 'd'.")

def validate_images(csv_file, output_csv=None):
    with open(csv_file, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)
        valid_rows = []

        plt.figure(figsize=(8, 8))
        
        for index, row in enumerate(rows):
            base64_image = row.get('image_url')

            if not base64_image or not is_base64_encoded(base64_image):
                print(f"Ligne {index + 1} ignorée : données invalides.")
                continue

            image = display_image_from_base64(base64_image)
            if image:
                ax = plt.subplot(1, 1, 1)
                validate_or_remove_image(image, index, ax, row, valid_rows)

        # Sauvegarde du CSV filtré si spécifié
        if output_csv:
            with open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(valid_rows)
            print(f"CSV filtré sauvegardé : {output_csv}")

        # Sauvegarde des images dans l'arborescence
        save_images(valid_rows)

        print(f"Traitement complet : {len(valid_rows)}/{len(rows)} images validées")

def save_images(valid_rows):
    os.makedirs('images', exist_ok=True)  # Création du dossier principal
    
    for row in valid_rows:
        try:
            animal = row.get('animal', 'inconnu')
            image_data = base64.b64decode(row['image_url'])
            
            # Création du sous-dossier par espèce
            species_dir = os.path.join('images', animal.replace(' ', '_'))
            os.makedirs(species_dir, exist_ok=True)
            
            # Génération d'un nom de fichier unique
            filename = f"{row.get('id', 'image')}_{hash(row['image_url']) & 0xFFFFFFFF}.jpg"
            filepath = os.path.join(species_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            print(f"Image sauvegardée : {filepath}")
        except Exception as e:
            print(f"Erreur de sauvegarde pour {row.get('id')} : {e}")

# Exemple d'utilisation avec les deux fonctionnalités
validate_images(
    csv_file='tracks_with_image.csv',
    output_csv='validated_images.csv'  # Optionnel
)