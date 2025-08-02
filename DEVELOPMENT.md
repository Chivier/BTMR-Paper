# BTMR Development Guide 💻

This document contains detailed information for developers working on the BTMR project.

## 🛠️ Technology Stack

### 🐍 Backend
- **Python 3.9+** with uv package manager
- **FastAPI** for high-performance API
- **OpenAI GPT** for AI-powered text processing
- **SQLite** for metadata storage with database abstraction layer
- **PyPDF2** for PDF processing
- **BeautifulSoup** for web scraping
- **Jinja2** for HTML template generation
- **WeasyPrint** for PDF generation
- **Pillow** for image processing and optimization
- **python-dotenv** for environment configuration

### ⚛️ Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **React Router** for navigation
- **TanStack Query** for data fetching
- **Zustand** for state management
- **Lucide React** for icons
- **React Hot Toast** for notifications


## Development

### Backend Development
```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run with auto-reload
uv run python -m src.api.main --reload

# Check code quality
uv run ruff check
uv run mypy src/
```

### Frontend Development
```bash
cd frontend

# Start development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

### Project Structure
```
BTMR-Paper/
├── src/                    # Backend source code
│   ├── api/               # FastAPI application
│   │   ├── main.py        # Main application entry
│   │   ├── routes.py      # API routes
│   │   ├── models.py      # Pydantic models
│   │   ├── services.py    # Business logic
│   │   └── config_service.py # Configuration service
│   ├── database/          # Database layer
│   │   ├── interface.py   # Database interface
│   │   ├── sqlite_impl.py # SQLite implementation
│   │   └── metadata_manager.py # Metadata management
│   ├── arxiv_fetcher.py   # ArXiv paper fetching
│   ├── paper_extractor.py # Content extraction
│   ├── html_generator.py  # HTML generation
│   ├── pdf_generator.py   # PDF generation
│   ├── image_processor.py # Image processing
│   ├── metadata_logger.py # Legacy CSV logging
│   ├── config.py          # Configuration management
│   └── utils.py           # Utility functions
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── types/         # TypeScript types
│   │   ├── context/       # React contexts
│   │   └── App.tsx        # Main app component
│   ├── public/            # Static assets
│   ├── uploads/           # Frontend file uploads
│   └── package.json       # Frontend dependencies
├── tests/                 # Test files
├── examples/              # Example files
├── scripts/               # Utility scripts
├── output/                # Generated outputs
├── uploads/               # Backend file uploads
├── logs/                  # Service logs
├── config.json            # Runtime configuration
├── startup.sh             # Service startup script
├── DATABASE_INTEGRATION.md # Database integration guide
├── pyproject.toml         # Python project config
└── README.md              # Project introduction and quickstart
```

## Database Management

### SQLite Database
BTMR uses SQLite for metadata storage with an abstraction layer that supports multiple database backends.

#### Features
- **Automatic Migration**: CSV data is automatically migrated to SQLite on first run
- **Paper Metadata**: Store processing history, statistics, and paper details
- **Health Monitoring**: Built-in database health checks
- **Backup Support**: Database backup and restore functionality
- **Query Interface**: Raw SQL query support for advanced operations

#### Database Operations
```bash
# Initialize database (done automatically)
uv run python -c "from src.database import DatabaseMetadataManager; DatabaseMetadataManager()"

# Migrate from CSV (if needed)
uv run python -c "
from src.database import DatabaseMetadataManager
manager = DatabaseMetadataManager()
manager.migrate_from_csv('output/paper_metadata.csv')
"

# Database health check
curl http://localhost:8000/api/v1/database/health
```

#### Database Schema
The database stores comprehensive paper metadata including:
- Paper ID, title, authors, and URLs
- Processing statistics (time, file sizes, figure/table counts)
- Status tracking and error handling
- Retry counts and timestamps
- Output formats and language settings

### Database Integration
For advanced database configuration and adding support for PostgreSQL, MySQL, or other databases, see [DATABASE_INTEGRATION.md](DATABASE_INTEGRATION.md).

## Service Management

The `startup.sh` script provides comprehensive service management:

### Service Commands
```bash
# Start all services
./startup.sh

# Check service status
./startup.sh status

# Stop all services
./startup.sh stop

# Restart services
./startup.sh restart

# Show help
./startup.sh help
```

### Service Features
- **Dependency Management**: Automatic installation of Python and Node.js dependencies
- **Health Monitoring**: Continuous monitoring of backend and frontend services
- **Database Initialization**: Automatic database setup and migration
- **Log Management**: Centralized logging to `logs/` directory
- **Port Management**: Automatic cleanup of occupied ports
- **Error Recovery**: Graceful error handling and cleanup

### Logs and Monitoring
```bash
# View backend logs
tail -f logs/backend.log

# View frontend logs
tail -f logs/frontend.log

# Check service status
./startup.sh status
```

## API Documentation

The API provides comprehensive OpenAPI documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example API Usage

#### Process a Paper
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/papers/process-sync",
    json={
        "input_source": "https://arxiv.org/abs/2301.12345",
        "input_type": "arxiv",
        "output_format": "html",
        "language": "en",
        "save_json": True
    }
)

paper_data = response.json()
print(f"Processed: {paper_data['metadata']['title']}")
```

#### Database Operations
```python
from src.database import DatabaseMetadataManager

# Initialize database manager
manager = DatabaseMetadataManager()

# Get recent papers
papers = manager.get_recent_papers(limit=10)

# Get processing statistics
stats = manager.get_statistics()
print(f"Total papers: {stats['total_papers']}")

# Search papers
search_results = manager.get_recent_papers(limit=20, search="machine learning")
```

#### Real-time Progress Tracking
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/progress/paper_id');

ws.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    console.log(`Progress: ${progress.progress}% - ${progress.message}`);
};
```

## Processing Papers via API

```bash
# Process an ArXiv paper
curl -X POST "http://localhost:8000/api/v1/papers/process-sync" \
     -H "Content-Type: application/json" \
     -d '{
       "input_source": "https://arxiv.org/abs/2301.12345",
       "input_type": "arxiv",
       "output_format": "html",
       "language": "en"
     }'

# Upload and process a PDF
curl -X POST "http://localhost:8000/api/v1/files/upload" \
     -F "file=@paper.pdf"

# List processed papers
curl "http://localhost:8000/api/v1/papers?page=1&per_page=10"
```

### API Endpoints

#### Core Endpoints
- `GET /api/v1/health` - Health check
- `POST /api/v1/papers/process` - Start async processing
- `POST /api/v1/papers/process-sync` - Synchronous processing
- `GET /api/v1/papers` - List papers with pagination
- `GET /api/v1/papers/{paper_id}` - Get paper details
- `GET /api/v1/papers/{paper_id}/download` - Download processed paper
- `DELETE /api/v1/papers/{paper_id}` - Delete paper
- `POST /api/v1/files/upload` - Upload files
- `GET /api/v1/stats` - Get processing statistics

#### WebSocket Endpoints
- `WS /api/v1/ws/progress/{paper_id}` - Real-time progress updates

### Configuration

#### Environment Variables
```env
# Required
OPENAI_API_KEY=your_api_key

# Optional
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4-turbo
TRANSLATE_MODEL=gpt-4-turbo
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=50MB

# Database Configuration
DATABASE_URL=sqlite:///output/paper_metadata.db
DB_POOL_SIZE=5
DB_POOL_TIMEOUT=30

# Processing Configuration
MAX_PAPER_LENGTH=50000
MAX_IMAGE_SIZE_MB=10.0
REQUEST_TIMEOUT=30
IMAGE_QUALITY=85
MAX_IMAGE_DIMENSION=2000
```

#### Supported Input Types
- **ArXiv**: URLs like `https://arxiv.org/abs/2301.12345`
- **PDF**: Direct PDF file uploads
- **URL**: Web pages with academic content
- **Markdown**: Markdown files

#### Output Formats
- **HTML**: Structured HTML with embedded images
- **PDF**: Generated PDF documents
- **JSON**: Raw extracted data

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   - Ensure your API key is set in the `.env` file
   - Check that the key has sufficient credits

2. **Port Already in Use**
   - Change the port: `python -m src.api.main --port 8001`
   - Kill existing processes: `lsof -ti:8000 | xargs kill`

3. **Frontend Build Issues**
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Check Node.js version: `node --version` (should be 18+)

4. **PDF Generation Issues**
   - Install system dependencies for WeasyPrint
   - On macOS: `brew install cairo pango gdk-pixbuf libffi`
   - On Ubuntu: `apt-get install libcairo2-dev libpango1.0-dev`

### Logs and Debugging
- Backend logs are printed to console
- Frontend development server shows build errors
- Check browser console for frontend issues
- API errors include detailed error messages

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `uv run pytest`
5. Submit a pull request

## Core Components

### Backend Components
- **Configuration System** (`src/config.py`): Centralized configuration with environment variable support
- **Database Layer** (`src/database/`): Abstracted database interface with SQLite implementation
- **Image Processor** (`src/image_processor.py`): Advanced image extraction and optimization
- **Paper Extractor** (`src/paper_extractor.py`): LLM-powered content extraction with OpenAI integration
- **HTML Generator** (`src/html_generator.py`): Beautiful HTML output with embedded images
- **PDF Generator** (`src/pdf_generator.py`): PDF generation using WeasyPrint
- **ArXiv Fetcher** (`src/arxiv_fetcher.py`): Specialized ArXiv paper downloading
- **Metadata Logger** (`src/metadata_logger.py`): Legacy CSV-based metadata logging
- **Utility Classes** (`src/utils.py`): Text, file, image, and validation utilities

### Frontend Components
- **React Pages**: Home, Papers, Process, Settings, and Paper Detail pages
- **Layout System**: Responsive layout with navigation and banner components
- **API Service**: Centralized API communication with TypeScript types
- **Notification System**: Toast notifications with context management
- **File Upload**: Drag-and-drop file upload interface

### Service Management
- **Startup Script** (`startup.sh`): Complete service management with health monitoring
- **Configuration Files**: Runtime configuration with `config.json`
- **Database Integration**: Comprehensive database abstraction layer
- **Log Management**: Centralized logging for all services
