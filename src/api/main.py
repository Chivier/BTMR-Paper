"""
FastAPI main application for BTMR.

Entry point for the web API server.
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from .routes import router
from .models import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 BTMR API Server starting up...")
    
    # Ensure required directories exist
    os.makedirs("output", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    yield
    
    # Shutdown
    print("🛑 BTMR API Server shutting down...")


# Create FastAPI app
app = FastAPI(
    title="BTMR API",
    description="Beautiful Text Mining Reader - API for processing academic papers with LLM",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Serve static files (for frontend)
if os.path.exists("frontend/dist"):
    app.mount("/static", StaticFiles(directory="frontend/dist"), name="static")

# Serve output files
if os.path.exists("output"):
    app.mount("/files", StaticFiles(directory="output"), name="files")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve frontend or API info."""
    # Check if frontend build exists
    frontend_index = Path("frontend/dist/index.html")
    
    if frontend_index.exists():
        # Serve the React frontend
        with open(frontend_index, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        # Serve API information page
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BTMR API</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 40px; }
                .api-info { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .endpoint { background: white; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #007bff; }
                .method { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
                .get { background: #28a745; color: white; }
                .post { background: #007bff; color: white; }
                .delete { background: #dc3545; color: white; }
                .websocket { background: #6f42c1; color: white; }
                a { color: #007bff; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 BTMR API Server</h1>
                    <p>Beautiful Text Mining Reader - API for processing academic papers with LLM</p>
                    <p>Version 0.2.0</p>
                </div>
                
                <div class="api-info">
                    <h2>📚 API Documentation</h2>
                    <p>Interactive API documentation is available at:</p>
                    <ul>
                        <li><a href="/docs">Swagger UI</a> - Interactive API explorer</li>
                        <li><a href="/redoc">ReDoc</a> - Alternative documentation</li>
                    </ul>
                </div>
                
                <div class="api-info">
                    <h2>🔗 Key Endpoints</h2>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <strong>/api/v1/health</strong>
                        <p>Health check endpoint</p>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <strong>/api/v1/papers/process</strong>
                        <p>Start processing a paper asynchronously</p>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <strong>/api/v1/papers/process-sync</strong>
                        <p>Process a paper synchronously (blocking)</p>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <strong>/api/v1/papers</strong>
                        <p>List processed papers with pagination</p>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <strong>/api/v1/papers/{paper_id}</strong>
                        <p>Get detailed paper data</p>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <strong>/api/v1/papers/{paper_id}/download</strong>
                        <p>Download processed paper (HTML/PDF/JSON)</p>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <strong>/api/v1/files/upload</strong>
                        <p>Upload files for processing</p>
                    </div>
                    
                    <div class="endpoint">
                        <span class="method websocket">WS</span>
                        <strong>/api/v1/ws/progress/{paper_id}</strong>
                        <p>Real-time progress updates via WebSocket</p>
                    </div>
                </div>
                
                <div class="api-info">
                    <h2>🛠️ Usage Examples</h2>
                    <h3>Process ArXiv Paper</h3>
                    <pre><code>curl -X POST "http://localhost:8000/api/v1/papers/process-sync" \\
     -H "Content-Type: application/json" \\
     -d '{
       "input_source": "https://arxiv.org/abs/2301.12345",
       "input_type": "arxiv",
       "output_format": "html",
       "language": "en"
     }'</code></pre>
                     
                    <h3>List Papers</h3>
                    <pre><code>curl "http://localhost:8000/api/v1/papers?page=1&per_page=10"</code></pre>
                </div>
                
                <div class="api-info">
                    <h2>🔧 Configuration</h2>
                    <p>Make sure to set up your environment variables:</p>
                    <ul>
                        <li><code>OPENAI_API_KEY</code> - Your OpenAI API key</li>
                        <li><code>OPENAI_API_BASE</code> - Custom API base URL (optional)</li>
                        <li><code>MODEL_NAME</code> - Default model name (optional)</li>
                    </ul>
                </div>
                
                <div class="api-info">
                    <h2>📁 File Access</h2>
                    <p>Processed files are available at:</p>
                    <ul>
                        <li><code>/files/{paper_id}/summary.html</code> - Generated HTML</li>
                        <li><code>/files/{paper_id}/summary.pdf</code> - Generated PDF</li>
                        <li><code>/files/{paper_id}/extracted_data.json</code> - Raw extracted data</li>
                        <li><code>/files/{paper_id}/images/</code> - Extracted images</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """)




def start_server():
    """Start the BTMR API server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start BTMR API server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting BTMR API server on {args.host}:{args.port}")
    print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🌐 Web Interface: http://{args.host}:{args.port}/")
    
    uvicorn.run(
        "src.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()
