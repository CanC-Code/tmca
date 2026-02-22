#!/bin/bash

# Configuration
BASE_IMAGE="runtime/icon_base.png"
RES_DIR="Android/app/src/main/res"

if [ ! -f "$BASE_IMAGE" ]; then
    echo "Error: Base image $BASE_IMAGE not found."
    exit 1
fi

# Array of directory suffixes and their respective sizes
# Format: "suffix:size"
declare -a SIZES=(
    "mipmap-mdpi:48x48"
    "mipmap-hdpi:72x72"
    "mipmap-xhdpi:96x96"
    "mipmap-xxhdpi:144x144"
    "mipmap-xxxhdpi:192x192"
)

echo "Generating Android icons..."

for entry in "${SIZES[@]}"; do
    DIR_NAME="${entry%%:*}"
    SIZE="${entry#*:}"
    
    TARGET_DIR="$RES_DIR/$DIR_NAME"
    mkdir -p "$TARGET_DIR"
    
    # Convert command (ImageMagick 7 uses 'magick', older versions use 'convert')
    convert "$BASE_IMAGE" -resize "$SIZE" "$TARGET_DIR/ic_launcher.png"
    
    echo "Created $TARGET_DIR/ic_launcher.png ($SIZE)"
done

echo "Icon generation complete."
