#!/bin/bash

# Configuration
BASE_IMAGE="runtime/icon_base.png"
RES_DIR="Android/app/src/main/res"

# 1. Create the base image if it's missing
if [ ! -f "$BASE_IMAGE" ]; then
    echo "Base image not found. Creating a professional placeholder..."
    mkdir -p runtime
    
    # Creates a 512x512 icon with a gradient background, a border, and centered text
    magick -size 512x512 gradient:#4facfe-#00f2fe \
           -fill none -stroke white -strokewidth 20 -draw "rectangle 10,10 502,502" \
           -fill white -font Courier-Bold -pointsize 150 -gravity center \
           -annotate +0+0 "NDK" \
           "$BASE_IMAGE"
    echo "Generated $BASE_IMAGE"
fi

# 2. Define Android icon sizes
# Format: "directory_name:pixel_size"
declare -a SIZES=(
    "mipmap-mdpi:48x48"
    "mipmap-hdpi:72x72"
    "mipmap-xhdpi:96x96"
    "mipmap-xxhdpi:144x144"
    "mipmap-xxxhdpi:192x192"
)

# 3. Generate the actual Android resources
echo "Generating Android icon resources..."
for entry in "${SIZES[@]}"; do
    DIR_NAME="${entry%%:*}"
    SIZE="${entry#*:}"
    TARGET_DIR="$RES_DIR/$DIR_NAME"
    
    mkdir -p "$TARGET_DIR"
    
    # Generate the png file
    magick "$BASE_IMAGE" -resize "$SIZE" "$TARGET_DIR/ic_launcher.png"
    echo "  > Created $TARGET_DIR/ic_launcher.png ($SIZE)"
done

echo "Success: All icons created."
