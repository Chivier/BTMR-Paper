"""
ArXiv paper fetcher supporting HTML, PDF, and source formats
"""
import os
import re
import requests
from typing import Optional, Tuple, List, Dict
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import tempfile
from PIL import Image
import shutil


class ArxivFetcher:
    """Fetch and extract content from arxiv papers"""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.base_url = "https://arxiv.org"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.output_dir = output_dir
        self.images_dir = None
        self.downloaded_images = {}  # Map from original URL to local path
    
    def _extract_arxiv_id(self, url: str) -> Optional[str]:
        """Extract arxiv ID from various URL formats"""
        # Match patterns like: 2301.12345, 2301.12345v1, cs.CV/2301.12345
        patterns = [
            r'arxiv\.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?)',
            r'arxiv\.org/pdf/(\d{4}\.\d{4,5}(?:v\d+)?)',
            r'arxiv\.org/abs/([a-zA-Z\-]+/\d{4}\.\d{4,5}(?:v\d+)?)',
            r'(\d{4}\.\d{4,5}(?:v\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                arxiv_id = match.group(1)
                # Remove version if present
                arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
                return arxiv_id
        
        return None
    
    def _download_image(self, img_url: str, base_url: str, img_index: int) -> Optional[str]:
        """Download an image and return the local path"""
        try:
            # Skip data URLs
            if img_url.startswith('data:'):
                return None
                
            # Handle relative URLs
            if not img_url.startswith(('http://', 'https://')):
                # For ArXiv, images are in the same directory as the HTML
                img_url = urljoin(base_url + '/', img_url)
            
            # Check if already downloaded
            if img_url in self.downloaded_images:
                return self.downloaded_images[img_url]
            
            response = requests.get(img_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '').lower()
            if 'png' in content_type:
                ext = '.png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'gif' in content_type:
                ext = '.gif'
            elif 'svg' in content_type:
                ext = '.svg'
            else:
                # Try to get from URL
                parsed_url = urlparse(img_url)
                path_ext = os.path.splitext(parsed_url.path)[1]
                ext = path_ext if path_ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg'] else '.png'
            
            # Save image
            img_filename = f"arxiv_img_{img_index}{ext}"
            if self.images_dir:
                img_path = os.path.join(self.images_dir, img_filename)
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                
                # Store mapping
                self.downloaded_images[img_url] = img_path
                return img_path
            
        except Exception as e:
            print(f"Failed to download image {img_url}: {e}")
            return None
    
    def fetch_html(self, url: str) -> Tuple[str, Dict[str, str]]:
        """Fetch HTML version of the paper and download images
        
        Returns:
            Tuple of (html_content_with_modified_img_tags, image_mapping)
        """
        arxiv_id = self._extract_arxiv_id(url)
        if not arxiv_id:
            raise ValueError(f"Could not extract arxiv ID from URL: {url}")
        
        # Setup images directory if output_dir is provided
        if self.output_dir:
            self.images_dir = os.path.join(self.output_dir, 'images')
            os.makedirs(self.images_dir, exist_ok=True)
        
        # Try HTML version first
        html_url = f"{self.base_url}/html/{arxiv_id}"
        response = requests.get(html_url, headers=self.headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract main content
            content = soup.find('div', {'class': 'ltx_page_main'})
            if content:
                # Download all images
                img_index = 1
                for img in content.find_all('img'):
                    img_url = img.get('src', '')
                    if img_url:
                        local_path = self._download_image(img_url, html_url, img_index)
                        if local_path:
                            # Update img tag with local path
                            img['src'] = local_path
                            img_index += 1
                
                # Return HTML string with updated image paths
                return str(content), self.downloaded_images
        
        # Fallback to abstract page
        abs_url = f"{self.base_url}/abs/{arxiv_id}"
        response = requests.get(abs_url, headers=self.headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('h1', {'class': 'title'})
            title_text = title.get_text(strip=True) if title else ""
            
            # Extract authors
            authors = soup.find('div', {'class': 'authors'})
            authors_text = authors.get_text(strip=True) if authors else ""
            
            # Extract abstract
            abstract = soup.find('blockquote', {'class': 'abstract'})
            abstract_text = abstract.get_text(strip=True) if abstract else ""
            
            html_content = f"<div><h1>{title_text}</h1><p>{authors_text}</p><p>{abstract_text}</p></div>"
            return html_content, {}
        
        raise Exception(f"Failed to fetch HTML content for arxiv ID: {arxiv_id}")
    
    def fetch_pdf(self, url: str) -> str:
        """Fetch and extract text from PDF version using Surya OCR"""
        arxiv_id = self._extract_arxiv_id(url)
        if not arxiv_id:
            raise ValueError(f"Could not extract arxiv ID from URL: {url}")
        
        pdf_url = f"{self.base_url}/pdf/{arxiv_id}.pdf"
        
        # Download PDF to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            response = requests.get(pdf_url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            
            tmp_path = tmp_file.name
        
        try:
            # Import Surya components
            from surya.ocr import run_ocr
            from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
            from surya.model.recognition.model import load_model as load_rec_model
            from surya.model.recognition.processor import load_processor as load_rec_processor
            from surya.input.load import load_pdf
            
            # Load models
            print("Loading Surya OCR models...")
            det_model = load_det_model()
            det_processor = load_det_processor()
            rec_model = load_rec_model()
            rec_processor = load_rec_processor()
            
            # Load PDF pages as images
            print(f"Processing PDF: {arxiv_id}.pdf")
            images = load_pdf(tmp_path)
            
            # Run OCR on all pages
            print(f"Running OCR on {len(images)} pages...")
            predictions = run_ocr(
                images, 
                [["en", "zh"]]*len(images),  # Support English and Chinese
                det_model, 
                det_processor,
                rec_model, 
                rec_processor
            )
            
            # Extract text from predictions
            text_content = []
            for page_idx, page_pred in enumerate(predictions):
                page_text = []
                for text_line in page_pred.text_lines:
                    page_text.append(text_line.text)
                
                if page_text:
                    text_content.append(f"\n--- Page {page_idx + 1} ---\n")
                    text_content.append('\n'.join(page_text))
            
            return '\n'.join(text_content)
        
        except ImportError as e:
            print(f"Surya not installed, falling back to PyPDF2: {e}")
            # Fallback to PyPDF2 if Surya is not available
            try:
                import PyPDF2
                text_content = []
                with open(tmp_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        text_content.append(text)
                
                return '\n'.join(text_content)
            except Exception as e2:
                raise Exception(f"Both Surya and PyPDF2 failed: Surya error: {e}, PyPDF2 error: {e2}")
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def fetch_source(self, url: str) -> str:
        """Fetch LaTeX source of the paper"""
        arxiv_id = self._extract_arxiv_id(url)
        if not arxiv_id:
            raise ValueError(f"Could not extract arxiv ID from URL: {url}")
        
        source_url = f"{self.base_url}/e-print/{arxiv_id}"
        
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            response = requests.get(source_url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            
            tmp_path = tmp_file.name
        
        try:
            import tarfile
            import gzip
            
            # Try to extract as tar.gz first
            try:
                with tarfile.open(tmp_path, 'r:gz') as tar:
                    # Look for main tex file
                    tex_files = [f for f in tar.getnames() if f.endswith('.tex')]
                    
                    if tex_files:
                        # Extract and read the main tex file
                        main_tex = None
                        for tex_file in tex_files:
                            if 'main' in tex_file.lower() or len(tex_files) == 1:
                                main_tex = tex_file
                                break
                        
                        if not main_tex:
                            main_tex = tex_files[0]
                        
                        member = tar.getmember(main_tex)
                        f = tar.extractfile(member)
                        if f:
                            content = f.read().decode('utf-8', errors='ignore')
                            return content
            
            except tarfile.ReadError:
                # Maybe it's just a gzipped tex file
                with gzip.open(tmp_path, 'rt', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        raise Exception(f"Failed to extract source for arxiv ID: {arxiv_id}")
    
    def fetch(self, url: str, format: str = "auto") -> Tuple[str, str, Dict[str, str]]:
        """
        Fetch paper content in specified format
        
        Args:
            url: ArXiv URL or ID
            format: "html", "pdf", "source", or "auto" (tries html, then pdf)
            
        Returns:
            Tuple of (content, format_used, image_mapping)
        """
        if format == "auto":
            # Try HTML first (usually cleaner text)
            try:
                html_content, image_mapping = self.fetch_html(url)
                return html_content, "html", image_mapping
            except Exception as e:
                print(f"HTML fetch failed: {e}, trying PDF...")
                try:
                    content = self.fetch_pdf(url)
                    return content, "pdf", {}
                except Exception as e:
                    print(f"PDF fetch failed: {e}, trying source...")
                    content = self.fetch_source(url)
                    return content, "source", {}
        
        elif format == "html":
            html_content, image_mapping = self.fetch_html(url)
            return html_content, "html", image_mapping
        elif format == "pdf":
            return self.fetch_pdf(url), "pdf", {}
        elif format == "source":
            return self.fetch_source(url), "source", {}
        else:
            raise ValueError(f"Unknown format: {format}")