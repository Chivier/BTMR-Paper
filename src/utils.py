"""
Utility Functions Module

Common utility functions used across the BTMR project.
Includes:
- File operations
- Text processing
- Image handling
- Validation functions
"""
import os
import re
import hashlib
from typing import Optional, List, Tuple, Dict, Any
from urllib.parse import urlparse, urljoin
import requests
from PIL import Image
import io


class TextUtils:
    """Text processing utility functions."""
    
    @staticmethod
    def truncate_text(text: str, max_length: int, add_ellipsis: bool = True) -> str:
        """
        Truncate text to maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum allowed length
            add_ellipsis: Whether to add "..." at the end
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        if add_ellipsis and max_length > 3:
            return text[:max_length - 3] + "..."
        
        return text[:max_length]
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean text by removing extra whitespace and special characters.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable() or char.isspace())
        
        return text
    
    @staticmethod
    def extract_keywords(text: str, keywords: List[str]) -> List[str]:
        """
        Extract keywords found in text (case-insensitive).
        
        Args:
            text: Text to search in
            keywords: List of keywords to find
            
        Returns:
            List of found keywords
        """
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords


class FileUtils:
    """File operation utility functions."""
    
    @staticmethod
    def ensure_directory(directory: str) -> str:
        """
        Ensure a directory exists, create if necessary.
        
        Args:
            directory: Directory path
            
        Returns:
            Absolute path to directory
        """
        abs_path = os.path.abspath(directory)
        os.makedirs(abs_path, exist_ok=True)
        return abs_path
    
    @staticmethod
    def get_unique_filename(directory: str, base_name: str, extension: str) -> str:
        """
        Get a unique filename in directory.
        
        Args:
            directory: Target directory
            base_name: Base filename without extension
            extension: File extension (with or without dot)
            
        Returns:
            Unique filename path
        """
        if not extension.startswith('.'):
            extension = '.' + extension
        
        counter = 0
        while True:
            if counter == 0:
                filename = f"{base_name}{extension}"
            else:
                filename = f"{base_name}_{counter}{extension}"
            
            filepath = os.path.join(directory, filename)
            if not os.path.exists(filepath):
                return filepath
            
            counter += 1
    
    @staticmethod
    def calculate_file_hash(filepath: str, algorithm: str = 'md5') -> str:
        """
        Calculate hash of a file.
        
        Args:
            filepath: Path to file
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
            
        Returns:
            Hex digest of file hash
        """
        hash_func = getattr(hashlib, algorithm)()
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()


class ImageUtils:
    """Image processing utility functions."""
    
    @staticmethod
    def validate_image_url(url: str) -> bool:
        """
        Validate if URL points to an image.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid image URL
        """
        if not url:
            return False
        
        # Check for data URLs
        if url.startswith('data:image/'):
            return True
        
        # Check file extension
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'}
        parsed = urlparse(url.lower())
        path = parsed.path
        
        return any(path.endswith(ext) for ext in image_extensions)
    
    @staticmethod
    def download_image(url: str, timeout: int = 30) -> Optional[bytes]:
        """
        Download image from URL.
        
        Args:
            url: Image URL
            timeout: Request timeout in seconds
            
        Returns:
            Image bytes or None if failed
        """
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return None
            
            return response.content
            
        except Exception as e:
            print(f"Failed to download image from {url}: {e}")
            return None
    
    @staticmethod
    def resize_image(image_bytes: bytes, max_dimension: int = 2000, quality: int = 85) -> bytes:
        """
        Resize image if larger than max dimension.
        
        Args:
            image_bytes: Original image bytes
            max_dimension: Maximum width or height
            quality: JPEG quality (0-100)
            
        Returns:
            Resized image bytes
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Check if resize needed
            if image.width <= max_dimension and image.height <= max_dimension:
                return image_bytes
            
            # Calculate new dimensions
            ratio = min(max_dimension / image.width, max_dimension / image.height)
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            
            # Resize image
            resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            if image.format == 'PNG' and image.mode in ('RGBA', 'LA'):
                resized.save(output, format='PNG')
            else:
                # Convert to RGB if necessary
                if resized.mode not in ('RGB', 'L'):
                    resized = resized.convert('RGB')
                resized.save(output, format='JPEG', quality=quality)
            
            return output.getvalue()
            
        except Exception as e:
            print(f"Failed to resize image: {e}")
            return image_bytes


class ValidationUtils:
    """Validation utility functions."""
    
    @staticmethod
    def is_valid_arxiv_id(arxiv_id: str) -> bool:
        """
        Validate ArXiv ID format.
        
        Args:
            arxiv_id: ArXiv ID to validate
            
        Returns:
            True if valid ArXiv ID
        """
        # Pattern: YYMM.NNNNN or category/YYMM.NNNNN
        patterns = [
            r'^\d{4}\.\d{4,5}(?:v\d+)?$',  # New format
            r'^[a-zA-Z\-]+/\d{4}\.\d{4,5}(?:v\d+)?$'  # Old format with category
        ]
        
        return any(re.match(pattern, arxiv_id) for pattern in patterns)
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid URL
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200 - len(ext)] + ext
        
        return filename.strip()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"


def parse_authors(authors: Any) -> str:
    """
    Parse authors from various formats to string.
    
    Args:
        authors: Authors in string or list format
        
    Returns:
        Comma-separated author string
    """
    if isinstance(authors, list):
        return ", ".join(authors)
    elif isinstance(authors, str):
        return authors
    else:
        return "Unknown Authors"