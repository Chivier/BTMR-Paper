"""
SQLite implementation of the database interface.

Provides SQLite-specific implementation of the DatabaseInterface for
storing paper metadata in a local SQLite database file.
"""
import os
import sqlite3
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from loguru import logger

from .interface import DatabaseInterface, DatabaseConfig, PaperRecord


class SQLiteDatabase(DatabaseInterface):
    """
    SQLite implementation of the database interface.
    
    This implementation uses SQLite as the backend database for storing
    paper metadata. It's suitable for single-user applications or
    development environments.
    """

    def __init__(self, config: DatabaseConfig):
        """
        Initialize SQLite database connection.
        
        Args:
            config: Database configuration object
        """
        self.config = config
        self.db_path = config.connection_string
        self.connection = None
        
        # Ensure the directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.connect()
        self.create_tables()

    def connect(self):
        """Establish SQLite database connection."""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=self.config.pool_timeout
            )
            self.connection.row_factory = sqlite3.Row
            
            # Enable foreign keys and WAL mode for better performance
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA journal_mode = WAL")
            self.connection.execute("PRAGMA synchronous = NORMAL")
            self.connection.execute("PRAGMA cache_size = 10000")
            self.connection.execute("PRAGMA temp_store = MEMORY")
            
        except sqlite3.Error as e:
            raise Exception(f"Failed to connect to SQLite database: {e}")

    def disconnect(self):
        """Close SQLite database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor."""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    def create_tables(self):
        """Create necessary database tables if they don't exist."""
        create_papers_table = """
        CREATE TABLE IF NOT EXISTS papers (
            paper_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT,
            arxiv_url TEXT,
            format_used TEXT NOT NULL,
            output_format TEXT NOT NULL,
            output_path TEXT NOT NULL,
            pdf_path TEXT,
            num_figures INTEGER DEFAULT 0,
            num_tables INTEGER DEFAULT 0,
            processing_time REAL DEFAULT 0.0,
            language TEXT DEFAULT 'en',
            file_size_kb REAL DEFAULT 0.0,
            status TEXT DEFAULT 'completed',
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_failed_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        create_statistics_table = """
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_name TEXT UNIQUE NOT NULL,
            stat_value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # Index for better performance
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_papers_timestamp ON papers(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(status)",
            "CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title)",
            "CREATE INDEX IF NOT EXISTS idx_papers_authors ON papers(authors)",
            "CREATE INDEX IF NOT EXISTS idx_papers_created_at ON papers(created_at)"
        ]

        # Trigger to update updated_at column
        create_trigger = """
        CREATE TRIGGER IF NOT EXISTS update_papers_updated_at
        AFTER UPDATE ON papers
        FOR EACH ROW
        BEGIN
            UPDATE papers SET updated_at = CURRENT_TIMESTAMP WHERE paper_id = NEW.paper_id;
        END
        """

        try:
            with self.get_cursor() as cursor:
                cursor.execute(create_papers_table)
                cursor.execute(create_statistics_table)
                
                for index_sql in create_indexes:
                    cursor.execute(index_sql)
                
                cursor.execute(create_trigger)
                
        except sqlite3.Error as e:
            raise Exception(f"Failed to create database tables: {e}")

    def insert_paper(self, paper: PaperRecord) -> bool:
        """Insert a new paper record."""
        insert_sql = """
        INSERT OR REPLACE INTO papers (
            paper_id, title, authors, arxiv_url, format_used, output_format,
            output_path, pdf_path, num_figures, num_tables, processing_time,
            language, file_size_kb, status, error_message, retry_count,
            timestamp, last_failed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(insert_sql, (
                    paper.paper_id,
                    paper.title,
                    paper.authors,
                    paper.arxiv_url,
                    paper.format_used,
                    paper.output_format,
                    paper.output_path,
                    paper.pdf_path,
                    paper.num_figures,
                    paper.num_tables,
                    paper.processing_time,
                    paper.language,
                    paper.file_size_kb,
                    paper.status,
                    paper.error_message,
                    paper.retry_count,
                    paper.timestamp.isoformat() if paper.timestamp else datetime.now().isoformat(),
                    paper.last_failed_at.isoformat() if paper.last_failed_at else None
                ))
            return True
        except sqlite3.Error as e:
            print(f"Error inserting paper: {e}")
            return False

    def update_paper_status(
        self, 
        paper_id: str, 
        status: str, 
        error_message: Optional[str] = None
    ) -> bool:
        """Update paper status and optionally error message."""
        update_sql = """
        UPDATE papers 
        SET status = ?, error_message = ?, 
            last_failed_at = CASE WHEN ? = 'failed' THEN CURRENT_TIMESTAMP ELSE last_failed_at END
        WHERE paper_id = ?
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(update_sql, (status, error_message, status, paper_id))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating paper status: {e}")
            return False

    def update_retry_count(self, paper_id: str) -> bool:
        """Increment retry count for a paper and update last_failed_at."""
        update_sql = """
        UPDATE papers 
        SET retry_count = retry_count + 1, 
            last_failed_at = CURRENT_TIMESTAMP,
            status = 'failed'
        WHERE paper_id = ?
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(update_sql, (paper_id,))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating retry count: {e}")
            return False

    def get_paper_by_id(self, paper_id: str) -> Optional[PaperRecord]:
        """Get paper record by ID."""
        select_sql = "SELECT * FROM papers WHERE paper_id = ?"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(select_sql, (paper_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_paper_record(row)
                return None
        except sqlite3.Error as e:
            print(f"Error getting paper by ID: {e}")
            return None

    def get_recent_papers(
        self, 
        limit: int = 10, 
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[PaperRecord]:
        """Get recent paper records with optional search."""
        base_sql = "SELECT * FROM papers"
        params = []
        
        if search:
            base_sql += " WHERE (title LIKE ? OR authors LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        base_sql += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(base_sql, params)
                rows = cursor.fetchall()
                
                return [self._row_to_paper_record(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error getting recent papers: {e}")
            return []

    def get_papers_count(self, search: Optional[str] = None) -> int:
        """Get total count of papers with optional search filter."""
        base_sql = "SELECT COUNT(*) FROM papers"
        params = []
        
        if search:
            base_sql += " WHERE (title LIKE ? OR authors LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(base_sql, params)
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error getting papers count: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about processed papers."""
        stats_queries = {
            'total_papers': "SELECT COUNT(*) FROM papers",
            'total_figures': "SELECT SUM(num_figures) FROM papers",
            'total_tables': "SELECT SUM(num_tables) FROM papers",
            'avg_processing_time': "SELECT AVG(processing_time) FROM papers",
            'total_size_mb': "SELECT SUM(file_size_kb) / 1024.0 FROM papers",
            'completed_papers': "SELECT COUNT(*) FROM papers WHERE status = 'completed'",
            'failed_papers': "SELECT COUNT(*) FROM papers WHERE status = 'failed'",
        }
        
        format_stats_sql = """
        SELECT output_format, COUNT(*) as count 
        FROM papers 
        GROUP BY output_format
        """
        
        language_stats_sql = """
        SELECT language, COUNT(*) as count 
        FROM papers 
        GROUP BY language
        """
        
        try:
            stats = {}
            
            with self.get_cursor() as cursor:
                # Get basic statistics
                for stat_name, query in stats_queries.items():
                    cursor.execute(query)
                    result = cursor.fetchone()[0]
                    stats[stat_name] = result if result is not None else 0
                
                # Get format distribution
                cursor.execute(format_stats_sql)
                formats_used = {row[0]: row[1] for row in cursor.fetchall()}
                stats['formats_used'] = formats_used
                
                # Get language distribution
                cursor.execute(language_stats_sql)
                languages = {row[0]: row[1] for row in cursor.fetchall()}
                stats['languages'] = languages
            
            return stats
        except sqlite3.Error as e:
            print(f"Error getting statistics: {e}")
            return {
                'total_papers': 0,
                'total_figures': 0,
                'total_tables': 0,
                'avg_processing_time': 0,
                'total_size_mb': 0,
                'completed_papers': 0,
                'failed_papers': 0,
                'formats_used': {},
                'languages': {}
            }

    def delete_paper(self, paper_id: str) -> bool:
        """Delete a paper record."""
        delete_sql = "DELETE FROM papers WHERE paper_id = ?"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(delete_sql, (paper_id,))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error deleting paper: {e}")
            return False

    def find_duplicate_paper(self, title: str, arxiv_url: Optional[str], language: str) -> Optional[PaperRecord]:
        """
        Find duplicate paper based on title/arxiv_url and language.
        
        Args:
            title: Paper title to check
            arxiv_url: ArXiv URL to check (if any)
            language: Report language to check
            
        Returns:
            PaperRecord if duplicate found, None otherwise
        """
        # Check for exact title match and same language
        title_sql = """
        SELECT * FROM papers 
        WHERE LOWER(title) = LOWER(?) AND language = ?
        ORDER BY timestamp DESC 
        LIMIT 1
        """
        
        # Check for ArXiv URL match and same language (if arxiv_url provided)
        arxiv_sql = """
        SELECT * FROM papers 
        WHERE arxiv_url = ? AND language = ?
        ORDER BY timestamp DESC 
        LIMIT 1
        """
        
        try:
            with self.get_cursor() as cursor:
                # First check by ArXiv URL if provided
                if arxiv_url and arxiv_url.strip():
                    cursor.execute(arxiv_sql, (arxiv_url, language))
                    row = cursor.fetchone()
                    if row:
                        logger.info(f"Found duplicate paper by ArXiv URL: {arxiv_url}")
                        return self._row_to_paper_record(row)
                
                # Then check by title
                cursor.execute(title_sql, (title, language))
                row = cursor.fetchone()
                if row:
                    logger.info(f"Found duplicate paper by title: {title} (language: {language})")
                    return self._row_to_paper_record(row)
                
                return None
        except sqlite3.Error as e:
            print(f"Error finding duplicate paper: {e}")
            return None

    def execute_raw_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        try:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error executing raw query: {e}")
            return []

    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the current database connection."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT sqlite_version()")
                sqlite_version = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA database_list")
                db_info = cursor.fetchall()
                
                return {
                    'database_type': 'SQLite',
                    'sqlite_version': sqlite_version,
                    'database_path': self.db_path,
                    'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0,
                    'connected': self.connection is not None,
                    'databases': [dict(row) for row in db_info]
                }
        except sqlite3.Error as e:
            return {
                'database_type': 'SQLite',
                'error': str(e),
                'connected': False
            }

    def health_check(self) -> bool:
        """Perform a health check on the database connection."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except sqlite3.Error:
            return False

    def backup_data(self, backup_path: str) -> bool:
        """Create a backup of the SQLite database."""
        try:
            # Ensure backup directory exists
            backup_dir = os.path.dirname(backup_path)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            
            # Copy the database file
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def restore_data(self, backup_path: str) -> bool:
        """Restore database from a backup."""
        try:
            if not os.path.exists(backup_path):
                print(f"Backup file not found: {backup_path}")
                return False
            
            # Close current connection
            self.disconnect()
            
            # Replace current database with backup
            shutil.copy2(backup_path, self.db_path)
            
            # Reconnect
            self.connect()
            return True
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            # Try to reconnect even if restore failed
            try:
                self.connect()
            except:
                pass
            return False

    def _row_to_paper_record(self, row) -> PaperRecord:
        """Convert database row to PaperRecord object."""
        return PaperRecord(
            paper_id=row['paper_id'],
            title=row['title'],
            authors=row['authors'] or '',
            arxiv_url=row['arxiv_url'],
            format_used=row['format_used'],
            output_format=row['output_format'],
            output_path=row['output_path'],
            pdf_path=row['pdf_path'],
            num_figures=row['num_figures'] or 0,
            num_tables=row['num_tables'] or 0,
            processing_time=row['processing_time'] or 0.0,
            language=row['language'] or 'en',
            file_size_kb=row['file_size_kb'] or 0.0,
            status=row['status'] or 'completed',
            error_message=row['error_message'],
            retry_count=row['retry_count'] or 0,
            timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.now(),
            last_failed_at=datetime.fromisoformat(row['last_failed_at']) if row['last_failed_at'] else None
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
