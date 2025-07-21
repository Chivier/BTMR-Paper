"""
PDF generator using Playwright for perfect HTML-to-PDF conversion
Uses a real browser engine for 100% fidelity with HTML display
"""
import os
import tempfile
from typing import Dict, Any
from playwright.sync_api import sync_playwright


class PDFGenerator:
    """Generate PDF using headless browser for perfect HTML rendering"""
    
    def generate(self, data: Dict[str, Any], output_path: str):
        """Generate PDF from HTML using Playwright"""
        from .html_generator import HTMLGenerator
        
        # Create HTML generator instance
        html_gen = HTMLGenerator()
        
        # Generate HTML content using temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            html_gen.generate(data, tmp.name)
            tmp_path = tmp.name
        
        # Read the generated HTML
        with open(tmp_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Use Playwright to convert HTML to PDF
        with sync_playwright() as p:
            # Launch headless browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Use the already created temp file
            
            try:
                # Load the HTML file
                page.goto(f'file://{tmp_path}')
                
                # Wait for content to fully load
                page.wait_for_load_state('networkidle')
                
                # Generate PDF with print CSS media
                page.pdf(
                    path=output_path,
                    format='A4',
                    print_background=True,  # Include background colors
                    margin={
                        'top': '20mm',
                        'right': '20mm',
                        'bottom': '20mm',
                        'left': '20mm'
                    }
                )
                
                print(f"PDF generated successfully: {output_path}")
                
            finally:
                # Cleanup
                browser.close()
                os.unlink(tmp_path)


def generate_pdf(data: Dict[str, Any], output_path: str):
    """Convenience function to generate PDF"""
    generator = PDFGenerator()
    generator.generate(data, output_path)