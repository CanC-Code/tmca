import os
import json
import subprocess

def run():
    android_dir = "Android"
    
    # 1. Create settings.gradle if missing to define project structure
    settings_path = os.path.join(android_dir, "settings.gradle")
    if not os.path.exists(settings_path):
        with open(settings_path, "w") as f:
            f.write("rootProject.name = 'MinishNDK'\ninclude ':app'\n")
        print("Generated settings.gradle")

    # 2. Setup Gradle Wrapper - Use --no-daemon and avoid full project evaluation
    if not os.path.exists(os.path.join(android_dir, "gradlew")):
        print("Bootstrapping Gradle 8.5 wrapper...")
        # We use '-p' to point to the directory but avoid triggering full plugin loads
        subprocess.run([
            "gradle", "wrapper", 
            "--gradle-version", "8.5", 
            "--no-daemon"
        ], cwd=android_dir, check=True)

    # 3. Generate assets.h
    assets_json = "assets/assets.json"
    output_h = "Android/app/src/main/cpp/assets.h"
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
