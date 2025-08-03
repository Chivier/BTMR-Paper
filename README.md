# BTMR - Beautiful Text Mining Reader 📚🤖

A modern web application for extracting and summarizing academic papers using AI. BTMR provides both a powerful Python backend API and a beautiful React frontend interface.

## 🌟 Overview

BTMR (Beautiful Text Mining Reader) is an intelligent academic paper processing tool that leverages AI to automatically extract, analyze, and summarize research papers from various sources. Whether you're a researcher, student, or academic enthusiast, BTMR helps you quickly digest complex papers and focus on what matters most.

### 🎯 Key Benefits
- **Time Saving**: Automatically extract and summarize papers in minutes
- **Multi-format Support**: Process ArXiv URLs and PDFs
- **Beautiful Output**: Generate clean HTML or PDF documents with embedded figures

## 🚀 Features

### 🔧 Backend API
- **📄 Paper Processing**: Extract content from ArXiv URLs and PDFs
- **🤖 AI-Powered Summarization**: Generate structured summaries using LLMs
- **💾 Multiple Output Formats**: HTML and PDF generation
- **⚡ Real-time Progress**: WebSocket support for live processing updates
- **📁 File Management**: Upload and manage paper
- **🔗 RESTful API**: Comprehensive API with OpenAPI documentation
- **📊 Database Management**: SQLite-based paper metadata storage with migration support
- **⚙️ Service Management**: Built-in startup script with health monitoring
- **🖼️ Image Processing**: Advanced image extraction and optimization

### 🎨 Frontend Interface
- **⚛️ Modern React UI**: Built with React 18, TypeScript, and Tailwind CSS, with fully i18n support
- **📱 Responsive Design**: Works seamlessly on desktop and mobile devices
- **🔄 Real-time Updates**: Live progress tracking during paper processing
- **📚 Paper Management**: Browse, search, and organize processed papers
- **📤 File Upload**: Drag-and-drop file upload interface

## Quick Start

### 📋 Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher
- OpenAI API key (or OpenAI compatiable LLM provider's key)
- [uv](https://docs.astral.sh/uv/) for Python package management

### 🛠️ Option 1: One-Command Startup (Recommended)

The easiest way to start BTMR is using the included startup script:

```bash
# Clone the repository
git clone <repository-url>
cd BTMR-Paper

# Set up environment variables
cp .env.example .env
# Edit .env and add your LLM providers API key

# Start all services with one command
./startup.sh
```

The startup script will:
- Install all dependencies
- Initialize the SQLite database
- Migrate existing CSV data if present
- Start both backend and frontend servers
- Provide health monitoring and service management

Service management commands:
```bash
./startup.sh status    # Check service status
./startup.sh stop      # Stop all services
./startup.sh restart   # Restart all services
./startup.sh help      # Show help
```

### Option 2: Manual Setup

For development or custom configurations:

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

4. **Initialize the database** (optional - done automatically on first run)
   ```bash
   # Initialize SQLite database
   uv run python -c "from src.database import DatabaseMetadataManager; DatabaseMetadataManager()"
   ```

5. **Start the backend server**
   ```bash
   # Using uv
   uv run python -m src.api.main
   
   # With custom options
   uv run python -m src.api.main --host 0.0.0.0 --port 8000 --reload
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
   uv run python -m src.api.main --host 0.0.0.0 --port 8000
   ```

   The complete application will be available at: http://localhost:8000

## 🐳 Docker Deployment

BTMR can be easily deployed using Docker with separate containers for frontend and backend services.

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd BTMR-Paper
   ```

2. **Set up environment variables** (You can also set it on web page)
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

   The services will be available at:
   - Frontend: http://localhost:3000 (or the port specified as FRONTEND_PORT)
   - Backend API: http://localhost:8000 (or the port specified as BACKEND_PORT)

### Docker Architecture

The Docker setup uses two separate services:
- **Backend**: Python FastAPI server managed with uv, running on port 8000
- **Frontend**: React application served by Vite preview server, running on port 3000

Both services communicate through the Docker network, and the frontend connects to the backend API.

### Environment Variables for Docker

Key environment variables in `.env`:
```env
# API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4.1
TRANSLATE_MODEL=gpt-4.1

# Port Configuration
FRONTEND_PORT=3000
BACKEND_PORT=8000

# Log Level
LOG_LEVEL='DEBUG'
```

### Docker Commands

```bash
# Start services
docker-compose up

# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build
```

### Volumes

The Docker setup includes volumes for persistent data:
- `./output`: Stores generated paper summaries
- `./uploads`: Stores uploaded files
- `./logs`: Application logs
- `./config.json`: Additional configuration

## Usage

### Processing Papers

#### Via Web Interface
1. Open the frontend at http://localhost:3000
2. Navigate to the home page
3. Click "Get Started" or use the paper processing form
4. Enter an ArXiv URL, upload a PDF, or provide a web URL
5. Select output format (HTML/PDF) and language
6. Click "Process" and monitor real-time progress

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for providing the GPT models
- ArXiv for the open access paper repository
- The open-source community for the excellent libraries used
- SQLite for the embedded database solution
- FastAPI and React communities for the excellent frameworks

---

For more information, visit the [project repository](https://github.com/Chivier/BTMR-Paper) or check the API documentation at http://localhost:8000/docs when running the server.
