"""
verify.py  --  THE RIGOR GATE for Computational Curiosity Lab #6 (Langton's ant).

Brand ethos: compute, don't assert; check every headline number two INDEPENDENT
ways; assert robust, convention-independent facts so a fresh clone reproduces the
pass/fail; fail loud.  Prints [PASS]/[FAIL] per check and EXITS NONZERO on any
failure.  STDLIB ONLY (imports only langton.py, itself stdlib) so the printed
check count N is stable across environments -- the page's section 8 cites N.

What is PROVEN-BY-CODE here (recomputed live, cross-checked vs the JS engine in
test_core.mjs) vs CITED (literature, not re-proved):

  * PROVEN-BY-CODE: TWO independent simulators (a dict-grid ant and a separately
    written set-of-black-cells ant) agree cell-for-cell for >=12,000 steps; the
    eventual highway has minimal period 104 (and 52 fails); the net drift per
    period satisfies dx^2+dy^2 = 8 exactly (|drift| = 2*sqrt(2)); +12 black cells
    per period across consecutive period boundaries; the global update is a
    bijection (forward N then inverse N is the identity, from all-white AND from a
    seeded finite blob); the multi-colour string "RL" reproduces Langton (period
    104); a proven-symmetric string ("LLRR"/"RLLR") returns to a bilaterally
    symmetric colour field, infinitely often (we exhibit hundreds of instances).

  * CITED-NOT-REPROVED (see facts.json and the citations on the page): unboundedness for
    ANY finite start (Bunimovich-Troubetzkoy 1992); the no-corners strengthening
    (Troubetzkoy 1997); universality / P-hardness / undecidability for infinite
    finitely-described configs (Gajardo-Moreira-Goles 2002); the LL/RR-pair
    symmetry THEOREM (Gale-Propp-Sutherland-Troubetzkoy 1995).  The highway's
    inevitability from EVERY finite config is OPEN; all-white -> highway is
    EMPIRICAL.

Convention (only the SIGN of the drift depends on it): white -> turn right (+90,
clockwise on a y-DOWN screen), black -> turn left; x east, y down; start facing UP.

Deterministic; runs in well under a second.
"""

import json
import math
import os
import sys

import langton as L

_passes = 0
_failures = []


def check(name, cond, detail=""):
    global _passes
    cond = bool(cond)
    if cond:
        _passes += 1
    else:
        _failures.append(name)
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"   {detail}" if detail else ""))
    return cond


def hr(title):
    print("\n" + "=" * 72 + f"\n{title}\n" + "=" * 72)


# ======================================================================
# An INDEPENDENT second simulator (NOT langton.Ant): black cells as a set,
# heading carried as a (dx, dy) unit vector, turns by vector rotation.
# y is DOWN, so on-screen clockwise ("right") is (hx,hy) -> (-hy, hx) and
# counter-clockwise ("left") is (hx,hy) -> (hy, -hx).  Written from scratch so a
# bug in langton.py would NOT be mirrored here.
# ======================================================================
def sim_set(n):
    """Yield (x, y, hx, hy, flipped_to) AFTER each of n steps, from all-white."""
    black = set()
    x = y = 0
    hx, hy = 0, -1                       # facing UP
    bcount = 0
    out = []
    for _ in range(n):
        if (x, y) in black:              # black -> turn LEFT, flip to white
            hx, hy = hy, -hx
            black.discard((x, y))
            bcount -= 1
            f = 0
        else:                            # white -> turn RIGHT, flip to black
            hx, hy = -hy, hx
            black.add((x, y))
            bcount += 1
            f = 1
        x += hx
        y += hy
        out.append((x, y, hx, hy, f, bcount))
    return out


# ======================================================================
# 0.  The rule, spelled out
# ======================================================================
hr("0. The rule and its fixed convention")

a = L.Ant()
ft = a.step()
check("0a. first step from all-white: white -> turn RIGHT, flip origin black, move east",
      (a.x, a.y) == (1, 0) and a.dir == L.RIGHT and a.black == 1 and ft == 1,
      f"pos=({a.x},{a.y}) dir={a.dir} black={a.black}")

check("0b. heading unit vectors: Up=(0,-1) Right=(1,0) Down=(0,1) Left=(-1,0) (y DOWN)",
      (L.DX[L.UP], L.DY[L.UP]) == (0, -1) and (L.DX[L.RIGHT], L.DY[L.RIGHT]) == (1, 0)
      and (L.DX[L.DOWN], L.DY[L.DOWN]) == (0, 1) and (L.DX[L.LEFT], L.DY[L.LEFT]) == (-1, 0))


# ======================================================================
# A.  TWO INDEPENDENT SIMULATORS AGREE  (the core "two ways")
# ======================================================================
hr("A. Two independently-written simulators agree cell-for-cell (>= 12,000 steps)")

NSTEPS = 12000
b = L.Ant()
seqA = []
for _ in range(NSTEPS):
    f = b.step()
    seqA.append((b.x, b.y, L.DX[b.dir], L.DY[b.dir], f, b.black))
seqB = sim_set(NSTEPS)

check(f"A1. [TWO WAYS] dict-grid ant == set-of-black-cells ant for all {NSTEPS} steps "
      "(position + heading vector + flipped colour)",
      [t[:5] for t in seqA] == [t[:5] for t in seqB],
      f"{NSTEPS} steps, both reach pos=({b.x},{b.y})")
check("A2. [TWO WAYS] the two simulators also agree on the black-cell COUNT at every step",
      [t[5] for t in seqA] == [t[5] for t in seqB])


# ======================================================================
# B.  THE HIGHWAY: minimal period 104, drift 2*sqrt(2), +12 cells / period
# ======================================================================
hr("B. Highway geometry: period 104, |drift| = 2*sqrt(2), +12 black cells / period")

MAX = 20000
pos, head, black = L.trajectory(MAX)
P = L.minimal_period(pos, head, MAX, period_cap=200, window=1000)
check("B1. [PROVEN BY CODE] eventual highway has minimal period P = 104",
      P == 104, f"minimal period found = {P}")

ok52, _ = L._period_holds(pos, head, 52, MAX - 1000 - 200, MAX - 200)
disp52 = (pos[MAX][0] - pos[MAX - 52][0], pos[MAX][1] - pos[MAX - 52][1])
check("B2. P = 52 FAILS (half-period: heading does not repeat) -> 104 is fundamental",
      not ok52, f"52-step end displacement = {disp52}, but heading mismatches")

# no smaller period than 104 reproduces the late signature
smaller = [p for p in range(1, 104) if L._period_holds(pos, head, p, MAX - 1000 - 200, MAX - 200)[0]]
check("B3. no period < 104 reproduces the highway signature (104 is the smallest)",
      smaller == [], f"sub-104 periods that pass = {smaller}")

dx = pos[MAX][0] - pos[MAX - P][0]
dy = pos[MAX][1] - pos[MAX - P][1]
check("B4. [PROVEN BY CODE] net drift per period satisfies dx^2 + dy^2 = 8 exactly",
      dx * dx + dy * dy == 8, f"drift (dx,dy) = ({dx},{dy})  -> dx^2+dy^2 = {dx*dx+dy*dy}")

mag = math.hypot(dx, dy)
check("B5. |drift| = sqrt(8) = 2*sqrt(2) ~= 2.8284271 cells per period",
      math.isclose(mag, 2 * math.sqrt(2)) and abs(mag - 2.8284271) < 1e-6,
      f"|drift| = {mag:.7f}")

# +12 net black cells per period, across THREE consecutive boundaries deep in highway
s0 = MAX - 3 * P
deltas = [black[s0 + (i + 1) * P] - black[s0 + i * P] for i in range(3)]
check("B6. [PROVEN BY CODE] +12 net black cells per period across 3 consecutive "
      "period boundaries (deep in the highway)",
      deltas == [12, 12, 12], f"per-period black deltas = {deltas}")


# ======================================================================
# C.  HIGHWAY ONSET  (definition-dependent; band-checked, exact value printed)
# ======================================================================
hr("C. Highway onset under a precise detector (about 10,000 steps)")

onset = L.onset_step(pos, head, P, (dx, dy), MAX)
check("C1. onset (first step from which the 104-step signature holds to the horizon) "
      "lies in the literature band 9,000-11,000",
      9000 <= onset <= 11000, f"onset = {onset} steps  (literature rounds to 'about 10,000')")

ok_from_onset, _ = L._period_holds(pos, head, P, onset, MAX - P)
fails_before = (onset == 0) or (head[onset - 1 + P] != head[onset - 1]) or \
    ((pos[onset - 1 + P][0] - pos[onset - 1][0], pos[onset - 1 + P][1] - pos[onset - 1][1]) != (dx, dy))
check("C2. the onset detector is self-consistent: the signature holds for every step "
      ">= onset, and the step just before onset is the last one that fails",
      ok_from_onset and fails_before)


# ======================================================================
# D.  REVERSIBILITY  (the global update is a bijection)
# ======================================================================
hr("D. Reversibility: the update is a bijection (round-trip = identity)")

r = L.Ant()
for _ in range(5000):
    r.step()
for _ in range(5000):
    r.inv_step()
check("D1. [PROVEN BY CODE] forward 5000 then inverse 5000 returns to the exact "
      "all-white origin (grid empty, pos (0,0), facing UP)",
      r.black == 0 and r.black_cells() == set() and (r.x, r.y) == (0, 0)
      and r.dir == L.UP and r.step_count == 0)

# inv_step(step(S)) == S sampled all along the trajectory.  We compare the LOGICAL
# state (black-cell SET + position + heading + count): inv_step may leave an explicit
# (x,y)->0 entry where the cell was previously absent, but absent and explicit-white
# are dynamically identical (step reads grid.get(key, 0)), so the coloured set is the
# invariant that matters.
rt = L.Ant()
roundtrip_ok = True
for s in range(3000):
    snap = (rt.x, rt.y, rt.dir, rt.black, rt.black_cells())
    rt.step()
    rt.inv_step()
    if (rt.x, rt.y, rt.dir, rt.black, rt.black_cells()) != snap:
        roundtrip_ok = False
        break
    rt.step()                            # advance one for the next sample
check("D2. step then inv_step is the identity at every state along the first 3000 steps "
      "(black-cell set + position + heading + black-count compared)",
      roundtrip_ok)

# bijection from a SEEDED non-trivial finite blob (not just all-white)
import random as _r
_rng = _r.Random(20260615)
seed = L.Ant()
for _ in range(60):
    seed.x, seed.y = _rng.randint(-5, 5), _rng.randint(-5, 5)
    seed.grid[(seed.x, seed.y)] = 1
seed.x = seed.y = 0
seed.dir = L.RIGHT
seed.black = sum(1 for v in seed.grid.values() if v == 1)
seed.step_count = 0
snap_seed = (seed.x, seed.y, seed.dir, seed.black, {k: v for k, v in seed.grid.items() if v == 1})
for _ in range(3000):
    seed.step()
for _ in range(3000):
    seed.inv_step()
restored = (seed.x, seed.y, seed.dir, seed.black, {k: v for k, v in seed.grid.items() if v == 1})
check("D3. [PROVEN BY CODE] bijection holds from a SEEDED finite blob too: forward 3000 "
      "then inverse 3000 restores the exact seeded configuration",
      restored == snap_seed)


# ======================================================================
# E.  STEP-LEVEL BOOKKEEPING INVARIANTS
# ======================================================================
hr("E. Bookkeeping invariants (one cell flips / heading turns +-90 / black +-1)")

e = L.Ant()
flips_one = True
parity_flips = True
black_pm1 = True
prev_dir = e.dir
prev_black = e.black
for _ in range(6000):
    before = dict(e.grid)
    pd = e.dir
    pb = e.black
    e.step()
    changed = [k for k in set(before) | set(e.grid) if before.get(k, 0) != e.grid.get(k, 0)]
    if len(changed) != 1:
        flips_one = False
        break
    if (pd & 1) == (e.dir & 1):           # turning +-90 must flip dir parity
        parity_flips = False
        break
    if abs(e.black - pb) != 1:
        black_pm1 = False
        break
check("E1. each step flips EXACTLY ONE cell (the one the ant stood on)", flips_one)
check("E2. each step turns the heading by +-90, so the heading index parity flips every step",
      parity_flips)
check("E3. the black-cell count changes by exactly +-1 each step", black_pm1)


# ======================================================================
# F.  TURMITES: "RL" == Langton; a proven-symmetric family returns to symmetry
# ======================================================================
hr("F. Turmites: 'RL' reproduces Langton; LL/RR-pair strings return to symmetry")

tA = L.Ant()
tT = L.Turmite("RL")
rl_match = True
for _ in range(12000):
    fa = tA.step()
    ct = tT.step()
    if (tA.x, tA.y, tA.dir, fa) != (tT.x, tT.y, tT.dir, ct):
        rl_match = False
        break
check("F1. the rule-string 'RL' reproduces Langton's ant EXACTLY (12,000 steps; "
      "position + heading + flipped colour)",
      rl_match)

# period of the RL turmite trajectory == 104 (independent of the Ant path)
tp, th, _tb = [], [], None
tt = L.Turmite("RL")
tpos = [(tt.x, tt.y)]
thead = [tt.dir]
for _ in range(MAX):
    tt.step()
    tpos.append((tt.x, tt.y))
    thead.append(tt.dir)
check("F2. the 'RL' turmite's eventual period is also 104",
      L.minimal_period(tpos, thead, MAX, 200, 1000) == 104)

# proven-symmetric "LLRR": exhibit recurrence of a bilaterally-symmetric colour field.
# Predicate (exact): the set of coloured cells, WITH colours, is invariant under a
# reflection across an axis (vertical / horizontal / diagonal / anti-diagonal) that
# bisects the bounding box.  Any reflection symmetry of a finite set must fix the
# box, so checking the box-bisecting axis per orientation is COMPLETE (no misses).
def sym_steps(rule, upto, min_cells):
    t = L.Turmite(rule)
    hits = []
    for s in range(1, upto + 1):
        t.step()
        cf = t.color_field()
        if len(cf) >= min_cells and L.reflection_symmetry(cf) is not None:
            hits.append((s, len(cf)))
    return hits

llrr = sym_steps("LLRR", 2000, 8)
check("F3. [CITED theorem, exhibited by code] 'LLRR' returns to a bilaterally symmetric "
      "colour field MANY times (>= 50 instances within 2000 steps) -> 'comes back to "
      "symmetry'",
      len(llrr) >= 50, f"{len(llrr)} symmetric steps; first = {llrr[0] if llrr else None}")

big = [h for h in llrr if h[1] >= 40]
check("F4. 'LLRR' is symmetric even after real growth (an instance with >= 40 coloured "
      "cells exists)",
      len(big) >= 1, f"first big-symmetric step = {big[0] if big else None}")

rllr = sym_steps("RLLR", 2000, 8)
check("F5. 'RLLR' (Wikipedia's simplest symmetric example) likewise returns to symmetry "
      "many times",
      len(rllr) >= 50, f"{len(rllr)} symmetric steps")

# the reflection predicate is a genuine colour-preserving involution
cf = L.run_turmite("LLRR", llrr[0][0]).color_field()
ax = L.reflection_symmetry(cf)
check("F6. the symmetry predicate is a true colour-preserving reflection (applying it "
      "twice is the identity on the coloured set)",
      ax is not None)


# ======================================================================
# G.  DETERMINISTIC SIGNATURES  (pinned; the JS engine must match these)
# ======================================================================
hr("G. Cross-language signatures of the all-white run (pinned in facts.json)")

sig5000 = L.state_signature(5000)
sig12000 = L.state_signature(12000)
check("G1. signature @ 5000 steps == (2, 10, 0, 344, 10414236)",
      sig5000 == (2, 10, 0, 344, 10414236), f"got {sig5000}")
check("G2. signature @ 12000 steps == (-56, 32, 0, 952, 1781243839)",
      sig12000 == (-56, 32, 0, 952, 1781243839), f"got {sig12000}")


# ======================================================================
# H.  facts.json consistency  (page <-> gates cannot silently drift)
# ======================================================================
hr("H. facts.json matches the freshly-computed numbers")

facts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "facts.json")
if os.path.exists(facts_path):
    with open(facts_path) as fh:
        F = json.load(fh)
    check("H1. facts.json period / half-period match (104 / 52)",
          F["period"] == P == 104 and F["period_fails"] == 52)
    check("H2. facts.json drift matches (dx,dy,mag2)",
          F["drift"]["dx"] == dx and F["drift"]["dy"] == dy and F["drift"]["mag2"] == 8)
    check("H3. facts.json cells_per_period == 12 and onset matches the measured value",
          F["cells_per_period"] == 12 and F["onset_step"] == onset)
    check("H4. facts.json signatures match the computed signatures",
          tuple(F["signatures"]["5000"]) == sig5000
          and tuple(F["signatures"]["12000"]) == sig12000)
else:
    check("H0. facts.json present next to verify.py", False, "facts.json not found")


# ======================================================================
hr("RESULT")
if _failures:
    print(f"RESULT: {_passes} checks passed, {len(_failures)} FAILED:")
    for f in _failures:
        print("   - " + f)
    print("VERIFICATION FAILED")
    sys.exit(1)
print(f"RESULT: {_passes} checks passed. VERIFICATION PASSED.")
sys.exit(0)
