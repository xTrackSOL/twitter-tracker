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
    img = Image.alpha_composite(img, glow)

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

def create_banner(width=1500, height=500):
    """Create a Twitter banner with tracking theme"""
    # Create a new image with black background
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

    # Draw tracking grid lines
    grid_spacing = height // 8
    num_lines = width // grid_spacing
    for i in range(1, num_lines):
        x = i * grid_spacing
        draw.line([(x, 0), (x, height)], fill=(0, 136, 204, 30), width=1)

    # Draw tracking corners with enhanced glow
    for start, end, width in corners:
        draw.line([start, end], fill=(0, 136, 204, 255), width=width)

    # Create glow effect on a separate image with same dimensions
    glow_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)

    # Draw the same elements on glow image
    for start, end, width in corners:
        glow_draw.line([start, end], fill=(0, 136, 204, 255), width=width)

    # Apply blur to glow image
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=5))

    # Composite the images
    img = Image.alpha_composite(img, glow_img)

    # Add blue glow to tracking elements
    blue_glow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    blue_draw = ImageDraw.Draw(blue_glow)
    for start, end, width in corners:
        blue_draw.line([start, end], fill=(0, 136, 204, 100), width=width * 3)
    blue_glow = blue_glow.filter(ImageFilter.GaussianBlur(radius=15))
    img = Image.alpha_composite(img, blue_glow)

    # Add small logos as decorative elements
    logo_size = height // 4
    logo_positions = [
        (width // 4 - logo_size // 2, height // 2 - logo_size // 2),
        (width * 3 // 4 - logo_size // 2, height // 2 - logo_size // 2)
    ]

    # Create and paste small X symbols
    for pos_x, pos_y in logo_positions:
        x_size = logo_size // 3
        center_x = pos_x + logo_size // 2
        center_y = pos_y + logo_size // 2

        x_points = [
            # First diagonal
            [(center_x - x_size, center_y - x_size),
             (center_x - x_size + stroke_width, center_y - x_size),
             (center_x + x_size, center_y + x_size),
             (center_x + x_size - stroke_width, center_y + x_size)],
            # Second diagonal
            [(center_x + x_size, center_y - x_size),
             (center_x + x_size - stroke_width, center_y - x_size),
             (center_x - x_size, center_y + x_size),
             (center_x - x_size + stroke_width, center_y + x_size)]
        ]

        for points in x_points:
            draw.polygon(points, fill=(255, 255, 255, 128))

    # Save banner
    img.save('twitter_banner.png', 'PNG')
    img.save('static/images/twitter_banner.png', 'PNG')
    print("Banner generated successfully!")

if __name__ == '__main__':
    create_logo()
    create_banner()