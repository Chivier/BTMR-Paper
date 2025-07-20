# BTMR - Beautiful Text Mining Reader

Extract key information from academic papers using LLM APIs and generate beautiful HTML/PDF summaries with a compact, elegant design.

## Features

- **Multi-format Support**: Fetch papers from ArXiv in HTML, PDF, or LaTeX source format
- **Advanced PDF OCR**: Uses Surya OCR for accurate text extraction from complex academic PDFs
- **LLM Extraction**: Uses OpenAI-compatible APIs to intelligently extract:
  - Title and Authors
  - Abstract with concise summaries
  - Background sections with descriptive titles
  - Main Contributions with brief summaries
  - Method descriptions with figures and key points
  - Results with tables, figures, and evaluations
- **Beautiful Output Formats**:
  - **HTML (default)**: Compact, elegant design with color-coded sections
  - **PDF**: Traditional document format with styled sections
  - Bento-style layout with subtle dividers
  - Automatic image embedding and localization
- **Language Support**: 
  - Default English output
  - Chinese translation with `--lang zh` option

## Installation

1. Clone the repository:
```bash
git clone <your-repo>
cd BTMR
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

Note: Surya OCR is required for proper PDF text extraction from academic papers with complex layouts, equations, and multiple columns.

3. Set up API keys:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Usage

### Basic Usage

Extract paper and generate beautiful HTML (default):
```bash
python main.py https://arxiv.org/abs/2301.12345
```

Generate PDF instead:
```bash
python main.py https://arxiv.org/abs/2301.12345 --format pdf
```

### Advanced Options

```bash
# Use OpenAI instead of Claude
python main.py https://arxiv.org/abs/2301.12345 -p openai

# Specify output filename
python main.py https://arxiv.org/abs/2301.12345 -o my_paper_summary.pdf

# Use specific model (overrides MODEL_NAME environment variable)
python main.py https://arxiv.org/abs/2301.12345 -m claude-3-haiku-20240307

# Use custom OpenAI-compatible endpoint (e.g., local model)
python main.py https://arxiv.org/abs/2301.12345 -p openai --openai-base-url http://localhost:1234/v1

# Use Azure OpenAI
python main.py https://arxiv.org/abs/2301.12345 -p openai --openai-base-url https://your-resource.openai.azure.com

# Force specific fetch format (auto, html, pdf, source)
python main.py https://arxiv.org/abs/2301.12345 -f pdf

# Generate HTML output (default)
python main.py https://arxiv.org/abs/2301.12345 --format html

# Generate PDF output
python main.py https://arxiv.org/abs/2301.12345 --format pdf

# Generate output in Chinese
python main.py https://arxiv.org/abs/2301.12345 --lang zh

# Save extracted data as JSON
python main.py https://arxiv.org/abs/2301.12345 --save-json

# Load from previously saved JSON
python main.py https://arxiv.org/abs/2301.12345 --load-json paper_data.json
```

## Configuration

### API Keys

Set your configuration in the `.env` file:
- `OPENAI_API_KEY`: For OpenAI API  
- `OPENAI_API_BASE`: OpenAI API base URL (default: `https://api.openai.com/v1`)
- `MODEL_NAME`: Default model to use (default: `gpt-4.1`)
- `TRANSLATE_MODEL`: Model for Chinese translation when using `--lang zh` (default: `gpt-4.1`)

### Model Options

**Available OpenAI models:**
- `gpt-4.1` (default, recommended)
- `gpt-4-turbo-preview`
- `gpt-4o`
- `gpt-3.5-turbo`

### OpenAI-Compatible Endpoints

The tool supports any OpenAI-compatible API endpoint via `OPENAI_API_BASE`:

**Local Models:**
```bash
# Ollama
OPENAI_API_BASE=http://localhost:11434/v1

# LM Studio  
OPENAI_API_BASE=http://localhost:1234/v1

# vLLM
OPENAI_API_BASE=http://localhost:8000/v1
```

**Cloud Services:**
```bash
# Azure OpenAI
OPENAI_API_BASE=https://your-resource.openai.azure.com

# OpenRouter
OPENAI_API_BASE=https://openrouter.ai/api/v1

# Together AI
OPENAI_API_BASE=https://api.together.xyz/v1
```

### Supported Paper Sources

- ArXiv URLs: `https://arxiv.org/abs/2301.12345`
- ArXiv PDFs: `https://arxiv.org/pdf/2301.12345.pdf`
- ArXiv IDs: `2301.12345` or `cs.CV/2301.12345`

## Output

The tool generates:
1. A beautiful PDF summary following the template design
2. Optional JSON file with extracted data (use `--save-json`)

## Example

```bash
# Extract a machine learning paper
python main.py https://arxiv.org/abs/2309.17143 -o attention_paper.pdf --save-json

# Output:
# ✅ Successfully generated PDF: attention_paper.pdf
# 📄 Paper Summary:
# Title: Attention Is All You Need
# Authors: Ashish Vaswani, et al.
# 
# 🎯 Main Contributions (3):
#   1. Proposed the Transformer architecture...
#   2. Demonstrated state-of-the-art results...
#   3. Showed that attention mechanisms...
```

## Troubleshooting

1. **Chinese Font Issues**: The tool will try to auto-detect Chinese fonts. If Chinese text doesn't render properly, you may need to install appropriate fonts for your system.

2. **API Rate Limits**: Both Claude and OpenAI have rate limits. If you encounter errors, wait a moment before retrying.

3. **Large Papers**: Very long papers may be truncated before sending to the LLM. The tool limits content to ~10,000 characters.

## Project Structure

```
BTMR/
├── main.py                 # Main entry point for the CLI tool
├── arxiv_fetcher.py       # Fetches papers from ArXiv in various formats
├── paper_extractor.py     # Extracts structured information using LLM APIs
├── html_generator.py      # Generates beautiful HTML output with compact design
├── pdf_generator.py       # Generates PDF output from extracted data
├── image_processor.py     # Processes images and markdown (Surya OCR optional)
├── test_api.py           # Test script for API connectivity
├── requirements.txt       # Full dependencies including Surya OCR
├── .env.example          # Example environment configuration
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── output/               # Generated output files (gitignored)
```

## Key Files

- **main.py**: Command-line interface, handles arguments and orchestrates the pipeline
- **arxiv_fetcher.py**: Downloads papers from ArXiv, supports HTML/PDF/source formats
- **paper_extractor.py**: Uses OpenAI API to extract structured information from papers
- **html_generator.py**: Creates elegant HTML with:
  - Compact, modern typography
  - Color-coded sections with left borders
  - Responsive design
  - Bento-style subtle dividers
  - Local image embedding support
- **pdf_generator.py**: Converts extracted data to PDF format
- **image_processor.py**: Surya OCR integration for PDF processing and image handling

## Output

All generated files are saved to the `output/` directory:
- HTML files with embedded styles and images
- PDF summaries
- JSON data files (optional)

## License

MIT