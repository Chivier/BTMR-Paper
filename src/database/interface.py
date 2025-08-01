"""
Database interface for BTMR Paper project.

Defines the abstract base class for database operations that can be
implemented by different database backends (SQLite, PostgreSQL, MySQL, etc.).
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class PaperRecord:
    """Data class representing a paper record in the database."""
    paper_id: str
    title: str
    authors: str  # JSON string or semicolon-separated
    arxiv_url: Optional[str]
    format_used: str
    output_format: str
    output_path: str
    pdf_path: Optional[str]
    num_figures: int
    num_tables: int
    processing_time: float
    language: str
    file_size_kb: float
    status: str
    error_message: Optional[str]
    retry_count: int
    timestamp: datetime
    last_failed_at: Optional[datetime]


@dataclass
class DatabaseConfig:
    """Configuration for database connection."""
    connection_string: str
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    additional_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}


class DatabaseInterface(ABC):
    """
    Abstract base class defining the database interface for paper metadata storage.
    
    This interface provides a contract that can be implemented by different
    SQL database backends (SQLite, PostgreSQL, MySQL, etc.).
    """

    @abstractmethod
    def __init__(self, config: DatabaseConfig):
        """
        Initialize the database connection.
        
        Args:
            config: Database configuration object
        """
        pass

    @abstractmethod
    def connect(self):
        """Establish database connection."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close database connection."""
        pass

    @abstractmethod
    def create_tables(self):
        """Create necessary database tables if they don't exist."""
        pass

    @abstractmethod
    def insert_paper(self, paper: PaperRecord) -> bool:
        """
        Insert a new paper record.
        
        Args:
            paper: PaperRecord object containing paper metadata
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def update_paper_status(
        self, 
        paper_id: str, 
        status: str, 
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update paper status and optionally error message.
        
        Args:
            paper_id: Paper ID to update
            status: New status
            error_message: Optional error message
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def update_retry_count(self, paper_id: str) -> bool:
        """
        Increment retry count for a paper and update last_failed_at.
        
        Args:
            paper_id: Paper ID to update
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_paper_by_id(self, paper_id: str) -> Optional[PaperRecord]:
        """
        Get paper record by ID.
        
        Args:
            paper_id: Paper ID to search for
            
        Returns:
            PaperRecord object or None if not found
        """
        pass

    @abstractmethod
    def get_recent_papers(
        self, 
        limit: int = 10, 
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[PaperRecord]:
        """
        Get recent paper records with optional search.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            search: Optional search term to filter by title or authors
            
        Returns:
            List of PaperRecord objects
        """
        pass

    @abstractmethod
    def get_papers_count(self, search: Optional[str] = None) -> int:
        """
        Get total count of papers with optional search filter.
        
        Args:
            search: Optional search term to filter by title or authors
            
        Returns:
            Total number of papers matching the filter
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about processed papers.
        
        Returns:
            Dictionary containing statistics like total papers, figures,
            tables, processing times, etc.
        """
        pass

    @abstractmethod
    def delete_paper(self, paper_id: str) -> bool:
        """
        Delete a paper record.
        
        Args:
            paper_id: Paper ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def execute_raw_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of dictionaries representing query results
        """
        pass

    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current database connection.
        
        Returns:
            Dictionary containing connection information
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Perform a health check on the database connection.
        
        Returns:
            True if database is healthy, False otherwise
        """
        pass

    @abstractmethod
    def backup_data(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path where backup should be stored
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def restore_data(self, backup_path: str) -> bool:
        """
        Restore database from a backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if successful, False otherwise
        """
        pass
