#!/bin/bash

# Configuration
BASE_IMAGE="runtime/icon_base.png"
RES_DIR="Android/app/src/main/res"

# 1. Determine which ImageMagick command to use
if command -v magick >/dev/null 2>&1; then
    IMG_TOOL="magick"
elif command -v convert >/dev/null 2>&1; then
    IMG_TOOL="convert"
else
    echo "Error: ImageMagick is not installed. Please install it with 'sudo apt-get install imagemagick'"
    exit 1
fi

echo "Using ImageMagick tool: $IMG_TOOL"

# 2. Create a master icon if it doesn't exist
if [ ! -f "$BASE_IMAGE" ]; then
    echo "Creating placeholder master icon..."
    mkdir -p runtime
    # Using $IMG_TOOL to ensure compatibility
    $IMG_TOOL -size 512x512 gradient:#4facfe-#00f2fe \
           -fill white -gravity center -pointsize 150 \
           -draw "text 0,0 'NDK'" \
           "$BASE_IMAGE"
fi

# 3. Map of directory names to pixel sizes
declare -a SIZES=(
    "mipmap-mdpi:48x48"
    "mipmap-hdpi:72x72"
    "mipmap-xhdpi:96x96"
    "mipmap-xxhdpi:144x144"
    "mipmap-xxxhdpi:192x192"
)

# 4. Generate the icons
echo "Generating Android icons in $RES_DIR..."
for entry in "${SIZES[@]}"; do
    DIR_NAME="${entry%%:*}"
    SIZE="${entry#*:}"
    TARGET_PATH="$RES_DIR/$DIR_NAME"
    
    mkdir -p "$TARGET_PATH"
    # MUST be named ic_launcher.png
    $IMG_TOOL "$BASE_IMAGE" -resize "$SIZE" "$TARGET_PATH/ic_launcher.png"
    echo "  > Created $DIR_NAME/ic_launcher.png"
done

echo "Icon generation complete."
