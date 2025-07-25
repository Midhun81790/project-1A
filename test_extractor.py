#!/usr/bin/env python3
"""
Test script for PDF Outline Extractor
Run this to test the extractor locally before Docker deployment
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_extractor():
    """Test the PDF extractor functionality"""
    
    print("🧪 Testing PDF Outline Extractor")
    print("=" * 50)
    
    # Check if input directory has PDFs
    input_dir = Path("./input")
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in input directory")
        print("Please place PDF files in the 'input' folder")
        return False
    
    print(f"📄 Found {len(pdf_files)} PDF file(s)")
    
    # Test import of modules
    try:
        from extractor import PDFExtractor
        from json_builder import JSONBuilder
        from bert_classifier import BERTHeadingClassifier
        print("✅ All modules imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test PDF processing
    try:
        extractor = PDFExtractor()
        json_builder = JSONBuilder()
        
        pdf_path = str(pdf_files[0])
        print(f"\n🔍 Testing with: {pdf_path}")
        
        # Extract raw information
        print("  → Extracting raw information...")
        raw_lines = extractor.extract_raw_info(pdf_path)
        print(f"  → Found {len(raw_lines)} text elements")
        
        if not raw_lines:
            print("  ❌ No text extracted from PDF")
            return False
        
        # Classify headings
        print("  → Classifying headings...")
        classified_lines = extractor.classify_headings(raw_lines)
        
        # Count headings
        heading_counts = {"h1": 0, "h2": 0, "h3": 0, "body": 0}
        for line in classified_lines:
            level = line.get("heading_level", "body")
            heading_counts[level] += 1
        
        print(f"  → Heading distribution: {heading_counts}")
        
        # Extract title
        title = extractor.extract_title(classified_lines)
        print(f"  → Document title: '{title}'")
        
        # Build JSON
        print("  → Building JSON output...")
        output_data = json_builder.build_output(title, classified_lines, pdf_path)
        
        # Validate
        if json_builder.validate_output(output_data):
            print("  ✅ JSON validation passed")
        else:
            print("  ❌ JSON validation failed")
            return False
        
        # Save test output
        os.makedirs("output", exist_ok=True)
        test_output_path = "output/test_output.json"
        json_builder.save_to_file(output_data, test_output_path)
        print(f"  ✅ Test output saved to: {test_output_path}")
        
        # Show sample outline
        outline = output_data.get("outline", [])
        print(f"\n📋 Sample outline ({len(outline)} headings):")
        for i, item in enumerate(outline[:5]):  # Show first 5
            print(f"  {i+1}. [{item['level']}] {item['text'][:60]}...")
        
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_bert_optional():
    """Test BERT classifier if available"""
    
    print("\n🤖 Testing BERT classifier (optional)...")
    
    try:
        from bert_classifier import BERTHeadingClassifier
        
        classifier = BERTHeadingClassifier()
        
        # Test quick heuristic classification
        test_texts = [
            "Chapter 1: Introduction",
            "1.1 Background Information",
            "This is a regular paragraph of text that should not be classified as a heading.",
            "METHODOLOGY",
            "3.2.1 Data Collection Procedures"
        ]
        
        print("  Testing heuristic classification:")
        for text in test_texts:
            result = classifier._quick_heuristic_check(text, {})
            print(f"    '{text[:30]}...' → {result['level']} (conf: {result['confidence']:.2f})")
        
        # Test BERT loading (optional)
        print("\n  Attempting to load BERT model...")
        if classifier.load_model():
            print("  ✅ BERT model loaded successfully")
            
            # Test BERT classification
            test_result = classifier.is_heading("Chapter 1: Introduction")
            print(f"  BERT test result: {test_result}")
        else:
            print("  ⚠️ BERT model not loaded (fallback to heuristics)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ BERT test error: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 PDF Outline Extractor - Test Suite")
    print("Adobe India Hackathon Challenge - Project 1A")
    print("=" * 60)
    
    success = True
    
    # Test core functionality
    if not test_extractor():
        success = False
    
    # Test BERT (optional)
    if not test_bert_optional():
        print("⚠️ BERT tests failed (non-critical)")
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All critical tests passed!")
        print("Ready for Docker deployment")
    else:
        print("❌ Some tests failed - check the errors above")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
