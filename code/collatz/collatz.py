"""
collatz.py  --  reference engine for Computational Curiosity Lab #5 (Collatz / 3n+1).

STDLIB ONLY (so verify.py's printed check count is stable across environments).

Two maps live here:
  * the RAW Collatz map      C(n) = n/2 (n even),  3n+1 (n odd)
  * the ACCELERATED/Syracuse T(n) = n/2 (n even), (3n+1)/2 (n odd)
    -- 3n+1 is even for odd n, so T folds in the forced halving.  Terras (1976)
    states his parity-vector theorem for THIS map; we VERIFY (not assume) which
    map gives the exact bijection (see is_parity_bijection / verify.py A).

"Total stopping time" counts steps of the RAW map to reach 1 (OEIS A006577);
its records are OEIS A006877 (starting values) / A006878 (the record lengths).
Trajectory-peak ("altitude") records are A006884 / A006885.

Everything is exact Python int arithmetic (peaks reach billions; no float).
"""

from __future__ import annotations

# ----------------------------------------------------------------------
# The two maps
# ----------------------------------------------------------------------

def collatz_step(n: int) -> int:
    """One step of the RAW Collatz map C."""
    return n // 2 if n % 2 == 0 else 3 * n + 1


def T_step(n: int) -> int:
    """One step of the ACCELERATED (Syracuse) map T(n)=n/2 | (3n+1)/2."""
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


# ----------------------------------------------------------------------
# Trajectories, stopping time, altitude  (RAW map -- matches the OEIS records)
# ----------------------------------------------------------------------

def trajectory(n: int, cap: int = 100000):
    """Full RAW trajectory n, C(n), C(C(n)), ... , 1  (inclusive of both ends).

    `cap` guards against a hypothetical non-terminating orbit; every n we can
    reach in practice terminates, so the cap is never hit for sane inputs.
    """
    if n < 1:
        raise ValueError("Collatz is defined on positive integers")
    seq = [n]
    while n != 1:
        n = collatz_step(n)
        seq.append(n)
        if len(seq) > cap:
            raise RuntimeError(f"trajectory exceeded cap={cap}; possible non-termination")
    return seq


def total_stopping_time(n: int) -> int:
    """# RAW steps to reach 1  (OEIS A006577).  a(1)=0, a(27)=111."""
    steps = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps


def max_value(n: int) -> int:
    """Highest value the RAW trajectory of n reaches ("altitude")."""
    hi = n
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        if n > hi:
            hi = n
    return hi


def stopping_time_below(n: int):
    """Terras 'stopping time' sigma(n): least k>=1 with C^k(n) < n  (RAW map).

    Returns None for n==1 (nothing below it).  Density-1 finiteness is Terras 1976.
    """
    if n <= 1:
        return None
    m, k = n, 0
    while True:
        m = m // 2 if m % 2 == 0 else 3 * m + 1
        k += 1
        if m < n:
            return k


# ----------------------------------------------------------------------
# The Terras parity-vector  (ACCELERATED map T) -- the exact, checkable skeleton
# ----------------------------------------------------------------------

def parity_vector(n: int, k: int):
    """First k parities under T:  (x_0, ..., x_{k-1}),  x_i = (T^i n) mod 2.

    Terras: this depends only on n mod 2**k, and n |-> v is a bijection
    Z/2**k  ->  {0,1}**k.  We TEST both claims in verify.py.
    """
    v = []
    m = n
    for _ in range(k):
        v.append(m & 1)
        m = m // 2 if m % 2 == 0 else (3 * m + 1) // 2
    return tuple(v)


def is_parity_bijection(k: int, step=T_step) -> bool:
    """True iff the length-k parity vectors over residues 0..2**k-1 are all
    distinct (i.e. n |-> parity_vector(n,k) is a bijection Z/2**k -> {0,1}**k).

    `step` lets verify.py show the RAW map does NOT enjoy this property.
    """
    seen = set()
    for r in range(1 << k):
        v = []
        m = r
        for _ in range(k):
            v.append(m & 1)
            m = step(m)
        t = tuple(v)
        if t in seen:
            return False
        seen.add(t)
    return len(seen) == (1 << k)


# ----------------------------------------------------------------------
# Records  (RAW map)  --  cross-checked against OEIS in verify.py
# ----------------------------------------------------------------------

def total_stopping_records(N: int):
    """[(n, steps), ...] for n in 2..N that set a new RAW total-stopping-time
    record.  Memoized (values <= N cached) so N up to 1e6 runs in seconds.
    Returns records with n==1 prepended as the (1,0) base.
    """
    steps = [0] * (N + 1)        # steps[m] for m<=N; 0 means 'unknown' (and steps[1] stays 0)
    known = bytearray(N + 1)     # known[m]=1 once steps[m] is final
    known[1] = 1
    records = [(1, 0)]
    best = 0
    for start in range(2, N + 1):
        path = []
        m = start
        while True:
            if m <= N and known[m]:
                base = steps[m]
                break
            path.append(m)
            m = m // 2 if m % 2 == 0 else 3 * m + 1
        for x in reversed(path):
            base += 1
            if x <= N and not known[x]:
                steps[x] = base
                known[x] = 1
        s = steps[start]
        if s > best:
            best = s
            records.append((start, s))
    return records


def altitude_records(N: int):
    """[(n, peak), ...] for n in 1..N that set a new RAW trajectory-peak record.
    No memoization (peak is not reducible); direct iteration per n.  Keep N modest
    in verify.py (figures.py pushes it higher).
    """
    records = []
    best = 0
    for n in range(1, N + 1):
        hi = max_value(n)
        if hi > best:
            best = hi
            records.append((n, hi))
    return records


# ----------------------------------------------------------------------
# Honest CONTRAST: sibling maps that DO have nontrivial cycles / divergence
# ----------------------------------------------------------------------

def step_3n_minus_1(n: int) -> int:
    """The 3n-1 map: n/2 (even), 3n-1 (odd).  Known to have several cycles."""
    return n // 2 if n % 2 == 0 else 3 * n - 1


def step_5n_plus_1(n: int) -> int:
    """The 5n+1 map: n/2 (even), 5n+1 (odd).  Believed to diverge for most n."""
    return n // 2 if n % 2 == 0 else 5 * n + 1


def find_cycle(start: int, step, cap: int = 1_000_000):
    """Iterate `step` from `start`; return the cycle (as a tuple, rotated to its
    minimum element) that the orbit falls into, or None if no cycle within `cap`
    steps / values (Floyd-free: we just record the path and detect a repeat).
    """
    seen = {}
    m = start
    path = []
    for i in range(cap):
        if m in seen:
            cyc = path[seen[m]:]
            k = cyc.index(min(cyc))
            return tuple(cyc[k:] + cyc[:k])
        seen[m] = i
        path.append(m)
        m = step(m)
        if m <= 0:        # 3n-1 can reach 0/negatives from some seeds; stop
            return None
    return None


# ----------------------------------------------------------------------
# The descent sieve  (the engine of Terras's density-1 theorem) + rational cycles
# ----------------------------------------------------------------------

def num_odd_steps(n: int, k: int) -> int:
    """How many of n's first k accelerated steps use the odd rule = popcount of
    the parity vector v_k(n).  (Distributed Binomial(k,1/2) over residues.)"""
    a, m = 0, n
    for _ in range(k):
        if m & 1:
            a += 1
        m = m // 2 if m % 2 == 0 else (3 * m + 1) // 2
    return a


def descending_class_fraction(k: int):
    """(num, den): fraction of residue classes mod 2**k that are GUARANTEED to
    drop below their start within k accelerated steps, i.e. #odd-steps a has
    3**a < 2**k.  Exact via the bijection (# residues with popcount a = C(k,a)).
    -> 1 as k -> infinity (Terras 1976), but slowly.  Returns ints (no float).
    """
    from math import comb
    den = 1 << k
    num = sum(comb(k, a) for a in range(k + 1) if 3 ** a < den)
    return num, den


def min_counterexample_survivors(k: int):
    """Residues mod 2**k that could still hold the SMALLEST counterexample, under
    two elementary rules + the descent test: r is odd, r % 4 == 3, and its class
    does NOT provably descend in k steps (3**a > 2**k).  For k=5 this is exactly
    {7, 15, 27, 31}.  (The surviving fraction -> 0, but not monotonically.)
    """
    den = 1 << k
    return [r for r in range(den)
            if r % 2 == 1 and r % 4 == 3 and 3 ** num_odd_steps(r, k) > den]


def rational_cycle(pattern):
    """The UNIQUE rational with odd denominator whose accelerated-map orbit has the
    periodic parity `pattern` (Lagarias 1990).  Returns the cycle as a list of
    Fraction, starting at that rational.  E.g. pattern (1,0,1,1,0,0,1) -> 151/47.
    """
    from fractions import Fraction
    m = len(pattern)
    # value after i steps = (P*x0 + Q) / 2**i ; solve x0 = (3**a x0 + Q)/2**m.
    P, Q = 1, 0
    for i, b in enumerate(pattern):
        if b:
            P, Q = 3 * P, 3 * Q + (1 << i)
    a = sum(pattern)
    denom = (1 << m) - 3 ** a
    if denom == 0:
        raise ValueError("pattern has 2**m == 3**a; no finite rational cycle")
    x0 = Fraction(Q, denom)
    cyc = [x0]
    x = x0
    for _ in range(m - 1):
        x = x / 2 if x.numerator % 2 == 0 else (3 * x + 1) / 2
        cyc.append(x)
    return cyc


if __name__ == "__main__":
    # quick smoke test
    print("27: stopping time", total_stopping_time(27), "peak", max_value(27))
    print("parity bijection k=10 (T):", is_parity_bijection(10))
    print("parity bijection k=10 (raw C):", is_parity_bijection(10, step=collatz_step))
    print("first total-stopping records <=100:", total_stopping_records(100))
    print("3n-1 cycle from 5:", find_cycle(5, step_3n_minus_1))
    print("3n-1 cycle from 17:", find_cycle(17, step_3n_minus_1))
