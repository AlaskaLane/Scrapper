import requests
import csv
import cv2
import numpy as np
import os


# Paramètres globaux
animals = [
    "Oryctolagus cuniculus", "Ailurus fulgens", "Lynx lynx", "Panthera leo",
    "Panthera tigris", "Elephas maximus", "Loxodonta africana", "Viverra zibetha",
    "Mustela lutreola", "Bison bison", "Equus ferus caballus", "Sus scrofa",
    "Vulpes lagopus", "Procyon lotor", "Ursus maritimus", "Macaca mulatta",
    "Gorilla gorilla", "Canis latrans", "Odobenus rosmarus", "Cervus canadensis",
    "Alces alces", "Peromyscus maniculatus", "Herpestes ichneumon"
]

EXCLUDED_DOMAINS = ["shutterstock.com", "alamy.com"]
FOOTPRINT_KEYWORDS = ["footprint", "paw print", "track", "tracks"]
MAX_IMAGES = 20
CSV_FILE = "tracks.csv"

# Charger les URL existantes
def load_existing_urls():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # Ignorer l'en-tête
        return set(row[1] for row in reader)

# Enregistrer les nouvelles URL
def save_to_csv(new_entries):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["animal", "image_url"])
        writer.writerows(new_entries)

# Récupération optimisée des images
def fetch_images(animal, max_images=MAX_IMAGES):
    print(f"🔍 Recherche optimisée d'images pour : {animal}")
    image_data = set()
    results_per_page = 10
    existing_urls = load_existing_urls()
    
    for keyword in FOOTPRINT_KEYWORDS:
        pages = (max_images // results_per_page) + 1
        for page in range(pages):
            start_index = page * results_per_page + 1
            query = f"{animal} {keyword} -shutterstock -alamy"
            url = (
                f"https://www.googleapis.com/customsearch/v1"
                f"?q={query}&cx={CX}&key={API_KEY}&searchType=image"
                f"&imgSize=medium&num={results_per_page}&start={start_index}"
            )
            
            try:
                response = requests.get(url)
                print(f"🛠️ Page {page + 1} | Mot-clé : '{keyword}' | Statut : {response.status_code}")
                response.raise_for_status()
                
                results = response.json()
                for item in results.get('items', []):
                    display_link = item.get('displayLink', '')
                    image_url = item.get('link')
                    image_snippet = item.get('snippet', '').lower()
                    
                    if not image_url or image_url in existing_urls:
                        continue
                    
                    if not any(k in image_url.lower() for k in FOOTPRINT_KEYWORDS) and not any(k in image_snippet for k in FOOTPRINT_KEYWORDS):
                        continue
                    
                    if any(domain in display_link for domain in EXCLUDED_DOMAINS):
                        continue
                    
                    if image_url not in image_data:
                        print(f"✅ Ajout image : {image_url}")
                        image_data.add(image_url)
                    
                    if len(image_data) >= max_images:
                        break
            
            except requests.exceptions.RequestException as e:
                print(f"❗ Erreur API pour {animal} : {e}")
                break
            
            if len(image_data) >= max_images:
                break
    
    return [(animal, url) for url in image_data]

# Détection d'empreintes avec OpenCV
def detect_footprints(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            return False
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_contours = [c for c in contours if cv2.contourArea(c) > 1000]
        
        return len(valid_contours) > 0
    
    except requests.exceptions.RequestException as e:
        print(f"❗ Erreur lors du téléchargement de l'image : {e}")
        return False

# Fonction principale
def main():
    all_results = []
    existing_urls = load_existing_urls()
    
    for animal in animals:
        image_data = fetch_images(animal, max_images=MAX_IMAGES)
        for animal, image_url in image_data:
            if image_url in existing_urls:
                continue
            if detect_footprints(image_url):
                all_results.append((animal, image_url))
                existing_urls.add(image_url)
    
    if all_results:
        print(f"💾 Enregistrement de {len(all_results)} nouvelles lignes dans '{CSV_FILE}'")
        save_to_csv(all_results)
    else:
        print("❗ Aucun nouveau résultat valide trouvé.")

if __name__ == "__main__":
    main()
