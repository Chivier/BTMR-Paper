

import os
import re
import base64
import tempfile
from pathlib import Path
from typing import Tuple, Dict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Import Surya - optional due to dependency issues
try:
    from surya.detection import DetectionPredictor
    from surya.recognition import RecognitionPredictor
    from surya.input.load import load_from_file
    from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
    from surya.model.recognition.model import load_model as load_rec_model
    from surya.model.recognition.processor import load_processor as load_rec_processor
    from surya.input.load import load_pdf
    SURYA_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    print(f"Warning: Surya OCR not available: {e}")
    print("PDF processing will use basic extraction. For better results, fix the dependency issues.")
    SURYA_AVAILABLE = False

class ImageProcessor:
    def __init__(self, output_dir='images'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def process_markdown(self, markdown_path: str) -> Tuple[str, dict]:
        image_mapping = {}
        if not SURYA_AVAILABLE:
            # Fallback: just return the original markdown content
            return Path(markdown_path).read_text(encoding='utf-8'), image_mapping
            
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
                image_mapping[img_references[i]] = str(img_path)

        return updated_markdown, image_mapping

    def process_html(self, url: str) -> Tuple[str, str, dict]:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.title.string if soup.title else 'Untitled'
        markdown_content = ''
        image_mapping = {}
        
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
                    image_mapping[img_url] = str(local_path)
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
                        image_mapping[img_url] = str(img_path)
                    except Exception as e:
                        print(f"Error downloading image {img_url}: {e}")

        return title, markdown_content, image_mapping

    def process_pdf(self, pdf_path: str) -> Tuple[str, str, Dict]:
        """
        Process uploaded PDF file and extract text content.
        
        Args:
            pdf_path: Path to the uploaded PDF file
            
        Returns:
            Tuple of (content, format_used, image_mapping)
        """
        print(f"Processing uploaded PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        image_mapping = {}
        
        # Try Surya OCR first (advanced OCR with better accuracy)
        if SURYA_AVAILABLE:
            try:
                print("Using Surya OCR for PDF processing...")
                
                # Load models
                det_model, det_processor = load_det_model(), load_det_processor()
                rec_model, rec_processor = load_rec_model(), load_rec_processor()
                
                # Load PDF pages as images
                images = load_pdf(pdf_path)
                print(f"Loaded {len(images)} pages from PDF")
                
                # Perform OCR on each page
                det_predictor = DetectionPredictor(det_model, det_processor)
                rec_predictor = RecognitionPredictor(rec_model, rec_processor)
                
                # Process text detection and recognition
                det_results = det_predictor(images)
                rec_results = rec_predictor(images, det_results)
                
                # Extract text from all pages
                full_text = []
                for page_idx, page_result in enumerate(rec_results):
                    page_text = []
                    for line in page_result.text_lines:
                        page_text.append(line.text)
                    
                    if page_text:
                        full_text.append(f"=== Page {page_idx + 1} ===")
                        full_text.extend(page_text)
                        full_text.append("")  # Add blank line between pages
                    
                    # Save page image for reference
                    if hasattr(page_result, 'image') and page_result.image:
                        img_filename = f"pdf_page_{page_idx + 1}.png"
                        img_path = self.output_dir / img_filename
                        page_result.image.save(img_path)
                        image_mapping[f"page_{page_idx + 1}"] = {
                            "url": str(img_path),
                            "caption": f"PDF Page {page_idx + 1}",
                            "caption_tag": f"Figure {page_idx + 1}:"
                        }
                
                content = "\n".join(full_text)
                if content.strip():
                    print(f"Surya OCR extracted {len(content)} characters from PDF")
                    return content, "pdf", image_mapping
                else:
                    print("Surya OCR produced empty content, falling back to PyPDF2...")
                    
            except Exception as e:
                print(f"Surya OCR failed: {e}, falling back to PyPDF2...")
        
        # Fallback to PyPDF2 for basic text extraction
        try:
            import PyPDF2
            print("Using PyPDF2 for PDF text extraction...")
            
            text_content = []
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                print(f"PDF has {len(pdf_reader.pages)} pages")
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text.strip():
                        text_content.append(f"=== Page {page_num + 1} ===")
                        text_content.append(text)
                        text_content.append("")  # Add blank line between pages
            
            content = "\n".join(text_content)
            
            if content.strip():
                print(f"PyPDF2 extracted {len(content)} characters from PDF")
                return content, "pdf", image_mapping
            else:
                raise Exception("PDF appears to be image-based or corrupted - no text could be extracted")
                
        except ImportError:
            raise Exception("PyPDF2 not available. Please install it with: pip install PyPDF2")
        except Exception as e:
            raise Exception(f"PDF text extraction failed: {str(e)}")

    def _download_image(self, img_url: str, base_filename: str) -> Path:
        """Download image from URL and save locally."""
        try:
            response = requests.get(img_url, timeout=10)
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            else:
                ext = '.jpg'  # Default fallback
            
            filename = f"{base_filename}{ext}"
            img_path = self.output_dir / filename
            
            with open(img_path, 'wb') as f:
                f.write(response.content)
            
            return img_path
            
        except Exception as e:
            print(f"Failed to download image {img_url}: {e}")
            return None
