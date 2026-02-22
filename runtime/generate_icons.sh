#!/bin/bash

# Configuration - Ensure these paths match your repo structure
BASE_IMAGE="runtime/icon_base.png"
# This path must lead to the actual Android app resource folder
RES_DIR="Android/app/src/main/res"

# 1. Create a master icon if it doesn't exist
if [ ! -f "$BASE_IMAGE" ]; then
    echo "Creating placeholder master icon..."
    mkdir -p runtime
    magick -size 512x512 gradient:#4facfe-#00f2fe \
           -fill white -font Courier-Bold -pointsize 150 -gravity center \
           -annotate +0+0 "NDK" \
           "$BASE_IMAGE"
fi

# 2. Map of directory names to pixel sizes
declare -a SIZES=(
    "mipmap-mdpi:48x48"
    "mipmap-hdpi:72x72"
    "mipmap-xhdpi:96x96"
    "mipmap-xxhdpi:144x144"
    "mipmap-xxxhdpi:192x192"
)

# 3. Generate the icons
echo "Generating Android icons in $RES_DIR..."
for entry in "${SIZES[@]}"; do
    DIR_NAME="${entry%%:*}"
    SIZE="${entry#*:}"
    TARGET_PATH="$RES_DIR/$DIR_NAME"
    
    mkdir -p "$TARGET_PATH"
    # MUST be named ic_launcher.png to match AndroidManifest.xml
    magick "$BASE_IMAGE" -resize "$SIZE" "$TARGET_PATH/ic_launcher.png"
    echo "  > Created $DIR_NAME/ic_launcher.png"
done

echo "Icon generation complete."
