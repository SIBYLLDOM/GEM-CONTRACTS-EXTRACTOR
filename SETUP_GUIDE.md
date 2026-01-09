# GEM Contracts Extractor - Setup Guide

## 📋 Project Overview

This is an automated web scraping system designed to extract contract data from the Government e-Marketplace (GeM) portal. The system uses browser automation with Playwright and includes intelligent CAPTCHA solving capabilities.

## 🏗️ Project Structure

```
GEM-CONTRACTS-EXTRACTOR/
│
├── run.py                      # Main entry point
├── config.py                   # Configuration settings
├── playwright_manager.py       # Browser initialization & management
├── requirements.txt            # Python dependencies
│
├── controller/                 # Business logic controllers
│   ├── contracts_controller.py # Main scraping logic
│   └── playwright_controller.py # Advanced controller with retry logic
│
├── solver/                     # CAPTCHA solving module
│   └── captcha_solver.py      # OCR-based CAPTCHA solver
│
├── service/                    # Service layer (empty currently)
│
├── data/                       # Data storage
│   ├── Datasets/              # Input categories CSV
│   └── scrapped/              # Output extracted data
│
└── logs/                       # Application logs

```

## 🔧 Installation Steps

### 1. Install Python
- Ensure Python 3.8+ is installed
- Check with: `python --version`

### 2. Install Tesseract OCR (Required for CAPTCHA solving)

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR\`
3. Verify installation: `tesseract --version`

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### 3. Install Python Dependencies

```bash
# Navigate to project directory
cd c:/Users/rexro/OneDrive/Desktop/TENDER/GEM-CONTRACTS-EXTRACTOR

# Install required packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

## 🚀 Running the Application

### Basic Usage

```bash
python run.py
```

### What the Application Does:

1. **Launches Browser** - Opens Chromium browser (non-headless mode)
2. **Navigates to GeM** - Goes to https://gem.gov.in/
3. **Accesses Contracts Page** - Clicks through "View Contracts" menu
4. **Processes Categories** - Iterates through categories from `data/Datasets/categories.csv`
5. **Solves CAPTCHAs** - Uses OCR to solve security challenges
6. **Extracts Data** - Scrapes contract information
7. **Saves Results** - Outputs to `data/scrapped/contracts_merged.csv`

## 📦 Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| playwright | 1.40.0 | Browser automation |
| Pillow | 10.1.0 | Image processing |
| pytesseract | 0.3.10 | OCR for CAPTCHA |
| opencv-python | 4.8.1.78 | Advanced image processing |
| numpy | 1.26.2 | Numerical operations |

## ⚙️ Configuration

Edit `config.py` to customize:

```python
GEM_HOME_URL = "https://gem.gov.in/"
HEADLESS = False              # Set to True for headless mode
SLOW_MO = 50                  # Slow down browser actions (ms)
DEFAULT_TIMEOUT = 30000       # Default timeout (ms)
VIEWPORT = {
    "width": 1280,
    "height": 800
}
```

## 📊 Input/Output

### Input:
- **Categories CSV**: `data/Datasets/categories.csv`
  - Format: `si_no,category_name`

### Output:
- **Contracts CSV**: `data/scrapped/contracts_merged.csv`
  - Columns: serial_no, category_name, bid_no, product, brand, model, ordered_quantity, price, total_value, buyer_dept_org, organization_name, buyer_designation, state, buyer_department, office_zone, buying_mode, contract_date, order_status, download_link

## 🔍 Features

### CAPTCHA Solver
- Multi-preprocessing pipeline
- Multiple PSM (Page Segmentation Mode) strategies
- Ensemble voting for accuracy
- Confidence scoring
- Auto-retry with refresh

### Smart Category Processing
- Discovers new categories from suggestions
- Auto-appends to CSV dataset
- Exact matching with retry logic
- Handles "No Result Found" gracefully

### Robust Error Handling
- Automatic retry on failures
- Browser state management
- File lock handling (Windows safe)
- Keyboard interrupt support

## 🐛 Troubleshooting

### Issue: Tesseract not found
**Solution:** Ensure Tesseract is installed and path is correct in `captcha_solver.py` line 16

### Issue: Browser doesn't launch
**Solution:** Run `playwright install` to download browser binaries

### Issue: CSV file locked
**Solution:** Close any Excel/editor with the CSV file open

### Issue: CAPTCHA fails repeatedly
**Solution:** 
- Check Tesseract installation
- Verify `ALLOWED` characters in `captcha_solver.py`
- Increase retry attempts in controller

## 🎯 Advanced Usage

### Run from specific category:
Modify `run.py` to use:
```python
contracts.run_from_si_no(5)  # Start from category with si_no=5
```

### Headless Mode:
```python
browser = PlaywrightManager(headless=True)
```

## 📝 Recent Updates

Check these files for recent changes:
- `CAPTCHA_RETRY_UPDATE.md` - CAPTCHA solver improvements
- `UPDATE_SUMMARY.md` - General system updates

## 🔐 Security Notes

- System requires interaction with government portal
- Ensure compliance with GeM terms of service
- CAPTCHA solving is for legitimate automated access only
- Keep credentials secure (if authentication is added)

## 📞 Support

For issues or questions:
1. Check existing documentation files
2. Review conversation history
3. Check logs in `logs/` directory

---

**Last Updated:** 2026-01-09
**Version:** 1.0
**Python:** 3.8+
