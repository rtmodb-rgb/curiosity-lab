# Benford's Law — Honest Fact Ledger (Lab #4)

*This is the integrity backbone of the explorable. It separates **what this
repo's code actually proves** from **what we cite but do not re-prove** from
**what is empirical or genuinely open**. Every headline number that appears on
the page is listed below with **exactly how it was checked**.*

- **Computation engine:** [`benford.py`](benford.py) (pure stdlib, no numpy).
- **The rigor gate:** [`verify.py`](verify.py) — STDLIB-ONLY, deterministic.
  As of the last run it prints **`RESULT: 23 checks passed. VERIFICATION
  PASSED.`** (~28 s). The page cites this number **23**; it is stable across a
  fresh clone *because the gate imports nothing optional* (the Lab #3 lesson:
  never let the check count depend on an optional dependency).
- **Browser parity:** [`core.js`](core.js) is the in-page engine; the marked
  `BENFORD_CORE` region is inlined **verbatim** into the HTML.
  [`test_core.mjs`](test_core.mjs) cross-checks it against `benford.py` and
  prints **`RESULT: 16 passed, 0 failed.`** (~4 s).
- **Sourced background & citations:** the inline citations throughout this file and the
  **Sources** section of the explorable.

Last verified: 2026-06-15.

---

## A. PROVEN-BY-CODE-HERE (recomputed in this repo, two ways where possible)

These are *not* assertions — `verify.py` recomputes each from scratch and fails
loud if it drifts. "Two ways" means **two independent leading-digit
algorithms** had to agree: **(1)** exact leading digit from the big-integer's
**decimal string** (ground truth, no floating point) and **(2)** the
high-precision **`floor(10**frac(n·log10 base))`** log method, which *never
forms the big integer at all* — it works purely in the exponent. Agreement of
these two is the computational signature that "Benford for a geometric sequence
**is** equidistribution of `n·log10 r mod 1`."

| # | Headline claim (as shown on the page) | Measured value | How checked (gate IDs) |
|---|---|---|---|
| 1 | `P(d)=log10(1+1/d)` matches the published table to 5 dp; P(1)=0.30103 … P(9)=0.04576; sums to 1 | sum = 1.000000000000000 | `0a`, `0b` |
| 2 | Two-digit law `P(D)=log10(1+1/D)` sums to 1 **and** marginalizes *exactly* to the first-digit law | max marg. error = **1.39e-16** | `0c`, `0d` |
| 3 | **2ⁿ is Benford.** Two independent leading-digit methods agree for **every** n=1..20000 | **0** disagreements | `A1` *(two ways)* |
| 4 | 2ⁿ at N=20000 is an excellent fit: max|freq−Benford| and χ² don't reject | maxdev = **0.000092**; χ² = **0.0049** (≪ 15.507 = χ²₍.95,8₎) | `A2`, `A3` |
| 5 | **2ⁿ converges** — maxdev strictly shrinks as N grows | N=100: **0.00918** → 1000: **0.00205** → 5000: **0.00065** → 20000: **0.00009** | `A4`, `A5` |
| 6 | **Fibonacci is Benford** (two methods agree; tight fit at M=20000) | 0 disagreements (n≤2000); maxdev = **0.000097** | `B1` *(two ways)*, `B2` |
| 7 | **n! is Benford** (two methods agree, *including the 3!=6 boundary*) | 0 disagreements (n≤2000) | `C1` *(two ways)* |
| 8 | n! fits Benford at N=5000 but **looser** than 2ⁿ | maxdev = **0.010453** | `C2` |
| 9 | **Convergence RATE differs: n! is much slower than 2ⁿ.** n! at N=5000 is farther from Benford than 2ⁿ is at *both* N=5000 *and* N=20000 | n!:**0.01045** vs 2ⁿ@5000:**0.00065** vs 2ⁿ@20000:**0.00009** | `C3` |
| 10 | **Generalized two-digit law for 2ⁿ:** first-two-digits → `log10(1+1/D)`, D=10..99 | maxdev = **0.000138** | `F1` |
| 11 | **Primes are a POOR, cutoff-dependent fit** (the honest contrast) | maxdev > 0.1 at every cutoff: **0.1767, 0.1789, 0.1806** for X=10⁵,10⁶,10⁷ | `D2` |
| 12 | **P(prime leads with 1) DRIFTS down with the cutoff** → no natural-density limit | **0.1244 → 0.1221 → 0.1204** (X=10⁵→10⁶→10⁷), strictly decreasing | `D3` |
| 13 | …and that drift sits *between* uniform 1/9 and Benford 0.30103 (neither is the limit) | 0.1111 < P(1) < 0.30103 ✓ | `D4` |
| 14 | **Prime sieve is correct** — counts match known π(x) | π(10⁵)=9592, π(10⁶)=78498, π(10⁷)=664579 ✓ | `D1` |
| 15 | **Uniform & normal samples are NOT Benford** | uniform(1,1000) maxdev = **0.18918**; normal(500,100) maxdev = **0.29974** | `E1`, `E2` |
| 16 | **Regression:** the log method is exact at every `d·10ᵏ` boundary (the snap fix, §D) | 0 mismatches over d=1..9, k=0..5; `lead_float`==`lead_str` on 20000 random ints | `G1`, `G2` |

**What "Benford for 2ⁿ/Fibonacci/n!" means here, precisely.** We do **not**
re-prove the limit theorem in code (you can't verify an asymptotic limit by
finite computation). What the code *does* prove, rigorously and reproducibly,
is: (a) the two independent leading-digit methods **agree exactly** over the
whole tested range — confirming the equidistribution mechanism numerically; and
(b) the empirical first-digit frequencies are **within a tight, decreasing
envelope** of the Benford targets, with the envelope shrinking as N grows
(monotone convergence behaviour). The *theorem that the limit equals Benford*
is cited (§B), not recomputed.

---

## B. CITED-NOT-REPROVED (we rely on the literature; the page says so)

These are stated on the page as theorems with attribution. The repo's code is
**consistent with** them but does **not** constitute a proof of them.

- **The master equivalence.** A sequence `(aₙ)` is Benford ⇔ `(log10 aₙ mod 1)`
  is equidistributed in [0,1). *Diaconis (1977), Ann. Probab. 5, 72–81;
  Berger–Hill (2015), Ch. 4.* — Our two-method agreement is the numerical
  shadow of this; the equivalence itself is cited.
- **Weyl's equidistribution theorem** (irrational rotation: `nα mod 1`
  equidistributes ⇔ α irrational). *Weyl (1916), Math. Ann. 77, 313–352.* This
  is **why** 2ⁿ and Fibonacci are Benford (`log10 2`, `log10 φ` irrational). We
  use the irrationality; we don't prove Weyl.
- **n! is Benford — Diaconis (1977).** Crucially, n! is **not** geometric
  (`log10 n! = Σ log10 k`), so it does **not** follow from the elementary
  irrational-rotation fact. Its equidistribution mod 1 is a genuinely deeper
  theorem. The page presents 2ⁿ/Fibonacci as "elementary Weyl" and n! as "a
  theorem (Diaconis 1977)" — and our check `C3` *demonstrates* the practical
  consequence (much slower convergence), without claiming to prove the theorem.
- **Primes have no natural-density leading-digit limit.** The proportion
  oscillates forever as the cutoff grows. *Raimi (1976); Caldwell, Prime Pages
  FAQ.* A Benford-type value appears only under **logarithmic/analytic density**
  (*Whitney 1972; Cohen–Katz 1984*). For a **finite cutoff** the fit is a
  size-dependent generalized law that drifts toward **uniform**, not Benford
  (*Luque–Lacasa 2009, Proc. R. Soc. A 465, 2197*). Our checks `D2`/`D3`/`D4`
  *exhibit* this oscillation/drift empirically (and figure 4 shows the full
  sawtooth); the non-existence-of-limit **theorem** is cited.
- **Scale-invariance ⇒ Benford — Pinkham (1961)**, *Ann. Math. Statist. 32,
  1223*. (Older than Hill; attribute scale-invariance to Pinkham.)
- **Base-invariance ⇒ Benford, and the random-mixture "statistical derivation"
  — Hill (1995)** (*Proc. AMS 123, 887*; *Statistical Science 10, 354*). The
  mixture theorem explains why *heterogeneous, multi-source* data trend Benford;
  it does **not** say every individual distribution or dataset is Benford.

Full primary-source list (journal, volume, pages) appears inline above and in the
explorable's **Sources** section.

---

## C. EMPIRICAL / OPEN (no theorem forces it; honest about that)

- **Real-world datasets (e.g. country areas, physical constants) "are
  Benford."** This is **empirical**. No theorem says a *particular* dataset must
  conform. Datasets that span many orders of magnitude, arise from
  multiplicative/growth processes, or mix many sources tend to fit well; Hill's
  mixture theorem is the best *explanation*, not a per-dataset proof.
  - If the page ships a real-data demo it uses
    [`data/country_areas.json`](data/country_areas.json) (CIA World Factbook —
    U.S. Government work, **public domain**). The Benford fit there is computed
    live and **labelled empirical**. (This data file is the principal's, not
    produced by this repo's verifier; `verify.py` does not depend on it, so the
    cited check count 23 is independent of it.)
- **The exact asymptotic leading-digit behaviour of primes at finite cutoff**
  is governed by the size-dependent GBL (Luque–Lacasa) → uniform; we show the
  drift numerically but the page frames the limit as **cited**.
- **Forensic / fraud / election applications** are *empirical practice with
  serious caveats*, not theorems. First-digit Benford tests on vote counts are
  considered **unreliable** by specialists (precincts span too narrow a
  magnitude range); present as a cautionary tale, not a success. *Deckert–
  Myagkov–Ordeshook (2011) + Mebane's reply, Political Analysis 19(3).*
- **The second-digit Benford mean ≈ 4.187** (Mebane's 2BL constant) is **quoted
  from the literature**; we did not re-sum it here.

---

## D. WHERE REALITY DIFFERED FROM THE NAIVE PLAN — the `3!=6` boundary bug

This is the one place implementation reality bit, and it's worth recording
because it nearly produced a *silently lucky* "pass."

**The trap.** Method 2 (the independent log method) takes the leading digit as
`floor(10**frac(log10 value))`. For a value that is **exactly `d·10ᵏ`** — e.g.
`6` (`= 3!`), or `2 = 2¹`, `4 = 2²`, `8 = 2³` — the true mantissa is the integer
`d`, but the floating round trip `10**(log10 6)` lands at `5.999…9`, and a naive
`floor` returns **5**, i.e. `d−1`. So a naive method-2 disagrees with the exact
string method *precisely at the boundary values*.

**Why it almost slipped through.** For `2ⁿ` the only boundary cases in range are
the tiny n=1,2,3 (values 2,4,8). With ordinary float precision those *happened*
to round the right way, so a naive run reported "0 disagreements" for `2ⁿ` — a
pass that depended on the **luck of the rounding direction**, not on
correctness. The factorial sequence exposed it immediately at `3! = 6`.

**The fix (robust, not lucky).** `benford.py::lead_log_hp` computes the mantissa
in `decimal` at 100 significant digits and **snaps** it with
`.quantize(Decimal(1).scaleb(-50))` (`_SNAP = 1e-50`) before flooring. This
`1e-50` threshold is:
- **~44 orders of magnitude below** the closest any *genuine* (non-boundary)
  mantissa comes to an integer boundary over the tested range — the minimum
  `2ⁿ` mantissa-to-boundary gap for n≤20000 is **≈6.4e-6** (at n=15772); and
- **~40 orders of magnitude above** the high-precision round-trip noise (~1e-90).

So the snap corrects **only** the exact-`d·10ᵏ` round-trip artefact and can
never perturb a real near-boundary value. After the fix, **all three** sequences
(2ⁿ, Fibonacci, n!) give **0 disagreements** — robustly, by design, not by
rounding luck.

**Hardened against regression.** Checks `G1` (every `d·10ᵏ`, d=1..9, k=0..5) and
`C1` (which explicitly asserts the `3!=6` case is exercised) would fail loudly if
the snap were ever removed. The exact decimal-string method (`lead_str`) remains
the unimpeachable ground truth; method 2 is the *independent cross-check*, now
exact everywhere it's tested.

**Lesson recorded:** a "0 disagreements" pass is only meaningful if it's robust
to perturbation. Verify the *mechanism*, not just the lucky number.

---

## E. Reproduce it yourself

```bash
cd benford
python3 verify.py            # -> RESULT: 23 checks passed. VERIFICATION PASSED.   (~28s, stdlib only)
node   test_core.mjs         # -> RESULT: 16 passed, 0 failed.                      (~4s, needs Node)
python3 figures.py           # -> writes img/fig1..5 at 1600x800, logs to figures.log  (needs matplotlib)
python3 benford.py           # quick self-print of P(d), 2**n stats, primes count
```

`verify.py` and `benford.py` need **only the Python standard library** — a fresh
clone reproduces the same 23-check result with no environment surprises.
`figures.py` is the only piece that needs a third-party package (matplotlib);
it is **not** part of the rigor gate and does not affect the cited check count.
