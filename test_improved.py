#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.extractor_improved import PDFOutlineExtractorImproved
import json

def test_improved_extractor():
    """Test the improved PDF outline extractor"""
    
    print("🚀 Testing Improved PDF Outline Extractor")
    print("=" * 50)
    
    # Test with the Adobe hackathon document
    pdf_file = "input/6874ef2e50a4a_adobe_india_hackathon_challenge_doc.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file not found: {pdf_file}")
        return
    
    try:
        extractor = PDFOutlineExtractorImproved()
        result = extractor.extract_outline(pdf_file)
        
        print(f"✅ Extraction completed")
        print(f"📋 Title: {result['title']}")
        print(f"📊 Outline entries: {len(result['outline'])}")
        print()
        
        print("📋 Extracted Outline:")
        print("-" * 30)
        for i, item in enumerate(result['outline'], 1):
            print(f"{i:2d}. [{item['level']}] {item['text']} (page {item['page']})")
        
        # Save result
        os.makedirs("output", exist_ok=True)
        output_file = "output/improved_outline.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Output saved to: {output_file}")
        
        # Compare with expected format
        print("\n🔍 Format Validation:")
        print(f"   Title format: {'✅' if isinstance(result['title'], str) else '❌'}")
        print(f"   Outline format: {'✅' if isinstance(result['outline'], list) else '❌'}")
        
        if result['outline']:
            first_item = result['outline'][0]
            required_keys = {'level', 'text', 'page'}
            has_keys = all(key in first_item for key in required_keys)
            print(f"   Required keys: {'✅' if has_keys else '❌'}")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_extractor()
