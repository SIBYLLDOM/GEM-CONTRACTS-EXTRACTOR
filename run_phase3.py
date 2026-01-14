"""
Phase 3: Complete PDF to JSON to CSV Pipeline
Master script that runs both extraction steps:
1. Extract PDFs to JSON files (English only)
2. Extract seller information from JSON to CSV

Run this to execute the complete Phase 3 pipeline.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_step(step_name: str, script_path: str) -> bool:
    """
    Run a Python script and return True if successful.
    """
    print("\n" + "=" * 80)
    print(f"STEP: {step_name}")
    print("=" * 80)
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.getcwd(),
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✓ {step_name} completed successfully!")
            return True
        else:
            print(f"\n✗ {step_name} failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n✗ Error running {step_name}: {e}")
        return False


def check_dependencies():
    """
    Check if required dependencies are installed.
    """
    print("Checking dependencies...")
    
    missing_deps = []
    
    # Check for PDF libraries
    pdf_lib_found = False
    try:
        import pdfplumber
        print("  ✓ pdfplumber found")
        pdf_lib_found = True
    except ImportError:
        try:
            import PyPDF2
            print("  ✓ PyPDF2 found")
            pdf_lib_found = True
        except ImportError:
            missing_deps.append("pdfplumber or PyPDF2")
    
    if missing_deps:
        print("\n✗ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install missing dependencies:")
        print("  pip install pdfplumber")
        print("  OR")
        print("  pip install PyPDF2")
        return False
    
    print("✓ All dependencies satisfied!\n")
    return True


def check_input_files():
    """
    Check if PDF files exist in data/scrapped directory.
    """
    pdf_dir = Path("data/scrapped")
    
    if not pdf_dir.exists():
        print(f"✗ Directory not found: {pdf_dir}")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"✗ No PDF files found in {pdf_dir}")
        return False
    
    print(f"✓ Found {len(pdf_files)} PDF files ready for processing")
    return True


def main():
    """
    Main execution function for Phase 3 pipeline.
    """
    print("=" * 80)
    print("PHASE 3: PDF TO JSON TO CSV PIPELINE")
    print("=" * 80)
    print()
    print("This pipeline will:")
    print("  1. Extract English content from PDFs → JSON files")
    print("  2. Extract seller information from JSON → CSV file")
    print()
    
    # Pre-flight checks
    if not check_dependencies():
        print("\n✗ Dependency check failed. Please install required packages.")
        return
    
    if not check_input_files():
        print("\n✗ Input file check failed. Please ensure PDFs are in data/scrapped/")
        return
    
    # Run Step 1: PDF to JSON extraction
    step1_success = run_step(
        "Step 1: Extract PDFs to JSON",
        "run_phase3_extract_pdf_v2.py"
    )
    
    if not step1_success:
        print("\n✗ Step 1 failed. Stopping pipeline.")
        return
    
    # Run Step 2: JSON to CSV extraction
    step2_success = run_step(
        "Step 2: Extract Seller Info to CSV",
        "run_phase3_json_to_csv.py"
    )
    
    if not step2_success:
        print("\n✗ Step 2 failed.")
        return

    # Run Step 3: Save to Database
    step3_success = run_step(
        "Step 3: Save Seller Info to Database",
        "save_seller_info_to_db.py"
    )
    
    if not step3_success:
        print("\n✗ Step 3 failed.")
        return
    
    # Final summary
    print("\n" + "=" * 80)
    print("PHASE 3 PIPELINE COMPLETE! 🎉")
    print("=" * 80)
    print("\nOutput files & Actions:")
    print(f"  📁 JSON files: data/JSON/")
    print(f"  📊 CSV file: data/seller_info.csv")
    print(f"  🗄️  Database: Updated 'contracts' table")
    print()
    print("Complete extraction and database sync successful!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Pipeline interrupted by user.")
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
