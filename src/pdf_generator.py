"""
PDF generator with beautiful template matching the draft style - single page version
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Flowable, Frame, PageTemplate, BaseDocTemplate
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from typing import Dict, Any, List, Tuple
import os
import base64
from io import BytesIO
from PIL import Image


class RoundedBox(Flowable):
    """Custom flowable for rounded boxes"""
    
    def __init__(self, width, height, radius=10, stroke_color=HexColor('#333333'), 
                 fill_color=HexColor('#f8f9fa'), stroke_width=2):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.radius = radius
        self.stroke_color = stroke_color
        self.fill_color = fill_color
        self.stroke_width = stroke_width
        self.content = []
    
    def draw(self):
        canvas = self.canv
        canvas.setStrokeColor(self.stroke_color)
        canvas.setFillColor(self.fill_color)
        canvas.setLineWidth(self.stroke_width)
        canvas.roundRect(0, 0, self.width, self.height, self.radius, stroke=1, fill=1)


class PDFGenerator:
    """Generate beautiful PDF from extracted paper data"""
    
    def __init__(self):
        # Try to register Chinese font
        self.chinese_font = None
        try:
            # Common Chinese font paths
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
                "C:\\Windows\\Fonts\\msyh.ttc",  # Windows
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Chinese', font_path))
                    self.chinese_font = 'Chinese'
                    break
        except Exception as e:
            print(f"Warning: Could not load Chinese font: {e}")
        
        # Define colors
        self.primary_color = HexColor('#2c3e50')
        self.secondary_color = HexColor('#34495e')
        self.accent_color = HexColor('#3498db')
        self.bg_color = HexColor('#ecf0f1')
        self.box_bg_color = HexColor('#ffffff')
        
        # Create custom styles
        self.styles = self._create_styles()
    
    def _create_styles(self):
        """Create custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName=self.chinese_font or 'Helvetica-Bold'
        ))
        
        # Author style
        styles.add(ParagraphStyle(
            name='Author',
            parent=styles['Normal'],
            fontSize=14,
            textColor=self.secondary_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName=self.chinese_font or 'Helvetica'
        ))
        
        # Section header style
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=self.primary_color,
            spaceAfter=12,
            fontName=self.chinese_font or 'Helvetica-Bold'
        ))
        
        # Subsection header style
        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.secondary_color,
            spaceAfter=8,
            fontName=self.chinese_font or 'Helvetica-Bold'
        ))
        
        # Body text style
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            fontName=self.chinese_font or 'Helvetica'
        ))
        
        # Chinese text style
        styles.add(ParagraphStyle(
            name='ChineseBody',
            parent=styles['CustomBody'],
            fontName=self.chinese_font or 'Helvetica',
            fontSize=11
        ))
        
        return styles
    
    def _create_rounded_section(self, title: str, content: List, width: float) -> List:
        """Create a rounded box section with content"""
        elements = []
        
        # Section title
        elements.append(Paragraph(title, self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Create table for rounded box effect
        data = [[content]]
        table = Table(data, colWidths=[width - 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.box_bg_color),
            ('BORDER', (0, 0), (-1, -1), 2, self.primary_color),
            ('BORDERRADIUS', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 15),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_contribution_list(self, contributions: List[str]) -> List:
        """Create a formatted contribution list"""
        elements = []
        
        for i, contribution in enumerate(contributions, 1):
            # Create rounded box for each contribution
            para = Paragraph(f"<b>Contribution {i}:</b> {contribution}", 
                           self.styles['CustomBody'])
            
            data = [[para]]
            table = Table(data, colWidths=[6*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), self.bg_color),
                ('BORDER', (0, 0), (-1, -1), 1, self.accent_color),
                ('BORDERRADIUS', (0, 0), (-1, -1), 8),
                ('PADDING', (0, 0), (-1, -1), 12),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _calculate_content_height(self, data: Dict[str, Any]) -> float:
        """Calculate the total height needed for all content"""
        # Estimate based on content - this is a rough calculation
        height = 0
        
        # Title section
        height += 150  # Title + authors
        
        # Abstract
        if data.get('abstract') or data.get('chinese_summary'):
            height += 300
        
        # Background sections
        if 'background' in data and data['background']:
            for bg in data['background']:
                height += 150  # Section header
                if bg.get('content'):
                    # Estimate text height (roughly 50 chars per line, 15 points per line)
                    lines = len(bg.get('content', '')) / 50
                    height += lines * 15
                if 'subsections' in bg:
                    height += len(bg['subsections']) * 100
        
        # Contributions
        if 'contributions' in data and data['contributions']:
            height += 100 + len(data['contributions']) * 80
        
        # Method
        if 'method' in data:
            height += 300
            if 'figures' in data['method']:
                height += len(data['method']['figures']) * 50
        
        # Results
        if 'results' in data:
            height += 400
        
        # Add padding
        height += 200
        
        return max(height, A4[1])  # At least one page height
    
    def generate(self, data: Dict[str, Any], output_path: str):
        """Generate single-page PDF from extracted data"""
        # Calculate content height
        content_height = self._calculate_content_height(data)
        
        # Create custom page size (A4 width, dynamic height)
        page_width = A4[0]
        page_height = content_height
        
        # Create a canvas with custom page size
        c = canvas.Canvas(output_path, pagesize=(page_width, page_height))
        
        # Create document with custom page size
        doc = BaseDocTemplate(
            output_path,
            pagesize=(page_width, page_height),
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        
        # Create a frame that spans the entire custom page
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id='normal'
        )
        
        # Create page template
        template = PageTemplate(id='SinglePage', frames=frame)
        doc.addPageTemplates([template])
        
        story = []
        content_width = page_width - 1.5*inch
        
        # Title section
        title_content = []
        title_content.append(Paragraph(data.get('title', 'Untitled'), 
                                     self.styles['CustomTitle']))
        title_content.append(Spacer(1, 0.1*inch))
        
        # Handle authors as list
        authors = data.get('authors', ['Unknown'])
        if isinstance(authors, list):
            authors_text = ', '.join(authors)
        else:
            authors_text = str(authors)
        title_content.append(Paragraph(authors_text, self.styles['Author']))
        
        story.extend(self._create_rounded_section("", title_content, content_width))
        
        # Abstract & Chinese Summary
        abstract_content = []
        abstract_text = data.get('abstract', '')
        chinese_summary = data.get('chinese_summary', '')
        
        if abstract_text:
            abstract_content.append(Paragraph("<b>Abstract:</b>", self.styles['CustomBody']))
            abstract_content.append(Spacer(1, 0.1*inch))
            abstract_content.append(Paragraph(abstract_text, self.styles['CustomBody']))
        
        if chinese_summary:
            abstract_content.append(Spacer(1, 0.2*inch))
            abstract_content.append(Paragraph("<b>中文总结:</b>", self.styles['ChineseBody']))
            abstract_content.append(Spacer(1, 0.1*inch))
            abstract_content.append(Paragraph(chinese_summary, self.styles['ChineseBody']))
        
        if abstract_content:
            story.extend(self._create_rounded_section("Abstract & 中文总结", 
                                                    abstract_content, content_width))
        
        # Background sections
        if 'background' in data and data['background']:
            background_content = []
            
            for bg_section in data['background']:
                # Main background section
                bg_title = bg_section.get('title', 'Background')
                bg_content = bg_section.get('content', '')
                
                if bg_content:
                    background_content.append(Paragraph(f"<b>{bg_title}</b>", 
                                                      self.styles['SubsectionHeader']))
                    background_content.append(Paragraph(bg_content, 
                                                      self.styles['CustomBody']))
                    background_content.append(Spacer(1, 0.2*inch))
                
                # Subsections
                if 'subsections' in bg_section:
                    for subsection in bg_section['subsections']:
                        sub_title = subsection.get('title', '')
                        sub_content = subsection.get('content', '')
                        
                        if sub_content:
                            # Create indented subsection box
                            para = Paragraph(f"<b>{sub_title}:</b> {sub_content}", 
                                           self.styles['CustomBody'])
                            
                            data = [[para]]
                            table = Table(data, colWidths=[5.5*inch])
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, -1), self.bg_color),
                                ('BORDER', (0, 0), (-1, -1), 1, self.secondary_color),
                                ('BORDERRADIUS', (0, 0), (-1, -1), 5),
                                ('PADDING', (0, 0), (-1, -1), 10),
                                ('LEFTPADDING', (0, 0), (-1, -1), 30),
                            ]))
                            
                            background_content.append(table)
                            background_content.append(Spacer(1, 0.1*inch))
            
            if background_content:
                story.extend(self._create_rounded_section("Background", 
                                                        background_content, content_width))
        
        # Contributions
        if 'contributions' in data and data['contributions']:
            contribution_elements = self._create_contribution_list(data['contributions'])
            story.extend(self._create_rounded_section("Target/Contribution", 
                                                    contribution_elements, content_width))
        
        # Method section
        if 'method' in data:
            method_content = []
            method = data['method']
            
            if 'description' in method:
                method_content.append(Paragraph(method['description'], 
                                              self.styles['CustomBody']))
                method_content.append(Spacer(1, 0.2*inch))
            
            if 'key_points' in method and method['key_points']:
                method_content.append(Paragraph("<b>Key Points:</b>", 
                                              self.styles['CustomBody']))
                for point in method['key_points']:
                    method_content.append(Paragraph(f"• {point}", 
                                                  self.styles['CustomBody']))
                method_content.append(Spacer(1, 0.2*inch))
            
            if 'figures' in method and method['figures']:
                method_content.append(Paragraph("<b>图示/算法/Points:</b>", 
                                              self.styles['ChineseBody']))
                for fig in method['figures']:
                    method_content.append(Paragraph(f"◦ {fig}", 
                                                  self.styles['CustomBody']))
            
            if method_content:
                story.extend(self._create_rounded_section("Method", 
                                                        method_content, content_width))
        
        # Results section
        if 'results' in data:
            results_content = []
            results = data['results']
            
            # Create result tags
            tag_data = []
            if 'baseline' in results and results['baseline']:
                tag_data.append(f"baseline: {results['baseline']}")
            if 'datasets' in results and results['datasets']:
                tag_data.append(f"数据集: {results['datasets']}")
            if 'experimental_setup' in results and results['experimental_setup']:
                tag_data.append(f"实验环境配置: {results['experimental_setup']}")
            
            if tag_data:
                # Create tags table
                tag_cells = [[Paragraph(tag, self.styles['CustomBody'])] for tag in tag_data]
                tag_table = Table([tag_cells], colWidths=[2*inch]*len(tag_cells))
                tag_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), self.accent_color),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                    ('BORDER', (0, 0), (-1, -1), 1, self.accent_color),
                    ('BORDERRADIUS', (0, 0), (-1, -1), 15),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                results_content.append(tag_table)
                results_content.append(Spacer(1, 0.2*inch))
            
            if 'evaluation' in results and results['evaluation']:
                results_content.append(Paragraph("<b>Evaluation Results:</b>", 
                                               self.styles['CustomBody']))
                results_content.append(Paragraph(results['evaluation'], 
                                               self.styles['CustomBody']))
                results_content.append(Spacer(1, 0.1*inch))
            
            if 'tables' in results and results['tables']:
                results_content.append(Paragraph("<b>Result Tables:</b>", 
                                               self.styles['CustomBody']))
                for table_desc in results['tables']:
                    results_content.append(Paragraph(f"• {table_desc}", 
                                                   self.styles['CustomBody']))
            
            if results_content:
                # Add benchmark note
                results_content.append(Spacer(1, 0.2*inch))
                results_content.append(Paragraph("bento样式排版所有 results", 
                                               self.styles['ChineseBody']))
                
                story.extend(self._create_rounded_section("Results", 
                                                        results_content, content_width))
        
        # Build PDF
        doc.build(story)