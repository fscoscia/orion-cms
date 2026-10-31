"""Generate the sample images that block previews use in the editor.

They are Orion's own work: abstract landscapes in the theme's colors and generic logos,
so they carry no third-party license. Run from the repository root:

    pipenv run python scripts/make_sample_images.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

OUTPUT_DIR = Path("src/orion/core/static/orion/samples")
SKY = ("#d7f2ee", "#b0e5dd")
HILLS = ("#7fd1c6", "#45b5a9", "#1f9a8e", "#15645d", "#16433f")
SUN = "#f2734f"

# (file name, size, hill shapes as (height ratio, wave offset), sun position)
LANDSCAPES = [
    ("landscape-1.webp", (1600, 900), (0.55, 0.0), (0.72, 0.28)),
    ("landscape-2.webp", (1600, 900), (0.62, 0.35), (0.22, 0.32)),
    ("landscape-3.webp", (800, 800), (0.58, 0.7), (0.5, 0.3)),
]

LOGOS = {
    "logo-1.svg": '<circle cx="24" cy="24" r="16"/>',
    "logo-2.svg": '<rect x="8" y="8" width="32" height="32" rx="6"/>',
    "logo-3.svg": '<path d="M24 6 42 40H6Z"/>',
    "logo-4.svg": '<path d="M24 6a18 18 0 1 0 0 36V6Z"/>',
}
LOGO_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="48" '
    'viewBox="0 0 200 48" fill="#52606d">{shape}'
    '<rect x="56" y="14" width="{width}" height="8" rx="4"/>'
    '<rect x="56" y="28" width="{short}" height="6" rx="3"/></svg>\n'
)


def landscape(size, hill_shape, sun_position):
    width, height = size
    image = Image.new("RGB", size, SKY[0])
    draw = ImageDraw.Draw(image)
    for row in range(height):
        # A vertical sky gradient, lighter at the top.
        ratio = row / height
        top, bottom = (
            Image.new("RGB", (1, 1), color).getpixel((0, 0)) for color in SKY
        )
        color = tuple(
            round(a + (b - a) * ratio) for a, b in zip(top, bottom, strict=True)
        )
        draw.line([(0, row), (width, row)], fill=color)
    sun_x, sun_y = sun_position
    radius = height * 0.09
    draw.ellipse(
        [
            width * sun_x - radius,
            height * sun_y - radius,
            width * sun_x + radius,
            height * sun_y + radius,
        ],
        fill=SUN,
    )
    base, offset = hill_shape
    for index, color in enumerate(HILLS):
        level = height * (base + index * 0.09)
        points = [(0, height)]
        for step in range(0, 33):
            x = width * step / 32
            wave = ((step + index * 3 + offset * 10) % 8) / 8
            points.append((x, level - height * 0.08 * abs(wave - 0.5) * 2))
        points.append((width, height))
        draw.polygon(points, fill=color)
    return image


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, size, hill_shape, sun_position in LANDSCAPES:
        landscape(size, hill_shape, sun_position).save(
            OUTPUT_DIR / name, "WEBP", quality=70, method=6
        )
    for index, (name, shape) in enumerate(LOGOS.items()):
        (OUTPUT_DIR / name).write_text(
            LOGO_TEMPLATE.format(shape=shape, width=110 - index * 10, short=70)
        )


if __name__ == "__main__":
    main()
