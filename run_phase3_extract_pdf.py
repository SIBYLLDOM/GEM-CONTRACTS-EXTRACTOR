"""
Phase 3: PDF to JSON Extraction Script
Extracts content from scraped PDFs and converts to clean JSON files
Filters out Hindi/non-English content and keeps only English text
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any
import pdfplumber
from datetime import datetime

# Directories
SCRAPPED_PDF_DIR = "data/scrapped"
JSON_OUTPUT_DIR = "data/JSON"

# Ensure output directory exists
Path(JSON_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def is_english_text(text: str) -> bool:
    """
    Check if text contains primarily English characters.
    Returns True if the text is predominantly English.
    """
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
    """
    Clean text by removing Hindi and non-English content.
    Keeps only English letters, numbers, and common punctuation.
    """
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


def extract_tables_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract tables from PDF and return as list of dictionaries.
    Only includes tables with English content.
    """
    tables_data = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                
                if tables:
                    for table_num, table in enumerate(tables, start=1):
                        # Convert table to clean format
                        clean_table = []
                        for row in table:
                            clean_row = []
                            for cell in row:
                                if cell:
                                    cell_text = str(cell).strip()
                                    if is_english_text(cell_text):
                                        clean_cell = clean_english_text(cell_text)
                                        clean_row.append(clean_cell)
                                    else:
                                        clean_row.append("")
                                else:
                                    clean_row.append("")
                            
                            # Only add row if it has some content
                            if any(clean_row):
                                clean_table.append(clean_row)
                        
                        if clean_table:
                            tables_data.append({
                                "page": page_num,
                                "table_number": table_num,
                                "data": clean_table
                            })
    except Exception as e:
        print(f"Error extracting tables: {e}")
    
    return tables_data


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from PDF.
    Returns only English text content.
    """
    full_text = ""
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    clean_text = clean_english_text(text)
                    if clean_text:
                        full_text += clean_text + "\n"
    except Exception as e:
        print(f"Error extracting text: {e}")
    
    return full_text.strip()


def extract_metadata_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata from PDF file.
    """
    metadata = {}
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if pdf.metadata:
                # Only include metadata that has English content
                for key, value in pdf.metadata.items():
                    if value:
                        str_value = str(value)
                        if is_english_text(str_value):
                            metadata[key] = clean_english_text(str_value)
    except Exception as e:
        print(f"Error extracting metadata: {e}")
    
    return metadata


def extract_pdf_to_json(pdf_path: str, output_path: str) -> bool:
    """
    Extract PDF content and save as JSON file.
    Returns True if successful, False otherwise.
    """
    try:
        print(f"Processing: {os.path.basename(pdf_path)}...")
        
        # Extract different components
        text_content = extract_text_from_pdf(pdf_path)
        tables = extract_tables_from_pdf(pdf_path)
        metadata = extract_metadata_from_pdf(pdf_path)
        
        # Build JSON structure
        json_data = {
            "source_file": os.path.basename(pdf_path),
            "extraction_date": datetime.now().isoformat(),
            "metadata": metadata,
            "text_content": text_content,
            "tables": tables,
            "table_count": len(tables),
            "total_pages": 0
        }
        
        # Get page count
        try:
            with pdfplumber.open(pdf_path) as pdf:
                json_data["total_pages"] = len(pdf.pages)
        except:
            pass
        
        # Save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved: {os.path.basename(output_path)}")
        return True
        
    except Exception as e:
        print(f"✗ Error processing {os.path.basename(pdf_path)}: {e}")
        return False


def process_all_pdfs():
    """
    Process all PDFs in the scrapped directory and convert to JSON.
    """
    # Get all PDF files
    pdf_files = list(Path(SCRAPPED_PDF_DIR).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {SCRAPPED_PDF_DIR}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    print("=" * 60)
    
    success_count = 0
    failed_count = 0
    
    for pdf_file in pdf_files:
        # Generate output filename (GEMC-XXXX.pdf -> GEMC-XXXX.json)
        json_filename = pdf_file.stem + ".json"
        json_path = os.path.join(JSON_OUTPUT_DIR, json_filename)
        
        # Extract and save
        if extract_pdf_to_json(str(pdf_file), json_path):
            success_count += 1
        else:
            failed_count += 1
    
    print("=" * 60)
    print(f"Processing complete!")
    print(f"✓ Success: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"JSON files saved in: {JSON_OUTPUT_DIR}")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 3: PDF to JSON Extraction")
    print("Extracting English-only content from PDFs")
    print("=" * 60)
    print()
    
    process_all_pdfs()
