#!/usr/bin/env python3
"""
Test script for Streamlit PDF handling
"""
import os
import sys

# Check if streamlit is installed
try:
    import streamlit as st
    print("✅ Streamlit is installed successfully!")
    print(f"   Version: {st.__version__}")
except ImportError as e:
    print(f"❌ Streamlit is not installed: {e}")
    sys.exit(1)

# Check if BTMR modules can be imported
try:
    from src.arxiv_fetcher import ArxivFetcher
    from src.paper_extractor import OpenAIExtractor
    from src.pdf_generator import PDFGenerator
    from src.html_generator import HTMLGenerator
    print("✅ BTMR modules imported successfully!")
except ImportError as e:
    print(f"❌ Failed to import BTMR modules: {e}")
    sys.exit(1)

# Check if OpenAI API key is set
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ OpenAI API key is configured (starts with: {api_key[:10]}...)")
else:
    print("⚠️  OpenAI API key not found in environment variables")
    print("   Please set OPENAI_API_KEY in your .env file")

print("\n📋 Instructions to run the Streamlit app:")
print("1. Make sure you have a PDF paper to test with")
print("2. Run: uv run streamlit run streamlit_app.py")
print("3. Open the URL shown in your browser (usually http://localhost:8501)")
print("4. Upload a PDF file and click 'Process Paper'")
print("\nFeatures to test:")
print("- PDF file upload")
print("- Content extraction from PDF")
print("- AI-powered paper summarization")
print("- HTML/PDF output generation")
print("- Download generated summaries")