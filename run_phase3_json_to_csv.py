"""
Phase 3B: Extract Seller Information from JSON to CSV
Extracts bid_no, seller_id, seller_name, seller_email, seller_contact, unit_price
from JSON files and saves to seller_info.csv
"""

import os
import json
import csv
import re
from pathlib import Path
from typing import Dict, Optional, List

# Directories
JSON_DIR = "data/JSON"
OUTPUT_CSV = "data/seller_info.csv"

# CSV Headers
CSV_HEADERS = ["bid_no", "seller_id", "seller_name", "seller_email", "unit_price"]


def extract_contract_number(text_content: str) -> Optional[str]:
    """Extract Contract Number from text content."""
    patterns = [
        r'Contract\s+No\s*:+\s*([A-Z0-9-]+)',
        r'CCoonnttrraacctt\s+NNoo\s*:+\s*([A-Z0-9-]+)',
        r'Contract\s+Number\s*:+\s*([A-Z0-9-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def extract_seller_id(text_content: str) -> Optional[str]:
    """Extract GeM Seller ID from text content."""
    patterns = [
        r'GeM\s+Seller\s+ID\s*:+\s*([A-Z0-9]+)',
        r'GGeeM\s+SSeelllleerr\s+IIDD\s*:+\s*([A-Z0-9]+)',
        r'Seller\s+ID\s*:+\s*([A-Z0-9]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def extract_seller_name(text_content: str) -> Optional[str]:
    """Extract Seller/Company Name from text content."""
    patterns = [
        r'Company\s+Name\s*:+\s*([^\n]+)',
        r'CCoommppaannyy\s+NNaammee\s*:+\s*([^\n]+)',
        r'Seller\s+Name\s*:+\s*([^\n]+)',
        r'SSeelllleerr\s+NNaammee\s*:+\s*([^\n]+)',
        r'Firm\s+Name\s*:+\s*([^\n]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up any extra formatting
            name = re.sub(r'\s+', ' ', name)
            return name
    
    return None


def extract_email(text_content: str) -> Optional[str]:
    """Extract Email ID from text content."""
    patterns = [
        r'Email\s+ID\s*:+\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'EEmmaaiill\s+IIDD\s*:+\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'Email\s*:+\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def extract_contact(text_content: str) -> Optional[str]:
    """Extract Contact Number from text content."""
    patterns = [
        r'Contact\s+No\.?\s*:+\s*([0-9]+)',
        r'CCoonntaacctt\s+NNoo\.?\s*:+\s*([0-9]+)',
        r'Phone\s*:+\s*([0-9]+)',
        r'Mobile\s*:+\s*([0-9]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


def normalize_for_match(text: str) -> str:
    """Normalize text for matching by removing artifacts and spaces."""
    if not text:
        return ""
    # Remove doubled characters (e.g., 'UUnniitt' -> 'Unit')
    # This is a common artifact in some PDF extractions
    text = re.sub(r'(.)\1', r'\1', text)
    return text.lower().replace(" ", "").replace("\n", "")

def extract_unit_price_from_tables(tables: List[Dict]) -> Optional[str]:
    """
    Extract Unit Price from table data.
    Handles 'doubled' characters like 'UUnniitt PPrriiccee'.
    """
    if not tables:
        return None
    
    for table in tables:
        table_data = table.get('data', [])
        if not table_data:
            continue
        
        unit_price_col_idx = -1
        header_row_idx = -1
        
        # 1. Search for the header row
        for row_idx, row in enumerate(table_data):
            for col_idx, cell in enumerate(row):
                if not cell:
                    continue
                
                norm_cell = normalize_for_match(cell)
                # Look for "unitprice" or "price" in the normalized text
                if "unitprice" in norm_cell or ("price" in norm_cell and "total" not in norm_cell):
                    unit_price_col_idx = col_idx
                    header_row_idx = row_idx
                    break
            if unit_price_col_idx != -1:
                break
        
        # 2. Extract the value from subsequent rows
        if unit_price_col_idx != -1 and header_row_idx != -1:
            for row_idx in range(header_row_idx + 1, len(table_data)):
                row = table_data[row_idx]
                if unit_price_col_idx < len(row):
                    price_cell = row[unit_price_col_idx].strip()
                    # Match numbers like "1,648" or "14,498.4" or "380"
                    if price_cell and re.match(r'^[\d,]+\.?\d*$', price_cell):
                        try:
                            # Verify it is a valid numeric value
                            price_num = float(price_cell.replace(',', ''))
                            if price_num > 0:
                                return price_cell
                        except ValueError:
                            continue
                            
    return None


def extract_seller_info_from_json(json_path: str) -> Dict[str, str]:
    """
    Extract all seller information from a JSON file.
    Returns a dictionary with all required fields.
    """
    result = {
        "bid_no": "",
        "seller_id": "",
        "seller_name": "",
        "seller_email": "",
        "unit_price": ""
    }
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        text_content = data.get('text_content', '')
        tables = data.get('tables', [])
        
        # Extract each field
        result['bid_no'] = extract_contract_number(text_content) or ""
        result['seller_id'] = extract_seller_id(text_content) or ""
        result['seller_name'] = extract_seller_name(text_content) or ""
        result['seller_email'] = extract_email(text_content) or ""
        result['unit_price'] = extract_unit_price_from_tables(tables) or ""
        
        # If bid_no is empty, try to get from filename
        if not result['bid_no']:
            filename = Path(json_path).stem
            if filename.startswith('GEMC-'):
                result['bid_no'] = filename
        
    except Exception as e:
        print(f"  Error processing {os.path.basename(json_path)}: {e}")
    
    return result


def process_all_json_to_csv():
    """
    Process all JSON files and create seller_info.csv
    """
    # Get all JSON files
    json_files = list(Path(JSON_DIR).glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {JSON_DIR}")
        print("Please run the PDF extraction script first (run_phase3_extract_pdf_v2.py)")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    print("=" * 70)
    
    all_records = []
    success_count = 0
    
    for idx, json_file in enumerate(json_files, 1):
        print(f"[{idx}/{len(json_files)}] Processing: {json_file.name}...")
        
        seller_info = extract_seller_info_from_json(str(json_file))
        all_records.append(seller_info)
        
        # Show extracted data
        print(f"  ✓ Bid: {seller_info['bid_no']}")
        print(f"    Seller ID: {seller_info['seller_id']}")
        print(f"    Email: {seller_info['seller_email']}")
        print(f"    Unit Price: {seller_info['unit_price']}")
        
        if seller_info['bid_no'] and seller_info['seller_id']:
            success_count += 1
    
    # Write to CSV
    print("\n" + "=" * 70)
    print("Writing to CSV...")
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(all_records)
    
    print(f"✓ CSV file created: {OUTPUT_CSV}")
    print(f"  Total records: {len(all_records)}")
    print(f"  Complete records: {success_count}")
    print("=" * 70)


if __name__ == "__main__":
    print("=" * 70)
    print("Phase 3B: JSON to CSV Extraction")
    print("Extracting seller information from JSON files")
    print("=" * 70)
    print()
    
    process_all_json_to_csv()
