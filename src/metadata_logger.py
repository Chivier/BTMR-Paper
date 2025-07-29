"""
Metadata Logger Module

This module handles logging paper metadata to CSV files for tracking
and management purposes.
"""
import csv
import os
from datetime import datetime
from typing import Dict, Any, Optional
import json


class MetadataLogger:
    """
    Handles logging paper processing metadata to CSV files.
    
    Attributes:
        csv_path (str): Path to the CSV file where metadata is stored
        fieldnames (list): List of CSV column names
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the metadata logger.
        
        Args:
            output_dir: Directory where output files are stored
        """
        self.output_dir = output_dir
        self.csv_path = os.path.join(output_dir, "paper_metadata.csv")
        self.fieldnames = [
            'timestamp',
            'paper_id',
            'title',
            'authors',
            'arxiv_url',
            'format_used',
            'output_format',
            'output_path',
            'pdf_path',
            'num_figures',
            'num_tables',
            'processing_time',
            'language',
            'file_size_kb'
        ]
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize CSV file with headers if it doesn't exist
        if not os.path.exists(self.csv_path):
            self._init_csv()
    
    def _init_csv(self):
        """Initialize CSV file with headers."""
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
    
    def log_paper(self, 
                  paper_id: str,
                  title: str,
                  authors: list,
                  arxiv_url: Optional[str],
                  format_used: str,
                  output_format: str,
                  output_path: str,
                  pdf_path: Optional[str],
                  extracted_data: Dict[str, Any],
                  processing_time: float,
                  language: str = "en"):
        """
        Log paper metadata to CSV file.
        
        Args:
            paper_id: Unique identifier for the paper
            title: Paper title
            authors: List of author names
            arxiv_url: Original ArXiv URL (if applicable)
            format_used: Format used for extraction (html/pdf/source)
            output_format: Output format (html/pdf)
            output_path: Path to the generated output file
            pdf_path: Path to the generated PDF file (if applicable)
            extracted_data: Full extracted data dictionary
            processing_time: Time taken to process in seconds
            language: Language of output (en/zh)
        """
        # Count figures and tables
        num_figures = 0
        num_tables = 0
        
        # Count method figures
        for subsection in extracted_data.get("method", {}).get("subsections", []):
            num_figures += len(subsection.get("figures", []))
        
        # Count results figures and tables
        results = extracted_data.get("results", {})
        for subsection in results.get("subsections", []):
            num_figures += len(subsection.get("figures", []))
        num_tables = len(results.get("tables", []))
        
        # Get file size
        file_size_kb = 0
        if os.path.exists(output_path):
            file_size_kb = os.path.getsize(output_path) / 1024
        
        # Prepare row data
        row_data = {
            'timestamp': datetime.now().isoformat(),
            'paper_id': paper_id,
            'title': title[:100],  # Limit title length
            'authors': '; '.join(authors[:3]),  # First 3 authors
            'arxiv_url': arxiv_url or '',
            'format_used': format_used,
            'output_format': output_format,
            'output_path': output_path,
            'pdf_path': pdf_path or '',
            'num_figures': num_figures,
            'num_tables': num_tables,
            'processing_time': f"{processing_time:.2f}",
            'language': language,
            'file_size_kb': f"{file_size_kb:.1f}"
        }
        
        # Write to CSV
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(row_data)
    
    def get_recent_papers(self, limit: int = 10) -> list:
        """
        Get recent paper entries from the CSV.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of dictionaries containing paper metadata
        """
        if not os.path.exists(self.csv_path):
            return []
        
        papers = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            papers = list(reader)
        
        # Return most recent papers
        return papers[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about processed papers.
        
        Returns:
            Dictionary containing statistics
        """
        if not os.path.exists(self.csv_path):
            return {
                'total_papers': 0,
                'total_figures': 0,
                'total_tables': 0,
                'avg_processing_time': 0,
                'total_size_mb': 0
            }
        
        papers = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            papers = list(reader)
        
        if not papers:
            return {
                'total_papers': 0,
                'total_figures': 0,
                'total_tables': 0,
                'avg_processing_time': 0,
                'total_size_mb': 0
            }
        
        total_figures = sum(int(p.get('num_figures', 0)) for p in papers)
        total_tables = sum(int(p.get('num_tables', 0)) for p in papers)
        total_time = sum(float(p.get('processing_time', 0)) for p in papers)
        total_size_kb = sum(float(p.get('file_size_kb', 0)) for p in papers)
        
        return {
            'total_papers': len(papers),
            'total_figures': total_figures,
            'total_tables': total_tables,
            'avg_processing_time': total_time / len(papers),
            'total_size_mb': total_size_kb / 1024,
            'formats_used': self._count_formats(papers),
            'languages': self._count_languages(papers)
        }
    
    def _count_formats(self, papers: list) -> Dict[str, int]:
        """Count occurrences of each format."""
        formats = {}
        for p in papers:
            fmt = p.get('output_format', 'unknown')
            formats[fmt] = formats.get(fmt, 0) + 1
        return formats
    
    def _count_languages(self, papers: list) -> Dict[str, int]:
        """Count occurrences of each language."""
        languages = {}
        for p in papers:
            lang = p.get('language', 'en')
            languages[lang] = languages.get(lang, 0) + 1
        return languages