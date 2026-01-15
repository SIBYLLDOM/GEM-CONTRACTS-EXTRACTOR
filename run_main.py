"""
GeM Contracts Extraction System - Master Orchestrator (run_main.py)
-----------------------------------------------------------------
This script runs all three phases sequentially:
1. Phase 1: Search & Row Scraping (run.py)
2. Phase 2: PDF Downloading (run_phase2.py)
3. Phase 3: Data Extraction & DB Sync (run_phase3.py)
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_phase(phase_name: str, script_name: str) -> bool:
    """
    Executes a phase and returns True if successful.
    """
    print("\n" + "=" * 80)
    print(f"🔥 STARTING {phase_name} ({script_name})")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # Run the script as a separate process to clean up resources between phases
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.getcwd(),
            capture_output=False,
            text=True
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"\n✅ {phase_name} COMPLETED SUCCESSFULLY in {duration:.2f}s")
            return True
        else:
            print(f"\n❌ {phase_name} FAILED (Return Code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during {phase_name}: {e}")
        return False

def main():
    print("\n" + "#" * 80)
    print("🚀 GeM CONTRACTS EXTRACTION MASTER PIPELINE")
    print("#" * 80)
    
    # Check if we are in venv
    if not hasattr(sys, 'real_prefix') and not (sys.base_prefix != sys.prefix):
        print("⚠️ Warning: It is recommended to run this script inside a virtual environment (venv).")

    # PHASE 1: Scrape rows into DB
    if not run_phase("PHASE 1: ROW SCRAPING", "run.py"):
        print("\n🛑 Pipeline halted after Phase 1 failure.")
        return

    # PHASE 2: Download PDFs for the newly scraped rows
    if not run_phase("PHASE 2: PDF DOWNLOADING", "run_phase2.py"):
        print("\n🛑 Pipeline halted after Phase 2 failure.")
        return

    # PHASE 3: Extract data from PDFs and update DB
    if not run_phase("PHASE 3: DATA EXTRACTION & ANALYSIS", "run_phase3.py"):
        print("\n🛑 Pipeline halted after Phase 3 failure.")
        return

    print("\n" + "!" * 80)
    print("🎉 ALL PHASES COMPLETED SUCCESSFULLY!")
    print("!" * 80)
    print("\nSummary:")
    print("  1. Rows Scraped & Database Initialized")
    print("  2. PDFs Downloaded to data/scrapped/")
    print("  3. Seller Details & Unit Prices Extracted & Sync'd to Database")
    print("\nYour data is now ready in the MySQL database and data/seller_info.csv")
    print("#" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Master Pipeline Interrupted by User.")
    except Exception as e:
        print(f"\n\n💥 Master Pipeline Crashed: {e}")
        import traceback
        traceback.print_exc()
