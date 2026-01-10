import subprocess
import sys


def run_script(script_name):
    print("\n" + "=" * 70)
    print(f"🚀 RUNNING → {script_name}")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, script_name],
        check=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"{script_name} failed")


def main():
    try:
        # PHASE 1
        run_script("run.py")

        # PHASE 2
        run_script("run_phase2.py")

        print("\n" + "=" * 70)
        print("🎉 ALL PHASES COMPLETED SUCCESSFULLY")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")

    except Exception as e:
        print(f"\n❌ Critical error: {e}")


if __name__ == "__main__":
    main()
