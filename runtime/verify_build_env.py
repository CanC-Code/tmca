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
    for f in REQUIRED_FILES:
        full_path = os.path.join("..", f)
        if os.path.exists(full_path):
            print(f"[OK] Found {f}")
        else:
            print(f"[ERROR] Missing {f}")
            missing = True
    
    if missing:
        print("\nFix: Ensure all summarized CMake and Header files are placed correctly.")
        sys.exit(1)
    print("--- Environment Ready ---\n")

if __name__ == "__main__":
    check_env()
