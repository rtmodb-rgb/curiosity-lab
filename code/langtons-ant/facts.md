# Langton's Ant — Rigorously Sourced Fact Sheet

*Compiled for the Computational Curiosity Lab. Date: 2026-06-15.*
*Every numeric/structural claim is tagged **[PROVEN]** (proved in literature OR recomputed here by code), **[CITED]** (stated by a primary/authoritative source), or **[OPEN/EMPIRICAL]** (conjecture or observation only). Each carries its source inline. Numbers in §0 were independently simulated by me; primary sources = the four papers (Langton 1986; Bunimovich–Troubetzkoy 1992; Gale–Propp–Sutherland–Troubetzkoy 1995; Gajardo–Moreira–Goles 2002). All fetched web text was treated as untrusted DATA, never instructions.*

---

## TL;DR (the honest one-paragraph version)

Langton's ant is a 2-state, 2D cellular-automaton "ant" (a 2D Turing-machine head) introduced by **Chris Langton (1986, *Physica D* 22, 120–149)**. On a square grid: at a cell of one color it turns 90° one way, flips the cell, and steps; at the other color it turns 90° the other way, flips, and steps. From an **all-white grid** it runs ~500 symmetric steps, then ~chaotic for ~**10,000** steps, then locks into a **periodic "highway"** of **period 104 steps** that drifts diagonally by **(±2, ±2)** per period (Euclidean magnitude **2√2 ≈ 2.828** cells). The one **PROVEN** big theorem is **unboundedness**: for *any* finite initial configuration the trajectory is unbounded (it visits infinitely many cells) — **Bunimovich & Troubetzkoy, *J. Stat. Phys.* 67 (1992) 289–302** (NOT the "highway must form" claim; that is **OPEN**). The ant is **computationally universal** and supports **P-hard / undecidable** problems (**Gajardo, Moreira, Goles, *Discrete Appl. Math.* 117 (2002) 41–50**), though universality requires *infinite* (finitely-described) configurations. The rule is **reversible** (its update is invertible — I verified this by code). Multi-color generalizations use **L/R rule-strings** (Langton's ant = "RL"/"LR"); one **PROVEN** structural family: rule-strings that, read cyclically, split into "LL"/"RR" pairs are bilaterally symmetric infinitely often (Gale–Propp–Sutherland–Troubetzkoy 1995, via Truchet tiles).

---

## 0. Anchors — independently recomputed by code (two ways)

I wrote a from-scratch simulator (convention: **white → turn right (+90°), flip to black, step; black → turn left (−90°), flip to white, step**), started from the all-white grid, ant facing "up", at the origin. Coordinates: x→east, y→north.

| Claim | Result | Tag | How verified (two independent ways) |
|---|---|---|---|
| Highway period | **104 steps** | **[PROVEN-by-code]** | (a) Displacement vector pos(s+104)−pos(s) is constant AND heading repeats for all late s; (b) P=52 fails (heading mismatch, disp (−6,−4)), P=104 is the minimal period. |
| Net displacement / period | **(−2, −2)**, magnitude **√8 = 2√2 ≈ 2.8284271** | **[PROVEN-by-code]** | (a) Direct vector measurement at many period boundaries (constant); (b) `math.hypot(2,2)=2.8284271247…`. Sign is convention-dependent (see ⚠). |
| Black cells added / period | **+12 net black cells per 104 steps** | **[PROVEN-by-code]** | Black-count deltas across consecutive period boundaries: 715→727→739→751 = **+12 each**. (Two boundaries checked, identical.) |
| Highway onset (all-white start) | first 104-periodicity holds from **step ≈ 9977** in my run | **[PROVEN-by-code]** / **[CITED ~10,000]** | My code: last deviation at step 9976. Literature rounds to **"about 10,000"** (Gajardo et al. 2002; Wikipedia). Exact step is **definition-dependent** — see ⚠. |
| Rule is **reversible** (update invertible) | reversing 5000 forward steps returns **exactly** to origin, all-white grid, original heading | **[PROVEN-by-code]** | Implemented the inverse map (un-step, then read the just-restored cell color to recover prior heading & color); round-trip = identity. |

> Cross-check vs an independent earlier run's anchors: **period 104 ✓**, **magnitude 2√2 ✓**, **emergence ~10,000 ✓**. That run measured displacement **(−2, +2)** and onset **~10,081**; this run measured **(−2, −2)** and onset **~9977**. These are **NOT discrepancies** — the y-sign flips with grid orientation (y-up vs y-down) and the x-sign flips with chirality (R-on-white vs L-on-white); the onset integer depends on how "onset" is defined. The robust invariants — **period 104**, **|disp| = 2√2**, **+12 cells/period**, **reversibility** — all agree. (See ⚠.)

---

## 1. The rule and its conventions

**[CITED] Definition.** Langton's ant is a 2-state 2D cellular automaton equivalent to a **2-dimensional Turing-machine head** ("the ant") on the square lattice ℤ². Each cell is white/black (state 0/1). One common statement of the rule (MathWorld convention):
> 1. On a **black** square, turn **right** 90° and move forward one unit. 2. On a **white** square, turn **left** 90° and move forward one unit. 3. When the ant leaves a square it **inverts** that square's color.
> — MathWorld, "Langton's Ant", https://mathworld.wolfram.com/LangtonsAnt.html

**[CITED] Chirality / orientation conventions differ between sources** — this is the single most important presentation footnote:
- **Wikipedia** & this fact sheet's §0: at **white** turn **90° clockwise (right)**, at **black** turn **90° counter-clockwise (left)**. (https://en.wikipedia.org/wiki/Langton%27s_ant)
- **MathWorld**: the **mirror image** — at **black** turn right, at **white** turn left.
These two are reflections of each other and produce identical dynamics up to a left-right flip; the highway just heads to the mirror-image diagonal. Any explorable must **pick one convention and state it**, because it fixes the sign of the drift direction (southwest vs southeast vs etc.). Magnitude (2√2) and period (104) are convention-independent.

**[CITED] CA / Turing-machine viewpoint.** The ant can be described as a CA in which the ant-occupied cell carries one of 8 colors encoding (cell state × 4 headings); equivalently it is the head of a 2D Turing machine with von Neumann neighborhood. (Gajardo–Moreira–Goles 2002, §1; MathWorld calls it "a 4-state two-dimensional Turing machine".)

---

## 2. Origin — Chris Langton, 1986

**[CITED] Primary source:** C. G. Langton, **"Studying artificial life with cellular automata," *Physica D: Nonlinear Phenomena* 22 (1–3) (1986) 120–149.** doi:10.1016/0167-2789(86)90237-X; hdl:2027.42/26022. The ant first appears in this paper, in the context of Langton's broader artificial-life program (he organized the first Artificial Life workshop the same year).
- Peer-reviewed secondary confirmation of attribution: **Gajardo–Moreira–Goles 2002** open with *"The virtual ant introduced by Langton [Physica D 22 (1986) 120]…"* — i.e., they cite this exact paper/page as the origin.
- A. Gajardo's project page: *"The ant was christened after its first discoverer, Chris Langton… presented it (among others) in an article for Physica D in 1986."* (https://www2.udec.cl/~angajardo/langton/general.html)
- ⚠ **Terminology caveat:** secondary sources call Langton's object the **"virtual ant"** (Gajardo et al.) or simply **"ant"** (Esolang: *"originally called 'ant' by its creator"*). I could **not** directly open the 1986 PDF to quote Langton's own in-paper wording — treat the exact term Langton used as **unverified by me** (the *attribution* to this paper is solid; the *exact word* is not independently confirmed here).

---

## 3. The PROVEN centerpiece — Unboundedness (no bounded trajectory)

**[PROVEN — primary citation:]** L. A. Bunimovich & S. E. Troubetzkoy, **"Recurrence properties of Lorentz lattice gas cellular automata," *Journal of Statistical Physics* 67 (1–2) (1992) 289–302.** doi:10.1007/BF01049035; Bibcode 1992JSP....67..289B.

**Exact statement (as quoted by primary literature):** Gale, Propp, Sutherland & Troubetzkoy (1995) name it the
> **"Fundamental Theorem of Myrmecology (Bunimovich–Troubetzkoy): An ant's track is always unbounded."**
> — *Further Travels with My Ant*, arXiv:math/9501233, §"The Story So Far".

And Gajardo–Moreira–Goles 2002 (§1.2) state it as:
> *"for any initial configuration, the trajectory of the ant is unbounded [2]."* ([2] = Bunimovich–Troubetzkoy 1992.)

**What is PROVEN:** For **any** finite (more generally, any) initial configuration, the ant **cannot remain in a bounded region forever** — it visits **infinitely many** cells; there is **no "repeatable"/periodic-in-place** trapped configuration. The framing is the **2D Lorentz lattice gas** (the ant = a particle scattering off "mirrors"/rotators). 
- **Stronger generalization [CITED/PROVEN]:** S. Troubetzkoy ("Lewis–Parker lecture 1997: the ant," *Alabama J. Math.* 21 (2) (1997)) proved the set of cells visited **infinitely often** has **no corners** (a "corner" = a set-cell with two non-opposite neighbors outside the set). Unboundedness follows as a corollary. (Cited in Gajardo et al. 2002, ref [18], and on Gajardo's page.)

**What is NOT proven by this theorem:** It does **NOT** prove that the **highway** specifically must form, nor that the long-term motion is the period-104 drift. Unboundedness is fully compatible with (hypothetical) non-highway unbounded behavior from some configurations. Keep these strictly separate (see §4).

**⚠ Naming discrepancy (handle carefully):** **MathWorld** labels the unboundedness result the **"Cohen–Kung theorem"** (https://mathworld.wolfram.com/Cohen-KungTheorem.html — *"A theorem that guarantees that the trajectory of Langton's ant is unbounded."*). **Wikipedia explicitly flags this as a misattribution:** *"this result was incorrectly attributed and is known as the Cohen-Kong theorem"* (citing Ian Stewart, *Sci. Am.* 271(1) (1994) 104–107). The **peer-reviewed proof of record is Bunimovich–Troubetzkoy (1992)**; "Cohen–Kung" is a popular-science name of disputed provenance. **Recommendation:** cite the result as **Bunimovich–Troubetzkoy (1992)** and, if you mention "Cohen–Kung," explicitly note it is a contested/popular name.

---

## 4. The OPEN problem — does the highway ALWAYS emerge?

**[OPEN/EMPIRICAL].** The statement *"from every finite initial configuration the ant eventually builds the periodic highway"* is an **open conjecture**, NOT a theorem. Distinguish two things:
1. **all-white start → highway** — **observed/empirical** (every simulation does it; it is *not* a separate theorem that it must).
2. **any finite config → highway** — **OPEN conjecture.**

**Primary statement of the open problem** — Gajardo–Moreira–Goles 2002, §1.2 (verbatim):
> *"it is conjectured: For any initial configuration with finite support, the ant eventually starts building the periodic highway, in some unobstructed direction. … If the conjecture is true, then any problem associated to the ant, whose input is an initial configuration with finite support, is decidable…"*
And §4 (Conclusions): *"the decidability of problems whose input is a configuration with finite support remains an open question. A positive answer would be given if the conjecture … is found to be true."*

Corroborating "still open" statements:
- **Wikipedia:** *"All finite initial configurations tested eventually converge to the same repetitive pattern, suggesting that the 'highway' is an attractor … but no one has been able to prove that this is true for all such initial configurations."*
- **MathWorld:** *"It is believed that no matter what initial pattern … it will eventually build a highway … This would appear to follow naturally from the fact that Langton's ant is reversible, although it remains formally unproved (Beermann and Van Foeken)."* ⚠ Note: the "reversibility ⇒ highway" intuition is a **heuristic, not a proof**.

So: **highway-from-all-white = robust empirical fact; highway-from-any-finite-config = open** (stated open by Gajardo, Moreira & Goles; echoed by Propp's circle, Wikipedia, MathWorld).

---

## 5. Computational universality, P-hardness, undecidability

**[PROVEN — primary citation:]** A. Gajardo, A. Moreira, E. Goles, **"Complexity of Langton's ant," *Discrete Applied Mathematics* 117 (1–3) (2002) 41–50.** doi:10.1016/S0166-218X(00)00334-6; arXiv:nlin/0306022. (Received 2000; full text read via the authors' PDF.)

**What is proved, precisely (from the paper's own §1.3 / §4):**
- **Boolean-circuit simulation:** They give an explicit construction where the **trajectory of a single ant** evaluates **any Boolean circuit** — input bits encoded as cell states, gates (NOT, AND, plus Cross/Copy/Duplicate junctions) laid out in rows, output read from a cell's final state.
- **[PROVEN] P-hardness:** The problem **(P)** = *"Given a finite initial configuration, an initial ant position, and a target cell γ — does the ant ever visit γ?"* is **P-hard**, by a log-space reduction from the **P-complete** Circuit Value Problem (CVP). *(So this hardness result already applies to **finite** configurations.)*
- **[PROVEN] Universality:** Using an **infinite but finitely-described** configuration (infinitely many circuit copies in a trapezoidal array simulating a linear CA, which can simulate a universal Turing machine), the ant is **capable of universal computation** ("simulates a universal Turing machine"). The authors explicitly call this *"a rather weak notion of universality (which requires an infinite — but finitely described — configuration)."*
- **[PROVEN] Undecidability:** Consequently there exist **undecidable** problems about the ant — e.g. whether a given finite block ever appears in the ant's evolution — **for infinite-support** initial configurations.

**Precision to preserve in the build:**
- **P-hardness** is shown for the "does-it-visit-cell-γ" problem on **finite** configs.
- **Universality / undecidability** require **infinite** (finitely-described) configs. Whether *finite-support* problems are decidable is **OPEN** and would follow from the §4 highway conjecture.
- Note dual phrasings in the wild: some secondary sources say "P-hard for reachability"; the paper's own term is P-hard via reduction from CVP. Both refer to the same Theorem.

---

## 6. Generalizations — turmites, L/R rule-strings, and the proven symmetry family

**[CITED] Multi-color "generalized ants" (Turk–Propp).** Use n cell-states cycled 1→2→…→n→1; a **rule-string** of n letters L/R tells the ant to turn left/right at each state. **Langton's ant is the 2-symbol string** — written **"RL"** in the Turk–Propp/Wikipedia convention, or **"LR"** in the Gale–Propp–Sutherland–Troubetzkoy convention (*"the simple ant has the rule-string LR"*, where L↔1, R↔0, so it is "ant 2"). ⚠ The two strings denote the **same** ant under relabeling of which color is "first" and which turn is L vs R; pick a convention and state it. (Sources: Wikipedia "Extension to multiple colors"; Gale et al. 1995 §"The Story So Far".)

**[PROVEN] The bilateral-symmetry theorem** — D. Gale, J. Propp, S. Sutherland, S. Troubetzkoy, **"Further Travels with My Ant," *Mathematical Intelligencer* 17 (3) (1995) 48–56** (reprinted as Ch. 18 of D. Gale, *Tracking the Automatic ANT*, Springer 1998); arXiv:math/9501233.
- **Statement (as the paper proves and Wikipedia summarizes):** If the rule-string, viewed as a **cyclic** list, decomposes into consecutive **identical pairs "LL" or "RR"**, then the ant's configuration returns to (central/bilateral) **symmetry infinitely often** — the pattern "keeps coming back to symmetry." 
- **Worked examples from the paper:** length-4 ants **9 = LRRL** and **12 = LLRR** are *"the truly surprising ones … the patterns get ever larger, but without ever getting too far away from bilateral symmetry."* Length-6: rule-strings **33, 39, 48, 51, 60** give symmetric patterns — and *"all these numbers are divisible by three"* (explained by the theorem, not coincidence).
- **Proof method:** **Truchet tiles** + the **Jordan curve theorem** for a special class of closed contours (the "principal contour"). This is a **genuine theorem with proof**, distinct from catalog observations.
- Simplest symmetric example commonly quoted: **"RLLR"** (Wikipedia).

**[OPEN/EMPIRICAL — observational catalog, NOT proven]:** The behaviors of most other multi-color ants and **turmites** (multi-*state* ants — "Turing machine termites," Ed Pegg Jr.) are **empirical**:
- **"RLR"** — *"Grows chaotically. It is not known whether this ant ever produces a highway."* (Wikipedia — explicitly an open empirical question.)
- **"LLRR" / "RRLL"** — symmetric growth (covered by the proven theorem above).
- **"LRRRRRLLR"** — *fills a square region around itself*; **"LLRRRLRLRLLR"** — *builds a convoluted highway*; **"RRLLLRLLLRRR"** — grows a filled triangle that starts moving after ~15,900 steps. **These specific behaviors are observations** (Wolfram-style / Wikipedia image catalog), **not theorems** — present them as empirical.

> Rule of thumb for the page: **proven** in this area = (i) unboundedness (Bunimovich–Troubetzkoy), (ii) no-corners (Troubetzkoy), (iii) the LL/RR cyclic-pair symmetry theorem (Gale–Propp–Sutherland–Troubetzkoy), (iv) P-hardness/universality/undecidability (Gajardo–Moreira–Goles). **Everything else about specific rule-strings, highways forming, or "looks chaotic" is empirical.**

---

## 7. Exactly-checkable structural facts (good for two-ways verification)

- **[PROVEN-by-code] Reversibility / invertibility.** Langton's ant's global update is a **bijection** on (grid-coloring, ant-position, ant-heading): given the current state you can uniquely reconstruct the previous state. I verified by implementing the inverse and round-tripping 5000 steps back to the exact all-white origin. (Consistency check vs MathWorld, which notes the ant "is reversible.") This can be re-verified by running forward N then backward N and asserting identity. *(Caveat: the heuristic "reversible ⇒ must build highway" is NOT a proof — see §4.)*
- **[PROVEN-by-code] Highway period & geometry.** Period **104**; net drift **(±2, ±2)** ⇒ Euclidean step **2√2 ≈ 2.828** per period; **+12 net black cells per period** (the highway is a fixed repeating ribbon of cells, translated by (±2,±2) each cycle). Minimal period: P=52 fails, P=104 is minimal. Recompute by detecting the smallest P with constant displacement + repeating heading after onset.
- **[CITED] Three-phase qualitative behavior from all-white** (Gajardo et al. 2002; Wikipedia; Gale et al. 1995): (1) **~first ~500 steps** roughly symmetric/simple; (2) **~chaotic until ~10,000 steps**; (3) **highway** (period-104 drift) thereafter. The "~500" and "~10,000" are **approximate literature figures**, not exact constants (Gale et al.: *"after about 10,000 time-units the ant settles into … highway-building"*; Gajardo et al.: *"seemingly randomly for about 10,000 steps"*).
- **[CITED] Parity / step-color bookkeeping.** Each step flips exactly one cell (white↔black) and turns the heading by exactly ±90°, so heading lives in ℤ/4 and changes parity every step; the total black-cell count changes by ±1 each step (net **+12** over a highway period, as measured). Useful as an invariant/checksum in a simulator. *(This is elementary bookkeeping, not a deep theorem.)*

---

## ⚠ Discrepancies / things to double-check when building

1. **Convention fixes the drift direction's sign, not its magnitude.** R-on-white vs L-on-white (chirality) and y-up vs y-down (screen coords) flip the signs of the drift vector. The earlier run's **(−2, +2)** and this run's **(−2, −2)** are the *same physics* in different conventions. **Decide one convention, state it in the UI, and label the diagonal accordingly.** Convention-independent facts to headline: **period 104**, **|drift| = 2√2 ≈ 2.828**, **+12 cells/period**.
2. **"Cohen–Kung theorem" is a contested name.** Cite unboundedness as **Bunimovich–Troubetzkoy (1992), *J. Stat. Phys.* 67, 289–302**. If you mention "Cohen–Kung," flag it as a popular-science name that Wikipedia calls a misattribution (origin: Stewart, *Sci. Am.*, 1994). Don't present "Cohen–Kung" as the canonical citation.
3. **Highway-onset step is definition-dependent.** Literature says "~10,000." My code's first-104-periodic step ≈ **9977**; an earlier run measured ≈ **10,081**; MathWorld's example figure is at step 10,647. Use **"~10,000 (about 10⁴) steps"** in copy and, if you show a precise integer, **define exactly** how you detect onset (e.g., "first step from which the 104-step displacement signature holds forever").
4. **Keep PROVEN vs OPEN crisp.** PROVEN: unboundedness (any finite config). OPEN: highway-from-any-finite-config. EMPIRICAL: highway-from-all-white (observed every time, but its inevitability is the open conjecture). Do not let "the ant always makes a highway" sound like a theorem.
5. **Universality's fine print.** Universality & undecidability need **infinite (finitely-described)** configurations; **P-hardness** holds for **finite** configs. Don't claim "Langton's ant is Turing-complete on finite configs" — that's exactly what's open (decidability of finite-support problems).
6. **Rule-string notation ("RL" vs "LR").** Same ant, different bookkeeping. State which convention your turmite explorer uses.
7. **Unverified by me:** Langton's *exact in-paper wording* for the ant (I could not open the 1986 PDF directly; attribution to Physica D 22:120–149 is solid via Gajardo et al.). Also, the *Math. Intelligencer* page numbers and the JSP page range are taken from cross-agreeing secondary indexes (MathWorld, dblp, the arXiv journal-ref, Springer) — they agree, but I did not see the journals' own title pages.

---

## Primary sources (full citations)

1. **C. G. Langton**, "Studying artificial life with cellular automata," *Physica D* **22**(1–3) (1986) 120–149. doi:10.1016/0167-2789(86)90237-X. — *Origin of the ant.*
2. **L. A. Bunimovich, S. E. Troubetzkoy**, "Recurrence properties of Lorentz lattice gas cellular automata," *J. Stat. Phys.* **67**(1–2) (1992) 289–302. doi:10.1007/BF01049035. — *Unboundedness ("Fundamental Theorem of Myrmecology").*
3. **S. Troubetzkoy**, "Lewis–Parker lecture 1997: the ant," *Alabama J. Math.* **21**(2) (1997). — *"Visited-infinitely-often set has no corners" (generalizes unboundedness).*
4. **D. Gale, J. Propp, S. Sutherland, S. Troubetzkoy**, "Further Travels with My Ant," *Mathematical Intelligencer* **17**(3) (1995) 48–56; arXiv:math/9501233; repr. in D. Gale, *Tracking the Automatic ANT*, Springer 1998 (Ch. 18). — *L/R rule-strings; LL/RR cyclic-pair bilateral-symmetry theorem (Truchet tiles + Jordan curve).*
5. **A. Gajardo, A. Moreira, E. Goles**, "Complexity of Langton's ant," *Discrete Appl. Math.* **117**(1–3) (2002) 41–50. doi:10.1016/S0166-218X(00)00334-6; arXiv:nlin/0306022. — *Boolean-circuit construction; P-hardness; universality & undecidability (infinite configs); states the highway conjecture as OPEN.*

Authoritative tertiary (orientation / cross-checks only, not cited for novel claims):
- MathWorld, "Langton's Ant" / "Cohen–Kung Theorem" — https://mathworld.wolfram.com/LangtonsAnt.html
- Wikipedia, "Langton's ant" — https://en.wikipedia.org/wiki/Langton%27s_ant
- A. Gajardo, "What you should know about Langton's ant" — https://www2.udec.cl/~angajardo/langton/general.html
