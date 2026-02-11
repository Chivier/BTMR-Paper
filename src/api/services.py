"""
Business logic services for the BTMR API.

Handles paper processing, file management, and data persistence.
"""
import os
import json
import uuid
import asyncio
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from loguru import logger

from ..arxiv_fetcher import ArxivFetcher
from ..paper_extractor import OpenAIExtractor
from ..html_generator import HTMLGenerator
from ..pdf_generator import PDFGenerator
from ..image_processor import ImageProcessor
from ..database import DatabaseMetadataManager
from .models import (
    PaperProcessRequest,
    ProcessingStatus,
    ProcessingProgress,
    PaperMetadata,
    ExtractedData,
    OutputFormat,
    InputType,
)


class PaperProcessingService:
    """Service for processing papers with progress tracking."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.metadata_logger = DatabaseMetadataManager()
        self.active_processes: Dict[str, ProcessingProgress] = {}
        self.active_papers: Dict[str, PaperMetadata] = {}
        
    def check_duplicate_paper(self, input_source: str, input_type: str, language: str) -> Optional[Any]:
        """
        Check if a paper with same title/arxiv_url and language already exists.
        
        Args:
            input_source: The input source (URL, ArXiv URL, etc.)
            input_type: Type of input ('arxiv', 'url', 'pdf', 'markdown')
            language: Language code ('en', 'zh')
            
        Returns:
            Existing paper metadata if duplicate found, None otherwise
        """
        # For ArXiv papers, check by ArXiv URL
        if input_type == 'arxiv':
            arxiv_url = input_source
            # Try to extract a basic title for checking
            title = f"ArXiv Paper: {input_source.split('/')[-1]}"
        elif input_type == 'url':
            # For URL papers, use the URL as identifier and basic title
            arxiv_url = input_source  # Use URL as identifier
            title = f"URL Paper: {input_source}"
        else:
            # For PDF/markdown, we can't easily check duplicates without processing first
            return None
            
        # Check for existing paper with same identifier and language using synchronous database call
        duplicate = self.metadata_logger.find_duplicate_paper(
            title=title,
            arxiv_url=arxiv_url,
            language=language
        )
        
        return duplicate

    def create_pending_paper(self, request: PaperProcessRequest, paper_id: str) -> PaperMetadata:
        """Create a pending paper entry immediately when processing starts."""
        # Determine initial title based on input
        if request.input_type == InputType.ARXIV:
            title = f"ArXiv Paper: {request.input_source.split('/')[-1]}"
        elif request.input_type == InputType.URL:
            title = f"URL Paper: {request.input_source}"
        elif request.input_type == InputType.PDF:
            title = "Uploaded PDF Paper"
        else:
            title = "Processing..."
        
        # Determine input URL for logging
        input_url = None
        if request.input_type == InputType.ARXIV:
            input_url = request.input_source
        elif request.input_type == InputType.URL:
            input_url = request.input_source
        
        # Calculate expected output paths
        paper_folder = self.output_dir / paper_id
        expected_output_path = str(paper_folder / "summary.html")
        expected_pdf_path = str(paper_folder / "summary.pdf")
        
        # Create paper metadata
        paper_metadata = PaperMetadata(
            paper_id=paper_id,
            title=title,
            authors=[],  # Will be filled when extraction completes
            arxiv_url=input_url,
            format_used=request.input_type.value,
            output_format=request.output_format,
            language=request.language,
            processing_time=0.0,
            created_at=datetime.now(),
            file_size=None,
            status=ProcessingStatus.PENDING
        )
        
        # LOG TO DATABASE IMMEDIATELY with basic metadata
        self.metadata_logger.log_paper(
            paper_id=paper_id,
            title=title,
            authors=[],
            arxiv_url=input_url,
            format_used=request.input_type.value,
            output_format=request.output_format.value,
            output_path=expected_output_path,
            pdf_path=expected_pdf_path,
            extracted_data={},  # Empty for now, will be updated on completion
            processing_time=0.0,
            language=request.language.value,
            status="pending"
        )
        
        # Store in active papers
        self.active_papers[paper_id] = paper_metadata
        return paper_metadata

    async def process_paper(
        self, 
        request: PaperProcessRequest,
        progress_callback: Optional[callable] = None,
        paper_id: Optional[str] = None
    ) -> Tuple[str, ExtractedData, str]:
        """
        Process a paper asynchronously with progress tracking.
        
        Args:
            request: Paper processing request
            progress_callback: Callback function for progress updates
            paper_id: Optional paper ID to use (generates one if not provided)
        
        Returns:
            Tuple of (paper_id, extracted_data, output_path)
        """
        # Use provided paper_id or generate unique one
        if not paper_id:
            paper_id = f"paper_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Immediately create pending paper entry
        paper_metadata = self.create_pending_paper(request, paper_id)
        
        paper_folder = self.output_dir / paper_id
        paper_folder.mkdir(exist_ok=True)
        
        # Initialize progress tracking
        progress = ProcessingProgress(
            paper_id=paper_id,
            status=ProcessingStatus.PENDING,
            progress=0.0,
            message="Initializing paper processing..."
        )
        self.active_processes[paper_id] = progress
        
        if progress_callback:
            await progress_callback(progress)
        
        try:
            start_time = datetime.now()
            
            # Step 1: Fetch paper content (with sub-steps)
            await self._update_progress(
                paper_id, ProcessingStatus.FETCHING, 5.0,
                "Starting paper content fetch...", progress_callback,
                current_step="Initializing", step_number=1, total_steps=4
            )
            
            if request.input_type == InputType.ARXIV:
                await self._update_progress(
                    paper_id, ProcessingStatus.FETCHING_ARXIV, 15.0,
                    f"Fetching ArXiv paper: {request.input_source}", progress_callback,
                    current_step="Fetching from ArXiv", step_number=1, total_steps=4
                )
            
            content, format_used, image_mapping = await self._fetch_content(
                request, paper_folder
            )
            
            if image_mapping:
                await self._update_progress(
                    paper_id, ProcessingStatus.PROCESSING_IMAGES, 25.0,
                    f"Processing {len(image_mapping)} images...", progress_callback,
                    current_step="Processing Images", step_number=1, total_steps=4,
                    additional_info={"image_count": len(image_mapping)}
                )
            
            await self._update_progress(
                paper_id, ProcessingStatus.FETCHING_CONTENT, 30.0,
                "Paper content fetched successfully", progress_callback,
                current_step="Content Fetched", step_number=1, total_steps=4
            )
            
            # Step 2: Extract information using LLM (with sub-steps)
            await self._update_progress(
                paper_id, ProcessingStatus.EXTRACTING, 35.0,
                "Starting information extraction...", progress_callback,
                current_step="Preparing Extraction", step_number=2, total_steps=4
            )
            
            await self._update_progress(
                paper_id, ProcessingStatus.EXTRACTING_STRUCTURE, 45.0,
                "Analyzing paper structure...", progress_callback,
                current_step="Analyzing Structure", step_number=2, total_steps=4
            )
            
            await self._update_progress(
                paper_id, ProcessingStatus.EXTRACTING_CONTENT, 55.0,
                "Extracting content with AI...", progress_callback,
                current_step="AI Content Extraction", step_number=2, total_steps=4
            )
            
            extracted_data = await self._extract_information(
                content, request, format_used, image_mapping
            )
            
            await self._update_progress(
                paper_id, ProcessingStatus.EXTRACTING, 70.0,
                "Information extraction completed", progress_callback,
                current_step="Extraction Complete", step_number=2, total_steps=4
            )
            
            # Step 3: Generate output (with sub-steps)
            await self._update_progress(
                paper_id, ProcessingStatus.GENERATING, 75.0,
                "Starting output generation...", progress_callback,
                current_step="Preparing Generation", step_number=3, total_steps=4
            )
            
            await self._update_progress(
                paper_id, ProcessingStatus.GENERATING_HTML, 80.0,
                "Generating HTML summary...", progress_callback,
                current_step="Creating HTML", step_number=3, total_steps=4
            )

            output_path, pdf_path = await self._generate_output(
                extracted_data, request, paper_folder, image_mapping
            )
            
            await self._update_progress(
                paper_id, ProcessingStatus.GENERATING_PDF, 90.0,
                "Generating PDF version...", progress_callback,
                current_step="Creating PDF", step_number=3, total_steps=4
            )
            
            # Step 4: Save metadata and complete
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Save JSON data if requested
            json_path = None
            if request.save_json:
                json_path = paper_folder / "extracted_data.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    # Convert ExtractedData to dict for JSON serialization
                    json.dump(extracted_data.model_dump(), f, ensure_ascii=False, indent=2)
            
            # Update the existing database record with completion data
            # First update status to completed
            self.metadata_logger.update_paper_status(paper_id, "completed")
            
            # Then update with extracted data and final paths (we'll need a new method for this)
            # For now, we'll delete the old record and insert the complete one
            self.metadata_logger.delete_paper(paper_id)
            self.metadata_logger.log_paper(
                paper_id=paper_id,
                title=extracted_data.title,
                authors=extracted_data.authors,
                arxiv_url=request.input_source if request.input_type == InputType.ARXIV else None,
                format_used=format_used,
                output_format=request.output_format.value,
                output_path=str(output_path),
                pdf_path=str(pdf_path) if pdf_path else None,
                extracted_data=extracted_data.model_dump(),
                processing_time=processing_time,
                language=request.language.value,
                status="completed"
            )
            
            await self._update_progress(
                paper_id, ProcessingStatus.COMPLETED, 100.0,
                "Paper processing completed successfully!", progress_callback
            )
            
            return paper_id, extracted_data, str(output_path)
            
        except Exception as e:
            # Log the full exception with backtrace
            logger.exception(f"Paper processing failed for {paper_id}: {str(e)}")
            
            # Update progress with error
            await self._update_progress(
                paper_id, ProcessingStatus.FAILED, 0.0,
                f"Processing failed: {str(e)}", progress_callback, error=str(e)
            )
            
            # Calculate processing time up to failure
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate expected output paths even for failed papers
            expected_output_path = str(paper_folder / "summary.html")
            expected_pdf_path = str(paper_folder / "summary.pdf")
            
            # Get the paper metadata for logging the failure
            paper_metadata = self.active_papers.get(paper_id)
            if paper_metadata:
                # Log the failed paper to metadata logger with detailed error information and expected paths
                self.metadata_logger.log_failed_paper(
                    paper_id=paper_id,
                    title=paper_metadata.title,
                    authors=paper_metadata.authors,
                    arxiv_url=paper_metadata.arxiv_url,
                    format_used=paper_metadata.format_used,
                    output_format=request.output_format.value,
                    expected_output_path=expected_output_path,
                    expected_pdf_path=expected_pdf_path,
                    error_message=str(e),
                    processing_time=processing_time,
                    language=request.language.value
                )
            else:
                # Fallback if no paper metadata available - still capture essential info
                input_url = request.input_source if request.input_type == InputType.ARXIV else None
                # For non-arxiv sources, try to capture the input source as well
                if request.input_type == InputType.URL:
                    input_url = request.input_source
                
                # Try to extract a meaningful title from the input source
                title = "Unknown Paper"
                if request.input_type == InputType.ARXIV:
                    title = f"ArXiv Paper: {request.input_source.split('/')[-1]}"
                elif request.input_type == InputType.URL:
                    title = f"URL Paper: {request.input_source}"
                elif request.input_type == InputType.PDF:
                    title = "Uploaded PDF Paper"
                
                self.metadata_logger.log_failed_paper(
                    paper_id=paper_id,
                    title=title,
                    authors=[],
                    arxiv_url=input_url,
                    format_used=request.input_type.value,
                    output_format=request.output_format.value,
                    expected_output_path=expected_output_path,
                    expected_pdf_path=expected_pdf_path,
                    error_message=str(e),
                    processing_time=processing_time,
                    language=request.language.value
                )
            
            # Update active paper status
            if paper_id in self.active_papers:
                self.active_papers[paper_id].status = ProcessingStatus.FAILED
                self.active_papers[paper_id].error_message = str(e)
            
            raise
    
    async def _fetch_content(
        self, 
        request: PaperProcessRequest, 
        paper_folder: Path
    ) -> Tuple[str, str, Dict]:
        """Fetch paper content based on input type."""
        try:
            image_processor = ImageProcessor(output_dir=str(paper_folder / 'images'))
            
            if request.input_type == InputType.ARXIV:
                # Run ArXiv fetching in thread pool with timeout to avoid blocking
                loop = asyncio.get_event_loop()
                
                def fetch_arxiv():
                    fetcher = ArxivFetcher(output_dir=str(paper_folder))
                    return fetcher.fetch(request.input_source, request.fetch_format)
                
                # Use asyncio.wait_for instead of signal for timeout
                content, format_used, image_mapping = await asyncio.wait_for(
                    loop.run_in_executor(None, fetch_arxiv),
                    timeout=180.0  # 3 minutes timeout
                )
                return content, format_used, image_mapping
                
            elif request.input_type == InputType.URL:
                _, content, image_mapping = image_processor.process_html(request.input_source)
                return content, "url", image_mapping
                
            elif request.input_type == InputType.MARKDOWN:
                content, image_mapping = image_processor.process_markdown(request.input_source)
                return content, "markdown", image_mapping
                
            elif request.input_type == InputType.PDF:
                # For PDF input, input_source should be the file path from uploaded file
                content, format_used, image_mapping = image_processor.process_pdf(request.input_source)
                return content, format_used, image_mapping
                
            else:
                raise ValueError(f"Unsupported input type: {request.input_type}")
        except Exception as e:
            if request.input_type == InputType.ARXIV:
                raise Exception(f"Failed to download ArXiv paper '{request.input_source}': {str(e)}")
            elif request.input_type == InputType.URL:
                raise Exception(f"Failed to fetch content from URL '{request.input_source}': {str(e)}")
            elif request.input_type == InputType.MARKDOWN:
                raise Exception(f"Failed to process markdown content: {str(e)}")
            elif request.input_type == InputType.PDF:
                raise Exception(f"Failed to process PDF file '{request.input_source}': {str(e)}")
            else:
                raise Exception(f"Failed to fetch content for input type '{request.input_type}': {str(e)}")
    
    async def _extract_information(
        self,
        content: str,
        request: PaperProcessRequest,
        format_used: str,
        image_mapping: Dict
    ) -> ExtractedData:
        """Extract structured information using LLM."""
        try:
            extractor = OpenAIExtractor(
                model=request.model,
                base_url=request.openai_base_url
            )
            
            # Run extraction in thread pool to avoid blocking with timeout
            loop = asyncio.get_event_loop()
            
            def extract_data():
                return extractor.extract(
                    content,
                    language=request.language.value,
                    format_type=format_used,
                    image_mapping=image_mapping
                )
            
            # Use asyncio.wait_for instead of signal for timeout
            extracted_data = await asyncio.wait_for(
                loop.run_in_executor(None, extract_data),
                timeout=300.0  # 5 minutes timeout
            )
            
            if "error" in extracted_data:
                raise Exception(f"AI extraction failed: {extracted_data['error']}")
            
            return ExtractedData(**extracted_data)
        except Exception as e:
            if "API" in str(e) or "OpenAI" in str(e):
                raise Exception(f"AI service error during content extraction: {str(e)}")
            elif "timeout" in str(e).lower():
                raise Exception(f"AI extraction timed out. The paper may be too long or complex: {str(e)}")
            else:
                raise Exception(f"Failed to extract information from paper content: {str(e)}")
    
    async def _generate_output(
        self,
        extracted_data: ExtractedData,
        request: PaperProcessRequest,
        paper_folder: Path,
        image_mapping: Dict
    ) -> str:
        """Generate output file (HTML or PDF)."""
        try:
            output_path = paper_folder / f"summary.html"
            pdf_path = paper_folder / "summary.pdf"
            
            # Run generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Generate HTML
            try:
                html_generator = HTMLGenerator(
                    output_dir=str(paper_folder),
                    image_mapping=image_mapping
                )
                await loop.run_in_executor(
                    None,
                    lambda: html_generator.generate(extracted_data.model_dump(), str(output_path))
                )
            except Exception as e:
                raise Exception(f"Failed to generate HTML summary: {str(e)}")
            
            # Generate PDF
            try:
                pdf_generator = PDFGenerator()
                await loop.run_in_executor(
                    None,
                    lambda: pdf_generator.generate(extracted_data.model_dump(), str(pdf_path))
                )
            except Exception as e:
                raise Exception(f"Failed to generate PDF summary: {str(e)}")
            
            return str(output_path), str(pdf_path)
        except Exception as e:
            if "HTML" in str(e) or "PDF" in str(e):
                raise  # Re-raise specific HTML/PDF errors
            else:
                raise Exception(f"Failed to generate output files: {str(e)}")
    
    async def _update_progress(
        self,
        paper_id: str,
        status: ProcessingStatus,
        progress: float,
        message: str,
        callback: Optional[callable] = None,
        error: Optional[str] = None,
        current_step: Optional[str] = None,
        step_number: Optional[int] = None,
        total_steps: Optional[int] = None,
        eta_seconds: Optional[float] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ):
        """Update processing progress with detailed information."""
        progress_update = ProcessingProgress(
            paper_id=paper_id,
            status=status,
            progress=progress,
            message=message,
            error=error,
            current_step=current_step,
            step_number=step_number,
            total_steps=total_steps,
            eta_seconds=eta_seconds,
            additional_info=additional_info
        )
        self.active_processes[paper_id] = progress_update
        
        # Update active paper status
        if paper_id in self.active_papers:
            self.active_papers[paper_id].status = status
            if error:
                self.active_papers[paper_id].error_message = error
        
        if callback:
            await callback(progress_update)
    
    def get_progress(self, paper_id: str) -> Optional[ProcessingProgress]:
        """Get current processing progress for a paper."""
        return self.active_processes.get(paper_id)
    
    def list_papers(
        self, 
        page: int = 1, 
        per_page: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[PaperMetadata], int]:
        """List processed papers with pagination, including active papers."""
        all_papers = []
        
        # First, add active papers (currently being processed)
        for paper_id, paper_metadata in self.active_papers.items():
            # Update status from active processes if available
            if paper_id in self.active_processes:
                progress = self.active_processes[paper_id]
                paper_metadata.status = progress.status
            
            all_papers.append(paper_metadata)
        
        # Then, get completed papers from metadata logger
        papers_data = self.metadata_logger.get_recent_papers(limit=1000)
        
        # Convert to PaperMetadata objects (skip if already in active papers)
        for paper_data in papers_data:
            if paper_data['paper_id'] not in self.active_papers:
                try:
                    # Parse authors if it's a string
                    authors = paper_data.get('authors', [])
                    if isinstance(authors, str):
                        authors = [a.strip() for a in authors.split(',') if a.strip()]
                    
                    # Parse status, error info, and retry count
                    status = paper_data.get('status', 'completed')
                    error_message = paper_data.get('error_message', '')
                    retry_count = int(paper_data.get('retry_count', '0'))
                    last_failed_at = None
                    if paper_data.get('last_failed_at'):
                        try:
                            last_failed_at = datetime.fromisoformat(paper_data['last_failed_at'])
                        except:
                            pass

                    # Parse status properly - handle both enum values and string values
                    try:
                        parsed_status = ProcessingStatus(status)
                    except ValueError:
                        # If status is not a valid enum value, check if it should be failed
                        if status == 'failed' or error_message:
                            parsed_status = ProcessingStatus.FAILED
                        else:
                            parsed_status = ProcessingStatus.COMPLETED
                        print(f"Warning: Unknown status '{status}' for paper {paper_data['paper_id']}, using {parsed_status.value}")

                    metadata = PaperMetadata(
                        paper_id=paper_data['paper_id'],
                        title=paper_data['title'],
                        authors=authors,
                        arxiv_url=paper_data.get('arxiv_url'),
                        format_used=paper_data['format_used'],
                        output_format=OutputFormat(paper_data['output_format']),
                        language=paper_data.get('language', 'en'),
                        processing_time=float(paper_data['processing_time']),
                        created_at=datetime.fromisoformat(paper_data['timestamp']),
                        status=parsed_status,
                        error_message=error_message if error_message else None,
                        retry_count=retry_count,
                        last_failed_at=last_failed_at
                    )
                    
                    all_papers.append(metadata)
                        
                except Exception as e:
                    print(f"Error parsing paper metadata: {e}")
                    print(f"Got metadata: {paper_data}")
                    continue
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            filtered_papers = []
            for paper in all_papers:
                if (search_lower in paper.title.lower() or
                    any(search_lower in author.lower() for author in 
                        (paper.authors if isinstance(paper.authors, list) else [paper.authors]))):
                    filtered_papers.append(paper)
            all_papers = filtered_papers
        
        # Sort by creation date (newest first)
        all_papers.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        total = len(all_papers)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_papers = all_papers[start_idx:end_idx]
        
        return paginated_papers, total
    
    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed paper data by ID."""
        paper_folder = self.output_dir / paper_id
        
        if not paper_folder.exists():
            return None
        
        # Load extracted data
        json_path = paper_folder / "extracted_data.json"
        if not json_path.exists():
            return None
        
        with open(json_path, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)
        
        # Find output file
        output_path = paper_folder / "summary.html"
        pdf_path = paper_folder / "summary.pdf"
        
        if output_path.exists():
            output_path = str(output_path)
        else:
            output_path = None
            
        if pdf_path.exists():
            pdf_path = str(pdf_path)
        else:
            pdf_path = None

        return {
            'paper_id': paper_id,
            'extracted_data': extracted_data,
            'output_path': output_path,
            'pdf_path': pdf_path,
            'json_path': str(json_path),
            'images_path': str(paper_folder / 'images') if (paper_folder / 'images').exists() else None
        }
    
    def get_paper_metadata_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get paper metadata by ID from metadata logger."""
        return self.metadata_logger.get_paper_by_id(paper_id)

    def delete_paper(self, paper_id: str) -> bool:
        """Delete a paper and its associated files and database record."""
        paper_folder = self.output_dir / paper_id
        success = False
        
        # Delete from database first
        if self.metadata_logger.delete_paper(paper_id):
            success = True
        
        # Delete files if folder exists
        if paper_folder.exists():
            shutil.rmtree(paper_folder)
            success = True
        
        # Remove from active processes if present
        if paper_id in self.active_processes:
            del self.active_processes[paper_id]
        
        # Remove from active papers if present
        if paper_id in self.active_papers:
            del self.active_papers[paper_id]
        
        return success


class FileService:
    """Service for handling file uploads and downloads."""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def save_uploaded_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Save uploaded file and return metadata."""
        # Generate unique filename
        upload_id = uuid.uuid4().hex
        file_extension = Path(filename).suffix
        unique_filename = f"{upload_id}_{filename}"
        file_path = self.upload_dir / unique_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return {
            'filename': filename,
            'file_path': str(file_path),
            'file_size': len(file_content),
            'upload_id': upload_id,
            'unique_filename': unique_filename
        }
    
    def get_file_path(self, upload_id: str) -> Optional[str]:
        """Get file path by upload ID."""
        for file_path in self.upload_dir.glob(f"{upload_id}_*"):
            return str(file_path)
        return None
    
    def delete_file(self, upload_id: str) -> bool:
        """Delete uploaded file by upload ID."""
        file_path = self.get_file_path(upload_id)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
