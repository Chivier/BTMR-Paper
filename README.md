

# BTMR - Beautiful Text Mining Reader 📚🤖

A modern, AI-powered web application for extracting, analyzing, and summarizing academic papers. BTMR transforms complex research papers into digestible, structured summaries with a beautiful interface.

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
  - [Option 1: One-Command Startup](#option-1-one-command-startup-recommended)
  - [Option 2: Manual Setup](#option-2-manual-setup)
- [Docker Deployment](#-docker-deployment)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 🌟 Overview

BTMR (Beautiful Text Mining Reader) is an intelligent academic paper processing tool that leverages AI to automatically extract, analyze, and summarize research papers from various sources. Perfect for researchers, students, and academic enthusiasts who want to quickly digest complex papers and focus on what matters most.

### 🎯 Key Benefits

- **⚡ Time Saving**: Process and summarize papers in minutes, not hours
- **🔗 Multi-format Support**: ArXiv URLs, PDFs, and web links
- **📊 Beautiful Output**: Clean HTML or PDF documents with embedded figures
- **🌐 Multilingual**: Support for English and Chinese with full i18n
- **📱 Responsive Design**: Works seamlessly across all devices

## 🚀 Features

### Backend Capabilities
- 📄 **Paper Processing**: Extract content from ArXiv URLs, PDFs, and web links
- 🤖 **AI-Powered Analysis**: Structured summaries using advanced LLMs
- 💾 **Multiple Formats**: Generate HTML and PDF outputs
- ⚡ **Real-time Progress**: WebSocket support for live updates
- 📊 **Database Management**: SQLite-based metadata storage with migrations
- 🔗 **RESTful API**: Comprehensive API with OpenAPI documentation
- 🖼️ **Image Processing**: Advanced extraction and optimization

### Frontend Features
- ⚛️ **Modern Tech Stack**: React 18, TypeScript, Tailwind CSS
- 🌐 **Internationalization**: Full i18n support (English/Chinese)
- 📱 **Responsive Design**: Mobile-first approach
- 🔄 **Real-time Updates**: Live progress tracking
- 📚 **Paper Management**: Browse, search, and organize papers
- 📤 **File Upload**: Intuitive drag-and-drop interface

## 🚀 Quick Start

### 📋 Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18 or higher  
- **LLM API Key**: OpenAI or compatible provider
- **Package Manager**: [uv](https://docs.astral.sh/uv/) (recommended)

### ⚡ Get Started in 3 Steps

1. **Clone and Setup**
   ```bash
   git clone https://github.com/Chivier/BTMR-Paper.git
   cd BTMR-Paper
   cp .env.example .env
   ```

2. **Configure Your API Key**
   Edit `.env` and add your LLM provider's API key:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Launch Application**
   ```bash
   ./startup.sh
   ```

🎉 **That's it!** The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 🛠️ Service Management

```bash
./startup.sh status    # Check service status
./startup.sh stop      # Stop all services  
./startup.sh restart   # Restart all services
./startup.sh help      # Show all commands
```

---

## 📦 Installation

### Option 1: One-Command Startup (Recommended)

The simplest way to get BTMR running:

```bash
git clone https://github.com/Chivier/BTMR-Paper.git
cd BTMR-Paper
cp .env.example .env
# Edit .env with your API key
./startup.sh
```

**What the startup script does:**
- ✅ Installs all dependencies automatically
- ✅ Initializes SQLite database
- ✅ Migrates existing data if present
- ✅ Starts both backend and frontend servers
- ✅ Provides health monitoring and service management

### Option 2: Manual Setup

For development or custom configurations:

#### 🔧 Backend Setup

```bash
# 1. Clone repository
git clone https://github.com/Chivier/BTMR-Paper.git
cd BTMR-Paper

# 2. Install dependencies
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Start backend server
uv run python -m src.api.main
```

**Backend will be available at:**
- 🌐 Main API: http://localhost:8000
- 📖 API Documentation: http://localhost:8000/docs
- 📚 Alternative Docs: http://localhost:8000/redoc

#### 🎨 Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

**Frontend will be available at:** http://localhost:3000

#### 🏗️ Production Build

```bash
# Build frontend
cd frontend && npm run build

# Start backend (serves frontend automatically)
uv run python -m src.api.main --host 0.0.0.0 --port 8000
```

**Complete application:** http://localhost:8000

---

## 🐳 Docker Deployment

Deploy BTMR using Docker for production environments or isolated development.

### 🚀 Quick Docker Start

```bash
# Clone and setup
git clone https://github.com/Chivier/BTMR-Paper.git
cd BTMR-Paper
cp .env.example .env
# Edit .env with your API key

# Launch with Docker Compose
docker-compose up --build
```

**Services will be available at:**
- 🎨 Frontend: http://localhost:3000
- ⚙️ Backend API: http://localhost:8000

### 🏗️ Docker Architecture

| Service | Technology | Port | Purpose |
|---------|------------|------|---------|
| **Backend** | FastAPI + uv | 8000 | API server and paper processing |
| **Frontend** | React + Vite | 3000 | Web interface |

### ⚙️ Docker Configuration

Key environment variables in `.env`:
```env
# API Configuration  
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4o
TRANSLATE_MODEL=gpt-4o

# Port Configuration
FRONTEND_PORT=3000
BACKEND_PORT=8000

# Logging
LOG_LEVEL=INFO
```

### 🛠️ Docker Commands

| Command | Purpose |
|---------|---------|
| `docker-compose up` | Start services |
| `docker-compose up -d` | Start in background |
| `docker-compose logs -f` | View live logs |
| `docker-compose down` | Stop services |
| `docker-compose up --build` | Rebuild and start |

### 💾 Persistent Data

Docker volumes ensure data persistence:
- `./output` → Generated summaries
- `./uploads` → Uploaded files  
- `./logs` → Application logs
- `./config.json` → Configuration

---

## 📖 Usage Guide

### 🌐 Web Interface

1. **Access the Application**
   - Open http://localhost:3000 in your browser
   - Choose your preferred language (English/Chinese)

2. **Process a Paper**
   - Navigate to the home page
   - Choose your input method:
     - 🔗 **ArXiv URL**: `https://arxiv.org/abs/2301.00000`
     - 📄 **PDF Upload**: Drag and drop or click to select
     - 🌐 **Web URL**: Any accessible research paper link
   
3. **Configure Output**
   - Select format: HTML or PDF
   - Choose language for summary
   - Set processing options

4. **Monitor Progress**
   - Real-time progress updates via WebSocket
   - View processing logs and status
   - Download results when complete

### 📚 Managing Papers

- **Browse Library**: View all processed papers
- **Search Papers**: Find papers by title, authors, or ArXiv ID
- **View Details**: Access full summaries and metadata
- **Re-download**: Get papers in different formats

### 🔧 API Usage

#### Process Paper via API

```bash
# Process ArXiv paper
curl -X POST "http://localhost:8000/api/papers/process" \
  -H "Content-Type: application/json" \
  -d '{
    "arxiv_url": "https://arxiv.org/abs/2301.00000",
    "output_format": "html",
    "language": "en"
  }'

# Upload and process PDF
curl -X POST "http://localhost:8000/api/papers/upload" \
  -F "file=@paper.pdf" \
  -F "output_format=pdf" \
  -F "language=zh"
```

#### Get Paper List

```bash
# Get all papers
curl "http://localhost:8000/api/papers"

# Search papers
curl "http://localhost:8000/api/papers?search=transformer"
```

### 🔧 Configuration

Edit `.env` or use the web interface settings:

```env
# LLM Configuration
OPENAI_API_KEY=your_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4o
TRANSLATE_MODEL=gpt-4o

# Processing Options
MAX_PAPER_SIZE_MB=50
OUTPUT_LANGUAGE=en
DEFAULT_OUTPUT_FORMAT=html

# Server Settings
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

---

## 🛠️ API Documentation

### Endpoints Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/papers` | GET | List all papers |
| `/api/papers/process` | POST | Process paper from URL |
| `/api/papers/upload` | POST | Upload and process PDF |
| `/api/papers/{id}` | GET | Get paper details |
| `/api/papers/{id}/download` | GET | Download paper output |
| `/api/config` | GET/PUT | Manage configuration |

### Interactive Documentation

When running the server, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🐛 Troubleshooting

### Common Issues

#### ❌ "API Key Not Found"
**Solution**: Ensure your `.env` file contains a valid API key:
```env
OPENAI_API_KEY=sk-your-actual-key-here
```

#### ❌ "Port Already in Use"
**Solution**: Stop existing services or change ports:
```bash
./startup.sh stop
# Or change ports in .env
FRONTEND_PORT=3001
BACKEND_PORT=8001
```

#### ❌ "PDF Processing Failed"
**Solution**: Check file size and format:
- Max file size: 50MB
- Supported formats: PDF
- Ensure PDF is not password-protected

#### ❌ "Frontend Not Loading"
**Solution**: Check if both services are running:
```bash
./startup.sh status
# If not running:
./startup.sh restart
```

### Getting Help

1. Check the logs: `./logs/backend.log`
2. Verify configuration: Visit http://localhost:8000/api/config
3. Test API directly: http://localhost:8000/docs
4. Open an issue: [GitHub Issues](https://github.com/Chivier/BTMR-Paper/issues)

---

## 🤝 Contributing

We welcome contributions! Please see our [DEVELOPMENT.md](DEVELOPMENT.md) for detailed guidelines.

### Quick Start for Contributors

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/BTMR-Paper.git
cd BTMR-Paper

# Create development environment
./startup.sh
# Make your changes
# Test thoroughly
# Submit a pull request
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for providing powerful GPT models
- **ArXiv** for the open access paper repository
- **FastAPI & React** communities for excellent frameworks
- **SQLite** for the embedded database solution
- **Open Source Community** for the incredible libraries and tools

---

## 🔗 Links

- 📝 **Repository**: [GitHub](https://github.com/Chivier/BTMR-Paper)
- 📖 **API Documentation**: http://localhost:8000/docs (when running)
- 🐛 **Issue Tracker**: [GitHub Issues](https://github.com/Chivier/BTMR-Paper/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Chivier/BTMR-Paper/discussions)

---

<div align="center">

**Made with ❤️ for the research community**

[⭐ Star us on GitHub](https://github.com/Chivier/BTMR-Paper) | [🐛 Report Issues](https://github.com/Chivier/BTMR-Paper/issues) | [💡 Request Features](https://github.com/Chivier/BTMR-Paper/discussions)

</div>
