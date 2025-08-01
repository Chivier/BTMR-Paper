# Database Integration Guide

This guide explains how to add support for new SQL databases to the BTMR Paper project.

## Overview

The BTMR Paper project uses a database abstraction layer that allows switching between different SQL database backends. The system is designed with:

1. **Database Interface** (`src/database/interface.py`) - Abstract base class defining the contract
2. **Database Implementations** - Concrete implementations for specific databases
3. **Metadata Manager** (`src/database/metadata_manager.py`) - High-level interface that uses the database implementations

## Current Implementation

### SQLite (Default)
- **File**: `src/database/sqlite_impl.py`
- **Class**: `SQLiteDatabase`
- **Use case**: Single-user applications, development, small-scale deployments
- **Configuration**: File path to SQLite database file

## Adding a New Database Backend

### Step 1: Create Database Implementation

Create a new file in `src/database/` for your database implementation (e.g., `postgresql_impl.py`):

```python
"""
PostgreSQL implementation of the database interface.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from .interface import DatabaseInterface, DatabaseConfig, PaperRecord

class PostgreSQLDatabase(DatabaseInterface):
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish PostgreSQL connection."""
        try:
            self.connection = psycopg2.connect(
                self.config.connection_string,
                cursor_factory=RealDictCursor
            )
        except psycopg2.Error as e:
            raise Exception(f"Failed to connect to PostgreSQL: {e}")
    
    # Implement all abstract methods from DatabaseInterface
    # ...
```

### Step 2: Implement Required Methods

Your implementation must provide all methods defined in `DatabaseInterface`:

#### Connection Management
- `connect()` - Establish database connection
- `disconnect()` - Close database connection  
- `health_check()` - Test if database is accessible

#### Table Management
- `create_tables()` - Create necessary tables with proper schema

#### CRUD Operations
- `insert_paper(paper: PaperRecord) -> bool`
- `update_paper_status(paper_id: str, status: str, error_message: Optional[str]) -> bool`
- `update_retry_count(paper_id: str) -> bool`
- `get_paper_by_id(paper_id: str) -> Optional[PaperRecord]`
- `delete_paper(paper_id: str) -> bool`

#### Query Operations
- `get_recent_papers(limit: int, offset: int, search: Optional[str]) -> List[PaperRecord]`
- `get_papers_count(search: Optional[str]) -> int`
- `get_statistics() -> Dict[str, Any]`

#### Utility Operations
- `execute_raw_query(query: str, params: Optional[Dict]) -> List[Dict[str, Any]]`
- `get_connection_info() -> Dict[str, Any]`
- `backup_data(backup_path: str) -> bool`
- `restore_data(backup_path: str) -> bool`

### Step 3: Database Schema

All implementations should create a table with the following schema:

```sql
CREATE TABLE papers (
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
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_failed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Add appropriate indexes for performance:

```sql
CREATE INDEX idx_papers_timestamp ON papers(timestamp);
CREATE INDEX idx_papers_status ON papers(status);
CREATE INDEX idx_papers_title ON papers(title);
CREATE INDEX idx_papers_authors ON papers(authors);
```

### Step 4: Configuration

Define database-specific configuration in `DatabaseConfig`:

```python
# PostgreSQL example
config = DatabaseConfig(
    connection_string="postgresql://user:password@localhost:5432/btmr_papers",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    additional_params={
        'sslmode': 'require',
        'application_name': 'btmr-paper'
    }
)
```

### Step 5: Update Package Exports

Add your implementation to `src/database/__init__.py`:

```python
from .postgresql_impl import PostgreSQLDatabase

__all__ = [
    'DatabaseInterface',
    'DatabaseConfig', 
    'PaperRecord',
    'SQLiteDatabase',
    'PostgreSQLDatabase',  # Add your implementation
    'DatabaseMetadataManager'
]
```

### Step 6: Usage

Use your new database implementation:

```python
from src.database import DatabaseConfig, PostgreSQLDatabase, DatabaseMetadataManager

# Create database configuration
config = DatabaseConfig(
    connection_string="postgresql://user:password@localhost:5432/btmr_papers"
)

# Create database instance
database = PostgreSQLDatabase(config)

# Use with metadata manager
metadata_manager = DatabaseMetadataManager(database=database)
```

## Database-Specific Examples

### PostgreSQL Implementation

```python
class PostgreSQLDatabase(DatabaseInterface):
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
            1, config.pool_size,
            config.connection_string,
            cursor_factory=RealDictCursor
        )
        self.create_tables()
    
    @contextmanager
    def get_connection(self):
        conn = self.connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.connection_pool.putconn(conn)
    
    def insert_paper(self, paper: PaperRecord) -> bool:
        insert_sql = """
        INSERT INTO papers (paper_id, title, authors, ...) 
        VALUES (%(paper_id)s, %(title)s, %(authors)s, ...)
        ON CONFLICT (paper_id) DO UPDATE SET
        title = EXCLUDED.title, authors = EXCLUDED.authors, ...
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(insert_sql, paper.__dict__)
            return True
        except psycopg2.Error as e:
            print(f"Error inserting paper: {e}")
            return False
```

### MySQL Implementation

```python
class MySQLDatabase(DatabaseInterface):
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="btmr_pool",
            pool_size=config.pool_size,
            **self._parse_connection_string(config.connection_string)
        )
        self.create_tables()
    
    def insert_paper(self, paper: PaperRecord) -> bool:
        insert_sql = """
        REPLACE INTO papers (paper_id, title, authors, ...)
        VALUES (%(paper_id)s, %(title)s, %(authors)s, ...)
        """
        
        try:
            conn = self.connection_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(insert_sql, paper.__dict__)
            conn.commit()
            return True
        except mysql.connector.Error as e:
            print(f"Error inserting paper: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
```

## Testing Your Implementation

Create tests to verify your implementation:

```python
import unittest
from src.database import DatabaseConfig, YourDatabase, PaperRecord
from datetime import datetime

class TestYourDatabase(unittest.TestCase):
    def setUp(self):
        config = DatabaseConfig(connection_string="your_test_connection_string")
        self.db = YourDatabase(config)
    
    def test_insert_and_retrieve_paper(self):
        paper = PaperRecord(
            paper_id="test_001",
            title="Test Paper",
            authors="Test Author",
            # ... other fields
        )
        
        # Test insert
        self.assertTrue(self.db.insert_paper(paper))
        
        # Test retrieve
        retrieved = self.db.get_paper_by_id("test_001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Test Paper")
    
    def tearDown(self):
        self.db.disconnect()
```

## Migration from CSV

The system includes a migration utility to transfer existing CSV data to the new database:

```python
from src.database import DatabaseMetadataManager

metadata_manager = DatabaseMetadataManager()
success = metadata_manager.migrate_from_csv("output/paper_metadata.csv")
if success:
    print("Migration completed successfully")
```

## Configuration Management

Add database configuration to your application's configuration system:

```python
# config.py
DATABASE_CONFIG = {
    'type': 'postgresql',  # or 'sqlite', 'mysql'
    'connection_string': os.getenv('DATABASE_URL', 'sqlite:///output/papers.db'),
    'pool_size': int(os.getenv('DB_POOL_SIZE', '5')),
    'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
}

def create_database():
    config = DatabaseConfig(**DATABASE_CONFIG)
    
    if DATABASE_CONFIG['type'] == 'postgresql':
        return PostgreSQLDatabase(config)
    elif DATABASE_CONFIG['type'] == 'mysql':
        return MySQLDatabase(config)
    else:
        return SQLiteDatabase(config)
```

## Best Practices

1. **Connection Pooling**: Use connection pools for production databases
2. **Error Handling**: Implement proper error handling and logging
3. **Transactions**: Use transactions for data consistency
4. **Security**: Sanitize inputs and use parameterized queries
5. **Performance**: Add appropriate indexes and optimize queries
6. **Testing**: Test with real database instances, not just mocks
7. **Migration**: Provide migration scripts for schema changes
8. **Backup**: Implement database-specific backup strategies

## Troubleshooting

### Common Issues

1. **Connection Problems**: Check connection strings and network connectivity
2. **Permission Issues**: Ensure database user has required permissions
3. **Schema Differences**: Verify table structures match expected schema
4. **Data Type Mismatches**: Handle database-specific data type conversions
5. **Transaction Timeouts**: Adjust timeout settings for long operations

### Debugging

Enable query logging and error reporting:

```python
config = DatabaseConfig(
    connection_string="your_connection_string",
    echo=True,  # Enable SQL logging
    additional_params={'debug': True}
)
```

## Performance Considerations

1. **Indexing**: Create indexes on frequently queried columns
2. **Connection Pooling**: Use appropriate pool sizes
3. **Query Optimization**: Optimize complex queries
4. **Batch Operations**: Use batch inserts for bulk data
5. **Caching**: Implement query result caching where appropriate

This guide should help you successfully integrate any SQL database with the BTMR Paper project. For specific database implementations, refer to the database vendor's documentation for best practices and optimization techniques.
