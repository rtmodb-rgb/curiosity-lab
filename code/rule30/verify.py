"""
Independent verification of the claims featured in the Rule 30 explorable.
Run:  python3 verify.py

Design goals (same rigor bar as the rest of the Curiosity Lab):
  * DEFINITIVE claims (A, B, engine self-test) are proven by exact integer / bit
    methods and asserted with exact equality -- no tolerances, no floats.
  * The EMPIRICAL claim (C) about the Rule 30 center column is clearly labeled
    as an observation, NOT a proof. Whether the density is exactly 1/2, and even
    whether the column is non-periodic, are OPEN problems (Wolfram's 2019
    Rule 30 Prize). We never call the column "random".

Self-contained, deterministic, and fast (full run well under ~60 s).
"""
import math
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import eca

PASS = []   # collected (name, ok) results for the final summary


def hr(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def record(name, ok):
    PASS.append((name, bool(ok)))
    print(f"   -> {name}: {'PASS' if ok else 'FAIL'}")


# ======================================================================
# ENGINE SELF-TEST (DEFINITIVE): step() reproduces every rule's truth table
# ======================================================================
hr("ENGINE SELF-TEST: step() matches the Wolfram truth table for all 256 rules")
mismatch = 0
for rule in range(256):
    for nb in range(8):                       # neighborhood code = 4L+2C+R
        L, C, R = (nb >> 2) & 1, (nb >> 1) & 1, nb & 1
        out = int(eca.step(np.array([L, C, R], np.uint8), rule)[1])
        if out != ((rule >> nb) & 1):
            mismatch += 1
print(f"   checked 256 rules x 8 neighborhoods = 2048 cases; mismatches = {mismatch}")
record("engine self-test (all rules)", mismatch == 0)


# ======================================================================
# CLAIM A (DEFINITIVE): Rule 90 == Pascal's triangle mod 2 (Sierpinski)
# ======================================================================
hr("CLAIM A (DEFINITIVE): Rule 90 from a single seed == Pascal's triangle mod 2")
T = 512   # spec asks for "at least 256"; we exceed it to show robustness
print(f"   Simulating Rule 90 for T={T} rows, and independently computing")
print("   Pascal mod 2 via Lucas' theorem: C(t,k) is ODD  <=>  (k & ~t) == 0")
print("   (i.e. the binary digits of k are a submask of those of t).")

grid = eca.evolve(90, steps=T)                # width = 2T+1, single centered seed
c = grid.shape[1] // 2
all_match = True
checked_rows = 0
for t in range(T + 1):
    # Rule 90 leaves cell (t,x) non-zero only where (t+x) is even; on that
    # sublattice cell value == C(t,(t+x)/2) mod 2.  Read x = -t,-t+2,...,t so
    # that k = (t+x)/2 runs 0..t -> one full Pascal row of length t+1.
    xs = c + np.arange(-t, t + 1, 2)
    sim_row = grid[t, xs]
    k = np.arange(t + 1, dtype=np.int64)
    lucas_row = ((k & ~np.int64(t)) == 0).astype(np.uint8)   # 1 iff C(t,k) odd
    if not np.array_equal(sim_row, lucas_row):
        all_match = False
        print(f"   !! mismatch at row t={t}")
        break
    checked_rows += 1
print(f"   rows compared element-by-element and identical: {checked_rows} of {T + 1}")
# extra independent cross-check on a couple of rows using math.comb directly
spot_ok = True
for t in (97, 200, 511):
    k = np.arange(t + 1)
    direct = np.array([math.comb(t, int(kk)) & 1 for kk in k], dtype=np.uint8)
    lucas = ((k.astype(np.int64) & ~np.int64(t)) == 0).astype(np.uint8)
    spot_ok = spot_ok and np.array_equal(direct, lucas)
print(f"   spot-check Lucas vs math.comb(t,k)&1 on rows 97/200/511: "
      f"{'identical' if spot_ok else 'MISMATCH'}")
record("Claim A: Rule 90 = Pascal mod 2", all_match and spot_ok)


# ======================================================================
# CLAIM B (DEFINITIVE): the two Rule-30 center-column engines agree
# ======================================================================
hr("CLAIM B (DEFINITIVE): two independent Rule-30 center-column engines agree")
N_B = 2000
print(f"   N={N_B}.  Engine (a): numpy uint8 lattice, width {2*N_B+1} (boundary-exact).")
print(f"            Engine (b): big-integer bitboard, new=(R<<1)^(R|(R>>1)).")
ca = eca.rule30_center_numpy(N_B)
cb = eca.rule30_center_bits(N_B)
same_shape = (ca.shape == cb.shape == (N_B + 1,))
identical = same_shape and np.array_equal(ca, cb)
print(f"   shapes equal ({ca.shape} vs {cb.shape}): {same_shape}")
print(f"   center columns identical element-by-element for all {N_B+1} entries: {identical}")
record("Claim B: two Rule-30 engines agree", identical)


# ======================================================================
# CLAIM C (EMPIRICAL -- OPEN PROBLEM): Rule 30 center-column statistics
# ======================================================================
hr("CLAIM C (EMPIRICAL, OPEN): Rule 30 center-column statistics at N=100000")
N_C = 100000
col = eca.rule30_center_bits(N_C)             # boundary-exact, length N_C+1
L = len(col)
ones = int(col.sum())
frac = ones / L

# 2-block (overlapping pair) distribution
pairs = (col[:-1].astype(np.int64) << 1) | col[1:].astype(np.int64)
pc = np.bincount(pairs, minlength=4)
npairs = pc.sum()

# runs (maximal constant blocks)
change = np.flatnonzero(col[1:] != col[:-1])
run_starts = np.concatenate(([0], change + 1))
run_ends = np.concatenate((change + 1, [L]))
run_len = run_ends - run_starts
run_val = col[run_starts]
nruns = len(run_len)
max_run0 = int(run_len[run_val == 0].max()) if np.any(run_val == 0) else 0
max_run1 = int(run_len[run_val == 1].max()) if np.any(run_val == 1) else 0

# single-bit Shannon entropy (bits per cell)
def H(ps):
    ps = ps[ps > 0]
    return float(-(ps * np.log2(ps)).sum())
H1 = H(np.array([1 - frac, frac]))

# block-entropy-rate estimate for L=8 (256 patterns, ~1e5 samples: well sampled)
BL = 8
win = sliding_window_view(col.astype(np.int64), BL)
weights = (1 << np.arange(BL - 1, -1, -1)).astype(np.int64)
codes = win @ weights
bc = np.bincount(codes, minlength=1 << BL)
HBL = H(bc / bc.sum())

print(f"   column length (incl. apex)      : {L}")
print(f"   number of 1s                    : {ones}")
print(f"   density of 1s                   : {frac:.9f}")
print(f"   |density - 0.5|                 : {abs(frac - 0.5):.9f}")
print(f"   2-block counts [00,01,10,11]    : {pc.tolist()}  (of {npairs} pairs)")
print(f"   2-block freqs  [00,01,10,11]    : "
      f"{[round(x, 5) for x in (pc / npairs).tolist()]}")
print(f"   number of runs                  : {nruns}")
print(f"   mean run length                 : {run_len.mean():.4f}")
print(f"   longest run of 0s / 1s          : {max_run0} / {max_run1}")
print(f"   single-bit Shannon entropy      : {H1:.6f} bits/cell  (max = 1.0)")
print(f"   8-block entropy rate (H_8 / 8)  : {HBL/BL:.6f} bits/cell  "
      f"(finite-sample estimate)")
print()
print("   INTERPRETATION (read carefully):")
print("   * These are EMPIRICAL, finite-sample statistics. The density is very")
print("     close to 1/2 and the entropy is very close to maximal, which is")
print("     CONSISTENT WITH but does NOT PROVE that the column is 'random'.")
print("   * It is an OPEN PROBLEM whether the asymptotic density is exactly 1/2,")
print("     and even whether the center column is non-periodic at all. These are")
print("     two of the three questions in Wolfram's 2019 Rule 30 Prize.")
print("   * We therefore make NO claim of randomness -- only that no periodicity")
print("     or bias is detectable at N=100000.")
# Claim C "passes" only in the sense of being computed & sanely bounded; it is
# explicitly NOT a proof. We sanity-gate the numbers, not the open question.
sane = (0.0 < frac < 1.0) and (0.49 < frac < 0.51) and (0.99 < H1 <= 1.0) and nruns > 0
record("Claim C: stats computed & within sane bounds (NOT a randomness proof)", sane)


# ======================================================================
# CLAIM D (SANITY): print the first rows so a human can eyeball them
# ======================================================================
hr("CLAIM D (SANITY): first 16 rows -- eyeball against the literature")
def show(grid, on="#", off="."):
    for r in grid:
        print("   " + "".join(on if v else off for v in r))

print("Rule 30 from a single seed (left side regular, right side chaotic):")
show(eca.evolve(30, steps=15))
print("\nRule 90 from a single seed (Sierpinski triangle):")
show(eca.evolve(90, steps=15))


# ======================================================================
# SUMMARY
# ======================================================================
hr("SUMMARY")
for name, ok in PASS:
    print(f"   [{'PASS' if ok else 'FAIL'}] {name}")
fails = [n for n, ok in PASS if not ok]
print()
if fails:
    print("FAILURES: " + "; ".join(fails))
else:
    print("ALL CHECKS PASSED")
