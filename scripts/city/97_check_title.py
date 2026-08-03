"""Compare the title in a render against the same measurements taken off the
reference frame. Plain python, no Blender.

Everything here is measured in sRGB on the saved PNG, which is the only place
the two are comparable: the reference is a PNG and Blender hands its own
pixels back as linear floats.

The mask is a connected-component pass, not a colour threshold, because the
city is full of other red things (the construction frame, cars, a sign) and a
plain threshold quietly counts all of them.

    python3 scripts/city/97_check_title.py renders/city_08_title.png
"""
import sys, pathlib
import numpy as np
from PIL import Image
from scipy import ndimage

REF = {"coverage": 7.68, "bbox": (0.642, 0.437), "centre": (0.479, 0.546),
       "face": (0.928, 0.107, 0.085)}
MIN_BLOB = 1500          # px at 1620x1080; scaled by area below


def title_mask(im):
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    raw = (r > 0.45) & (r > g * 1.7) & (r > b * 1.7)
    lab, n = ndimage.label(raw)
    if n == 0:
        return raw
    sizes = ndimage.sum(raw, lab, range(1, n + 1))
    # the city has other red things in it (the construction frame, cars, a
    # sign) and they are all small next to a letter, so the floor is set off
    # the biggest blob rather than off an absolute pixel count
    floor = max(MIN_BLOB * im.shape[0] * im.shape[1] / (1620 * 1080),
                sizes.max() * 0.10)
    keep = np.zeros_like(raw)
    for i in np.nonzero(sizes >= floor)[0]:
        keep |= (lab == i + 1)
    return keep


def main(path):
    im = np.asarray(Image.open(path).convert("RGB")).astype(float) / 255
    h, w, _ = im.shape
    m = title_mask(im)
    if not m.any():
        print("  no title found")
        return
    ys, xs = np.nonzero(m)
    px = im[m]
    lum = px @ np.array([0.2126, 0.7152, 0.0722])
    face = px[lum > np.percentile(lum, 60)].mean(0)
    side = px[lum < np.percentile(lum, 20)].mean(0)
    bbox = ((xs.max() - xs.min()) / w, (ys.max() - ys.min()) / h)
    centre = ((xs.min() + xs.max()) / 2 / w, 1 - (ys.min() + ys.max()) / 2 / h)

    print(f"\n  {pathlib.Path(path).name}   {w}x{h}")
    print(f"  coverage  {100 * m.mean():5.2f} %        "
          f"reference {REF['coverage']:.2f} %")
    print(f"  bbox      {bbox[0]:.3f} x {bbox[1]:.3f}    "
          f"reference {REF['bbox'][0]} x {REF['bbox'][1]}")
    print(f"  centre    {centre[0]:.3f} , {centre[1]:.3f}    "
          f"reference {REF['centre'][0]} , {REF['centre'][1]}")
    print(f"  face rgb  {face[0]:.3f} {face[1]:.3f} {face[2]:.3f}    "
          f"reference {REF['face'][0]} {REF['face'][1]} {REF['face'][2]}")
    print(f"  side rgb  {side[0]:.3f} {side[1]:.3f} {side[2]:.3f}")
    fill = 100 * m.sum() / ((xs.max() - xs.min()) * (ys.max() - ys.min()))
    print(f"  ink       {fill:5.1f} % of its own box   reference 27.3 %\n")


main(sys.argv[1] if len(sys.argv) > 1 else "renders/city_08_title.png")
