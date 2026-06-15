# Builder's note — the hat monotile (Computational Curiosity Lab #3)

The verified computational foundation for "the hat" (the 2023 aperiodic
monotile of Smith, Myers, Kaplan & Goodman-Strauss). **Brand ethos: compute,
don't assert; verify every headline number two independent ways; be honest
about what doesn't fully work.** This note is the honest ledger — read it
before writing any public page on top of these files.

Gates (both green, both exit nonzero on any failure):
- `python3 verify.py`  → **RESULT: 27 core checks passed (+ 6 optional shapely cross-checks = 33 total when shapely is installed). VERIFICATION PASSED.** (numpy + sympy only ⇒ 27; the headline count is the 27 core checks.)
- `node test_core.mjs`  → **RESULT: 105 passed, 0 failed.**

---

## 1. The hat (hat.py)

- **13 vertices / 13 edges** — confirmed (`len(HAT_OUTLINE) == 13`). It is a
  non-convex 13-gon.
- **Tile(1, √3)** — edge-length multiset is `{1.0 ×6, √3 ×6, 2.0 ×1}` (one
  "a"-edge is doubled to length 2). This pins it as **Tile(1, √3)**, *not*
  Tile(1,1) (which is the equilateral *spectre* base — a common confusion).
- **Area = 8√3 ≈ 13.856406461**, checked two independent ways:
  1. shoelace of the 13-gon, and
  2. sum of the **8 kite** areas (each kite = √3), with an independent shapely
     check that the 8 kites' union has zero symmetric difference with the
     13-gon. Also = **32 unit-triangles** (8√3 = 32·√3/4).
- The 8-kite overlay (kisrhombille kites of a side-2 hexagon grid; hexagon
  centres touched: (0,0)×4, (2,2)×2, (4,−2)×2) was found **computationally**
  and verified to union exactly to the authoritative 13-gon.

## 2. The substitution (substitution.py) — realized matrix

Four metatiles **H** (hexagon, 4 hats — exactly **one reflected**), **T**
(triangle, 1 hat), **P** (parallelogram, 2 hats), **F** (pentagon, 2 hats).

The substitution matrix is **REALIZED**, not asserted: `realized_matrix()`
counts children-by-type in the actual geometric substitution (build the
29-tile patch, carve the next-level H,T,P,F, count what each contains). It
reproduces the reference exactly (columns/rows in order H,T,P,F):

```
        from H  from T  from P  from F
   H  [   3       1       2       2  ]
   T  [   1       0       0       0  ]
   P  [   3       0       1       1  ]
   F  [   3       0       2       3  ]
```

i.e. the rule **H → 3H + 1T + 3P + 3F**, T → H, P → 2H+P+2F, F → 2H+P+3F.

### Eigen-structure (verify.py, two+ independent ways)
- **numpy dominant eigenvalue = 6.8541019662 = (7+3√5)/2 = φ⁴** (φ = golden
  ratio). Linear inflation is φ² ≈ 2.618; area inflation φ⁴ ≈ 6.854.
- **sympy exact characteristic polynomial = (x−1)(x+1)(x²−7x+1)** — eigenvalues
  {φ⁴, 1, 7−φ⁴ ≈ 0.14589803, −1}.
- **Perron (limit-frequency) eigenvector**, normalized to sum 1:
  `(1/3, 7/6−√5/2, √5−2, 3/2−√5/2) = (0.33333333, 0.04863268, 0.23606798,
  0.38196601)`. Matched two ways: sympy nullspace of (M−φ⁴I), and the column
  of a high float matrix-power (see caveat 5).
- **Realized counts == Mᵏ·e_seed exactly** for every seed and k = 0..5 (the
  geometric tree's actual hat labels are counted, then compared to integer
  matrix powers — they agree exactly).

## 3. Geometric verification (verify.py) — a real patch is a real tiling

On a **level-4 H** patch (**1156 hats**) and an independent **level-3 F** patch
(112 hats), all in exact integer arithmetic (global ×2 scale puts every hat
vertex on the integer triangular lattice; each hat has integer area **J = 32**):

- **(f) no overlaps** — every directed atomic edge is unique, AND all 8N kite
  cells are distinct (two independent exact-integer tests). shapely cross-check:
  max pairwise overlap area = 0.
- **(g) no gaps** — every interior atomic edge is shared by exactly 2 tiles; the
  boundary is exactly ONE simple loop (no holes); enclosed area = 32·N exactly.
  shapely cross-check: union has 0 holes, 1 piece, area = 16·N (hex units).
- **(h) every tile is congruent to the canonical hat** — 0/1156 (and 0/112)
  non-congruent, using a reflection-aware edge+turning-angle signature; all hat
  transforms share one scale (|det| = 1 in the doubled frame) and are isometries.
- **(i) unreflected : reflected → φ⁴** — reflected hats live ONLY in H metatiles
  (one each). The ratio **oscillates** (because of the ±1 eigenvalues) and only
  converges in the limit: L2..L6 = `7.33333, 6.68182, 6.86395, 6.85035, 6.85431`
  → φ⁴ = 6.85410. At level 4 there are **147 reflected** of 1156 hats.

## 4. core.js ↔ substitution.py (test_core.mjs)

`core.js` is a dependency-free, line-by-line JS port (browser-inlinable region
between `/*===HAT_CORE_START===*/` and `/*===HAT_CORE_END===*/`). The Node test
compares it to the Python for **every seed {H,T,P,F} × level 1..5**:

- total hat count, counts by metatile type, counts by label (reflected vs
  unreflected), and the **full multiset of hat centroids to 6 decimals** — all
  identical (both run in the same global-scale-2 frame, so coordinates agree, not
  merely "up to similarity"). **105/105 PASS.**
- The marked core region has no import/export/require and, extracted alone,
  reproduces `patch(4,'H')` — so a web page can inline it verbatim.

Bonus (verified): total hats from the H seed are
**4, 25, 169, 1156, 7921 = 2², 5², 13², 34², 89²** — squares of every-other
Fibonacci number. (Verified for 5 terms from the realized counts; stated as an
observed identity, not proved here.)

## 5. Figures (figures.py → img/, figures.log)

Rendered full-bleed with exact figure size; **intrinsic pixel dimensions are
content-driven and read back from disk with PIL** (not forced square, no
`bbox_inches='tight'`):

| file | px | aspect | content |
|---|---|---|---|
| `img/fig1_hat.png` | 1400 × 1010 | 1.39 | the hat (13-gon) + its 8 kites, vertices marked |
| `img/fig2_substitution.png` | 1800 × 701 | 2.57 | one step: H metatile → level-2 H, children coloured by type (H→3H+1T+3P+3F) |
| `img/fig3_patch.png` | 1700 × 1669 | 1.02 | level-4 tiling, 1156 hats coloured by orientation, the 147 reflected hats lit up |

(fig3 is ~square because the patch's extent is ~square — that is the true
content aspect, correctly preserved.)

---

## Caveats & honesty ledger (read this)

1. **What is ported vs. derived.** The hat's 13-gon outline and the four
   metatile placement transforms are **ported** (BSD-3-Clause) from Craig
   Kaplan's `hatviz` (github.com/isohedral/hatviz) — getting the placement
   transforms right from prose is the crux, so we lean on the authoritative
   source. The numeric matrix **M** is **per cp4space** (Adam P. Goucher). What
   is **ours and independently verified here**: the 8-kite decomposition (found
   computationally), the *realization* of M by counting actual geometric
   children, the entire eigen-structure, and all geometric (overlap/gap/
   congruence) checks.

2. **Supertiles are NOT geometrically self-similar at finite levels** (except
   the trivial T). This is a faithful combinatorial+geometric substitution, not
   a naive fixed-shape inflation: the level-k H is *not* a scaled copy of the
   level-1 H — its boundary shape changes with k and only converges to a limit
   shape. Do **not** draw a single fixed inflation rule and claim the supertile
   equals a scaled metatile. (This is why fig2 shows the genuine carved
   children, not a self-similar redraw.)

3. **The ratio converges, it doesn't sit at φ⁴.** unreflected:reflected
   oscillates around φ⁴ (±1 eigenvalues). Quote it as "→ φ⁴ in the limit," with
   the finite-level wobble shown honestly.

4. **Aperiodicity is cited, not reproved.** These files verify that the
   substitution produces valid, gap/overlap-free, all-congruent hat patches with
   the predicted statistics. They do **not** re-prove that the hat tiles *only*
   aperiodically — that is the paper's theorem (Smith–Myers–Kaplan–
   Goodman-Strauss, *Combinatorial Theory* 4(1), 2024). Any public page must
   attribute the aperiodicity result, not imply we derived it.

5. **One numerical subtlety, handled.** The frequency-vector convergence check
   needs `M^k` for large k; `int64` overflows at ~φ⁴³⁰ > 9.2×10¹⁸, which once
   produced a spurious negative "eigenvector." Fixed by using float64
   `matrix_power(M, 40)`. The exact integer relations are still checked
   separately with Python big-ints (`realized counts == Mᵏ e_seed`).

6. **shapely is optional.** verify.py's primary overlap/gap checks are exact
   integer (numpy + sympy only) and stand on their own; shapely is an
   *independent* cross-check that **skips gracefully** (prints `[INFO]`) if not
   installed. The advertised **headline count is the 27 core checks** (always
   run, dependency-light); shapely adds 6 more (= 33 total) and verify.py reports
   the split explicitly, so the number can never silently differ from the page.
   No headline result — including the 27-check count — depends on shapely.

7. **Out of scope (not built here): the spectre.** The strictly-chiral monotile
   (the "spectre", Tile(1,1) with curved edges, tiles with rotations+
   translations only — no reflections) is documented in the lab's research
   notes but is **not** implemented in this foundation.
   It is a clean candidate for a follow-up section/cycle; flagging it so nobody
   assumes the spectre is covered by these files.

8. **Nothing here is faked or weakened to go green.** Every check in verify.py
   runs for real and fails loud on regression (nonzero exit). If a future change
   breaks a relation, the gate will say so.

---
*Files: `hat.py` (geometry + 8-kite + self-test), `substitution.py` (H,T,P,F
substitution + patch generator), `verify.py` (the rigor gate, 27 core checks + 6 optional shapely),
`figures.py` → `img/` + `figures.log`, `core.js` (browser core), `test_core.mjs`
(core↔python, 105 checks). Facts compiled from the cited literature (see the
explorable's references). Ports: hatviz (Kaplan, BSD-3-Clause), matrix per
cp4space (Goucher).*
