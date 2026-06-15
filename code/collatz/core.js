/*
 * core.js  --  the in-browser Collatz engine, dependency-free JavaScript.
 *
 * Computational Curiosity Lab #5 (Collatz / 3n+1).  A faithful port of
 * collatz.py: the raw map C and accelerated map T, trajectories / stopping time
 * / altitude, the Terras parity-vector BIJECTION (exact for T, not for C), the
 * descent sieve (engine of Terras's density-1 theorem), OEIS record scans, and
 * the sibling-map cycles (3n-1, 5n+1).
 *
 * EXACTNESS: single trajectories use BigInt, so an arbitrarily large starting
 * value never silently overflows.  The bulk record scans use Number -- which is
 * exact here because every trajectory peak for a start n < 1e6 stays below
 * ~6e10 << 2^53 (verified).  test_core.mjs cross-checks ALL of this against
 * collatz.py and the OEIS tables, and guards that the page inlines this region
 * byte-for-byte.
 *
 * The region between the COLLATZ_CORE markers is self-contained (no import /
 * export / require) so a web page can inline it verbatim into a <script>.
 */

/* === COLLATZ_CORE START === */
"use strict";

// ---- the two maps ---------------------------------------------------------
// Raw Collatz map C(n) = n/2 (even) | 3n+1 (odd).  Works on Number or BigInt.
function collatzStep(n) {
  if (typeof n === "bigint") return (n & 1n) === 0n ? n / 2n : 3n * n + 1n;
  return n % 2 === 0 ? n / 2 : 3 * n + 1;
}
// Accelerated / Syracuse map T(n) = n/2 (even) | (3n+1)/2 (odd).
function tStep(n) {
  if (typeof n === "bigint") return (n & 1n) === 0n ? n / 2n : (3n * n + 1n) / 2n;
  return n % 2 === 0 ? n / 2 : (3 * n + 1) / 2;
}

// ---- single trajectories (BigInt: always exact) ---------------------------
// Full RAW trajectory n, C(n), ..., 1 as an array of BigInt.
function trajectory(n) {
  let x = typeof n === "bigint" ? n : BigInt(n);
  if (x < 1n) throw new Error("Collatz is defined on positive integers");
  const seq = [x];
  while (x !== 1n) {
    x = (x & 1n) === 0n ? x / 2n : 3n * x + 1n;
    seq.push(x);
  }
  return seq;
}
// total stopping time = # RAW steps to reach 1 (OEIS A006577); a(1)=0, a(27)=111.
function totalStoppingTime(n) {
  let x = typeof n === "bigint" ? n : BigInt(n);
  let s = 0;
  while (x !== 1n) { x = (x & 1n) === 0n ? x / 2n : 3n * x + 1n; s++; }
  return s;
}
// highest value the RAW trajectory of n reaches ("altitude"), as BigInt.
function maxValue(n) {
  let x = typeof n === "bigint" ? n : BigInt(n);
  let hi = x;
  while (x !== 1n) { x = (x & 1n) === 0n ? x / 2n : 3n * x + 1n; if (x > hi) hi = x; }
  return hi;
}
// Terras stopping time sigma(n): least k>=1 with C^k(n) < n (RAW map); null for n<=1.
function stoppingTimeBelow(n) {
  let x = typeof n === "bigint" ? n : BigInt(n);
  if (x <= 1n) return null;
  const n0 = x;
  let k = 0;
  while (true) {
    x = (x & 1n) === 0n ? x / 2n : 3n * x + 1n;
    k++;
    if (x < n0) return k;
  }
}

// ---- the Terras parity vector (accelerated map T) -------------------------
// first k parities (x_i = (T^i n) mod 2) as a 0/1 array; depends only on n mod 2^k.
function parityVector(n, k) {
  const v = new Array(k);
  let m = typeof n === "bigint" ? n : BigInt(n);
  for (let i = 0; i < k; i++) {
    v[i] = Number(m & 1n);
    m = (m & 1n) === 0n ? m / 2n : (3n * m + 1n) / 2n;
  }
  return v;
}
// # odd-steps among the first k accelerated steps = popcount of the parity vector.
function numOddSteps(n, k) {
  let a = 0;
  let m = typeof n === "bigint" ? n : BigInt(n);
  for (let i = 0; i < k; i++) {
    if ((m & 1n) === 1n) a++;
    m = (m & 1n) === 0n ? m / 2n : (3n * m + 1n) / 2n;
  }
  return a;
}
// True iff n |-> parityVector(n,k) is a bijection Z/2^k -> {0,1}^k.
// step defaults to tStep (bijective); pass collatzStep to see it FAIL.
function isParityBijection(k, step) {
  step = step || tStep;
  const seen = new Set();
  for (let r = 0; r < (1 << k); r++) {
    let m = r, key = 0;
    for (let i = 0; i < k; i++) { key = key * 2 + (m & 1); m = step(m); }
    if (seen.has(key)) return false;
    seen.add(key);
  }
  return seen.size === (1 << k);
}

// ---- the descent sieve (engine of Terras's density-1 theorem) -------------
function binom(k, a) {                 // exact C(k,a) for the small k we use
  if (a < 0 || a > k) return 0;
  a = Math.min(a, k - a);
  let r = 1;
  for (let i = 0; i < a; i++) r = (r * (k - i)) / (i + 1);
  return Math.round(r);
}
// [num, den]: fraction of residue classes mod 2^k that PROVABLY drop below their
// start within k accelerated steps (#odd-steps a has 3^a < 2^k).  -> 1, slowly.
function descendingClassFraction(k) {
  const den = Math.pow(2, k);
  let num = 0;
  let pow3 = 1;
  for (let a = 0; a <= k; a++) {
    if (pow3 < den) num += binom(k, a);
    pow3 *= 3;
  }
  return [num, den];
}
// residues mod 2^k that could hold the SMALLEST counterexample: odd, ==3 mod 4,
// and 3^(#odd-steps) > 2^k.  For k=5 -> [7,15,27,31].
function minCounterexampleSurvivors(k) {
  const den = 1 << k;
  const out = [];
  for (let r = 0; r < den; r++) {
    if (r % 2 === 1 && r % 4 === 3 && Math.pow(3, numOddSteps(r, k)) > den) out.push(r);
  }
  return out;
}

// ---- bulk record scans (Number: exact for N <= 1e6) -----------------------
// [[n, steps], ...] for n in 1..N setting a new RAW total-stopping-time record.
function totalStoppingRecords(N) {
  const steps = new Int32Array(N + 1);   // 0 = unknown; steps[1] stays 0
  const known = new Uint8Array(N + 1);
  known[1] = 1;
  const recs = [[1, 0]];
  let best = 0;
  const path = [];
  for (let start = 2; start <= N; start++) {
    path.length = 0;
    let m = start, base;
    while (true) {
      if (m <= N && known[m]) { base = steps[m]; break; }
      path.push(m);
      m = m % 2 === 0 ? m / 2 : 3 * m + 1;
    }
    for (let j = path.length - 1; j >= 0; j--) {
      base += 1;
      const x = path[j];
      if (x <= N && !known[x]) { steps[x] = base; known[x] = 1; }
    }
    const s = steps[start];
    if (s > best) { best = s; recs.push([start, s]); }
  }
  return recs;
}
// [[n, peak], ...] for n in 1..N setting a new RAW trajectory-peak record.
function altitudeRecords(N) {
  const recs = [];
  let best = 0;
  for (let n = 1; n <= N; n++) {
    let x = n, hi = n;
    while (x !== 1) { x = x % 2 === 0 ? x / 2 : 3 * x + 1; if (x > hi) hi = x; }
    if (hi > best) { best = hi; recs.push([n, hi]); }
  }
  return recs;
}

// ---- honest contrast: sibling maps that DO cycle / diverge ----------------
function step3nMinus1(n) { return n % 2 === 0 ? n / 2 : 3 * n - 1; }
function step5nPlus1(n) { return n % 2 === 0 ? n / 2 : 5 * n + 1; }
// the cycle (rotated to its minimum element) that `start` falls into under step.
function findCycle(start, step, cap) {
  cap = cap || 1000000;
  const seen = new Map();
  const path = [];
  let m = start;
  for (let i = 0; i < cap; i++) {
    if (seen.has(m)) {
      const cyc = path.slice(seen.get(m));
      const k = cyc.indexOf(Math.min.apply(null, cyc));
      return cyc.slice(k).concat(cyc.slice(0, k));
    }
    seen.set(m, i);
    path.push(m);
    m = step(m);
    if (m <= 0) return null;
  }
  return null;
}

// ---- rational cycle for a periodic parity pattern (BigInt; Lagarias 1990) --
// pattern is a 0/1 array; returns the cycle as ["p/q", ...] starting at the rational.
function rationalCycle(pattern) {
  const m = pattern.length;
  let P = 1n, Q = 0n;                   // value after i steps = (P*x0 + Q)/2^i
  for (let i = 0; i < m; i++) {
    if (pattern[i]) { Q = 3n * Q + (1n << BigInt(i)); P = 3n * P; }
  }
  let a = 0; for (const b of pattern) a += b;
  const denom = (1n << BigInt(m)) - 3n ** BigInt(a);
  if (denom === 0n) throw new Error("pattern has 2^m == 3^a; no finite rational cycle");
  // reduce x0 = Q/denom
  const g0 = bgcd(Q < 0n ? -Q : Q, denom < 0n ? -denom : denom) || 1n;
  let pn = Q / g0, pd = denom / g0;
  const cyc = [pn + "/" + pd];
  for (let s = 0; s < m - 1; s++) {
    // one accelerated step on the fraction pn/pd (pd odd): parity = pn mod 2
    if (((pn % 2n) + 2n) % 2n === 0n) { pn = pn / 2n; /* pd unchanged but pn even */ }
    else { pn = 3n * pn + pd; pd = pd * 2n; }
    const g = bgcd(pn < 0n ? -pn : pn, pd < 0n ? -pd : pd) || 1n;
    pn /= g; pd /= g;
    cyc.push(pn + "/" + pd);
  }
  return cyc;
}
function bgcd(a, b) { while (b) { [a, b] = [b, a % b]; } return a; }
/* === COLLATZ_CORE END === */

export {
  collatzStep, tStep,
  trajectory, totalStoppingTime, maxValue, stoppingTimeBelow,
  parityVector, numOddSteps, isParityBijection,
  binom, descendingClassFraction, minCounterexampleSurvivors,
  totalStoppingRecords, altitudeRecords,
  step3nMinus1, step5nPlus1, findCycle, rationalCycle,
};
