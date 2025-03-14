import csv
import requests
import base64
from io import BytesIO
import time

# Fonction pour télécharger l'image depuis l'URL et la convertir en base64
def image_to_base64(url):
    try:
        print(f"Tentative de téléchargement de l'image depuis : {url}")
        response = requests.get(url, timeout=10)  # Timeout pour éviter un blocage trop long
        response.raise_for_status()  # Vérifie si le code de statut est 200 (OK)

        # Vérifiez que l'URL correspond bien à une image (en fonction du type MIME)
        if 'image' in response.headers.get('Content-Type', ''):
            # Convertir l'image en base64
            image_data = BytesIO(response.content)
            encoded_image = base64.b64encode(image_data.read()).decode('utf-8')
            print(f"Image téléchargée et encodée en base64.")
            return encoded_image
        else:
            print(f"URL non image : {url}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement de l'image: {url}. Détails : {e}")
        return None
    except Exception as e:
        print(f"Erreur avec l'URL {url}: {e}")
        return None

# Lire le CSV existant et modifier les URLs des images
def update_csv(input_csv, output_csv):
    with open(input_csv, mode='r', newline='', encoding='utf-8') as infile, \
         open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # Supposons que la colonne contenant l'URL de l'image s'appelle 'image_url'
            image_url = row.get('image_url')
            if image_url:
                print(f"Traitement de l'image pour : {image_url}")
                # Remplacer l'URL de l'image par l'image en base64
                base64_image = image_to_base64(image_url)
                if base64_image:
                    row['image_url'] = base64_image
                else:
                    row['image_url'] = "Image non trouvée ou erreur"
            else:
                print(f"Pas d'URL d'image trouvée dans la ligne.")
            writer.writerow(row)
            time.sleep(1) 
            
# Exemple d'utilisation
input_csv = 'mammal_tracks/tracks.csv'  # Nom de votre fichier CSV d'entrée
output_csv = 'tracks_with_url.csv'  # Nom du fichier CSV de sortie avec les images en base64

update_csv(input_csv, output_csv)
