#!/bin/bash
# Create HEXAGON icons using ImageMagick

echo "Creating HEXAGON icons..."

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "ImageMagick not found. Installing..."
    sudo pacman -S imagemagick --noconfirm
fi

# Create a simple hexagon icon using ImageMagick
convert -size 512x512 xc:transparent \
    -fill "#3b82f6" \
    -draw "polygon 256,50 450,156 450,356 256,462 62,356 62,156" \
    -fill "#1e293b" \
    -draw "polygon 256,100 400,180 400,332 256,412 112,332 112,180" \
    -fill "#60a5fa" \
    -font "DejaVu-Sans-Bold" -pointsize 120 -gravity center \
    -annotate +0+0 "H" \
    hexagon-electron/resources/icon.png

# Copy for tray
cp hexagon-electron/resources/icon.png hexagon-electron/resources/tray-icon.png

echo "✓ Icons created!"
