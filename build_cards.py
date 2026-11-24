"""Social preview cards (1280x640) for the public repos: dark LiDAR of Roudsea, app name, one line, a phone.

Upload each by hand: repo -> Settings -> General -> Social preview -> Edit -> Upload an image.
    C:/Dev/Terra/.venv/Scripts/python.exe build_cards.py <screenshot folder>
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import build_banner as bb  # noqa: E402

CW, CH = 1280, 640
FONT_B = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_R = r"C:\Windows\Fonts\segoeui.ttf"
CARDS = [
    ("fieldnotes", "Field Notes", "Pocket map and notebook for rangers.", "fieldnotes_1.png"),
    ("boxcheck", "Box Check", "Offline phone app for nest box checks.", "boxcheck_3.png"),
    ("canopy-ranger", "Canopy Ranger", "Check the radio link before you fit the sensor.", "ranger_1.png"),
]


def background():
    bb.X0, bb.Y0, bb.WM, bb.HM = 332600, 481250, 1300, 650      # 2:1 strip over the ridges and the moss
    z = bb.load()
    v = bb.shade(z)
    v = (v - np.percentile(v, 2)) / (np.percentile(v, 99.8) - np.percentile(v, 2))
    lo, hi = np.array(bb.THEMES["dark"]["lo"]), np.array(bb.THEMES["dark"]["hi"])
    rgb = (lo + np.clip(v, 0, 1)[..., None] * (hi - lo)).astype(np.uint8)
    im = Image.fromarray(rgb).resize((CW, CH), Image.Resampling.LANCZOS)
    shade = Image.new("L", (CW, CH))                              # darken the left so text reads
    ImageDraw.Draw(shade).rectangle((0, 0, CW, CH), fill=0)
    grad = np.tile(np.clip(1.0 - np.linspace(0, 1.4, CW), 0.15, 1.0)[None, :], (CH, 1))
    dark = Image.new("RGB", (CW, CH), (6, 9, 14))
    return Image.composite(dark, im, Image.fromarray((grad * 200).astype(np.uint8)))


def phone(shot_path, h=560):
    s = Image.open(shot_path).convert("RGB")
    w = int(s.width * h / s.height)
    s = s.resize((w, h), Image.Resampling.LANCZOS)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), radius=34, fill=255)
    return s, mask


def main(shots):
    out = Path(__file__).parent / "cards"
    out.mkdir(exist_ok=True)
    bg = background()
    fb, fr, fs = ImageFont.truetype(FONT_B, 76), ImageFont.truetype(FONT_R, 34), ImageFont.truetype(FONT_R, 24)
    for slug, name, line, shot in CARDS:
        card = bg.copy()
        p, m = phone(shots / shot)
        px, py = CW - p.width - 90, (CH - p.height) // 2
        glow = Image.new("L", (CW, CH), 0)
        ImageDraw.Draw(glow).rounded_rectangle((px - 6, py - 6, px + p.width + 6, py + p.height + 6), 40, fill=150)
        card.paste((90, 162, 255), (0, 0), glow.filter(ImageFilter.GaussianBlur(18)).point(lambda v: v // 3))
        frame = Image.new("L", (p.width + 12, p.height + 12), 0)
        ImageDraw.Draw(frame).rounded_rectangle((0, 0, p.width + 11, p.height + 11), 40, fill=255)
        card.paste((24, 28, 34), (px - 6, py - 6), frame)
        card.paste(p, (px, py), m)
        d = ImageDraw.Draw(card)
        d.text((80, 220), name, font=fb, fill=(236, 240, 243))
        d.text((84, 318), line, font=fr, fill=(176, 188, 182))
        d.text((84, 560), "github.com/nickjsykes", font=fs, fill=(120, 132, 128))
        card.save(out / f"{slug}.png", optimize=True)
        print(out / f"{slug}.png")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
