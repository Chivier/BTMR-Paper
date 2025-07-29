"""
Paper Information Extractor using LLM APIs

This module handles the extraction of structured information from academic papers
using Large Language Models (LLMs). It supports:
- Intelligent prompt engineering for accurate extraction
- Smart figure/table classification based on captions
- Multi-language support (English and Chinese)
- Context-aware image placement recommendations

The extractor uses carefully crafted prompts to ensure high-quality output with
proper formatting and intelligent content organization.
"""
import os
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import openai
from dotenv import load_dotenv

load_dotenv()


class LLMExtractor(ABC):
    """
    Abstract base class for LLM-based extractors.
    
    Provides a common interface for different LLM providers.
    """

    @abstractmethod
    def extract(self, paper_content: str) -> Dict[str, Any]:
        """
        Extract structured information from paper content.
        
        Args:
            paper_content: Raw paper text content
            
        Returns:
            Structured dictionary with extracted information
        """
        pass


class OpenAIExtractor(LLMExtractor):
    """
    OpenAI-compatible API extractor for paper information.
    
    This class works with any OpenAI-compatible endpoint including:
    - OpenAI API
    - Azure OpenAI
    - Local models (Ollama, LM Studio, vLLM)
    - Other providers (OpenRouter, Together AI)
    
    The extractor implements sophisticated prompt engineering to:
    - Extract key paper components (title, authors, abstract, etc.)
    - Classify figures into method vs. results sections
    - Generate concise summaries with highlighted metrics
    - Support multi-language output
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the OpenAI extractor.
        
        Args:
            api_key: Optional API key (defaults to OPENAI_API_KEY env var)
            model: Optional model name (defaults to MODEL_NAME env var or "gpt-4-turbo")
            base_url: Optional API base URL (defaults to OPENAI_API_BASE env var)
        """
        # Get API key with proper fallback
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        # Get base URL with proper fallback  
        base_url = base_url or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model or os.getenv("MODEL_NAME", "gpt-4-turbo")
        print(f"Initialized OpenAI extractor with model: {self.model}, base_url: {base_url}")

    def _summarize_text(self, text: str, max_length: int = 150) -> str:
        """Summarize a given text using the OpenAI API."""
        if not text or len(text) <= max_length:
            return text
        
        try:
            prompt = f"""Please summarize the following text concisely to about {max_length} characters:

{text}"""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100,
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            print(f"Error during summarization: {e}")
            return text # Fallback to original text

    def extract(self, paper_content: str, language: str = "en", format_type: str = "text", image_mapping: Dict[str, dict] = None) -> Dict[str, Any]:
        prompt = f"""Please extract the following information from this academic paper. Be comprehensive and detailed.

1. **Paper Title**: The main title of the paper.
2. **Authors**: List of authors as an array of strings, one per author.
3. **Abstract**: Extract a CONCISE summary of the paper (100-150 words). Focus on the core problem, approach, and key results. Use **bold** markdown to highlight important metrics and achievements. When appropriate, reference key figures showing results (e.g., "achieving **10× speedup** (see Figure 9)").
4. **Background**: Extract main background topics with:
   - Blog-style writing with descriptive titles
   - Use **bold** markdown to highlight key concepts, challenges, and important facts
   - Keep content concise (100-150 words per section)
   - Remove any "(details not specified)" or similar placeholder text
5. **Contributions**: Extract main contributions with:
   - Clear, descriptive titles
   - Highlight ALL key metrics, numbers, and achievements using **bold** markdown
   - Focus on concrete improvements and quantifiable results
   - When appropriate, reference figures that illustrate the contribution
6. **Method**: DETAILED methodology explanation suitable for LLM field beginners with EXCELLENT FORMATTING:
   - **IMPORTANT: Assume the reader is new to this specific approach - explain everything clearly**
   - **FORMATTING REQUIREMENTS**:
     * Use SHORT PARAGRAPHS (2-3 sentences max) separated by blank lines
     * Use numbered lists (1., 2., 3.) for sequential steps
     * Use bullet points (•) for parallel concepts
     * **Bold** all technical terms on first use, key insights, and important numbers
     * Start each major concept with a new paragraph
   - For EACH algorithm, technique, or design choice, organize as follows:
     
     **[Technique Name]**
     
     **Why needed:** Brief explanation of the problem or limitation being addressed.
     
     **Core idea:** Intuitive explanation using analogies or simple language.
     
     **How it works:**
     1. **Step 1:** Clear description with any necessary context
     2. **Step 2:** Next step with examples if helpful
     3. **Step 3:** Continue numbering for all steps
     
     **Key insight:** The clever idea that makes this work.
     
     **Technical details:** Deeper dive for those who want specifics.
     
   - **Define terms inline**: "We use **LoRA** (Low-Rank Adaptation) - a technique that adds small trainable matrices to frozen model weights"
   - **Use transition phrases** between paragraphs: "Building on this...", "To address this limitation...", "This leads to..."
   - Break complex methods into clearly labeled subsections
   - Include ONLY figures that show HOW the system works
   - Make it scannable - readers should grasp key points from bold text alone
7. **Results**: Comprehensive results with:
   - Use **bold** to highlight ALL performance numbers, improvements, and comparisons
   - Organize by evaluation aspects (e.g., "Performance Comparison", "Scalability Analysis", "Energy Efficiency")
   - Include ONLY figures that show evaluation results:
     * Performance comparisons (with "vs", "comparison")
     * Benchmark results, speedup graphs
     * Experimental evaluations
   - Properly distinguish between figures and tables
   - Remove any placeholder text like "(details not specified in the provided content)"

{"IMPORTANT: The paper content is in HTML format. Look for <img> tags and extract the 'src' attribute value EXACTLY as it appears. These will be local file paths. Extract the EXACT path from src attribute, do NOT modify or create placeholder URLs." if format_type == "html" else ""}

{f'''
IMAGE CAPTION INFORMATION:
The following images are available in the paper with their captions:
{json.dumps(image_mapping, indent=2) if image_mapping else "No caption information available"}

CRITICAL RULES FOR IMAGE USAGE:

1. **DO NOT USE ALL IMAGES** - Only reference images that naturally fit the content you're describing

2. **DISTINGUISH FIGURES FROM TABLES**:
   - ONLY include in results.tables if the caption explicitly starts with "Table X:"
   - ALL images with "Figure X:" are FIGURES (not tables)
   - If there are no actual table images, leave results.tables as empty array []
   - NEVER convert a Figure into a Table just because the paper text mentions a table
   - NEVER put the same image in both figures and tables

3. **METHOD FIGURES** (method.subsections[].figures):
   - Architecture, system design, framework diagrams
   - Algorithm flowcharts, workflow diagrams
   - Implementation details, component organization
   - Design intuitions, parallelism plans
   - Keywords: "architecture", "design", "plan", "framework", "algorithm", "workflow"
   - EXCLUDE: anything with "vs", "comparison", "performance", "speedup"

4. **RESULTS FIGURES** (results.subsections[].figures):
   - Performance comparisons ("X vs Y")
   - Benchmark results, speedup graphs
   - Experimental evaluations, measurements
   - Keywords: "vs", "comparison", "performance", "speedup", "benchmark", "evaluation"
   - EXCLUDE: design diagrams, architecture, workflow

5. **SMART PLACEMENT**:
   - In abstract: reference key results with "(see Figure X)" when mentioning performance
   - In contributions: reference figures that illustrate the contribution
   - Place figures contextually - don't force all images to be used
   - Each image should appear EXACTLY ONCE

6. **For "scalability analysis" or ambiguous cases**:
   - If it shows HOW to achieve scalability → method
   - If it shows MEASURED scalability results → results
''' if image_mapping else ''}

Paper content:
{paper_content[:50000]}

Return the information in this JSON format:
{{
    "title": "Paper title",
    "authors": ["Author1 Name", "Author2 Name", "Author3 Name"],
    "abstract": "Full abstract text...",
    "background": [
        {{
            "title": "Background 1: Brief descriptive title (under 10 words)",
            "content": "Detailed content...",
            "subsections": [
                {{"title": "Subsection title", "content": "Subsection content..."}}
            ]
        }}
    ],
    "contributions": [
        {{
            "title": "Brief contribution title (under 10 words)",
            "content": "Detailed description of this contribution..."
        }}
    ],
    "method": {{
        "description": "Overall methodology description explaining the high-level approach and key innovations...",
        "subsections": [
            {{
                "title": "System Architecture",
                "content": "**Overview**\n\nOur system consists of **three main components**: the encoder, processor, and decoder. Each plays a crucial role in transforming input into meaningful output.\n\n**Why this design:** Traditional approaches suffer from bottlenecks when scaling. Our architecture addresses this through parallel processing.\n\n**Component Details:**\n\n• **Encoder**: Converts raw input into embeddings using a **transformer-based architecture**\n• **Processor**: Applies our novel **attention mechanism** to focus on relevant features\n• **Decoder**: Generates output using learned representations\n\n**Key insight:** By separating encoding and processing, we achieve **10x faster inference** while maintaining accuracy.\n\n**Technical implementation:** The encoder uses 12 layers with hidden dimension of 768...",
                "figures": [
                    {{
                        "url": "ACTUAL image URL",
                        "caption": "Figure X: Architecture diagram"
                    }}
                ]
            }},
            {{
                "title": "Algorithm Design",
                "content": "**Adaptive Attention Algorithm**\n\n**Problem addressed:** Standard attention has O(n²) complexity, limiting sequence length.\n\n**Core idea:** Like a spotlight that dynamically adjusts its focus area - wider for context, narrower for details.\n\n**How it works:**\n1. **Compute query vectors** from input embeddings using learned projection\n2. **Calculate attention scores** using our adaptive threshold mechanism\n3. **Apply sparsity mask** to keep only top-k relevant connections\n4. **Normalize and aggregate** values for final output\n\n**Example:** For a 1000-token sequence, we reduce connections from 1M to just 10K.\n\n**Key insight:** Most tokens only need to attend to **local context** plus a few **global anchors**.\n\n**Complexity:** O(n·k) where k << n, typically k ≈ √n",
                "figures": []
            }}
        ],
        "key_points": [
            "Key innovation explained in simple terms",
            "Key methodological point 2"
        ]
    }},
    "results": {{
        "subsections": [
            {{
                "title": "Performance Comparison",
                "content": "Performance comparison results...",
                "figures": [
                    {{
                        "url": "ACTUAL image URL",
                        "caption": "Figure X: Performance comparison"
                    }}
                ]
            }},
            {{
                "title": "Scalability Analysis", 
                "content": "Scalability analysis results...",
                "figures": []
            }}
        ],
        "baseline": "Baseline comparison details...",
        "datasets": "Datasets used...",
        "experimental_setup": "Experimental setup details...",
        "tables": []  // CRITICAL: Only include images where caption_tag="Table X:", leave empty if no tables
    }}
}}

IMPORTANT FOR IMAGE EXTRACTION AND CLASSIFICATION:
1. **Check the image metadata provided above**:
   - Each image has a "caption_tag" field (e.g., "Figure 1:", "Table 1:")
   - ONLY include an image in results.tables if its caption_tag is "Table X:"
   - ALL images with "Figure X:" caption_tag are FIGURES, NOT tables
   
2. **Classify FIGURES based on their caption content**:
   - **Method figures**: Architecture, design, algorithm, workflow, framework
   - **Result figures**: Performance comparison (vs), speedup, benchmark results
   
3. **DO NOT CREATE TABLES**:
   - If no images have "Table X:" in caption_tag, leave results.tables empty []
   - NEVER convert a Figure into a Table
   - The paper text may mention tables that don't exist as images
   
4. **Avoid duplication**:
   - Each image should appear ONLY ONCE
   - Check the actual image path/URL to ensure no duplicates
"""
        
        # Debug: Print content length
        print(f"Sending {len(paper_content)} characters to LLM...")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        try:
            # Debug response
            if not response.choices[0].message.content:
                print("Warning: LLM returned empty response")
                print(f"Model used: {self.model}")
                return {"error": "Empty response from LLM"}
                
            extracted_data = json.loads(response.choices[0].message.content)

            # Don't summarize abstract anymore - keep it longer
            # if "abstract" in extracted_data:
            #     extracted_data["abstract"] = self._summarize_text(extracted_data["abstract"])
            
            # Don't summarize background content anymore - keep it detailed with highlights
            # if "background" in extracted_data:
            #     for item in extracted_data["background"]:
            #         if "content" in item and len(item["content"]) > 300:
            #             item["content"] = self._summarize_text(item["content"], max_length=250)
            #         if "subsections" in item:
            #             for sub_item in item["subsections"]:
            #                 if "content" in sub_item and len(sub_item["content"]) > 300:
            #                     sub_item["content"] = self._summarize_text(sub_item["content"], max_length=250)
            
            # Translate to Chinese if requested
            if language == "zh":
                extracted_data = self._translate_to_chinese(extracted_data)
            
            return extracted_data
        except Exception as e:
            print(f"Error parsing response: {e}")
            return {"error": str(e), "raw_response": response.choices[0].message.content}
    
    def _translate_to_chinese(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Translate extracted data to Chinese using TRANSLATE_MODEL"""
        translate_model = os.getenv("TRANSLATE_MODEL", self.model)
        
        # Prepare content for translation - include ALL fields
        content_to_translate = {
            "title": data.get("title", ""),
            "abstract": data.get("abstract", ""),
            "background": [],
            "contributions": [],
            "method": {
                "description": data.get("method", {}).get("description", ""),
                "subsections": [],
                "key_points": data.get("method", {}).get("key_points", [])
            },
            "results": {
                "subsections": [],
                "baseline": data.get("results", {}).get("baseline", ""),
                "datasets": data.get("results", {}).get("datasets", ""),
                "experimental_setup": data.get("results", {}).get("experimental_setup", ""),
                "evaluation": data.get("results", {}).get("evaluation", "")
            }
        }
        
        # Extract background content
        for bg in data.get("background", []):
            bg_item = {
                "title": bg.get("title", ""),
                "content": bg.get("content", ""),
                "subsections": []
            }
            for sub in bg.get("subsections", []):
                bg_item["subsections"].append({
                    "title": sub.get("title", ""),
                    "content": sub.get("content", "")
                })
            content_to_translate["background"].append(bg_item)
        
        # Extract contributions
        for contrib in data.get("contributions", []):
            if isinstance(contrib, dict):
                content_to_translate["contributions"].append({
                    "title": contrib.get("title", ""),
                    "content": contrib.get("content", "")
                })
            else:
                content_to_translate["contributions"].append(contrib)
        
        # Extract method subsections
        for subsec in data.get("method", {}).get("subsections", []):
            content_to_translate["method"]["subsections"].append({
                "title": subsec.get("title", ""),
                "content": subsec.get("content", "")
            })
        
        # Extract results subsections
        for subsec in data.get("results", {}).get("subsections", []):
            content_to_translate["results"]["subsections"].append({
                "title": subsec.get("title", ""),
                "content": subsec.get("content", "")
            })
        
        # Create translation prompt
        translate_prompt = f"""Please translate the following academic paper content from English to Chinese. 
IMPORTANT REQUIREMENTS:
1. Maintain the JSON structure and formatting (including **bold** markdown)
2. For technical terms, keep the English term followed by Chinese translation in parentheses
3. For the METHOD section specifically:
   - Keep the detailed, beginner-friendly explanations
   - Maintain all step-by-step walkthroughs and examples
   - Preserve the educational tone that explains WHY, WHAT, and HOW
   - Keep analogies and intuitive explanations
   - Ensure technical term definitions remain clear
4. Make the Chinese translation equally accessible to LLM field beginners

Content to translate (in JSON format):
{json.dumps(content_to_translate, ensure_ascii=False, indent=2)}

Return the Chinese translation in the same JSON format, maintaining all structure and educational value."""
        
        try:
            response = self.client.chat.completions.create(
                model=translate_model,
                messages=[{"role": "user", "content": translate_prompt}],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            translated = json.loads(response.choices[0].message.content)
            
            # Apply translations back to original data
            data["title"] = translated.get("title", data.get("title", ""))
            data["abstract"] = translated.get("abstract", data.get("abstract", ""))
            
            # Update background
            for i, bg in enumerate(data.get("background", [])):
                if i < len(translated.get("background", [])):
                    trans_bg = translated["background"][i]
                    bg["title"] = trans_bg.get("title", bg.get("title", ""))
                    bg["content"] = trans_bg.get("content", bg.get("content", ""))
                    for j, sub in enumerate(bg.get("subsections", [])):
                        if j < len(trans_bg.get("subsections", [])):
                            trans_sub = trans_bg["subsections"][j]
                            sub["title"] = trans_sub.get("title", sub.get("title", ""))
                            sub["content"] = trans_sub.get("content", sub.get("content", ""))
            
            # Update contributions
            for i, contrib in enumerate(data.get("contributions", [])):
                if i < len(translated.get("contributions", [])):
                    trans_contrib = translated["contributions"][i]
                    if isinstance(contrib, dict) and isinstance(trans_contrib, dict):
                        contrib["title"] = trans_contrib.get("title", contrib.get("title", ""))
                        contrib["content"] = trans_contrib.get("content", contrib.get("content", ""))
                    elif isinstance(trans_contrib, str):
                        data["contributions"][i] = trans_contrib
            
            # Update method
            if "method" in data and "method" in translated:
                trans_method = translated["method"]
                data["method"]["description"] = trans_method.get("description", data["method"].get("description", ""))
                data["method"]["key_points"] = trans_method.get("key_points", data["method"].get("key_points", []))
                
                # Update method subsections
                for i, subsec in enumerate(data["method"].get("subsections", [])):
                    if i < len(trans_method.get("subsections", [])):
                        trans_subsec = trans_method["subsections"][i]
                        subsec["title"] = trans_subsec.get("title", subsec.get("title", ""))
                        subsec["content"] = trans_subsec.get("content", subsec.get("content", ""))
            
            # Update results  
            if "results" in data and "results" in translated:
                trans_results = translated["results"]
                data["results"]["baseline"] = trans_results.get("baseline", data["results"].get("baseline", ""))
                data["results"]["datasets"] = trans_results.get("datasets", data["results"].get("datasets", ""))
                data["results"]["experimental_setup"] = trans_results.get("experimental_setup", data["results"].get("experimental_setup", ""))
                data["results"]["evaluation"] = trans_results.get("evaluation", data["results"].get("evaluation", ""))
                
                # Update results subsections
                for i, subsec in enumerate(data["results"].get("subsections", [])):
                    if i < len(trans_results.get("subsections", [])):
                        trans_subsec = trans_results["subsections"][i]
                        subsec["title"] = trans_subsec.get("title", subsec.get("title", ""))
                        subsec["content"] = trans_subsec.get("content", subsec.get("content", ""))
            
        except Exception as e:
            print(f"Translation error: {e}. Keeping original English content.")
        
        return data
