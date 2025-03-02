#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw, ImageFont
import math

def create_icon(name, text, color, size=(128, 128), output_dir='icons'):
    """Create a simple icon with text"""
    # Create image with background color
    img = Image.new('RGBA', size, color)
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 32)
    except IOError:
        font = ImageFont.load_default()
    
    # Calculate text position to center it
    # Using getbbox instead of deprecated textsize
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)
    
    # Draw text
    draw.text(position, text, fill='white', font=font)
    
    # Save image
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    img.save(os.path.join(output_dir, f"{name}.png"))
    print(f"Created icon: {name}.png")

def create_app_icon(output_dir='icons'):
    """Create the main application icon"""
    size = (128, 128)
    img = Image.new('RGBA', size, '#5E81AC')
    draw = ImageDraw.Draw(img)
    
    # Draw a grid of buttons
    margin = 20
    button_size = (size[0] - 2 * margin) // 2
    spacing = 8
    
    colors = ['#88C0D0', '#A3BE8C', '#EBCB8B', '#BF616A']
    
    for i in range(2):
        for j in range(2):
            x = margin + j * (button_size + spacing)
            y = margin + i * (button_size + spacing)
            
            # Draw button
            color_index = i * 2 + j
            draw.rectangle(
                [x, y, x + button_size, y + button_size],
                fill=colors[color_index],
                outline='white',
                width=2
            )
    
    # Save image
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    img.save(os.path.join(output_dir, "app-icon.png"))
    print(f"Created app icon: app-icon.png")

def main():
    # Create sample icons for buttons
    create_icon("terminal", "T", "#88C0D0")
    create_icon("browser", "B", "#5E81AC")
    create_icon("files", "F", "#A3BE8C")
    create_icon("monitor", "M", "#B48EAD")
    create_icon("reboot", "R", "#BF616A")
    create_icon("shutdown", "S", "#D08770")
    
    # Create app icon
    create_app_icon()
    
    print("All icons created successfully!")

if __name__ == "__main__":
    main() 