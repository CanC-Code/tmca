import os
import json
import subprocess

def run():
    # 1. Setup Gradle Wrapper if missing
    android_dir = "Android"
    if not os.path.exists(os.path.join(android_dir, "gradlew")):
        print("Generating Gradle wrapper...")
        subprocess.run(["gradle", "wrapper"], cwd=android_dir, check=True)

    # 2. Generate assets.h from tmca/assets/assets.json
    assets_json = "assets/assets.json"
    output_h = "Android/app/src/main/cpp/assets.h"
    
    os.makedirs(os.path.dirname(output_h), exist_ok=True)
    
    asset_data = []
    if os.path.exists(assets_json):
        with open(assets_json, "r") as f:
            data = json.load(f)
            # Assuming tmca assets.json format
            for asset in data.get("assets", []):
                name = asset.get("name", "unknown").replace(".", "_").replace("/", "_")
                asset_data.append(f'    {{"{name}", {asset.get("start", 0)}, {asset.get("size", 0)}}}')
    
    with open(output_h, "w") as f:
        f.write("#ifndef ASSETS_H\n#define ASSETS_H\n\n")
        f.write("typedef struct { const char* name; int offset; int size; } AssetMetadata;\n\n")
        f.write("static const AssetMetadata g_AssetTable[] = {\n")
        if asset_data:
            f.write(",\n".join(asset_data))
        else:
            f.write('    {"dummy", 0, 0}\n')
        f.write("\n};\n\n")
        f.write(f"#define ASSET_COUNT {max(len(asset_data), 1)}\n\n")
        f.write("#endif")
    print(f"Generated {output_h}")

if __name__ == "__main__":
    run()
