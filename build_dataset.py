#!/usr/bin/env python3
"""
Build training dataset for heading classification by extracting text lines from PDFs
and matching them with ground truth JSON annotations.
"""

import json
import os
import fitz  # PyMuPDF
import pandas as pd
import re
from typing import List, Dict, Tuple

class DatasetBuilder:
    def __init__(self, pdf_dir: str, json_dir: str):
        self.pdf_dir = pdf_dir
        self.json_dir = json_dir
        self.training_data = []
        
    def extract_text_elements(self, pdf_path: str) -> List[Dict]:
        """Extract all text elements with metadata from PDF."""
        doc = fitz.open(pdf_path)
        elements = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text and len(text) > 2:  # Filter out very short texts
                                elements.append({
                                    "text": text,
                                    "page": page_num,
                                    "font_size": round(span["size"], 1),
                                    "font_flags": span["flags"],
                                    "is_bold": bool(span["flags"] & 2**4),
                                    "bbox": span["bbox"]
                                })
        
        doc.close()
        return elements
    
    def load_ground_truth(self, json_path: str) -> List[str]:
        """Load ground truth headings from JSON file."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        headings = []
        for item in data.get("outline", []):
            heading_text = item.get("text", "").strip()
            if heading_text:
                headings.append(heading_text)
        
        return headings
    
    def clean_text_for_matching(self, text: str) -> str:
        """Clean text for better matching with ground truth."""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove common artifacts
        text = re.sub(r'[^\w\s\-\(\)\[\].,;:!?&]', '', text)
        return text.lower()
    
    def is_heading_match(self, extracted_text: str, ground_truth_headings: List[str]) -> bool:
        """Check if extracted text matches any ground truth heading."""
        cleaned_extracted = self.clean_text_for_matching(extracted_text)
        
        for heading in ground_truth_headings:
            cleaned_heading = self.clean_text_for_matching(heading)
            
            # Exact match
            if cleaned_extracted == cleaned_heading:
                return True
            
            # Partial match (extracted text contains heading or vice versa)
            if len(cleaned_heading) > 10:  # Only for longer headings
                if cleaned_heading in cleaned_extracted or cleaned_extracted in cleaned_heading:
                    return True
            
            # Fuzzy match for fragmented text (common in PDF extraction)
            if len(cleaned_heading) > 15:
                # Check if most words from heading appear in extracted text
                heading_words = set(cleaned_heading.split())
                extracted_words = set(cleaned_extracted.split())
                
                if len(heading_words) > 2:  # At least 3 words
                    overlap = len(heading_words.intersection(extracted_words))
                    if overlap / len(heading_words) >= 0.7:  # 70% word overlap
                        return True
        
        return False
    
    def process_file(self, file_num: int):
        """Process a single PDF file and its corresponding JSON."""
        pdf_path = os.path.join(self.pdf_dir, f"file{file_num:02d}.pdf")
        json_path = os.path.join(self.json_dir, f"file{file_num:02d}.json")
        
        if not os.path.exists(pdf_path) or not os.path.exists(json_path):
            print(f"Skipping file{file_num:02d} - missing PDF or JSON")
            return
        
        print(f"Processing file{file_num:02d}...")
        
        # Extract text elements from PDF
        text_elements = self.extract_text_elements(pdf_path)
        print(f"  Extracted {len(text_elements)} text elements")
        
        # Load ground truth headings
        ground_truth_headings = self.load_ground_truth(json_path)
        print(f"  Ground truth has {len(ground_truth_headings)} headings")
        
        # Label each text element
        for element in text_elements:
            is_heading = self.is_heading_match(element["text"], ground_truth_headings)
            
            self.training_data.append({
                "file": f"file{file_num:02d}",
                "text": element["text"],
                "page": element["page"],
                "font_size": element["font_size"],
                "is_bold": element["is_bold"],
                "font_flags": element["font_flags"],
                "label": 1 if is_heading else 0
            })
        
        # Count labels for this file
        file_data = [d for d in self.training_data if d["file"] == f"file{file_num:02d}"]
        heading_count = sum(1 for d in file_data if d["label"] == 1)
        total_count = len(file_data)
        print(f"  Labeled {heading_count} headings out of {total_count} text elements")
    
    def build_dataset(self):
        """Build the complete training dataset."""
        print("Building training dataset...")
        
        # Process files 01-05
        for file_num in range(1, 6):
            self.process_file(file_num)
        
        # Convert to DataFrame and save
        df = pd.DataFrame(self.training_data)
        
        print(f"\nDataset Summary:")
        print(f"Total text elements: {len(df)}")
        print(f"Headings (label=1): {df['label'].sum()}")
        print(f"Non-headings (label=0): {len(df) - df['label'].sum()}")
        print(f"Heading ratio: {df['label'].mean():.3f}")
        
        # Save dataset
        output_path = "data/heading_training_data.csv"
        df.to_csv(output_path, index=False)
        print(f"\nDataset saved to: {output_path}")
        
        # Show sample data
        print("\nSample data:")
        print(df[df['label'] == 1].head(10)[['text', 'font_size', 'is_bold', 'label']])
        
        return df

def main():
    builder = DatasetBuilder(
        pdf_dir="input",
        json_dir="Challenge_1a/actual-outputs"
    )
    
    dataset = builder.build_dataset()
    
    print("\nDataset creation complete!")
    print(f"Training data ready for MiniLM classifier training.")

if __name__ == "__main__":
    main()
