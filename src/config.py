"""
Configuration Module

Centralized configuration management for BTMR.
This module handles all configuration settings including:
- API endpoints and keys
- Model configurations
- Output settings
- Processing limits
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """
    Central configuration class for BTMR.
    
    All configuration values can be overridden via environment variables.
    """
    
    # API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    DEFAULT_MODEL: str = os.getenv("MODEL_NAME", "gpt-4-turbo")
    TRANSLATE_MODEL: str = os.getenv("TRANSLATE_MODEL", "gpt-4-turbo")
    
    # Processing Limits
    MAX_PAPER_LENGTH: int = 50000  # Maximum characters to send to LLM
    MAX_IMAGE_SIZE_MB: float = 10.0  # Maximum image file size
    REQUEST_TIMEOUT: int = 30  # HTTP request timeout in seconds
    
    # Output Configuration
    DEFAULT_OUTPUT_DIR: str = "output"
    DEFAULT_OUTPUT_FORMAT: str = "html"
    DEFAULT_LANGUAGE: str = "en"
    
    # Image Processing
    IMAGE_QUALITY: int = 85  # JPEG compression quality (0-100)
    MAX_IMAGE_DIMENSION: int = 2000  # Maximum width/height for images
    
    # Fetcher Configuration
    ARXIV_BASE_URL: str = "https://arxiv.org"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # HTML Generator Colors
    COLORS: Dict[str, str] = {
        "abstract": "#7d7dff",
        "background": "#ff9f43",
        "contribution": "#1dd1a1",
        "method": "#ff6b6b",
        "results": "#feca57"
    }
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """
        Get all configuration values as a dictionary.
        
        Returns:
            Dictionary of all configuration values
        """
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate required configuration values.
        
        Returns:
            True if all required values are set, False otherwise
        """
        if not cls.OPENAI_API_KEY:
            print("Error: OPENAI_API_KEY is not set")
            return False
        
        return True
    
    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """
        Get standard HTTP headers for requests.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            'User-Agent': cls.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }


class PromptTemplates:
    """
    Centralized prompt templates for LLM interactions.
    
    This keeps all prompts in one place for easy maintenance and updates.
    """
    
    EXTRACTION_PROMPT = """Please extract the following information from this academic paper. Be comprehensive and detailed.

1. **Paper Title**: The main title of the paper.
2. **Authors**: List of authors as an array of strings, one per author.
3. **Abstract**: Extract a CONCISE summary of the paper (100-150 words). Focus on the core problem, approach, and key results. Use **bold** markdown to highlight important metrics and achievements. When appropriate, reference key figures showing results (e.g., "achieving **10× speedup** (see Figure 9)").
4. **Background**: Extract main background topics with:
   - Blog-style writing with descriptive titles
   - Use **bold** markdown to highlight key concepts, challenges, and important facts
   - Keep content concise (100-150 words per section)
   - Remove any "(details not specified)" or similar placeholder text
5. **Contributions**: Extract main contributions with:
   - Clear, descriptive titles
   - Highlight ALL key metrics, numbers, and achievements using **bold** markdown
   - Focus on concrete improvements and quantifiable results
   - When appropriate, reference figures that illustrate the contribution
6. **Method**: Detailed methodology with:
   - Use **bold** to highlight key techniques, algorithms, and design choices
   - Organize content in logical subsections (e.g., "System Architecture", "Algorithm Design", "Implementation Details")
   - Include ONLY figures that show HOW the system works:
     * Architecture diagrams, system design
     * Algorithm descriptions, workflow diagrams
     * Implementation details, component diagrams
     * Design intuitions, parallelism plans
   - Do NOT include performance evaluation figures here
   - Only reference figures that directly support the method description
7. **Results**: Comprehensive results with:
   - Use **bold** to highlight ALL performance numbers, improvements, and comparisons
   - Organize by evaluation aspects (e.g., "Performance Comparison", "Scalability Analysis", "Energy Efficiency")
   - Include ONLY figures that show evaluation results:
     * Performance comparisons (with "vs", "comparison")
     * Benchmark results, speedup graphs
     * Experimental evaluations
   - Properly distinguish between figures and tables
   - Remove any placeholder text like "(details not specified in the provided content)"
"""
    
    SUMMARIZATION_PROMPT = """Please summarize the following text concisely to about {max_length} characters:

{text}"""
    
    TRANSLATION_PROMPT = """Please translate the following academic paper content from English to Chinese. 
Maintain the structure and keep technical terms accurate. Return the translation in the same JSON format.

Content to translate:
{content}

Return the Chinese translation in this exact format, maintaining all structure."""