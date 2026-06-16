/*
 * core.js  --  the in-browser Langton's-ant engine, dependency-free JavaScript.
 *
 * Computational Curiosity Lab #6 (Langton's ant).  A faithful port of langton.py:
 * the two-colour ant on a sparse grid, its exact inverse (the global update is a
 * bijection), all-white trajectories / deterministic signatures, the highway
 * analyser (minimal period, net drift, black-cells-per-period, onset under a
 * precise detector), and the multi-colour "turmite" generalisation with the
 * bilateral-symmetry predicate for the proven LL/RR-pair family (Gale et al. 1995).
 *
 * CONVENTION (fixed once; stated on the page):
 *   white(0) -> turn 90 deg RIGHT (clockwise on a y-DOWN screen), flip to black, step;
 *   black(1) -> turn 90 deg LEFT  (counter-clockwise),            flip to white, step.
 *   x is east, y is DOWN (the <canvas> convention); the ant starts at (0,0) facing UP
 *   on an all-white grid.  Headings 0..3 = [Up,Right,Down,Left] (visual clockwise), so
 *   "turn right" = +1 (mod 4), "turn left" = -1.  Only the SIGN of the drift direction
 *   depends on this convention; the invariants (period 104, |drift| = 2*sqrt(2),
 *   +12 black cells / period, reversibility) do not.
 *
 * EXACTNESS: counts and coordinates are small integers; the deterministic signature
 * hash is taken mod a 31-bit prime with every intermediate product < 2^53, so a
 * JavaScript Number reproduces langton.py's Python-int hash bit-for-bit.  test_core.mjs
 * cross-checks ALL of this against langton.py and guards that the page inlines this
 * region byte-for-byte.
 *
 * The region between the LANGTON_CORE markers is self-contained (no import / export /
 * require) so a web page can inline it verbatim into a <script>.
 */

/* === LANGTON_CORE START === */
"use strict";

// Headings: 0=Up 1=Right 2=Down 3=Left  (visual clockwise on a y-DOWN screen).
const UP = 0, RIGHT = 1, DOWN = 2, LEFT = 3;
const DX = [0, 1, 0, -1];     // +x is east  (RIGHT)
const DY = [-1, 0, 1, 0];     // +y is south (DOWN);  UP decreases y

// A 31-bit prime: polynomial-hash modulus.  Every intermediate product below stays
// well under 2^53, so a JS Number reproduces langton.py's hash exactly.
const SIG_MOD = 2147483647;

// ---- the two-colour ant  (sparse Map grid: only touched cells are stored) -----
class Ant {
  constructor() {
    this.grid = new Map();   // "x,y" -> 0|1   (key absent = white)
    this.x = 0;
    this.y = 0;
    this.dir = UP;
    this.stepCount = 0;
    this.black = 0;          // number of cells currently coloured black (=1)
  }

  color(x, y) {
    const v = this.grid.get(x + "," + y);
    return v === undefined ? 0 : v;
  }

  // Set a cell's colour (0/1) while keeping the black-cell count correct.  Used to
  // seed a finite configuration before running (the all-white run never needs it).
  setCell(x, y, c) {
    const key = x + "," + y;
    const cur = this.grid.get(key);
    const old = cur === undefined ? 0 : cur;
    if (old === c) return;
    this.grid.set(key, c);
    this.black += c === 1 ? 1 : -1;
  }

  // Advance one step.  Returns the colour the current cell is flipped TO.
  step() {
    const key = this.x + "," + this.y;
    const c = this.grid.get(key);
    let flippedTo;
    if (c === undefined || c === 0) {   // white -> turn RIGHT, flip to black
      this.dir = (this.dir + 1) & 3;
      this.grid.set(key, 1);
      this.black += 1;
      flippedTo = 1;
    } else {                            // black -> turn LEFT, flip to white
      this.dir = (this.dir + 3) & 3;
      this.grid.set(key, 0);
      this.black -= 1;
      flippedTo = 0;
    }
    this.x += DX[this.dir];
    this.y += DY[this.dir];
    this.stepCount += 1;
    return flippedTo;
  }

  // Undo exactly one forward step (the global update is a bijection).
  invStep() {
    const px = this.x - DX[this.dir];   // move back onto the previously-flipped cell
    const py = this.y - DY[this.dir];
    const raw = this.grid.get(px + "," + py);
    const cNow = raw === undefined ? 0 : raw;
    const cPre = 1 - cNow;              // that cell was flipped during the forward step
    this.grid.set(px + "," + py, cPre);
    this.black += cPre === 1 ? 1 : -1;
    // recover the previous heading from the cell's restored (pre-step) colour
    if (cPre === 0) {                   // had been white -> we turned right (+1); undo -1
      this.dir = (this.dir + 3) & 3;
    } else {                            // had been black -> we turned left (-1); undo +1
      this.dir = (this.dir + 1) & 3;
    }
    this.x = px;
    this.y = py;
    this.stepCount -= 1;
  }

  // Array of [x, y] for every currently-black cell.
  blackCells() {
    const out = [];
    for (const [k, v] of this.grid) {
      if (v === 1) {
        const i = k.indexOf(",");
        out.push([Number(k.slice(0, i)), Number(k.slice(i + 1))]);
      }
    }
    return out;
  }
}

function runFromAllWhite(n) {
  const a = new Ant();
  for (let i = 0; i < n; i++) a.step();
  return a;
}

// Record the all-white run.  pos[i]=[x,y], head[i]=dir, black[i]=#black after i steps.
function trajectory(n) {
  const a = new Ant();
  const pos = [[a.x, a.y]];
  const head = [a.dir];
  const black = [a.black];
  for (let i = 0; i < n; i++) {
    a.step();
    pos.push([a.x, a.y]);
    head.push(a.dir);
    black.push(a.black);
  }
  return { pos, head, black };
}

// Deterministic fingerprint of the all-white run after n steps:
// [x, y, dir, blackCount, hash], hash = polynomial over the lexicographically-sorted
// black cells mod SIG_MOD (every product < 2^53, so it matches langton.py exactly).
function stateSignature(n) {
  const a = runFromAllWhite(n);
  const blacks = a.blackCells();
  blacks.sort((p, q) => p[0] - q[0] || p[1] - q[1]);
  let h = 0;
  for (const cell of blacks) {
    h = (h * 1000003 + (cell[0] + 1000000) * 2000003 + (cell[1] + 1000000)) % SIG_MOD;
  }
  return [a.x, a.y, a.dir, a.black, h];
}

// Rolling hash of the ENTIRE all-white path (x, y, dir at every state 0..n).  A single
// number that differs if any step of the trajectory differs; matches langton.py.
function pathSignature(n) {
  const a = new Ant();
  let h = (a.x + 1000000) * 2000003 + (a.y + 1000000) * 9 + a.dir;
  h %= SIG_MOD;
  for (let i = 0; i < n; i++) {
    a.step();
    h = (h * 1000003 + (a.x + 1000000) * 2000003 + (a.y + 1000000) * 9 + a.dir) % SIG_MOD;
  }
  return h;
}

// ---- highway analysis: minimal period, drift, cells/period, onset -------------
// True (returns [dx,dy]) iff over s in [lo,hi) the P-step displacement is constant
// AND the heading repeats; null otherwise.
function periodHolds(pos, head, P, lo, hi) {
  const d0x = pos[lo + P][0] - pos[lo][0];
  const d0y = pos[lo + P][1] - pos[lo][1];
  for (let s = lo; s < hi; s++) {
    if (head[s + P] !== head[s]) return null;
    if (pos[s + P][0] - pos[s][0] !== d0x || pos[s + P][1] - pos[s][1] !== d0y) return null;
  }
  return [d0x, d0y];
}

// Smallest P (1..periodCap) whose displacement signature is exactly periodic over the
// last `window` steps.  Multiples of the true period also pass, so the smallest is the
// fundamental period (104 for Langton).
function minimalPeriod(pos, head, maxSteps, periodCap, window) {
  periodCap = periodCap || 200;
  window = window || 1000;
  const lo = maxSteps - window - periodCap;
  for (let P = 1; P <= periodCap; P++) {
    if (periodHolds(pos, head, P, lo, lo + window)) return P;
  }
  return null;
}

// First step from which the P-step signature (displacement === [driftX,driftY] and
// heading repeats) holds for ALL later s up to the horizon.  = (last failing step)+1.
function onsetStep(pos, head, P, driftX, driftY, maxSteps) {
  let onset = 0;
  for (let s = 0; s <= maxSteps - P; s++) {
    if (head[s + P] !== head[s] ||
        pos[s + P][0] - pos[s][0] !== driftX ||
        pos[s + P][1] - pos[s][1] !== driftY) {
      onset = s + 1;
    }
  }
  return onset;
}

// Run from all-white; return {period, dx, dy, drift_mag2, cells_per_period, onset_step}.
// Drift is measured at the very end of the run (deep in the highway).
function detectHighway(maxSteps, periodCap, window) {
  maxSteps = maxSteps || 20000;
  periodCap = periodCap || 200;
  window = window || 1000;
  const tr = trajectory(maxSteps);
  const pos = tr.pos, head = tr.head, black = tr.black;
  const P = minimalPeriod(pos, head, maxSteps, periodCap, window);
  if (P === null) throw new Error("no period <= " + periodCap + " found within " + maxSteps + " steps");
  const dx = pos[maxSteps][0] - pos[maxSteps - P][0];
  const dy = pos[maxSteps][1] - pos[maxSteps - P][1];
  const cells = black[maxSteps] - black[maxSteps - P];
  const onset = onsetStep(pos, head, P, dx, dy, maxSteps);
  return { period: P, dx: dx, dy: dy, drift_mag2: dx * dx + dy * dy, cells_per_period: cells, onset_step: onset };
}

// ---- multi-colour turmites  ("RL" == Langton's ant) ---------------------------
// Apply one turn letter to a heading index.  'R' = right (+1), 'L' = left (-1).
function turn(dir, ch) {
  return ch === "R" ? (dir + 1) & 3 : (dir + 3) & 3;
}

class Turmite {
  // rule[c] in {'L','R'} is the turn on a cell of colour c; colours cycle
  // 0->1->...->(n-1)->0 as the ant leaves.  'RL' is Langton's ant here.
  constructor(rule) {
    rule = String(rule).toUpperCase();
    if (rule.length === 0 || /[^LR]/.test(rule)) {
      throw new Error("rule must be a non-empty string of 'L'/'R'");
    }
    this.rule = rule;
    this.n = rule.length;
    this.grid = new Map();
    this.x = 0;
    this.y = 0;
    this.dir = UP;
    this.stepCount = 0;
  }

  step() {
    const key = this.x + "," + this.y;
    const raw = this.grid.get(key);
    const c = raw === undefined ? 0 : raw;
    this.dir = turn(this.dir, this.rule[c]);
    const nc = (c + 1) % this.n;
    this.grid.set(key, nc);
    this.x += DX[this.dir];
    this.y += DY[this.dir];
    this.stepCount += 1;
    return nc;
  }

  // Map "x,y" -> colour for every non-zero (non-white) cell.
  colorField() {
    const m = new Map();
    for (const [k, v] of this.grid) if (v !== 0) m.set(k, v);
    return m;
  }
}

function runTurmite(rule, n) {
  const t = new Turmite(rule);
  for (let i = 0; i < n; i++) t.step();
  return t;
}

// ---- bilateral-symmetry predicate (proven LL/RR-pair family, Gale et al. 1995) -
// colorField: Map "x,y" -> colour (non-white cells).  Search a single mirror axis
// (vertical / horizontal / either diagonal) that maps the field onto itself, colours
// included.  Any reflection symmetry of a finite set must fix its bounding box, so
// the one box-bisecting axis per orientation is the only candidate -> COMPLETE.
// Returns a short axis tag, else null.
function reflectionSymmetry(colorField) {
  if (!colorField || colorField.size === 0) return null;
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  const pts = [];
  for (const [k, col] of colorField) {
    const i = k.indexOf(",");
    const x = Number(k.slice(0, i)), y = Number(k.slice(i + 1));
    pts.push([x, y, col]);
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
  }
  function symmetric(map) {
    for (let i = 0; i < pts.length; i++) {
      const m = map(pts[i][0], pts[i][1]);
      if (colorField.get(m[0] + "," + m[1]) !== pts[i][2]) return false;
    }
    return true;
  }
  function half(twice) { return twice % 2 === 0 ? String(twice / 2) : (twice / 2).toString(); }

  const a = minX + maxX;               // vertical mirror x = a/2
  if (symmetric(function (x, y) { return [a - x, y]; })) return "vertical x=" + half(a);
  const b = minY + maxY;               // horizontal mirror y = b/2
  if (symmetric(function (x, y) { return [x, b - y]; })) return "horizontal y=" + half(b);
  const diffs = [];                    // diagonal slope +1: (x,y) -> (y+k, x-k)
  const xb = [minX, maxX], yb = [minY, maxY];
  for (let p = 0; p < 2; p++) for (let q = 0; q < 2; q++) diffs.push(xb[p] - yb[q]);
  const kk = Math.min.apply(null, diffs) + Math.max.apply(null, diffs);
  if (kk % 2 === 0) {
    const k = kk / 2;
    if (symmetric(function (x, y) { return [y + k, x - k]; })) return "diagonal x-y=" + k;
  }
  const sums = [];                     // anti-diagonal slope -1: (x,y) -> (m-y, m-x)
  for (let p = 0; p < 2; p++) for (let q = 0; q < 2; q++) sums.push(xb[p] + yb[q]);
  const mm = Math.min.apply(null, sums) + Math.max.apply(null, sums);
  if (mm % 2 === 0) {
    const m = mm / 2;
    if (symmetric(function (x, y) { return [m - y, m - x]; })) return "antidiagonal x+y=" + m;
  }
  return null;
}

// First step (1..maxSteps) at which `rule`'s field has >= minCells coloured cells AND
// admits a reflection symmetry.  Returns [step, axis] or null.  The >= minCells floor
// skips the trivially-symmetric first few steps; for the proven LL/RR-pair family such
// steps recur infinitely often (we only need to exhibit one after real growth).
function firstSymmetricStep(rule, maxSteps, minCells) {
  if (minCells === undefined) minCells = 8;
  const t = new Turmite(rule);
  for (let s = 1; s <= maxSteps; s++) {
    t.step();
    const cf = t.colorField();
    if (cf.size >= minCells) {
      const axis = reflectionSymmetry(cf);
      if (axis !== null) return [s, axis];
    }
  }
  return null;
}
/* === LANGTON_CORE END === */

export {
  UP, RIGHT, DOWN, LEFT, DX, DY, SIG_MOD,
  Ant, runFromAllWhite, trajectory, stateSignature, pathSignature,
  periodHolds, minimalPeriod, onsetStep, detectHighway,
  turn, Turmite, runTurmite, reflectionSymmetry, firstSymmetricStep,
};
