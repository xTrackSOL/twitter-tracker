from PIL import Image, ImageDraw, ImageFilter
import math

def create_logo(size=512):
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
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

    # Draw X symbol
    for points in x_points:
        draw.polygon(points, fill='white')

    # Draw tracking corners with glow
    for start, end, width in corners:
        # Draw the main line
        draw.line([start, end], fill=(0, 136, 204, 255), width=width)

    # Apply glow effect
    glow = img.filter(ImageFilter.GaussianBlur(radius=5))

    # Create final image with dark background
    final = Image.new('RGBA', (size, size), (15, 17, 23, 255))
    final = Image.alpha_composite(final, glow)
    final = Image.alpha_composite(final, img)

    # Save both the original and static folder
    final.save('bot_logo.png', 'PNG')
    final.save('static/images/bot_logo.png', 'PNG')
    print("Logo generated successfully!")

def create_banner(width=1500, height=500):
    """Create a Twitter banner with tracking theme"""
    # Create a new image with dark background
    img = Image.new('RGBA', (width, height), (15, 17, 23, 255))
    draw = ImageDraw.Draw(img)

    # Calculate dimensions for tracking elements
    padding = height // 8
    corner_size = height // 4
    stroke_width = height // 32

    # Define tracking corners and lines
    corners = [
        # Left side
        [(padding, padding), (padding + corner_size, padding), stroke_width],
        [(padding, padding), (padding, padding + corner_size), stroke_width],
        [(padding, height - padding), (padding, height - padding - corner_size), stroke_width],
        [(padding, height - padding), (padding + corner_size, height - padding), stroke_width],
        # Right side
        [(width - padding - corner_size, padding), (width - padding, padding), stroke_width],
        [(width - padding, padding), (width - padding, padding + corner_size), stroke_width],
        [(width - padding - corner_size, height - padding), (width - padding, height - padding), stroke_width],
        [(width - padding, height - padding - corner_size), (width - padding, height - padding), stroke_width],
    ]

    # Draw tracking corners with glow
    corner_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    corner_draw = ImageDraw.Draw(corner_layer)

    for start, end, width in corners:
        corner_draw.line([start, end], fill=(0, 136, 204, 255), width=width)

    # Add small X symbols
    x_size = height // 8
    x_positions = [(width // 4, height // 2), (width * 3 // 4, height // 2)]

    x_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    x_draw = ImageDraw.Draw(x_layer)

    for center_x, center_y in x_positions:
        x_stroke = x_size // 8
        x_points = [
            # First diagonal
            [(center_x - x_size, center_y - x_size),
             (center_x - x_size + x_stroke, center_y - x_size),
             (center_x + x_size, center_y + x_size),
             (center_x + x_size - x_stroke, center_y + x_size)],
            # Second diagonal
            [(center_x + x_size, center_y - x_size),
             (center_x + x_size - x_stroke, center_y - x_size),
             (center_x - x_size, center_y + x_size),
             (center_x - x_size + x_stroke, center_y + x_size)]
        ]
        for points in x_points:
            x_draw.polygon(points, fill=(255, 255, 255, 128))

    # Create glow effects
    corner_glow = corner_layer.filter(ImageFilter.GaussianBlur(radius=10))
    x_glow = x_layer.filter(ImageFilter.GaussianBlur(radius=5))

    # Composite all layers
    img = Image.alpha_composite(img, corner_glow)
    img = Image.alpha_composite(img, corner_layer)
    img = Image.alpha_composite(img, x_glow)
    img = Image.alpha_composite(img, x_layer)

    # Save banner
    img.save('twitter_banner.png', 'PNG')
    img.save('static/images/twitter_banner.png', 'PNG')
    print("Banner generated successfully!")

if __name__ == '__main__':
    create_logo()
    create_banner()