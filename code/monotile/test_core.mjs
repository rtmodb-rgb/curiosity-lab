/*
 * test_core.mjs  --  Node test (no external deps): does core.js reproduce
 * substitution.py EXACTLY?  For every seed in {H,T,P,F} and level 1..5
 * (k = 0..4) we compare: total hat count, counts by metatile type, counts by
 * label (= reflected vs unreflected), and the full multiset of hat centroids
 * to 6 decimals (coordinates agree -- both run in the same global-scale-2
 * frame).  We also confirm the region between the HAT_CORE markers is
 * self-contained (no import/export/require) and works when inlined alone.
 *
 * Run:  node test_core.mjs        (exits nonzero on any failure)
 * Paths resolve via import.meta.url with a /shared/... fallback, so this runs
 * from a fresh clone or from the shared volume.
 */
import { execFileSync } from 'node:child_process';
import { readFileSync, existsSync, writeFileSync, mkdtempSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(fileURLToPath(import.meta.url));

function resolveDir() {
  const cands = [HERE, '/shared/projects/curiosity-lab/monotile'];
  for (const c of cands) {
    if (existsSync(path.join(c, 'core.js')) && existsSync(path.join(c, 'substitution.py'))) {
      return c;
    }
  }
  throw new Error('could not locate core.js + substitution.py (looked in: ' + cands.join(', ') + ')');
}
const DIR = resolveDir();

let failures = 0, passes = 0;
function check(name, cond, detail = '') {
  if (cond) { passes++; console.log(`[PASS] ${name}` + (detail ? `   ${detail}` : '')); }
  else { failures++; console.log(`[FAIL] ${name}` + (detail ? `   ${detail}` : '')); }
}

// ---- JS-side fingerprint (mirrors the Python ref dump exactly) ----
const fmt = (x) => { const s = (x + 0).toFixed(6); return s === '-0.000000' ? '0.000000' : s; };
function centroid(v) {
  let cx = 0, cy = 0;
  for (const p of v) { cx += p[0]; cy += p[1]; }
  cx /= v.length; cy /= v.length;
  return fmt(cx) + ',' + fmt(cy);
}
function fingerprint(core, seed, level) {
  const hats = core.patch(level, seed);
  const byType = { H: 0, T: 0, P: 0, F: 0 };
  const byLabel = { H: 0, H1: 0, T: 0, P: 0, F: 0 };
  let reflected = 0;
  const centroids = [];
  for (const h of hats) {
    byType[h.mtype]++; byLabel[h.label]++;
    if (h.reflected) reflected++;
    centroids.push(centroid(h.vertices));
  }
  centroids.sort();
  return { n: hats.length, byType, byLabel, reflected, centroids };
}

// ---- Python reference dump ----
const PY = [
  'import json, sys',
  'from collections import Counter',
  'sys.path.insert(0, sys.argv[1])',
  'import substitution as S',
  'def fmt(x):',
  '    s = "%.6f" % (x + 0.0)',
  '    return "0.000000" if s == "-0.000000" else s',
  'def centroid(v):',
  '    cx = sum(p[0] for p in v) / len(v)',
  '    cy = sum(p[1] for p in v) / len(v)',
  '    return fmt(cx) + "," + fmt(cy)',
  'out = {}',
  'for seed in S.ORDER:',
  '    for level in range(1, 6):',
  '        hats = S.patch(level, seed)',
  '        bl = Counter(h["label"] for h in hats)',
  '        bt = Counter(h["mtype"] for h in hats)',
  '        out[seed + str(level)] = {',
  '            "n": len(hats),',
  '            "byType": {k: bt.get(k, 0) for k in S.ORDER},',
  '            "byLabel": {k: bl.get(k, 0) for k in ["H","H1","T","P","F"]},',
  '            "reflected": sum(1 for h in hats if h["reflected"]),',
  '            "centroids": sorted(centroid(h["vertices"]) for h in hats),',
  '        }',
  'print(json.dumps(out))',
].join('\n');

function pythonRef() {
  const buf = execFileSync('python3', ['-c', PY, DIR],
                           { cwd: DIR, maxBuffer: 256 * 1024 * 1024 });
  return JSON.parse(buf.toString());
}

function arraysEqual(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

// ======================================================================
(async function main() {
  console.log('core.js  vs  substitution.py   (dir: ' + DIR + ')\n');

  const corePath = path.join(DIR, 'core.js');
  const core = await import(pathToFileURL(corePath).href);
  const ref = pythonRef();

  const SEEDS = ['H', 'T', 'P', 'F'];
  const PHI4 = (7 + 3 * Math.sqrt(5)) / 2;

  for (const seed of SEEDS) {
    for (let level = 1; level <= 5; level++) {
      const key = seed + level;
      const R = ref[key];
      const J = fingerprint(core, seed, level);
      const tag = `seed ${seed}, level ${level}`;

      check(`${tag}: total hat count`, J.n === R.n, `js=${J.n} py=${R.n}`);
      const typeOk = ['H', 'T', 'P', 'F'].every((k) => J.byType[k] === R.byType[k]);
      check(`${tag}: counts by metatile type`, typeOk,
            `js=${JSON.stringify(J.byType)} py=${JSON.stringify(R.byType)}`);
      const labelOk = ['H', 'H1', 'T', 'P', 'F'].every((k) => J.byLabel[k] === R.byLabel[k]);
      check(`${tag}: counts by label (refl vs unrefl)`, labelOk,
            `js=${JSON.stringify(J.byLabel)} py=${JSON.stringify(R.byLabel)}`);
      check(`${tag}: reflected count`, J.reflected === R.reflected,
            `js=${J.reflected} py=${R.reflected}`);
      check(`${tag}: hat centroids match to 6 dp (coords agree)`,
            arraysEqual(J.centroids, R.centroids),
            `${J.centroids.length} centroids`);
    }
  }

  // reflected:unreflected ratio trends to phi^4 (info + sanity on the H seed)
  const f5 = fingerprint(core, 'H', 5);
  const ratio = (f5.n - f5.reflected) / f5.reflected;
  check('H seed level 5: unrefl:refl ratio near phi^4 (oscillating)',
        Math.abs(ratio - PHI4) < 0.05,
        `ratio=${ratio.toFixed(5)}  phi^4=${PHI4.toFixed(5)}`);

  // total-count sequence from H seed is the bisected-Fibonacci squares
  const totals = [1, 2, 3, 4, 5].map((L) => fingerprint(core, 'H', L).n);
  check('H seed totals = 4,25,169,1156,7921 (= 2^2,5^2,13^2,34^2,89^2)',
        arraysEqual(totals, [4, 25, 169, 1156, 7921]), `totals=${JSON.stringify(totals)}`);

  // ---- marker region is self-contained and works when inlined alone ----
  const text = readFileSync(corePath, 'utf8');
  const m = text.match(/\/\*===HAT_CORE_START===\*\/([\s\S]*?)\/\*===HAT_CORE_END===\*\//);
  check('HAT_CORE markers present (start + end)', !!m);
  if (m) {
    const region = m[1];
    const clean = !/\b(import|export|require)\b/.test(region);
    check('marked core region has no import/export/require', clean);
    // run the extracted region ALONE (add a minimal export shim) and re-check
    const tmp = path.join(mkdtempSync(path.join(tmpdir(), 'hatcore-')), 'inlined.mjs');
    writeFileSync(tmp, region + '\nexport { patch as P };\n');
    const inlined = await import(pathToFileURL(tmp).href);
    const a = inlined.P(4, 'H').length, b = core.patch(4, 'H').length;
    check('extracted core region runs standalone & matches', a === b, `inlined=${a} core=${b}`);
  }

  console.log(`\nRESULT: ${passes} passed, ${failures} failed.`);
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error('ERROR:', e); process.exit(2); });
