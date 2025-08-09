#!/usr/bin/env python3
"""
Test backend logging specifically for API integration.
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the logging configuration and initialize it
from logging_config import setup_logging
from loguru import logger

# Force setup the logging
setup_logging()

def test_backend_error():
    """Test backend error logging similar to what would happen in the API"""
    try:
        # Simulate a backend processing error like would happen in services.py
        paper_id = "test_paper_456"
        
        def simulate_paper_processing():
            # Simulate nested calls like in the actual backend
            def fetch_arxiv_content():
                raise ConnectionError("ArXiv server unreachable")
            
            def extract_with_openai():
                fetch_arxiv_content()
                return {"title": "test"}
            
            def generate_html():
                return extract_with_openai()
            
            return generate_html()
        
        simulate_paper_processing()
        
    except Exception as e:
        # This is exactly what we do in services.py
        logger.exception(f"Paper processing failed for {paper_id}: {str(e)}")
        print(f"✅ Backend error logged for paper {paper_id}")

def test_api_error():
    """Test API-level error logging"""
    try:
        # Simulate an API endpoint error
        request_url = "/api/v1/papers/process"
        request_method = "POST"
        
        # Simulate some API processing
        config = {"model": "gpt-4"}
        missing_value = config["missing_key"]  # This will fail
        
    except Exception as e:
        # This is what the global exception handler does
        logger.exception(f"Unhandled exception occurred during {request_method} {request_url}: {str(e)}")
        print("✅ API error logged with full context")

if __name__ == "__main__":
    print("🔧 Testing backend logging integration...")
    print("📁 Check these files after running:")
    print("   - output/app.log")
    print("   - output/errors.log")
    print()
    
    logger.info("Starting backend logging integration test")
    
    print("1. Testing backend processing error...")
    test_backend_error()
    
    print("2. Testing API error...")  
    test_api_error()
    
    logger.info("Backend logging test completed")
    print("\n✅ Tests completed!")
    print("📋 Check log files to verify:")
    print("   - Full stack traces with variable values")
    print("   - Function call hierarchy")
    print("   - Exception chaining")
    print("   - Separate error logs")
