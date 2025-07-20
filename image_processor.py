

import os
import re
import base64
from pathlib import Path
from typing import Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Import Surya - optional due to dependency issues
try:
    from surya.detection import DetectionPredictor
    from surya.recognition import RecognitionPredictor
    from surya.input.load import load_from_file
    SURYA_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    print(f"Warning: Surya OCR not available: {e}")
    print("PDF processing will use basic extraction. For better results, fix the dependency issues.")
    SURYA_AVAILABLE = False

class ImageProcessor:
    def __init__(self, output_dir='images'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def process_markdown(self, markdown_path: str) -> str:
        if not SURYA_AVAILABLE:
            # Fallback: just return the original markdown content
            return Path(markdown_path).read_text(encoding='utf-8')
            
        det_predictor = DetectionPredictor()
        rec_predictor = RecognitionPredictor()

        images = load_from_file(markdown_path)
        predictions = rec_predictor(images)

        updated_markdown = Path(markdown_path).read_text(encoding='utf-8')
        img_references = re.findall(r'!\[.*?\]\(.*?\)', updated_markdown)

        for i, pred in enumerate(predictions):
            if i < len(img_references):
                img_filename = f"{Path(markdown_path).stem}_fig_{i+1}.png"
                img_path = self.output_dir / img_filename
                pred.image.save(img_path)
                
                # Replace the old image reference with the new local path
                updated_markdown = updated_markdown.replace(img_references[i], f'![{pred.caption or ""}]({img_path})', 1)

        return updated_markdown

    def process_html(self, url: str) -> Tuple[str, str]:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.title.string if soup.title else 'Untitled'
        markdown_content = ''
        
        # Download and process images
        img_count = 0
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src:
                # Make URL absolute if it's relative
                img_url = urljoin(url, src)
                local_path = self._download_image(img_url, f"html_img_{img_count}")
                if local_path:
                    # Replace src with local path
                    img['src'] = str(local_path)
                    img_count += 1

        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'img']):
            if element.name.startswith('h'):
                level = int(element.name[1])
                markdown_content += f'{"#" * level} {element.get_text(strip=True)}\n\n'
            elif element.name == 'p':
                markdown_content += f'{element.get_text()}\n\n'
            elif element.name == 'img':
                img_url = element.get('src')
                if img_url:
                    img_url = urljoin(url, img_url)
                    img_filename = Path(img_url).name
                    img_path = self.output_dir / img_filename
                    
                    try:
                        img_response = requests.get(img_url)
                        img_response.raise_for_status()
                        with open(img_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        alt_text = element.get('alt', '')
                        markdown_content += f'![{alt_text}]({img_path})\n\n'
                    except Exception as e:
                        print(f"Error downloading image {img_url}: {e}")

        return title, markdown_content

