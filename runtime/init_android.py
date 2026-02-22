import os
import subprocess

def setup_gradle():
    android_dir = "Android"
    if not os.path.exists(android_dir):
        print("Android directory not found!")
        return

    print("Generating Gradle Wrapper...")
    # This uses the system gradle installed in the GitHub runner 
    # to create the local wrapper for the project
    try:
        subprocess.run(["gradle", "wrapper"], cwd=android_dir, check=True)
        print("Gradle wrapper generated successfully.")
    except Exception as e:
        print(f"Failed to generate wrapper: {e}")

if __name__ == "__main__":
    setup_gradle()
