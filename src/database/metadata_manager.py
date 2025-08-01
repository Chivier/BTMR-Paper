"""
Database-backed metadata manager for BTMR Paper project.

Replaces the CSV-based MetadataLogger with a database-backed solution
that uses the DatabaseInterface for persistence.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from .interface import DatabaseInterface, PaperRecord
from .sqlite_impl import SQLiteDatabase, DatabaseConfig


class DatabaseMetadataManager:
    """
    Database-backed metadata manager that replaces the CSV-based MetadataLogger.
    
    This class provides the same interface as MetadataLogger but uses
    a SQL database for storage instead of CSV files.
    """

    def __init__(self, database: Optional[DatabaseInterface] = None, output_dir: str = "output"):
        """
        Initialize the database metadata manager.
        
        Args:
            database: DatabaseInterface implementation to use. If None, creates SQLite database.
            output_dir: Directory where output files are stored
        """
        self.output_dir = output_dir
        
        if database is None:
            # Create default SQLite database
            db_path = os.path.join(output_dir, "paper_metadata.db")
            config = DatabaseConfig(connection_string=db_path)
            self.database = SQLiteDatabase(config)
        else:
            self.database = database
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

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
        Log paper metadata to database.
        
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
        # Count figures and tables from extracted data
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
        
        # Create paper record
        paper_record = PaperRecord(
            paper_id=paper_id,
            title=title[:100],  # Limit title length
            authors='; '.join(authors[:3]),  # First 3 authors
            arxiv_url=arxiv_url,
            format_used=format_used,
            output_format=output_format,
            output_path=output_path,
            pdf_path=pdf_path,
            num_figures=num_figures,
            num_tables=num_tables,
            processing_time=processing_time,
            language=language,
            file_size_kb=file_size_kb,
            status=status,
            error_message=error_message,
            retry_count=0,
            timestamp=datetime.now(),
            last_failed_at=datetime.now() if status == 'failed' else None
        )
        
        # Insert into database
        self.database.insert_paper(paper_record)

    def log_failed_paper(self, 
                        paper_id: str,
                        title: str,
                        authors: list,
                        arxiv_url: Optional[str],
                        format_used: str,
                        output_format: str,
                        error_message: str,
                        processing_time: float = 0.0,
                        language: str = "en",
                        expected_output_path: Optional[str] = None,
                        expected_pdf_path: Optional[str] = None):
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
            expected_output_path: Expected path where HTML output would have been saved
            expected_pdf_path: Expected path where PDF output would have been saved
        """
        paper_record = PaperRecord(
            paper_id=paper_id,
            title=title[:100],
            authors='; '.join(authors[:3]),
            arxiv_url=arxiv_url,
            format_used=format_used,
            output_format=output_format,
            output_path=expected_output_path or '',
            pdf_path=expected_pdf_path,
            num_figures=0,
            num_tables=0,
            processing_time=processing_time,
            language=language,
            file_size_kb=0.0,
            status='failed',
            error_message=error_message,
            retry_count=0,
            timestamp=datetime.now(),
            last_failed_at=datetime.now()
        )
        
        self.database.insert_paper(paper_record)

    def get_recent_papers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent paper entries from the database.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of dictionaries containing paper metadata
        """
        papers = self.database.get_recent_papers(limit=limit)
        
        # Convert PaperRecord objects to dictionaries for compatibility
        result = []
        for paper in papers:
            paper_dict = {
                'paper_id': paper.paper_id,
                'title': paper.title,
                'authors': paper.authors,
                'arxiv_url': paper.arxiv_url,
                'format_used': paper.format_used,
                'output_format': paper.output_format,
                'output_path': paper.output_path,
                'pdf_path': paper.pdf_path,
                'num_figures': str(paper.num_figures),
                'num_tables': str(paper.num_tables),
                'processing_time': str(paper.processing_time),
                'language': paper.language,
                'file_size_kb': str(paper.file_size_kb),
                'status': paper.status,
                'error_message': paper.error_message,
                'retry_count': str(paper.retry_count),
                'timestamp': paper.timestamp.isoformat(),
                'last_failed_at': paper.last_failed_at.isoformat() if paper.last_failed_at else ''
            }
            result.append(paper_dict)
        
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about processed papers.
        
        Returns:
            Dictionary containing statistics
        """
        return self.database.get_statistics()

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get paper metadata by ID.
        
        Args:
            paper_id: Paper ID to search for
            
        Returns:
            Paper metadata dict or None if not found
        """
        paper = self.database.get_paper_by_id(paper_id)
        
        if paper is None:
            return None
        
        # Convert to dictionary for compatibility
        return {
            'paper_id': paper.paper_id,
            'title': paper.title,
            'authors': paper.authors,
            'arxiv_url': paper.arxiv_url,
            'format_used': paper.format_used,
            'output_format': paper.output_format,
            'output_path': paper.output_path,
            'pdf_path': paper.pdf_path,
            'num_figures': str(paper.num_figures),
            'num_tables': str(paper.num_tables),
            'processing_time': str(paper.processing_time),
            'language': paper.language,
            'file_size_kb': str(paper.file_size_kb),
            'status': paper.status,
            'error_message': paper.error_message,
            'retry_count': str(paper.retry_count),
            'timestamp': paper.timestamp.isoformat(),
            'last_failed_at': paper.last_failed_at.isoformat() if paper.last_failed_at else ''
        }

    def update_retry_count(self, paper_id: str) -> bool:
        """
        Increment retry count for a paper and update last_failed_at.
        
        Args:
            paper_id: Paper ID to update
            
        Returns:
            True if updated successfully, False if paper not found
        """
        return self.database.update_retry_count(paper_id)

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
        return self.database.update_paper_status(paper_id, status, error_message)

    def delete_paper(self, paper_id: str) -> bool:
        """
        Delete a paper record.
        
        Args:
            paper_id: Paper ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        return self.database.delete_paper(paper_id)

    def get_papers_paginated(
        self, 
        page: int = 1, 
        per_page: int = 20,
        search: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get paginated list of papers with optional search.
        
        Args:
            page: Page number (1-based)
            per_page: Number of papers per page
            search: Optional search term
            
        Returns:
            Tuple of (papers list, total count)
        """
        offset = (page - 1) * per_page
        papers = self.database.get_recent_papers(limit=per_page, offset=offset, search=search)
        total = self.database.get_papers_count(search=search)
        
        # Convert to dictionaries for compatibility
        papers_dict = []
        for paper in papers:
            paper_dict = {
                'paper_id': paper.paper_id,
                'title': paper.title,
                'authors': paper.authors,
                'arxiv_url': paper.arxiv_url,
                'format_used': paper.format_used,
                'output_format': paper.output_format,
                'output_path': paper.output_path,
                'pdf_path': paper.pdf_path,
                'num_figures': str(paper.num_figures),
                'num_tables': str(paper.num_tables),
                'processing_time': str(paper.processing_time),
                'language': paper.language,
                'file_size_kb': str(paper.file_size_kb),
                'status': paper.status,
                'error_message': paper.error_message,
                'retry_count': str(paper.retry_count),
                'timestamp': paper.timestamp.isoformat(),
                'last_failed_at': paper.last_failed_at.isoformat() if paper.last_failed_at else ''
            }
            papers_dict.append(paper_dict)
        
        return papers_dict, total

    def migrate_from_csv(self, csv_path: str) -> bool:
        """
        Migrate existing CSV data to the database.
        
        Args:
            csv_path: Path to the existing CSV file
            
        Returns:
            True if migration was successful, False otherwise
        """
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return False
        
        try:
            import csv
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Parse timestamp
                    try:
                        timestamp = datetime.fromisoformat(row['timestamp'])
                    except:
                        timestamp = datetime.now()
                    
                    # Parse last_failed_at
                    last_failed_at = None
                    if row.get('last_failed_at'):
                        try:
                            last_failed_at = datetime.fromisoformat(row['last_failed_at'])
                        except:
                            pass
                    
                    # Create paper record
                    paper_record = PaperRecord(
                        paper_id=row['paper_id'],
                        title=row['title'],
                        authors=row['authors'],
                        arxiv_url=row.get('arxiv_url'),
                        format_used=row['format_used'],
                        output_format=row['output_format'],
                        output_path=row['output_path'],
                        pdf_path=row.get('pdf_path'),
                        num_figures=int(row.get('num_figures', 0)),
                        num_tables=int(row.get('num_tables', 0)),
                        processing_time=float(row.get('processing_time', 0.0)),
                        language=row.get('language', 'en'),
                        file_size_kb=float(row.get('file_size_kb', 0.0)),
                        status=row.get('status', 'completed'),
                        error_message=row.get('error_message'),
                        retry_count=int(row.get('retry_count', 0)),
                        timestamp=timestamp,
                        last_failed_at=last_failed_at
                    )
                    
                    # Insert into database
                    self.database.insert_paper(paper_record)
            
            print(f"Successfully migrated data from {csv_path}")
            return True
        
        except Exception as e:
            print(f"Error migrating from CSV: {e}")
            return False

    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path where backup should be stored
            
        Returns:
            True if successful, False otherwise
        """
        return self.database.backup_data(backup_path)

    def restore_database(self, backup_path: str) -> bool:
        """
        Restore database from a backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if successful, False otherwise
        """
        return self.database.restore_data(backup_path)

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database.
        
        Returns:
            Dictionary containing health check results
        """
        is_healthy = self.database.health_check()
        connection_info = self.database.get_connection_info()
        
        return {
            'healthy': is_healthy,
            'connection_info': connection_info,
            'statistics': self.get_statistics() if is_healthy else {}
        }

    def __del__(self):
        """Cleanup database connection on object destruction."""
        if hasattr(self, 'database') and self.database:
            try:
                self.database.disconnect()
            except:
                pass
