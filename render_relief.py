"""Full-resolution LiDAR relief renders in the Christmas-print 'slate' style, without the poster frame.

Same colours and shading as C:\\Dev\\Christmas\\relief_print.py, at the DTM's native 1 m per pixel.
Writes src/<slug>_full.png (gitignored) for build_banner.py and build_cards.py to crop from.
Run with the Terra venv (rasterio, scipy):
    C:/Dev/Terra/.venv/Scripts/python.exe render_relief.py
Contains Environment Agency data (c) Environment Agency, Open Government Licence v3.
"""
from pathlib import Path

import numpy as np
import rasterio
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).parent
DTM = Path(r"C:\Dev\Christmas\dtm")
SLUGS = ["roudsea", "duddon_mosses", "north_walney", "gait_barrows"]
CMAP = LinearSegmentedColormap.from_list("s", ["#16242b", "#24424a", "#4d7269", "#b08a52", "#e2c48a", "#f6ecd2"])
WATER = "#0c1215"


def render(path):
    with rasterio.open(path) as src:
        z = src.read(1).astype("float32")
        nodata, res = src.nodata, src.res[0]
    mask = ~np.isfinite(z)
    if nodata is not None and np.isfinite(nodata):
        mask |= z == nodata
    mask |= z < -100
    idx = ndi.distance_transform_edt(mask, return_distances=False, return_indices=True)
    zf = z[tuple(idx)]

    def hillshade(az, alt=40, zfac=4.0):
        gy, gx = np.gradient(zf * zfac / res)
        slope = np.arctan(np.hypot(gx, gy))
        aspect = np.arctan2(gy, -gx)
        azr, altr = np.radians(360 - az + 90), np.radians(alt)
        return np.sin(altr) * np.cos(slope) + np.cos(altr) * np.sin(slope) * np.cos(azr - aspect)

    hs = np.clip(sum(w * hillshade(az) for az, w in [(315, 0.5), (270, 0.2), (360, 0.2), (225, 0.1)]), 0, 1)
    lrm = np.clip((zf - ndi.gaussian_filter(zf, 12 / res)) / 0.8, -1, 1)
    ranks = np.searchsorted(np.sort(zf[~mask][::37]), zf) / (~mask).sum() * 37
    tint = np.clip(ranks, 0, 1) ** 0.8
    rgb = CMAP(tint)[..., :3]
    rgb = np.clip(rgb * (0.35 + 0.85 * hs + 0.22 * lrm)[..., None], 0, 1)
    rgb[mask] = to_rgb(WATER)
    return Image.fromarray((rgb * 255).astype(np.uint8))


if __name__ == "__main__":
    (HERE / "src").mkdir(exist_ok=True)
    for slug in SLUGS:
        im = render(DTM / f"{slug}.tif")
        im.save(HERE / "src" / f"{slug}_full.png")
        print(slug, im.size)
