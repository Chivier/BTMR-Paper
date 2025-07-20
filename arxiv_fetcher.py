"""
ArXiv paper fetcher supporting HTML, PDF, and source formats
"""
import os
import re
import requests
from typing import Optional, Tuple, List
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import tempfile
from PIL import Image


class ArxivFetcher:
    """Fetch and extract content from arxiv papers"""
    
    def __init__(self):
        self.base_url = "https://arxiv.org"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
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
    
    def fetch_html(self, url: str) -> str:
        """Fetch HTML version of the paper"""
        arxiv_id = self._extract_arxiv_id(url)
        if not arxiv_id:
            raise ValueError(f"Could not extract arxiv ID from URL: {url}")
        
        # Try HTML version first
        html_url = f"{self.base_url}/html/{arxiv_id}"
        response = requests.get(html_url, headers=self.headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract main content
            content = soup.find('div', {'class': 'ltx_page_main'})
            if content:
                return content.get_text(separator='\n', strip=True)
        
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
            
            return f"Title: {title_text}\n\nAuthors: {authors_text}\n\nAbstract: {abstract_text}"
        
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
    
    def fetch(self, url: str, format: str = "auto") -> Tuple[str, str]:
        """
        Fetch paper content in specified format
        
        Args:
            url: ArXiv URL or ID
            format: "html", "pdf", "source", or "auto" (tries html, then pdf)
            
        Returns:
            Tuple of (content, format_used)
        """
        if format == "auto":
            # Try HTML first (usually cleaner text)
            try:
                content = self.fetch_html(url)
                return content, "html"
            except Exception as e:
                print(f"HTML fetch failed: {e}, trying PDF...")
                try:
                    content = self.fetch_pdf(url)
                    return content, "pdf"
                except Exception as e:
                    print(f"PDF fetch failed: {e}, trying source...")
                    content = self.fetch_source(url)
                    return content, "source"
        
        elif format == "html":
            return self.fetch_html(url), "html"
        elif format == "pdf":
            return self.fetch_pdf(url), "pdf"
        elif format == "source":
            return self.fetch_source(url), "source"
        else:
            raise ValueError(f"Unknown format: {format}")