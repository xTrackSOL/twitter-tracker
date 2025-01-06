from PIL import Image, ImageDraw, ImageFilter
import math

def create_logo(size=512):
    # Create a new image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    padding = size // 8
    center = size // 2
    width = size - (padding * 2)
    stroke_width = width // 8

    # Draw X shape
    points_left = [
        (padding, padding),  # Top left
        (padding + stroke_width, padding),  # Top left inner
        (center + stroke_width/2, center),  # Center right
        (size - padding, size - padding),  # Bottom right
        (size - padding - stroke_width, size - padding),  # Bottom right inner
        (center - stroke_width/2, center),  # Center left
    ]

    points_right = [
        (size - padding, padding),  # Top right
        (size - padding - stroke_width, padding),  # Top right inner
        (center + stroke_width/2, center),  # Center right
        (padding, size - padding),  # Bottom left
        (padding + stroke_width, size - padding),  # Bottom left inner
        (center - stroke_width/2, center),  # Center left
    ]

    # Draw the X with white color
    draw.polygon(points_left, fill='white')
    draw.polygon(points_right, fill='white')

    # Add glow effect
    glow = img.filter(ImageFilter.GaussianBlur(radius=3))
    img = Image.alpha_composite(glow, img)

    # Save both the original and static folder
    img.save('bot_logo.png', 'PNG')
    img.save('static/images/bot_logo.png', 'PNG')
    print("Logo generated successfully!")

if __name__ == '__main__':
    create_logo()