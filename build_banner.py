"""Build the profile banner: real 1 m LiDAR of a Cumbrian reserve, with a quiet radio network over it.

Slate ridge, limestone ridge and the restored moss with its bunds, in one strip. Nodes are placed by hand
and are NOT real equipment locations. Writes banner-light.svg and banner-dark.svg next to this file.

Needs rasterio + scipy (the Terra venv has them) and the EA LiDAR tiles cached by GridRef's build:
    C:/Dev/Terra/.venv/Scripts/python.exe build_banner.py
Contains Environment Agency data (c) Environment Agency, Open Government Licence v3.
"""
import base64, glob, io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from PIL import Image
from rasterio.merge import merge
from scipy.ndimage import gaussian_filter

LIDAR = Path(r"C:\Dev\GridRef\build\src\lidar")
X0, Y0 = 332720, 481440            # SW corner of the strip (BNG metres)
WM, HM = 1600, 400                 # strip size in metres (4:1)
W, H = 1200, 300                   # banner size in px
SCALE = 2                          # raster rendered at 2x for sharp screens
CONTOUR_M = 5

THEMES = {
    "light": dict(lo=(150, 132, 104), hi=(252, 248, 238), line="#9a6534", radio="#2f6fb5", ring="#2f6fb5"),
    "dark": dict(lo=(6, 9, 14), hi=(96, 104, 110), line="#a57a4f", radio="#5aa2ff", ring="#5aa2ff"),
}

# Radio network in px on the banner. Gateway on the limestone ridge; nodes are illustrative only.
GATEWAY = (560, 72)
NODES = [(150, 170), (255, 120), (395, 215), (760, 155), (965, 118), (1105, 222)]
RELAY = {0: 1, 5: 4}                   # node 5 reaches the gateway through node 4, like a relay would


def load():
    tiles = []
    for t in glob.glob(str(LIDAR / "dtm_*.tif")):
        x, y = map(int, Path(t).stem.split("_")[1:3])
        if x < X0 + WM and x + 1200 > X0 and y < Y0 + HM and y + 1200 > Y0:
            tiles.append(rasterio.open(t))
    if not tiles:
        raise SystemExit(f"No LiDAR tiles cover the strip in {LIDAR}")
    z, _ = merge(tiles, bounds=(X0, Y0, X0 + WM, Y0 + HM), nodata=np.nan)
    z = z[0].astype(float)
    z[z < -100] = np.nan
    return np.where(np.isnan(z), np.nanmedian(z), z)


def hillshade(z, az=315, alt=38):
    gy, gx = np.gradient(z)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    a, b = np.radians(az), np.radians(alt)
    return np.clip(np.sin(b) * np.sin(slope) + np.cos(b) * np.cos(slope) * np.cos(a - aspect), 0, 1)


def shade(z):
    """Hillshade for the shape of the ground, plus local relief so bunds, drains and walls stand out."""
    hs = hillshade(gaussian_filter(z, 0.8))
    lrm = z - gaussian_filter(z, 12)
    v = 0.75 * hs + np.clip(lrm, -0.8, 0.8) * 0.45
    return np.clip(v, 0, 1)


def raster_b64(v, theme):
    lo, hi = np.array(THEMES[theme]["lo"]), np.array(THEMES[theme]["hi"])
    v = (v - np.percentile(v, 2)) / (np.percentile(v, 99.8) - np.percentile(v, 2))
    rgb = (lo + np.clip(v, 0, 1)[..., None] * (hi - lo)).astype(np.uint8)
    im = Image.fromarray(rgb).resize((W * SCALE, H * SCALE), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode()


def contours(z):
    sm = gaussian_filter(z, 5)
    x = np.linspace(0, W, z.shape[1])
    y = np.linspace(0, H, z.shape[0])
    fig, ax = plt.subplots()
    cs = ax.contour(x, y, sm, levels=np.arange(np.ceil(sm.min() / CONTOUR_M) * CONTOUR_M, sm.max(), CONTOUR_M))
    out = []
    for segs in cs.allsegs:
        d = " ".join("M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in s[::2])
                     for s in segs if len(s) > 6)
        if d:
            out.append(d)
    plt.close(fig)
    return out


def radio(c):
    parts = []
    links = []
    for i, n in enumerate(NODES):
        to = NODES[RELAY[i]] if i in RELAY else GATEWAY
        links.append((n, to))
    for k, ((x1, y1), (x2, y2)) in enumerate(links):
        pid = f"l{k}"
        parts.append(f'<path id="{pid}" d="M{x1},{y1} L{x2},{y2}" stroke="{c["radio"]}" stroke-width="1" '
                     f'stroke-dasharray="2 5" opacity="0.35" fill="none"/>')
        dur = 2.4 + (k % 3) * 0.5
        begin = 1.3 * k
        parts.append(f'<circle r="2.2" fill="{c["radio"]}" opacity="0">'
                     f'<animateMotion dur="{dur}s" begin="{begin}s;l{k}a.end+{5 + k % 4}s" id="l{k}a" fill="freeze">'
                     f'<mpath href="#{pid}"/></animateMotion>'
                     f'<animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.1;0.85;1" dur="{dur}s" '
                     f'begin="{begin}s;l{k}a.end+{5 + k % 4}s" fill="freeze"/></circle>')
    for (x, y) in NODES:
        parts.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{c["radio"]}" opacity="0.8"/>')
    gx, gy = GATEWAY
    for d in (0, 2):
        parts.append(f'<circle cx="{gx}" cy="{gy}" r="6" fill="none" stroke="{c["ring"]}" stroke-width="1" opacity="0">'
                     f'<animate attributeName="r" values="6;46" dur="4s" begin="{d}s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values="0.45;0" dur="4s" begin="{d}s" repeatCount="indefinite"/>'
                     f'</circle>')
    parts.append(f'<rect x="{gx - 4}" y="{gy - 4}" width="8" height="8" rx="1.5" fill="{c["radio"]}" '
                 f'transform="rotate(45 {gx} {gy})"/>')
    return "\n".join(parts)


def svg(theme, img, lines):
    c = THEMES[theme]
    cl = "".join(f'<path d="{d}"/>' for d in lines)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="LiDAR relief of a Cumbrian nature reserve with a small radio sensor network">
<defs><clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>
<g clip-path="url(#frame)">
  <image width="{W}" height="{H}" href="data:image/jpeg;base64,{img}"/>
  <g fill="none" stroke="{c["line"]}" stroke-width="0.6" opacity="0.45">{cl}</g>
  {radio(c)}
</g>
</svg>
'''


def main():
    here = Path(__file__).parent
    z = load()
    v = shade(z)
    lines = contours(z)
    for theme in THEMES:
        out = here / f"banner-{theme}.svg"
        out.write_text(svg(theme, raster_b64(v, theme), lines), encoding="utf-8")
        print(f"{out.name}: {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
