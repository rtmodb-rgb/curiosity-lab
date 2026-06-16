"""
langton.py -- reference engine for Computational Curiosity Lab #6 (Langton's ant).

STDLIB ONLY, so verify.py's printed check count is stable across environments.

CONVENTION (fixed once; stated on the page)
-------------------------------------------
  * White cell (0)  -> turn 90 deg RIGHT (clockwise on screen), flip to black, step.
  * Black cell (1)  -> turn 90 deg LEFT  (counter-clockwise),    flip to white, step.
  * Coordinates: x -> east (right), y -> DOWN  (the screen / <canvas> convention).
  * The ant starts at the origin (0, 0) facing UP, on an all-white grid.

Headings are indices 0..3 = [Up, Right, Down, Left] -- the *visual clockwise*
order on a y-DOWN screen -- so "turn right" = +1 (mod 4) and "turn left" = -1.
Unit step vectors (y points DOWN): DX = [0, 1, 0, -1], DY = [-1, 0, 1, 0].

Only the SIGN of the drift *direction* depends on this convention (chirality
flips x, y-up/down flips y).  The headline invariants are convention-INDEPENDENT
and verify.py recomputes every one of them two independent ways:
    period = 104 steps,  |drift| = 2*sqrt(2),  +12 black cells / period,
    reversibility (the global update is a bijection).

Multi-colour generalisation (turmites): colours cycle 0->1->...->(n-1)->0 as the
ant leaves a cell, and an L/R rule-string indexed by the current colour gives the
turn.  Langton's ant is the 2-colour string "RL" (colour 0 = white -> R,
colour 1 = black -> L).  This file's `Turmite('RL')` reproduces `Ant` exactly.
"""

from __future__ import annotations

# Headings: 0=Up 1=Right 2=Down 3=Left  (visual clockwise on a y-DOWN screen).
UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3
DX = (0, 1, 0, -1)    # +x is east  (RIGHT)
DY = (-1, 0, 1, 0)    # +y is south (DOWN);  UP decreases y

# A 31-bit prime: polynomial-hash modulus.  Every intermediate product stays well
# below 2**53, so JavaScript's Number reproduces this hash exactly (see core.js).
SIG_MOD = 2147483647


# ----------------------------------------------------------------------
# The two-colour ant  (sparse dict grid: only touched cells are stored)
# ----------------------------------------------------------------------
class Ant:
    """Langton's ant on a sparse grid: ``grid[(x, y)] -> 0/1`` (absent = white)."""

    __slots__ = ("grid", "x", "y", "dir", "step_count", "black")

    def __init__(self) -> None:
        self.grid: dict[tuple[int, int], int] = {}
        self.x = 0
        self.y = 0
        self.dir = UP
        self.step_count = 0
        self.black = 0           # number of cells currently coloured black (=1)

    def color(self, x: int, y: int) -> int:
        return self.grid.get((x, y), 0)

    def step(self) -> int:
        """Advance one step.  Returns the colour the current cell is flipped TO."""
        key = (self.x, self.y)
        c = self.grid.get(key, 0)
        if c == 0:                       # white -> turn RIGHT, flip to black
            self.dir = (self.dir + 1) & 3
            self.grid[key] = 1
            self.black += 1
            flipped_to = 1
        else:                            # black -> turn LEFT, flip to white
            self.dir = (self.dir + 3) & 3
            self.grid[key] = 0
            self.black -= 1
            flipped_to = 0
        self.x += DX[self.dir]
        self.y += DY[self.dir]
        self.step_count += 1
        return flipped_to

    def inv_step(self) -> None:
        """Undo exactly one forward step (the global update is a bijection)."""
        px = self.x - DX[self.dir]       # move back onto the previously-flipped cell
        py = self.y - DY[self.dir]
        c_now = self.grid.get((px, py), 0)
        c_pre = 1 - c_now                # that cell was flipped during the forward step
        self.grid[(px, py)] = c_pre
        if c_pre == 1:
            self.black += 1
        else:
            self.black -= 1
        # recover the previous heading from the cell's restored (pre-step) colour
        if c_pre == 0:                   # had been white -> we turned right (+1); undo -1
            self.dir = (self.dir + 3) & 3
        else:                            # had been black -> we turned left (-1); undo +1
            self.dir = (self.dir + 1) & 3
        self.x = px
        self.y = py
        self.step_count -= 1

    def black_cells(self) -> set[tuple[int, int]]:
        return {k for k, v in self.grid.items() if v == 1}


# ----------------------------------------------------------------------
# Convenience runners / trajectory recorders
# ----------------------------------------------------------------------
def run_from_all_white(n: int) -> Ant:
    a = Ant()
    for _ in range(n):
        a.step()
    return a


def trajectory(n: int):
    """Record the all-white run.  Returns three lists of length n+1 (index = #steps
    taken so far): ``pos[i] = (x, y)``, ``head[i] = dir``, ``black[i]`` = #black cells."""
    a = Ant()
    pos = [(a.x, a.y)]
    head = [a.dir]
    black = [a.black]
    for _ in range(n):
        a.step()
        pos.append((a.x, a.y))
        head.append(a.dir)
        black.append(a.black)
    return pos, head, black


def state_signature(n: int):
    """A deterministic, cross-language-exact fingerprint of the all-white run after
    ``n`` steps: ``(x, y, dir, black_count, hash_of_black_set)``.  The hash is a
    polynomial over the lexicographically-sorted black cells, mod a 31-bit prime
    (every product < 2**53, so core.js's Number path matches bit-for-bit)."""
    a = run_from_all_white(n)
    blacks = sorted(k for k, v in a.grid.items() if v == 1)
    h = 0
    for (x, y) in blacks:
        h = (h * 1000003 + (x + 1_000_000) * 2000003 + (y + 1_000_000)) % SIG_MOD
    return (a.x, a.y, a.dir, a.black, h)


# ----------------------------------------------------------------------
# Highway analysis: minimal period, drift, cells/period, onset
# ----------------------------------------------------------------------
def _period_holds(pos, head, P, lo, hi):
    """True iff over s in [lo, hi) the P-step displacement is constant AND the
    heading repeats.  Returns (ok, drift_or_None)."""
    d0 = (pos[lo + P][0] - pos[lo][0], pos[lo + P][1] - pos[lo][1])
    for s in range(lo, hi):
        if head[s + P] != head[s]:
            return False, None
        if (pos[s + P][0] - pos[s][0], pos[s + P][1] - pos[s][1]) != d0:
            return False, None
    return True, d0


def minimal_period(pos, head, max_steps, period_cap=200, window=1000):
    """Smallest P (1..period_cap) whose displacement signature is exactly periodic
    over the last `window` steps of the run.  Multiples of the true period also
    pass, so the *smallest* P is the fundamental period (104 for Langton)."""
    lo = max_steps - window - period_cap
    for P in range(1, period_cap + 1):
        ok, _ = _period_holds(pos, head, P, lo, lo + window)
        if ok:
            return P
    return None


def onset_step(pos, head, P, drift, max_steps):
    """First step from which the P-step signature (displacement == `drift` and
    heading repeats) holds for ALL later s up to the horizon.  Defined as
    (last step where it fails) + 1; 0 if it never fails."""
    onset = 0
    for s in range(0, max_steps - P + 1):
        if head[s + P] != head[s] or \
           (pos[s + P][0] - pos[s][0], pos[s + P][1] - pos[s][1]) != drift:
            onset = s + 1
    return onset


def detect_highway(max_steps=20000, period_cap=200, window=1000):
    """Run from all-white; return the eventual-highway descriptors.

    ``{period, dx, dy, drift_mag2, cells_per_period, onset_step}``.
    Drift is measured at the very end of the run (deep in the highway)."""
    pos, head, black = trajectory(max_steps)
    P = minimal_period(pos, head, max_steps, period_cap, window)
    if P is None:
        raise RuntimeError(f"no period <= {period_cap} found within {max_steps} steps")
    dx = pos[max_steps][0] - pos[max_steps - P][0]
    dy = pos[max_steps][1] - pos[max_steps - P][1]
    cells = black[max_steps] - black[max_steps - P]
    onset = onset_step(pos, head, P, (dx, dy), max_steps)
    return {
        "period": P,
        "dx": dx,
        "dy": dy,
        "drift_mag2": dx * dx + dy * dy,
        "cells_per_period": cells,
        "onset_step": onset,
    }


# ----------------------------------------------------------------------
# Multi-colour turmites  ("RL" == Langton's ant)
# ----------------------------------------------------------------------
def turn(dir_: int, ch: str) -> int:
    """Apply one turn letter to a heading index.  'R' = right (+1), 'L' = left (-1)."""
    return (dir_ + 1) & 3 if ch == "R" else (dir_ + 3) & 3


class Turmite:
    """A multi-colour ant.  ``rule[c]`` in {'L','R'} is the turn taken on a cell of
    colour ``c``; colours cycle 0->1->...->(n-1)->0 as the ant leaves.  The 2-colour
    string 'RL' is Langton's ant under this file's convention."""

    __slots__ = ("rule", "n", "grid", "x", "y", "dir", "step_count")

    def __init__(self, rule: str) -> None:
        rule = rule.upper()
        if not rule or any(c not in "LR" for c in rule):
            raise ValueError("rule must be a non-empty string of 'L'/'R'")
        self.rule = rule
        self.n = len(rule)
        self.grid: dict[tuple[int, int], int] = {}
        self.x = 0
        self.y = 0
        self.dir = UP
        self.step_count = 0

    def step(self) -> int:
        """Advance one step; returns the colour the current cell becomes."""
        key = (self.x, self.y)
        c = self.grid.get(key, 0)
        self.dir = turn(self.dir, self.rule[c])
        nc = (c + 1) % self.n
        self.grid[key] = nc
        self.x += DX[self.dir]
        self.y += DY[self.dir]
        self.step_count += 1
        return nc

    def color_field(self):
        """``{(x, y): colour}`` for every non-zero (non-white) cell."""
        return {k: v for k, v in self.grid.items() if v != 0}


def run_turmite(rule: str, n: int) -> Turmite:
    t = Turmite(rule)
    for _ in range(n):
        t.step()
    return t


# ----------------------------------------------------------------------
# Bilateral-symmetry predicate (for the proven LL/RR-pair family, Gale et al. 1995)
# ----------------------------------------------------------------------
def reflection_symmetry(color_field):
    """Search for a single mirror axis (vertical, horizontal, or either diagonal)
    that maps the colour field onto itself (positions AND colours).  Axes are
    allowed on the integer or half-integer lattice (so the centre may sit on a cell
    or between two cells).  Returns the first axis found as a short tag, else None.

    Vertical    x = a/2 : (x, y) -> (a - x, y)
    Horizontal  y = b/2 : (x, y) -> (x, b - y)
    Diagonal  (slope +1, through a lattice point): (x, y) -> (y + k, x - k)
    Anti-diag (slope -1):                           (x, y) -> (m - y, m - x)
    """
    cells = color_field
    if not cells:
        return None
    xs = [p[0] for p in cells]
    ys = [p[1] for p in cells]

    def symmetric(maps):
        for (x, y), c in cells.items():
            mx, my = maps(x, y)
            if cells.get((mx, my)) != c:
                return False
        return True

    # vertical mirror x = a/2  -> 2x reflection point a = (min_x + max_x) is the
    # only candidate that can map the bounding box to itself
    a = min(xs) + max(xs)
    if symmetric(lambda x, y, a=a: (a - x, y)):
        return f"vertical x={a/2:g}"
    b = min(ys) + max(ys)
    if symmetric(lambda x, y, b=b: (x, b - y)):
        return f"horizontal y={b/2:g}"
    # diagonal slope +1 through point: x - y = const must be symmetric about its mean
    k = None
    diffs = [x - y for x in (min(xs), max(xs)) for y in (min(ys), max(ys))]
    kk = (min(diffs) + max(diffs))
    if kk % 2 == 0:
        k = kk // 2
        if symmetric(lambda x, y, k=k: (y + k, x - k)):
            return f"diagonal x-y={k}"
    sums = [x + y for x in (min(xs), max(xs)) for y in (min(ys), max(ys))]
    mm = (min(sums) + max(sums))
    if mm % 2 == 0:
        m = mm // 2
        if symmetric(lambda x, y, m=m: (m - y, m - x)):
            return f"antidiagonal x+y={m}"
    return None


def first_symmetric_step(rule: str, max_steps: int, min_cells: int = 8):
    """First step (1..max_steps) at which `rule`'s colour field has >= `min_cells`
    coloured cells AND admits a reflection symmetry.  Returns (step, axis) or None.

    For the proven LL/RR-pair family (Gale-Propp-Sutherland-Troubetzkoy 1995) such
    steps recur infinitely often; we only need to exhibit one after real growth."""
    t = Turmite(rule)
    for s in range(1, max_steps + 1):
        t.step()
        cf = t.color_field()
        if len(cf) >= min_cells:
            axis = reflection_symmetry(cf)
            if axis is not None:
                return s, axis
    return None


if __name__ == "__main__":
    print("convention: white->R(+90 cw), black->L(-90 ccw); y DOWN; start facing UP")
    hw = detect_highway()
    print("highway:", hw)
    sig5000 = state_signature(5000)
    print("signature @5000:", sig5000)
    a = Ant()
    for _ in range(5000):
        a.step()
    for _ in range(5000):
        a.inv_step()
    print("reversibility @5000: black=%d pos=(%d,%d) dir=%d -> %s"
          % (a.black, a.x, a.y, a.dir,
             "OK" if (a.black == 0 and a.x == 0 and a.y == 0 and a.dir == UP) else "FAIL"))
    print("RL == Langton period:", detect_highway()["period"])
    for r in ("LLRR", "RLLR", "LRRL"):
        print(f"symmetry {r}:", first_symmetric_step(r, 2000))
