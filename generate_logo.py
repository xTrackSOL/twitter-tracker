from PIL import Image, ImageDraw, ImageFilter
import math

def create_logo(size=512):
    # Create a new image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Discord blurple color
    blurple = (88, 101, 242)

    # Draw circular background with gradient
    padding = size // 8
    center = size // 2
    radius = (size - padding * 2) // 2

    # Create gradient background
    for r in range(radius + 10):
        alpha = int(255 * (1 - (r / radius) ** 2))
        if alpha < 0:
            alpha = 0
        color = (*blurple, alpha)
        draw.ellipse(
            [center - r, center - r, center + r, center + r],
            outline=color
        )

    # Draw stylized Twitter bird
    bird_points = [
        (center - radius//2, center + radius//4),      # Left base
        (center - radius//3, center),                  # Left curve
        (center - radius//4, center - radius//3),      # Left wing
        (center, center - radius//2),                  # Head
        (center + radius//4, center - radius//3),      # Right wing
        (center + radius//3, center),                  # Right curve
        (center + radius//2, center + radius//4),      # Right base
        (center, center + radius//3),                  # Tail
    ]

    # Draw bird with anti-aliasing
    draw.polygon(bird_points, fill='white')

    # Add glow effect
    glow = img.filter(ImageFilter.GaussianBlur(radius=3))
    img = Image.alpha_composite(glow, img)

    # Add subtle shine
    shine_points = [
        (center - radius//6, center - radius//3),
        (center - radius//8, center - radius//2),
        (center, center - radius//2.5),
    ]
    draw = ImageDraw.Draw(img)
    draw.polygon(shine_points, fill=(255, 255, 255, 80))

    # Save the logo
    img.save('bot_logo.png', 'PNG')
    print("Logo generated successfully!")

if __name__ == '__main__':
    create_logo()