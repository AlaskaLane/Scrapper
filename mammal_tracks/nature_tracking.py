import logging
import time
import os
import pandas as pd
import requests
from functools import wraps
from dataclasses import dataclass
from typing import List, Dict
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('scraper.log'), logging.StreamHandler()]
)

@dataclass
class TrackedAnimal:
    scientific_name: str
    tracks: List[Dict[str, str]]

def retry_decorator(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logging.warning(f"Attempt {attempt+1} failed: {str(e)}")
                time.sleep(2 ** attempt)
        return None
    return wrapper

class MammalTracksScraper:
    def __init__(self, headless=True):
        self.driver = self._init_driver(headless)
        self.wait = WebDriverWait(self.driver, 20)

    def _init_driver(self, headless):
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def _close_popups(self):
        """Ferme toutes les fenêtres superposées"""
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.shiftnav-main-toggle-content, .cookie-notice-container')
                    .forEach(el => el.remove());
            """)
        except:
            pass

    def _click_load_more(self):
        """Gestion améliorée du bouton Load More"""
        try:
            # Attendre que le bouton soit disponible
            load_more = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.jig-loadMoreButton")
                )
            )

            # Scroll précis jusqu'au bouton
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                load_more
            )

            # Attendre que le bouton soit cliquable
            self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div.jig-loadMoreButton")
            ))

            # Double vérification de la visibilité
            ActionChains(self.driver).move_to_element(load_more).perform()

            # Cliquer avec JavaScript
            self.driver.execute_script("arguments[0].click();", load_more)
            logging.info("Bouton Load More cliqué avec succès")

            # Attendre le chargement
            self.wait.until(
                lambda d: d.find_element(By.CSS_SELECTOR, "div.jig-loadMoreButton")
                .text != "Load more"
            )
            return True

        except TimeoutException:
            logging.info("Aucun nouveau contenu à charger")
            return False
        except Exception as e:
            logging.error(f"Échec du clic sur Load More: {str(e)}")
            return False

    def _load_all_content(self):
        """Chargement complet avec vérification des images"""
        last_count = 0
        unchanged = 0
        
        while True:
            self._close_popups()
            
            # Vérifier les nouvelles images
            containers = self.driver.find_elements(By.CSS_SELECTOR, ".jig-imageContainer")
            if len(containers) == last_count:
                unchanged += 1
                if unchanged > 2:
                    break
            else:
                last_count = len(containers)
                unchanged = 0
            
            # Tenter de charger plus de contenu
            if not self._click_load_more():
                break

        # Dernière vérification
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.02)

    def _extract_track_data(self, container):
        try:
            # Récupérer le lien principal depuis la balise <a>
            link_element = container.find_element(By.CSS_SELECTOR, "a.jig-link")
            href = link_element.get_attribute('href')
            
            # Récupérer le titre depuis la caption
            title_element = container.find_element(By.CSS_SELECTOR, ".jig-caption-title")
            title = title_element.text.strip()
            
            # Récupérer l'image de preview
            img_element = link_element.find_element(By.CSS_SELECTOR, "img.jig-photo-image")
            img_src = img_element.get_attribute('src') or img_element.get_attribute('data-src')
            
            return {
                "animal_name": title,
                "image_url": href,  # Utiliser le href principal comme URL finale
                "preview_url": img_src,  # Conserver l'URL de preview si nécessaire
                "filename": os.path.basename(urlparse(href).path)
            }
        except NoSuchElementException:
            return None

    @retry_decorator
    def scrape_tracks(self):
        try:
            self.driver.get("https://naturetracking.com/mammal-tracks/")
            
            # Sélection du filtre Tracks
            self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div[data-filter-slug='tracks']")
            )).click()
            time.sleep(0.05)  # Réduire le temps d'attente

            # Chargement complet
            self._load_all_content()

            # Extraction finale avec le bon sélecteur
            links = self.driver.find_elements(By.CSS_SELECTOR, ".jig-imageContainer a.jig-link")
            tracks = []
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    title = link.find_element(By.CSS_SELECTOR, ".jig-caption-title").text
                    tracks.append({
                        "animal_name": title.strip(),
                        "image_url": href,
                        "filename": os.path.basename(urlparse(href).path)
                    })
                except NoSuchElementException:
                    continue
            
            return TrackedAnimal(
                scientific_name="Mammal Tracks Gallery",
                tracks=tracks
            )

        except Exception as e:
            logging.error(f"Erreur majeure: {str(e)}")
            self.driver.save_screenshot('error.png')
            return None

    def download_images(self, data, output_dir="nature_tracking"):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/*,*/*;q=0.8',
            'Referer': 'https://naturetracking.com/'
        }
        
        for item in data:
            try:
                # Nettoyer le nom de l'animal pour le dossier
                animal_name = item['animal_name'].strip().replace(' ', '_').lower()
                animal_dir = os.path.join(output_dir, animal_name)
                os.makedirs(animal_dir, exist_ok=True)

                # Télécharger dans le dossier de l'espèce
                filename = os.path.basename(urlparse(item['image_url']).path)
                filepath = os.path.join(animal_dir, filename)

                filepath = os.path.join('data', filepath)

                encoded_url = requests.utils.quote(item['image_url'], safe=":/")

                response = requests.get(encoded_url, stream=True, headers=headers)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                item['local_path'] = filepath
                print(f"Image téléchargée : {filepath}")
            except Exception as e:
                logging.error(f"Échec téléchargement {item['image_url']}: {str(e)}")
        return data

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = MammalTracksScraper(headless=False)
    try:
        result = scraper.scrape_tracks()
        if result:
            df = pd.DataFrame(result.tracks)
            print(f"\nNombre d'entrées récupérées: {len(df)}")
            
            if len(df) > 0:
                scraper.download_images(df.to_dict('records'))
                df.to_csv("tracks.csv", index=False)
                print(f"Exemple de données:\n{df.head().to_markdown()}")
            else:
                print("Aucune donnée valide trouvée!")
                
    except Exception as e:
        logging.error(f"Erreur d'exécution: {str(e)}")
    finally:
        scraper.close()