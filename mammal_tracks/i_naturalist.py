from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import requests
from urllib.parse import urljoin
import logging
from dataclasses import dataclass
from typing import Set, Optional

@dataclass
class ScraperConfig:
    base_url: str = 'https://www.inaturalist.org/observations'
    download_dir: str = './data/i_naturalist'
    log_file: str = 'downloaded_images.txt'
    request_delay: float = 2.0
    scroll_delay: float = 1.0
    page_load_timeout: int = 10
    headless: bool = False

class MammalTrackScraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.downloaded_images: Set[str] = set()
        self.setup_logging()
        self.setup_driver()
        self.setup_storage()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        if self.config.headless:
            options.add_argument('--headless')
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    def setup_storage(self):
        os.makedirs(self.config.download_dir, exist_ok=True)
        if os.path.exists(self.config.log_file):
            with open(self.config.log_file, 'r') as f:
                self.downloaded_images.update(f.read().splitlines())

    def get_search_url(self, page: int) -> str:
        return f"{self.config.base_url}?photos&q=track&iconic_taxa=Mammalia&page={page}"

    def scroll_page(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.config.scroll_delay)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def extract_image_url(self, element) -> Optional[str]:
        style = element.get_attribute('style')
        if style and 'url("' in style:
            return style.split('url("')[1].split('")')[0]
        return None

    def extract_animal_name(self, photo_element) -> str:
        try:
            parent_div = photo_element.find_element(
                By.XPATH,
                "./ancestor::div[@class='thumbnail borderless d-flex flex-column']"
            )
            name_element = parent_div.find_element(
                By.CSS_SELECTOR,
                ".display-name.comname, .secondary-name"
            )
            return name_element.text.replace(' ', '_').lower()
        except Exception as e:
            logging.warning(f"Could not extract animal name: {e}")
            return "unknown_animal"

    def download_image(self, url: str, file_path: str):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            self.downloaded_images.add(url)
            with open(self.config.log_file, 'a') as f:
                f.write(url + '\n')
            
            logging.info(f"Successfully downloaded: {file_path}")
            time.sleep(self.config.request_delay)
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download {url}: {e}")

    def process_page(self, page_number: int) -> bool:
        self.driver.get(self.get_search_url(page_number))
        self.scroll_page()

        try:
            WebDriverWait(self.driver, self.config.page_load_timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.photo.has-photo'))
            )
        except Exception as e:
            logging.info(f"No more images found on page {page_number}")
            return False

        photo_elements = self.driver.find_elements(By.CSS_SELECTOR, '.photo.has-photo')
        
        for i, photo_element in enumerate(photo_elements):
            image_url = self.extract_image_url(photo_element)
            if not image_url or image_url in self.downloaded_images:
                continue

            animal_name = self.extract_animal_name(photo_element)
            file_name = f"{page_number}_{i + 1}_{animal_name}.jpg"
            file_path = os.path.join(self.config.download_dir, file_name)
            
            self.download_image(image_url, file_path)

        return True

    def run(self):
        try:
            page_number = 1
            while self.process_page(page_number):
                page_number += 1
        finally:
            self.driver.quit()

def main():
    config = ScraperConfig()
    scraper = MammalTrackScraper(config)
    scraper.run()

if __name__ == "__main__":
    main()