# Phase 3: PDF Extraction and CSV Generation

## Overview
Phase 3 extracts data from scraped PDF contracts and generates structured output files.

## What It Does

### Step 1: PDF → JSON Extraction
- Reads all PDFs from `data/scrapped/`
- Extracts **English-only content** (filters out Hindi text)
- Extracts:
  - Text content
  - Tables (structured data)
  - Metadata
- Saves clean JSON files to `data/JSON/`

### Step 2: JSON → CSV Extraction  
- Reads all JSON files from `data/JSON/`
- Extracts seller information:
  - `bid_no` (Contract Number: GEMC-XXXXXXXXXXXX)
  - `seller_id` (GeM Seller ID)
  - `seller_name` (Company Name)
  - `seller_email` (Email ID)
  - `unit_price` (Price per unit from table data)
- Saves to `data/seller_info.csv`

### Step 3: CSV → Database Sync (New)
- Connects to MySQL database
- Checks if `contracts` table needs new columns (`seller_id`, `seller_name`, `seller_email`, `unit_price`)
- Matches CSV records by `bid_no`
- Updates the database records with the new seller information

## Files Created

### Scripts
1. **`run_phase3.py`** - Master pipeline (runs all 3 steps)
2. **`run_phase3_extract_pdf_v2.py`** - PDF to JSON converter
3. **`run_phase3_json_to_csv.py`** - JSON to CSV extractor
4. **`save_seller_info_to_db.py`** - Database update script

### Output Files
- **`data/JSON/*.json`** - Individual JSON files for each contract
- **`data/seller_info.csv`** - Consolidated seller information

## Installation

Install at least one PDF library:

```bash
pip install pdfplumber
```

OR

```bash
pip install PyPDF2
```

Both are listed in `requirements.txt`.

## Usage

### Option 1: Run Complete Pipeline (Recommended)
```bash
python run_phase3.py
```

This runs both steps automatically:
1. Extracts all PDFs to JSON
2. Generates seller_info.csv

### Option 2: Run Steps Individually

**Step 1 only: PDF to JSON**
```bash
python run_phase3_extract_pdf_v2.py
```

**Step 2 only: JSON to CSV**
```bash
python run_phase3_json_to_csv.py
```

## Input/Output Structure

```
data/
├── scrapped/              # Input: PDF files
│   ├── GEMC-511687701265917.pdf
│   ├── GEMC-511687702174618.pdf
│   └── ... (42 PDFs total)
│
├── JSON/                  # Output: JSON files (Step 1)
│   ├── GEMC-511687701265917.json
│   ├── GEMC-511687702174618.json
│   └── ... (42 JSON files)
│
└── seller_info.csv        # Output: Final CSV (Step 2)
```

## JSON File Structure

Each JSON file contains:

```json
{
  "source_file": "GEMC-511687701265917.pdf",
  "extraction_date": "2026-01-14T23:56:19",
  "extraction_method": "pdfplumber",
  "metadata": {
    "Creator": "...",
    "Producer": "..."
  },
  "text_content": "Clean English text content...",
  "tables": [
    {
      "page": 1,
      "table_number": 1,
      "data": [
        ["Header1", "Header2", "..."],
        ["Value1", "Value2", "..."]
      ]
    }
  ],
  "table_count": 5,
  "total_pages": 12
}
```

## CSV File Structure

`seller_info.csv` columns:
- `bid_no` - Contract number (e.g., GEMC-511687701265917)
- `seller_id` - GeM Seller ID (e.g., 5I7A200001827894)
- `seller_name` - Company/Seller name
- `seller_email` - Contact email
- `seller_contact` - Phone number
- `unit_price` - Price per unit (e.g., 1,648)

## Features

### English-Only Filtering
- Uses character analysis to detect English vs Hindi text
- 70% ASCII threshold for language detection
- Removes all non-English content automatically

### Smart Unit Price Extraction
- Locates "Unit Price" columns in tables
- Finds price values after quantity/unit specifications
- Validates price ranges (filters out totals)
- Handles comma-formatted numbers

### Error Handling
- Continues processing even if some files fail
- Reports success/failure counts
- Detailed progress output

### Fallback Support
- Works with pdfplumber (preferred) OR PyPDF2
- Auto-detects available library
- Table extraction available with pdfplumber only

## Expected Results

For 42 PDF files:
- **42 JSON files** in `data/JSON/`
- **1 CSV file** with 42 rows (+ header) in `data/seller_info.csv`

## Troubleshooting

### "No PDF library found"
Install a PDF library:
```bash
pip install pdfplumber
```

### "No PDF files found"
Ensure PDFs are in `data/scrapped/` directory.

### Missing unit_price values
- Some PDFs may have different table formats
- Check the JSON file to see if tables were extracted
- May need manual adjustment for non-standard formats

### Missing seller information
- Some PDFs may not contain all fields
- The CSV will have empty values for missing data
- Check the JSON `text_content` field for raw data

## Notes

- Phase 3 is **separate from main pipeline** (not merged)
- Can be run independently at any time
- Safe to re-run (overwrites existing JSON/CSV files)
- Processing time: ~1-2 seconds per PDF

## Next Steps

After Phase 3 completion:
1. Review `data/seller_info.csv` for completeness
2. Use CSV for analysis, reporting, or database import
3. JSON files available for detailed contract analysis
