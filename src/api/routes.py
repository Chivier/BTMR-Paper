"""
FastAPI routes for the BTMR API.

Defines REST endpoints for paper processing, file management, and WebSocket connections.
"""
import os
import json
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import (
    APIRouter, 
    HTTPException, 
    UploadFile, 
    File, 
    Query, 
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect
)
from fastapi.responses import FileResponse, JSONResponse

from .models import (
    PaperProcessRequest,
    PaperResponse,
    PaperListResponse,
    PaperMetadata,
    ProcessingProgress,
    ProcessingStatus,
    ErrorResponse,
    HealthResponse,
    FileUploadResponse,
    ConfigurationRequest,
    ConfigurationResponse,
)
from .services import PaperProcessingService, FileService
from .config_service import ConfigurationService
from playwright.async_api import async_playwright
from ..pdf_generator import PDFGenerator

# Initialize services
paper_service = PaperProcessingService()
file_service = FileService()
config_service = ConfigurationService()

# Create router
router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.paper_connections: dict = {}  # paper_id -> [websockets]

    async def connect(self, websocket: WebSocket, paper_id: Optional[str] = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if paper_id:
            if paper_id not in self.paper_connections:
                self.paper_connections[paper_id] = []
            self.paper_connections[paper_id].append(websocket)

    def disconnect(self, websocket: WebSocket, paper_id: Optional[str] = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if paper_id and paper_id in self.paper_connections:
            if websocket in self.paper_connections[paper_id]:
                self.paper_connections[paper_id].remove(websocket)
            if not self.paper_connections[paper_id]:
                del self.paper_connections[paper_id]

    async def send_progress_update(self, progress: ProcessingProgress):
        """Send progress update to relevant WebSocket connections."""
        paper_id = progress.paper_id
        if paper_id in self.paper_connections:
            disconnected = []
            for websocket in self.paper_connections[paper_id]:
                try:
                    await websocket.send_json(progress.model_dump())
                except:
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws, paper_id)

manager = ConnectionManager()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.2.0",
        dependencies={
            "fastapi": "0.104.0+",
            "python": "3.10+",
            "openai": "1.12.0+",
        }
    )


@router.post("/papers/process")
async def process_paper(
    request: PaperProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    Start processing a paper asynchronously.
    Returns immediately with paper metadata and starts background processing.
    """
    try:
        # Generate paper ID for tracking
        paper_id = f"paper_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(request.input_source) % 10000:04d}"
        
        # Get current configuration to pass to processing
        current_config = config_service.get_configuration()
        
        # Update request with configuration if not provided
        if not request.model:
            request.model = current_config.default_model
        if not request.openai_base_url:
            request.openai_base_url = current_config.openai_api_base
        
        # Create pending paper entry immediately
        paper_metadata = paper_service.create_pending_paper(request, paper_id)
        
        # Start processing in background with the generated paper_id
        async def process_with_progress(req: PaperProcessRequest, pid: str):
            try:
                await paper_service.process_paper(
                    req, 
                    progress_callback=manager.send_progress_update,
                    paper_id=pid
                )
                # Remove from active papers when completed
                if pid in paper_service.active_papers:
                    del paper_service.active_papers[pid]
            except Exception as e:
                print(f"Background processing failed for {pid}: {e}")
                # Update paper status to failed
                if pid in paper_service.active_papers:
                    paper_service.active_papers[pid].status = 'failed'
                # Send error via WebSocket
                error_progress = ProcessingProgress(
                    paper_id=pid,
                    status='failed',
                    progress=0.0,
                    message=f"Processing failed: {str(e)}",
                    error=str(e)
                )
                await manager.send_progress_update(error_progress)
        
        background_tasks.add_task(process_with_progress, request, paper_id)
        
        return {
            "paper_id": paper_id,
            "status": "processing_started",
            "message": "Paper processing started.",
            "paper_metadata": paper_metadata.model_dump()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Configuration endpoints
@router.get("/config", response_model=ConfigurationResponse)
async def get_configuration():
    """Get current application configuration."""
    try:
        return config_service.get_configuration()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config", response_model=ConfigurationResponse)
async def update_configuration(request: ConfigurationRequest):
    """Update application configuration."""
    try:
        return config_service.update_configuration(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/reset", response_model=ConfigurationResponse)
async def reset_configuration():
    """Reset configuration to defaults."""
    try:
        return config_service.reset_configuration()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/validate")
async def validate_configuration():
    """Validate current configuration."""
    try:
        return config_service.validate_configuration()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/models")
async def get_available_models(
    api_key: Optional[str] = Query(None, description="Temporary API key for testing"),
    api_base: Optional[str] = Query(None, description="Temporary API base URL for testing")
):
    """Get list of available AI models."""
    try:
        return config_service.get_available_models(api_key, api_base)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/papers/process-sync", response_model=PaperResponse)
async def process_paper_sync(request: PaperProcessRequest):
    """
    Process a paper synchronously (blocking).
    Use this for immediate results or testing.
    """
    try:
        # Get current configuration to pass to processing
        current_config = config_service.get_configuration()
        
        # Update request with configuration if not provided
        if not request.model:
            request.model = current_config.default_model
        if not request.openai_base_url:
            request.openai_base_url = current_config.openai_api_base
        
        paper_id, extracted_data, output_path = await paper_service.process_paper(request)
        
        # Get paper metadata
        papers, _ = paper_service.list_papers(page=1, per_page=1)
        metadata = papers[0] if papers else None
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Paper metadata not found")
        
        return PaperResponse(
            metadata=metadata,
            extracted_data=extracted_data,
            output_path=output_path,
            json_path=f"output/{paper_id}/extracted_data.json",
            images_path=f"output/{paper_id}/images"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title and authors")
):
    """List processed papers with pagination and search."""
    try:
        papers, total = paper_service.list_papers(page, per_page, search)
        total_pages = (total + per_page - 1) // per_page
        
        return PaperListResponse(
            papers=papers,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{paper_id}")
async def get_paper(paper_id: str):
    """Get detailed paper data by ID."""
    try:
        paper_data = paper_service.get_paper(paper_id)
        
        if not paper_data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        return paper_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{paper_id}/progress", response_model=ProcessingProgress)
async def get_paper_progress(paper_id: str):
    """Get current processing progress for a paper."""
    try:
        progress = paper_service.get_progress(paper_id)
        
        if not progress:
            raise HTTPException(status_code=404, detail="Paper progress not found")
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{paper_id}/download")
async def download_paper(paper_id: str, format: str = Query("html", regex="^(html|pdf|json)$")):
    """Download processed paper in specified format."""
    try:
        paper_data = paper_service.get_paper(paper_id)
        print(f"Paper data: {paper_data}")
        
        if not paper_data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        if format == "json":
            file_path = paper_data.get('json_path')
            media_type = "application/json"
            filename = f"{paper_id}_data.json"
        
        elif format == "html":
            file_path = paper_data.get('output_path')
            media_type = "text/html"
            filename = f"{paper_id}_summary.html"
        elif format == "pdf":
            file_path = paper_data.get('pdf_path')
            media_type = "application/pdf"
            filename = f"{paper_id}_summary.pdf"

        if not file_path or not file_path.endswith(f".{format}"):
            raise HTTPException(status_code=404, detail=f"{format.upper()} file not found")
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/papers/{paper_id}/retry")
async def retry_paper(paper_id: str, background_tasks: BackgroundTasks):
    """Retry processing a failed paper."""
    try:
        # Check if paper exists and is in failed state
        paper_data = paper_service.get_paper_metadata_by_id(paper_id)
        if not paper_data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        if paper_data.get('status') != 'failed':
            raise HTTPException(status_code=400, detail="Only failed papers can be retried")
        
        # Get current configuration
        current_config = config_service.get_configuration()
        
        # Recreate the original request from stored metadata
        request = PaperProcessRequest(
            input_source=paper_data.get('arxiv_url') or paper_data.get('input_source', ''),
            input_type=paper_data.get('format_used', 'arxiv'),
            output_format=paper_data.get('output_format', 'html'),
            language=paper_data.get('language', 'en'),
            model=current_config.default_model,
            openai_base_url=current_config.openai_api_base
        )
        
        # Update retry count in metadata
        paper_service.metadata_logger.update_retry_count(paper_id)
        
        # Reset paper status to pending
        paper_service.metadata_logger.update_paper_status(paper_id, 'pending')
        
        # Start processing in background with the same paper_id
        async def retry_process_with_progress(req: PaperProcessRequest, pid: str):
            try:
                await paper_service.process_paper(
                    req, 
                    progress_callback=manager.send_progress_update,
                    paper_id=pid
                )
                # Remove from active papers when completed
                if pid in paper_service.active_papers:
                    del paper_service.active_papers[pid]
            except Exception as e:
                print(f"Retry processing failed for {pid}: {e}")
                # Update paper status to failed
                paper_service.metadata_logger.update_paper_status(
                    pid, 'failed', str(e)
                )
                # Send error via WebSocket
                error_progress = ProcessingProgress(
                    paper_id=pid,
                    status='failed',
                    progress=0.0,
                    message=f"Retry failed: {str(e)}",
                    error=str(e)
                )
                await manager.send_progress_update(error_progress)
        
        background_tasks.add_task(retry_process_with_progress, request, paper_id)
        
        return {
            "paper_id": paper_id,
            "status": "retry_started",
            "message": "Paper retry processing started."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/papers/{paper_id}")
async def delete_paper(paper_id: str):
    """Delete a paper and its associated files."""
    try:
        success = paper_service.delete_paper(paper_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        return {"message": "Paper deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for processing."""
    try:
        # Validate file type
        allowed_types = {
            'application/pdf': '.pdf',
            'text/markdown': '.md',
            'text/plain': '.txt',
            'text/html': '.html'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Read file content
        content = await file.read()
        
        # Save file
        file_data = await file_service.save_uploaded_file(content, file.filename)
        
        return FileUploadResponse(
            filename=file_data['filename'],
            file_path=file_data['file_path'],
            file_size=file_data['file_size'],
            content_type=file.content_type,
            upload_id=file_data['upload_id']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{upload_id}")
async def delete_uploaded_file(upload_id: str):
    """Delete an uploaded file."""
    try:
        success = file_service.delete_file(upload_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/progress/{paper_id}")
async def websocket_progress(websocket: WebSocket, paper_id: str):
    """WebSocket endpoint for real-time progress updates."""
    await manager.connect(websocket, paper_id)
    
    try:
        # Send current progress if available
        current_progress = paper_service.get_progress(paper_id)
        if current_progress:
            await websocket.send_json(current_progress.model_dump())
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages (ping/pong, etc.)
                data = await websocket.receive_text()
                
                # Echo back for ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket, paper_id)


@router.websocket("/ws/general")
async def websocket_general(websocket: WebSocket):
    """General WebSocket endpoint for system-wide updates."""
    await manager.connect(websocket)
    
    try:
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


# Statistics endpoint
@router.get("/stats")
async def get_statistics():
    """Get processing statistics."""
    try:
        # Get recent papers for statistics
        papers, total = paper_service.list_papers(page=1, per_page=1000)
        
        # Calculate statistics
        total_papers = total
        total_processing_time = sum(p.processing_time for p in papers)
        avg_processing_time = total_processing_time / total_papers if total_papers > 0 else 0
        
        # Count by format
        format_counts = {}
        language_counts = {}
        
        for paper in papers:
            format_counts[paper.output_format.value] = format_counts.get(paper.output_format.value, 0) + 1
            language_counts[paper.language.value] = language_counts.get(paper.language.value, 0) + 1
        
        return {
            "total_papers": total_papers,
            "total_processing_time": total_processing_time,
            "average_processing_time": avg_processing_time,
            "format_distribution": format_counts,
            "language_distribution": language_counts,
            "active_processes": len(paper_service.active_processes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
