"""
Pydantic models for the BTMR API.

Defines request/response models for paper processing endpoints.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class InputType(str, Enum):
    """Types of input sources for paper processing."""
    ARXIV = "arxiv"
    URL = "url"
    MARKDOWN = "md"
    PDF = "pdf"


class OutputFormat(str, Enum):
    """Output format options."""
    HTML = "html"
    PDF = "pdf"


class Language(str, Enum):
    """Supported output languages."""
    ENGLISH = "en"
    CHINESE = "zh"


class ProcessingStatus(str, Enum):
    """Processing status states."""
    PENDING = "pending"
    FETCHING = "fetching"
    EXTRACTING = "extracting"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class PaperProcessRequest(BaseModel):
    """Request model for paper processing."""
    input_source: str = Field(..., description="URL, file path, or ArXiv ID")
    input_type: InputType = Field(default=InputType.ARXIV, description="Type of input source")
    output_format: OutputFormat = Field(default=OutputFormat.HTML, description="Output format")
    language: Language = Field(default=Language.ENGLISH, description="Output language")
    fetch_format: str = Field(default="auto", description="Format to fetch for ArXiv papers")
    save_json: bool = Field(default=True, description="Save extracted data as JSON")
    model: Optional[str] = Field(default=None, description="LLM model to use")
    openai_base_url: Optional[str] = Field(default=None, description="Custom OpenAI API base URL")


class Figure(BaseModel):
    """Figure or image in a paper."""
    url: str
    caption: str
    figure_type: Optional[str] = None


class Subsection(BaseModel):
    """Subsection within a paper section."""
    title: str
    content: str
    figures: List[Figure] = []


class Contribution(BaseModel):
    """Paper contribution."""
    title: str
    content: str


class Background(BaseModel):
    """Background section."""
    title: str
    content: str
    subsections: List[Subsection] = []


class Method(BaseModel):
    """Method section."""
    description: Optional[str] = None
    key_points: List[str] = []
    subsections: List[Subsection] = []
    figures: List[Figure] = []


class Results(BaseModel):
    """Results section."""
    evaluation: Optional[str] = None
    baseline: Optional[str] = None
    datasets: Optional[str] = None
    experimental_setup: Optional[str] = None
    subsections: List[Subsection] = []
    figures: List[Figure] = []
    tables: List[Figure] = []


class ExtractedData(BaseModel):
    """Complete extracted paper data."""
    title: str
    authors: Union[List[str], str]
    abstract: str
    background: List[Background] = []
    contributions: List[Contribution] = []
    method: Optional[Method] = None
    results: Optional[Results] = None
    processing_metadata: Optional[Dict[str, Any]] = None


class ProcessingProgress(BaseModel):
    """Processing progress update."""
    paper_id: str
    status: ProcessingStatus
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None


class PaperMetadata(BaseModel):
    """Paper metadata for listing."""
    paper_id: str
    title: str
    authors: Union[List[str], str]
    arxiv_url: Optional[str] = None
    format_used: str
    output_format: OutputFormat
    language: Language
    processing_time: float
    created_at: datetime
    file_size: Optional[int] = None
    status: ProcessingStatus
    error_message: Optional[str] = None
    retry_count: int = 0
    last_failed_at: Optional[datetime] = None


class PaperResponse(BaseModel):
    """Response model for paper data."""
    metadata: PaperMetadata
    extracted_data: ExtractedData
    output_path: str
    json_path: Optional[str] = None
    images_path: Optional[str] = None


class PaperListResponse(BaseModel):
    """Response model for paper listing."""
    papers: List[PaperMetadata]
    total: int
    page: int
    per_page: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    dependencies: Dict[str, str] = {}


class FileUploadResponse(BaseModel):
    """File upload response."""
    filename: str
    file_path: str
    file_size: int
    content_type: str
    upload_id: str


class ConfigurationRequest(BaseModel):
    """Request model for updating configuration."""
    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = None
    default_model: Optional[str] = None
    translate_model: Optional[str] = None
    max_paper_length: Optional[int] = Field(None, ge=1000, le=200000)
    max_image_size_mb: Optional[float] = Field(None, ge=0.1, le=100.0)
    request_timeout: Optional[int] = Field(None, ge=5, le=300)
    default_output_format: Optional[str] = None
    default_language: Optional[str] = None
    image_quality: Optional[int] = Field(None, ge=1, le=100)
    max_image_dimension: Optional[int] = Field(None, ge=100, le=5000)
    log_level: Optional[str] = None


class ConfigurationResponse(BaseModel):
    """Response model for configuration data."""
    openai_api_key: str = Field(..., description="Masked API key")
    openai_api_base: str
    default_model: str
    translate_model: str
    max_paper_length: int
    max_image_size_mb: float
    request_timeout: int
    default_output_format: str
    default_language: str
    image_quality: int
    max_image_dimension: int
    log_level: str
    colors: Dict[str, str]
    
    @classmethod
    def from_config(cls, config_dict: Dict[str, Any]) -> "ConfigurationResponse":
        """Create response from config dictionary."""
        # Mask the API key for security
        masked_key = ""
        if config_dict.get("OPENAI_API_KEY"):
            key = config_dict["OPENAI_API_KEY"]
            if len(key) > 8:
                masked_key = key[:4] + "*" * (len(key) - 8) + key[-4:]
            else:
                masked_key = "*" * len(key)
        
        return cls(
            openai_api_key=masked_key,
            openai_api_base=config_dict.get("OPENAI_API_BASE", ""),
            default_model=config_dict.get("DEFAULT_MODEL", ""),
            translate_model=config_dict.get("TRANSLATE_MODEL", ""),
            max_paper_length=config_dict.get("MAX_PAPER_LENGTH", 50000),
            max_image_size_mb=config_dict.get("MAX_IMAGE_SIZE_MB", 10.0),
            request_timeout=config_dict.get("REQUEST_TIMEOUT", 30),
            default_output_format=config_dict.get("DEFAULT_OUTPUT_FORMAT", "html"),
            default_language=config_dict.get("DEFAULT_LANGUAGE", "en"),
            image_quality=config_dict.get("IMAGE_QUALITY", 85),
            max_image_dimension=config_dict.get("MAX_IMAGE_DIMENSION", 2000),
            log_level=config_dict.get("LOG_LEVEL", "INFO"),
            colors=config_dict.get("COLORS", {})
        )
