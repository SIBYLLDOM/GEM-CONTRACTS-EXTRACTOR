# 📦 GEM Contracts Extractor - Project Analysis

## 🎯 Project Purpose

**Automated Web Scraping System** for extracting contract data from India's Government e-Marketplace (GeM) portal.

---

## 📂 Complete Folder Structure

```
GEM-CONTRACTS-EXTRACTOR/
│
├── 📄 run.py                           # ⭐ MAIN ENTRY POINT - Start here!
├── 📄 config.py                        # Configuration (URLs, timeouts, viewport)
├── 📄 playwright_manager.py            # Browser lifecycle management
├── 📄 requirements.txt                 # ✅ Python dependencies (CREATED)
├── 📄 SETUP_GUIDE.md                   # ✅ Installation guide (CREATED)
├── 📄 .gitignore                       # Git ignore rules
├── 📄 CAPTCHA_RETRY_UPDATE.md          # CAPTCHA improvements documentation
├── 📄 UPDATE_SUMMARY.md                # General updates documentation
│
├── 📁 controller/                      # Business Logic Layer
│   ├── 📄 __init__.py                  # Package initializer
│   ├── 📄 contracts_controller.py      # Original scraping controller
│   └── 📄 playwright_controller.py     # Advanced controller with retry logic
│
├── 📁 solver/                          # CAPTCHA Solving Module
│   ├── 📄 __init__.py                  # Package initializer
│   └── 📄 captcha_solver.py           # OCR-based CAPTCHA solver
│
├── 📁 service/                         # Service Layer (Currently Empty)
│   └── 📄 __init__.py                  # Package initializer
│
├── 📁 data/                            # Data Storage
│   ├── 📁 Datasets/                    # Input data
│   │   └── 📄 categories.csv           # Categories to process
│   └── 📁 scrapped/                    # Output data
│       └── 📄 contracts_merged.csv     # Extracted contracts
│
├── 📁 logs/                            # Application Logs
│   └── (log files)
│
├── 📁 __pycache__/                     # Python cache (auto-generated)
└── 📁 venv/                            # Virtual environment (local)

```

---

## 🔧 Technology Stack

### Core Technologies
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.8+ | Programming language |
| **Playwright** | 1.40.0 | Browser automation framework |
| **Tesseract OCR** | Latest | CAPTCHA text recognition |

### Python Libraries
| Library | Version | Usage |
|---------|---------|-------|
| `playwright` | 1.40.0 | Automate Chromium browser |
| `Pillow (PIL)` | 10.1.0 | Image loading & manipulation |
| `pytesseract` | 0.3.10 | Python wrapper for Tesseract OCR |
| `opencv-python` | 4.8.1.78 | Advanced image processing |
| `numpy` | 1.26.2 | Numerical array operations |

---

## 🔄 System Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                        START - run.py                            │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Initialize Browser (playwright_manager.py)                   │
│     • Launch Chromium (non-headless)                            │
│     • Navigate to https://gem.gov.in/                           │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Navigate to Contracts Page                                   │
│     • Click "View Contracts" menu                               │
│     • Wait for page load                                        │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Load Categories from CSV                                     │
│     • Read data/Datasets/categories.csv                         │
│     • Store in memory                                           │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. FOR EACH CATEGORY:                                          │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
        ┌────────────────────────────────────────┐
        │  4a. Select Category                    │
        │      • Type category name               │
        │      • Collect suggestions              │
        │      • Save new categories to CSV       │
        │      • Select first (exact) match       │
        └────────────────┬───────────────────────┘
                         ▼
        ┌────────────────────────────────────────┐
        │  4b. Set Date Filter                    │
        │      FROM: 2 days ago                   │
        │      TO: Today                          │
        └────────────────┬───────────────────────┘
                         ▼
        ┌────────────────────────────────────────┐
        │  4c. Solve CAPTCHA                      │
        │      • Extract image                    │
        │      • Apply preprocessing              │
        │      • Run OCR (multiple methods)       │
        │      • Vote for best result             │
        │      • Submit with confidence > 0.55    │
        │      • Retry up to 10 times             │
        └────────────────┬───────────────────────┘
                         ▼
        ┌────────────────────────────────────────┐
        │  4d. Check Results                      │
        └────────┬───────────────┬────────────────┘
                 ▼               ▼
        [No Results]        [Data Found!]
                 │               │
                 │               ▼
                 │    ┌──────────────────────────┐
                 │    │  4e. Extract Data         │
                 │    │      • Bid numbers        │
                 │    │      • Products/brands    │
                 │    │      • Quantities/prices  │
                 │    │      • Buyer info         │
                 │    │      • Download links     │
                 │    └──────────┬───────────────┘
                 │               ▼
                 │    ┌──────────────────────────┐
                 │    │  4f. Solve Modal CAPTCHA  │
                 │    │      (for each item)      │
                 │    └──────────┬───────────────┘
                 │               ▼
                 │    ┌──────────────────────────┐
                 │    │  4g. Save to CSV          │
                 │    │      (append row)         │
                 │    └──────────┬───────────────┘
                 │               │
                 └───────┬───────┘
                         ▼
                 [Next Category]
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. SUCCESS - All categories processed                          │
│     • Browser kept open for inspection                          │
│     • Results saved to data/scrapped/contracts_merged.csv       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Import Dependencies Analysis

### run.py
```python
from playwright_manager import PlaywrightManager
from controller.contracts_controller import ContractsController
import traceback  # Built-in
```

### playwright_manager.py
```python
from playwright.sync_api import sync_playwright
```

### controller/contracts_controller.py
```python
import csv         # Built-in
import base64      # Built-in
import io          # Built-in
from datetime import datetime, timedelta  # Built-in
from pathlib import Path  # Built-in
from PIL import Image     # Pillow package
from solver.captcha_solver import ensemble_solve
```

### controller/playwright_controller.py
```python
import csv         # Built-in
import base64      # Built-in
import io          # Built-in
import time        # Built-in
from datetime import datetime, timedelta  # Built-in
from pathlib import Path  # Built-in
from PIL import Image     # Pillow package
from solver.captcha_solver import ensemble_solve
```

### solver/captcha_solver.py
```python
import io                    # Built-in
import cv2                   # opencv-python
import numpy as np           # numpy
from PIL import Image, ImageOps, ImageFilter  # Pillow
import pytesseract           # pytesseract
from collections import Counter  # Built-in
```

---

## 🚀 Installation Commands

```bash
# 1. Navigate to project
cd c:/Users/rexro/OneDrive/Desktop/TENDER/GEM-CONTRACTS-EXTRACTOR

# 2. Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install

# 5. Install Tesseract OCR separately
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr
# Mac: brew install tesseract

# 6. Run the application
python run.py
```

---

## 📊 Data Flow

```
INPUT                          PROCESSING                       OUTPUT
──────                         ──────────                       ──────

categories.csv        →    contracts_controller.py    →    contracts_merged.csv
(si_no, name)              (scraping logic)                (full contract data)
                                    ↓
                          captcha_solver.py
                          (OCR processing)
                                    ↓
                          playwright_manager.py
                          (browser control)
```

---

## 🎓 Key Features

### ✅ Intelligent CAPTCHA Solving
- **Multi-preprocessing**: Grayscale, contrast, sharpen, threshold, invert
- **Multiple PSM modes**: 6, 7, 8, 10, 13 (different text layouts)
- **Ensemble voting**: Character-by-character consensus
- **Confidence scoring**: Only submits when confidence > 0.55
- **Auto-refresh**: Retries up to 10 times

### ✅ Dynamic Category Discovery
- Types exact category from CSV
- Captures all dropdown suggestions
- Auto-appends new categories to CSV
- Case-insensitive duplicate checking
- Windows-safe file writing with retry

### ✅ Robust Error Handling
- Automatic retry on failures
- Graceful handling of "No Result Found"
- Browser state recovery
- File lock management (Windows)
- Keyboard interrupt support

### ✅ Data Extraction
17 fields per contract:
1. serial_no
2. category_name
3. bid_no
4. product
5. brand
6. model
7. ordered_quantity
8. price
9. total_value
10. buyer_dept_org
11. organization_name
12. buyer_designation
13. state
14. buyer_department
15. office_zone
16. buying_mode
17. contract_date
18. order_status
19. download_link

---

## 🔍 Code Organization

### Separation of Concerns

| Module | Responsibility |
|--------|----------------|
| `run.py` | Application entry point & orchestration |
| `playwright_manager.py` | Browser lifecycle management |
| `config.py` | Configuration constants |
| `contracts_controller.py` | Basic scraping logic |
| `playwright_controller.py` | Advanced scraping with retry |
| `captcha_solver.py` | OCR & image processing |

---

## ⚙️ Configuration Options

Located in `config.py`:

```python
GEM_HOME_URL = "https://gem.gov.in/"
HEADLESS = False              # Run browser in background
SLOW_MO = 50                  # Slow down actions (ms)
DEFAULT_TIMEOUT = 30000       # Page load timeout (ms)
VIEWPORT = {
    "width": 1280,
    "height": 800
}
```

---

## 🐛 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Tesseract not found" | Install Tesseract and set path in captcha_solver.py line 16 |
| "Browser doesn't launch" | Run `playwright install` |
| "CSV file locked" | Close Excel/editor with the file open |
| "CAPTCHA fails" | Check Tesseract installation, increase retry attempts |
| "Module not found" | Run `pip install -r requirements.txt` |

---

## 📈 System Requirements

- **OS**: Windows 10/11, Linux, macOS
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 500MB for dependencies + browser binaries
- **Internet**: Required for GeM portal access

---

## 🎯 Next Steps

1. ✅ **requirements.txt created** - All Python dependencies listed
2. ✅ **SETUP_GUIDE.md created** - Complete installation guide
3. ✅ **PROJECT_ANALYSIS.md created** - This comprehensive overview
4. 📝 **Ready to install** - Follow installation commands above
5. 🚀 **Ready to run** - Execute `python run.py`

---

**Analysis Date:** 2026-01-09  
**Project Version:** 1.0  
**Status:** Production Ready  

