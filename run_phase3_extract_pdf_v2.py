"""
Phase 3: Fast PDF to JSON Extraction Script
Uses multi-processing for maximum speed.
Extracts content from scraped PDFs and converts to clean JSON files
Filters out Hindi/non-English content and keeps only English text.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

# Try importing PDF libraries
PDF_LIBRARY = None
try:
    import pdfplumber
    PDF_LIBRARY = "pdfplumber"
except ImportError:
    try:
        import PyPDF2
        PDF_LIBRARY = "PyPDF2"
    except ImportError:
        pass

# Directories
SCRAPPED_PDF_DIR = "data/scrapped"
JSON_OUTPUT_DIR = "data/JSON"

def is_english_text(text: str) -> bool:
    """Check if text contains primarily English characters."""
    if not text or not text.strip():
        return False
    # Remove whitespace and special characters for analysis
    cleaned_text = re.sub(r'[^\w\s]', '', text)
    if not cleaned_text:
        return False
    # Count English characters (ASCII letters and numbers)
    english_chars = sum(1 for c in cleaned_text if ord(c) < 128 and (c.isalnum() or c.isspace()))
    total_chars = len(cleaned_text)
    # If more than 70% are English characters, consider it English
    if total_chars > 0:
        return (english_chars / total_chars) > 0.7
    return False

def clean_english_text(text: str) -> str:
    """Clean text by removing Hindi and non-English content."""
    if not text:
        return ""
    # Split into lines and filter
    lines = text.split('\n')
    english_lines = []
    for line in lines:
        line = line.strip()
        if line and is_english_text(line):
            # Remove any remaining non-ASCII characters
            clean_line = ''.join(char if ord(char) < 128 else ' ' for char in line)
            clean_line = ' '.join(clean_line.split())  # Normalize whitespace
            if clean_line:
                english_lines.append(clean_line)
    return '\n'.join(english_lines)

def extract_with_pdfplumber(pdf_path: str) -> Dict[str, Any]:
    """Extract PDF content using pdfplumber library."""
    import pdfplumber
    result = {"text_content": "", "tables": [], "metadata": {}, "total_pages": 0}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            result["total_pages"] = len(pdf.pages)
            # Extract metadata
            if pdf.metadata:
                for key, value in pdf.metadata.items():
                    if value:
                        str_val = str(value)
                        if is_english_text(str_val):
                            result["metadata"][key] = clean_english_text(str_val)
            # Extract text from all pages
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    clean_txt = clean_english_text(text)
                    if clean_txt:
                        full_text += clean_txt + "\n"
            result["text_content"] = full_text.strip()
            # Extract tables
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                if tables:
                    for table_num, table in enumerate(tables, start=1):
                        clean_table = []
                        for row in table:
                            clean_row = []
                            for cell in row:
                                if cell:
                                    cell_text = str(cell).strip()
                                    if is_english_text(cell_text):
                                        clean_row.append(clean_english_text(cell_text))
                                    else:
                                        clean_row.append("")
                                else:
                                    clean_row.append("")
                            if any(clean_row):
                                clean_table.append(clean_row)
                        if clean_table:
                            result["tables"].append({
                                "page": page_num, "table_number": table_num, "data": clean_table
                            })
    except Exception as e:
        print(f"Error with pdfplumber on {pdf_path}: {e}")
    return result

def extract_with_pypdf2(pdf_path: str) -> Dict[str, Any]:
    """Extract PDF content using PyPDF2 library."""
    import PyPDF2
    result = {"text_content": "", "tables": [], "metadata": {}, "total_pages": 0}
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            result["total_pages"] = len(pdf_reader.pages)
            # Extract metadata
            if pdf_reader.metadata:
                for key, value in pdf_reader.metadata.items():
                    if value:
                        str_val = str(value)
                        if is_english_text(str_val):
                            result["metadata"][key.replace('/', '')] = clean_english_text(str_val)
            # Extract text from all pages
            full_text = ""
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    clean_txt = clean_english_text(text)
                    if clean_txt:
                        full_text += clean_txt + "\n"
            result["text_content"] = full_text.strip()
    except Exception as e:
        print(f"Error with PyPDF2 on {pdf_path}: {e}")
    return result

def process_single_pdf(args: Tuple[str, str, str]) -> bool:
    """Task for worker processes."""
    pdf_path, output_path, lib = args
    try:
        # Extract based on available library
        if lib == "pdfplumber":
            extracted_data = extract_with_pdfplumber(pdf_path)
        elif lib == "PyPDF2":
            extracted_data = extract_with_pypdf2(pdf_path)
        else:
            return False

        # Build JSON structure
        json_data = {
            "source_file": os.path.basename(pdf_path),
            "extraction_date": datetime.now().isoformat(),
            "extraction_method": lib,
            "metadata": extracted_data["metadata"],
            "text_content": extracted_data["text_content"],
            "tables": extracted_data["tables"],
            "table_count": len(extracted_data["tables"]),
            "total_pages": extracted_data["total_pages"]
        }
        # Save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def process_all_pdfs():
    """Process all PDFs in parallel."""
    Path(JSON_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    pdf_files = list(Path(SCRAPPED_PDF_DIR).glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {SCRAPPED_PDF_DIR}")
        return

    if not PDF_LIBRARY:
        print("✗ No PDF library found. Please install: pip install pdfplumber or PyPDF2")
        return

    print(f"\n🚀 Phase 3: Fast Parallel Extraction")
    print(f"   Mode: {PDF_LIBRARY} | Files: {len(pdf_files)}")
    print("=" * 70)

    # Prepare tasks
    tasks = []
    for pdf_file in pdf_files:
        json_path = os.path.join(JSON_OUTPUT_DIR, pdf_file.stem + ".json")
        tasks.append((str(pdf_file), json_path, PDF_LIBRARY))

    success_count = 0
    # Utilize all CPU cores
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_single_pdf, task): task for task in tasks}
        
        count = 0
        for future in as_completed(futures):
            count += 1
            pdf_path = futures[future][0]
            if future.result():
                success_count += 1
                if count % 5 == 0 or count == len(pdf_files):
                    print(f"[{count}/{len(pdf_files)}] Processed: {os.path.basename(pdf_path)}")
            else:
                print(f"[{count}/{len(pdf_files)}] ✗ Failed: {os.path.basename(pdf_path)}")

    print("\n" + "=" * 70)
    print(f"📊 Fast Processing Complete!")
    print(f"   ✓ Success: {success_count}/{len(pdf_files)}")
    print(f"   📁 JSON: {JSON_OUTPUT_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    process_all_pdfs()
