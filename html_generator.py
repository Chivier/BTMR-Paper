
"""
HTML generator creating a beautiful vertical long-image layout matching the draft design
"""
import os
from typing import Dict, Any, List
from datetime import datetime
import base64
import requests

class HTMLGenerator:
    """Generate beautiful HTML from extracted paper data matching the draft design"""
    
    def __init__(self, output_dir=None, image_mapping=None):
        self.template = self._get_template()
        self.output_dir = output_dir
        self.image_folder = None
        self.image_mapping = image_mapping or {}  # Maps URLs to local paths
        self.image_counter = 0
    
    def _get_template(self) -> str:
        """Get the HTML template with embedded CSS"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Paper Summary</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #fafbfc;
            --text-color: #2c3e50;
            --title-color: #ffffff;
            --primary-color: #4c8bf5;
            --section-bg: #ffffff;
            --shadow-color: rgba(0, 0, 0, 0.04);
            --border-color: #e8ecef;

            --color-abstract: #7d7dff;
            --color-background: #ff9f43;
            --color-contribution: #1dd1a1;
            --color-method: #ff6b6b;
            --color-results: #feca57;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Noto Sans SC', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            min-height: 100vh;
            padding: 30px 20px;
            line-height: 1.6;
            font-weight: 400;
            font-size: 15px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .section {{
            background: var(--section-bg);
            border-radius: 8px;
            padding: 25px 30px;
            box-shadow: 0 2px 8px var(--shadow-color);
            border: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
        }}
        
        .section-header {{
            font-size: 1.5em;
            font-weight: 600;
            margin-bottom: 20px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: relative;
        }}

        .section-header::after {{
            content: '';
            position: absolute;
            bottom: -8px;
            left: 50%;
            transform: translateX(-50%);
            width: 50px;
            height: 3px;
            border-radius: 2px;
        }}
        
        .title-section {{
            text-align: center;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: var(--title-color);
            padding: 35px 30px;
        }}
        
        .title-section h1 {{
            font-size: 2em;
            margin-bottom: 15px;
            font-weight: 700;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            line-height: 1.3;
        }}
        
        .title-section .authors {{
            font-size: 1em;
            opacity: 0.95;
            font-weight: 400;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 8px;
        }}

        .author-tag {{
            background: rgba(255, 255, 255, 0.2);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
        }}
        
        .abstract-section .section-header {{ color: var(--color-abstract); }}
        .abstract-section .section-header::after {{ background-color: var(--color-abstract); }}
        
        .background-section .section-header {{ color: var(--color-background); }}
        .background-section .section-header::after {{ background-color: var(--color-background); }}

        .contribution-section .section-header {{ color: var(--color-contribution); }}
        .contribution-section .section-header::after {{ background-color: var(--color-contribution); }}

        .method-section .section-header {{ color: var(--color-method); }}
        .method-section .section-header::after {{ background-color: var(--color-method); }}

        .result-section .section-header {{ color: var(--color-results); }}
        .result-section .section-header::after {{ background-color: var(--color-results); }}

        .content-box {{
            background: transparent;
            padding: 0;
            margin: 15px 0;
            position: relative;
            padding-left: 25px;
            border-left: 4px solid;
        }}

        .content-box + .content-box {{
            margin-top: 20px;
            padding-top: 20px;
            position: relative;
        }}

        .content-box + .content-box::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -25px;
            right: 0;
            height: 1px;
            background: #e2e8f0;
        }}

        .abstract-content {{ border-left-color: var(--color-abstract); }}
        .chinese-summary {{ border-left-color: var(--color-abstract); }}
        .background-main {{ border-left-color: var(--color-background); }}
        .contribution-item {{ border-left-color: var(--color-contribution); }}
        .method-content {{ border-left-color: var(--color-method); }}
        .result-content {{ border-left-color: var(--color-results); }}

        .content-box h3 {{
            font-size: 1.15em;
            font-weight: 600;
            margin-bottom: 8px;
            color: #1a202c;
        }}

        .content-box p {{
            margin: 0;
            color: #4a5568;
        }}
        
        .content-box strong {{
            font-weight: 600;
            color: #2d3748;
            background-color: rgba(254, 235, 200, 0.4);
            padding: 2px 4px;
            border-radius: 3px;
        }}
        
        .background-subs {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-left: 25px;
            margin-top: 15px;
        }}
        
        .background-sub {{
            background: transparent;
            padding: 0;
            padding-left: 20px;
            border-left: 3px solid var(--color-background);
            opacity: 0.8;
        }}
        
        .background-sub h4 {{
            font-size: 1em;
            font-weight: 600;
            margin-bottom: 5px;
            color: #2d3748;
        }}

        .background-sub p {{
            margin: 0;
            font-size: 0.95em;
            color: #4a5568;
        }}
        
        .method-points ul, .result-content ul {{
            list-style: none;
            padding-left: 0;
            margin: 10px 0;
        }}

        .method-points li, .result-content li {{
            margin-bottom: 8px;
            position: relative;
            padding-left: 20px;
            font-size: 0.95em;
            color: #4a5568;
        }}

        .method-points li::before {{
            content: '•';
            position: absolute;
            left: 0;
            color: var(--color-method);
            font-weight: bold;
            font-size: 1.2em;
        }}

        .result-content li::before {{
            content: '▸';
            position: absolute;
            left: 0;
            color: var(--color-results);
        }}

        .method-points h4, .method-figures h4 {{
            font-size: 1.05em;
            font-weight: 600;
            margin-bottom: 10px;
            margin-top: 15px;
            color: #2d3748;
        }}

        .paper-figure {{
            margin: 20px 0;
            text-align: center;
        }}

        .paper-figure img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px var(--shadow-color);
            border: 1px solid var(--border-color);
        }}

        .paper-figure figcaption {{
            margin-top: 8px;
            font-style: italic;
            color: #718096;
            font-size: 0.875em;
        }}
        
        .footer {{
            text-align: center;
            color: #718096;
            margin-top: 30px;
            font-size: 0.85em;
        }}
        
        .footer a {{
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
        }}
        
        @media (max-width: 768px) {{
            body {{ padding: 20px 15px; font-size: 14px; }}
            .container {{ gap: 15px; }}
            .section {{ padding: 20px; }}
            .title-section h1 {{ font-size: 1.8em; }}
            .section-header {{ font-size: 1.3em; }}
            .background-subs {{ margin-left: 20px; }}
            .content-box {{ padding-left: 20px; }}
        }}
        
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ max-width: none; gap: 15px; }}
            .section {{ box-shadow: none; border: 1px solid #ddd; page-break-inside: avoid; margin-bottom: 15px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
        <div class="footer">
            <p>Generated on {timestamp} | <a href="https://github.com/your-repo/BTMR" target="_blank">BTMR Paper Extractor</a></p>
        </div>
    </div>
</body>
</html>'''
    
    def _create_title_section(self, data: Dict[str, Any]) -> str:
        title = data.get('title', 'Untitled Paper')
        authors = data.get('authors', [])
        if isinstance(authors, str):
            # Handle string format: "Author1, Author2, et al."
            authors = authors
        elif isinstance(authors, list):
            # Handle list format: join with commas
            authors = ', '.join(authors)
        
        # Create single author tag with all authors
        authors_html = f'<span class="author-tag">{authors}</span>' if authors else ''

        return f'''
        <div class="section title-section">
            <h1>{title}</h1>
            <div class="authors">{authors_html}</div>
        </div>'''
    
    def _create_abstract_section(self, data: Dict[str, Any]) -> str:
        abstract = data.get('abstract', '')
        if not abstract: return ''
        html = '<div class="section abstract-section"><div class="section-header">Abstract</div>'
        html += f'<div class="content-box abstract-content"><p>{abstract}</p></div>'
        html += '</div>'
        return html

    def _create_background_section(self, data: Dict[str, Any]) -> str:
        backgrounds = data.get('background', [])
        if not backgrounds: return ''
        html = '<div class="section background-section"><div class="section-header">Background</div>'
        for i, bg in enumerate(backgrounds, 1):
            # Check if there's only one subsection - if so, merge it with parent
            subsections = bg.get('subsections', [])
            if len(subsections) == 1:
                # Merge single subsection with parent
                sub = subsections[0]
                merged_content = bg.get("content", "")
                if merged_content and sub.get("content"):
                    merged_content += " " + sub.get("content", "")
                elif sub.get("content"):
                    merged_content = sub.get("content", "")
                html += f'''
                <div class="background-item">
                    <div class="content-box background-main">
                        <h3>B{i}. {bg.get("title", "Background")}</h3>
                        <p>{merged_content}</p>
                    </div>
                </div>'''
            else:
                # Multiple subsections or no subsections - keep original structure
                html += f'''
                <div class="background-item">
                    <div class="content-box background-main">
                        <h3>B{i}. {bg.get("title", "Background")}</h3>
                        <p>{bg.get("content", "")}</p>
                    </div>'''
                if subsections and len(subsections) > 1:
                    html += '<div class="background-subs">'
                    for j, sub in enumerate(subsections, 1):
                        html += f'''
                        <div class="background-sub">
                            <h4>B{i}.{j} {sub.get("title", "")}</h4>
                            <p>{sub.get("content", "")}</p>
                        </div>'''
                    html += '</div>'
                html += '</div>'
        html += '</div>'
        return html

    def _create_contribution_section(self, data: Dict[str, Any]) -> str:
        contributions = data.get('contributions', [])
        if not contributions: return ''
        html = '<div class="section contribution-section"><div class="section-header">Contributions</div>'
        for i, contrib in enumerate(contributions, 1):
            # Extract title and content if contribution is a dict
            if isinstance(contrib, dict):
                title = contrib.get('title', 'Contribution')
                content = contrib.get('content', '')
                # Convert markdown bold to HTML
                content = self._convert_markdown_bold(content)
                html += f'<div class="content-box contribution-item"><h3>C{i}. {title}</h3><p>{content}</p></div>'
            else:
                # Legacy format - just the contribution text
                content = self._convert_markdown_bold(contrib)
                html += f'<div class="content-box contribution-item"><h3>C{i}. Contribution</h3><p>{content}</p></div>'
        html += '</div>'
        return html
    
    def _convert_markdown_bold(self, text: str) -> str:
        """Convert markdown bold **text** to HTML <strong>text</strong>"""
        import re
        return re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)

    def _create_method_section(self, data: Dict[str, Any]) -> str:
        method = data.get('method', {})
        if not method: return ''
        html = '<div class="section method-section"><div class="section-header">Method</div>'
        if method.get('description'):
            html += f'<div class="content-box method-content"><p>{method["description"]}</p></div>'
        
        if method.get('key_points'):
            html += '<div class="method-points"><h4>Key Points:</h4><ul>'
            for point in method['key_points']:
                html += f'<li>{point}</li>'
            html += '</ul></div>'

        figures = method.get('figures', [])
        if figures:
            html += '<div class="method-figures"><h4>Figures & Algorithms</h4>'
            for i, fig in enumerate(figures):
                if isinstance(fig, dict) and 'url' in fig and 'caption' in fig:
                    html += self._create_figure_html(fig['url'], fig['caption'], figure_id=i+1)
                else:
                    html += f'<p>{fig}</p>'
            html += '</div>'

        html += '</div>'
        return html

    def _create_result_section(self, data: Dict[str, Any]) -> str:
        results = data.get('results', {})
        if not results: return ''
        html = '<div class="section result-section"><div class="section-header">Results</div>'
        
        if results.get('evaluation'):
            html += f'<div class="content-box result-content"><p>{results["evaluation"]}</p></div>'
        
        # Add other result details if present
        if results.get('baseline'):
            html += f'<div class="content-box result-content"><h4>Baseline Comparison</h4><p>{results["baseline"]}</p></div>'
        
        if results.get('datasets'):
            html += f'<div class="content-box result-content"><h4>Datasets</h4><p>{results["datasets"]}</p></div>'
        
        if results.get('experimental_setup'):
            html += f'<div class="content-box result-content"><h4>Experimental Setup</h4><p>{results["experimental_setup"]}</p></div>'

        # Add tables
        tables = results.get('tables', [])
        if tables:
            for i, table in enumerate(tables):
                if isinstance(table, dict) and 'url' in table and 'caption' in table:
                    html += self._create_figure_html(table['url'], table['caption'], figure_id=100+i)
        
        # Add result figures
        figures = results.get('figures', [])
        if figures:
            for i, fig in enumerate(figures):
                if isinstance(fig, dict) and 'url' in fig and 'caption' in fig:
                    html += self._create_figure_html(fig['url'], fig['caption'], figure_id=200+i)
            
        html += '</div>'
        return html

    def _create_figure_html(self, image_url: str, caption: str, figure_id: int = 0) -> str:
        """Generate HTML for an embedded image from a URL or local path."""
        import re
        import shutil
        
        try:
            # First check if this image was already downloaded during fetch
            if image_url in self.image_mapping:
                source_path = self.image_mapping[image_url]
                if os.path.exists(source_path) and self.image_folder:
                    # Copy to our output folder with proper naming
                    fig_match = re.search(r'Figure\s+(\d+)', caption, re.IGNORECASE)
                    table_match = re.search(r'Table\s+(\d+)', caption, re.IGNORECASE)
                    
                    if fig_match:
                        fig_num = fig_match.group(1)
                        ext = os.path.splitext(source_path)[1]
                        img_filename = f"figure_{fig_num}{ext}"
                    elif table_match:
                        table_num = table_match.group(1)
                        ext = os.path.splitext(source_path)[1]
                        img_filename = f"table_{table_num}{ext}"
                    else:
                        self.image_counter += 1
                        ext = os.path.splitext(source_path)[1]
                        img_filename = f"image_{self.image_counter}{ext}"
                    
                    dest_path = os.path.join(self.image_folder, img_filename)
                    if source_path != dest_path:  # Don't copy if already in right place
                        shutil.copy2(source_path, dest_path)
                    
                    img_src = f"images/{img_filename}"
                    return f'''
            <figure class="paper-figure">
                <img src="{img_src}" alt="{caption}">
                <figcaption>{caption}</figcaption>
            </figure>'''
            
            # If not in mapping, try to download (backward compatibility)
            if image_url.startswith(('http://', 'https://')):
                response = requests.get(image_url)
                response.raise_for_status()
                img_data = response.content
                
                # Save image to the images folder
                if self.image_folder:
                    # Extract figure number from caption if possible
                    fig_match = re.search(r'Figure\s+(\d+)', caption, re.IGNORECASE)
                    if fig_match:
                        fig_num = fig_match.group(1)
                        img_filename = f"figure_{fig_num}.png"
                    else:
                        img_filename = f"image_{figure_id}.png"
                    
                    img_path = os.path.join(self.image_folder, img_filename)
                    with open(img_path, 'wb') as f:
                        f.write(img_data)
                    
                    # Use relative path in HTML
                    img_src = f"images/{img_filename}"
                else:
                    # Fallback to base64 encoding
                    img_data_b64 = base64.b64encode(img_data).decode("utf-8")
                    img_src = f"data:image/png;base64,{img_data_b64}"
            else:
                # Handle local file paths (e.g., images/fig1.png)
                import os
                # Try multiple possible paths
                possible_paths = [
                    image_url,  # As-is
                    os.path.join(os.getcwd(), image_url),  # Relative to current dir
                    os.path.join(os.path.dirname(__file__), image_url),  # Relative to script
                ]
                
                file_found = False
                for path in possible_paths:
                    if os.path.exists(path):
                        if self.image_folder:
                            # Copy to images folder
                            fig_match = re.search(r'Figure\s+(\d+)', caption, re.IGNORECASE)
                            if fig_match:
                                fig_num = fig_match.group(1)
                                img_filename = f"figure_{fig_num}{os.path.splitext(path)[1]}"
                            else:
                                img_filename = f"image_{figure_id}{os.path.splitext(path)[1]}"
                            
                            img_dest = os.path.join(self.image_folder, img_filename)
                            shutil.copy2(path, img_dest)
                            img_src = f"images/{img_filename}"
                        else:
                            # Fallback to base64
                            with open(path, "rb") as f:
                                img_data = base64.b64encode(f.read()).decode("utf-8")
                                # Detect image type from extension
                                ext = os.path.splitext(path)[1].lower()
                                mime_type = {
                                    '.png': 'image/png',
                                    '.jpg': 'image/jpeg',
                                    '.jpeg': 'image/jpeg',
                                    '.gif': 'image/gif',
                                    '.svg': 'image/svg+xml'
                                }.get(ext, 'image/png')
                                img_src = f"data:{mime_type};base64,{img_data}"
                        file_found = True
                        break
                
                if not file_found:
                    print(f"Warning: Image file not found: {image_url}")
                    return f'<p><em>[Image not found: {caption}]</em></p>'
            
            return f'''
            <figure class="paper-figure">
                <img src="{img_src}" alt="{caption}">
                <figcaption>{caption}</figcaption>
            </figure>'''
        except Exception as e:
            print(f"Error processing image {image_url}: {e}")
            return f'<p><em>[Image not found: {caption}]</em></p>'

    def generate(self, data: Dict[str, Any], output_path: str):
        """Generate HTML from extracted data"""
        # Setup image folder if output directory is available
        if self.output_dir or os.path.dirname(output_path):
            paper_dir = self.output_dir or os.path.dirname(output_path)
            self.image_folder = os.path.join(paper_dir, 'images')
            os.makedirs(self.image_folder, exist_ok=True)
        
        sections = [
            self._create_title_section(data),
            self._create_abstract_section(data),
            self._create_background_section(data),
            self._create_contribution_section(data),
            self._create_method_section(data),
            self._create_result_section(data)
        ]
        content = '\n'.join(filter(None, sections))
        html = self.template.format(
            title=data.get('title', 'Paper Summary'),
            content=content,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ HTML generated: {output_path}")
        print(f"🌐 Open in browser: file://{os.path.abspath(output_path)}")
