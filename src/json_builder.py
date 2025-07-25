import json
import re
from typing import List, Dict, Any
from datetime import datetime

class JSONBuilder:
    def __init__(self):
        self.output_format = {
            "document_info": {},
            "outline": [],
            "metadata": {}
        }
    
    def build_output(self, title: str, lines: List[Dict[str, Any]], pdf_path: str) -> Dict[str, Any]:
        """
        Build the final JSON output structure in the required format
        """
        # Extract headings and create flat outline structure
        headings = self._extract_headings(lines)
        flat_outline = self._build_flat_outline(headings)
        
        return {
            "title": title.strip(),
            "outline": flat_outline
        }
    
    def _extract_headings(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract only heading lines from processed lines
        """
        headings = []
        for line in lines:
            if line["heading_level"] in ["h1", "h2", "h3"]:
                heading = {
                    "text": line["text"],
                    "level": int(line["heading_level"][1]),
                    "page": line["page_num"],
                    "confidence": line.get("confidence", 0.0),
                    "position": line["position"],
                    "font_info": {
                        "size": line["font_size"],
                        "name": line["font_name"],
                        "is_bold": line["is_bold"],
                        "is_italic": line["is_italic"]
                    }
                }
                headings.append(heading)
        return headings
    
    def _build_flat_outline(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build flat outline structure in the required format
        """
        outline = []
        
        for heading in headings:
            # Convert level number to H1, H2, H3 format
            level_str = f"H{heading['level']}"
            
            # Add trailing space to text to match expected format
            text = heading['text'].strip()
            if not text.endswith(' '):
                text += ' '
            
            outline_entry = {
                "level": level_str,
                "text": text,
                "page": heading["page"]
            }
            
            outline.append(outline_entry)
        
        return outline
    
    def _build_metadata(self, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build metadata about the extraction process
        """
        total_lines = len(lines)
        heading_counts = {"h1": 0, "h2": 0, "h3": 0, "body": 0}
        
        font_sizes = []
        for line in lines:
            heading_level = line.get("heading_level", "body")
            heading_counts[heading_level] += 1
            font_sizes.append(line["font_size"])
        
        return {
            "extraction_stats": {
                "total_text_lines": total_lines,
                "heading_distribution": heading_counts,
                "font_size_range": {
                    "min": min(font_sizes) if font_sizes else 0,
                    "max": max(font_sizes) if font_sizes else 0,
                    "avg": sum(font_sizes) / len(font_sizes) if font_sizes else 0
                }
            },
            "processing_info": {
                "extraction_method": "PyMuPDF + Rule-based Classification",
                "confidence_threshold": 0.3,
                "features_used": [
                    "font_size",
                    "font_weight",
                    "text_position",
                    "text_patterns",
                    "capitalization"
                ]
            }
        }
    
    def save_to_file(self, output_data: Dict[str, Any], output_path: str) -> None:
        """
        Save JSON output to file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        Validate the output structure for the required format
        """
        # Check top-level structure
        required_keys = ["title", "outline"]
        for key in required_keys:
            if key not in output_data:
                return False
        
        # Check title is string
        if not isinstance(output_data["title"], str):
            return False
        
        # Check outline structure
        if not isinstance(output_data["outline"], list):
            return False
        
        # Validate each outline entry
        for entry in output_data["outline"]:
            if not self._validate_outline_entry(entry):
                return False
        
        return True
    
    def _validate_outline_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Validate individual outline entry for the required format
        """
        required_keys = ["level", "text", "page"]
        
        for key in required_keys:
            if key not in entry:
                return False
        
        # Validate level format (H1, H2, H3)
        if not isinstance(entry["level"], str) or not re.match(r'^H[123]$', entry["level"]):
            return False
        
        # Validate text is string
        if not isinstance(entry["text"], str):
            return False
        
        # Validate page is integer
        if not isinstance(entry["page"], int) or entry["page"] < 1:
            return False
        
        return True
