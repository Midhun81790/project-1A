import os
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from typing import List, Dict, Any
import re

class BERTHeadingClassifier:
    """
    Optional BERT-based heading classifier using MiniLM
    Only use if better accuracy is needed and model size constraint allows
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.is_loaded = False
        
        # Pre-computed heading patterns for quick classification
        self.heading_keywords = [
            'introduction', 'background', 'methodology', 'results', 
            'conclusion', 'abstract', 'summary', 'overview', 'chapter',
            'section', 'subsection', 'appendix', 'references', 'bibliography'
        ]
    
    def load_model(self) -> bool:
        """
        Load the BERT model for heading classification
        Returns True if successful, False otherwise
        """
        try:
            # Only load if not already loaded
            if self.is_loaded:
                return True
            
            print(f"Loading BERT model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            self.is_loaded = True
            print("BERT model loaded successfully")
            return True
            
        except Exception as e:
            print(f"Error loading BERT model: {e}")
            print("Falling back to rule-based classification")
            return False
    
    def is_heading(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Determine if text is a heading using BERT + heuristics
        Returns dict with prediction and confidence
        """
        if not text or len(text.strip()) == 0:
            return {"is_heading": False, "confidence": 0.0, "level": "body"}
        
        text = text.strip()
        
        # Quick heuristic checks first (faster)
        heuristic_result = self._quick_heuristic_check(text, context)
        
        # If heuristics are confident, use them
        if heuristic_result["confidence"] > 0.7:
            return heuristic_result
        
        # Use BERT if available and heuristics are uncertain
        if self.is_loaded:
            bert_result = self._bert_classification(text)
            
            # Combine BERT and heuristic results
            combined_confidence = (bert_result["confidence"] * 0.6 + 
                                 heuristic_result["confidence"] * 0.4)
            
            # Use BERT prediction if it's more confident
            if bert_result["confidence"] > heuristic_result["confidence"]:
                return {
                    "is_heading": bert_result["is_heading"],
                    "confidence": combined_confidence,
                    "level": bert_result["level"],
                    "method": "bert+heuristic"
                }
        
        return heuristic_result
    
    def _quick_heuristic_check(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhanced quick heuristic-based heading detection
        """
        confidence = 0.0
        is_heading = False
        level = "body"
        
        # Immediate rejections for very short or problematic text
        if len(text.strip()) <= 2:
            return {"is_heading": False, "confidence": 0.95, "level": "body", "method": "heuristic"}
        
        # Length analysis with stricter rules
        text_len = len(text.strip())
        if text_len < 5:
            confidence -= 0.3  # Penalize very short text
        elif 5 <= text_len <= 80:
            confidence += 0.25  # Optimal heading length
        elif text_len <= 120:
            confidence += 0.15  # Acceptable length
        else:
            confidence -= 0.2   # Too long for typical heading
        
        # Font size check if context available
        if context and "font_size" in context:
            font_size = context["font_size"]
            avg_font = context.get("avg_font_size", 12)
            
            size_ratio = font_size / avg_font
            if size_ratio > 1.5:
                confidence += 0.5
                level = "h1"
                is_heading = True
            elif size_ratio > 1.25:
                confidence += 0.4
                level = "h2" 
                is_heading = True
            elif size_ratio > 1.1:
                confidence += 0.3
                level = "h3"
                is_heading = True
        
        # Enhanced bold text analysis
        if context and context.get("is_bold", False):
            confidence += 0.3
            if not is_heading and text_len > 5:
                level = "h3"
                is_heading = True
        
        # Sophisticated pattern matching
        text_lower = text.lower().strip()
        
        # Strong heading patterns
        strong_patterns = [
            (r'^(chapter|section|part|appendix|round)\s+\d+', 0.5, "h1"),
            (r'^(introduction|conclusion|summary|abstract|methodology|results)', 0.4, "h2"),
            (r'^\d+\.\s+[A-Z]', 0.4, "h2"),  # "1. Something"
            (r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*:$', 0.4, "h2"),  # "Title Case:"
        ]
        
        for pattern, score, suggested_level in strong_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                confidence += score
                if score > 0.3:
                    is_heading = True
                    level = suggested_level
                break
        
        # Medium patterns
        medium_patterns = [
            (r'^\d+\.\d+', 0.3, "h3"),  # Decimal numbering
            (r'^[IVX]+\.', 0.3, "h2"),  # Roman numerals
            (r'^[A-Z]\.', 0.2, "h3"),   # Letter enumeration
        ]
        
        for pattern, score, suggested_level in medium_patterns:
            if re.search(pattern, text):
                confidence += score
                if not is_heading and score > 0.2:
                    is_heading = True
                    level = suggested_level
                break
        
        # ALL CAPS analysis (with length constraints)
        if text.isupper() and 3 < text_len < 50:
            confidence += 0.3
            is_heading = True
            if not level or level == "body":
                level = "h2"
        
        # Title case bonus
        if text.istitle() and text_len < 60:
            confidence += 0.2
        
        # Strong negative indicators
        negative_patterns = [
            r'^(this|that|the|a|an|in|on|at|to|for|with|by|from)\s',
            r'[.!?]$',  # Ends with sentence punctuation
            r'\b(said|says|according|reported|mentioned|however|therefore|furthermore)\b',
            r'^(www|http|@)',  # URLs, emails
            r'^\d+$',  # Just numbers
        ]
        
        for pattern in negative_patterns:
            if re.search(pattern, text_lower):
                confidence -= 0.4
                break
        
        # Position-based analysis
        if context and "position" in context:
            x_pos = context["position"].get("x", 0)
            if x_pos < 50:  # Very left-aligned
                confidence += 0.15
            elif x_pos < 100:  # Left-aligned
                confidence += 0.1
        
        # Apply minimum confidence threshold
        min_confidence = 0.4  # Raised threshold for better precision
        
        # Final decision with stricter rules
        if confidence >= min_confidence and is_heading:
            # Additional validation for edge cases
            if text_len < 4 and confidence < 0.7:
                is_heading = False
                level = "body"
                confidence = 0.8
        else:
            is_heading = False
            level = "body"
        
        return {
            "is_heading": is_heading,
            "confidence": min(max(confidence, 0.0), 1.0),
            "level": level,
            "method": "heuristic"
        }
    
    def _bert_classification(self, text: str) -> Dict[str, Any]:
        """
        BERT-based heading classification
        """
        try:
            # Tokenize and encode
            inputs = self.tokenizer(text, return_tensors="pt", 
                                  truncation=True, max_length=128, 
                                  padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)  # Mean pooling
            
            # Simple classification based on embedding patterns
            # This is a simplified approach - in production, you'd train a classifier
            confidence = self._compute_heading_confidence(embeddings, text)
            
            # Determine level based on confidence and text features
            if confidence > 0.8:
                level = "h1"
            elif confidence > 0.6:
                level = "h2"
            elif confidence > 0.4:
                level = "h3"
            else:
                level = "body"
            
            return {
                "is_heading": confidence > 0.4,
                "confidence": confidence,
                "level": level,
                "method": "bert"
            }
            
        except Exception as e:
            print(f"BERT classification error: {e}")
            # Fallback to simple heuristic
            return {"is_heading": False, "confidence": 0.0, "level": "body", "method": "fallback"}
    
    def _compute_heading_confidence(self, embeddings: torch.Tensor, text: str) -> float:
        """
        Compute heading confidence based on embeddings and text features
        This is a simplified approach - in production, use trained classifier
        """
        # Convert to numpy for easier handling
        emb = embeddings.cpu().numpy().flatten()
        
        # Simple heuristics based on embedding characteristics
        # Headings typically have different semantic patterns
        
        # Text length factor
        length_factor = max(0, 1 - len(text) / 100)
        
        # Embedding norm (headings often have distinct semantic density)
        norm_factor = min(1.0, np.linalg.norm(emb) / 10)
        
        # Combine factors
        confidence = (length_factor * 0.3 + norm_factor * 0.7)
        
        # Boost for obvious heading patterns
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in self.heading_keywords):
            confidence += 0.2
        
        if re.match(r'^\d+\.', text):
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def batch_classify(self, texts: List[str], contexts: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Classify multiple texts in batch for efficiency
        """
        if contexts is None:
            contexts = [{}] * len(texts)
        
        results = []
        for text, context in zip(texts, contexts):
            result = self.is_heading(text, context)
            results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model
        """
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "device": str(self.device),
            "model_size_mb": self._estimate_model_size() if self.is_loaded else 0
        }
    
    def _estimate_model_size(self) -> float:
        """
        Estimate model size in MB
        """
        if not self.is_loaded:
            return 0
        
        total_params = sum(p.numel() for p in self.model.parameters())
        # Rough estimate: 4 bytes per parameter (float32)
        size_mb = (total_params * 4) / (1024 * 1024)
        return round(size_mb, 2)
