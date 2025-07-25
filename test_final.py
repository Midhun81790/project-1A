#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.extractor_final import PDFOutlineExtractorFinal
import json

def test_final_extractor():
    """Test the final PDF outline extractor"""
    
    print("🚀 Testing Final PDF Outline Extractor")
    print("=" * 50)
    
    # Test with the Adobe hackathon document
    pdf_file = "input/6874ef2e50a4a_adobe_india_hackathon_challenge_doc.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file not found: {pdf_file}")
        return
    
    try:
        extractor = PDFOutlineExtractorFinal()
        result = extractor.extract_outline(pdf_file)
        
        print(f"✅ Extraction completed")
        print(f"📋 Title: '{result['title']}'")
        print(f"📊 Outline entries: {len(result['outline'])}")
        print()
        
        print("📋 Extracted Outline:")
        print("-" * 50)
        for i, item in enumerate(result['outline'], 1):
            print(f"{i:2d}. [{item['level']}] {item['text']} (page {item['page']})")
        
        # Save result
        os.makedirs("output", exist_ok=True)
        output_file = "output/final_outline.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ Output saved to: {output_file}")
        
        # Format validation
        print("\n🔍 Format Validation:")
        print(f"   Title format: {'✅' if isinstance(result['title'], str) else '❌'}")
        print(f"   Outline format: {'✅' if isinstance(result['outline'], list) else '❌'}")
        
        if result['outline']:
            first_item = result['outline'][0]
            required_keys = {'level', 'text', 'page'}
            has_keys = all(key in first_item for key in required_keys)
            print(f"   Required keys: {'✅' if has_keys else '❌'}")
            
            # Check H1/H2/H3 format
            levels = {item['level'] for item in result['outline']}
            valid_levels = levels.issubset({'H1', 'H2', 'H3'})
            print(f"   Valid levels: {'✅' if valid_levels else '❌'}")
        
        # Compare with expected structure
        print(f"\n📈 Quality Metrics:")
        h1_count = len([item for item in result['outline'] if item['level'] == 'H1'])
        h2_count = len([item for item in result['outline'] if item['level'] == 'H2'])
        h3_count = len([item for item in result['outline'] if item['level'] == 'H3'])
        
        print(f"   H1 headings: {h1_count}")
        print(f"   H2 headings: {h2_count}")
        print(f"   H3 headings: {h3_count}")
        print(f"   Total: {len(result['outline'])} headings")
        
        # Expected vs actual comparison note
        print(f"\n📝 Expected format matching:")
        print(f"   Expected count: ~17 headings")
        print(f"   Actual count: {len(result['outline'])} headings")
        print(f"   Match quality: {'🎯 Good' if 10 <= len(result['outline']) <= 25 else '⚠️ Needs adjustment'}")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_extractor()
