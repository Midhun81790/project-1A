#!/usr/bin/env python3

import os
import sys
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from extractor import PDFOutlineExtractor

def process_pdf(pdf_path: str, output_dir: str = "output") -> dict:
    """
    Process a single PDF and extract its outline using optimized Challenge 1A approach.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the output JSON
        
    Returns:
        Dictionary with processing results
    """
    try:
        start_time = time.time()
        
        # Initialize the optimized extractor
        extractor = PDFOutlineExtractor()
        
        # Extract outline using reference-based patterns
        result = extractor.extract_outline(pdf_path)
        
        # Generate output filename
        pdf_name = Path(pdf_path).stem
        output_filename = f"{pdf_name}_outline.json"
        output_path = Path(output_dir) / output_filename
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save JSON output directly
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        
        processing_time = time.time() - start_time
        
        return {
            "status": "success",
            "pdf_path": pdf_path,
            "output_path": str(output_path),
            "processing_time": processing_time,
            "outline_count": len(result["outline"]),
            "title": result["title"]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "pdf_path": pdf_path,
            "error": str(e),
            "processing_time": 0,
            "outline_count": 0
        }

def main():
    """
    Main function optimized for Challenge 1A format matching.
    Processes PDFs and generates outlines matching reference structure.
    """
    print("🚀 PDF Outline Extractor - Challenge 1A Optimized")
    print("=" * 60)
    
    # Define input and output directories
    input_dir = "input"
    output_dir = "output"
    
    # Ensure directories exist
    Path(input_dir).mkdir(exist_ok=True)
    Path(output_dir).mkdir(exist_ok=True)
    
    # Find all PDFs in input directory
    pdf_files = list(Path(input_dir).glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in '{input_dir}' directory")
        print(f"💡 Please place PDF files in the '{input_dir}' directory and run again")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF file(s) to process")
    print()
    
    # Process each PDF
    results = []
    total_start_time = time.time()
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"Processing {i}/{len(pdf_files)}: {pdf_path.name}")
        
        result = process_pdf(str(pdf_path), output_dir)
        results.append(result)
        
        if result["status"] == "success":
            print(f"✅ Successfully processed in {result['processing_time']:.2f}s")
            print(f"   📋 Title: {result['title']}")
            print(f"   📊 Outline items: {result['outline_count']}")
            print(f"   💾 Saved to: {result['output_path']}")
        else:
            print(f"❌ Error: {result['error']}")
        print()
    
    # Summary
    total_time = time.time() - total_start_time
    successful = len([r for r in results if r["status"] == "success"])
    
    print("=" * 60)
    print("📈 PROCESSING SUMMARY")
    print(f"✅ Successful: {successful}/{len(pdf_files)}")
    print(f"⏱️  Total time: {total_time:.2f}s")
    print(f"📁 Output directory: {output_dir}")
    
    if successful > 0:
        avg_time = sum(r["processing_time"] for r in results if r["status"] == "success") / successful
        print(f"📊 Average processing time: {avg_time:.2f}s per PDF")
    
    print("\n🎯 Challenge 1A optimization complete!")

if __name__ == "__main__":
    main()
