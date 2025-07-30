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
            'file_size_kb',
            'status',
            'error_message',
            'retry_count',
            'last_failed_at'
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
                  language: str = "en",
                  status: str = "completed",
                  error_message: Optional[str] = None):
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
            status: Processing status (completed/failed)
            error_message: Error message if processing failed
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
            'file_size_kb': f"{file_size_kb:.1f}",
            'status': status,
            'error_message': error_message or '',
            'retry_count': '0',
            'last_failed_at': datetime.now().isoformat() if status == 'failed' else ''
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

    def log_failed_paper(self, 
                        paper_id: str,
                        title: str,
                        authors: list,
                        arxiv_url: Optional[str],
                        format_used: str,
                        output_format: str,
                        error_message: str,
                        processing_time: float = 0.0,
                        language: str = "en"):
        """
        Log a failed paper processing attempt.
        
        Args:
            paper_id: Unique identifier for the paper
            title: Paper title
            authors: List of author names
            arxiv_url: Original ArXiv URL (if applicable)
            format_used: Format used for extraction attempt
            output_format: Intended output format
            error_message: Error message describing the failure
            processing_time: Time taken before failure
            language: Language of output (en/zh)
        """
        row_data = {
            'timestamp': datetime.now().isoformat(),
            'paper_id': paper_id,
            'title': title[:100],
            'authors': '; '.join(authors[:3]),
            'arxiv_url': arxiv_url or '',
            'format_used': format_used,
            'output_format': output_format,
            'output_path': '',
            'pdf_path': '',
            'num_figures': '0',
            'num_tables': '0',
            'processing_time': f"{processing_time:.2f}",
            'language': language,
            'file_size_kb': '0',
            'status': 'failed',
            'error_message': error_message,
            'retry_count': '0',
            'last_failed_at': datetime.now().isoformat()
        }
        
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(row_data)

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get paper metadata by ID.
        
        Args:
            paper_id: Paper ID to search for
            
        Returns:
            Paper metadata dict or None if not found
        """
        if not os.path.exists(self.csv_path):
            return None
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['paper_id'] == paper_id:
                    return row
        return None

    def update_retry_count(self, paper_id: str) -> bool:
        """
        Increment retry count for a paper and update last_failed_at.
        
        Args:
            paper_id: Paper ID to update
            
        Returns:
            True if updated successfully, False if paper not found
        """
        if not os.path.exists(self.csv_path):
            return False
        
        # Read all rows
        rows = []
        updated = False
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['paper_id'] == paper_id:
                    # Update retry count and last_failed_at
                    current_count = int(row.get('retry_count', '0'))
                    row['retry_count'] = str(current_count + 1)
                    row['last_failed_at'] = datetime.now().isoformat()
                    row['status'] = 'failed'
                    updated = True
                rows.append(row)
        
        if updated:
            # Write back all rows
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        
        return updated

    def update_paper_status(self, paper_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """
        Update paper status and optionally error message.
        
        Args:
            paper_id: Paper ID to update
            status: New status
            error_message: Optional error message
            
        Returns:
            True if updated successfully, False if paper not found
        """
        if not os.path.exists(self.csv_path):
            return False
        
        # Read all rows
        rows = []
        updated = False
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['paper_id'] == paper_id:
                    row['status'] = status
                    if error_message:
                        row['error_message'] = error_message
                    if status == 'failed':
                        row['last_failed_at'] = datetime.now().isoformat()
                    updated = True
                rows.append(row)
        
        if updated:
            # Write back all rows
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        
        return updated
