"""Build the profile banner: Nick's own LiDAR render of Roudsea with a quiet radio network over it.

Slate ridge, limestone ridge, the restored moss and the far woods, from Environment Agency 1 m LiDAR
(rendered by Nick). Nodes are placed by hand and are NOT real equipment locations.
Writes banner.svg next to this file; works on GitHub's light and dark themes alike.
    python build_banner.py
Contains Environment Agency data (c) Environment Agency, Open Government Licence v3.
"""
import base64, io
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "src" / "roudsea_full.png"   # from render_relief.py, 1 m per pixel
CROP = (0, 800, 3833, 1758)        # 4:1 slice: slate, limestone, the moss, the far woods
W, H = 1200, 300                   # banner size in px
SCALE = 2                          # raster at 2x for sharp screens

# Palette from the renders: deep water teal to sand to limestone white, plus one warm accent.
PALETTE = {"deep": "#123f47", "teal": "#3d7d84", "sand": "#c5a46c", "bone": "#f1e8d2", "accent": "#e8603c"}

# Radio network in banner px. Gateway on the limestone whaleback; nodes illustrative only.
GATEWAY = (410, 100)
NODES = [(150, 172), (262, 70), (330, 232), (560, 130), (640, 248), (860, 112), (1045, 192)]
RELAY = {0: 1, 6: 5}               # these reach the gateway through a neighbour, as a relay would


def raster_b64():
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(SRC).convert("RGB").crop(CROP).resize((W * SCALE, H * SCALE), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode()


def radio(col):
    parts = []
    for k, n in enumerate(NODES):
        (x1, y1), (x2, y2) = n, (NODES[RELAY[k]] if k in RELAY else GATEWAY)
        pid = f"l{k}"
        parts.append(f'<path id="{pid}" d="M{x1},{y1} L{x2},{y2}" stroke="{col}" stroke-width="1.2" '
                     f'stroke-dasharray="2 5" opacity="0.55" fill="none"/>')
        dur, again = 2.4 + (k % 3) * 0.5, 5 + k % 4
        begin = f"{1.3 * k}s;l{k}a.end+{again}s"
        parts.append(f'<circle r="2.6" fill="{col}" opacity="0">'
                     f'<animateMotion id="l{k}a" dur="{dur}s" begin="{begin}" fill="freeze"><mpath href="#{pid}"/></animateMotion>'
                     f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.85;1" dur="{dur}s" begin="{begin}" fill="freeze"/>'
                     f'</circle>')
    for x, y in NODES:
        parts.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="{PALETTE["deep"]}" opacity="0.35"/>'
                     f'<circle cx="{x}" cy="{y}" r="3" fill="{col}"/>')
    gx, gy = GATEWAY
    for d in (0, 2):
        parts.append(f'<circle cx="{gx}" cy="{gy}" r="6" fill="none" stroke="{col}" stroke-width="1.2" opacity="0">'
                     f'<animate attributeName="r" values="6;48" dur="4s" begin="{d}s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values="0.6;0" dur="4s" begin="{d}s" repeatCount="indefinite"/></circle>')
    parts.append(f'<rect x="{gx - 5}" y="{gy - 5}" width="10" height="10" rx="2" fill="{col}" '
                 f'stroke="{PALETTE["deep"]}" stroke-opacity="0.5" transform="rotate(45 {gx} {gy})"/>')
    return "\n".join(parts)


def main():
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="LiDAR relief of a Cumbrian nature reserve with a small radio sensor network">
<defs><clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>
<g clip-path="url(#frame)">
  <image width="{W}" height="{H}" href="data:image/jpeg;base64,{raster_b64()}"/>
  {radio(PALETTE["accent"])}
</g>
</svg>
'''
    out = HERE / "banner.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"{out.name}: {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
