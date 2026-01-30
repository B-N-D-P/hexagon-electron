#!/usr/bin/env python3
"""
Create simple HEXAGON icon using PIL
"""

from PIL import Image, ImageDraw, ImageFont
import math

def create_hexagon_icon(size=512):
    # Create transparent image
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Calculate hexagon points
    center_x, center_y = size // 2, size // 2
    radius = size // 2 - 50
    
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        points.append((x, y))
    
    # Draw outer hexagon (blue)
    draw.polygon(points, fill='#3b82f6', outline='#1e40af')
    
    # Draw inner hexagon (dark)
    inner_radius = radius - 60
    inner_points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = center_x + inner_radius * math.cos(angle)
        y = center_y + inner_radius * math.sin(angle)
        inner_points.append((x, y))
    
    draw.polygon(inner_points, fill='#1e293b', outline='#475569')
    
    # Draw "H" text
    try:
        # Try to load a nice font
        font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 180)
    except:
        # Fallback to default
        font = ImageFont.load_default()
    
    # Draw text
    text = "H"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - 20
    
    draw.text((text_x, text_y), text, fill='#60a5fa', font=font)
    
    return img

if __name__ == "__main__":
    print("Creating HEXAGON icon...")
    
    # Create main icon
    icon = create_hexagon_icon(512)
    icon.save('hexagon-electron/resources/icon.png')
    print("✓ Icon created: hexagon-electron/resources/icon.png")
    
    # Create tray icon (smaller)
    tray_icon = create_hexagon_icon(64)
    tray_icon.save('hexagon-electron/resources/tray-icon.png')
    print("✓ Tray icon created: hexagon-electron/resources/tray-icon.png")
    
    print("✓ Icons ready!")
