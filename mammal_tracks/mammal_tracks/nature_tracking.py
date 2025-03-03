from bs4 import BeautifulSoup
import requests
import os
import logging
from dataclasses import dataclass
from typing import List, Optional
import time
from urllib.parse import urljoin
import re

@dataclass
class ScraperConfig:
    base_url: str = 'https://naturetracking.com'
    download_dir: str = 'nature_tracking_data'
    request_delay: float = 2.0
    headers: dict = None

    def __post_init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

class NatureTracking:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.setup_logging()
        self.setup_storage()
        self.session = requests.Session()
        self.session.headers.update(self.config.headers)

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('nature_tracking_scraper.log'),
                logging.StreamHandler()
            ]
        )

    def setup_storage(self):
        os.makedirs(self.config.download_dir, exist_ok=True)

    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
            return None

    def download_image(self, url: str, filename: str):
        try:
            full_url = urljoin(self.config.base_url, url)
            response = self.session.get(full_url)
            response.raise_for_status()
            
            file_path = os.path.join(self.config.download_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logging.info(f"Successfully downloaded: {filename}")
            time.sleep(self.config.request_delay)
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download {url}: {e}")

    def sanitize_filename(self, filename: str) -> str:
        return re.sub(r'[^\w\-_.]', '_', filename)

    def scrape_tracking_guides(self):
        soup = self.get_page_content(self.config.base_url)
        if not soup:
            return

        # Find and process tracking guides
        guide_elements = soup.find_all('article')
        for guide in guide_elements:
            try:
                title = guide.find('h2').text.strip()
                content = guide.find('div', class_='content')
                
                if content:
                    # Save the guide content
                    filename = self.sanitize_filename(f"{title}.txt")
                    with open(os.path.join(self.config.download_dir, filename), 'w', encoding='utf-8') as f:
                        f.write(f"Title: {title}\n\n")
                        f.write(content.get_text(strip=True))

                # Download associated images
                images = guide.find_all('img')
                for i, img in enumerate(images):
                    if img.get('src'):
                        img_filename = self.sanitize_filename(f"{title}_image_{i+1}{os.path.splitext(img['src'])[1]}")
                        self.download_image(img['src'], img_filename)

            except Exception as e:
                logging.error(f"Error processing guide: {e}")

    def scrape_track_database(self):
        database_url = urljoin(self.config.base_url, '/database')
        soup = self.get_page_content(database_url)
        if not soup:
            return

        # Process track database content
        track_entries = soup.find_all('div', class_='track-entry')
        for entry in track_entries:
            try:
                species = entry.find('h3').text.strip()
                details = entry.find('div', class_='details').get_text(strip=True)
                
                # Save track information
                filename = self.sanitize_filename(f"track_{species}.txt")
                with open(os.path.join(self.config.download_dir, filename), 'w', encoding='utf-8') as f:
                    f.write(f"Species: {species}\n\n")
                    f.write(details)

            except Exception as e:
                logging.error(f"Error processing track entry: {e}")

    def run(self):
        logging.info("Starting Nature Tracking scraper")
        self.scrape_tracking_guides()
        self.scrape_track_database()
        logging.info("Scraping completed")

def main():
    config = ScraperConfig()
    scraper = NatureTracking(config)
    scraper.run()

if __name__ == "__main__":
    main()