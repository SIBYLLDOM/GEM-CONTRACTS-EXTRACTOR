from playwright_manager import PlaywrightManager
from controller.pdfdownload import PDFDownloader


def main():
    print("=" * 70)
    print("📥 GeM Contracts PDF Download System (PHASE-2)")
    print("=" * 70)

    print("\n[INIT] Launching browser...")
    browser = PlaywrightManager(headless=False)
    browser.start()

    try:
        downloader = PDFDownloader(browser)
        downloader.run()   # ✅ CORRECT METHOD

        print("\n" + "=" * 70)
        print("🎉 PHASE-2 COMPLETED")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        input("\nPress ENTER to close browser...")
        browser.stop()


if __name__ == "__main__":
    main()
