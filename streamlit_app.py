#!/usr/bin/env python3
"""
Streamlit app for testing PDF handling in BTMR
"""
import streamlit as st
import os
import tempfile
import json
from datetime import datetime
from pathlib import Path
import base64

# Import BTMR modules
from src.arxiv_fetcher import ArxivFetcher
from src.paper_extractor import OpenAIExtractor
from src.pdf_generator import PDFGenerator
from src.html_generator import HTMLGenerator
from src.image_processor import ImageProcessor

# Configure Streamlit page
st.set_page_config(
    page_title="BTMR - PDF Paper Processor",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'output_html' not in st.session_state:
    st.session_state.output_html = None
if 'output_pdf' not in st.session_state:
    st.session_state.output_pdf = None

def process_pdf_file(pdf_file, language='en'):
    """Process uploaded PDF file and extract paper information"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded file
        pdf_path = os.path.join(temp_dir, pdf_file.name)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_file.getbuffer())
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("output", f"streamlit_paper_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract content from PDF
        fetcher = ArxivFetcher()
        st.info("📄 Extracting content from PDF...")
        
        # Try to extract content using the fetcher's PDF processing
        content = fetcher.process_local_pdf(pdf_path)
        
        if not content:
            st.error("Failed to extract content from PDF")
            return None
        
        # Process with LLM
        st.info("🤖 Processing with AI model...")
        extractor = OpenAIExtractor(language=language)
        extracted_data = extractor.extract(content, output_dir)
        
        return extracted_data, output_dir

def generate_output(extracted_data, output_dir, format='html'):
    """Generate HTML or PDF output from extracted data"""
    if format == 'html':
        output_path = os.path.join(output_dir, "summary.html")
        generator = HTMLGenerator()
        generator.generate(extracted_data, output_path)
        
        # Read the generated HTML
        with open(output_path, 'r', encoding='utf-8') as f:
            return f.read(), output_path
    else:
        output_path = os.path.join(output_dir, "summary.pdf")
        generator = PDFGenerator()
        generator.generate(extracted_data, output_path)
        
        # Read the generated PDF
        with open(output_path, 'rb') as f:
            return f.read(), output_path

def display_extracted_data(data):
    """Display extracted data in Streamlit UI"""
    if not data:
        return
    
    # Title and Authors
    st.header(data.get('title', 'Untitled'))
    
    authors = data.get('authors', [])
    if authors:
        st.subheader("Authors")
        cols = st.columns(min(len(authors), 4))
        for i, author in enumerate(authors):
            with cols[i % 4]:
                st.info(f"👤 {author}")
    
    # Abstract
    if 'abstract' in data:
        st.subheader("📝 Abstract")
        st.write(data['abstract'])
    
    # Background
    if 'background' in data:
        st.subheader("📚 Background")
        for item in data['background']:
            if isinstance(item, dict):
                st.write(f"**{item.get('subtitle', '')}**")
                st.write(item.get('content', ''))
            else:
                st.write(item)
    
    # Contributions
    if 'contributions' in data:
        st.subheader("🎯 Main Contributions")
        for i, contrib in enumerate(data['contributions'], 1):
            st.write(f"**C{i}.** {contrib}")
    
    # Methods
    if 'methods' in data:
        st.subheader("🔧 Methods")
        for method in data['methods']:
            if isinstance(method, dict):
                st.write(f"**{method.get('subtitle', '')}**")
                st.write(method.get('content', ''))
                if 'image_url' in method and method['image_url']:
                    st.image(method['image_url'], caption=method.get('image_caption', ''))
            else:
                st.write(method)
    
    # Results
    if 'results' in data:
        st.subheader("📊 Results")
        for result in data['results']:
            if isinstance(result, dict):
                st.write(f"**{result.get('subtitle', '')}**")
                st.write(result.get('content', ''))
                if 'evaluation' in result:
                    st.info(f"📈 {result['evaluation']}")
            else:
                st.write(result)

# Main UI
st.title("📚 BTMR - Beautiful Text Mining Reader")
st.markdown("### PDF Paper Processing & Summarization")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Language selection
    language = st.selectbox(
        "Output Language",
        ["en", "zh"],
        format_func=lambda x: "English" if x == "en" else "Chinese"
    )
    
    # Model configuration
    st.subheader("AI Model Settings")
    model_name = st.text_input(
        "Model Name",
        value=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        help="OpenAI model to use for extraction"
    )
    
    api_base = st.text_input(
        "API Base URL",
        value=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        help="OpenAI API base URL"
    )
    
    # Output format
    st.subheader("Output Settings")
    output_format = st.radio(
        "Output Format",
        ["HTML", "PDF"],
        help="Choose the output format for the summary"
    )

# Main content area
tab1, tab2, tab3 = st.tabs(["📤 Upload & Process", "📊 Extracted Data", "📄 Generated Output"])

with tab1:
    st.markdown("### Upload a PDF Paper")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload an academic paper in PDF format"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        st.write(f"File size: {uploaded_file.size / 1024:.2f} KB")
        
        # Process button
        if st.button("🚀 Process Paper", type="primary"):
            with st.spinner("Processing paper... This may take a few minutes."):
                try:
                    # Process the PDF
                    result = process_pdf_file(uploaded_file, language)
                    
                    if result:
                        extracted_data, output_dir = result
                        st.session_state.extracted_data = extracted_data
                        
                        # Generate output
                        st.info(f"📝 Generating {output_format} output...")
                        output_content, output_path = generate_output(
                            extracted_data, 
                            output_dir, 
                            output_format.lower()
                        )
                        
                        if output_format == "HTML":
                            st.session_state.output_html = output_content
                            st.session_state.output_pdf = None
                        else:
                            st.session_state.output_pdf = output_content
                            st.session_state.output_html = None
                        
                        st.success(f"✅ Processing complete! Output saved to: {output_path}")
                        
                        # Show download button
                        if output_format == "HTML":
                            st.download_button(
                                label="📥 Download HTML",
                                data=output_content,
                                file_name=f"paper_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                                mime="text/html"
                            )
                        else:
                            st.download_button(
                                label="📥 Download PDF",
                                data=output_content,
                                file_name=f"paper_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf"
                            )
                    
                except Exception as e:
                    st.error(f"❌ Error processing paper: {str(e)}")
                    st.exception(e)

with tab2:
    st.markdown("### 📊 Extracted Paper Data")
    
    if st.session_state.extracted_data:
        # Display the extracted data
        display_extracted_data(st.session_state.extracted_data)
        
        # Option to download JSON
        st.divider()
        json_str = json.dumps(st.session_state.extracted_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download Extracted Data (JSON)",
            data=json_str,
            file_name=f"extracted_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    else:
        st.info("👆 Please upload and process a PDF file first")

with tab3:
    st.markdown("### 📄 Generated Output Preview")
    
    if st.session_state.output_html:
        st.markdown("#### HTML Output")
        # Display HTML in an iframe
        st.components.v1.html(st.session_state.output_html, height=800, scrolling=True)
        
    elif st.session_state.output_pdf:
        st.markdown("#### PDF Output")
        # Display PDF
        base64_pdf = base64.b64encode(st.session_state.output_pdf).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("👆 Please upload and process a PDF file first")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>BTMR - Beautiful Text Mining Reader | Made with ❤️ using Streamlit</p>
    <p>Powered by OpenAI GPT Models</p>
</div>
""", unsafe_allow_html=True)