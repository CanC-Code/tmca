#!/bin/bash
# Configuration
BASE_IMAGE="runtime/icon_base.png"
RES_DIR="Android/app/src/main/res"

# 1. Create a professional placeholder if no base image exists
if [ ! -f "$BASE_IMAGE" ]; then
    echo "Creating placeholder icon..."
    mkdir -p runtime
    magick -size 512x512 gradient:#4facfe-#00f2fe \
           -fill white -font Courier-Bold -pointsize 150 -gravity center \
           -annotate +0+0 "NDK" \
           "$BASE_IMAGE"
fi

# 2. Generate required Android densities
declare -a SIZES=("mipmap-mdpi:48x48" "mipmap-hdpi:72x72" "mipmap-xhdpi:96x96" "mipmap-xxhdpi:144x144" "mipmap-xxxhdpi:192x192")

for entry in "${SIZES[@]}"; do
    DIR_NAME="${entry%%:*}"
    SIZE="${entry#*:}"
    TARGET_DIR="$RES_DIR/$DIR_NAME"
    mkdir -p "$TARGET_DIR"
    magick "$BASE_IMAGE" -resize "$SIZE" "$TARGET_DIR/ic_launcher.png"
    echo "Created $TARGET_DIR/ic_launcher.png ($SIZE)"
done
