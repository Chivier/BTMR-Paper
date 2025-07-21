"""
PDF generator using WeasyPrint for HTML-to-PDF conversion with perfect fidelity
"""
import os
import tempfile
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from typing import Dict, Any


class PDFGenerator:
    """Generate PDF directly from HTML for perfect consistency"""
    
    def __init__(self):
        # Configure fonts for better Unicode support
        self.font_config = FontConfiguration()
    
    def generate(self, data: Dict[str, Any], output_path: str):
        """Generate PDF from the same HTML used for web display"""
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
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        # Convert HTML to PDF with WeasyPrint
        # This ensures complete consistency between HTML and PDF output
        HTML(string=html_content).write_pdf(
            output_path,
            font_config=self.font_config
        )
        
        print(f"PDF generated successfully: {output_path}")


def generate_pdf(data: Dict[str, Any], output_path: str):
    """Convenience function to generate PDF"""
    generator = PDFGenerator()
    generator.generate(data, output_path)