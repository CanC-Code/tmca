import os
import json
import subprocess

def run():
    # 1. Setup Gradle Wrapper with a version compatible with Java 17
    android_dir = "Android"
    if not os.path.exists(os.path.join(android_dir, "gradlew")):
        print("Generating Gradle 8.5 wrapper...")
        # Using --gradle-version 8.5 ensures compatibility with Java 17
        subprocess.run(["gradle", "wrapper", "--gradle-version", "8.5", "--quiet"], cwd=android_dir, check=True)

    # 2. Generate assets.h
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
                start = asset.get("start", 0)
                size = asset.get("size", 0)
                asset_entries.append(f'    {{"{name}", {hex(start)}, {size}}}')
    
    with open(output_h, "w") as f:
        f.write("/* GENERATED FILE - DO NOT EDIT */\n")
        f.write("#ifndef ASSETS_H\n#define ASSETS_H\n\n")
        f.write("typedef struct { const char* name; int offset; int size; } AssetMetadata;\n\n")
        f.write("static const AssetMetadata g_AssetTable[] = {\n")
        if asset_entries:
            f.write(",\n".join(asset_entries))
        else:
            f.write('    {"dummy", 0, 0}')
        f.write("\n};\n\n")
        f.write(f"#define ASSET_COUNT {max(len(asset_entries), 1)}\n\n")
        f.write("#endif\n")
    print(f"Generated {output_h} with {len(asset_entries)} entries.")

if __name__ == "__main__":
    run()
