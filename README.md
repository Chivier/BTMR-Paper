# BTMR - Beautiful Text Mining Reader

BTMR (Beautiful Text Mining Reader) is a powerful Python tool that extracts and summarizes academic papers from ArXiv using LLM APIs. It fetches papers, uses AI to extract structured information, and generates beautiful HTML or PDF summaries with intelligent figure classification.

## Features

- 🚀 **Multi-format Support**: Fetches papers from ArXiv in HTML, PDF, or LaTeX source format
- 🤖 **LLM-powered Extraction**: Uses OpenAI-compatible APIs to extract structured information
- 🎨 **Beautiful Output**: Generates elegant HTML or PDF summaries with color-coded sections
- 🖼️ **Smart Image Handling**: Automatically classifies and places figures in appropriate sections
- 🌍 **Multi-language**: Supports both English and Chinese output
- 📊 **Metadata Tracking**: Records processing history in CSV for easy management
- 🧹 **Output Management**: Includes cleanup scripts for storage management

## Installation

### Basic Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/BTMR.git
cd BTMR

# Install dependencies (without advanced PDF processing)
pip install -r requirements-lite.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY
```

### Full Installation (with Surya OCR)
```bash
# For better PDF processing with Surya OCR
pip install -r requirements.txt
```

## Quick Start

### Basic Usage
```bash
# Generate HTML summary from ArXiv paper
python main.py https://arxiv.org/abs/2301.12345

# Generate PDF output
python main.py https://arxiv.org/abs/2301.12345 --format pdf

# Generate Chinese summary
python main.py https://arxiv.org/abs/2301.12345 --lang zh

# Save intermediate JSON data
python main.py https://arxiv.org/abs/2301.12345 --save-json
```

### Advanced Usage
```bash
# Force specific format for ArXiv fetching
python main.py https://arxiv.org/abs/2301.12345 --fetch-format html

# Process local markdown file
python main.py paper.md --input-type md

# Load from previously extracted JSON
python main.py --load-json output/paper_20240101_120000/extracted_data.json --format pdf
```

## Project Structure

```
BTMR/
├── src/                      # Core modules
│   ├── __init__.py          # Package initialization
│   ├── arxiv_fetcher.py     # ArXiv paper fetching logic
│   ├── paper_extractor.py   # LLM-based information extraction
│   ├── html_generator.py    # HTML output generation
│   ├── pdf_generator.py     # PDF output generation
│   ├── image_processor.py   # Image extraction and processing
│   └── metadata_logger.py   # CSV metadata logging
├── scripts/                  # Utility scripts
│   └── cleanup_output.py    # Output directory management
├── tests/                    # Test scripts
│   ├── test_api.py          # API connectivity test
│   └── check_final_improvements.py  # Image classification checker
├── output/                   # Generated outputs (git-ignored)
│   ├── paper_YYYYMMDD_HHMMSS/  # Individual paper outputs
│   └── paper_metadata.csv   # Processing history
├── main.py                   # Main entry point
├── requirements.txt          # Full dependencies
├── requirements-lite.txt     # Basic dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Module Documentation

### Core Modules (src/)

#### arxiv_fetcher.py
Handles fetching papers from ArXiv with multiple format support:
- **ArxivFetcher class**: Main fetcher with fallback strategies
  - `fetch()`: Tries HTML → PDF → LaTeX source → Abstract
  - `fetch_html()`: Fetches and processes HTML version with images
  - `fetch_pdf()`: Extracts text from PDF (with optional Surya OCR)
  - `fetch_source()`: Downloads and compiles LaTeX source
  - `_extract_figure_with_caption()`: Extracts figure metadata for classification

#### paper_extractor.py
Extracts structured information using LLM:
- **OpenAIExtractor class**: OpenAI-compatible API extractor
  - `extract()`: Main extraction method with smart prompts
  - `_translate_to_chinese()`: Translates content to Chinese
  - Implements intelligent figure/table classification rules
  - Supports context-aware image placement

#### html_generator.py
Generates beautiful HTML output:
- **HTMLGenerator class**: Creates styled HTML summaries
  - Color-coded sections (purple abstract, orange background, etc.)
  - Bento-style layout with responsive design
  - Smart image embedding with base64 encoding
  - Markdown table support

#### pdf_generator.py
Generates PDF output using ReportLab:
- **PDFGenerator class**: Creates structured PDF documents
  - Automatic font detection for Chinese support
  - Section-based layout with proper formatting
  - Image inclusion with captions

#### image_processor.py
Handles image extraction and processing:
- **ImageProcessor class**: Manages images from various sources
  - `process_html()`: Extracts images from HTML
  - `process_markdown()`: Handles markdown image references
  - `download_and_save_image()`: Downloads with validation
  - Optional Surya OCR integration

#### metadata_logger.py
Tracks processing history:
- **MetadataLogger class**: CSV-based metadata storage
  - `log_paper()`: Records paper processing details
  - `get_recent_papers()`: Retrieves processing history
  - `get_statistics()`: Provides usage statistics

### Scripts

#### cleanup_output.py
Output directory management tool:
```bash
# Show statistics
python scripts/cleanup_output.py stats

# Remove outputs older than 7 days (dry run)
python scripts/cleanup_output.py age 7

# Actually remove old outputs
python scripts/cleanup_output.py age 7 --execute

# Keep total size under 1GB
python scripts/cleanup_output.py size 1000 --execute

# Clean orphaned CSV entries
python scripts/cleanup_output.py orphans --execute
```

## Configuration

### Environment Variables (.env)
```bash
# Required
OPENAI_API_KEY=your-api-key-here

# Optional
OPENAI_API_BASE=https://api.openai.com/v1  # API endpoint
MODEL_NAME=gpt-4-turbo                      # Default model
TRANSLATE_MODEL=gpt-4-turbo                 # Translation model
```

### Supported LLM Providers
Works with any OpenAI-compatible endpoint:
- OpenAI (default)
- Azure OpenAI
- Anthropic Claude (via proxy)
- Local models (Ollama, LM Studio, vLLM)
- Cloud services (OpenRouter, Together AI)

## Output Structure

Each paper creates a timestamped folder:
```
output/paper_20240101_120000/
├── summary.html              # Main output (or summary.pdf)
├── extracted_data.json       # Extracted structured data
├── image_metadata.json       # Figure caption mappings
└── images/                   # Extracted figures
    ├── arxiv_img_1.png      # Original images
    ├── figure_1.png         # Renamed based on captions
    └── ...
```

## Key Features Explained

### Intelligent Image Classification
- Automatically distinguishes between method figures and result figures
- Uses caption analysis and keywords for classification
- Prevents duplicate images across sections
- Supports smart placement with contextual references

### Multi-format Fetching Strategy
1. **HTML**: Best quality, includes formatted text and images
2. **PDF**: Fallback with OCR support for complex layouts
3. **LaTeX**: Compiles source when available
4. **Abstract**: Last resort for basic information

### Metadata Tracking
- CSV file tracks all processed papers
- Records processing time, format used, figure counts
- Enables batch management and cleanup
- Provides usage statistics

## Testing

```bash
# Test API connectivity
python tests/test_api.py

# Check image classification improvements
python tests/check_final_improvements.py
```

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure `OPENAI_API_KEY` is set in `.env`
   - Check API endpoint compatibility

2. **Image Download Failures**
   - Some ArXiv papers may have restricted images
   - The tool will skip invalid image URLs

3. **PDF Processing**
   - Install full requirements for Surya OCR support
   - Fallback to basic extraction if Surya unavailable

4. **Memory Issues**
   - Large papers (>50k characters) are automatically truncated
   - Use cleanup scripts to manage storage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commits
4. Add tests if applicable
5. Submit a pull request

## License

AGPL-3.0 License (see [LICENSE](LICENSE))

## Acknowledgments

- ArXiv for providing open access to papers
- OpenAI for powerful language models
- The open-source community for excellent libraries