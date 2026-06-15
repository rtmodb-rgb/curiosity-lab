"""
verify.py  --  THE RIGOR GATE for Computational Curiosity Lab #5 (Collatz / 3n+1).

Brand ethos: compute, don't assert; check every headline number two INDEPENDENT
ways (or against OEIS published terms); assert robust facts so a fresh clone
reproduces the pass/fail; fail loud.  Prints [PASS]/[FAIL] per check and EXITS
NONZERO on any failure.  STDLIB-ONLY (imports only collatz.py, itself stdlib) so
the printed check count K is stable across environments -- the page cites K.

What is PROVEN-BY-CODE here vs CITED:
  * PROVEN-BY-CODE: the Terras parity-vector BIJECTION holds for the accelerated
    map T and FAILS for the raw map C (k up to 16); the parity vector depends
    only on n mod 2**k; the 2-adic affine identity 2**k * T**k(n) = 3**a * n + c
    with c fixed by the residue; the OEIS record tables A006877/8 (to 1e6) and
    A006884/5 (to 1e5) reproduce EXACTLY from an independent computation, incl.
    27->111 (peak 9232) and 837799->524 (peak 2,974,984,576); the honest
    CONTRAST that 3n-1 and 5n+1 have genuine nontrivial cycles.
  * CITED-NOT-REPROVED (see facts.md / /shared/kb/collatz-facts.md): Terras's
    density-1 theorem; Tao 2019; Krasikov-Lagarias; the conjecture itself
    (verified to ~2**68 by Barina -- a computation, not a proof).

Deterministic; total runtime a few seconds.
"""

import sys
import collatz as C

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
# 0.  The two maps -- definitions and a couple of fixed points
# ======================================================================
hr("0. The raw map C and the accelerated (Syracuse) map T")

check("0a. C: even halves, odd -> 3n+1  (C(4)=2, C(5)=16)",
      C.collatz_step(4) == 2 and C.collatz_step(5) == 16)
check("0b. T: even halves, odd -> (3n+1)/2  (T(4)=2, T(5)=8)",
      C.T_step(4) == 2 and C.T_step(5) == 8)
# the only trivial RAW cycle is 1 -> 4 -> 2 -> 1
check("0c. raw trivial cycle 1->4->2->1",
      C.collatz_step(1) == 4 and C.collatz_step(4) == 2 and C.collatz_step(2) == 1)


# ======================================================================
# A.  THE TERRAS PARITY-VECTOR BIJECTION  (the checkable skeleton)
# ======================================================================
hr("A. Terras parity-vector bijection: exact for T, FAILS for raw C")

KMAX = 16
bij_T = all(C.is_parity_bijection(k, step=C.T_step) for k in range(1, KMAX + 1))
check(f"A1. [PROVEN BY CODE] n |-> (first k parities under T) is a BIJECTION "
      f"Z/2^k -> {{0,1}}^k for ALL k=1..{KMAX}",
      bij_T, f"all {KMAX} levels bijective (2^{KMAX}={1 << KMAX} residues at k={KMAX})")

# the SAME construction on the raw map is NOT a bijection (parities collide):
raw_fails = [k for k in range(2, 9) if not C.is_parity_bijection(k, step=C.collatz_step)]
check("A2. [CONTRAST] the raw map C does NOT give a bijection (parities collide) for k=2..8",
      raw_fails == list(range(2, 9)),
      f"raw map fails to be a bijection at k = {raw_fails}")

# depends only on the residue n mod 2^k  (n and n + 2^k share the first-k parities)
import random as _r
_rng = _r.Random(12345)
res_ok = True
for _ in range(5000):
    k = _rng.randint(1, 14)
    n = _rng.randint(1, 10 ** 7)
    if C.parity_vector(n, k) != C.parity_vector(n + (1 << k), k):
        res_ok = False
        break
check("A3. parity vector depends ONLY on n mod 2^k  (5000 random (n,k); n vs n+2^k)",
      res_ok, "every trial: v_k(n) == v_k(n + 2^k)")

# equidistribution corollary: in EVERY block of 2^k consecutive integers, each of
# the 2^k parity patterns occurs EXACTLY once (a second, independent formulation).
equi_ok = True
for _ in range(200):
    k = _rng.randint(1, 11)
    m0 = _rng.randint(0, 10 ** 6)
    seen = {C.parity_vector(m0 + i, k) for i in range(1 << k)}
    if len(seen) != (1 << k):
        equi_ok = False
        break
check("A4. equidistribution: every window of 2^k consecutive ints hits each "
      "parity pattern exactly once (200 random windows)",
      equi_ok)

# 2-adic affine identity: 2^k * T^k(n) = 3^a * n + c, with a = #odd-steps and c a
# constant fixed by the residue mod 2^k (verify c is identical for n and n+2^k).
def _Tk_and_a(n, k):
    a = 0
    for _ in range(k):
        if n & 1:
            a += 1
        n = n // 2 if n % 2 == 0 else (3 * n + 1) // 2
    return n, a            # (T^k(n), number of odd steps)

aff_ok = True
for _ in range(3000):
    k = _rng.randint(1, 14)
    n = _rng.randint(1, 10 ** 6)
    Tk1, a1 = _Tk_and_a(n, k)
    Tk2, a2 = _Tk_and_a(n + (1 << k), k)
    c1 = (1 << k) * Tk1 - 3 ** a1 * n
    c2 = (1 << k) * Tk2 - 3 ** a2 * (n + (1 << k))
    if a1 != a2 or c1 != c2:
        aff_ok = False
        break
check("A5. 2-adic affine form 2^k*T^k(n) = 3^a*n + c: a and c depend ONLY on the "
      "residue (3000 random (n,k))",
      aff_ok)


# ======================================================================
# B.  TOTAL STOPPING TIME + records  (RAW map)  vs OEIS A006877 / A006878
# ======================================================================
hr("B. Total stopping time + records  vs  OEIS A006877 / A006878")

# two INDEPENDENT ways: a step counter vs the length of the materialized path.
two_ways_ok = all(C.total_stopping_time(n) == len(C.trajectory(n)) - 1
                  for n in range(2, 3000))
check("B1. [TWO WAYS] total_stopping_time(n) == len(trajectory(n))-1 for n=2..2999",
      two_ways_ok)

check("B2. landmark stopping times: a(1)=0, a(2)=1, a(6)=8, a(7)=16, a(27)=111",
      C.total_stopping_time(1) == 0 and C.total_stopping_time(2) == 1
      and C.total_stopping_time(6) == 8 and C.total_stopping_time(7) == 16
      and C.total_stopping_time(27) == 111)

# OEIS-published prefixes (the INDEPENDENT external truth):
OEIS_A006877 = [1, 2, 3, 6, 7, 9, 18, 25, 27, 54, 73, 97, 129, 171, 231, 313, 327,
                649, 703, 871, 1161, 2223, 2463, 2919, 3711, 6171, 10971, 13255,
                17647, 23529, 26623, 34239, 35655, 52527, 77031, 106239, 142587,
                156159, 216367, 230631, 410011, 511935, 626331, 837799]
OEIS_A006878 = [0, 1, 7, 8, 16, 19, 20, 23, 111, 112, 115, 118, 121, 124, 127, 130,
                143, 144, 170, 178, 181, 182, 208, 216, 237, 261, 267, 275, 278,
                281, 307, 310, 323, 339, 350, 353, 374, 382, 385, 442, 448, 469,
                508, 524]
recs = C.total_stopping_records(10 ** 6)
my_starts = [n for n, s in recs]
my_steps = [s for n, s in recs]
check("B3. total-stopping record START values up to 1e6 == OEIS A006877 (44 terms)",
      my_starts == OEIS_A006877, f"{len(my_starts)} records; "
      f"first mismatch idx = {next((i for i in range(min(len(my_starts), len(OEIS_A006877))) if my_starts[i] != OEIS_A006877[i]), 'none')}")
check("B4. total-stopping RECORD LENGTHS up to 1e6 == OEIS A006878 (44 terms)",
      my_steps == OEIS_A006878)
check("B5. the most stubborn n < 1e6 is 837799 with 524 steps (the last 1e6 record)",
      recs[-1] == (837799, 524))


# ======================================================================
# C.  ALTITUDE (trajectory peak) records  vs OEIS A006884 / A006885
# ======================================================================
hr("C. Trajectory-peak records  vs  OEIS A006884 / A006885")

# two INDEPENDENT ways for the peak: streaming max vs max(trajectory list).
peak_two_ways_ok = all(C.max_value(n) == max(C.trajectory(n)) for n in range(1, 3000))
check("C1. [TWO WAYS] max_value(n) == max(trajectory(n)) for n=1..2999",
      peak_two_ways_ok)
check("C2. 27 climbs to 9232; 703 climbs to 250504",
      C.max_value(27) == 9232 and C.max_value(703) == 250504)

OEIS_A006884 = [1, 2, 3, 7, 15, 27, 255, 447, 639, 703, 1819, 4255, 4591, 9663,
                20895, 26623, 31911, 60975, 77671]
OEIS_A006885 = [1, 2, 16, 52, 160, 9232, 13120, 39364, 41524, 250504, 1276936,
                6810136, 8153620, 27114424, 50143264, 106358020, 121012864,
                593279152, 1570824736]
alt = C.altitude_records(10 ** 5)
check("C3. peak-record START values up to 1e5 == OEIS A006884",
      [n for n, p in alt] == OEIS_A006884)
check("C4. peak-record PEAKS up to 1e5 == OEIS A006885",
      [p for n, p in alt] == OEIS_A006885)
check("C5. 837799's peak is 2,974,984,576 (~3 billion, from a < 1e6 start)",
      C.max_value(837799) == 2974984576)


# ======================================================================
# D.  EVERY n up to 1e6 reaches 1  +  Terras 'drops below itself'
# ======================================================================
hr("D. All n<=1e6 reach 1; and every n drops below itself (Terras sigma finite)")

# total_stopping_records computed a finite stopping time for ALL n<=1e6 (the loop
# terminated), i.e. each of the one million orbits reached 1 -- a tiny replica of
# the historical verification (now pushed to ~2^68 by Barina; CITED).
check("D1. all 1,000,000 starts <= 1e6 reach 1 (max total stopping time = 524 @ 837799)",
      max(s for n, s in recs) == 524 and recs[-1][0] == 837799)

# Terras stopping time sigma(n) = first step the RAW orbit goes below n; finite
# for every n we test (density-1 finiteness is Terras 1976 -- CITED as a theorem).
sigma_finite = all(C.stopping_time_below(n) is not None for n in range(2, 200000))
check("D2. sigma(n) (first descent below n) is finite for every n=2..199999 "
      "[density 1: Terras 1976, cited]",
      sigma_finite)


# ======================================================================
# E.  HONEST CONTRAST: 3n-1 and 5n+1 have genuine nontrivial cycles
# ======================================================================
hr("E. Sibling maps DO cycle/diverge -- why 3n+1 is non-obvious")

cyc_3a = C.find_cycle(1, C.step_3n_minus_1)
cyc_3b = C.find_cycle(5, C.step_3n_minus_1)
cyc_3c = C.find_cycle(17, C.step_3n_minus_1)
check("E1. 3n-1 has the trivial cycle {1,2}",
      cyc_3a == (1, 2))
check("E2. 3n-1 has a nontrivial 5-cycle {5,7,10,14,20}",
      set(cyc_3b) == {5, 7, 10, 14, 20} and len(cyc_3b) == 5)
check("E3. 3n-1 has a nontrivial 18-cycle starting at 17",
      len(cyc_3c) == 18 and min(cyc_3c) == 17)

cyc_5a = C.find_cycle(1, C.step_5n_plus_1)
cyc_5b = C.find_cycle(13, C.step_5n_plus_1)
check("E4. 5n+1 has a cycle through 1  {1,2,3,4,6,8,16}",
      set(cyc_5a) == {1, 2, 3, 4, 6, 8, 16})
check("E5. 5n+1 has a DISTINCT nontrivial cycle through 13 (not containing 1) -- "
      "so '5n+1 always reaches 1' is simply FALSE",
      cyc_5b is not None and 1 not in cyc_5b and 13 in cyc_5b)

# and for the GENUINE 3n+1 map, no nontrivial cycle appears: every orbit we
# checked lands in the trivial {1,2,4}.  Traversed from its min element 1 the
# raw cycle is 1 -> 4 -> 2 -> 1, i.e. the canonical tuple (1, 4, 2).
genuine_ok = all(C.find_cycle(n, C.collatz_step) == (1, 4, 2) for n in range(1, 5000))
check("E6. the genuine 3n+1 map: every start 1..4999 lands in the trivial cycle "
      "{1,2,4} -- NO nontrivial cycle found (none is known; CITED bounds are huge)",
      genuine_ok)


# ======================================================================
# F.  THE DESCENT SIEVE  (the engine of Terras's density-1 theorem)
# ======================================================================
hr("F. Descent sieve: #odd-steps ~ Binomial(k,1/2); descending fraction -> 1")

from math import comb
# F1: by the bijection, #residues mod 2^k with popcount(parity)=a is EXACTLY C(k,a)
#     -- a second, independent re-confirmation of the bijection (two ways).
pop_ok = True
for k in (5, 10, 12):
    cnt = [0] * (k + 1)
    for r in range(1 << k):
        cnt[C.num_odd_steps(r, k)] += 1
    if cnt != [comb(k, a) for a in range(k + 1)]:
        pop_ok = False
check("F1. [TWO WAYS] #odd-steps over residues mod 2^k == Binomial(k, a)=C(k,a) "
      "(k=5,10,12) -- equidistribution corollary of the bijection",
      pop_ok)

# F2: fraction of classes that PROVABLY descend within k steps (3^a < 2^k) rises
#     toward 1 (Terras density-1), exceeds 1/2 already, but converges SLOWLY.
fr = [C.descending_class_fraction(k) for k in (5, 10, 15, 20, 25)]
vals = [n / d for n, d in fr]
check("F2. descending-class fraction strictly INCREASES over k=5,10,15,20,25 and "
      "every value is > 1/2 (-> 1 slowly; Terras 1976)",
      all(vals[i] < vals[i + 1] for i in range(4)) and all(v > 0.5 for v in vals),
      "  ".join(f"k={k}:{v:.4f}" for k, v in zip((5, 10, 15, 20, 25), vals)))

# F3: with two elementary rules (min counterexample is odd and == 3 mod 4), only
#     4 of the 32 classes mod 32 survive: 7, 15, 27, 31.
check("F3. minimal-counterexample survivors mod 32 (odd & =3 mod4 & not-descended) "
      "== {7, 15, 27, 31}",
      C.min_counterexample_survivors(5) == [7, 15, 27, 31],
      f"mod16={C.min_counterexample_survivors(4)}  mod32={C.min_counterexample_survivors(5)}")


# ======================================================================
# G.  RATIONAL CYCLES: every periodic parity pattern <-> one rational (Lagarias 1990)
# ======================================================================
hr("G. Periodic parity pattern <-> unique rational with odd denominator")

from fractions import Fraction
PAT = (1, 0, 1, 1, 0, 0, 1)
cyc = C.rational_cycle(PAT)
# round-trip: the parity of each rational in the cycle reproduces PAT, and it closes
parities = tuple(x.numerator % 2 for x in cyc)
closes = (cyc[-1] / 2 if cyc[-1].numerator % 2 == 0 else (3 * cyc[-1] + 1) / 2) == cyc[0]
check("G1. parity pattern (1,0,1,1,0,0,1) -> the rational cycle 151/47 (Lagarias 1990)",
      cyc[0] == Fraction(151, 47) and len(cyc) == 7)
check("G2. that rational cycle's own parities reproduce the pattern AND it closes up",
      parities == PAT and closes,
      f"parities={parities}")


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
