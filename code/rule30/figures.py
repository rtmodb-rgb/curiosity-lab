"""
Generate hero images for the Rule 30 explorable into rule30/img/.

All images are rendered crisply with no interpolation (pixel-exact cellular
automata). The two flagship space-time diagrams (Rule 30 evolution and the
Rule 90 Sierpinski triangle) are written with matplotlib's imsave at native
cell resolution and integer-upscaled so they stay sharp at large display sizes.
The multi-rule gallery and the center-column "randomness" panel use matplotlib
subplots so they can carry minimal rule-number labels.

Run:  python3 figures.py
"""
import os
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import eca

OUT = os.path.join(os.path.dirname(__file__), "img")
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

written = []


def save_bw(arr, name, scale=1):
    """Pixel-exact black-on-white PNG (0 -> white, 1 -> black)."""
    a = arr
    if scale != 1:
        a = np.kron(arr, np.ones((scale, scale), dtype=np.uint8))
    path = os.path.join(OUT, name)
    plt.imsave(path, a, cmap="gray_r", vmin=0, vmax=1, dpi=200)
    written.append(name)
    return path


def evolve_periodic(rule, init, steps):
    """Evolve with PERIODIC (wrap-around) boundaries -- used for the gallery so
    random-initial-condition pictures tile cleanly with no edge cone. (The
    exact center-column engines in eca.py use zero boundaries by design.)"""
    table = eca.rule_table(rule)
    row = np.asarray(init, dtype=np.uint8).copy()
    out = np.empty((steps + 1, row.size), dtype=np.uint8)
    out[0] = row
    for t in range(1, steps + 1):
        left = np.roll(row, 1)
        right = np.roll(row, -1)
        code = (left << 2) | (row << 1) | right
        row = table[code]
        out[t] = row
    return out


# --- 1) Rule 30 evolution from a single seed ---------------------------
t0 = time.time()
g30 = eca.evolve(30, steps=400)                       # 401 x 801, boundary-exact
save_bw(g30, "rule30_evolution.png", scale=2)         # -> 802 x 1602
print(f"rule30_evolution.png  {g30.shape} x2  ({time.time()-t0:.2f}s)")

# --- 2) Rule 90 Sierpinski triangle ------------------------------------
t0 = time.time()
g90 = eca.evolve(90, steps=255)                       # 256 x 511 (clean gasket)
save_bw(g90, "rule90_sierpinski.png", scale=3)        # -> 768 x 1533
print(f"rule90_sierpinski.png {g90.shape} x3  ({time.time()-t0:.2f}s)")

# --- 3) Gallery of iconic rules ----------------------------------------
t0 = time.time()
GAL_RULES = [30, 90, 110, 184, 60, 150]
W, STEPS = 601, 300
rng = np.random.default_rng(30)
init = rng.integers(0, 2, size=W, dtype=np.uint8)     # one shared random row
fig, axes = plt.subplots(2, 3, figsize=(12, 6.6))
for ax, r in zip(axes.flat, GAL_RULES):
    grid = evolve_periodic(r, init, STEPS)
    ax.imshow(grid, cmap="gray_r", vmin=0, vmax=1, interpolation="nearest",
              aspect="auto")
    ax.set_title(f"Rule {r}", fontsize=13, fontfamily="monospace")
    ax.set_xticks([]); ax.set_yticks([])
fig.suptitle("Elementary cellular automata from one shared random row "
             "(periodic boundary)", fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.97))
path = os.path.join(OUT, "rule_gallery.png")
fig.savefig(path, dpi=160, facecolor="white")
plt.close(fig)
written.append("rule_gallery.png")
print(f"rule_gallery.png      rules={GAL_RULES} {W}x{STEPS} random init  "
      f"({time.time()-t0:.2f}s)")

# --- 4) Rule 30 center-column "randomness" -----------------------------
t0 = time.time()
col = eca.rule30_center_bits(70000)                   # boundary-exact column
strip_n = 400
raster_w = 256
raster_h = 220
raster = col[:raster_w * raster_h].reshape(raster_h, raster_w)

fig, (axL, axR) = plt.subplots(
    1, 2, figsize=(11, 6), gridspec_kw={"width_ratios": [1, 5]})
# left: tall thin strip of the first `strip_n` center bits
axL.imshow(col[:strip_n].reshape(-1, 1), cmap="gray_r", vmin=0, vmax=1,
           interpolation="nearest", aspect="auto")
axL.set_title(f"center column\nfirst {strip_n} bits", fontsize=11,
              fontfamily="monospace")
axL.set_xticks([])
axL.set_ylabel("step", fontsize=10)
# right: consecutive center bits laid out 256 per row -> looks structureless
axR.imshow(raster, cmap="gray_r", vmin=0, vmax=1, interpolation="nearest",
           aspect="auto")
axR.set_title(f"{raster_w*raster_h} consecutive center bits, "
              f"{raster_w} per row (no visible pattern)",
              fontsize=11, fontfamily="monospace")
axR.set_xticks([]); axR.set_yticks([])
fig.tight_layout()
path = os.path.join(OUT, "rule30_center_column.png")
fig.savefig(path, dpi=160, facecolor="white")
plt.close(fig)
written.append("rule30_center_column.png")
print(f"rule30_center_column.png  strip={strip_n} raster={raster.shape}  "
      f"({time.time()-t0:.2f}s)")

# --- report ------------------------------------------------------------
print("\nFiles written to", OUT)
for name in written:
    sz = os.path.getsize(os.path.join(OUT, name))
    print(f"  {name:28s} {sz/1024:8.1f} KB")
