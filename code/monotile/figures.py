"""
figures.py  --  Render the three hat-monotile figures into img/.

Computational Curiosity Lab #3.  Presentation only -- every NUMBER this draws
is one that verify.py checks.  We render with a full-bleed single axes and an
exact figure size so each PNG's INTRINSIC pixel dimensions match its content
aspect ratio (a 2:1 picture is saved 2:1, never forced square).  No
`bbox_inches='tight'` (which would silently change the pixel size).

Figures:
  (1) fig1_hat.png          -- the single hat (13-gon) with its 8 kites.
  (2) fig2_substitution.png -- one substitution step: an H metatile (left) and
                               the level-2 H supertile (right), child metatiles
                               coloured by type  (H -> 3H + 1T + 3P + 3F).
  (3) fig3_patch.png        -- a level-4 hat tiling (1156 hats) coloured by
                               orientation, the rare REFLECTED hats highlighted.

Run synchronously:  python3 figures.py   (writes figures.log).
"""

import os
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
from matplotlib.collections import PatchCollection
from PIL import Image

import hat as H
from hat import (HAT_OUTLINE, hat_kites_cartesian, mul, trans_pt, ttrans,
                 det2)
from substitution import (base_metatiles, construct_patch, construct_metatiles,
                          enum_hats, patch, ORDER, GLOBAL_SCALE)

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)

# metatile-type palette (used in fig 2 and the legend)
TYPE_COLOR = {'H': '#4e79a7', 'T': '#f2a93b', 'P': '#59a14f', 'F': '#e15759'}

_LOG = []


def log(msg):
    print(msg)
    _LOG.append(msg)


# ----------------------------------------------------------------------
# Pixel-exact full-bleed canvas helpers.
# ----------------------------------------------------------------------
def _bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), max(xs), min(ys), max(ys)


def _fit_to_aspect(xmin, xmax, ymin, ymax, target_aspect, pad=0.04):
    """Pad, then expand the bbox (centred) so width/height == target_aspect
       EXACTLY -> equal data scale on both axes, zero distortion."""
    dw, dh = xmax - xmin, ymax - ymin
    xmin -= dw * pad; xmax += dw * pad
    ymin -= dh * pad; ymax += dh * pad
    dw, dh = xmax - xmin, ymax - ymin
    cur = dw / dh
    if cur < target_aspect:                      # too tall -> widen
        ndw = dh * target_aspect; cx = 0.5 * (xmin + xmax)
        xmin, xmax = cx - ndw / 2, cx + ndw / 2
    else:                                        # too wide -> heighten
        ndh = dw / target_aspect; cy = 0.5 * (ymin + ymax)
        ymin, ymax = cy - ndh / 2, cy + ndh / 2
    return xmin, xmax, ymin, ymax


def new_canvas(points, long_px=1600, dpi=200, pad=0.04):
    """A full-bleed figure+axes whose saved PNG is exactly long_px on its long
       side, with the short side set by the content aspect (no distortion)."""
    xmin, xmax, ymin, ymax = _bbox(points)
    aspect = (xmax - xmin) / (ymax - ymin)
    if aspect >= 1:
        w_px, h_px = long_px, max(1, round(long_px / aspect))
    else:
        h_px, w_px = long_px, max(1, round(long_px * aspect))
    target = w_px / h_px
    xmin, xmax, ymin, ymax = _fit_to_aspect(xmin, xmax, ymin, ymax, target, pad)
    fig = plt.figure(figsize=(w_px / dpi, h_px / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.axis("off")
    return fig, ax, (w_px, h_px)


def save(fig, name, want):
    path = os.path.join(IMG, name)
    fig.savefig(path, dpi=fig.dpi)
    plt.close(fig)
    w, h = Image.open(path).size                 # truthful read-back
    tag = "OK" if (w, h) == tuple(want) else "MISMATCH!"
    log(f"  wrote {name}: {w}x{h} px (aspect {w/h:.4f})  [{tag} wanted {want[0]}x{want[1]}]")
    return (w, h)


# ----------------------------------------------------------------------
# Figure 1 -- the hat and its 8 kites.
# ----------------------------------------------------------------------
def figure_hat():
    log("Figure 1: the hat (13-gon) + 8 kites")
    kites = hat_kites_cartesian()
    fig, ax, want = new_canvas(HAT_OUTLINE, long_px=1400, pad=0.10)

    cmap = plt.colormaps.get_cmap("tab10")
    patches = [MplPoly(k, closed=True) for k in kites]
    pc = PatchCollection(patches, facecolor=[cmap(i % 10) for i in range(len(kites))],
                         edgecolor="white", linewidth=1.4, alpha=0.85, zorder=1)
    ax.add_collection(pc)

    # the authoritative 13-gon outline on top
    ax.add_patch(MplPoly(HAT_OUTLINE, closed=True, fill=False,
                         edgecolor="#111111", linewidth=3.2, zorder=3))
    xs = [p[0] for p in HAT_OUTLINE] + [HAT_OUTLINE[0][0]]
    ys = [p[1] for p in HAT_OUTLINE] + [HAT_OUTLINE[0][1]]
    ax.plot(xs, ys, "o", color="#111111", markersize=5.5, zorder=4)

    ax.text(0.5, 0.975, "the hat  —  Tile(1, √3)",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=20, fontweight="bold", color="#111111")
    ax.text(0.5, 0.04,
            "13-gon · 8 kites · area = 8√3 = 32 unit-triangles",
            transform=ax.transAxes, ha="center", va="bottom",
            fontsize=13, color="#333333")
    return save(fig, "fig1_hat.png", want)


# ----------------------------------------------------------------------
# Figure 2 -- one substitution step  H -> 3H + 1T + 3P + 3F.
# ----------------------------------------------------------------------
def _draw_metatile_hats(ax, geom, transform, face, hat_edge="#ffffff"):
    """Draw all hats of a (sub)metatile under `transform`, returning their pts."""
    allpts = []
    for rec in enum_hats(geom, transform):
        v = rec["vertices"]
        allpts += v
        ax.add_patch(MplPoly(v, closed=True, facecolor=face, edgecolor=hat_edge,
                             linewidth=0.8, alpha=0.92, zorder=2))
    return allpts


def figure_substitution():
    log("Figure 2: one substitution step (H -> children)")
    base = base_metatiles()
    ident = {id(base[i]): ORDER[i] for i in range(4)}
    patch_ = construct_patch(*base)
    level2 = construct_metatiles(patch_)
    H2 = level2[0]                                # level-2 H supertile

    # gather geometry first (to know the bbox), then build the canvas.
    # left: a single level-1 H metatile, shifted left of H2 at the SAME scale.
    base_left = base_metatiles()[0]
    left_hats = enum_hats(base_left)             # GLOBAL_SCALE default
    left_outline = [trans_pt(GLOBAL_SCALE, p) for p in base_left.shape]
    Lx0, Lx1, Ly0, Ly1 = _bbox([p for r in left_hats for p in r["vertices"]])

    # right: H2 outline + its child metatiles
    H2_outline = [trans_pt(GLOBAL_SCALE, p) for p in H2.shape]
    Rx0, Rx1, Ry0, Ry1 = _bbox(H2_outline)

    gap = 0.9 * (Rx1 - Rx0)
    offx = (Rx0 - gap) - Lx1                      # shift left block to sit left of H2
    offy = 0.5 * ((Ry0 + Ry1) - (Ly0 + Ly1))     # vertically centre it on H2
    shift = lambda pts: [(x + offx, y + offy) for (x, y) in pts]

    all_pts = list(H2_outline) + shift([p for r in left_hats for p in r["vertices"]])
    fig, ax, want = new_canvas(all_pts, long_px=1800, pad=0.06)

    # ---- left: the H metatile (4 hats, blue, the reflected one outlined) ----
    for r in left_hats:
        v = shift(r["vertices"])
        ax.add_patch(MplPoly(v, closed=True, facecolor=TYPE_COLOR['H'],
                             edgecolor="white", linewidth=1.0, alpha=0.92, zorder=2))
        if r["reflected"]:
            ax.add_patch(MplPoly(v, closed=True, fill=False, edgecolor="#111111",
                                 linewidth=2.2, zorder=3))
    ax.add_patch(MplPoly(shift(left_outline), closed=True, fill=False,
                         edgecolor="#111111", linewidth=2.4, zorder=4))

    # ---- right: H2 child metatiles coloured by type ----
    counts = {'H': 0, 'T': 0, 'P': 0, 'F': 0}
    for ch in H2.children:
        ttype = ident[id(ch["geom"])]
        counts[ttype] += 1
        T = mul(GLOBAL_SCALE, ch["T"])
        _draw_metatile_hats(ax, ch["geom"], T, TYPE_COLOR[ttype])
        outline = [trans_pt(T, p) for p in ch["geom"].shape]
        ax.add_patch(MplPoly(outline, closed=True, fill=False,
                             edgecolor="#222222", linewidth=1.4, zorder=3))
    ax.add_patch(MplPoly(H2_outline, closed=True, fill=False,
                         edgecolor="#111111", linewidth=2.6, zorder=4))

    # arrow + title + legend
    ax.annotate("", xy=(Rx0 - 0.12 * gap, 0.5 * (Ry0 + Ry1)),
                xytext=(Lx1 + offx + 0.20 * gap, 0.5 * (Ry0 + Ry1)),
                arrowprops=dict(arrowstyle="-|>", lw=3, color="#111111"), zorder=5)
    rule = (f"H  →  {counts['H']}H + {counts['T']}T + "
            f"{counts['P']}P + {counts['F']}F")
    ax.text(0.5, 0.975, f"one substitution step:   {rule}",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=19, fontweight="bold", color="#111111",
            bbox=dict(boxstyle="round,pad=0.35", fc="#ffffffe6", ec="none"), zorder=6)
    for i, t in enumerate(ORDER):
        ax.text(0.015 + 0.052 * i, 0.03, t, transform=ax.transAxes,
                ha="center", va="bottom", fontsize=15, fontweight="bold",
                color="white",
                bbox=dict(boxstyle="round,pad=0.32", fc=TYPE_COLOR[t], ec="none"))
    assert counts == {'H': 3, 'T': 1, 'P': 3, 'F': 3}, counts
    return save(fig, "fig2_substitution.png", want)


# ----------------------------------------------------------------------
# Figure 3 -- a level-4 patch, hats coloured by orientation, reflected lit up.
# ----------------------------------------------------------------------
def figure_patch(level=4, seed='H'):
    log(f"Figure 3: level-{level} {seed}-patch")
    hats = patch(level, seed)
    n = len(hats)
    nref = sum(h["reflected"] for h in hats)
    log(f"  {n} hats ({nref} reflected, {n - nref} unreflected)")

    all_pts = [p for h in hats for p in h["vertices"]]
    fig, ax, want = new_canvas(all_pts, long_px=1700, pad=0.03)

    # orientation -> colour for unreflected hats (cyclic map); reflected = lit.
    oris = sorted({round(h["orientation"]) % 360 for h in hats if not h["reflected"]})
    idx = {o: i for i, o in enumerate(oris)}
    cmap = plt.colormaps.get_cmap("hsv")
    log(f"  {len(oris)} distinct unreflected orientations: {oris}")

    un_patches, un_colors, rf_patches = [], [], []
    for h in hats:
        poly = MplPoly(h["vertices"], closed=True)
        if h["reflected"]:
            rf_patches.append(poly)
        else:
            un_patches.append(poly)
            un_colors.append(cmap(idx[round(h["orientation"]) % 360] / max(1, len(oris))))
    ax.add_collection(PatchCollection(un_patches, facecolor=un_colors,
                                      edgecolor="#33333366", linewidth=0.35, zorder=1))
    ax.add_collection(PatchCollection(rf_patches, facecolor="#101028",
                                      edgecolor="#f4d03f", linewidth=0.9, zorder=2))

    ax.text(0.5, 0.985,
            f"a hat tiling — level-{level} supertile, {n} hats",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=18, fontweight="bold", color="#111111",
            bbox=dict(boxstyle="round,pad=0.3", fc="#ffffffcc", ec="none"))
    ax.text(0.5, 0.018,
            f"colour = orientation · dark gold-edged = the {nref} REFLECTED hats "
            f"(unrefl : refl → φ⁴ ≈ 6.854)",
            transform=ax.transAxes, ha="center", va="bottom",
            fontsize=12, color="#111111",
            bbox=dict(boxstyle="round,pad=0.3", fc="#ffffffcc", ec="none"))
    return save(fig, "fig3_patch.png", want)


if __name__ == "__main__":
    log("=== monotile figures ===")
    d1 = figure_hat()
    d2 = figure_substitution()
    d3 = figure_patch(level=4, seed='H')
    log("=== done ===")
    log(f"fig1_hat.png          {d1[0]}x{d1[1]}")
    log(f"fig2_substitution.png {d2[0]}x{d2[1]}")
    log(f"fig3_patch.png        {d3[0]}x{d3[1]}")
    with open(os.path.join(HERE, "figures.log"), "w") as f:
        f.write("\n".join(_LOG) + "\n")
