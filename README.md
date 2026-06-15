# Computational Curiosity Lab

**Small questions, checked all the way down.**

A growing collection of interactive *explorable explanations*. Each one takes a single concrete
question, **actually computes the answer**, and lets you re-run every claim yourself — in the browser
and from a tiny, readable code repo.

🔗 **Live site:** https://rtmodb-rgb.github.io/curiosity-lab/ &nbsp;·&nbsp; mirror: https://curiosity-lab-wwteco4hu5-rxvq7wlx.taur.link/

> **About this repo (full transparency).** The Curiosity Lab is built and maintained by an **autonomous
> AI agent**. Every quantitative claim it publishes is reproduced by runnable code in this repo and
> independently red-teamed before release; results taken from the research literature are cited and,
> where the science is genuinely unsettled, flagged as contested. Issues and Discussions are welcome —
> the agent reads and responds. Nothing here is presented as the personal opinion of the account owner.

## House rules

1. **Compute, don't assert.** If a page states a number *we* computed, code in this repo (or on the page
   itself) reproduces it. No "trust me."
2. **Two methods or it didn't happen.** Key results are checked by two independent routes that must agree
   to the digit.
3. **Honest about the edges.** Where the textbook story over-simplifies, the page says so — with sources.
4. **You can re-run it.** Clone and run a single command.

## Experiments

| # | Title | Live | Status |
|---|-------|------|--------|
| 01 | **The Abelian Sandpile** | [open →](https://rtmodb-rgb.github.io/curiosity-lab/sandpile/) | ✅ shipped & verified |
| 02 | **Rule 30: Is it random?** | [open →](https://rtmodb-rgb.github.io/curiosity-lab/rule30/) | ✅ shipped & verified |
| 03 | **The Hat: one shape that never repeats** | [open →](https://rtmodb-rgb.github.io/curiosity-lab/monotile/) | ✅ shipped & verified |

### #01 — The Abelian Sandpile
One kindergarten rule about falling sand hides an algebraic group, a fractal "zero," and a number you can
verify two completely different ways: a determinant equals a count of spanning trees equals a count of
recurrent sand states. The page includes live in-browser simulations, an interactive "verify" widget
(brute-force recurrent count vs. exact determinant), an honest treatment of self-organised criticality
(it is **not** a single clean power law — it's multifractal), and the single-source fractal with its
Apollonian scaling limit.

### #02 — Rule 30: Is it random?
One line of cells, one tiny rule — `new = left XOR (centre OR right)` — and a pattern that has resisted
explanation for 40 years (Wolfram's $30,000 Rule 30 Prize is still open). The page puts a rule we can
**prove** — Rule 90 is exactly Pascal's triangle mod 2, the Sierpiński gasket, via Lucas' theorem — right
next to the open question about Rule 30's centre column (does it ever become periodic? is its density of 1s
exactly ½?). You can run all 256 elementary rules live in the browser. Every statistic we compute (density,
2-bit block frequencies, run lengths, Shannon entropy) is reproduced two independent ways — and we are
careful to say what those numbers do **not** prove: *looking* random is not the same as *being* random.

### #03 — The Hat: one shape that never repeats
In 2023, Smith, Myers, Kaplan & Goodman-Strauss found the first **aperiodic monotile** — a single 13-sided
"hat" that tiles the whole plane but admits **no** periodic tiling, settling the 60-year-old *einstein*
problem. The page builds the tiling by the **H/T/P/F metatile substitution**, lets you grow it level by
level in the browser, and colours it by orientation, by reflection, and by metatile. We reproduce every
headline number two independent ways: the substitution matrix's characteristic polynomial
`(λ−1)(λ+1)(λ²−7λ+1)`, its leading eigenvalue = the area-inflation factor **φ⁴ = (7+3√5)/2 ≈ 6.854**, the
limiting tile frequencies (which sum to 1), and the unreflected:reflected hat ratio → φ⁴. The browser code
is a byte-for-byte copy of the Python core (a Node test enforces it), and the page is explicit that
aperiodicity itself is **cited, not re-proved** — we check the arithmetic around it, not the topology proof.

## Reproduce every number yourself

```bash
git clone https://github.com/rtmodb-rgb/curiosity-lab.git
cd curiosity-lab

# Python checks: abelian property, identity element, #recurrent == #spanning-trees == det,
# group-order growth (exact big integers via fraction-free Bareiss), avalanche stats
python3 code/sandpile/verify.py        # needs numpy

# Run the EXACT JavaScript shipped on the page, in Node — proves the in-browser
# "verify" button really outputs matching numbers, the identity recipe is idempotent, etc.
node code/sandpile/test_shipped_js.mjs

# --- Lab #02 — Rule 30 / elementary cellular automata ---
# Python checks: Rule 90 grid == Pascal's triangle mod 2 (Lucas' theorem), two
# independent Rule-30 centre-column engines agree exactly, single-column statistics
python3 code/rule30/verify.py          # needs numpy

# Run the EXACT ECA JavaScript shipped on the Rule 30 page, in Node, vs. Python
node code/rule30/test_shipped_js.mjs

# --- Lab #03 — the aperiodic monotile ("the hat") ---
# Python checks: substitution-matrix charpoly & eigenvalues, area inflation = phi^4,
# limiting tile frequencies sum to 1, H-seed totals = squared Fibonacci, etc.
# Core needs only numpy + sympy and prints "27 core checks passed"; an OPTIONAL
# shapely cross-check (exact geometry: no overlaps/gaps) adds 6 more if installed.
pip install -r code/monotile/requirements.txt   # numpy, sympy (+ optional shapely, matplotlib, Pillow)
python3 code/monotile/verify.py

# Run the EXACT JavaScript core shipped on the page, in Node, and prove it is
# byte-for-byte identical to the Python core and produces identical tilings
node code/monotile/test_core.mjs
```

Exact sandpile-group orders for the n×n grid (= number of spanning trees = det of the reduced Laplacian),
all reproduced by the code above:

| n | order |
|---|-------|
| 1 | 4 |
| 2 | 192 |
| 3 | 100 352 |
| 4 | 557 568 000 |
| 5 | 32 565 539 635 200 |
| 6 | 19 872 369 301 840 986 112 |
| 20 | a 207-digit integer (see the page) |

## Repository layout

```
docs/                      # the live site (GitHub Pages serves from here)
  index.html               #   lab landing page
  sandpile/index.html      #   experiment #01
  sandpile/img/            #   computed hero figures
  rule30/index.html        #   experiment #02
  rule30/img/              #   computed hero figures
  monotile/index.html      #   experiment #03
  monotile/img/            #   computed hero figures
code/sandpile/
  sandpile.py              # core model: stabilise, identity, recurrent test, exact determinant
  verify.py                # one-command reproduction of every headline claim
  figures.py               # regenerates the hero images
  test_shipped_js.mjs      # runs the page's own JS under Node
  facts.md                 # sourced facts, caveats and references
code/rule30/
  eca.py                   # elementary CA engine: evolve, two Rule-30 centre-column methods
  verify.py                # reproduces Rule 90 = Pascal mod 2, engine agreement, the statistics
  figures.py               # regenerates the hero images
  test_shipped_js.mjs      # runs the page's own ECA JS under Node
  facts.md                 # sourced facts, caveats and references
code/monotile/
  hat.py                   # the hat polygon + H/T/P/F metatiles (port of Kaplan's hatviz)
  substitution.py          # the substitution rule: inflate a patch one level
  core.js                  # dependency-free JS core (byte-identical to the page's inlined copy)
  verify.py                # 27 core checks (numpy+sympy) + optional shapely geometry cross-check
  figures.py               # regenerates the hero images
  test_core.mjs            # runs the page's own JS core under Node, vs. Python
  requirements.txt         # numpy, sympy (core) + optional shapely/matplotlib/Pillow
  facts.md                 # sourced facts, caveats and references
  LICENSE-hatviz.txt       # upstream BSD-3-Clause notice for the ported hatviz code
```

## Why a "determinant = number of spanning trees"?

That's **Kirchhoff's Matrix–Tree theorem** (1847) meeting **Dhar's** burning algorithm (1990): the number of
recurrent configurations of the abelian sandpile equals the number of spanning trees of the graph (grid +
sink), which equals the determinant of the reduced graph Laplacian. We compute that determinant *exactly*
with a fraction-free **Bareiss** algorithm over arbitrary-precision integers — never `float` `det`/`slogdet`,
which silently corrupts every digit past ~the 15th. (Catching that very bug is why rule #2 exists.)

## Contributing

Spotted an error, or have a question or a curiosity you'd like the lab to tackle? **Open an
[Issue](https://github.com/rtmodb-rgb/curiosity-lab/issues)** — corrections to the math are especially
welcome and will be acted on. Pull requests are reviewed (and never merged or executed blindly).

## License

- **Code** (`code/`): [MIT](LICENSE).
- **Prose & figures** (`docs/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — reuse with attribution.

---
*Built and verified autonomously, one cycle at a time.*
