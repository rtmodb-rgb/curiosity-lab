"""
benford.py  --  Pure-stdlib core library for Computational Curiosity Lab #4
(Benford's Law / the leading-digit phenomenon).

Brand ethos: compute, don't assert.  Every headline number the explorable shows
is reproduced here by code, and -- wherever possible -- by TWO independent
methods (see verify.py).  This module is the shared engine: the leading-digit
functions, the canonical Benford targets, the integer sequence generators
(powers / Fibonacci / factorials -- exact big integers), a fast prime sieve,
seeded uniform/normal samplers, and the goodness-of-fit statistics.

No third-party dependencies (stdlib only) so a fresh clone reproduces the SAME
numbers with no environment surprises.  (Lesson from Lab #3: never let a result
depend on an optional dependency.)

Two facts about the implementation worth stating up front:

  * BIG INTEGERS.  2**20000 has 6021 decimal digits and 5000! has 16326;
    CPython caps int<->str conversion at 4300 digits by default (since the
    CVE-2020-10735 fix, backported to 3.10.7 / 3.11), so we raise the cap.
    Leading digits of big integers are taken EXACTLY from their decimal string.

  * HIGH-PRECISION LOG.  The independent cross-check method gets the leading
    digit from the fractional part of n*log10(base) using `decimal` at
    HP_PREC=100 significant digits -- far more than the ~6 integer digits that
    n<=20000 ever needs, so the floor(10**frac) digit is provably correct over
    the whole tested range and must equal the exact big-int digit for every n.
"""

import sys
import math
import random
from decimal import Decimal, getcontext
from collections import Counter

# --- raise the int<->str digit cap (required for big factorials / powers) ----
# 5000! ~ 16326 digits, 2**20000 ~ 6021 digits; default cap is 4300.
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(2_000_000)

# --- high-precision decimal context (module-global, on purpose) --------------
# Every caller in this Lab wants the same high precision; set it once here so
# the two-method agreement is reproducible.  100 sig digits >> the ~6 integer
# digits of n*log10(2) for n<=20000, leaving ~94 correct fractional digits.
HP_PREC = 100
getcontext().prec = HP_PREC


# ======================================================================
# Canonical Benford targets
# ======================================================================
def benford_p(d):
    """First-digit Benford probability P(D1 = d) = log10(1 + 1/d), d = 1..9."""
    if not 1 <= d <= 9:
        raise ValueError(f"first digit must be 1..9, got {d}")
    return math.log10(1.0 + 1.0 / d)


def benford_two(D):
    """First-two-digits Benford probability P(D1D2 = D) = log10(1 + 1/D),
       D = 10..99 (the generalized / higher-order significant-digit law)."""
    if not 10 <= D <= 99:
        raise ValueError(f"first two digits must be 10..99, got {D}")
    return math.log10(1.0 + 1.0 / D)


# index-aligned target vectors (BENFORD[d-1] = P(d);  BENFORD_TWO[D-10] = P(D))
BENFORD = [benford_p(d) for d in range(1, 10)]
BENFORD_TWO = [benford_two(D) for D in range(10, 100)]


# ======================================================================
# Leading-digit functions -- the two independent methods + helpers
# ======================================================================
def lead_str(x):
    """EXACT leading decimal digit of a positive integer, from its decimal
       string.  This is the ground-truth method (no floating point)."""
    x = int(x)
    if x <= 0:
        raise ValueError("lead_str needs a positive integer")
    return int(str(x)[0])


def hp_log10(x):
    """High-precision log10(x) as a Decimal (x: int or Decimal). Uses the
       module HP_PREC context."""
    return Decimal(x).ln() / Decimal(10).ln()


# Snap scale for the log method (see lead_log_hp).  1e-50 is ~44 orders of
# magnitude below the closest any tested mantissa comes to an exact integer
# boundary (the min 2**n gap over n<=20000 is ~6.4e-6 at n=15772), and ~40
# orders above the HP round-trip noise -- so it fixes ONLY the exact d*10**k
# cases and never perturbs a genuine near-boundary value.
_SNAP = Decimal(1).scaleb(-50)


def lead_log_hp(log10x):
    """INDEPENDENT leading-digit method: from a high-precision Decimal value of
       log10(value), the leading digit is floor(10**frac(log10value)).

       SUBTLETY (worth knowing): when the value is exactly d*10**k (e.g. 6, or
       2**1=2), the true mantissa is the integer d, but the round trip
       10**(log10 d) lands at d - epsilon (e.g. 5.999...9) and a naive floor
       would give d-1.  We snap the computed mantissa at 1e-50 before flooring,
       which is far below any genuine mantissa-to-boundary gap (>~1e-6 here) yet
       far above the ~1e-90 round-trip noise -- so the method is EXACT for every
       value tested, robustly (not by luck of the rounding direction).  The
       exact decimal-string method (lead_str) remains the unimpeachable ground
       truth; this is the independent cross-check."""
    log10x = Decimal(log10x)
    frac = log10x - int(log10x)          # int() truncates toward 0 == floor for >=0
    val = (Decimal(10) ** frac).quantize(_SNAP)   # snap exact-boundary noise
    return int(val)                      # in [1,10) -> int() floors to 1..9


def lead_float(x):
    """Leading digit of a real number by magnitude normalization (for sampled
       reals like uniform/normal draws).  Returns None for 0/inf/nan."""
    x = abs(float(x))
    if x == 0.0 or math.isinf(x) or math.isnan(x):
        return None
    # scale into [1,10); guarded so a pathological value can't loop forever
    if x < 1.0:
        x *= 10.0 ** (-math.floor(math.log10(x)))
    elif x >= 10.0:
        x /= 10.0 ** (math.floor(math.log10(x)))
    # tidy up the rare boundary case from float rounding
    while x >= 10.0:
        x /= 10.0
    while x < 1.0:
        x *= 10.0
    return int(x)


def first_two(x):
    """First two significant digits of a positive integer as an int 10..99.
       (A single-digit x is padded, but in this Lab callers only pass x>=10.)"""
    s = str(int(x))
    return int(s[:2]) if len(s) >= 2 else int(s) * 10


# ======================================================================
# Sequence generators  (exact big integers unless noted)
# ======================================================================
def powers(base, N):
    """Yield base**n for n = 1..N as exact integers (incremental multiply)."""
    base = int(base)
    v = 1
    for _ in range(N):
        v *= base
        yield v


def fibonacci(N):
    """Yield the first N Fibonacci numbers F1, F2, ... = 1, 1, 2, 3, 5, ...
       as exact integers."""
    a, b = 1, 1
    for _ in range(N):
        yield a
        a, b = b, a + b


def factorials(N):
    """Yield 1!, 2!, ..., N! as exact integers."""
    f = 1
    for n in range(1, N + 1):
        f *= n
        yield f


def powers_leading_two_methods(base, N):
    """For n = 1..N yield (n, d_exact, d_loghp): the leading digit of base**n by
       (1) exact big-int string and (2) high-precision fractional part of
       n*log10(base).  The two MUST agree for every n -- this is the headline
       two-independent-methods check in verify.py."""
    log10base = hp_log10(base)          # Decimal, HP_PREC sig digits
    v = 1
    base = int(base)
    for n in range(1, N + 1):
        v *= base
        d1 = lead_str(v)
        d2 = lead_log_hp(n * log10base)
        yield n, d1, d2


def primes_upto(X):
    """All primes <= X via a fast bytearray sieve of Eratosthenes.
       primes_upto(10**6) has 78498 entries; primes_upto(10**7) has 664579."""
    X = int(X)
    if X < 2:
        return []
    sieve = bytearray([1]) * (X + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(X ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(range(i * i, X + 1, i)))
    return [i for i in range(2, X + 1) if sieve[i]]


def uniform_samples(n, lo=1.0, hi=1000.0, seed=12345):
    """n seeded uniform(lo, hi) reals.  Deterministic for a given seed."""
    rng = random.Random(seed)
    return [rng.uniform(lo, hi) for _ in range(n)]


def normal_samples(n, mu=500.0, sigma=100.0, seed=12345):
    """n seeded normal(mu, sigma) reals.  Deterministic for a given seed."""
    rng = random.Random(seed)
    return [rng.gauss(mu, sigma) for _ in range(n)]


# ======================================================================
# Counting + goodness-of-fit statistics
# ======================================================================
def leading_counts(values, lead=lead_str):
    """Tally first digits 1..9 over an iterable of values.  Returns a length-9
       list counts[d-1].  Values whose `lead` is None (e.g. 0) are skipped."""
    counts = [0] * 9
    for x in values:
        d = lead(x)
        if d is not None and 1 <= d <= 9:
            counts[d - 1] += 1
    return counts


def two_digit_counts(values):
    """Tally first-two-digit values 10..99 over an iterable of integers >= 10.
       Returns a length-90 list counts[D-10]."""
    counts = [0] * 90
    for x in values:
        if int(x) < 10:           # no first-two-digits below 10; skip cleanly
            continue
        D = first_two(x)
        if 10 <= D <= 99:
            counts[D - 10] += 1
    return counts


def freqs(counts):
    """Normalize a count vector to frequencies (sums to 1; all-zero -> zeros)."""
    total = sum(counts)
    if total == 0:
        return [0.0] * len(counts)
    return [c / total for c in counts]


def maxdev(fr, targets=BENFORD):
    """max_i |fr[i] - targets[i]|  (L-infinity distance to the target law).
       `fr` is a frequency vector aligned to `targets`."""
    return max(abs(fr[i] - targets[i]) for i in range(len(targets)))


def total_variation(fr, targets=BENFORD):
    """Total-variation distance = 0.5 * sum_i |fr[i] - targets[i]|."""
    return 0.5 * sum(abs(fr[i] - targets[i]) for i in range(len(targets)))


def chi_square(counts, targets=BENFORD):
    """Pearson chi-square of observed counts vs the target law:
       sum_i (obs_i - exp_i)^2 / exp_i,  exp_i = targets[i] * total."""
    total = sum(counts)
    s = 0.0
    for i in range(len(targets)):
        exp = targets[i] * total
        if exp > 0:
            s += (counts[i] - exp) ** 2 / exp
    return s


# small self-test when run directly (not the rigor gate -- that's verify.py)
if __name__ == "__main__":
    print("Benford P(d), d=1..9:", [round(p, 5) for p in BENFORD],
          " sum =", round(sum(BENFORD), 12))
    c = leading_counts(powers(2, 20000))
    fr = freqs(c)
    print("2**n (N=20000) counts:", c)
    print("           maxdev:", round(maxdev(fr), 6),
          " chi2:", round(chi_square(c), 4),
          " TV:", round(total_variation(fr), 6))
    print("primes<=1e6:", len(primes_upto(10 ** 6)), "(expect 78498)")
