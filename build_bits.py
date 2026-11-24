"""Section header strips and tool thumbnails for the profile README, in the LiDAR palette.

    python build_bits.py <screenshot folder>
Writes header-field.svg, header-bench.svg and thumbs/*.png next to this file.
Thumbnails come from the app screenshots (made-up data, no reserve names) and the
LiDAR renders in src/ (render_relief.py).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).parent
Image.MAX_IMAGE_PIXELS = None
DEEP, TEAL, SAND, BONE, ACCENT = "#123f47", "#3d7d84", "#c5a46c", "#f1e8d2", "#e8603c"
T = 240                                   # thumbnail px (shown at 120, sharp on retina)


def lidar_slice(slug, box, w, h):
    """A thin strip of a render, fading to deep teal on the left so the title reads."""
    import base64, io
    import numpy as np
    im = Image.open(HERE / "src" / f"{slug}_full.png").convert("RGB").crop(box)
    im = im.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    a = np.clip(0.95 - np.linspace(0, 1.1, w * 2), 0.18, 0.88)
    mask = Image.fromarray((np.tile(a[None, :], (h * 2, 1)) * 255).astype(np.uint8))
    im = Image.composite(Image.new("RGB", im.size, DEEP), im, mask)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def header(title, out, slug, box):
    w, h = 1200, 56
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{title}">
<defs><clipPath id="c"><rect width="{w}" height="{h}" rx="10"/></clipPath></defs>
<g clip-path="url(#c)"><image width="{w}" height="{h}" href="data:image/jpeg;base64,{lidar_slice(slug, box, w, h)}"/></g>
<rect x="24" y="25" width="22" height="4" rx="2" fill="{ACCENT}"/>
<text x="58" y="34" font-family="'Segoe UI', -apple-system, Helvetica, Arial, sans-serif" font-size="17"
      font-weight="600" letter-spacing="3" fill="{BONE}">{title.upper()}</text>
</svg>
'''
    (HERE / out).write_text(svg, encoding="utf-8")


def rounded(im, r=36):
    im = im.convert("RGBA").resize((T, T), Image.Resampling.LANCZOS)
    m = Image.new("L", (T, T), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, T - 1, T - 1), r, fill=255)
    im.putalpha(m)
    return im


def from_shot(path, box):
    """box is (x, y, size) in the screenshot's own pixels: a square crop."""
    x, y, s = box
    return rounded(Image.open(path).crop((x, y, x + s, y + s)))


def from_render(slug, box, marker):
    im = Image.open(HERE / "src" / f"{slug}_full.png").convert("RGB")
    x, y, s = box
    im = im.crop((x, y, x + s, y + s)).resize((T, T), Image.Resampling.LANCZOS)
    if marker:                            # a flagged site: coral ring with a dot, as the report would mark it
        d = ImageDraw.Draw(im)
        cx, cy = marker
        d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), outline=ACCENT, width=5)
        d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=ACCENT)
    return rounded(im)


def main(shots):
    header("Out in the field", "header-field.svg", "duddon_mosses", (0, 1400, 3006, 1540))
    header("On the bench", "header-bench.svg", "north_walney", (0, 1600, 4023, 1788))
    out = HERE / "thumbs"
    out.mkdir(exist_ok=True)
    from_shot(shots / "fieldnotes_plain.png", (100, 1092, 900)).save(out / "fieldnotes.png", optimize=True)
    from_shot(shots / "boxcheck_3.png", (40, 520, 1090)).save(out / "boxcheck.png", optimize=True)
    from_shot(shots / "ranger_2.png", (49, 461, 1072)).save(out / "ranger.png", optimize=True)
    from_render("gait_barrows", (500, 700, 900), (130, 110)).save(out / "threat-detector.png", optimize=True)
    for f in sorted(out.iterdir()):
        print(f.name, f.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
