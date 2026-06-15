"""
figures.py  --  Render the Collatz figures into img/  (Curiosity Lab #5).

Presentation only: every NUMBER drawn here is one that verify.py checks.
Figures are saved at an EXACT pixel size (figsize x dpi, no bbox_inches='tight'),
read back with PIL, and the true dimensions logged to figures.log.

  fig1_hailstone.png   a few hailstone trajectories (value vs step, log y):
                       27 climbs to 9232 in 111 steps, 703 to 250504, etc.
  fig2_scatter.png     total stopping time vs n for n<=10000 -- the famous
                       banded "fan"; total-stopping records highlighted.
  fig3_bijection.png   the Terras parity vectors mod 2^5: 32 residues -> 32
                       distinct 5-bit patterns (a bijection) for the accelerated
                       map T; the raw map C collides (NOT a bijection).
  fig4_sieve.png       descent sieve: #odd-steps ~ Binomial(k,1/2); and the
                       provably-descending fraction vs k rising slowly toward 1.

Deterministic.  Run:  python3 figures.py
"""

import os
import math

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from PIL import Image

import collatz as C

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)

# Okabe-Ito colorblind-safe palette
BLUE = "#0072B2"; ORANGE = "#E69F00"; GREEN = "#009E73"; VERM = "#D55E00"
SKY = "#56B4E9"; PURPLE = "#CC79A7"; YELLOW = "#F0E442"; BLACK = "#222222"
GREY = "#9aa0a6"

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "font.size": 13, "axes.titlesize": 17, "axes.titleweight": "bold",
    "axes.edgecolor": "#444444", "axes.linewidth": 1.0,
    "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.8,
    "xtick.color": "#333", "ytick.color": "#333", "axes.labelcolor": "#222",
})

_LOG = []
def log(msg):
    print(msg); _LOG.append(msg)

def save(fig, name, dpi):
    path = os.path.join(IMG, name)
    fig.savefig(path, dpi=dpi)           # NO bbox_inches='tight' -> exact pixels
    plt.close(fig)
    w, h = Image.open(path).size
    log(f"  wrote {name}: {w}x{h} px (aspect {w/h:.4f})")
    return (w, h)


# ----------------------------------------------------------------------
# fig1: hailstone trajectories
# ----------------------------------------------------------------------
def fig1_hailstone():
    log("fig1: hailstone trajectories")
    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    seeds = [(27, VERM), (703, BLUE), (97, GREEN), (871, PURPLE)]
    for n, col in seeds:
        traj = [int(x) for x in C.trajectory(n)]
        ax.plot(range(len(traj)), traj, color=col, lw=1.7,
                label=f"n={n}: {C.total_stopping_time(n)} steps, peak {C.max_value(n):,}")
    ax.set_yscale("log")
    ax.set_xlabel("step"); ax.set_ylabel("value (log scale)")
    ax.set_title("Hailstone trajectories: simple rule, wild flight")
    ax.legend(fontsize=10, loc="upper right", framealpha=.95)
    ax.margins(x=0.01)
    return save(fig, "fig1_hailstone.png", 150)


# ----------------------------------------------------------------------
# fig2: stopping-time scatter (the famous banded fan) + records
# ----------------------------------------------------------------------
def fig2_scatter():
    log("fig2: stopping-time scatter")
    N = 10000
    ys = np.fromiter((C.total_stopping_time(n) for n in range(1, N + 1)),
                     dtype=int, count=N)
    xs = np.arange(1, N + 1)
    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    ax.scatter(xs, ys, s=2.2, c=BLUE, alpha=0.35, linewidths=0, rasterized=True)
    recs = [(n, s) for n, s in C.total_stopping_records(N)]
    rx = [n for n, s in recs]; ry = [s for n, s in recs]
    ax.plot(rx, ry, color=VERM, lw=1.3, zorder=3)
    ax.scatter(rx, ry, s=22, c=VERM, zorder=4, label="total-stopping-time records")
    for n, s in recs:
        if n in (27, 871, 6171):
            ax.annotate(f"{n}", (n, s), textcoords="offset points", xytext=(4, 4),
                        fontsize=9, color=VERM, fontweight="bold")
    ax.set_xlabel("starting number n"); ax.set_ylabel("steps to reach 1")
    ax.set_title("How long until you hit 1?  (n ≤ 10,000)")
    ax.legend(fontsize=10, loc="upper left", framealpha=.95)
    ax.margins(x=0.01)
    return save(fig, "fig2_scatter.png", 150)


# ----------------------------------------------------------------------
# fig3: the Terras parity bijection (mod 32) -- T bijective, raw C collides
# ----------------------------------------------------------------------
def fig3_bijection():
    log("fig3: parity bijection mod 32")
    k = 5
    res = list(range(1 << k))
    matT = np.array([C.parity_vector(r, k) for r in res])
    # raw-map parity vectors (same construction, raw step) -> collisions
    def pv_raw(r, k):
        v = []; m = r
        for _ in range(k):
            v.append(m & 1); m = C.collatz_step(m)
        return v
    matC = np.array([pv_raw(r, k) for r in res])
    nT = len({tuple(row) for row in matT})
    nC = len({tuple(row) for row in matC})

    cmap = ListedColormap(["#eef1f6", BLUE])
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 5.0))
    for ax, mat, title, ndist in (
        (axes[0], matT, f"accelerated map T\n{nT} distinct → a bijection", nT),
        (axes[1], matC, f"raw map C\n{nC} distinct → collisions, NOT a bijection", nC)):
        ax.imshow(mat, cmap=cmap, aspect="auto", interpolation="nearest")
        ax.set_xticks(range(k)); ax.set_xticklabels([f"step {i}" for i in range(k)], fontsize=8, rotation=30)
        ax.set_yticks(range(0, 32, 4)); ax.set_yticklabels(range(0, 32, 4), fontsize=8)
        ax.set_ylabel("residue r  (mod 32)"); ax.set_title(title, fontsize=12)
        ax.grid(False)
    fig.suptitle("Terras parity vectors: the hidden skeleton (k = 5)",
                 fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return save(fig, "fig3_bijection.png", 150)


# ----------------------------------------------------------------------
# fig4: descent sieve -- popcount ~ Binomial, descending fraction -> 1
# ----------------------------------------------------------------------
def fig4_sieve():
    log("fig4: descent sieve")
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.3))

    # left: popcount distribution mod 2^10 vs Binomial(10, a)
    k = 10
    cnt = np.zeros(k + 1, dtype=int)
    for r in range(1 << k):
        cnt[C.num_odd_steps(r, k)] += 1
    a = np.arange(k + 1)
    binom = np.array([math.comb(k, j) for j in a])
    thr = k * math.log(2) / math.log(3)        # a < thr  => provably descends
    ax = axes[0]
    colors = [GREEN if j < thr else VERM for j in a]
    ax.bar(a, cnt, color=colors, alpha=0.85, label="residues mod $2^{10}$")
    ax.plot(a, binom, "o-", color=BLACK, ms=4, lw=1.2, label="Binomial(10, ½)")
    ax.axvline(thr, color=ORANGE, ls="--", lw=1.4)
    ax.annotate(f"a < {thr:.2f}\n→ descends", (thr, cnt.max() * 0.82),
                fontsize=9, color="#9a5410", ha="right")
    ax.set_xlabel("# odd steps a in first 10"); ax.set_ylabel("how many residues")
    ax.set_title("# odd steps is exactly Binomial", fontsize=13)
    ax.legend(fontsize=9, framealpha=.95)

    # right: descending fraction vs k -> 1 (slowly)
    ax = axes[1]
    ks = np.arange(1, 41)
    fr = [C.descending_class_fraction(int(kk)) for kk in ks]
    vals = [num / den for num, den in fr]
    ax.plot(ks, vals, "o-", color=BLUE, ms=3, lw=1.4)
    ax.axhline(1.0, color=GREY, ls=":", lw=1.2)
    for kk, v in [(5, vals[4]), (20, vals[19])]:
        ax.annotate(f"k={kk}: {v:.3f}", (kk, v), textcoords="offset points",
                    xytext=(4, -14), fontsize=9, color=BLUE)
    ax.set_ylim(0.5, 1.02)
    ax.set_xlabel("steps k"); ax.set_ylabel("fraction provably descending")
    ax.set_title("→ 1, but slowly (Terras)", fontsize=13)
    fig.suptitle("Why almost every number falls: the descent sieve",
                 fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return save(fig, "fig4_sieve.png", 150)


if __name__ == "__main__":
    log("rendering Collatz figures ...")
    fig1_hailstone()
    fig2_scatter()
    fig3_bijection()
    fig4_sieve()
    with open(os.path.join(HERE, "figures.log"), "w") as f:
        f.write("\n".join(_LOG) + "\n")
    log("done.")
