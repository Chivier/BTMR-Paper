#!/usr/bin/env python3
"""
Test script to verify that backtrace logging is working properly.
Run this script to test exception logging with full backtraces.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import our logging configuration first to initialize logging
from logging_config import setup_logging

from loguru import logger

def test_nested_exception():
    """Test nested exception logging with backtraces."""
    def level3():
        raise ValueError("This is a test exception from level 3")
    
    def level2():
        try:
            level3()
        except ValueError as e:
            raise RuntimeError("Level 2 error") from e
    
    def level1():
        try:
            level2()
        except RuntimeError as e:
            raise Exception("Level 1 error") from e
    
    try:
        level1()
    except Exception as e:
        logger.exception(f"Test exception caught: {str(e)}")
        print("Exception logged with backtrace - check output/app.log and output/errors.log")

def test_api_simulation():
    """Simulate an API error with backtrace."""
    try:
        # Simulate some API processing
        data = {"test": "data"}
        result = data["missing_key"]  # This will raise KeyError
    except Exception as e:
        logger.exception(f"API processing failed: {str(e)}")
        print("API error logged with backtrace")

def test_paper_processing_simulation():
    """Simulate a paper processing error with context."""
    paper_id = "test_paper_123"
    try:
        # Simulate paper processing steps
        def fetch_content():
            raise ConnectionError("Failed to connect to ArXiv server")
        
        def extract_data():
            # This won't be reached due to fetch error
            pass
        
        fetch_content()
        extract_data()
    except Exception as e:
        logger.exception(f"Paper processing failed for {paper_id}: {str(e)}")
        print(f"Paper processing error logged with full context for {paper_id}")

if __name__ == "__main__":
    print("Testing backtrace logging configuration...")
    print("Check the following log files after running:")
    print("- output/app.log (general application logs)")
    print("- output/errors.log (error-specific logs)")
    print()
    
    logger.info("Starting backtrace logging tests")
    
    print("1. Testing nested exception...")
    test_nested_exception()
    
    print("\n2. Testing API simulation...")
    test_api_simulation()
    
    print("\n3. Testing paper processing simulation...")
    test_paper_processing_simulation()
    
    logger.info("Backtrace logging tests completed")
    print("\nTests completed. Check the log files to verify backtrace information is present.")
    print("You should see:")
    print("- Full stack traces with function names and line numbers")
    print("- Variable values at each exception point")
    print("- Chained exception details")
    print("- Separate error logs in errors.log")
