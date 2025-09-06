import os
import sys
import subprocess

def check_files():
    missing = []
    for fname in ["data.csv", "modules/streamlit_app.py"]:
        if not os.path.exists(fname):
            missing.append(fname)
    if missing:
        print("\nERROR: The following required files are missing:")
        for f in missing:
            print(f"  - {f}")
        print("Please ensure all files are present before launching the app.")
        return False
    return True

if __name__ == '__main__':
    print("\n==============================")
    print(" Welcome to Personal Finance Tracker! ")
    print("==============================\n")
    print("Launching Streamlit app...")
    if not check_files():
        sys.exit(1)
    try:
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'modules/streamlit_app.py'], check=True)
    except Exception as e:
        print(f"Error launching Streamlit: {e}")