"""Generate hero images for the explorable. Outputs PNGs to ../../../public/curiosity-lab/sandpile/img/"""
import os, time
import numpy as np
from PIL import Image
import sandpile as sp

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                   "public", "curiosity-lab", "sandpile", "img")
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

# Palette shared with the in-browser version (height 0..3 -> RGB)
PAL = np.array([
    [ 26,  32,  58],   # 0 deep indigo
    [ 45, 122, 152],   # 1 teal
    [240, 162,  73],   # 2 amber
    [250, 241, 217],   # 3 cream
], dtype=np.uint8)


def to_img(arr, scale=1):
    rgb = PAL[np.clip(arr, 0, 3)]
    img = Image.fromarray(rgb, "RGB")
    if scale != 1:
        img = img.resize((arr.shape[1] * scale, arr.shape[0] * scale), Image.NEAREST)
    return img


def crop_nonzero(arr, pad=2):
    nz = np.argwhere(arr > 0)
    if len(nz) == 0:
        return arr
    (r0, c0), (r1, c1) = nz.min(0), nz.max(0) + 1
    r0 = max(0, r0 - pad); c0 = max(0, c0 - pad)
    r1 = min(arr.shape[0], r1 + pad); c1 = min(arr.shape[1], c1 + pad)
    return arr[r0:r1, c0:c1]


# --- 1) Identity element ------------------------------------------------
for n in (128, 256, 512):
    t = time.time()
    e = sp.identity(n)
    to_img(e).save(os.path.join(OUT, f"identity_{n}.png"))
    print(f"identity n={n}: {time.time()-t:.1f}s  (saved)")

# --- 2) Single-source avalanche patterns --------------------------------
for chips, n in [(50000, 401), (200000, 601), (1000000, 1101)]:
    t = time.time()
    h, total = sp.single_source(n, chips)
    border = h[0, :].sum() + h[-1, :].sum() + h[:, 0].sum() + h[:, -1].sum()
    h = crop_nonzero(h)
    to_img(h).save(os.path.join(OUT, f"single_{chips}.png"))
    print(f"single chips={chips} grid={n}: {time.time()-t:.1f}s  topples={total}  "
          f"border_touch={border}  size={h.shape}  (saved)")

print("\nOUT:", OUT)
print(os.listdir(OUT))
