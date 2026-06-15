"""
verify.py  --  THE RIGOR GATE for Computational Curiosity Lab #4 (Benford's Law).

Brand ethos: compute, don't assert; check every headline number two independent
ways where possible; assert ROBUST INEQUALITIES (not brittle exact floats) so a
fresh clone reproduces the same pass/fail; fail loud.  Prints [PASS]/[FAIL] per
check and EXITS NONZERO on any failure.  STDLIB-ONLY (imports only benford.py,
itself stdlib-only) so the printed check count K is stable across environments
-- the page cites this K.  (Lesson from Lab #3: never let the count depend on an
optional dependency.)

What is proven HERE (by code) vs cited:
  * PROVEN-BY-CODE: 2**n / Fibonacci / n! are Benford (empirically, to tight
    tolerance, with convergence); two INDEPENDENT leading-digit methods agree
    for 2**n over ALL n=1..20000; the generalized two-digit law; the honest
    CONTRASTS (primes are an N-dependent poor fit; uniform & normal are not
    Benford).  Convergence RATES differ (2**n fast, n! slow -- Diaconis 1977).
  * CITED-NOT-REPROVED (see facts.md): Weyl's
    theorem; the prime non-convergence theorem; Diaconis 1977; Hill 1995.

Deterministic; total runtime well under ~90 s.
"""

import sys
import benford as B

_passes = 0
_failures = []


def check(name, cond, detail=""):
    """Record one [PASS]/[FAIL] line.  cond is coerced to bool."""
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
# 0.  The Benford law itself (targets + the generalized-law identity)
# ======================================================================
hr("0. Benford targets and the generalized-law identity")

check("0a. first-digit P(1..9) sum to 1",
      abs(sum(B.BENFORD) - 1.0) < 1e-12,
      f"sum = {sum(B.BENFORD):.15f}")

# published table to 5 dp
TABLE = [0.30103, 0.17609, 0.12494, 0.09691, 0.07918,
         0.06695, 0.05799, 0.05115, 0.04576]
check("0b. P(d) matches the published table to 5 dp (P1=0.30103 ... P9=0.04576)",
      all(abs(round(B.BENFORD[i], 5) - TABLE[i]) < 1e-9 for i in range(9)),
      f"P = {[round(p, 5) for p in B.BENFORD]}")

check("0c. two-digit P(10..99) sum to 1",
      abs(sum(B.BENFORD_TWO) - 1.0) < 1e-12,
      f"sum = {sum(B.BENFORD_TWO):.15f}")

# generalized law is consistent with the first-digit law:
# sum_{j=0..9} log10(1 + 1/(10d+j)) telescopes to log10(1 + 1/d) = P(d).
marg_err = max(abs(sum(B.benford_two(10 * d + j) for j in range(10)) - B.benford_p(d))
               for d in range(1, 10))
check("0d. generalized two-digit law marginalizes EXACTLY to the first-digit law",
      marg_err < 1e-12, f"max |sum_j P(10d+j) - P(d)| = {marg_err:.2e}")


# ======================================================================
# A.  2**n  --  two INDEPENDENT leading-digit methods + Benford + convergence
# ======================================================================
hr("A. 2**n: two independent leading-digit methods agree, and -> Benford")

# ONE pass over n=1..20000:
#   m1 = exact big-int decimal string  (ground truth)
#   m2 = high-precision floor(10**frac(n*log10 2))  -- never forms 2**n
# also snapshot cumulative first-digit counts for convergence, and tally the
# first-two-digit counts for the generalized-law check (Section F).
N = 20000
CHECKPOINTS = (100, 1000, 5000, 20000)
disagree = 0
counts = [0] * 9
two_counts = [0] * 90
snap = {}
v = 1
log2 = B.hp_log10(2)
for n in range(1, N + 1):
    v <<= 1                              # exact 2**n
    d1 = B.lead_str(v)                   # method 1: exact decimal string
    d2 = B.lead_log_hp(n * log2)         # method 2: high-precision log (geometric)
    if d1 != d2:
        disagree += 1
    counts[d1 - 1] += 1
    if v >= 10:
        D = B.first_two(v)
        two_counts[D - 10] += 1
    if n in CHECKPOINTS:
        snap[n] = list(counts)

check("A1. [TWO WAYS] exact-string & HP-log leading digit AGREE for ALL n=1..20000",
      disagree == 0, f"disagreements = {disagree}  (must be 0)")

md20000 = B.maxdev(B.freqs(snap[20000]))
chi20000 = B.chi_square(snap[20000])
check("A2. 2**n N=20000 max|freq-Benford| < 0.001",
      md20000 < 0.001, f"maxdev = {md20000:.6f}  (~0.00009 expected)")
check("A3. 2**n N=20000 chi-square does NOT reject Benford (< 15.507 = chi2_.95,8)",
      chi20000 < 15.507, f"chi2 = {chi20000:.4f}  (8 dof)")

mds = [B.maxdev(B.freqs(snap[n])) for n in CHECKPOINTS]
decreasing = all(mds[i] > mds[i + 1] for i in range(len(mds) - 1))
check("A4. 2**n convergence: maxdev strictly DECREASES across N=100,1000,5000,20000",
      decreasing, "  ".join(f"N={n}:{m:.5f}" for n, m in zip(CHECKPOINTS, mds)))

ENVELOPE = (0.02, 0.005, 0.0015, 0.0003)   # robust brackets around 0.0092/0.0021/0.00065/0.00009
check("A5. 2**n maxdev below a robust per-N envelope (0.02/0.005/0.0015/0.0003)",
      all(mds[i] < ENVELOPE[i] for i in range(4)),
      "  ".join(f"N={n}:{m:.5f}<{e}" for n, m, e in zip(CHECKPOINTS, mds, ENVELOPE)))


# ======================================================================
# B.  Fibonacci (exact big integers)  -> Benford, + independent method check
# ======================================================================
hr("B. Fibonacci: -> Benford, with an independent leading-digit cross-check")

# ONE pass over F_1..F_20000: empirical first-digit counts (lead_str, full range)
# plus an independent cross-check (exact string vs HP log of the exact value) on
# n=1..2000 -- two independent algorithms for the leading digit must agree.
MF = 20000
XCHECK = 2000
fib_counts = [0] * 9
fib_disagree = 0
for n, F in enumerate(B.fibonacci(MF), start=1):
    d = B.lead_str(F)
    fib_counts[d - 1] += 1
    if n <= XCHECK and d != B.lead_log_hp(B.hp_log10(F)):
        fib_disagree += 1

check(f"B1. [TWO WAYS] Fibonacci exact-string & HP-log agree for n=1..{XCHECK}",
      fib_disagree == 0, f"disagreements = {fib_disagree}")
md_fib = B.maxdev(B.freqs(fib_counts))
check(f"B2. Fibonacci M={MF} max|freq-Benford| < 0.001",
      md_fib < 0.001, f"maxdev = {md_fib:.6f}  (~0.0001 expected)")


# ======================================================================
# C.  n!  --  Benford, but a DEEPER theorem (Diaconis 1977) and SLOWER
# ======================================================================
hr("C. n!: -> Benford (Diaconis 1977) but converges SLOWER than 2**n")

MFAC = 5000
fac_counts = [0] * 9
fac_disagree = 0
fac_n3_seen = False
for n, f in enumerate(B.factorials(MFAC), start=1):
    d = B.lead_str(f)
    fac_counts[d - 1] += 1
    if n <= XCHECK:
        if n == 3:
            fac_n3_seen = True       # 3! = 6 is the exact-boundary case we hardened
        if d != B.lead_log_hp(B.hp_log10(f)):
            fac_disagree += 1

check(f"C1. [TWO WAYS] n! exact-string & HP-log agree for n=1..{XCHECK} (incl. 3!=6)",
      fac_disagree == 0 and fac_n3_seen, f"disagreements = {fac_disagree}")
md_fac = B.maxdev(B.freqs(fac_counts))
check(f"C2. n! n=1..{MFAC} max|freq-Benford| < 0.05 (Benford, looser)",
      md_fac < 0.05, f"maxdev = {md_fac:.6f}  (~0.0105 expected)")
# honest rate contrast: n! at N=5000 is FARTHER from Benford than 2**n at both
# N=5000 and even N=20000 -- the convergence rate is genuinely slower.
md_pow_5000 = B.maxdev(B.freqs(snap[5000]))
check("C3. n! converges SLOWER than 2**n  (maxdev_fac(5000) > maxdev_pow(5000) and > maxdev_pow(20000))",
      md_fac > md_pow_5000 and md_fac > md20000,
      f"n!:{md_fac:.5f}  2^n@5000:{md_pow_5000:.5f}  2^n@20000:{md20000:.5f}")


# ======================================================================
# D.  Primes  --  the HONEST contrast: N-dependent poor fit, no density limit
# ======================================================================
hr("D. Primes: a poor, CUTOFF-DEPENDENT fit (no natural-density Benford limit)")

KNOWN_PI = {10 ** 5: 9592, 10 ** 6: 78498, 10 ** 7: 664579}   # literature values
prime_p1 = {}
prime_md = {}
counts_ok = True
for X in (10 ** 5, 10 ** 6, 10 ** 7):
    pr = B.primes_upto(X)
    if len(pr) != KNOWN_PI[X]:
        counts_ok = False
    fr = B.freqs(B.leading_counts(pr))
    prime_p1[X] = fr[0]
    prime_md[X] = B.maxdev(fr)
    print(f"     primes <= {X:>9}: count={len(pr):>7}  maxdev={prime_md[X]:.5f}  P(1)={fr[0]:.4f}")

check("D1. prime counts match known pi(x): pi(1e5)=9592, pi(1e6)=78498, pi(1e7)=664579",
      counts_ok, "sieve vs literature")
check("D2. primes are a POOR Benford fit: maxdev > 0.1 at every cutoff",
      all(prime_md[X] > 0.1 for X in prime_md),
      f"maxdevs = {[round(prime_md[X], 4) for X in (10**5, 10**6, 10**7)]}")
p1s = [prime_p1[X] for X in (10 ** 5, 10 ** 6, 10 ** 7)]
check("D3. P(lead=1) DRIFTS with the cutoff (strictly decreasing) -> no density limit",
      p1s[0] > p1s[1] > p1s[2],
      f"P(1): 1e5={p1s[0]:.4f} > 1e6={p1s[1]:.4f} > 1e7={p1s[2]:.4f}")
check("D4. that drift sits BETWEEN uniform 1/9 and Benford 0.30103 (neither limit)",
      all(1 / 9 < p < B.BENFORD[0] for p in p1s),
      f"1/9={1/9:.4f} < P(1) < {B.BENFORD[0]:.4f}")


# ======================================================================
# E.  Distributions that are NOT Benford (seeded; deterministic)
# ======================================================================
hr("E. NOT Benford: uniform & normal samples")

K = 200000
mu = B.maxdev(B.freqs(B.leading_counts(B.uniform_samples(K), lead=B.lead_float)))
mn = B.maxdev(B.freqs(B.leading_counts(B.normal_samples(K), lead=B.lead_float)))
check("E1. uniform(1,1000) is NOT Benford: maxdev > 0.1",
      mu > 0.1, f"maxdev = {mu:.5f}  (~0.19 expected)")
check("E2. normal(500,100) is NOT Benford: maxdev > 0.1",
      mn > 0.1, f"maxdev = {mn:.5f}  (~0.30 expected)")


# ======================================================================
# F.  Generalized first-two-digit Benford for 2**n
# ======================================================================
hr("F. Generalized first-two-digit Benford for 2**n")

md_two = B.maxdev(B.freqs(two_counts), B.BENFORD_TWO)
check("F1. 2**n first-two-digits -> log10(1+1/D), D=10..99: maxdev < 0.001 (N=20000)",
      md_two < 0.001, f"maxdev = {md_two:.6f}  (~0.00014 expected)")


# ======================================================================
# G.  Regression: the exact-boundary subtlety we found and hardened
# ======================================================================
hr("G. Regression: log method is exact at d*10**k boundaries (the 3!=6 case)")

# value = d*10**k has mantissa exactly d; a naive floor(10**log10(value)) gives
# d-1 (e.g. 5.999...9 for 6).  lead_log_hp snaps this; assert it agrees with the
# exact string method on a battery of such boundary values.
BOUNDARY = [d * 10 ** k for k in range(0, 6) for d in range(1, 10)]
bad = [v for v in BOUNDARY if B.lead_log_hp(B.hp_log10(v)) != B.lead_str(v)]
check("G1. lead_log_hp == lead_str for all d*10**k (k=0..5, d=1..9) [snap regression]",
      not bad, f"mismatches = {len(bad)}" + (f" e.g. {bad[:5]}" if bad else ""))

# lead_float (used for sampled reals) agrees with lead_str on exact integers
import random as _r
_rng = _r.Random(7)
ints = [_rng.randint(1, 10 ** 9) for _ in range(20000)]
bad_f = sum(1 for x in ints if B.lead_float(float(x)) != B.lead_str(x))
check("G2. lead_float == lead_str on 20000 random integers in [1,1e9]",
      bad_f == 0, f"mismatches = {bad_f}")


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
