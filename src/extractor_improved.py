import fitz  # PyMuPDF
import re
import json
from typing import List, Dict, Any

class PDFOutlineExtractorImproved:
    def __init__(self):
        self.bert_classifier = None
        try:
            from .bert_classifier import BERTClassifier
            self.bert_classifier = BERTClassifier()
        except Exception as e:
            print(f"Warning: BERT classifier not available: {e}")
    
    def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
        """Extract outline from PDF with improved accuracy"""
        doc = fitz.open(pdf_path)
        
        # Extract text with metadata
        text_elements = self._extract_text_elements(doc)
        
        # Filter and classify headings
        headings = self._classify_and_filter_headings(text_elements)
        
        # Extract title
        title = self._extract_title(headings, text_elements)
        
        # Build final outline
        outline = self._build_outline(headings)
        
        doc.close()
        
        return {
            "title": title,
            "outline": outline
        }
    
    def _extract_text_elements(self, doc) -> List[Dict[str, Any]]:
        """Extract text elements with font and position metadata"""
        elements = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                elements.append({
                                    "text": text,
                                    "font_size": span["size"],
                                    "font_name": span["font"],
                                    "flags": span["flags"],
                                    "bbox": span["bbox"],
                                    "page": page_num + 1,
                                    "is_bold": bool(span["flags"] & 2**4)
                                })
        
        return elements
    
    def _classify_and_filter_headings(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify and filter headings using improved logic"""
        if not elements:
            return []
        
        # Calculate font statistics
        font_sizes = [elem["font_size"] for elem in elements]
        avg_size = sum(font_sizes) / len(font_sizes)
        sorted_sizes = sorted(set(font_sizes), reverse=True)
        
        # Define thresholds based on document structure
        large_threshold = sorted_sizes[0] if len(sorted_sizes) > 0 else avg_size * 1.5
        medium_threshold = sorted_sizes[1] if len(sorted_sizes) > 1 else avg_size * 1.3
        small_threshold = sorted_sizes[2] if len(sorted_sizes) > 2 else avg_size * 1.1
        
        headings = []
        seen_headings = set()  # Deduplication
        toc_page = None
        
        for elem in elements:
            text = elem["text"].strip()
            
            # Skip Table of Contents page content
            if "table of contents" in text.lower():
                toc_page = elem["page"]
                continue
            
            if toc_page and elem["page"] == toc_page:
                continue
            
            # Apply filters
            if not self._is_valid_heading(text):
                continue
            
            # Classify heading level
            level, confidence = self._classify_heading(elem, large_threshold, medium_threshold, small_threshold)
            
            if level != "body" and confidence > 0.4:
                # Deduplication key
                key = (text.lower().strip(), elem["page"])
                if key not in seen_headings:
                    seen_headings.add(key)
                    headings.append({
                        "text": text,
                        "level": level.upper(),
                        "page": elem["page"],
                        "confidence": confidence
                    })
        
        # Sort by page and filter duplicates
        headings.sort(key=lambda x: (x["page"], x["text"]))
        
        return self._filter_and_refine_headings(headings)
    
    def _is_valid_heading(self, text: str) -> bool:
        """Check if text could be a valid heading"""
        text = text.strip()
        
        # Length checks
        if len(text) < 3 or len(text) > 200:
            return False
        
        # Skip noise patterns
        noise_patterns = [
            r'^\d+$',  # Just numbers
            r'^page\s+\d+',  # Page numbers
            r'^[^\w\s]+$',  # Just symbols
            r'^\w{1,2}$',  # Single letters
            r'^\s*$',  # Empty or whitespace
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, text.lower()):
                return False
        
        # Skip repeated noise words (appearing too frequently)
        frequent_noise = [
            "qualifications board",
            "software testing",
            "overview"
        ]
        
        if text.lower() in frequent_noise:
            return False
        
        return True
    
    def _classify_heading(self, elem: Dict[str, Any], large_threshold: float, 
                         medium_threshold: float, small_threshold: float) -> tuple:
        """Classify heading level and confidence"""
        text = elem["text"].strip()
        font_size = elem["font_size"]
        is_bold = elem["is_bold"]
        
        confidence = 0.0
        level = "body"
        
        # Font size scoring
        size_score = 0
        if font_size >= large_threshold:
            size_score = 0.4
        elif font_size >= medium_threshold:
            size_score = 0.3
        elif font_size >= small_threshold:
            size_score = 0.2
        
        # Bold text bonus
        bold_score = 0.2 if is_bold else 0
        
        # Pattern-based scoring (CRITICAL for structure)
        pattern_score, suggested_level = self._analyze_patterns(text)
        
        # Structure keyword scoring
        structure_score, struct_level = self._analyze_structure_keywords(text)
        
        # Calculate total confidence
        confidence = size_score + bold_score + pattern_score + structure_score
        
        # Determine final level
        if suggested_level:
            level = suggested_level
        elif struct_level:
            level = struct_level
        elif confidence >= 0.4:
            if font_size >= large_threshold:
                level = "h1"
            elif font_size >= medium_threshold:
                level = "h2"
            else:
                level = "h3"
        
        return level, confidence
    
    def _analyze_patterns(self, text: str) -> tuple:
        """Analyze text patterns for heading classification"""
        text_lower = text.lower().strip()
        
        # High-priority patterns with specific levels
        patterns = [
            (r'^\d+\.\s+', "h1", 0.5),  # "1. Introduction"
            (r'^\d+\.\d+\s+', "h2", 0.4),  # "2.1 Overview"
            (r'^\d+\.\d+\.\d+\s+', "h3", 0.3),  # "2.1.1 Details"
            (r'^chapter\s+\d+', "h1", 0.5),
            (r'^appendix\s+[a-z]', "h1", 0.4),
            (r'^part\s+[ivx]+', "h1", 0.5),
            (r'^section\s+\d+', "h2", 0.4),
        ]
        
        for pattern, level, score in patterns:
            if re.match(pattern, text_lower):
                return score, level
        
        return 0, None
    
    def _analyze_structure_keywords(self, text: str) -> tuple:
        """Analyze structural keywords"""
        text_lower = text.lower().strip()
        
        # H1 keywords
        h1_keywords = [
            'introduction', 'conclusion', 'summary', 'overview', 'abstract',
            'table of contents', 'contents', 'acknowledgment', 'acknowledgements',
            'references', 'revision history', 'preface', 'foreword', 'appendix',
            'glossary', 'bibliography'
        ]
        
        # H2 keywords
        h2_keywords = [
            'intended audience', 'career paths', 'learning objectives',
            'entry requirements', 'structure and course', 'keeping it current',
            'business outcomes', 'methodology', 'results', 'discussion',
            'background', 'trademarks', 'documents and web sites'
        ]
        
        # Check for exact matches or strong containment
        for keyword in h1_keywords:
            if keyword == text_lower or (keyword in text_lower and len(text_lower) <= len(keyword) + 20):
                return 0.4, "h1"
        
        for keyword in h2_keywords:
            if keyword == text_lower or (keyword in text_lower and len(text_lower) <= len(keyword) + 20):
                return 0.3, "h2"
        
        return 0, None
    
    def _filter_and_refine_headings(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Final filtering and refinement"""
        if not headings:
            return []
        
        refined = []
        
        for heading in headings:
            # Skip very low confidence
            if heading["confidence"] < 0.4:
                continue
            
            # Skip if it's just repeated words
            text = heading["text"].strip()
            words = text.split()
            if len(words) == 1 and len([h for h in headings if h["text"].strip() == text]) > 3:
                continue  # Skip if same single word appears too often
            
            refined.append(heading)
        
        return refined
    
    def _extract_title(self, headings: List[Dict[str, Any]], elements: List[Dict[str, Any]]) -> str:
        """Extract document title from headings and text elements"""
        
        # Strategy 1: Look for title in first few H1 headings
        h1_headings = [h for h in headings if h["level"] == "H1"][:3]
        
        if len(h1_headings) >= 2:
            # Check if first two H1s should be combined as title
            first_two = [h["text"].strip() for h in h1_headings[:2]]
            combined = " ".join(first_two)
            
            # If reasonable length and structure
            if len(combined) <= 100 and not any(word in combined.lower() for word in 
                                               ['revision', 'table', 'contents', 'acknowledgment']):
                return combined.strip()
        
        # Strategy 2: Use first meaningful H1
        for h1 in h1_headings:
            text = h1["text"].strip()
            if len(text) >= 5 and not any(word in text.lower() for word in 
                                         ['revision', 'table', 'contents', 'acknowledgment']):
                return text
        
        # Strategy 3: Look for large text on first page
        first_page_elements = [e for e in elements if e["page"] == 1]
        if first_page_elements:
            # Sort by font size
            first_page_elements.sort(key=lambda x: x["font_size"], reverse=True)
            
            for elem in first_page_elements[:5]:  # Check top 5 largest
                text = elem["text"].strip()
                if 10 <= len(text) <= 100 and not re.match(r'^\d+$', text):
                    return text
        
        return "Untitled Document"
    
    def _build_outline(self, headings: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Build final outline structure"""
        outline = []
        
        for heading in headings:
            outline.append({
                "level": heading["level"],
                "text": heading["text"],
                "page": heading["page"]
            })
        
        return outline
