from PIL import Image, ImageDraw, ImageFilter
import math

def create_logo(size=512):
    # Create a new image with black background
    img = Image.new('RGBA', (size, size), (15, 17, 23, 255))  # Dark background matching website
    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    padding = size // 8
    center = size // 2
    width = size - (padding * 2)
    x_size = width // 2

    # Draw X symbol (Twitter/X logo)
    stroke_width = width // 16
    x_points = [
        # First diagonal line of X
        [(center - x_size, center - x_size),  # Top left
         (center - x_size + stroke_width, center - x_size),  # Top left inner
         (center + x_size, center + x_size),  # Bottom right
         (center + x_size - stroke_width, center + x_size)],  # Bottom right inner
        # Second diagonal line of X
        [(center + x_size, center - x_size),  # Top right
         (center + x_size - stroke_width, center - x_size),  # Top right inner
         (center - x_size, center + x_size),  # Bottom left
         (center - x_size + stroke_width, center + x_size)]  # Bottom left inner
    ]

    # Draw tracking elements (corners)
    corner_size = width // 4
    corner_stroke = stroke_width // 2
    corners = [
        # Top left
        [(padding, padding), (padding + corner_size, padding), corner_stroke],  # Horizontal
        [(padding, padding), (padding, padding + corner_size), corner_stroke],  # Vertical
        # Top right
        [(size - padding - corner_size, padding), (size - padding, padding), corner_stroke],
        [(size - padding, padding), (size - padding, padding + corner_size), corner_stroke],
        # Bottom left
        [(padding, size - padding), (padding + corner_size, size - padding), corner_stroke],
        [(padding, size - padding - corner_size), (padding, size - padding), corner_stroke],
        # Bottom right
        [(size - padding - corner_size, size - padding), (size - padding, size - padding), corner_stroke],
        [(size - padding, size - padding - corner_size), (size - padding, size - padding), corner_stroke]
    ]

    # Draw tracking corners with enhanced glow
    for start, end, width in corners:
        draw.line([start, end], fill=(0, 136, 204, 255), width=width)  # Telegram blue color

    # Draw X symbol
    for points in x_points:
        draw.polygon(points, fill='white')

    # Add glow effect
    glow = img.filter(ImageFilter.GaussianBlur(radius=5))
    img = Image.alpha_composite(img, img)

    # Add blue glow to tracking elements
    blue_glow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    blue_draw = ImageDraw.Draw(blue_glow)
    for start, end, width in corners:
        blue_draw.line([start, end], fill=(0, 136, 204, 100), width=width * 3)
    blue_glow = blue_glow.filter(ImageFilter.GaussianBlur(radius=10))
    img = Image.alpha_composite(img, blue_glow)

    # Save both the original and static folder
    img.save('bot_logo.png', 'PNG')
    img.save('static/images/bot_logo.png', 'PNG')
    print("Logo generated successfully!")

if __name__ == '__main__':
    create_logo()