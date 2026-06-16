/*
 * test_core.mjs  --  Node test (no external deps): does core.js reproduce
 * langton.py EXACTLY, across the language boundary?  We cross-check:
 *   - the highway descriptors {period, drift, drift_mag2, cells/period, onset}
 *     (detectHighway) === Python === the pinned invariants (104, 8, 12, ~9977);
 *   - the ENTIRE all-white path: (x,y,dir) for steps 0..2000 elementwise JS ===
 *     Python, AND a rolling hash of all 12,000 states JS === Python;
 *   - deterministic black-set signatures at n = 100,1000,5000,9977,12000
 *     (JS Number hash === Python int hash, bit-for-bit);
 *   - reversibility: forward 5000 then inverse 5000 returns to the all-white origin
 *     (JS === Python), the seeded round-trip restores the seed, and step then
 *     invStep is the identity at every state along the first 2000 steps;
 *   - bookkeeping invariants (one cell flips / heading parity flips / black +-1);
 *   - turmites: 'RL' reproduces Langton's ant for 12,000 steps (JS === Python),
 *     its eventual period is also 104, and the proven LL/RR-pair strings
 *     ('LLRR','RLLR','LRRL') return to a symmetric field at the same step + axis;
 *   - the region between the LANGTON_CORE markers is self-contained (no
 *     import/export/require), runs when inlined alone, AND -- if index.html
 *     exists -- appears in it BYTE-FOR-BYTE (the page never drifts from core.js).
 *
 * Run:  node test_core.mjs        (exits nonzero on any failure)
 * Paths resolve via import.meta.url (the script's own directory).
 */
import { execFileSync } from "node:child_process";
import { readFileSync, existsSync, writeFileSync, mkdtempSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { tmpdir } from "node:os";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
function resolveDir() {
  const cands = [HERE];
  for (const c of cands) {
    if (existsSync(path.join(c, "core.js")) && existsSync(path.join(c, "langton.py"))) return c;
  }
  throw new Error("could not locate core.js + langton.py (looked in: " + cands.join(", ") + ")");
}
const DIR = resolveDir();

let passes = 0, failures = 0;
function check(name, cond, detail = "") {
  if (cond) { passes++; console.log(`[PASS] ${name}` + (detail ? `   ${detail}` : "")); }
  else { failures++; console.log(`[FAIL] ${name}` + (detail ? `   ${detail}` : "")); }
}

// ---- Python reference dump (imports langton.py from DIR) -------------------
const PY = [
  "import json, sys",
  "sys.path.insert(0, sys.argv[1])",
  "import langton as L",
  "MOD = L.SIG_MOD",
  "hw = L.detect_highway()",
  "pos, head, black = L.trajectory(12000)",
  "path2000 = ';'.join('%d,%d,%d' % (pos[i][0], pos[i][1], head[i]) for i in range(2001))",
  "h = ((pos[0][0]+1000000)*2000003 + (pos[0][1]+1000000)*9 + head[0]) % MOD",
  "for i in range(1, 12001):",
  "    x, y = pos[i]; d = head[i]",
  "    h = (h*1000003 + (x+1000000)*2000003 + (y+1000000)*9 + d) % MOD",
  "sigs = {str(n): list(L.state_signature(n)) for n in (100,1000,5000,9977,12000)}",
  "a = L.Ant()",
  "for _ in range(5000): a.step()",
  "for _ in range(5000): a.inv_step()",
  "rev = [a.x, a.y, a.dir, a.black, len(a.black_cells())]",
  "tA = L.Ant(); tT = L.Turmite('RL'); rl = True",
  "for _ in range(12000):",
  "    fa = tA.step(); ct = tT.step()",
  "    if (tA.x,tA.y,tA.dir,fa) != (tT.x,tT.y,tT.dir,ct): rl = False; break",
  "tt = L.Turmite('RL'); tp=[(tt.x,tt.y)]; th=[tt.dir]",
  "for _ in range(20000): tt.step(); tp.append((tt.x,tt.y)); th.append(tt.dir)",
  "rlper = L.minimal_period(tp, th, 20000, 200, 1000)",
  "sym = {r: list(L.first_symmetric_step(r, 2000)) for r in ('LLRR','RLLR','LRRL')}",
  "out = {",
  "  'hw': hw, 'path2000': path2000, 'psig12000': h, 'sigs': sigs,",
  "  'rev': rev, 'rl': rl, 'rlper': rlper, 'sym': sym,",
  "}",
  "print(json.dumps(out))",
].join("\n");

function pythonRef() {
  const buf = execFileSync("python3", ["-c", PY, DIR], { cwd: DIR, maxBuffer: 64 * 1024 * 1024 });
  return JSON.parse(buf.toString());
}

(async function main() {
  console.log("core.js  vs  langton.py   (dir: " + DIR + ")\n");
  const corePath = path.join(DIR, "core.js");
  const C = await import(pathToFileURL(corePath).href);
  const ref = pythonRef();

  // ---- highway descriptors ---------------------------------------------------
  const hw = C.detectHighway();
  check("detectHighway() {period,dx,dy,mag2,cells,onset} JS === Python",
        JSON.stringify(hw) === JSON.stringify(ref.hw),
        `JS ${JSON.stringify(hw)}`);
  check("highway invariants: period 104, |drift|^2 = 8, +12 cells/period, onset in 9000..11000",
        hw.period === 104 && hw.drift_mag2 === 8 && hw.cells_per_period === 12 &&
        hw.onset_step >= 9000 && hw.onset_step <= 11000,
        `onset = ${hw.onset_step}`);

  // ---- the whole all-white path ---------------------------------------------
  const tr = C.trajectory(2000);
  const js2000 = [];
  for (let i = 0; i <= 2000; i++) js2000.push(tr.pos[i][0] + "," + tr.pos[i][1] + "," + tr.head[i]);
  check("all-white path (x,y,dir) for steps 0..2000 elementwise JS === Python",
        js2000.join(";") === ref.path2000);
  check("rolling hash of all 12,000 path states JS === Python (whole path identical)",
        C.pathSignature(12000) === ref.psig12000,
        `hash = ${C.pathSignature(12000)}`);

  // ---- deterministic black-set signatures -----------------------------------
  let sigOk = true, sigDetail = "";
  for (const n of [100, 1000, 5000, 9977, 12000]) {
    const js = C.stateSignature(n);
    const py = ref.sigs[String(n)];
    if (JSON.stringify(js) !== JSON.stringify(py)) { sigOk = false; sigDetail = `n=${n}: ${JSON.stringify(js)} != ${JSON.stringify(py)}`; }
  }
  check("black-set signatures at n=100,1000,5000,9977,12000 JS === Python (hash bit-for-bit)",
        sigOk, sigOk ? `sig@12000 = ${JSON.stringify(C.stateSignature(12000))}` : sigDetail);

  // ---- reversibility ---------------------------------------------------------
  const a = new C.Ant();
  for (let i = 0; i < 5000; i++) a.step();
  for (let i = 0; i < 5000; i++) a.invStep();
  const rev = [a.x, a.y, a.dir, a.black, a.blackCells().length];
  check("forward 5000 then inverse 5000 returns to the all-white origin (JS === Python)",
        rev.join() === "0,0,0,0,0" && rev.join() === ref.rev.join(),
        `JS final state [x,y,dir,black,#cells] = [${rev.join(",")}]`);

  // seeded round-trip: a finite blob is restored exactly by forward-then-inverse
  const seed = [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1], [2, 3], [-3, -2], [4, -1]];
  const sd = new C.Ant();
  for (const [x, y] of seed) sd.setCell(x, y, 1);
  const before = sd.blackCells().map((c) => c.join(",")).sort().join("|");
  const bx = sd.x, by = sd.y, bdir = sd.dir, bblack = sd.black;
  for (let i = 0; i < 3000; i++) sd.step();
  for (let i = 0; i < 3000; i++) sd.invStep();
  const after = sd.blackCells().map((c) => c.join(",")).sort().join("|");
  check("seeded round-trip: forward 3000 then inverse 3000 restores the exact seed",
        after === before && sd.x === bx && sd.y === by && sd.dir === bdir && sd.black === bblack);

  // step then invStep is the identity at every state along the first 2000 steps
  const rt = new C.Ant();
  let idOk = true;
  for (let s = 0; s < 2000; s++) {
    const snap = rt.x + "|" + rt.y + "|" + rt.dir + "|" + rt.black + "|" +
      rt.blackCells().map((c) => c.join(",")).sort().join(";");
    rt.step(); rt.invStep();
    const now = rt.x + "|" + rt.y + "|" + rt.dir + "|" + rt.black + "|" +
      rt.blackCells().map((c) => c.join(",")).sort().join(";");
    if (now !== snap) { idOk = false; break; }
    rt.step();   // advance one for the next sample
  }
  check("step then invStep is the identity at every state along the first 2000 steps", idOk);

  // ---- bookkeeping invariants ------------------------------------------------
  const bk = new C.Ant();
  let flips = true, parity = true, delta = true;
  let prevBlack = bk.black, prevParity = bk.dir & 1;
  for (let s = 0; s < 4000; s++) {
    const px = bk.x, py = bk.y;
    const before2 = bk.color(px, py);
    bk.step();
    if (bk.color(px, py) === before2) flips = false;           // the stood-on cell changed
    if ((bk.dir & 1) === prevParity) parity = false;           // heading parity flips each step
    if (Math.abs(bk.black - prevBlack) !== 1) delta = false;   // black count changes by +-1
    prevBlack = bk.black; prevParity = bk.dir & 1;
  }
  check("bookkeeping: each step flips exactly one cell, heading parity flips, black count +-1",
        flips && parity && delta);

  // ---- turmites --------------------------------------------------------------
  const ta = new C.Ant(), tt = new C.Turmite("RL");
  let rl = true;
  for (let i = 0; i < 12000; i++) {
    const fa = ta.step(), ct = tt.step();
    if (ta.x !== tt.x || ta.y !== tt.y || ta.dir !== tt.dir || fa !== ct) { rl = false; break; }
  }
  check("turmite 'RL' reproduces Langton's ant EXACTLY for 12,000 steps (JS === Python)",
        rl && ref.rl === true);

  const t2 = new C.Turmite("RL");
  const tp = [[t2.x, t2.y]], th = [t2.dir];
  for (let i = 0; i < 20000; i++) { t2.step(); tp.push([t2.x, t2.y]); th.push(t2.dir); }
  const rlper = C.minimalPeriod(tp, th, 20000, 200, 1000);
  check("turmite 'RL' eventual period is also 104 (JS === Python)",
        rlper === 104 && rlper === ref.rlper);

  for (const r of ["LLRR", "RLLR", "LRRL"]) {
    const js = C.firstSymmetricStep(r, 2000);
    const py = ref.sym[r];
    check(`proven LL/RR-pair turmite '${r}' returns to a symmetric field at the same step + axis (JS === Python)`,
          JSON.stringify(js) === JSON.stringify(py),
          `JS ${JSON.stringify(js)}`);
  }

  // reflectionSymmetry is a genuine colour-preserving involution
  const cf = C.runTurmite("LLRR", C.firstSymmetricStep("LLRR", 2000)[0]).colorField();
  check("reflectionSymmetry finds a real mirror axis on the first symmetric LLRR field",
        C.reflectionSymmetry(cf) !== null);

  // ---- marked core region: self-contained, standalone, byte-identical in page
  const text = readFileSync(corePath, "utf8");
  const START = "/* === LANGTON_CORE START === */";
  const END = "/* === LANGTON_CORE END === */";
  const i0 = text.indexOf(START), i1 = text.indexOf(END);
  check("LANGTON_CORE markers present exactly once (start + end)",
        i0 >= 0 && i1 > i0 &&
        text.indexOf(START, i0 + 1) === -1 && text.indexOf(END, i1 + 1) === -1);
  if (i0 >= 0 && i1 > i0) {
    const region = text.slice(i0 + START.length, i1);
    check("marked core region has no import/export/require",
          !/\b(import|export|require)\b/.test(region));
    const tmp = path.join(mkdtempSync(path.join(tmpdir(), "langtoncore-")), "inlined.mjs");
    writeFileSync(tmp, region + "\nexport { detectHighway, stateSignature, Ant, Turmite, firstSymmetricStep };\n");
    const inl = await import(pathToFileURL(tmp).href);
    const ok = inl.detectHighway().period === 104 &&
      JSON.stringify(inl.stateSignature(5000)) === "[2,10,0,344,10414236]" &&
      inl.firstSymmetricStep("LLRR", 2000)[0] === 18;
    check("extracted core region runs standalone & matches", ok);

    const htmlPath = path.join(DIR, "index.html");
    if (existsSync(htmlPath)) {
      const html = readFileSync(htmlPath, "utf8");
      const j0 = html.indexOf(START), j1 = html.indexOf(END);
      const same = j0 >= 0 && j1 > j0 && html.slice(j0 + START.length, j1) === region;
      check("index.html inlines the LANGTON_CORE region BYTE-FOR-BYTE", same,
            same ? "" : "page core region differs from core.js");
    } else {
      console.log("[INFO] index.html not present yet; byte-identity check deferred.");
    }
  }

  console.log(`\nRESULT: ${passes} passed, ${failures} failed.`);
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error("ERROR:", e); process.exit(2); });
