"""Social preview cards (1280x640) for the public repos, on Nick's own LiDAR renders.

Upload each by hand: repo -> Settings -> General -> Social preview -> Edit -> Upload an image.
    python build_cards.py <screenshot folder>
Contains Environment Agency data (c) Environment Agency, Open Government Licence v3.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
Image.MAX_IMAGE_PIXELS = None
CW, CH = 1280, 640
FONT_B = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_R = r"C:\Windows\Fonts\segoeui.ttf"
DEEP = (10, 38, 44)          # palette from the renders
BONE = (241, 232, 210)
SAND = (214, 190, 146)
ACCENT = (232, 96, 60)

# slug, name, line, screenshot (or None), render, crop box in the render
CARDS = [
    ("fieldnotes", "Field Notes", "Pocket map and notebook for rangers.", "fieldnotes_1.png", "duddon_mosses", (0, 1000, 3006, 2503)),
    ("boxcheck", "Box Check", "Offline phone app for nest box checks.", "boxcheck_3.png", "roudsea", (400, 450, 2400, 1450)),
    ("canopy-ranger", "Canopy Ranger", "Check the radio link before you fit the sensor.", "ranger_1.png", "north_walney", (0, 1000, 4023, 3011)),
    ("threat-detector", "Threat Detector", "Every week's planning applications,\nscreened against ancient woodland.", None, "gait_barrows", (0, 900, 2014, 1907)),
]


def background(render, box):
    im = Image.open(HERE / "src" / f"{render}_full.png").convert("RGB").crop(box).resize((CW, CH), Image.Resampling.LANCZOS)
    a = np.clip(1.15 - np.linspace(0, 1.5, CW), 0.12, 0.92)        # deep teal wash, strongest behind the text
    mask = Image.fromarray((np.tile(a[None, :], (CH, 1)) * 255).astype(np.uint8))
    return Image.composite(Image.new("RGB", (CW, CH), DEEP), im, mask)


def phone(shot_path, h=560):
    s = Image.open(shot_path).convert("RGB")
    w = int(s.width * h / s.height)
    s = s.resize((w, h), Image.Resampling.LANCZOS)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), radius=34, fill=255)
    return s, mask


def main(shots):
    out = HERE / "cards"
    out.mkdir(exist_ok=True)
    fb, fr, fs = ImageFont.truetype(FONT_B, 76), ImageFont.truetype(FONT_R, 34), ImageFont.truetype(FONT_R, 24)
    for slug, name, line, shot, render, box in CARDS:
        card = background(render, box)
        if shot:
            p, m = phone(shots / shot)
            px, py = CW - p.width - 90, (CH - p.height) // 2
            shadow = Image.new("L", (CW, CH), 0)
            ImageDraw.Draw(shadow).rounded_rectangle((px - 4, py + 10, px + p.width + 4, py + p.height + 18), 40, fill=170)
            card.paste(DEEP, (0, 0), shadow.filter(ImageFilter.GaussianBlur(16)))
            frame = Image.new("L", (p.width + 12, p.height + 12), 0)
            ImageDraw.Draw(frame).rounded_rectangle((0, 0, p.width + 11, p.height + 11), 40, fill=255)
            card.paste((18, 22, 26), (px - 6, py - 6), frame)
            card.paste(p, (px, py), m)
        d = ImageDraw.Draw(card)
        d.rectangle((84, 196, 84 + 56, 202), fill=ACCENT)           # small accent rule above the name
        d.text((80, 214), name, font=fb, fill=BONE)
        d.multiline_text((84, 312), line, font=fr, fill=SAND, spacing=10)
        d.text((84, 560), "github.com/nickjsykes", font=fs, fill=(150, 170, 165))
        card.save(out / f"{slug}.jpg", quality=90, optimize=True, progressive=True)
        print(out / f"{slug}.jpg", (out / f"{slug}.jpg").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
