"""
Configuration service for managing application settings.

Handles reading, updating, and persisting configuration values.
"""
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv, set_key, unset_key

from src.config import Config
from .models import ConfigurationRequest, ConfigurationResponse


class ConfigurationService:
    """Service for managing application configuration."""
    
    def __init__(self):
        self.env_file = Path(".env")
        self.config_file = Path("config.json")
        load_dotenv()
        # Reload Config class attributes from environment after loading .env
        self._reload_config_from_env()
        # Load config file on startup
        self._load_config_file()
    
    def get_configuration(self) -> ConfigurationResponse:
        """Get current configuration."""
        config_dict = Config.get_config_dict()
        return ConfigurationResponse.from_config(config_dict)
    
    def update_configuration(self, request: ConfigurationRequest) -> ConfigurationResponse:
        """Update configuration with new values."""
        # Create .env file if it doesn't exist
        if not self.env_file.exists():
            self.env_file.touch()
        
        # Update environment variables for API-related settings
        env_updates = {}
        
        if request.openai_api_key is not None:
            env_updates["OPENAI_API_KEY"] = request.openai_api_key
            
        if request.openai_api_base is not None:
            env_updates["OPENAI_API_BASE"] = request.openai_api_base
            
        if request.default_model is not None:
            env_updates["MODEL_NAME"] = request.default_model
            
        if request.translate_model is not None:
            env_updates["TRANSLATE_MODEL"] = request.translate_model
            
        if request.log_level is not None:
            env_updates["LOG_LEVEL"] = request.log_level
        
        # Update .env file
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(str(self.env_file), key, value)
            else:  # Remove empty values
                unset_key(str(self.env_file), key)
        
        # Update runtime configuration for other settings
        if request.max_paper_length is not None:
            Config.MAX_PAPER_LENGTH = request.max_paper_length
            
        if request.max_image_size_mb is not None:
            Config.MAX_IMAGE_SIZE_MB = request.max_image_size_mb
            
        if request.request_timeout is not None:
            Config.REQUEST_TIMEOUT = request.request_timeout
            
        if request.default_output_format is not None:
            Config.DEFAULT_OUTPUT_FORMAT = request.default_output_format
            
        if request.default_language is not None:
            Config.DEFAULT_LANGUAGE = request.default_language
            
        if request.image_quality is not None:
            Config.IMAGE_QUALITY = request.image_quality
            
        if request.max_image_dimension is not None:
            Config.MAX_IMAGE_DIMENSION = request.max_image_dimension
        
        # Save non-environment settings to config file
        self._save_config_file()
        
        # Reload environment variables
        load_dotenv(override=True)
        
        # Update Config class attributes from environment
        Config.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        Config.OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        Config.DEFAULT_MODEL = os.getenv("MODEL_NAME", "gpt-4-turbo")
        Config.TRANSLATE_MODEL = os.getenv("TRANSLATE_MODEL", "gpt-4-turbo")
        Config.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        return self.get_configuration()
    
    def _reload_config_from_env(self):
        """Reload Config class attributes from environment variables."""
        Config.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        Config.OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        Config.DEFAULT_MODEL = os.getenv("MODEL_NAME", "gpt-4-turbo")
        Config.TRANSLATE_MODEL = os.getenv("TRANSLATE_MODEL", "gpt-4-turbo")
        Config.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    def _save_config_file(self):
        """Save non-environment configuration to JSON file."""
        config_data = {
            "MAX_PAPER_LENGTH": Config.MAX_PAPER_LENGTH,
            "MAX_IMAGE_SIZE_MB": Config.MAX_IMAGE_SIZE_MB,
            "REQUEST_TIMEOUT": Config.REQUEST_TIMEOUT,
            "DEFAULT_OUTPUT_FORMAT": Config.DEFAULT_OUTPUT_FORMAT,
            "DEFAULT_LANGUAGE": Config.DEFAULT_LANGUAGE,
            "IMAGE_QUALITY": Config.IMAGE_QUALITY,
            "MAX_IMAGE_DIMENSION": Config.MAX_IMAGE_DIMENSION,
            "COLORS": Config.COLORS
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def _load_config_file(self):
        """Load configuration from JSON file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Update Config class attributes
                for key, value in config_data.items():
                    if hasattr(Config, key):
                        setattr(Config, key, value)
                        
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
    
    def reset_configuration(self) -> ConfigurationResponse:
        """Reset configuration to defaults."""
        # Remove custom config file
        if self.config_file.exists():
            self.config_file.unlink()
        
        # Reset Config class to defaults
        Config.MAX_PAPER_LENGTH = 50000
        Config.MAX_IMAGE_SIZE_MB = 10.0
        Config.REQUEST_TIMEOUT = 30
        Config.DEFAULT_OUTPUT_FORMAT = "html"
        Config.DEFAULT_LANGUAGE = "en"
        Config.IMAGE_QUALITY = 85
        Config.MAX_IMAGE_DIMENSION = 2000
        Config.COLORS = {
            "abstract": "#7d7dff",
            "background": "#ff9f43",
            "contribution": "#1dd1a1",
            "method": "#ff6b6b",
            "results": "#feca57"
        }
        
        return self.get_configuration()
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration and return status."""
        issues = []
        warnings = []
        
        # Check required settings
        if not Config.OPENAI_API_KEY:
            issues.append("OpenAI API key is not set")
        
        # Check API base URL format
        if Config.OPENAI_API_BASE and not Config.OPENAI_API_BASE.startswith(('http://', 'https://')):
            issues.append("OpenAI API base URL must start with http:// or https://")
        
        # Check numeric ranges
        if Config.MAX_PAPER_LENGTH < 1000:
            warnings.append("Max paper length is very low (< 1000 characters)")
        elif Config.MAX_PAPER_LENGTH > 100000:
            warnings.append("Max paper length is very high (> 100,000 characters)")
        
        if Config.MAX_IMAGE_SIZE_MB < 1:
            warnings.append("Max image size is very low (< 1 MB)")
        elif Config.MAX_IMAGE_SIZE_MB > 50:
            warnings.append("Max image size is very high (> 50 MB)")
        
        if Config.REQUEST_TIMEOUT < 10:
            warnings.append("Request timeout is very low (< 10 seconds)")
        elif Config.REQUEST_TIMEOUT > 120:
            warnings.append("Request timeout is very high (> 120 seconds)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "config_file_exists": self.config_file.exists(),
            "env_file_exists": self.env_file.exists()
        }
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get list of available models from OpenAI API."""
        import requests
        
        # Always use credentials from config/environment
        api_key = Config.OPENAI_API_KEY
        api_base = Config.OPENAI_API_BASE
        
        # Check if API key is available
        if not api_key:
            return {
                "models": [],
                "error": "OpenAI API key not configured",
                "custom_note": "Please configure your OpenAI API key to see available models"
            }
        
        try:
            # Fetch models from OpenAI API
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Use the configured API base URL
            api_base = api_base.rstrip('/')
            response = requests.get(
                f"{api_base}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                models = []
                
                for model in data.get('data', []):
                    model_id = model.get('id', '')
                    model_name = model.get('name', model_id)
                    model_desc = model.get('description', f"Model: {model_name}")
                    
                    models.append({
                        "id": model_id,
                        "name": model_name,  # Use model name
                        "description": model_desc,
                        "recommended": False,
                        "owned_by": model.get('owned_by', 'openai'),
                        "created": model.get('created', 0)
                    })
                
                # Sort models: recommended first, then by name
                models.sort(key=lambda x: (not x["recommended"], x["name"]))
                
                return {
                    "models": models,
                    "custom_note": "Models fetched from OpenAI API. You can also use custom models by entering the model name directly",
                    "last_updated": response.headers.get('date', 'Unknown')
                }
            
            else:
                # API request failed
                return {
                    "models": self._get_fallback_models(),
                    "error": f"Failed to fetch models from API (HTTP {response.status_code})",
                    "custom_note": "Using fallback model list. Please check your API key and connection"
                }
                
        except requests.exceptions.RequestException as e:
            # Network or request error
            return {
                "models": self._get_fallback_models(),
                "error": f"Network error: {str(e)}",
                "custom_note": "Using fallback model list. Please check your internet connection and API configuration"
            }
        except Exception as e:
            # Other errors
            return {
                "models": self._get_fallback_models(),
                "error": f"Unexpected error: {str(e)}",
                "custom_note": "Using fallback model list"
            }
    
    def test_model(self, model_id: str) -> Dict[str, Any]:
        """Test if a specific model is available and get its capabilities."""
        import requests
        
        # Always use credentials from config/environment
        api_key = Config.OPENAI_API_KEY
        api_base = Config.OPENAI_API_BASE
        
        if not api_key:
            return {
                "available": False,
                "error": "OpenAI API key not configured. Please set your API key in the settings.",
                "capabilities": {
                    "supports_images": False,
                    "supports_files": False,
                    "max_tokens": None,
                    "context_length": None
                }
            }
        
        try:
            # Test model with a simple completion request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            api_base = api_base.rstrip('/')
            test_payload = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": "Hello, respond with 'Available' if you can process this request."}
                ],
                "max_tokens": 10,
                "temperature": 0
            }
            
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Determine model capabilities based on model ID
                capabilities = self._determine_model_capabilities(model_id)
                
                return {
                    "available": True,
                    "model_id": model_id,
                    "response": data.get('choices', [{}])[0].get('message', {}).get('content', ''),
                    "usage": data.get('usage', {}),
                    "capabilities": capabilities,
                    "test_successful": True
                }
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                return {
                    "available": False,
                    "error": error_data.get('error', {}).get('message', f"HTTP {response.status_code}"),
                    "status_code": response.status_code,
                    "capabilities": {
                        "supports_images": False,
                        "supports_files": False,
                        "max_tokens": None,
                        "context_length": None
                    }
                }
                
        except requests.exceptions.Timeout:
            return {
                "available": False, 
                "error": "Request timeout - model may be slow or unavailable",
                "capabilities": {
                    "supports_images": False,
                    "supports_files": False,
                    "max_tokens": None,
                    "context_length": None
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                "available": False,
                "error": f"Network error: {str(e)}",
                "capabilities": {
                    "supports_images": False,
                    "supports_files": False,
                    "max_tokens": None,
                    "context_length": None
                }
            }
        except Exception as e:
            return {
                "available": False,
                "error": f"Unexpected error: {str(e)}",
                "capabilities": {
                    "supports_images": False,
                    "supports_files": False,
                    "max_tokens": None,
                    "context_length": None
                }
            }
    
    def _determine_model_capabilities(self, model_id: str) -> Dict[str, Any]:
        """Determine model capabilities based on model ID patterns."""
        model_id_lower = model_id.lower()
        
        # GPT-4 Vision models
        if any(x in model_id_lower for x in ['gpt-4-vision', 'gpt-4-turbo', 'gpt-4o']):
            return {
                "supports_images": True,
                "supports_files": True,
                "max_tokens": 4096 if 'gpt-4o-mini' in model_id_lower else 4096,
                "context_length": 128000,
                "vision_capable": True
            }
        
        # GPT-4 standard models
        elif model_id_lower.startswith('gpt-4'):
            return {
                "supports_images": False,
                "supports_files": True,
                "max_tokens": 4096,
                "context_length": 8192 if model_id_lower == 'gpt-4' else 32768,
                "vision_capable": False
            }
        
        # GPT-3.5 models
        elif model_id_lower.startswith('gpt-3.5'):
            return {
                "supports_images": False,
                "supports_files": False,
                "max_tokens": 4096,
                "context_length": 16385,
                "vision_capable": False
            }
        
        # Claude models (for custom endpoints)
        elif 'claude' in model_id_lower:
            return {
                "supports_images": True,
                "supports_files": True,
                "max_tokens": 4096,
                "context_length": 200000,
                "vision_capable": True
            }
        
        # Default/unknown models
        else:
            return {
                "supports_images": False,
                "supports_files": False,
                "max_tokens": None,
                "context_length": None,
                "vision_capable": False
            }

    def _get_fallback_models(self) -> list:
        """Get fallback model list when API is unavailable."""
        return [
            {
                "id": "gpt-4-turbo",
                "name": "gpt-4-turbo",
                "description": "Model: gpt-4-turbo",
                "recommended": True,
                "owned_by": "openai",
                "created": 0
            },
            {
                "id": "gpt-4o",
                "name": "gpt-4o",
                "description": "Model: gpt-4o",
                "recommended": True,
                "owned_by": "openai",
                "created": 0
            },
            {
                "id": "gpt-4",
                "name": "gpt-4",
                "description": "Model: gpt-4",
                "recommended": False,
                "owned_by": "openai",
                "created": 0
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "gpt-3.5-turbo",
                "description": "Model: gpt-3.5-turbo",
                "recommended": False,
                "owned_by": "openai",
                "created": 0
            },
            {
                "id": "gpt-4o-mini",
                "name": "gpt-4o-mini",
                "description": "Model: gpt-4o-mini",
                "recommended": False,
                "owned_by": "openai",
                "created": 0
            }
        ]
