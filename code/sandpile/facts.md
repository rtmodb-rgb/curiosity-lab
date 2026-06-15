# Abelian Sandpile / BTW Model — Verified Facts with Sources

Compiled 2026-06-15 by the Researcher for the ASM explorable-explanation project.
Goal: precise, sourced statements with explicit caveats so the explainer does not overclaim.

**Conventions.** Graph G = (V, E), undirected finite (multi)graph with a distinguished
non-toppling **sink** s. A site v topples when its grain count z(v) ≥ deg(v), sending one
grain along each incident edge. On the standard 2D square grid, interior sites have deg = 4,
so the threshold is 4; boundary edges lead to the sink (grains are lost at the boundary).
"Stabilization" T(·) = topple until no non-sink site is unstable.

---

## 1. Abelian property (order-independence of stabilization)

**Statement (precise).** Let c be any configuration on a finite graph with a global sink
reachable from every vertex. Toppling unstable non-sink vertices in *any* order until none
remain unstable terminates after finitely many topplings and yields a **unique** stable
configuration T(c). Moreover the *odometer* — the number of times each vertex topples during
stabilization — is also independent of the toppling order. Consequently the grain-addition
operators {a_v} commute, and the final state of an avalanche does not depend on the order in
which sites are fired. (This is the "Abelian" in Abelian Sandpile Model.)

Two equivalent senses of "abelian": (i) order of topplings within one avalanche is irrelevant;
(ii) the order in which external grains are added to different sites is irrelevant.

- **Original source:** D. Dhar, "Self-organized critical state of sandpile automaton models,"
  *Phys. Rev. Lett.* **64**, 1613–1616 (1990).
  DOI: 10.1103/PhysRevLett.64.1613. (Erratum: PRL **64**, 2837 (1990).)
  This paper introduces the abelian operator algebra and proves commutativity.
- **Secondary / expository sources:**
  - L. Levine & J. Propp, "What is… a Sandpile?", *Notices of the AMS* **57**(8), 976–979 (2010).
    https://www.ams.org/notices/201008/rtx100800976p.pdf  (clean statement + proofs sketch).
  - A. Holroyd, L. Levine, K. Mészáros, Y. Peres, J. Propp, D. Wilson, "Chip-firing and
    rotor-routing on directed graphs," in *In and Out of Equilibrium 2*, Progr. Probab. 60 (2008),
    arXiv:0801.3306 — general "abelian property" / strong convergence for chip-firing.
  - Related least-action formalism: A. Fey, L. Levine, Y. Peres, "Growth rates and explosions
    in sandpiles," *J. Stat. Phys.* **138**, 143–159 (2010), arXiv:0901.3805 (the *least-action
    principle*: each vertex topples no more than necessary; ties the odometer to an obstacle problem).
  - Wikipedia "Abelian sandpile model" (good lay summary; cites Dhar).

**Note on terminology.** Dhar's threshold formulation (topple at z ≥ deg) and BTW's original
"slope/height ≥ 4" formulation coincide on the square grid. The abelian property holds for any
finite graph with a sink that every vertex can reach.

---

## 2. Sandpile group: recurrent configs, spanning trees, reduced Laplacian

**Statement (precise).** The *recurrent* configurations (those that recur infinitely often
under random grain addition; equivalently, reachable from the maximal stable configuration)
form a finite **abelian group** under the operation c ⊕ c′ := T(c + c′) (coordinatewise add,
then stabilize). This group is canonically isomorphic to the cokernel of the **reduced graph
Laplacian** Δ̃:

  Sandpile group K(G) ≅ ℤ^{V∖{s}} / Δ̃ ℤ^{V∖{s}},

where Δ̃ is the graph Laplacian L = D − A with the sink's row and column deleted. Each
equivalence class mod Δ̃ contains **exactly one** recurrent configuration (the group elements
*are* the recurrent configs).

**Order of the group.** |K(G)| = det(Δ̃). By **Kirchhoff's Matrix–Tree Theorem**, det(Δ̃)
equals the number of **spanning trees** of G. (For the grid-with-sink, spanning trees of the
graph obtained by joining all boundary sites to a single sink vertex.) The determinant is
independent of which vertex is chosen as sink in a connected graph (the spanning-tree count is
a graph invariant), though the *group up to isomorphism* can depend on the sink in general
graphs; for vertex-transitive-like situations it does not.

- **Sources:**
  - D. Dhar (1990), PRL **64**, 1613 — first identifies recurrent states with the group and
    counts them via the determinant; the bijection with spanning trees comes via the
    "burning algorithm."
  - **Burning algorithm / spanning-tree bijection:** S. N. Majumdar & D. Dhar, "Equivalence
    between the Abelian sandpile model and the q→0 limit of the Potts model," *Physica A*
    **185**, 129–135 (1992); and Dhar's burning test for recurrence.
  - L. Levine & J. Propp, *Notices AMS* **57** (2010): explicitly states K(G) = ℤ^V/Δℤ^V and
    that |K(G)| = number of spanning trees via Matrix–Tree. (good citable secondary source)
  - Survey/textbook: S. Corry & D. Perkinson, *Divisors and Sandpiles: An Introduction to
    Chip-Firing*, AMS (2018) — Ch. 9 gives two proofs of the Matrix–Tree theorem and identifies
    the tree count with the number of recurrent sandpiles.
    http://people.reed.edu/~davidp/divisors_and_sandpiles/
  - Names: the same group is variously called the **sandpile group**, **critical group**,
    **Jacobian**, or (graph) **Picard group**.

**Worked sanity check (in the literature).** Cycle C_n with one sink: n spanning trees ⇒ n
recurrent configurations ⇒ sandpile group ≅ ℤ/nℤ (Babai REU notes; Levine class notes).

---

## 3. Identity element on the n×n grid (the fractal) and how to compute it

**Statement.** Because the recurrent configs form a group, there is an identity element e
(the unique recurrent configuration with e ⊕ c = c for all recurrent c). On a symmetric
domain like an n×n square grid it is generally **not** the all-zero configuration; it is a
striking, self-similar / fractal-patterned recurrent configuration (patches of periodic
"tiling" textures). First studied in depth computationally by **M. Creutz**.

**Standard algorithm ("burn 2·max twice").** Let u_max be the **maximal stable
configuration**. In the convention used by this project's code and page (toppling threshold 4
at *every* site; boundary cells drain their missing edges into a single sink), u_max = **3 at
every site** — one below threshold everywhere. (In the alternative "open-boundary" convention,
where a site's threshold equals its number of grid-neighbours, u_max would instead be 3 interior
/ 2 edge / 1 corner — but that is a *different* model, not the one used here.) Then the identity is

  **e = T( 2·u_max − T(2·u_max) ).**

Procedure (two stabilizations):
1. Form 2·u_max (every site = 6 — unstable; this is exactly what identity() builds: a full grid of 6).
2. Stabilize it: β = T(2·u_max).
3. Subtract coordinatewise: γ = 2·u_max − β. (This is guaranteed ≥ 0, because any stable
   config ≤ u_max, so β ≤ u_max ⇒ γ = u_max + (u_max − β) ≥ 0.)
4. Stabilize again: e = T(γ). This is the group identity.

Why it works (sketch): T(2u_max) = 2u_max − Δ̃x for some integer x, so
T(2u_max − T(2u_max)) = T(Δ̃x) ≡ 0 (mod Δ̃ℤ), i.e. it lies in the identity coset; and it is
recurrent because it is u_max plus a nonnegative config, then stabilized. The unique recurrent
representative of the zero coset is the identity. (Full proof: Doman thesis Thm 4.1 below.)

- **Sources:**
  - M. Creutz, "Abelian sandpiles," *Computers in Physics* **5**, 198 (1991) — first detailed
    study of the identity ("Creutz identity"); coined its computational exploration.
  - Y. Le Borgne & D. Rossin, "On the identity of the sandpile group," *Discrete Mathematics*
    **256**(3), 775–790 (2002) — the e = T(2u_max − T(2u_max)) recipe and its analysis.
  - N. Doman, "The Identity of the Abelian Sandpile Group" (Bachelor thesis, Univ. of
    Groningen, supervisor J. Top, 2020) — **Theorem 4.1 states the identity of R_n is
    T(2u_max − T(2u_max))** with full proof and worked 2×2/3×3/4×4 examples.
    https://fse.studenttheses.ub.rug.nl/21391/1/bMath_2020_DomanN.pdf
  - Fractal/self-similar structure & scaling limit of the identity discussed in:
    M. Lang & M. Shkolnikov, "Harmonic dynamics of the abelian sandpile," *PNAS* **116**(8),
    2821–2830 (2019) — calls it the "sandpile (Creutz) identity," notes its self-similar fractal
    structure and an apparent scaling limit. https://www.pnas.org/doi/10.1073/pnas.1812015116
  - SageMath has `sandpiles` with an `identity()` method (good for the explainer to verify).
    https://doc.sagemath.org/html/en/thematic_tutorials/sandpile.html

**Caveat for the explainer:** the *existence of a scaling limit of the identity* on growing
grids is supported by Pegden–Smart-type results (point 5) but the identity's exact limiting
image is described via the same PDE/Apollonian machinery; it is fine to call it a fractal and
say its large-grid limit is rigorously a scaling limit, but don't claim a simple closed form.

---

## 4. Self-organized criticality & avalanche statistics — THE SOBER TRUTH

> This is the section to be most careful with. The honest summary: **BTW (1987) conjectured
> that avalanche sizes follow a power law, and the model does self-organize to a scale-free
> critical-looking state — but for the deterministic 2D sandpile the avalanche-size
> distribution is NOT a single clean power law. It shows multifractal (not simple finite-size)
> scaling, several distinct and not-simply-related exponents, and reported exponent values
> depend on method and are debated. The deterministic BTW model is also NOT in the same
> universality class as the stochastic (Manna) sandpile, contradicting early universality
> hopes.**

### What is solidly established
- **Self-organization to a critical-looking stationary state.** Under slow random driving
  (add grains, dissipate at the boundary), the system is *attracted* to a stationary measure
  with no tuned parameter. Dhar proved this stationary measure is the **uniform measure on
  recurrent configurations**. Correlation length/time diverge with system size — the hallmark
  of "self-organized" criticality.
  - P. Bak, C. Tang, K. Wiesenfeld, "Self-organized criticality: an explanation of 1/f noise,"
    *Phys. Rev. Lett.* **59**, 381–384 (1987); long version *Phys. Rev. A* **38**, 364 (1988).
  - D. Dhar (1990); D. Dhar, "Theoretical studies of self-organized criticality,"
    *Physica A* **369**, 29–70 (2006) (review).
- **The DIRECTED abelian sandpile is exactly solvable, with genuine clean power laws.** This
  is the one case with rigorous closed-form exponents (mean-field-like).
  - D. Dhar & R. Ramaswamy, "Exactly solved model of self-organized critical phenomena,"
    *Phys. Rev. Lett.* **63**, 1659 (1989).
  - This is why the explainer should distinguish *directed* (clean) from *undirected 2D BTW*
    (messy) sandpiles if it shows exponents.
- **Many *static* quantities of the 2D ASM are computed exactly** via the spanning-tree
  mapping and a conjectured logarithmic conformal field theory with central charge **c = −2**:
  e.g. single-site height probabilities (Majumdar–Dhar 1991/92; Priezzhev 1994), and
  height–height correlations.
  - V. B. Priezzhev, "Structure of two-dimensional sandpile. I. Height probabilities,"
    *J. Stat. Phys.* **74**, 955–979 (1994).
  - S. Mahieu & P. Ruelle, "Scaling fields in the two-dimensional abelian sandpile model,"
    *Phys. Rev. E* **64**, 066130 (2001) — c = −2 logarithmic CFT.
- **Upper critical dimension is believed to be d_c = 4** (mean-field exponents above 4).

### The complications / caveats (do NOT overclaim a single power law)
1. **Not simple finite-size scaling — multifractal scaling instead.** For the 2D deterministic
   BTW, the avalanche-size distribution does **not** collapse under the standard FSS ansatz
   P(s) ≈ s^{−τ} f(s/L^D). Different moments scale with exponents that are not linearly
   related — the signature of **multifractality**. A vanishingly small fraction of very large
   avalanches dominates the higher moments ("constant gap scaling" only in high moments).
   - C. Tebaldi, M. De Menech, A. L. Stella, "Multifractal scaling in the Bak–Tang–Wiesenfeld
     sandpile and edge events," *Phys. Rev. Lett.* **83**, 3952–3955 (1999).
   - M. De Menech, A. L. Stella, C. Tebaldi, "Rare events and breakdown of simple scaling in
     the Abelian sandpile model," *Phys. Rev. E* **58**, R2677–R2680 (1998). Verbatim from the
     abstract: *"Due to intermittency and conservation, the Abelian sandpile in two dimensions
     obeys multifractal, rather than finite size scaling."*
2. **Several distinct avalanche observables with different exponents.** One must distinguish
   - size **s** (total number of topplings),
   - area **a** (number of *distinct* sites that toppled),
   - duration **t** (number of parallel update steps),
   - radius / linear extent / perimeter.
   In 2D BTW sites topple multiple times, so **s ≠ a** (size grows faster than area), and the
   exponents τ_s, τ_a, τ_t are different and not simply related. Decomposing avalanches into
   "waves" of toppling (Ivashkevich–Ktitarev–Priezzhev 1994) gives cleaner objects than raw
   avalanches.
3. **Reported exponent values are method-dependent and debated.** Commonly quoted *effective*
   values for 2D BTW are around τ_s ≈ 1.2–1.35 for size and an avalanche-dimension D ≈ 2.6–2.8,
   but different fitting windows/moment-analyses give different numbers, and these should be
   presented as **effective/contested**, not as exact universal constants. Two-slope fits
   appear (e.g. one set of exponents for large avalanches, another for small).
   - S. Lübeck, "Moment analysis of the probability distribution of different sandpile models,"
     *Phys. Rev. E* **61**, 204 (2000).
   - B. Markovic & C. Gros, "Power laws and self-organized criticality in theory and nature,"
     *Physics Reports* **536**, 41–74 (2014) — review; shows the 2D BTW CCDF needs *two* sets
     of FSS exponents (e.g. τ_S≈1.31, D_S≈2.8 for large avalanches; τ_S≈1.15, D_S≈2 for small),
     i.e. no single clean power law.
4. **BTW (deterministic) and Manna (stochastic) are DIFFERENT universality classes.** Early
   work hoped all conservative sandpiles were universal; careful moment analyses showed the
   deterministic BTW does not share critical exponents/scaling behavior with the stochastic
   Manna model. The Manna model *does* obey clean finite-size scaling (robust "Manna class");
   the deterministic BTW does not.
   - S. S. Manna, "Two-state model of self-organized criticality," *J. Phys. A* **24**, L363 (1991).
   - A. Ben-Hur & O. Biham, "Universality in sandpile models," *Phys. Rev. E* **53**, R1317 (1996).
   - A. Vespignani, R. Dickman, M. A. Muñoz, S. Zapperi, "Absorbing-state phase transitions in
     fixed-energy sandpiles," *Phys. Rev. E* **64**, 056104 (2001) (the FES/driven connection;
     and evidence the two pictures may not share critical features).
   - L. Levine & co., "The approach to criticality in sandpiles," *Phys. Rev. E* **82**, 031121
     (2010), arXiv:1001.3199 — shows the driven sandpile and the fixed-energy sandpile may NOT
     share critical exponents, undercutting a clean DMVZ universality story.
5. **The original "1/f noise" claim is itself contested.** BTW's title invoked 1/f noise, but
   later analyses argued the sandpile's temporal power spectrum is closer to 1/f² than 1/f.
   - H. J. Jensen, K. Christensen, H. C. Fogedby, "1/f noise, distribution of lifetimes, and a
     pile of sand," *Phys. Rev. B* **40**, 7425 (1989).
6. **Real granular sandpiles often do NOT show SOC.** Experiments on actual sand piles
   frequently show quasi-periodic large avalanches, not scale-free statistics; SOC-like
   behavior was seen for elongated grains (rice piles).
   - V. Frette et al., "Avalanche dynamics in a pile of rice," *Nature* **379**, 49 (1996).
   - (caveat already on Wikipedia: "empirical validity of the sandpile model remains a subject
     of debate.")

### Bottom line for the explainer
- Safe to say: BTW self-organizes to a scale-free critical state; avalanches span many orders
  of magnitude and *look* power-law over a range.
- Honest caveat to include: for the **deterministic 2D BTW**, the avalanche distribution is
  **not a single clean power law** — it shows multifractal scaling, multiple exponents (size
  vs. area vs. duration), method-dependent/debated exponent values, and finite-size effects;
  and BTW is **not** in the same universality class as the stochastic Manna model. The clean,
  rigorously-known power laws live in the *directed* sandpile and in mean-field/d≥4.

---

## 5. Scaling limit of the single-source sandpile on ℤ²

**Setup.** Start from the empty lattice ℤ^d (d ≥ 2), drop **N chips at a single vertex** (the
origin), and stabilize (threshold 2d; on ℤ² that is 4). The terminal stable configuration s_N
occupies a region of diameter ~ N^{1/d} and displays an intricate fractal pattern of regions
with periodic toppling-count/height textures.

**Theorem (Pegden–Smart, convergence of the rescaled configuration).** Rescale space by the
natural radius: define s̄_N(x) := s_N(N^{1/d} x). Then s̄_N **converges weak-∗ in L^∞** (i.e.
local spatial averages converge) to a unique limiting function s as N → ∞. Equivalently the
rescaled odometer functions converge (uniformly, after the right normalization) to the solution
of an elliptic obstacle-type **PDE** (a "sandpile PDE"), obtained via viscosity-solution theory
applied to the Fey–Levine–Peres least-action principle.

- W. Pegden & C. K. Smart, "Convergence of the Abelian sandpile," *Duke Math. J.* **162**(4),
  627–642 (2013). arXiv:1105.0111. PDF: https://www.math.cmu.edu/~wes/pdfs/sand.pdf
  (Theorem 1.1: the rescaled sandpiles s̄_n(x) := s_n(n^{1/d} x) converge weak-∗.)

**Caveat (important, do not overstate).** Weak-∗ convergence means *local averages* converge —
it does **not** say the pattern smooths out or converges pointwise. The fractal/microstructure
persists at all scales; what converges is the configuration viewed as a distribution. So "the
sandpile has a scaling limit" is true in this precise averaged sense; the limit object still
encodes fractal structure.

**Explaining the fractal (Levine–Pegden–Smart).** The limit and its self-similar fractal
structure are characterized via *integer-superharmonic matrices*, whose set has an **Apollonian
circle-packing** structure; this yields the Apollonian triangulation seen in zoomed views.
- L. Levine, W. Pegden, C. K. Smart, "Apollonian structure in the Abelian sandpile,"
  *Geom. Funct. Anal. (GAFA)* **26**, 306–336 (2016). arXiv:1208.4839.
  PDF: https://pi.math.cornell.edu/~levine/apollonian.pdf
- L. Levine, W. Pegden, C. K. Smart, "The Apollonian structure of integer superharmonic
  matrices," *Annals of Mathematics* **186**(1), 1–67 (2017). arXiv:1309.3267.
- Foundational least-action input: A. Fey, L. Levine, Y. Peres, *J. Stat. Phys.* **138**, 143
  (2010).

**Related but distinct.** A *different* scaling limit (relaxing a perturbation of the maximal
stable state) converges to a picture described by **tropical curves** — N. Kalinin &
M. Shkolnikov, "Tropical curves in sandpiles," *C. R. Acad. Sci.* (2016) and follow-ups.
Don't conflate this with the single-source Apollonian limit.

---

## Quick "do / don't" cheat-sheet for the explainer

| Claim | Verdict |
|---|---|
| Final stable state independent of toppling order | ✅ TRUE (Dhar 1990) |
| Recurrent configs = finite abelian group | ✅ TRUE (Dhar 1990) |
| \|group\| = #spanning trees = det(reduced Laplacian) | ✅ TRUE (Matrix–Tree) |
| Identity on grid is a fractal; e = T(2u_max − T(2u_max)) | ✅ TRUE (Creutz; Le Borgne–Rossin) |
| BTW self-organizes to a scale-free critical state | ✅ TRUE (BTW 1987; Dhar) |
| 2D BTW avalanche sizes are ONE clean power law | ❌ OVERCLAIM — multifractal, multiple/debated exponents |
| BTW and Manna are the same universality class | ❌ FALSE — different classes |
| BTW "explains 1/f noise" | ⚠️ CONTESTED — closer to 1/f² in analyses |
| Single-source sandpile on ℤ² has a (weak-∗) scaling limit | ✅ TRUE (Pegden–Smart 2013) |
| The limit is exactly smooth / has closed form | ❌ NO — fractal persists; Apollonian structure |
| Directed sandpile has exact power-law exponents | ✅ TRUE (Dhar–Ramaswamy 1989) |

## Could NOT independently verify here (flag if you need it nailed down)
- Exact numerical exponent values for 2D BTW (τ_s, τ_a, τ_t, D): I report *ranges/effective*
  values from reviews because the literature genuinely disagrees and they are method-dependent.
  If the explainer wants to display a number, present it as "effective exponent, contested,"
  not as a constant. (The Markovic–Gros review and Lübeck moment analysis are the best anchors.)
- The precise central-charge/CFT identification (c = −2) is well-supported for *static*
  observables but is a *conjectured* full description of avalanche dynamics, not a theorem.
- Whether the *identity element's* scaling limit has an explicit description: it follows the
  same Pegden–Smart/Apollonian framework but I did not find a clean closed-form for it.
