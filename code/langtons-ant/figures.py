"""
Generate hero images for the Langton's ant explorable into langtons-ant/img/.

Everything here is rendered from the SAME canonical engine the page and the
verifier use (``langton.py``) -- no separate re-implementation, no magic
numbers.  Cells are drawn pixel-exact (nearest-neighbour, no interpolation) so
the diagonal "highway" stays crisp at any display size.

Convention (identical to the page and facts.json):
    white -> turn RIGHT (+90 on a y-DOWN screen), flip to black, step;
    black -> turn LEFT  (-90), flip to white, step.
    x runs east, y runs DOWN; the ant starts at the origin facing UP.
Because y runs down, arrays are indexed [row=y, col=x] and shown with
origin="upper", so the picture matches the in-browser canvas exactly.

Run:  python3 figures.py
"""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

import langton

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "img"))
os.makedirs(OUT, exist_ok=True)

# --- house palette (matches the explorable's design tokens) ---
CREAM = "#f3eee2"   # --c-inset (light)
INK = "#19202f"     # --c-ink   (light)  -> black cells
AMBER = "#aa5d1a"   # ant marker / accent
LINE = "#d3ccba"    # --c-line-strong (light)
DIM = "#6b7689"     # muted label ink

# Turmite colour ramp -- BYTE-for-byte the TURMITE_PAL used in index.html
# (index 0 is the background "white"/cream; colours 1.. are the painted states).
TURMITE_PAL = [
    "#aa5d1a", "#1978a8", "#d4207a", "#148238", "#8126ff", "#d2371f",
    "#216eda", "#8b6d15", "#137f6d", "#c31dc3", "#408013", "#4040ff",
    "#7c7313", "#cd1fa1",
]

written = []


def _bbox(cells, pad=1):
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    return min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad


def _grid_from_cells(cells, x0, x1, y0, y1):
    """Dense 0/1 array indexed [row=y, col=x] over the inclusive box."""
    w = x1 - x0 + 1
    h = y1 - y0 + 1
    g = np.zeros((h, w), dtype=np.uint8)
    for (x, y) in cells:
        if x0 <= x <= x1 and y0 <= y <= y1:
            g[y - y0, x - x0] = 1
    return g


def fig_story(steps=12000, name="langton_story.png"):
    """The whole all-white run: a chaotic blob with the highway shooting off it.
    The amber marker is the ant's final position."""
    ant = langton.run_from_all_white(steps)
    cells = ant.black_cells()
    x0, x1, y0, y1 = _bbox(cells, pad=2)
    g = _grid_from_cells(cells, x0, x1, y0, y1)

    fig, ax = plt.subplots(figsize=(7.2, 7.2 * g.shape[0] / g.shape[1]), dpi=200)
    ax.imshow(g, cmap=ListedColormap([CREAM, INK]), vmin=0, vmax=1,
              interpolation="nearest", origin="upper",
              extent=[x0 - 0.5, x1 + 0.5, y1 + 0.5, y0 - 0.5])
    ax.plot(ant.x, ant.y, "o", color=AMBER, ms=7,
            markeredgecolor=CREAM, markeredgewidth=1.2, zorder=5)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(LINE)
    ax.text(0.015, 0.985,
            "Langton's ant, %d steps from all white\nchaotic core -> periodic diagonal highway"
            % steps,
            transform=ax.transAxes, va="top", ha="left", fontsize=10.5,
            color=DIM, family="monospace")
    fig.patch.set_facecolor("white")
    fig.tight_layout(pad=0.4)
    path = os.path.join(OUT, name)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    written.append(name)
    print("  %-26s %d black cells, ant at (%d, %d)" % (name, len(cells), ant.x, ant.y))


def fig_highway(steps=11000, half=34, name="langton_highway.png"):
    """A close-up window centred on the ant deep in the highway: the repeating
    104-step diagonal motif (several periods of it)."""
    ant = langton.run_from_all_white(steps)
    cx, cy = ant.x, ant.y
    cells = [(x, y) for (x, y) in ant.black_cells()
             if cx - half <= x <= cx + half and cy - half <= y <= cy + half]
    x0, x1, y0, y1 = cx - half, cx + half, cy - half, cy + half
    g = _grid_from_cells(cells, x0, x1, y0, y1)

    fig, ax = plt.subplots(figsize=(7.2, 7.2), dpi=200)
    ax.imshow(g, cmap=ListedColormap([CREAM, INK]), vmin=0, vmax=1,
              interpolation="nearest", origin="upper",
              extent=[x0 - 0.5, x1 + 0.5, y1 + 0.5, y0 - 0.5])
    ax.plot(cx, cy, "o", color=AMBER, ms=8,
            markeredgecolor=CREAM, markeredgewidth=1.3, zorder=5)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(LINE)
    ax.text(0.015, 0.015,
            "the highway, close up\nperiod 104  .  drift 2v2 ~ 2.828 / period  .  +12 cells / period",
            transform=ax.transAxes, va="bottom", ha="left", fontsize=10.5,
            color=DIM, family="monospace")
    fig.patch.set_facecolor("white")
    fig.tight_layout(pad=0.4)
    path = os.path.join(OUT, name)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    written.append(name)
    print("  %-26s window %dx%d around (%d, %d)"
          % (name, 2 * half + 1, 2 * half + 1, cx, cy))


def _draw_turmite(ax, rule, steps, label):
    t = langton.run_turmite(rule, steps)
    field = t.color_field()           # dict (x, y) -> colour index (>=1; 0 = bg)
    if field:
        cells = list(field.keys())
        x0, x1, y0, y1 = _bbox(cells, pad=1)
    else:
        x0, x1, y0, y1 = -1, 1, -1, 1
    w, h = x1 - x0 + 1, y1 - y0 + 1
    img = np.zeros((h, w, 3), dtype=float)
    bg = np.array(matplotlib.colors.to_rgb(CREAM))
    img[:, :] = bg
    for (x, y), c in field.items():
        col = TURMITE_PAL[(c - 1) % len(TURMITE_PAL)]
        img[y - y0, x - x0] = matplotlib.colors.to_rgb(col)
    ax.imshow(img, interpolation="nearest", origin="upper",
              extent=[x0 - 0.5, x1 + 0.5, y1 + 0.5, y0 - 0.5])
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(LINE)
    ax.set_title(label, fontsize=11, color=INK, family="monospace", pad=6)


def fig_turmites(name="turmite_gallery.png"):
    """Four rule-strings: RL (=Langton), the proven-symmetric LLRR, the chaotic
    RLR, and the square-filling LRRRRRLLR."""
    specs = [
        ("RL", 12000, "RL  = Langton (highway)"),
        ("LLRR", 16000, "LLRR  proven symmetric"),
        ("RLR", 40000, "RLR  chaotic (open)"),
        ("LRRRRRLLR", 70000, "LRRRRRLLR  fills a square"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 9.0), dpi=200)
    for ax, (rule, steps, label) in zip(axes.ravel(), specs):
        _draw_turmite(ax, rule, steps, label)
        print("  turmite %-12s %d steps" % (rule, steps))
    fig.patch.set_facecolor("white")
    fig.suptitle("Turmites: tiny rule changes, wildly different worlds",
                 fontsize=13, color=INK, family="monospace", y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    path = os.path.join(OUT, name)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    written.append(name)


def main():
    print("Rendering Langton's ant figures into", OUT)
    fig_story()
    fig_highway()
    fig_turmites()
    print("\nWrote %d file(s):" % len(written))
    for n in written:
        p = os.path.join(OUT, n)
        print("  %-26s %7d bytes" % (n, os.path.getsize(p)))


if __name__ == "__main__":
    main()
