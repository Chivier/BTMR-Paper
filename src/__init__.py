"""
BTMR (Beautiful Text Mining Reader) - Core Modules

This package contains the core modules for extracting and summarizing academic papers
from ArXiv using LLM APIs.
"""

__version__ = "1.0.0"
__author__ = "BTMR Team"

# Import main components for easier access
from .arxiv_fetcher import ArxivFetcher
from .paper_extractor import OpenAIExtractor
from .html_generator import HTMLGenerator
from .pdf_generator import PDFGenerator
from .image_processor import ImageProcessor

__all__ = [
    'ArxivFetcher',
    'OpenAIExtractor',
    'HTMLGenerator',
    'PDFGenerator',
    'ImageProcessor'
]