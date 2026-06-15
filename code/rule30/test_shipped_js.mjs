/* ============================================================================
   test_shipped_js.mjs  —  the shipped-JS gate for Curiosity Lab #2 (Rule 30)

   This does NOT re-implement the engine. It reads the published page,
   EXTRACTS the exact ECA core JavaScript between the markers
       /*===ECA_CORE_START===* /  ...  /*===ECA_CORE_END===* /
   evaluates it, and runs the page's OWN functions against Python ground truth.

   Run:  node test_shipped_js.mjs
   Exits nonzero on any failure.
   ============================================================================ */
import fs from 'node:fs';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
// Resolve assets so this gate runs BOTH from the git repo (code/rule30 alongside
// ../../docs/rule30) AND from the lab workspace (/shared/...).
const firstExisting = (paths) => paths.find(p => fs.existsSync(p)) ?? paths[0];
const HTML_PATH = firstExisting([
  join(__dirname, '..', '..', 'docs', 'rule30', 'index.html'),  // git repo layout
  '/shared/public/curiosity-lab/rule30/index.html',            // lab workspace layout
]);
const ECA_DIR = dirname(firstExisting([
  join(__dirname, 'eca.py'),                                    // git repo: beside this script
  '/shared/projects/curiosity-lab/rule30/eca.py',              // lab workspace
]));

const html = fs.readFileSync(HTML_PATH, 'utf8');
const m = html.match(/\/\*===ECA_CORE_START===\*\/([\s\S]*?)\/\*===ECA_CORE_END===\*\//);
if (!m) { console.error('FAIL: could not find ECA core markers in', HTML_PATH); process.exit(1); }

// Evaluate the EXACT shipped core in an isolated function scope and hand back
// the functions it declares. No DOM is referenced by the core block.
const core = new Function(m[1] + '\nreturn {ruleBit, stepRow, evolve, rule30CenterLattice, rule30CenterBits};')();
const { ruleBit, stepRow, evolve, rule30CenterLattice, rule30CenterBits } = core;

let allPass = true;
const note = (ok, label, extra='') => {
  allPass = allPass && ok;
  console.log(`   [${ok ? 'PASS' : 'FAIL'}] ${label}${extra ? '  —  ' + extra : ''}`);
};
const hr = t => console.log('\n' + '='.repeat(68) + '\n' + t + '\n' + '='.repeat(68));

/* ---------------------------------------------------------------- CHECK A */
hr('A) The page\'s step() reproduces all 256 rules × 8 neighbourhoods');
{
  let bad = 0;
  for (let rule = 0; rule < 256; rule++)
    for (let code = 0; code < 8; code++) {
      const L = (code >> 2) & 1, C = (code >> 1) & 1, R = code & 1;     // code = 4L+2C+R
      const out = stepRow(Uint8Array.from([L, C, R]), rule)[1];         // centre cell sees [L,C,R]
      const want = (rule >> code) & 1;                                  // bit c of the rule
      if (out !== want) bad++;
      if (ruleBit(rule, code) !== want) bad++;                          // ruleBit consistency
    }
  note(bad === 0, 'engine self-test (2048 cases)', `mismatches = ${bad}`);
}

/* ---------------------------------------------------------------- CHECK B */
hr('B) Rule 90 single-seed grid == Pascal\'s triangle mod 2 (Lucas), T ≤ 128');
{
  const T = 128;
  const grid = evolve(90, T);                 // page function; width 2T+1, centred seed
  const c = (grid[0].length - 1) / 2;
  let lucasBad = 0, parityBad = 0, offBad = 0;

  // independent reference 1: Lucas submask  C(t,k) odd  <=>  (k & ~t)==0   (BigInt)
  // independent reference 2: exact BigInt binomial parity  (totally CA-free, Lucas-free)
  const combMod2 = (t, k) => {
    let num = 1n, den = 1n;
    for (let i = 0n; i < BigInt(k); i++) { num *= (BigInt(t) - i); den *= (i + 1n); }
    return Number((num / den) % 2n);
  };

  for (let t = 0; t <= T; t++) {
    for (let k = 0; k <= t; k++) {
      const x = c + (-t + 2 * k);                       // on-parity sublattice
      const lucas = ((BigInt(k) & ~BigInt(t)) === 0n) ? 1 : 0;
      if (grid[t][x] !== lucas) lucasBad++;
      if (lucas !== combMod2(t, k)) parityBad++;        // Lucas vs exact binomial parity
    }
    // off-parity cells inside the light cone must be 0
    for (let x = c - t; x <= c + t; x++)
      if (((x - (c - t)) & 1) === 1 && grid[t][x] !== 0) offBad++;
  }
  note(lucasBad === 0, 'shipped Rule 90 grid == Lucas submask', `rows 0..${T}, mismatches = ${lucasBad}`);
  note(parityBad === 0, 'Lucas == exact BigInt C(t,k) mod 2 (independent ref)', `mismatches = ${parityBad}`);
  note(offBad === 0, 'off-parity cells are 0 (single-seed Rule 90)', `violations = ${offBad}`);
}

/* ---------------------------------------------------------------- CHECK C */
hr('C) Rule 30 centre column from the page == Python eca.py (N=2000), density 0.4888');
{
  const N = 2000;
  const refStr = execSync(
    `python3 -c "import sys; sys.path.insert(0,'${ECA_DIR}'); import eca; print(','.join(map(str, eca.rule30_center(${N},'numpy').tolist())))"`,
    { encoding: 'utf8' }
  ).trim();
  const ref = refStr.split(',').map(Number);

  const jsLat  = Array.from(rule30CenterLattice(N));   // page engine (a)
  const jsBits = Array.from(rule30CenterBits(N));      // page engine (b)

  let latBad = 0, bitBad = 0, engBad = 0;
  const okLen = ref.length === N + 1 && jsLat.length === N + 1 && jsBits.length === N + 1;
  for (let i = 0; i <= N; i++) {
    if (jsLat[i]  !== ref[i]) latBad++;
    if (jsBits[i] !== ref[i]) bitBad++;
    if (jsLat[i]  !== jsBits[i]) engBad++;
  }
  const ones = jsBits.reduce((a, b) => a + b, 0);
  const dens = ones / (N + 1);
  const refOnes = ref.reduce((a, b) => a + b, 0);

  note(okLen, 'lengths are N+1 = 2001', `ref=${ref.length} lat=${jsLat.length} bits=${jsBits.length}`);
  note(latBad === 0, 'page lattice engine == Python reference', `mismatches = ${latBad}`);
  note(bitBad === 0, 'page bitboard engine == Python reference', `mismatches = ${bitBad}`);
  note(engBad === 0, 'the two page engines agree with each other (Claim B)', `mismatches = ${engBad}`);
  note(ones === refOnes && ones === 978, '#ones matches Python', `js=${ones} python=${refOnes}`);
  note(Math.round(dens * 1e4) / 1e4 === 0.4888, 'density rounds to 0.4888', `density = ${dens.toFixed(9)}`);
}

/* ---------------------------------------------------------------- CHECK D */
hr('D) The page\'s named Boolean nicknames actually equal their rules');
{
  // these strings are shown in the UI; assert each formula reproduces the rule table
  const f = {
    30:  (L,C,R) => L ^ (C | R),
    60:  (L,C,R) => L ^ C,
    90:  (L,C,R) => L ^ R,
    150: (L,C,R) => L ^ C ^ R,
  };
  let bad = 0;
  for (const r of Object.keys(f).map(Number))
    for (let code = 0; code < 8; code++) {
      const L = (code >> 2) & 1, C = (code >> 1) & 1, R = code & 1;
      if ((f[r](L, C, R) & 1) !== ((r >> code) & 1)) bad++;
    }
  note(bad === 0, 'nicknames {30:L⊕(C∨R),60:L⊕C,90:L⊕R,150:L⊕C⊕R} match', `mismatches = ${bad}`);
}

/* ---------------------------------------------------------------- SUMMARY */
hr('SUMMARY');
console.log(allPass ? '   ALL SHIPPED-JS CHECKS PASSED ✓' : '   FAILURES PRESENT ✗');
process.exit(allPass ? 0 : 1);
