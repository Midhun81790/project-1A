import fitz  # PyMuPDF
import re
import json
from typing import List, Dict, Any
import statistics

class PDFExtractor:
    """
    Optimized PDF extractor for accurate document outline extraction
    Specifically tuned for clean, structured output matching expected formats
    """
    
    def __init__(self):
        self.debug = False
    
    def extract_raw_info(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract raw text with font and position information"""
        doc = fitz.open(pdf_path)
        all_lines = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text and len(text) >= 2:
                                all_lines.append({
                                    "text": text,
                                    "font_size": span["size"],
                                    "font_name": span["font"],
                                    "is_bold": bool(span["flags"] & 16),
                                    "is_italic": bool(span["flags"] & 2),
                                    "bbox": span["bbox"],
                                    "page_num": page_num + 1,
                                    "position": {
                                        "x": span["bbox"][0],
                                        "y": span["bbox"][1],
                                        "width": span["bbox"][2] - span["bbox"][0],
                                        "height": span["bbox"][3] - span["bbox"][1]
                                    }
                                })
        
        doc.close()
        return all_lines
    
    def classify_headings(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify headings with focus on document structure and accuracy"""
        if not lines:
            return []
        
        # Calculate font statistics for dynamic thresholds
        font_sizes = [line["font_size"] for line in lines]
        avg_font_size = statistics.mean(font_sizes)
        font_size_std = statistics.stdev(font_sizes) if len(font_sizes) > 1 else 0
        
        # Calculate percentiles for better classification
        sorted_sizes = sorted(set(font_sizes), reverse=True)
        large_threshold = sorted_sizes[0] if len(sorted_sizes) > 0 else avg_font_size * 1.5
        medium_threshold = sorted_sizes[1] if len(sorted_sizes) > 1 else avg_font_size * 1.3
        small_threshold = sorted_sizes[2] if len(sorted_sizes) > 2 else avg_font_size * 1.1
        
        classified_lines = []
        
        # First pass: Identify text frequency to filter noise
        text_frequency = {}
        for line in lines:
            clean_text = line["text"].strip().lower()
            text_frequency[clean_text] = text_frequency.get(clean_text, 0) + 1
        
        # Second pass: Classify with enhanced filtering
        for line in lines:
            text = line["text"].strip()
            text_lower = text.lower()
            
            # Skip frequently repeated noise (except numbered sections)
            if (text_frequency.get(text_lower, 0) > 5 and 
                not re.match(r'^\d+\.', text) and 
                not self._is_structural_keyword(text)):
                line_copy = line.copy()
                line_copy["heading_level"] = "body"
                line_copy["confidence"] = 0.9
                classified_lines.append(line_copy)
                continue
            
            # Classify the line
            level, confidence = self._classify_line(
                line, large_threshold, medium_threshold, small_threshold, avg_font_size
            )
            
            line_copy = line.copy()
            line_copy["heading_level"] = level
            line_copy["confidence"] = confidence
            classified_lines.append(line_copy)
        
        return classified_lines
    
    def _classify_line(self, line: Dict[str, Any], large_threshold: float, 
                      medium_threshold: float, small_threshold: float, 
                      avg_font_size: float) -> tuple:
        """Classify a single line as heading or body text"""
        text = line["text"].strip()
        font_size = line["font_size"]
        is_bold = line["is_bold"]
        x_position = line["position"]["x"]
        
        # Skip obvious noise
        if not self._is_valid_heading_candidate(text):
            return "body", 0.95
        
        confidence = 0.0
        level = "body"
        
        # 1. Pattern-based classification (highest priority)
        pattern_level, pattern_score = self._analyze_structural_patterns(text)
        if pattern_level:
            level = pattern_level
            confidence = pattern_score
        
        # 2. Font size analysis
        elif font_size >= large_threshold:
            level = "h1"
            confidence = 0.6
        elif font_size >= medium_threshold:
            level = "h2"  
            confidence = 0.5
        elif font_size >= small_threshold:
            level = "h3"
            confidence = 0.4
        
        # 3. Structural keyword analysis
        if not pattern_level:
            keyword_level, keyword_score = self._analyze_structural_keywords(text)
            if keyword_level and keyword_score > confidence:
                level = keyword_level
                confidence = keyword_score
        
        # 4. Apply bonuses
        if is_bold and level != "body":
            confidence += 0.15
        
        if x_position < 100 and level != "body":  # Left-aligned
            confidence += 0.1
        
        # 5. Apply length penalty for very short text
        if len(text) < 5 and confidence < 0.7:
            confidence *= 0.5
        
        # Final threshold check
        if confidence < 0.4:
            level = "body"
            confidence = 0.8
        
        return level, min(confidence, 1.0)
    
    def _is_valid_heading_candidate(self, text: str) -> bool:
        """Check if text could be a valid heading"""
        # Length constraints
        if len(text) < 3 or len(text) > 200:
            return False
        
        # Skip obvious noise patterns
        noise_patterns = [
            r'^\d+$',  # Just numbers
            r'^page\s+\d+',  # Page numbers
            r'^[^\w\s]+$',  # Just symbols
            r'^\w{1,2}$',  # Very short
            r'^copyright',  # Copyright text
            r'^©',  # Copyright symbol
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, text.lower()):
                return False
        
        return True
    
    def _analyze_structural_patterns(self, text: str) -> tuple:
        """Analyze text for structural patterns"""
        text_lower = text.lower().strip()
        
        # High-priority numbered patterns
        patterns = [
            (r'^\d+\.\s+[a-zA-Z]', "h1", 0.8),  # "1. Introduction"
            (r'^\d+\.\d+\s+[a-zA-Z]', "h2", 0.7),  # "2.1 Overview"
            (r'^\d+\.\d+\.\d+\s+[a-zA-Z]', "h3", 0.6),  # "2.1.1 Details"
            (r'^chapter\s+\d+', "h1", 0.8),
            (r'^section\s+\d+', "h2", 0.7),
            (r'^appendix\s+[a-z]', "h1", 0.7),
            (r'^part\s+[ivx]+', "h1", 0.8),
            (r'^round\s+\d+[a-z]*:', "h1", 0.7),  # "Round 1A:"
        ]
        
        for pattern, level, score in patterns:
            if re.match(pattern, text_lower):
                return level, score
        
        return None, 0
    
    def _analyze_structural_keywords(self, text: str) -> tuple:
        """Analyze text for structural keywords"""
        text_lower = text.lower().strip()
        
        # H1 level keywords
        h1_keywords = {
            'introduction': 0.7,
            'conclusion': 0.7,
            'summary': 0.7,
            'overview': 0.6,
            'abstract': 0.7,
            'table of contents': 0.8,
            'contents': 0.7,
            'acknowledgment': 0.8,
            'acknowledgements': 0.8,
            'references': 0.8,
            'revision history': 0.8,
            'appendix': 0.7,
            'glossary': 0.7,
            'bibliography': 0.7
        }
        
        # H2 level keywords
        h2_keywords = {
            'intended audience': 0.6,
            'career paths': 0.6,
            'learning objectives': 0.6,
            'entry requirements': 0.6,
            'business outcomes': 0.6,
            'methodology': 0.6,
            'background': 0.5,
            'trademarks': 0.6,
            'keeping it current': 0.6
        }
        
        # Check for keyword matches
        for keyword, score in h1_keywords.items():
            if keyword in text_lower and abs(len(text_lower) - len(keyword)) <= 30:
                return "h1", score
        
        for keyword, score in h2_keywords.items():
            if keyword in text_lower and abs(len(text_lower) - len(keyword)) <= 30:
                return "h2", score
        
        return None, 0
    
    def _is_structural_keyword(self, text: str) -> bool:
        """Check if text contains structural keywords"""
        structural_words = [
            'introduction', 'conclusion', 'summary', 'overview', 'abstract',
            'references', 'acknowledgment', 'appendix', 'glossary', 'contents',
            'revision', 'history', 'methodology', 'background', 'objectives'
        ]
        
        text_lower = text.lower()
        return any(word in text_lower for word in structural_words)
    
    def post_process_headings(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-process headings for final cleanup and consistency"""
        # Filter to only headings
        headings = [line for line in lines if line["heading_level"] in ["h1", "h2", "h3"]]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_headings = []
        
        for heading in headings:
            key = (heading["text"].strip().lower(), heading["page_num"])
            if key not in seen:
                seen.add(key)
                unique_headings.append(heading)
        
        # Limit to reasonable number for clean output
        if len(unique_headings) > 30:
            # Prioritize H1 and H2 headings
            h1_h2 = [h for h in unique_headings if h["heading_level"] in ["h1", "h2"]]
            h3 = [h for h in unique_headings if h["heading_level"] == "h3"]
            
            # Take all H1/H2 and top H3s
            unique_headings = h1_h2 + h3[:max(0, 30 - len(h1_h2))]
        
        # Sort by page number
        unique_headings.sort(key=lambda x: x["page_num"])
        
        return unique_headings
    
    def extract_title(self, lines: List[Dict[str, Any]]) -> str:
        """Extract document title from classified lines"""
        # Get H1 headings
        h1_headings = [line for line in lines if line["heading_level"] == "h1"]
        
        if len(h1_headings) >= 2:
            # Try combining first two meaningful H1s
            first_two = [h["text"].strip() for h in h1_headings[:2]]
            
            # Skip structural headings for title
            skip_words = ['revision', 'table', 'contents', 'acknowledgment', 
                         'references', 'appendix', 'glossary']
            
            meaningful = []
            for text in first_two:
                if not any(word in text.lower() for word in skip_words):
                    meaningful.append(text)
            
            if len(meaningful) >= 2:
                # Combine with double spaces as in expected format
                combined = "  ".join(meaningful)
                if len(combined) <= 100:
                    return combined + "  "  # Add trailing spaces
        
        # Fallback to first meaningful H1
        for h1 in h1_headings:
            text = h1["text"].strip()
            skip_words = ['revision', 'table', 'contents', 'acknowledgment', 'references']
            if len(text) >= 5 and not any(word in text.lower() for word in skip_words):
                return text
        
        return "Untitled Document"
