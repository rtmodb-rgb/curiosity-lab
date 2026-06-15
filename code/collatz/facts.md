# Collatz Conjecture (3n+1 / Syracuse problem) — Sourced Facts

**Compiled:** 2026-06-15 by Researcher for Curiosity-Lab explorable.
**Tagging:** [PROVEN] = rigorous theorem · [EMPIRICAL] = computationally verified / observed · [CONJECTURED] = open · [CITED] = sourced quantity/record · [DRAFT-FLAG] = correction to PI's draft.

Each numeric value below is given so code can assert exact equality. Primary sources cited (arXiv / DOI / journal / OEIS).

---

## ⚠️ TL;DR — Corrections to the PI's draft (read first)

1. **Verification record is OUT OF DATE.** Barina 2021 reached 2^68 ≈ 2.95×10^20 — *correct for that paper* — but Barina's **2025** follow-up pushed it to **2^71 ≈ 2.36×10^21** (J. Supercomputing 81, art. 810, 2025). Use 2^71 as the current record. [DRAFT-FLAG]
2. **Eliahou's cycle-length bound is ~17 *million*, not ~17 *billion*.** The minimum number of elements in a nontrivial cycle from Eliahou (1993) is **17,087,915** (≈1.7×10^7). The draft's "~17 billion" is wrong by ~1000×. *Separately*, the **current** best cycle-length bound (2025, tied to the 2^71 verification) is **217,976,794,617** (≈2.18×10^11) for the shortcut map — that one *is* ~218 billion. Don't conflate the two. [DRAFT-FLAG]
3. **Terras parity-vector bijection holds for the ACCELERATED / Syracuse map** T(n)=n/2 (even), (3n+1)/2 (odd) — NOT the raw two-step map. This is the map to implement. (Details in §3.) [DRAFT-FLAG: draft was unsure — answer is the accelerated map.]
4. **Krasikov–Lagarias c = 0.84 is CORRECT** (x^0.84, Acta Arith. 109, 2003). ✓
5. **Tao published in *Forum of Mathematics, Pi* 10 (2022), e12**, doi:10.1017/fmp.2022.8 (the draft asked "published where?"). ✓ statement.
6. **All requested OEIS first terms verified correct** (A006877, A006878, A006884, A006885). 27 peaks at **9232** and has total stopping time **111**. ✓ (nuance in §6: the peak 9232 is hit mid-trajectory, not "at step 111").
7. **3n−1 cycles at 1, 5, 17 — CORRECT.** (§8.)

---

## 1. Statement & history

### The map [PROVEN definitions]
- **Raw Collatz map** f(n) = n/2 if n even; 3n+1 if n odd. (Wikipedia/Lagarias notation; Tao writes Col(N).)
- **Accelerated / "shortcut" / Syracuse map** T(n) = n/2 if n even; (3n+1)/2 if n odd. (Since 3n+1 is even for odd n, this just folds the forced halving into one step.) **Most theory (Terras, Eliahou, cycle work) uses T.**
- **Conjecture [CONJECTURED]:** for every positive integer N, iterating reaches 1 (i.e. Col_min(N)=1). Equivalent statements: every n≥2 has finite *stopping time*; the only cycle is the trivial one.
- **Stopping time** σ(n): least k with T^k(n) < n. **Total stopping time** σ_∞(n): least k with T^k(n)=1 (for raw map: steps to reach 1). (Lagarias 1985.)

### History [CITED — with nuance]
- Named for **Lothar Collatz**, who introduced the idea in **1937**, two years after his doctorate (Wikipedia; MathWorld "posed by L. Collatz in 1937"; Lagarias survey). **Nuance/flag:** Collatz did *not* publish the 3n+1 problem at the time — it circulated by word of mouth (through the 1950s–60s) and the first research publications appeared only in the 1970s. The "1937" is from his notebooks/recollection, so cite it as "introduced ~1937" rather than "published 1937." [DRAFT-FLAG: "1937?" — yes, but as introduction/notebook date, not publication.]
- **Aliases** (all per Lagarias 1985 / MathWorld): the **3n+1 problem**, **Syracuse problem/algorithm** (popularized at **Syracuse University**, via Kakutani), **Hasse's algorithm** (Helmut Hasse), **Kakutani's problem** (Shizuo Kakutani), **Ulam's problem/conjecture** (Stanisław Ulam), **Thwaites conjecture** (Bryan Thwaites), **hailstone numbers**, **wondrous numbers** (Hofstadter, *GEB*).
- **Authoritative surveys (USE THESE as primary):**
  - J. C. Lagarias, "The 3x+1 problem and its generalizations," *Amer. Math. Monthly* **92** (1985), 3–23. (The canonical survey.)
  - J. C. Lagarias (ed.), *The Ultimate Challenge: The 3x+1 Problem*, AMS, 2010, ISBN 978-0-8218-4940-8. (Includes Lagarias's two annotated bibliographies, also on arXiv: arXiv:math/0309224 and arXiv:math/0608208.)
- **Famous quotes [CITED]:** Erdős: "Mathematics may not be ready for such problems." (Guy, *Unsolved Problems in Number Theory*.) Lagarias (2010): the conjecture "is an extraordinarily difficult problem, completely out of reach of present day mathematics."

---

## 2. Computational verification record [CITED / EMPIRICAL]

- **Current record (2025): all N ≤ 2^71 ≈ 2.3612×10^21 verified to reach 1.**
  - David Barina, "Improved verification limit for the convergence of the Collatz conjecture," *The Journal of Supercomputing* **81** (2025), art. no. 810. doi:10.1007/s11227-025-07337-0.
  - Exact: 2^71 = **2,361,183,241,434,822,606,848** ≈ 2.36×10^21. (Wikipedia lead now states "up to 2.36×10^21," citing Barina 2025.)
- **Prior record (2021): all N ≤ 2^68 ≈ 2.95×10^20.**
  - David Barina, "Convergence verification of the Collatz problem," *The Journal of Supercomputing* **77** (2021), 2681–2688. doi:10.1007/s11227-020-03368-x. Code: github.com/xbarin02/collatz.
  - Exact: 2^68 = **295,147,905,179,352,825,856** ≈ 2.9515×10^20.
- **Earlier (context):** Tomás Oliveira e Silva verified up to ~**20·2^58 ≈ 5.76×10^18** (and ran a long-running project at sweet.ua.pt/tos/3x+1.html). His tables also feed OEIS extended terms.
- **Note for the explorable:** the live tracker at pcbarina.fit.vutbr.cz reports ongoing GPU verification. Treat 2^71 as the citable record; anything beyond is in-progress, not peer-reviewed.

---

## 3. Terras parity-vector / stopping-time theorem (CENTERPIECE)

**Primary source:** Riho Terras, "A stopping time problem on the positive integers," *Acta Arithmetica* **30** (1976), no. 3, 241–252. doi:10.4064/aa-30-3-241-252. MR0568274. Free PDF: matwbn.icm.edu.pl/ksiazki/aa/aa30/aa3034.pdf.

**Which map:** Terras uses the **accelerated map** T(x) = x/2 if x even, **(3x+1)/2** if x odd. ALL of the following are stated for T. [DRAFT-FLAG: this is the map to implement.]

### (a) Density-1 finite stopping time [PROVEN]
- Define stopping time σ(n) = least k≥1 with T^k(n) < n.
- **Theorem (Terras 1976):** *the set of positive integers with finite stopping time has natural density 1.* Equivalently, the density of n with σ(n) = ∞ is 0; "almost every n eventually drops below its starting value." Proof uses the distribution of parity vectors + a central-limit-theorem argument.
- Independently proved by **C. J. Everett**, "Iteration of the number-theoretic function f(2n)=n, f(2n+1)=3n+2," *Advances in Mathematics* **25** (1977), 42–45.
- ⚠️ This is much weaker than the full conjecture: density-1 "drops below start once" ≠ "reaches 1," and natural-density-0 exceptional set could still be infinite.

### (b) Parity-vector bijection [PROVEN — implement this exactly]
- For n, define the **parity vector** of length k:
  v_k(n) = ( x_0 mod 2, x_1 mod 2, …, x_{k−1} mod 2 ), where x_0 = n and x_{i+1} = T(x_i).
  (Each bit records whether step i used the odd rule (3x+1)/2 [bit 1] or the even rule x/2 [bit 0]. The parity sequence = the sequence of operations.)
- **Theorem (Terras 1976; restated Lagarias 1985):** v_k(n) depends only on **n mod 2^k**, and the induced map
      Z/2^k Z  →  {0,1}^k ,   (n mod 2^k) ↦ v_k(n)
  is a **bijection** (a permutation of the 2^k residue classes). Equivalently: *two integers m, n have the same first-k parity sequence ⟺ m ≡ n (mod 2^k).* Each of the 2^k possible 0/1 patterns is realized by exactly one residue class mod 2^k.
- **Consequences to assert in code:** for fixed k, as n ranges over a complete residue system mod 2^k, the 2^k parity vectors are all distinct → exactly one residue per pattern. (e.g. k=1: residues {0,1}→bits {0,1}; k=2: the 4 residues map bijectively to the 4 bit-pairs.)
- **2-adic form [PROVEN]:** the parity-vector function Q(x)=Σ_{k≥0} (T^k(x) mod 2)·2^k is a **2-adic isometry** of Z_2 (Lagarias 1985 §; Wikipedia "As a parity sequence"). Hence every infinite parity sequence corresponds to exactly one 2-adic integer, and almost all Z_2 trajectories are acyclic.

### (c) "Coefficient stopping time" [CITED]
- Terras also introduced the **coefficient stopping time** χ(n): the least k for which the affine 3x+1 transform's multiplicative coefficient forces T^k(n)<n (the count of odd steps among the first k). He proved χ(n) ≤ σ(n) for all n, and the **Coefficient Stopping Time Conjecture** is that χ(n)=σ(n) for n>1 (open; discussed in Lagarias 1985).

---

## 4. Tao (2019/2022) — "almost all orbits attain almost bounded values" [PROVEN, CITE not re-prove]

**Source:** Terence Tao, "Almost all orbits of the Collatz map attain almost bounded values," *Forum of Mathematics, Pi* **10** (2022), e12, 1–56. doi:10.1017/fmp.2022.8. arXiv:1909.03562 (submitted Sep 2019; published 2022). ISSN 2050-5086.

**Setup (Tao's notation):** Col(N)=3N+1 (N odd), N/2 (N even); Col_min(N)=inf_n Col^n(N).

**Theorem 1.3 (precise statement):** *For any function f: N+1 → R with lim_{N→∞} f(N) = +∞ (no matter how slowly), one has Col_min(N) ≤ f(N) for **almost all** N, in the sense of **logarithmic density**.*

**Context / what it improves [CITED]:**
- **Korec (1994)** earlier showed: for any θ > log3/log4 ≈ **0.7924**, Col_min(N) ≤ N^θ for almost all N in the sense of **natural** density.
- Tao replaces the power N^θ by *any* divergent f (e.g. log log log N), at the cost of using logarithmic (not natural) density.
- Method: approximate invariant/self-similar measure for the (accelerated/Syracuse) dynamics; characteristic-function estimate of a skew random walk on a 3-adic cyclic group; a 2-D renewal process. (For the explorable: it does **not** prove the conjecture — exceptional set could be infinite, and "below f(N)" ≠ "reaches 1".)
- Quanta described it as "one of the most significant results on the Collatz conjecture in decades."

---

## 5. Krasikov–Lagarias lower bound [PROVEN, CITED]

**Source:** Ilia Krasikov & Jeffrey C. Lagarias, "Bounds for the 3x+1 problem using difference inequalities," *Acta Arithmetica* **109** (2003), no. 3, 237–258. doi:10.4064/aa109-3-4. arXiv:math/0205002. MR1980260.

**Result:** *For all sufficiently large x, the number of n in [1,x] whose forward orbit reaches 1 is at least x^c with c = 0.84.* i.e. #{n ≤ x : orbit of n contains 1} ≥ x^0.84.
- **c = 0.84 is correct** [DRAFT confirmed]. This improved earlier tree-search bounds (Applegate–Lagarias had x^0.81; Krasikov earlier x^{3/7}≈0.428, x^0.65, x^0.81). Computer-aided proof via nonlinear-programming difference inequalities.

---

## 6. OEIS exact data for record-holders [CITED/EMPIRICAL — all verified against OEIS]

> Map used by these sequences: the **raw** map (both 3x+1 and halving steps counted), n>1 until reaching 1.

### A006877 — starting values setting new TOTAL-stopping-time records (raw-map steps to reach 1)
First 44 terms (verified on OEIS):
```
1, 2, 3, 6, 7, 9, 18, 25, 27, 54, 73, 97, 129, 171, 231, 313, 327, 649, 703,
871, 1161, 2223, 2463, 2919, 3711, 6171, 10971, 13255, 17647, 23529, 26623,
34239, 35655, 52527, 77031, 106239, 142587, 156159, 216367, 230631, 410011,
511935, 626331, 837799
```
(Draft's "1,2,3,6,7,9,18,25,27,54,73,97,…" ✓.)

### A006878 — the corresponding record total stopping times
First terms (verified):
```
0, 1, 7, 8, 16, 19, 20, 23, 111, 112, 115, 118, 121, 124, 127, 130, 143, 144,
170, 178, 181, 182, 208, 216, 237, 261, 267, 275, 278, 281, 307, 310, 323, ...
```
(Draft's "0,1,7,8,16,19,20,23,111,…" ✓.) **Pairing:** A006877[9]=27 ↔ A006878[9]=111, so 27 has total stopping time **111**. ✓

### A006884 — starting values setting new records for **highest point of trajectory** (altitude)
First terms (verified):
```
1, 2, 3, 7, 15, 27, 255, 447, 639, 703, 1819, 4255, 4591, 9663, 20895, 26623,
31911, 60975, 77671, 113383, 138367, 159487, 270271, 665215, 704511, 1042431,
1212415, 1441407, 1875711, 1988859, 2643183, 2684647, 3041127, 3873535,
4637979, 5656191, 6416623, 6631675
```

### A006885 — the corresponding record **maximum values reached** (peaks)
First terms (verified):
```
1, 2, 16, 52, 160, 9232, 13120, 39364, 41524, 250504, 1276936, 6810136,
8153620, 27114424, 50143264, 106358020, 121012864, 593279152, 1570824736,
2482111348, 2798323360, 17202377752, 24648077896, 52483285312, 56991483520,
90239155648, 139646736808, 151629574372
```
**Pairing (assert in code):** A006884[k] ↔ A006885[k]:
- (1↔1), (2↔2), (3↔16), (7↔52), (15↔160), **(27↔9232)**, (255↔13120), (447↔39364), …
- ✓ **27 reaches a peak (altitude) of 9232** [DRAFT confirmed]. Its full raw trajectory has 111 steps to 1; the value 9232 is hit *mid-trajectory* (around step ~77 of 111), then it descends to 1. So phrase as: "27 climbs to 9232 before falling, taking 111 steps total." [minor DRAFT precision]

### Other useful sequences
- **A006370** — the Collatz map itself: a(n)=3n+1 if n odd, n/2 if n even.
- **A006577** — number of halving+tripling steps for n to reach 1 (the "total stopping time" of n; a(27)=111). MathWorld/Wikipedia A006577.
- **A025586** — largest value (peak) in the trajectory of n (a(27)=9232). (A006885 = its record values.)
- **A070165** — irregular triangle: full trajectory of n. (A008884 = the n=27 trajectory specifically.)
- **A060410 / A060409 / A060411** — peak values, dropping times, and step-of-max for the A006884 record-holders.

---

## 7. No nontrivial cycle — lower bounds [PROVEN / CITED]

Using the **shortcut map** T; "cycle" = (a_0,…,a_q) distinct positive integers with T(a_i)=a_{i+1}, T(a_q)=a_0. Only known cycle: **(1, 2)** [the trivial cycle].

- **Min element of any nontrivial cycle > current verification bound:** since all n ≤ 2^71 reach 1, any nontrivial cycle's least element exceeds **2^71 ≈ 2.36×10^21**. [PROVEN given verification — EMPIRICAL input]
- **Eliahou (1993) — cycle length:** Shalom Eliahou, "The 3x+1 problem: new lower bounds on nontrivial cycle lengths," *Discrete Mathematics* **118** (1993), 45–56. doi:10.1016/0012-365X(93)90052-U.
  - Result: any nontrivial cyclic orbit under T must contain **at least 17,087,915 elements** (≈1.7×10^7). [DRAFT-FLAG: this is 17 *million*, not 17 *billion*.]
  - Sharper structural result: the period p of any nontrivial cycle has the form **p = 301994·a + 17087915·b + 85137581·c**, with a,b,c ≥ 0 integers, **b ≥ 1**, and **a·c = 0**. (Derived from the continued-fraction expansion of log_2 3.)
- **Current best cycle-length bound (2025):** **217,976,794,617** (shortcut map) ≈ 2.18×10^11, or **355,504,839,929** without the shortcut. (Wikipedia, citing Barina 2025 — improves as the verification limit rises.) [CITED]
- **m-cycle results [PROVEN]:** An "m-cycle" = a cycle splitting into m runs of (increasing odds then decreasing evens).
  - Steiner (1977): no nontrivial **1-cycle**.
  - Simons (2005): no **2-cycle** (*Math. Comp.* 74, 1565–1572).
  - Simons & de Weger (2005): no **m-cycle for m ≤ 68** (*Acta Arithmetica* **117** (2005), 51–70, doi:10.4064/aa117-1-3).
  - **Hercher (2023): no m-cycle for m ≤ 91.** Christian Hercher, "There are no Collatz m-cycles with m ≤ 91," *J. Integer Sequences* **26** (2023), Article 23.3.5. arXiv:2201.00406. [confirms draft]

---

## 8. Honest contrast variants — why the conjecture is non-obvious [PROVEN cycles, CITED]

These show that the "3" and "+1" matter: nearby maps DO have nontrivial cycles / divergence. Display these truthfully.

### 3n−1 map (n/2 if even, 3n−1 if odd), positive integers
- **Three known cycles** (conjectured to be all), least element first:
  1. **1 → 2 → 1** (trivial)
  2. **5 → 14 → 7 → 20 → 10 → 5**
  3. **17 → 50 → 25 → 74 → 37 → 110 → 55 → 164 → 82 → 41 → 122 → 61 → 182 → 91 → 272 → 136 → 68 → 34 → 17**
  [DRAFT confirmed: cycles at 5 and 17 (plus trivial 1).]
- **Equivalence [PROVEN]:** 3n−1 on positive integers ≡ the 3n+1 map on *negative* integers. The full-integer 3n+1 map has exactly **four known cycles** (Wikipedia "Iterating on all integers"): around 1 (1→4→2→1), −1 (−1→−2), −5 (−5→−14→−7→−20→−10), and −17 (length 18). The last three correspond to the 3n−1 positive cycles at 1, 5, 17.

### 5n+1 map (n/2 if even, 5n+1 if odd)
- **Known small cycles** (least element first), e.g.:
  - **1 → 6 → 3 → 16 → 8 → 4 → 2 → 1**
  - **13 → 66 → 33 → 166 → 83 → 416 → 208 → 104 → 52 → 26 → 13**
  - **17 → 86 → 43 → 216 → 108 → 54 → 27 → 136 → 68 → 34 → 17**
- **Believed divergent [CONJECTURED/EMPIRICAL]:** many starting values (e.g. **7**, also 9, 11) appear to grow without bound — no cycle found. The 5n+1 problem is conjectured to have orbits diverging to ∞ for almost all n. (Caveat: divergence is *observed/heuristic*, not proven — verify exact cycle membership numerically before displaying, since these come from recreational sources, not a peer-reviewed catalog. The 1- and 13- and 17-cycles are easy to re-verify by hand.)
- **Heuristic [HEURISTIC]:** for qn+1 maps, the multiplicative drift per odd step is ~q/4 (after forced halving). For q=3: 3/4 < 1 ⇒ expected decrease ⇒ conjecture plausible. For q=5: 5/4 > 1 ⇒ expected increase ⇒ divergence plausible. (Matthews–Watts 1984 heuristics; MathWorld.) This single inequality is the cleanest "why 3n+1 but not 5n+1" talking point.

---

## 9. Other rigorously-checkable / "verify-it-yourself" facts

- **[PROVEN] Geometric-mean drift = 3/4.** Over odd steps of the shortcut map, the geometric mean of successive-ratio is 3/4 (each odd value is on average 3/4 of the previous odd value). This is a *heuristic for the conjecture* but a *theorem* about the 2-adic extension: for almost all 2-adic starting values there are exactly two halving steps per tripling step. (Wikipedia §heuristic; Lagarias.) [Label as HEURISTIC for integers, PROVEN for 2-adic measure.]
- **[PROVEN] Multiples of 3 are never interior cycle members / unreachable as non-start odd values appropriately**; integers ≡0 mod 3 cannot lie on a nontrivial cycle (used to prune searches).
- **[PROVEN] Self-similarity mod 2^k (from §3b):** the surviving residues (possible first-counterexample classes) thin out exponentially. Concrete checkable fact: **the only surviving residues mod 32 are 7, 15, 27, 31** (all others provably drop below themselves within ≤5 steps). Good interactive widget: let users pick k and see which residues mod 2^k survive. (Wikipedia "shortcuts"; Garner 1981.)
  - Smaller examples to assert: first counterexample must be odd (since f(2n)=n<2n); must be ≡3 mod 4 (since f²(4n+1)=3n+1 < 4n+1).
- **[PROVEN] Rational cycles (shortcut map):** every periodic parity sequence is generated by **exactly one rational** with odd denominator (Lagarias 1990, *Acta Arith.* 56, 33–53). Example to display: parity cycle (1 0 1 1 0 0 1) ↔ the rational **151/47**, giving the rational cycle 151/47 → 250/47 → 125/47 → 211/47 → 340/47 → 170/47 → 85/47 → 151/47.
- **[EMPIRICAL/HEURISTIC] Benford's law for trajectory values.** Leading digits of Collatz trajectory values are *observed* to approximately follow Benford's law; this is empirical/heuristic, **not** a proven theorem for Collatz specifically. Label clearly as EMPIRICAL. (See the team's /shared/kb/benford-facts.md for the rigorous Benford background and the distinction between proven generators (e.g. 2^n is Benford by equidistribution of n·log10(2)) and merely-observed ones.)
- **[PROVEN, fun] Real/complex extension:** Chamberland (1996) showed a smooth real interpolation of the map has orbits escaping monotonically to ∞ and a second attracting 2-cycle near (1.1925…, 2.1386…) — so the conjecture is special to the integers. (Wikipedia §extension; Chamberland, *Dynamics of Continuous, Discrete and Impulsive Systems* 1996.)
- **[CITED, culture] Undecidability flavor:** Conway (1972) showed generalized Collatz-type functions can be Turing-complete (FRACTRAN); in 2024 a 6-state Turing machine ("antihydra") was found whose halting reduces to a Collatz-like problem, suggesting BB(6) is extremely hard. (Wikipedia §"As a computational problem".)

---

## Source ledger (primary, with identifiers)

| Topic | Source | ID |
|---|---|---|
| Terras stopping time + parity bijection | Acta Arith. 30 (1976) 241–252 | doi:10.4064/aa-30-3-241-252; MR0568274 |
| Everett independent proof | Adv. Math. 25 (1977) 42–45 | — |
| Lagarias survey | Amer. Math. Monthly 92 (1985) 3–23 | — |
| Lagarias annotated bibliographies | arXiv:math/0309224, arXiv:math/0608208 | (in AMS 2010 book) |
| Tao 2019/2022 | Forum of Math. Pi 10 (2022) e12 | doi:10.1017/fmp.2022.8; arXiv:1909.03562 |
| Korec density bound | Math. Slovaca 44 (1994) | θ>log3/log4≈0.7924 |
| Krasikov–Lagarias x^0.84 | Acta Arith. 109 (2003) 237–258 | doi:10.4064/aa109-3-4; arXiv:math/0205002 |
| Barina 2021 (2^68) | J. Supercomput. 77 (2021) 2681–2688 | doi:10.1007/s11227-020-03368-x |
| Barina 2025 (2^71) | J. Supercomput. 81 (2025) art.810 | doi:10.1007/s11227-025-07337-0 |
| Eliahou cycle length | Discrete Math. 118 (1993) 45–56 | doi:10.1016/0012-365X(93)90052-U |
| Simons & de Weger m≤68 | Acta Arith. 117 (2005) 51–70 | doi:10.4064/aa117-1-3 |
| Simons no 2-cycle | Math. Comp. 74 (2005) 1565–1572 | doi:10.1090/s0025-5718-04-01728-4 |
| Hercher m≤91 | J. Integer Seq. 26 (2023) Art.23.3.5 | arXiv:2201.00406 |
| Lagarias rational cycles | Acta Arith. 56 (1990) 33–53 | doi:10.4064/aa-56-1-33-53 |
| OEIS records | A006877, A006878, A006884, A006885, A006577, A025586, A006370, A070165 | oeis.org |

*All OEIS first-terms above were pulled directly from oeis.org/<id>/list on 2026-06-15 and match the PI's draft where given (with the two corrections flagged in the TL;DR).*
