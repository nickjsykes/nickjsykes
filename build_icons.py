"""Icons for the 'On the bench' projects: a rounded tile of washed-out LiDAR with a line drawing on top.

    python build_icons.py
Writes icons/canopy.svg, icons/warden.svg, icons/mothcam.svg next to this file.
"""
import base64, io
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
Image.MAX_IMAGE_PIXELS = None
S = 240
DEEP, BONE, SAND, ACCENT = (18, 63, 71), "#f1e8d2", "#c5a46c", "#e8603c"


def texture(slug, box, wash=0.72):
    im = Image.open(HERE / "src" / f"{slug}_full.png").convert("RGB").crop(box).resize((S, S), Image.Resampling.LANCZOS)
    im = Image.blend(im, Image.new("RGB", (S, S), DEEP), wash)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def tile(name, slug, box, drawing, wash=0.72):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}" role="img" aria-label="{name}">
<defs><clipPath id="c"><rect width="{S}" height="{S}" rx="36"/></clipPath></defs>
<g clip-path="url(#c)"><image width="{S}" height="{S}" href="data:image/jpeg;base64,{texture(slug, box, wash)}"/></g>
<g fill="none" stroke="{BONE}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round">{drawing}</g>
</svg>
'''
    (HERE / "icons").mkdir(exist_ok=True)
    (HERE / "icons" / f"{name}.svg").write_text(svg, encoding="utf-8")


def photo_tile(name, path, box):
    """A real project photo, square-cropped, rounded like the app thumbnails."""
    from PIL import ImageDraw, ImageOps
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    x, y, side = box
    im = im.crop((x, y, x + side, y + side)).resize((S, S), Image.Resampling.LANCZOS).convert("RGBA")
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, S - 1, S - 1), 36, fill=255)
    im.putalpha(m)
    (HERE / "icons").mkdir(exist_ok=True)
    im.save(HERE / "icons" / f"{name}.png", optimize=True)


# Warden: full-colour LiDAR like the banner, with two coral alerts: things that need a human to look
WARDEN = f'''
<circle cx="160" cy="92" r="22" stroke="{ACCENT}" stroke-width="7"/>
<circle cx="160" cy="92" r="6.5" fill="{ACCENT}" stroke="none"/>
<circle cx="84" cy="158" r="15" stroke="{ACCENT}" stroke-width="6"/>
<circle cx="84" cy="158" r="4.5" fill="{ACCENT}" stroke="none"/>'''


# MothCam: night over the moss, a warm glow where the trap's light sits, moths drawn in towards it
def moth(x, y, a, s=1.0):
    return (f'<path transform="translate({x},{y}) rotate({a}) scale({s})" '
            f'd="M0,-13 C5,-6 15,2 17,10 C9,9 3,8 0,4 C-3,8 -9,9 -17,10 C-15,2 -5,-6 0,-13 Z" '
            f'fill="{BONE}" stroke="none" opacity="0.95"/>')


MOTHCAM = f'''
<defs><radialGradient id="glow"><stop offset="0" stop-color="#fff4d8" stop-opacity="0.95"/>
<stop offset="0.25" stop-color="#f3c98a" stop-opacity="0.55"/><stop offset="1" stop-color="#f3c98a" stop-opacity="0"/></radialGradient></defs>
<circle cx="120" cy="128" r="96" fill="url(#glow)" stroke="none"/>
<circle cx="120" cy="128" r="11" fill="#fffaf0" stroke="none"/>
{moth(74, 90, 45, 1.25)}{moth(166, 86, -40, 1.1)}{moth(168, 168, -130, 1.0)}{moth(76, 170, 130, 0.95)}'''


if __name__ == "__main__":
    # Canopy: the radio model from the Wellhouse Wood planning: predicted link quality over the hillshade
    photo_tile("canopy", r"C:\Dev\SLRSG\Wood 1 - Wellhouse Wood\Planning before the visit\03_radio_model.png", (130, 230, 660))
    tile("warden", "roudsea", (900, 1000, 2000, 2100), WARDEN, wash=0.0)
    tile("mothcam", "duddon_mosses", (1500, 2200, 2300, 3000), MOTHCAM, wash=0.86)
    for f in sorted((HERE / "icons").iterdir()):
        print(f.name, f.stat().st_size // 1024, "KB")
