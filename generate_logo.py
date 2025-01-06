from PIL import Image, ImageDraw, ImageFilter

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

    # Draw X symbol
    for points in x_points:
        draw.polygon(points, fill='white')

    # Draw tracking corners
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

    # Draw tracking corners with glow
    for start, end, width in corners:
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
    # Create base image with dark background
    base = Image.new('RGBA', (width, height), (15, 17, 23, 255))

    # Create separate layer for tracking elements
    tracking = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    track_draw = ImageDraw.Draw(tracking)

    # Calculate dimensions
    padding = height // 8
    corner_size = height // 4
    stroke_width = height // 32

    # Draw tracking corners
    corners = [
        # Left side
        [(padding, padding), (padding + corner_size, padding)],
        [(padding, padding), (padding, padding + corner_size)],
        [(padding, height - padding), (padding + corner_size, height - padding)],
        [(padding, height - padding - corner_size), (padding, height - padding)],
        # Right side
        [(width - padding - corner_size, padding), (width - padding, padding)],
        [(width - padding, padding), (width - padding, padding + corner_size)],
        [(width - padding - corner_size, height - padding), (width - padding, height - padding)],
        [(width - padding, height - padding - corner_size), (width - padding, height - padding)]
    ]

    # Draw corner lines
    for start, end in corners:
        track_draw.line([start, end], fill=(0, 136, 204, 255), width=stroke_width)

    # Create glow effect for tracking
    tracking_glow = tracking.filter(ImageFilter.GaussianBlur(radius=10))

    # Create X symbols layer
    x_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    x_draw = ImageDraw.Draw(x_layer)

    # Add X symbols
    x_positions = [(width // 4, height // 2), (width * 3 // 4, height // 2)]
    x_size = height // 8

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

    # Create X symbols glow
    x_glow = x_layer.filter(ImageFilter.GaussianBlur(radius=5))

    # Compose all layers
    result = Image.alpha_composite(base, tracking_glow)
    result = Image.alpha_composite(result, tracking)
    result = Image.alpha_composite(result, x_glow)
    result = Image.alpha_composite(result, x_layer)

    # Save banner
    result.save('twitter_banner.png', 'PNG')
    result.save('static/images/twitter_banner.png', 'PNG')
    print("Banner generated successfully!")

if __name__ == '__main__':
    create_logo()
    create_banner()