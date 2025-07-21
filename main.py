#!/usr/bin/env python3
"""
Main script to extract paper information and generate beautiful PDF
"""
import argparse
import sys
import os
import json
from datetime import datetime
from typing import Optional

from src.arxiv_fetcher import ArxivFetcher
from src.paper_extractor import OpenAIExtractor
from src.pdf_generator import PDFGenerator
from src.html_generator import HTMLGenerator
from src.image_processor import ImageProcessor
from src.metadata_logger import MetadataLogger


def main():
    parser = argparse.ArgumentParser(
        description="Extract paper information using LLM and generate beautiful PDF"
    )
    parser.add_argument(
        "input",
        help="URL or local file path (markdown or HTML)"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output filename (default: paper_summary_TIMESTAMP.html/.pdf)"
    )
    parser.add_argument(
        "--format",
        choices=["html", "pdf"],
        default="html",
        help="Output format (default: html)"
    )
    parser.add_argument(
        "-m", "--model",
        help="Model name to use (overrides MODEL_NAME environment variable)"
    )
    parser.add_argument(
        "--openai-base-url",
        help="OpenAI API base URL (overrides OPENAI_API_BASE environment variable)"
    )
    parser.add_argument(
        "-f", "--fetch-format",
        choices=["auto", "html", "pdf", "source"],
        default="auto",
        help="Paper format to fetch for arXiv URLs (default: auto)"
    )
    parser.add_argument(
        "--input-type",
        choices=["arxiv", "url", "md"],
        default="arxiv",
        help="Type of input (default: arxiv)"
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save extracted data as JSON file"
    )
    parser.add_argument(
        "--load-json",
        help="Load previously extracted data from JSON file"
    )
    parser.add_argument(
        "--lang",
        choices=["en", "zh"],
        default="en",
        help="Output language (default: en)"
    )
    parser.add_argument(
        "--pdf-engine",
        choices=["reportlab", "weasyprint", "playwright"],
        default="playwright",
        help="PDF generation engine (default: playwright for better fidelity and no system dependencies)"
    )
    
    args = parser.parse_args()
    
    # Generate output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = "html" if args.format == "html" else "pdf"
        # Create a folder for this paper
        paper_folder = os.path.join("output", f"paper_{timestamp}")
        args.output = os.path.join(paper_folder, f"summary.{extension}")
    else:
        # If output is provided without directory, put it in output/
        if not os.path.dirname(args.output):
            args.output = os.path.join("output", args.output)
        # Extract paper folder from output path
        paper_folder = os.path.dirname(args.output)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Track processing time
    start_time = datetime.now()
    
    try:
        if args.load_json:
            # Load existing data
            print(f"Loading extracted data from {args.load_json}...")
            with open(args.load_json, 'r', encoding='utf-8') as f:
                extracted_data = json.load(f)
        else:
            image_processor = ImageProcessor(output_dir=os.path.join(paper_folder, 'images'))
            content = ""
            image_mapping = {}
            format_used = "unknown"  # Default format
            
            if args.input_type == 'arxiv':
                print(f"Fetching paper from {args.input}...")
                fetcher = ArxivFetcher(output_dir=paper_folder)
                content, format_used, image_mapping = fetcher.fetch(args.input, args.fetch_format)
                print(f"Successfully fetched paper using {format_used} format")
                if image_mapping:
                    print(f"Downloaded {len(image_mapping)} images")
            elif args.input_type == 'url':
                print(f"Fetching content from {args.input}...")
                _, content, image_mapping = image_processor.process_html(args.input)
            elif args.input_type == 'md':
                print(f"Processing markdown file {args.input}...")
                content, image_mapping = image_processor.process_markdown(args.input)

            # Extract information using LLM
            print(f"Extracting paper information using OpenAI...")
            extractor = OpenAIExtractor(model=args.model, base_url=args.openai_base_url)
            # Pass format type and image mapping if we used arxiv
            if args.input_type == 'arxiv':
                extracted_data = extractor.extract(content, language=args.lang, format_type=format_used, image_mapping=image_mapping)
            else:
                extracted_data = extractor.extract(content, language=args.lang, image_mapping=image_mapping)
            
            if "error" in extracted_data:
                print(f"Error during extraction: {extracted_data['error']}")
                return 1
            
            # Save JSON if requested
            if args.save_json:
                json_filename = os.path.join(paper_folder, 'extracted_data.json')
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(extracted_data, f, ensure_ascii=False, indent=2)
                print(f"Saved extracted data to {json_filename}")
        
        # Generate output file
        if args.format == "html":
            print(f"Generating HTML: {args.output}...")
            # Pass image mapping if we have it
            if 'image_mapping' in locals() and image_mapping:
                generator = HTMLGenerator(output_dir=paper_folder, image_mapping=image_mapping)
            else:
                generator = HTMLGenerator(output_dir=paper_folder)
            generator.generate(extracted_data, args.output)
        else:
            print(f"Generating PDF using {args.pdf_engine}: {args.output}...")
            
            # Choose PDF generator based on engine
            if args.pdf_engine == "reportlab":
                from src.pdf_generator import PDFGenerator
                generator = PDFGenerator()
            elif args.pdf_engine == "weasyprint":
                from src.pdf_generator_weasyprint import PDFGenerator
                generator = PDFGenerator()
            else:  # playwright
                from src.pdf_generator_playwright import PDFGenerator
                generator = PDFGenerator()
            
            generator.generate(extracted_data, args.output)
            print(f"✅ Successfully generated PDF: {args.output}")
        
        # Log metadata
        
        # Initialize metadata logger
        metadata_logger = MetadataLogger()
        
        # Extract paper ID from output path
        paper_id = os.path.basename(paper_folder)
        
        # Log the paper processing
        metadata_logger.log_paper(
            paper_id=paper_id,
            title=extracted_data.get('title', 'Unknown'),
            authors=extracted_data.get('authors', []),
            arxiv_url=args.input if args.input_type == 'arxiv' else None,
            format_used=format_used if args.input_type == 'arxiv' else args.input_type,
            output_format=args.format,
            output_path=args.output,
            extracted_data=extracted_data,
            processing_time=(datetime.now() - start_time).total_seconds(),
            language=args.lang
        )
        
        # Print summary
        print("\n📄 Paper Summary:")
        print(f"Title: {extracted_data.get('title', 'N/A')}")
        authors = extracted_data.get('authors', [])
        if isinstance(authors, list):
            authors = ", ".join(authors)
        print(f"Authors: {authors}")
        
        if 'contributions' in extracted_data:
            print(f"\n🎯 Main Contributions ({len(extracted_data['contributions'])}):")
            for i, contrib in enumerate(extracted_data['contributions'][:3], 1):
                if isinstance(contrib, dict):
                    # New format with title and content
                    title = contrib.get('title', 'Contribution')
                    content = contrib.get('content', '')
                    display_text = f"{title}: {content}" if content else title
                else:
                    # Legacy format - just string
                    display_text = contrib
                print(f"  {i}. {display_text[:80]}{'...' if len(display_text) > 80 else ''}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
