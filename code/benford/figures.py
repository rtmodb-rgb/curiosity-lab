"""
figures.py  --  Render the five Benford figures into img/  (Curiosity Lab #4).

Presentation only: every NUMBER drawn here is one that verify.py checks.
Figures are saved at an EXACT pixel size (figsize x dpi, no bbox_inches='tight'),
read back with PIL, and the true dimensions logged to figures.log.

  fig1_benford_bars.png   canonical Benford bars + 2**n and Fibonacci empirical
                          frequencies overlaid (they hug the curve).
  fig2_convergence.png    log-log max-deviation vs N: 2**n (fast) vs n! (slow)
                          vs primes (flat & large) -- different convergence rates.
  fig3_equidistribution.png  {n*log10 2 mod 1} fills [0,1) uniformly (Weyl); the
                          nine digit-bands have width log10(1+1/d).
  fig4_primes_oscillation.png  primes P(first digit = 1) vs cutoff X keeps
                          oscillating -- no natural-density limit (the honest fig).
  fig5_two_digit.png      generalized first-two-digit Benford curve, 2**n overlaid.

Deterministic.  Run:  python3 figures.py
"""

import os
import math

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

import benford as B

np.random.seed(0)   # nothing random here, but pin it for reproducibility

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
# shared data (computed once)
# ----------------------------------------------------------------------
log("computing sequences ...")
NP2 = 20000
pow2_leads = np.empty(NP2, dtype=np.int8)
pow2_two = []                                   # first-two-digits (n with 2**n>=10)
v = 1
for i in range(NP2):
    v <<= 1
    pow2_leads[i] = B.lead_str(v)
    if v >= 10:
        pow2_two.append(B.first_two(v))
pow2_two = np.array(pow2_two, dtype=np.int16)

fib_leads = np.fromiter((B.lead_str(F) for F in B.fibonacci(NP2)), dtype=np.int8, count=NP2)

NFAC = 5000
fac_leads = np.fromiter((B.lead_str(f) for f in B.factorials(NFAC)), dtype=np.int8, count=NFAC)

log("sieving primes to 1e7 ...")
primes = np.array(B.primes_upto(10 ** 7), dtype=np.int64)
prime_leads = np.array([int(str(p)[0]) for p in primes], dtype=np.int8)

BEN = np.array(B.BENFORD)


def cum_maxdev(leads, Ns):
    """max|freq-Benford| over the first N entries, for each N in Ns."""
    out = []
    for N in Ns:
        c = np.bincount(leads[:N], minlength=10)[1:10]
        out.append(float(B.maxdev((c / c.sum()).tolist())))
    return out


# ----------------------------------------------------------------------
# Figure 1 -- Benford bars + 2**n & Fibonacci empirical overlay
# ----------------------------------------------------------------------
def figure_bars():
    log("Figure 1: Benford bars + 2**n / Fibonacci overlay")
    digits = np.arange(1, 10)
    c2 = np.bincount(pow2_leads, minlength=10)[1:10]; f2 = c2 / c2.sum()
    cf = np.bincount(fib_leads, minlength=10)[1:10]; ff = cf / cf.sum()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(digits, BEN, width=0.72, color=SKY, alpha=0.55,
           edgecolor=BLUE, linewidth=1.3, label="Benford  log₁₀(1+1/d)", zorder=1)
    ax.plot(digits, f2, "o", color=VERM, markersize=10, zorder=3,
            label=f"2ⁿ  (n=1..{NP2:,})")
    ax.plot(digits, ff, "D", color=GREEN, markersize=8, zorder=3,
            markerfacecolor="none", markeredgewidth=2,
            label=f"Fibonacci  (n=1..{NP2:,})")
    for d, p in zip(digits, BEN):
        ax.text(d, p + 0.006, f"{p*100:.1f}%", ha="center", va="bottom",
                fontsize=10.5, color=BLUE)
    ax.set_xticks(digits)
    ax.set_xlabel("leading digit  d")
    ax.set_ylabel("P(first digit = d)")
    ax.set_ylim(0, 0.345)
    ax.set_title("Leading digits of 2ⁿ and Fibonacci hug Benford's law")
    ax.legend(frameon=True, framealpha=0.95, loc="upper right")
    fig.tight_layout()
    return save(fig, "fig1_benford_bars.png", dpi=160)


# ----------------------------------------------------------------------
# Figure 2 -- convergence: 2**n vs n! vs primes
# ----------------------------------------------------------------------
def figure_convergence():
    log("Figure 2: convergence (log-log) 2**n vs n! vs primes")
    N2 = np.unique(np.logspace(1, math.log10(NP2), 40).astype(int))
    md2 = cum_maxdev(pow2_leads, N2)
    NF = np.unique(np.logspace(1, math.log10(NFAC), 30).astype(int))
    mdf = cum_maxdev(fac_leads, NF)

    # primes: maxdev vs number of primes pi(X), at log-spaced cutoffs
    cutoffs = np.unique(np.logspace(2, 7, 30).astype(np.int64))
    idx = np.searchsorted(primes, cutoffs, side="right")
    npr, mdp = [], []
    for k in idx:
        if k < 50:
            continue
        c = np.bincount(prime_leads[:k], minlength=10)[1:10]
        npr.append(k); mdp.append(float(B.maxdev((c / c.sum()).tolist())))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.loglog(N2, md2, "-o", color=VERM, markersize=5, label="2ⁿ  (fast)")
    ax.loglog(NF, mdf, "-D", color=GREEN, markersize=5, label="n!  (slow — Diaconis 1977)")
    ax.loglog(npr, mdp, "-s", color=BLUE, markersize=5, label="primes ≤ X  (poor & flat)")
    ax.axhline(0.5 * sum(abs(1/9 - b) for b in BEN), color=GREY, ls=":", lw=1)
    ax.set_xlabel("number of terms  N  (= π(X) for primes)")
    ax.set_ylabel("max | empirical − Benford |")
    ax.set_title("Different speeds: 2ⁿ races to Benford, n! crawls, primes never arrive")
    ax.legend(frameon=True, framealpha=0.95, loc="lower left")
    ax.grid(True, which="both", alpha=0.4)
    fig.tight_layout()
    return save(fig, "fig2_convergence.png", dpi=160)


# ----------------------------------------------------------------------
# Figure 3 -- equidistribution of {n*log10 2 mod 1} with digit bands
# ----------------------------------------------------------------------
def figure_equidistribution():
    log("Figure 3: {n*log10 2 mod 1} equidistribution + digit bands")
    l2 = math.log10(2)
    frac = (np.arange(1, NP2 + 1) * l2) % 1.0

    fig, ax = plt.subplots(figsize=(10, 5))
    # nine digit-bands [log10 d, log10(d+1)) of width log10(1+1/d)
    band_cols = [SKY, ORANGE, GREEN, VERM, PURPLE, YELLOW, BLUE, "#bcbd22", "#17becf"]
    for d in range(1, 10):
        lo, hi = math.log10(d), math.log10(d + 1)
        ax.axvspan(lo, hi, color=band_cols[d - 1], alpha=0.28, zorder=0)
        ax.axvline(hi, color="white", lw=1.0, zorder=1)        # crisp band separator
        ax.text((lo + hi) / 2, 0.55, str(d), ha="center", va="center",
                fontsize=20, fontweight="bold", color=BLACK, alpha=0.85, zorder=4)
        ax.text((lo + hi) / 2, 0.40, f"{(hi-lo)*100:.1f}%", ha="center", va="center",
                fontsize=9.5, color="#222", zorder=4)
    # empirical density of the fractional parts (should be flat ≈ 1 -> uniform)
    ax.hist(frac, bins=50, range=(0, 1), density=True, histtype="step",
            color=BLACK, linewidth=2.0, zorder=3, label="density of {n·log₁₀2}")
    ax.axhline(1.0, color=VERM, ls="--", lw=1.6, zorder=2,
               label="uniform density = 1 (Weyl)")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.3)
    ax.set_xlabel("fractional part of  n·log₁₀2   (= log₁₀ of the mantissa)")
    ax.set_ylabel("probability density")
    ax.set_title("Why 2ⁿ is Benford: n·log₁₀2 fills [0,1) uniformly; bands = P(d)")
    ax.legend(frameon=True, framealpha=0.96, loc="upper right", fontsize=11)
    ax.grid(False)
    fig.tight_layout()
    return save(fig, "fig3_equidistribution.png", dpi=160)


# ----------------------------------------------------------------------
# Figure 4 -- primes P(first digit = 1) vs cutoff X keeps oscillating
# ----------------------------------------------------------------------
def figure_primes_oscillation():
    log("Figure 4: primes P(lead=1) oscillation vs cutoff")
    is1 = (prime_leads == 1).astype(np.int64)
    pref1 = np.concatenate(([0], np.cumsum(is1)))     # pref1[i] = #lead-1 among first i primes
    Xs = np.unique(np.logspace(2, 7, 700).astype(np.int64))
    idx = np.searchsorted(primes, Xs, side="right")
    keep = idx >= 30
    Xs, idx = Xs[keep], idx[keep]
    p1 = pref1[idx] / idx

    top = float(p1.max()) * 1.04                       # show the full sawtooth (don't clip)
    log(f"  fig4 P(lead=1) range over the sweep: {p1.min():.4f} .. {p1.max():.4f}")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.semilogx(Xs, p1, "-", color=BLUE, linewidth=1.5, zorder=3,
                label="primes: P(first digit = 1) up to X")
    ax.axhline(B.BENFORD[0], color=VERM, ls="--", lw=1.8,
               label=f"Benford  {B.BENFORD[0]:.3f}")
    ax.axhline(1/9, color=GREEN, ls=":", lw=1.8, label="uniform  1/9 ≈ 0.111")
    ax.set_xlim(Xs.min(), Xs.max()); ax.set_ylim(0.10, top)
    ax.set_xlabel("cutoff  X   (primes ≤ X, log scale)")
    ax.set_ylabel("P(first digit = 1)")
    ax.set_title("Primes never settle: P(lead = 1) oscillates, with no limit")
    ax.legend(frameon=True, framealpha=0.95, loc="upper right")
    fig.tight_layout()
    return save(fig, "fig4_primes_oscillation.png", dpi=160)


# ----------------------------------------------------------------------
# Figure 5 -- generalized first-two-digit Benford, 2**n overlaid
# ----------------------------------------------------------------------
def figure_two_digit():
    log("Figure 5: generalized first-two-digit Benford + 2**n overlay")
    D = np.arange(10, 100)
    target = np.array(B.BENFORD_TWO)
    c = np.bincount(pow2_two - 10, minlength=90).astype(float)
    emp = c / c.sum()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(D, target * 100, color=SKY, alpha=0.45, zorder=1,
                    label="Benford  log₁₀(1+1/D)")
    ax.plot(D, target * 100, "-", color=BLUE, linewidth=1.6, zorder=2)
    ax.plot(D, emp * 100, "o", color=VERM, markersize=3.6, zorder=3,
            label=f"2ⁿ first-two-digits  (n with 2ⁿ≥10, N={len(pow2_two):,})")
    ax.set_xlim(10, 99); ax.set_ylim(0, target[0] * 100 * 1.25)
    ax.set_xlabel("first two digits  D")
    ax.set_ylabel("P(first two digits = D)   [%]")
    ax.set_title("The law goes deeper: first-TWO-digit Benford, with 2ⁿ overlaid")
    ax.legend(frameon=True, framealpha=0.95, loc="upper right")
    fig.tight_layout()
    return save(fig, "fig5_two_digit.png", dpi=160)


if __name__ == "__main__":
    log("=== Benford figures ===")
    d1 = figure_bars()
    d2 = figure_convergence()
    d3 = figure_equidistribution()
    d4 = figure_primes_oscillation()
    d5 = figure_two_digit()
    log("=== done ===")
    for nm, d in [("fig1_benford_bars.png", d1), ("fig2_convergence.png", d2),
                  ("fig3_equidistribution.png", d3),
                  ("fig4_primes_oscillation.png", d4), ("fig5_two_digit.png", d5)]:
        log(f"{nm:30s} {d[0]}x{d[1]}")
    with open(os.path.join(HERE, "figures.log"), "w") as f:
        f.write("\n".join(_LOG) + "\n")
