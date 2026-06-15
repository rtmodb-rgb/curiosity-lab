"""
Elementary cellular automata (ECA) engine for the Curiosity Lab Rule 30 explorable.

An ECA updates a 1-D row of binary cells. Each new cell depends on a 3-cell
neighborhood (left, center, right). We use the standard Wolfram numbering: the
8 possible neighborhoods are indexed 0..7 by `code = 4*left + 2*center + right`,
and the rule's output for that neighborhood is bit `code` of the rule number
(0..255). So Rule 30 = 0b00011110, Rule 90 = 0b01011010, etc.

Boundary convention: cells outside the array are treated as 0 (a "quiescent"
background). For a single seed evolved for N steps this is exact for the whole
populated region as long as the lattice is at least 2*N+1 wide, because the
light cone spreads at most one cell per step.

Two independent Rule-30 center-column engines are provided and are asserted to
agree in verify.py:
  * a numpy uint8 lattice (general, used as the reference), and
  * a big-integer "bitboard" engine (R is a Python int, bit i = cell i),
    where the whole row is updated in one shot via
        new = (R << 1) ^ (R | (R >> 1))
    which is exactly Rule 30 (new = left XOR (center OR right)).

Everything here is meant to be independently re-runnable and checkable.
"""
import numpy as np


# ----------------------------------------------------------------------
# Rule table helpers
# ----------------------------------------------------------------------
def rule_table(rule):
    """Return the 8-entry output table of `rule` as a uint8 array.

    table[code] = output for neighborhood code (0..7), code = 4L+2C+R.
    """
    if not (0 <= rule <= 255):
        raise ValueError("rule must be in 0..255")
    return np.array([(rule >> code) & 1 for code in range(8)], dtype=np.uint8)


# ----------------------------------------------------------------------
# Single-step update on a numpy uint8 row (zero / quiescent boundaries)
# ----------------------------------------------------------------------
def step(row, rule):
    """Advance one ECA step. `row` is a 1-D array of 0/1; cells outside are 0.

    Vectorized: builds the neighborhood code for every cell, then looks up the
    rule bit. Returns a new uint8 array of the same length.
    """
    row = np.asarray(row, dtype=np.uint8)
    left = np.empty_like(row)
    left[0] = 0
    left[1:] = row[:-1]                     # left neighbor (0 at the edge)
    right = np.empty_like(row)
    right[-1] = 0
    right[:-1] = row[1:]                     # right neighbor (0 at the edge)
    code = (left << 2) | (row << 1) | right  # neighborhood code 0..7
    return ((rule >> code) & 1).astype(np.uint8)


# ----------------------------------------------------------------------
# Full space-time diagram
# ----------------------------------------------------------------------
def evolve(rule, init=None, steps=64, width=None):
    """Return the space-time diagram as a (steps+1, W) uint8 array.

    Row 0 is the initial condition, rows 1..steps are successive updates.

    init :
        None       -> a single 1 at the center of a zero row. If `width` is
                      also None it defaults to 2*steps+1 (boundary-exact for a
                      single centered seed: the light cone never reaches the
                      edge within `steps` steps).
        array-like -> used verbatim as the initial row; `width` is taken from
                      its length (the `width` argument is ignored).
    """
    if init is None:
        if width is None:
            width = 2 * steps + 1            # boundary-exact for a center seed
        row = np.zeros(width, dtype=np.uint8)
        row[width // 2] = 1
    else:
        row = np.asarray(init, dtype=np.uint8).copy()
        width = row.size

    grid = np.empty((steps + 1, width), dtype=np.uint8)
    grid[0] = row
    for t in range(1, steps + 1):
        row = step(row, rule)
        grid[t] = row
    return grid


# ----------------------------------------------------------------------
# Rule 30 center column -- engine (a): numpy uint8 lattice
# ----------------------------------------------------------------------
def rule30_center_numpy(n):
    """Center-column bits of Rule 30 from a single seed, via a numpy lattice.

    Returns a uint8 array of length n+1: element t is the center cell after t
    steps (element 0 is the seed = 1). Uses width 2n+1 with the seed at the
    center, so the result is boundary-exact for all n steps.
    """
    width = 2 * n + 1
    c = width // 2
    row = np.zeros(width, dtype=np.uint8)
    row[c] = 1
    out = np.empty(n + 1, dtype=np.uint8)
    out[0] = row[c]
    for t in range(1, n + 1):
        row = step(row, 30)
        out[t] = row[c]
    return out


# ----------------------------------------------------------------------
# Rule 30 center column -- engine (b): big-integer bitboard
# ----------------------------------------------------------------------
def rule30_center_bits(n):
    """Center-column bits of Rule 30 from a single seed, via big-integer bits.

    The entire row of width W = 2n+1 is held in one Python int R (bit i = cell
    i). Rule 30 updates the whole row at once:

        new = (R << 1) ^ (R | (R >> 1))      # = left XOR (center OR right)
        new &= (1 << W) - 1                   # clamp to width W

    With the seed at bit W//2 and W = 2n+1, the populated triangle exactly fits
    in [0, W-1] for all n steps, so the center bit is boundary-exact. Returns a
    uint8 array of length n+1 (element t = center cell after t steps).
    """
    width = 2 * n + 1
    c = width // 2
    mask = (1 << width) - 1
    R = 1 << c                                # single centered seed
    out = np.empty(n + 1, dtype=np.uint8)
    out[0] = (R >> c) & 1
    for t in range(1, n + 1):
        R = ((R << 1) ^ (R | (R >> 1))) & mask
        out[t] = (R >> c) & 1
    return out


def rule30_center(n, method="bits"):
    """Convenience wrapper. method = 'bits' (fast) or 'numpy' (reference)."""
    if method == "bits":
        return rule30_center_bits(n)
    if method == "numpy":
        return rule30_center_numpy(n)
    raise ValueError("method must be 'bits' or 'numpy'")
