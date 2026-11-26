"""Build transparent Inter nameplates: python3 build_assets.py.

Requires Pillow. The bundled Inter font is licensed under SIL OFL; see
assets/fonts/OFL.txt. Technology marks in images/tech are real Simple Icons
SVGs, with no background rectangles or third-party badge services.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'images'
FONT = ROOT / 'assets/fonts/InterVariable.ttf'
SCALE = 2


def font(size, weight=400):
    face = ImageFont.truetype(str(FONT), round(size * SCALE))
    face.set_variation_by_axes([32 if size >= 32 else 14, weight])
    return face


def build(theme, mobile=False):
    dark = theme == 'dark'
    ink = '#F0F6FC' if dark else '#1F2328'
    muted = '#9CAABD' if dark else '#59636E'
    blue = '#91BAFA' if dark else '#2765B4'
    w, h = (600, 192) if mobile else (1200, 188)
    image = Image.new('RGBA', (w * SCALE, h * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size, color, weight=400, anchor='lt'):
        draw.text((x * SCALE, y * SCALE), value, font=font(size, weight),
                  fill=color, anchor=anchor)

    if mobile:
        text(0, 24, 'Dimath Jayasinghe', 56, ink, 650)
        text(1, 111, 'Backend & systems engineer', 27, blue, 450)
        text(1, 162, 'UCSC, University of Colombo · Sri Lanka', 20, muted)
    else:
        text(0, 32, 'Dimath Jayasinghe', 70, ink, 650)
        text(2, 135, 'Backend & systems engineer', 28, blue, 450)
        text(w - 1, 65, 'University of Colombo', 21, ink, 500, 'rt')
        text(w - 1, 104, 'Computer Science undergraduate', 18, muted, anchor='rt')
        text(w - 1, 140, 'Colombo, Sri Lanka', 18, muted, anchor='rt')
    path = OUT / f'profile-{theme}{"-mobile" if mobile else ""}.png'
    image.save(path, optimize=True)
    assert image.mode == 'RGBA' and image.getpixel((0, 0))[3] == 0
    print(f'Built {path.relative_to(ROOT)} (transparent, Inter)')


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    for theme in ('light', 'dark'):
        build(theme)
        build(theme, mobile=True)
