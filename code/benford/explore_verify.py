#!/usr/bin/env python3
"""
Lab #4 Benford — independent end-to-end verification (a second method, kept
separate from verify.py). Goal: confirm the DEFINITIVE core and the HONEST
contrasts hold, two independent ways where possible.

Checks:
  A. 2^n leading digits -> Benford, via TWO independent leading-digit methods
     (exact big-int string  vs  high-precision fractional part of n*log10 2),
     which must AGREE for every n; and the empirical freq -> log10(1+1/d).
  B. Convergence: max_d |freq_N(d) - benford(d)| decreases as N grows.
  C. Fibonacci and n! leading digits -> Benford (same mechanism).
  D. CONTRAST: primes up to X are a POOR Benford fit AND depend on the cutoff X
     (no natural-density limit) -> the honest "where intuition fails" point.
  E. CONTRAST: uniform & normal samples are NOT Benford.
  F. Generalized Benford (first two digits) for 2^n: P(D)=log10(1+1/D), D=10..99.
"""
import math
import sys
from decimal import Decimal, getcontext
from collections import Counter

sys.set_int_max_str_digits(2_000_000)   # 5000! has ~16k digits; 2^20000 ~6k digits
getcontext().prec = 80
LOG10_2_HP = Decimal(2).ln() / Decimal(10).ln()          # high precision log10(2)

def benford(d):  # d=1..9
    return math.log10(1 + 1.0/d)

BEN = [benford(d) for d in range(1, 10)]

def lead_str(x: int) -> int:
    """Leading decimal digit of positive int x, exact."""
    return int(str(x)[0])

def lead_from_log_hp(log10x: Decimal) -> int:
    """Leading digit from high-precision log10(x): floor(10^frac(log10x))."""
    frac = log10x - int(log10x)            # in [0,1)
    return int(Decimal(10) ** frac)        # in 1..9

def freqs(counter, total):
    return [counter.get(d, 0)/total for d in range(1, 10)]

def maxdev(fr):
    return max(abs(fr[i] - BEN[i]) for i in range(9))

def chisq(counter, total):
    # chi-square vs Benford expected
    s = 0.0
    for i, d in enumerate(range(1, 10)):
        exp = BEN[i]*total
        obs = counter.get(d, 0)
        s += (obs-exp)**2/exp
    return s

print("Benford targets P(d):", [round(b, 5) for b in BEN], " sum=", round(sum(BEN), 12))
print("="*72)

# ---- A. 2^n, two independent leading-digit methods must agree ----
N = 20000
c2 = Counter()
mism = 0
for n in range(1, N+1):
    x = 1 << n                              # exact 2^n
    d1 = lead_str(x)
    d2 = lead_from_log_hp(n * LOG10_2_HP)   # independent, high precision
    if d1 != d2:
        mism += 1
    c2[d1] += 1
print(f"A. 2^n  N={N}:  method-disagreements = {mism}  (must be 0)")
fr2 = freqs(c2, N)
print("   freq  :", [round(f, 4) for f in fr2])
print("   benford:", [round(b, 4) for b in BEN])
print(f"   max |freq-benford| = {maxdev(fr2):.5f}   chi2 = {chisq(c2, N):.3f}")

# ---- B. convergence of 2^n ----
print("-"*72)
print("B. 2^n convergence (max deviation should shrink):")
for NN in (100, 1000, 5000, 20000):
    cc = Counter(lead_str(1 << n) for n in range(1, NN+1))
    print(f"   N={NN:>6}: maxdev={maxdev(freqs(cc, NN)):.5f}")

# ---- C. Fibonacci and n! ----
print("-"*72)
def fib_leads(M):
    a, b = 1, 1
    c = Counter()
    for _ in range(M):
        c[lead_str(a)] += 1
        a, b = b, a + b
    return c
M = 20000
cf = fib_leads(M)
print(f"C1. Fibonacci M={M}: maxdev={maxdev(freqs(cf, M)):.5f}  (Benford expected)")

Mf = 5000
cfac = Counter()
f = 1
for n in range(1, Mf+1):
    f *= n
    cfac[lead_str(f)] += 1
print(f"C2. n! n=1..{Mf}: maxdev={maxdev(freqs(cfac, Mf)):.5f}  (Benford expected)")

# ---- D. primes: poor fit AND cutoff-dependent ----
print("-"*72)
def primes_upto(n):
    sieve = bytearray([1]) * (n + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            sieve[i*i::i] = bytearray(len(sieve[i*i::i]))
    return [i for i in range(2, n + 1) if sieve[i]]

for X in (10**5, 10**6, 10**7):
    pr = primes_upto(X)
    cp = Counter(lead_str(p) for p in pr)
    frp = freqs(cp, len(pr))
    print(f"D. primes < {X:>9}: count={len(pr):>7}  maxdev_vs_Benford={maxdev(frp):.5f}  "
          f"P(1)={frp[0]:.4f} (Benford {BEN[0]:.4f})")
print("   ^ note maxdev stays LARGE and P(1) drifts with the cutoff -> no natural-density Benford limit")

# ---- E. uniform & normal NOT Benford ----
print("-"*72)
import random
random.seed(12345)
K = 200000
def lead_float(x):
    x = abs(x)
    if x == 0:
        return None
    while x < 1:
        x *= 10
    while x >= 10:
        x /= 10
    return int(x)
cu = Counter(); cn = Counter()
for _ in range(K):
    u = random.uniform(1, 1000)          # uniform spanning ~3 decades
    du = lead_float(u)
    if du:
        cu[du] += 1
    g = random.gauss(500, 100)           # normal, bounded-ish
    dg = lead_float(g)
    if dg:
        cn[dg] += 1
print(f"E1. uniform(1,1000) K={K}: maxdev={maxdev(freqs(cu, sum(cu.values()))):.5f}  (NOT Benford)")
print(f"E2. normal(500,100) K={K}: maxdev={maxdev(freqs(cn, sum(cn.values()))):.5f}  (NOT Benford)")

# ---- F. generalized Benford first-two-digits for 2^n ----
print("-"*72)
def first_two(x: int) -> int:
    s = str(x)
    return int(s[:2]) if len(s) >= 2 else int(s) * 10  # pad single-digit (n>=4 -> always >=2 digits)
c2d = Counter(first_two(1 << n) for n in range(4, N+1))   # 2^4=16 is first 2-digit
tot2d = sum(c2d.values())
gen = lambda D: math.log10(1 + 1.0/D)
gmax = max(abs(c2d.get(D, 0)/tot2d - gen(D)) for D in range(10, 100))
print(f"F. 2^n first-two-digits N={N}: maxdev vs log10(1+1/D)={gmax:.6f}  sum_target={sum(gen(D) for D in range(10,100)):.6f}")
print("   sample: P(10)={:.5f} (target {:.5f}),  P(99)={:.5f} (target {:.5f})".format(
    c2d.get(10,0)/tot2d, gen(10), c2d.get(99,0)/tot2d, gen(99)))
print("="*72)
print("DONE.")
