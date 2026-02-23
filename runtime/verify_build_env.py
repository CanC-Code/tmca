import sys
import os

REQUIRED_FILES = [
    "include/android_compat.h",
    "include/global.h",
    "tools/src/asset_processor/CMakeLists.txt",
    "Android/app/src/main/cpp/CMakeLists.txt"
]

def check_env():
    print("--- Verifying Build Environment ---")
    missing = False
    
    # Get the root directory (current working directory in GitHub Actions)
    root_dir = os.getcwd()
    
    for f in REQUIRED_FILES:
        # Look for the file relative to the root, not the parent of the root
        full_path = os.path.join(root_dir, f)
        
        if os.path.exists(full_path):
            print(f"[OK] Found {f}")
        else:
            print(f"[ERROR] Missing {f}")
            missing = True

    if missing:
        print("\nFix: Ensure files are committed to the repository at the correct paths.")
        sys.exit(1)
    print("--- Environment Ready ---\n")

if __name__ == "__main__":
    check_env()
