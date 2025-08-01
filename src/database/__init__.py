"""
Database package for BTMR Paper project.

Provides database interfaces and implementations for storing paper metadata.
"""

from .interface import DatabaseInterface, DatabaseConfig, PaperRecord
from .sqlite_impl import SQLiteDatabase
from .metadata_manager import DatabaseMetadataManager

__all__ = [
    'DatabaseInterface',
    'DatabaseConfig', 
    'PaperRecord',
    'SQLiteDatabase',
    'DatabaseMetadataManager'
]
