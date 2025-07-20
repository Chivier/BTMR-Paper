"""
Paper information extractor using LLM APIs
"""
import os
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import openai
from dotenv import load_dotenv

load_dotenv()


class LLMExtractor(ABC):
    """Abstract base class for LLM extractors"""

    @abstractmethod
    def extract(self, paper_content: str) -> Dict[str, Any]:
        """Extract structured information from paper content"""
        pass


class OpenAIExtractor(LLMExtractor):
    """OpenAI API extractor"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_API_BASE")
        )
        self.model = model or os.getenv("MODEL_NAME", "gpt-4-turbo")

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

    def extract(self, paper_content: str, language: str = "en", format_type: str = "text") -> Dict[str, Any]:
        prompt = f"""Please extract the following information from this academic paper. Be comprehensive and detailed.

1. **Paper Title**: The main title of the paper.
2. **Authors**: A single string with all authors separated by commas.
3. **Abstract**: Extract the FULL paper abstract. Keep it comprehensive (200-400 words), preserving all key points, motivation, approach, and results.
4. **Background**: Extract main background topics in blog-style writing. Each topic should have:
   - A descriptive title (e.g., "The computational challenge of LLM inference")
   - Clear, engaging content written in accessible language
   - Use concrete examples and avoid overly technical jargon
   - Keep content concise but informative (100-200 words per section)
5. **Contributions**: Extract main contributions with:
   - Clear, descriptive titles
   - For each contribution, highlight key metrics and numbers using **bold** markdown
   - Example: "Achieved **15x speedup** over baseline with **99.5% accuracy**"
   - Focus on concrete achievements and quantifiable improvements
6. **Method**: Provide DETAILED methodology description including:
   - Overall approach and architecture
   - Key algorithms and techniques
   - Implementation details
   - System design choices
   - IMPORTANT: Find and include ALL figures showing the approach, architecture, algorithms, or method diagrams
7. **Results**: Comprehensive results including:
   - Detailed evaluation metrics
   - Comparisons with baselines
   - Performance analysis
   - IMPORTANT: Find and include ALL tables, charts, and result figures

{"The paper content is in HTML format. Extract images by looking for <img> tags." if format_type == "html" else ""}

Paper content:
{paper_content[:15000]}

Return the information in this JSON format:
{{
    "title": "Paper title",
    "authors": "Author1, Author2, Author3",
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
        "description": "Overall methodology description...",
        "key_points": [
            "Key methodological point 1",
            "Key methodological point 2"
        ],
        "figures": [
            {{
                "url": "ACTUAL image URL from the paper",
                "caption": "Figure X: Description of what the figure shows"
            }}
        ]
    }},
    "results": {{
        "evaluation": "Summary of evaluation results...",
        "baseline": "Baseline comparison details...",
        "datasets": "Datasets used...",
        "experimental_setup": "Experimental setup details...",
        "tables": [
            {{
                "url": "ACTUAL image URL of table",
                "caption": "Table X: Description of the table contents"
            }}
        ],
        "figures": [
            {{
                "url": "ACTUAL image URL of result figure",
                "caption": "Figure X: Result visualization or chart"
            }}
        ]
    }}
}}

IMPORTANT: 
- For figures and tables, extract the ACTUAL URLs from <img> tags in the HTML. Do not use placeholder URLs.
- Include ALL relevant figures in Method section (architecture diagrams, flowcharts, algorithms)
- Include ALL tables and result figures in Results section
- Each background and contribution should have a descriptive title, not just "Background 1" or "Contribution 1"
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        try:
            extracted_data = json.loads(response.choices[0].message.content)

            # Don't summarize abstract anymore - keep it longer
            # if "abstract" in extracted_data:
            #     extracted_data["abstract"] = self._summarize_text(extracted_data["abstract"])
            
            # Keep background content more detailed, only summarize if very long
            if "background" in extracted_data:
                for item in extracted_data["background"]:
                    if "content" in item and len(item["content"]) > 300:
                        item["content"] = self._summarize_text(item["content"], max_length=250)
                    if "subsections" in item:
                        for sub_item in item["subsections"]:
                            if "content" in sub_item and len(sub_item["content"]) > 300:
                                sub_item["content"] = self._summarize_text(sub_item["content"], max_length=250)
            
            # Translate to Chinese if requested
            if language == "zh":
                extracted_data = self._translate_to_chinese(extracted_data)
            
            return extracted_data
        except Exception as e:
            print(f"Error parsing response: {e}")
            return {{"error": str(e), "raw_response": response.choices[0].message.content}}
    
    def _translate_to_chinese(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Translate extracted data to Chinese using TRANSLATE_MODEL"""
        translate_model = os.getenv("TRANSLATE_MODEL", self.model)
        
        # Prepare content for translation
        content_to_translate = {
            "title": data.get("title", ""),
            "abstract": data.get("abstract", ""),
            "background": [],
            "contributions": [],
            "method_description": data.get("method", {}).get("description", ""),
            "method_key_points": data.get("method", {}).get("key_points", []),
            "results_evaluation": data.get("results", {}).get("evaluation", "")
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
        
        # Create translation prompt
        translate_prompt = f"""Please translate the following academic paper content from English to Chinese. 
Maintain the structure and keep technical terms accurate. Return the translation in the same JSON format.

Content to translate:
{json.dumps(content_to_translate, ensure_ascii=False, indent=2)}

Return the Chinese translation in this exact format, maintaining all structure."""
        
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
            if "method" in data and "method_description" in translated:
                data["method"]["description"] = translated.get("method_description", data["method"].get("description", ""))
                if "method_key_points" in translated:
                    data["method"]["key_points"] = translated.get("method_key_points", data["method"].get("key_points", []))
            
            # Update results
            if "results" in data and "results_evaluation" in translated:
                data["results"]["evaluation"] = translated.get("results_evaluation", data["results"].get("evaluation", ""))
            
        except Exception as e:
            print(f"Translation error: {e}. Keeping original English content.")
        
        return data
