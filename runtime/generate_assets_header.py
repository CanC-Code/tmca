import os
import json
import subprocess
import shutil

def run():
    android_dir = "Android"

    # 1. Create settings.gradle if missing in the main Android dir
    settings_path = os.path.join(android_dir, "settings.gradle")
    if not os.path.exists(settings_path):
        os.makedirs(android_dir, exist_ok=True)
        with open(settings_path, "w") as f:
            f.write("rootProject.name = 'MinishNDK'\ninclude ':app'\n")
        print("Generated settings.gradle")

    # 2. Setup Gradle Wrapper using a 'Clean Room' approach
    if not os.path.exists(os.path.join(android_dir, "gradlew")):
        print("Bootstrapping Gradle 8.5 wrapper (isolated)...")
        temp_dir = "gradle_bootstrap"
        os.makedirs(temp_dir, exist_ok=True)

        # FIX: Create a dummy settings file in the temp dir so Gradle identifies it as a project
        with open(os.path.join(temp_dir, "settings.gradle"), "w") as f:
            f.write("// Bootstrap settings")

        # Generate wrapper in the temp directory
        subprocess.run([
            "gradle", "wrapper", 
            "--gradle-version", "8.5", 
            "--no-daemon"
        ], cwd=temp_dir, check=True)

        # Move generated files to Android directory
        for item in ["gradlew", "gradlew.bat", "gradle"]:
            src = os.path.join(temp_dir, item)
            dst = os.path.join(android_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst): shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        shutil.rmtree(temp_dir)
        print("Wrapper successfully isolated and moved.")

    # 3. Generate assets.h
    assets_json = "assets/assets.json"
    output_h = os.path.join(android_dir, "app/src/main/cpp/assets.h")
    os.makedirs(os.path.dirname(output_h), exist_ok=True)

    asset_entries = []
    if os.path.exists(assets_json):
        with open(assets_json, "r") as f:
            data = json.load(f)
            items = data if isinstance(data, list) else data.get("assets", [])
            for asset in items:
                name = asset.get("name", "unknown").replace(".", "_").replace("/", "_")
                asset_entries.append(f'    {{"{name}", {hex(asset.get("start", 0))}, {asset.get("size", 0)}}}')

    with open(output_h, "w") as f:
        f.write("#ifndef ASSETS_H\n#define ASSETS_H\n\n")
        f.write("typedef struct { const char* name; int offset; int size; } AssetMetadata;\n\n")
        f.write("static const AssetMetadata g_AssetTable[] = {\n")
        f.write(",\n".join(asset_entries) if asset_entries else '    {"dummy", 0, 0}')
        f.write("\n};\n\n")
        f.write(f"#define ASSET_COUNT {max(len(asset_entries), 1)}\n\n")
        f.write("#endif")
    print(f"Generated {output_h}")

if __name__ == "__main__":
    run()
