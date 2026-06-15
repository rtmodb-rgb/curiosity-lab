/*
 * core.js  --  The in-browser Benford engine, in dependency-free JavaScript.
 *
 * Computational Curiosity Lab #4 (Benford's Law).  This is a faithful port of
 * benford.py: the canonical Benford targets, the two leading-digit methods, the
 * exact integer sequence generators (powers / Fibonacci / factorials -- via
 * native BigInt, so there is NO 4300-digit cap the way CPython has), a prime
 * sieve, and the goodness-of-fit statistics.
 *
 * test_core.mjs cross-checks this against benford.py: the 2**n / Fibonacci /
 * factorial leading-digit SEQUENCES are identical to Python's, the prime counts
 * match (pi(1e6)=78498), and the statistics agree to tolerance.
 *
 * The region between the BENFORD_CORE markers is self-contained (no import /
 * export / require), so a web page can inline it verbatim into a <script>.  A
 * byte-identity guard in test_core.mjs checks the page never drifts from this.
 *
 * Leading digit, two ways (mirrors benford.py):
 *   leadStr(x)        -- EXACT, from the decimal string (BigInt or Number).
 *                        Ground truth; no floating point.
 *   leadLog10(log10x) -- from floor(10**frac(log10 value)); the "predict it
 *                        from the logarithm" method used for the equidistribution
 *                        view.  In double precision this is exact for moderate n;
 *                        leadStr is always the canonical digit for histograms.
 */

/* === BENFORD_CORE START === */
"use strict";

// ---- canonical Benford targets -------------------------------------------
function benfordP(d) {            // first digit d = 1..9
  return Math.log10(1 + 1 / d);
}
function benfordTwo(D) {          // first two digits D = 10..99
  return Math.log10(1 + 1 / D);
}
const BENFORD = Array.from({ length: 9 }, (_, i) => benfordP(i + 1));        // [d-1]
const BENFORD_TWO = Array.from({ length: 90 }, (_, i) => benfordTwo(i + 10)); // [D-10]
const LOG10_2 = Math.log10(2);
const LOG10_PHI = Math.log10((1 + Math.sqrt(5)) / 2);

// ---- leading-digit methods ------------------------------------------------
// Exact: first character of the decimal string. Works for BigInt or Number.
function leadStr(x) {
  const s = (typeof x === "bigint" ? x : Math.trunc(Math.abs(x))).toString();
  return s.charCodeAt(0) - 48;           // '1'..'9' -> 1..9
}
// fractional part of a base-10 logarithm, in [0,1)
function mantissaFrac(log10x) {
  const f = log10x - Math.floor(log10x);
  return f < 0 ? f + 1 : f;
}
// leading digit from log10(value): floor(10**frac). A tiny epsilon makes the
// exact d*10**k boundary (e.g. value 2,4,6,8) robust against double round-trip
// noise -- the same subtlety benford.py snaps at 1e-50 (see its lead_log_hp).
function leadLog10(log10x) {
  return Math.floor(Math.pow(10, mantissaFrac(log10x)) + 1e-9);
}
// first two significant digits of a non-negative integer (BigInt or Number)
function firstTwo(x) {
  const s = (typeof x === "bigint" ? x : Math.trunc(Math.abs(x))).toString();
  return s.length >= 2 ? Number(s.slice(0, 2)) : Number(s) * 10;
}

// ---- exact integer sequence generators (BigInt: no digit cap) -------------
function* powers(base, N) {       // base**1 .. base**N
  const b = BigInt(base);
  let v = 1n;
  for (let n = 0; n < N; n++) { v *= b; yield v; }
}
function* fibonacci(N) {          // F1, F2, ... = 1, 1, 2, 3, 5, ...
  let a = 1n, b = 1n;
  for (let n = 0; n < N; n++) { yield a; const t = a + b; a = b; b = t; }
}
function* factorials(N) {         // 1!, 2!, ..., N!
  let f = 1n;
  for (let n = 1; n <= N; n++) { f *= BigInt(n); yield f; }
}
// the geometric two-method generator for base**n: returns the leading digit by
// (1) exact BigInt string and (2) floor(10**frac(n*log10 base)); they agree.
function* powersLeadingTwoMethods(base, N) {
  const log10base = Math.log10(base);
  const b = BigInt(base);
  let v = 1n;
  for (let n = 1; n <= N; n++) {
    v *= b;
    yield [n, leadStr(v), leadLog10(n * log10base)];
  }
}

// ---- prime sieve (Sieve of Eratosthenes) ----------------------------------
// primesUpto(1e6) -> 78498 entries; primesUpto(1e7) -> 664579.
function primesUpto(X) {
  X = Math.floor(X);
  if (X < 2) return [];
  const sieve = new Uint8Array(X + 1).fill(1);
  sieve[0] = sieve[1] = 0;
  const lim = Math.floor(Math.sqrt(X));
  for (let i = 2; i <= lim; i++) {
    if (sieve[i]) for (let j = i * i; j <= X; j += i) sieve[j] = 0;
  }
  const out = [];
  for (let i = 2; i <= X; i++) if (sieve[i]) out.push(i);
  return out;
}

// ---- counting + goodness-of-fit statistics --------------------------------
// Tally first digits 1..9 over an iterable of values -> length-9 array[d-1].
function leadingCounts(iterable, lead = leadStr) {
  const c = new Array(9).fill(0);
  for (const x of iterable) {
    const d = lead(x);
    if (d >= 1 && d <= 9) c[d - 1]++;
  }
  return c;
}
// Tally first-two-digit values 10..99 over integers >= 10 -> length-90 array.
function twoDigitCounts(iterable) {
  const c = new Array(90).fill(0);
  for (const x of iterable) {
    if ((typeof x === "bigint" ? x : BigInt(Math.trunc(x))) < 10n) continue;
    const D = firstTwo(x);
    if (D >= 10 && D <= 99) c[D - 10]++;
  }
  return c;
}
function freqs(counts) {
  const t = counts.reduce((a, b) => a + b, 0);
  return t === 0 ? counts.map(() => 0) : counts.map((c) => c / t);
}
// L-infinity distance of a frequency vector to a target law (default Benford).
function maxdev(fr, targets = BENFORD) {
  let m = 0;
  for (let i = 0; i < targets.length; i++) {
    const d = Math.abs(fr[i] - targets[i]);
    if (d > m) m = d;
  }
  return m;
}
// total-variation distance = 0.5 * sum |fr - target|.
function totalVariation(fr, targets = BENFORD) {
  let s = 0;
  for (let i = 0; i < targets.length; i++) s += Math.abs(fr[i] - targets[i]);
  return 0.5 * s;
}
// Pearson chi-square of observed counts vs the target law.
function chiSquare(counts, targets = BENFORD) {
  const t = counts.reduce((a, b) => a + b, 0);
  let s = 0;
  for (let i = 0; i < targets.length; i++) {
    const e = targets[i] * t;
    if (e > 0) s += ((counts[i] - e) ** 2) / e;
  }
  return s;
}
/* === BENFORD_CORE END === */

export {
  benfordP, benfordTwo, BENFORD, BENFORD_TWO, LOG10_2, LOG10_PHI,
  leadStr, leadLog10, mantissaFrac, firstTwo,
  powers, fibonacci, factorials, powersLeadingTwoMethods, primesUpto,
  leadingCounts, twoDigitCounts, freqs, maxdev, totalVariation, chiSquare,
};
