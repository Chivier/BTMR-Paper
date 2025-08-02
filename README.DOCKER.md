# Docker Setup for BTMR

This document explains how to run BTMR using Docker and docker-compose.

## 📁 Docker Files

- `Dockerfile.backend` - Dockerfile for the Python backend service
- `frontend/Dockerfile` - Dockerfile for the React frontend service
- `docker-compose.yml` - Development setup with separate frontend and backend services
- `docker-compose.prod.yml` - Production setup with only the backend service serving the built frontend

## 🚀 Development Setup

For development, you can run both services separately with hot reloading:

```bash
# Build and start both services
docker-compose up --build

# Or start in detached mode
docker-compose up --build -d
```

This will:
- Start the backend API on http://localhost:8000
- Start the frontend development server on http://localhost:3000
- Enable hot reloading for both services

## 🏭 Production Setup

For production deployment, the backend serves the built frontend:

```bash
# Build and start the production service
docker-compose -f docker-compose.prod.yml up --build

# Or start in detached mode
docker-compose -f docker-compose.prod.yml up --build -d
```

This will:
- Build the frontend application
- Start only the backend service on http://localhost:8000
- Serve the built frontend through the backend

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory with your configuration:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4-turbo
TRANSLATE_MODEL=gpt-4-turbo
LOG_LEVEL=INFO
```

### Runtime Configuration

The `config.json` file contains runtime settings that can be modified:

```json
{
  "MAX_PAPER_LENGTH": 50000,
  "MAX_IMAGE_SIZE_MB": 10.0,
  "REQUEST_TIMEOUT": 30,
  "DEFAULT_OUTPUT_FORMAT": "html",
  "DEFAULT_LANGUAGE": "en",
  "IMAGE_QUALITY": 85,
  "MAX_IMAGE_DIMENSION": 2000
}
```

## 📂 Data Persistence

The following directories are mounted as volumes for data persistence:

- `./output` - Generated paper summaries and extracted data
- `./uploads` - Uploaded paper files
- `./logs` - Service logs

## 🛠️ Useful Commands

### Development

```bash
# Start services
docker-compose up

# Start services in background
docker-compose up -d

# View logs
docker-compose logs

# Stop services
docker-compose down

# Rebuild services
docker-compose build
```

### Production

```bash
# Start production service
docker-compose -f docker-compose.prod.yml up

# Start in background
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs

# Stop service
docker-compose -f docker-compose.prod.yml down

# Rebuild service
docker-compose -f docker-compose.prod.yml build
```

## 🔧 Troubleshooting

### Common Issues

1. **Port Conflicts**
   - Make sure ports 8000 and 3000 are not in use by other applications
   - Change port mappings in docker-compose.yml if needed

2. **Build Failures**
   - Ensure all required files are present
   - Check that Docker has sufficient resources allocated

3. **API Connection Issues**
   - Verify that the backend service is running
   - Check the logs for error messages

4. **Frontend Development Issues**
   - Ensure the frontend service is running
   - Check that the backend API URL is correctly configured

### Viewing Logs

```bash
# View all logs
docker-compose logs

# View backend logs
docker-compose logs backend

# View frontend logs
docker-compose logs frontend

# View logs in real-time
docker-compose logs -f
```

## 📦 Dependencies

### Backend Dependencies

The backend Dockerfile installs system dependencies required for:
- WeasyPrint PDF generation
- Image processing
- OCR functionality

### Frontend Dependencies

The frontend Dockerfile installs all Node.js dependencies from package.json.

## 🔄 Development Workflow

1. Start both services using `docker-compose up`
2. Develop frontend code with hot reloading at http://localhost:3000
3. Develop backend code with hot reloading at http://localhost:8000
4. Access API documentation at http://localhost:8000/docs
5. Processed files will be available in the `output` directory

## 🏗️ Building for Production

When using the production setup:
1. The frontend is built and served by the backend
2. All processing happens through the backend API
3. Processed files are stored in the `output` directory
4. Access the complete application at http://localhost:8000

## 📚 Additional Information

For more information about BTMR, see:
- [README.md](README.md) - Main project documentation
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development guide
