# BTMR - Beautiful Text Mining Reader

A modern web application for extracting and summarizing academic papers using AI. BTMR provides both a powerful Python backend API and a beautiful React frontend interface.

## Features

### Backend API
- **Paper Processing**: Extract content from ArXiv papers, PDFs, and URLs
- **AI-Powered Summarization**: Generate structured summaries using OpenAI GPT models
- **Multiple Output Formats**: HTML and PDF generation
- **Real-time Progress**: WebSocket support for live processing updates
- **File Management**: Upload and manage paper files
- **RESTful API**: Comprehensive API with OpenAPI documentation

### Frontend Interface
- **Modern React UI**: Built with React 18, TypeScript, and Tailwind CSS
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Updates**: Live progress tracking during paper processing
- **Paper Management**: Browse, search, and organize processed papers
- **Statistics Dashboard**: View processing insights and analytics
- **File Upload**: Drag-and-drop file upload interface

## Technology Stack

### Backend
- **Python 3.9+** with uv package manager
- **FastAPI** for high-performance API
- **OpenAI GPT** for AI-powered text processing
- **PyPDF2** for PDF processing
- **BeautifulSoup** for web scraping
- **Jinja2** for HTML template generation
- **WeasyPrint** for PDF generation

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **React Router** for navigation
- **TanStack Query** for data fetching
- **Zustand** for state management
- **Lucide React** for icons
- **React Hot Toast** for notifications

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher
- OpenAI API key

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd BTMR-Paper
   ```

2. **Install Python dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_API_BASE=https://api.openai.com/v1  # Optional
   MODEL_NAME=gpt-4  # Optional, defaults to gpt-3.5-turbo
   ```

4. **Start the backend server**
   ```bash
   # Using uv
   uv run python -m src.api.main
   
   # Or directly
   python -m src.api.main
   
   # With custom options
   python -m src.api.main --host 0.0.0.0 --port 8000 --reload
   ```

   The API will be available at:
   - **Main API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Alternative Docs**: http://localhost:8000/redoc

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

   The frontend will be available at: http://localhost:3000

### Production Build

1. **Build the frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Start the backend** (it will serve the frontend automatically)
   ```bash
   python -m src.api.main --host 0.0.0.0 --port 8000
   ```

   The complete application will be available at: http://localhost:8000

## Usage

### Processing Papers

#### Via Web Interface
1. Open the frontend at http://localhost:3000
2. Navigate to the home page
3. Click "Get Started" or use the paper processing form
4. Enter an ArXiv URL, upload a PDF, or provide a web URL
5. Select output format (HTML/PDF) and language
6. Click "Process" and monitor real-time progress

#### Via API
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
MODEL_NAME=gpt-4
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=50MB
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
│   │   └── services.py    # Business logic
│   ├── arxiv_fetcher.py   # ArXiv paper fetching
│   ├── paper_extractor.py # Content extraction
│   ├── html_generator.py  # HTML generation
│   ├── pdf_generator.py   # PDF generation
│   └── utils.py           # Utility functions
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── types/         # TypeScript types
│   │   └── App.tsx        # Main app component
│   ├── public/            # Static assets
│   └── package.json       # Frontend dependencies
├── tests/                 # Test files
├── examples/              # Example files
├── scripts/               # Utility scripts
├── pyproject.toml         # Python project config
└── README.md              # This file
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

#### Real-time Progress Tracking
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/progress/paper_id');

ws.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    console.log(`Progress: ${progress.progress}% - ${progress.message}`);
};
```

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for providing the GPT models
- ArXiv for the open access paper repository
- The open-source community for the excellent libraries used

---

For more information, visit the [project repository](https://github.com/Chivier/BTMR-Paper) or check the API documentation at http://localhost:8000/docs when running the server.
