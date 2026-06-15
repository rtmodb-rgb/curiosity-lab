/*
 * test_core.mjs  --  Node test (no external deps): does core.js reproduce
 * collatz.py EXACTLY, across the language boundary?  We cross-check:
 *   - total stopping time, altitude (max value) and Terras sigma for n=1..3000
 *     (JS BigInt path === Python int), value for value;
 *   - the OEIS record tables: totalStoppingRecords(1e5) and altitudeRecords(1e5)
 *     START/STEP/PEAK arrays === Python === OEIS A006877/8/A006884/5;
 *   - the Terras parity BIJECTION verdicts (exact for T at k=1..14, FAILS for the
 *     raw map C at k=2..8) === Python;
 *   - the descent sieve: popcount distribution == binomial; descendingClassFraction
 *     [num,den] === Python; minCounterexampleSurvivors(5) === [7,15,27,31];
 *   - the 151/47 rational cycle; the sibling-map cycles (3n-1, 5n+1);
 *   - landmark facts: 27 -> 111 (peak 9232), 837799 -> 524 (peak 2,974,984,576);
 *   - the region between the COLLATZ_CORE markers is self-contained (no
 *     import/export/require), runs when inlined alone, AND -- if index.html
 *     exists -- appears in it BYTE-FOR-BYTE (the page never drifts from core.js).
 *
 * Run:  node test_core.mjs        (exits nonzero on any failure)
 * Paths resolve via import.meta.url with a /shared/... fallback.
 */
import { execFileSync } from "node:child_process";
import { readFileSync, existsSync, writeFileSync, mkdtempSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { tmpdir } from "node:os";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
function resolveDir() {
  const cands = [HERE, "/shared/projects/curiosity-lab/collatz"];
  for (const c of cands) {
    if (existsSync(path.join(c, "core.js")) && existsSync(path.join(c, "collatz.py"))) return c;
  }
  throw new Error("could not locate core.js + collatz.py (looked in: " + cands.join(", ") + ")");
}
const DIR = resolveDir();

let passes = 0, failures = 0;
function check(name, cond, detail = "") {
  if (cond) { passes++; console.log(`[PASS] ${name}` + (detail ? `   ${detail}` : "")); }
  else { failures++; console.log(`[FAIL] ${name}` + (detail ? `   ${detail}` : "")); }
}

// ---- Python reference dump (imports collatz.py from DIR) -------------------
const PY = [
  "import json, sys",
  "from collections import Counter",
  "sys.path.insert(0, sys.argv[1])",
  "import collatz as C",
  "st = ','.join(str(C.total_stopping_time(n)) for n in range(1,3001))",
  "mx = ','.join(str(C.max_value(n)) for n in range(1,3001))",
  "sb = ','.join(str(C.stopping_time_below(n)) for n in range(2,3001))",
  "recs = C.total_stopping_records(10**5)",
  "alt  = C.altitude_records(10**5)",
  "cnt  = Counter(C.num_odd_steps(r,10) for r in range(1024))",
  "out = {",
  "  'st': st, 'mx': mx, 'sb': sb,",
  "  'rec_starts': [n for n,s in recs], 'rec_steps': [s for n,s in recs],",
  "  'alt_starts': [n for n,p in alt], 'alt_peaks': [str(p) for n,p in alt],",
  "  'bij_T': [C.is_parity_bijection(k, C.T_step) for k in range(1,15)],",
  "  'bij_C': [C.is_parity_bijection(k, C.collatz_step) for k in range(2,9)],",
  "  'pop_k10': [cnt[a] for a in range(11)],",
  "  'desc': {str(k): list(C.descending_class_fraction(k)) for k in (5,10,15,20,25)},",
  "  'surv32': C.min_counterexample_survivors(5),",
  "  'ratcyc': [str(x) for x in C.rational_cycle((1,0,1,1,0,0,1))],",
  "  's27': [C.total_stopping_time(27), str(C.max_value(27))],",
  "  's837799': [C.total_stopping_time(837799), str(C.max_value(837799))],",
  "  'cyc_3m1_5': list(C.find_cycle(5, C.step_3n_minus_1)),",
  "  'cyc_3m1_17': list(C.find_cycle(17, C.step_3n_minus_1)),",
  "  'cyc_5p1_1': list(C.find_cycle(1, C.step_5n_plus_1)),",
  "  'cyc_5p1_13': list(C.find_cycle(13, C.step_5n_plus_1)),",
  "}",
  "print(json.dumps(out))",
].join("\n");

function pythonRef() {
  const buf = execFileSync("python3", ["-c", PY, DIR], { cwd: DIR, maxBuffer: 64 * 1024 * 1024 });
  return JSON.parse(buf.toString());
}

(async function main() {
  console.log("core.js  vs  collatz.py   (dir: " + DIR + ")\n");
  const corePath = path.join(DIR, "core.js");
  const C = await import(pathToFileURL(corePath).href);
  const ref = pythonRef();

  // ---- per-n sequences agree across the language boundary -------------------
  const st = [], mx = [], sb = [];
  for (let n = 1; n <= 3000; n++) { st.push(String(C.totalStoppingTime(n))); mx.push(String(C.maxValue(n))); }
  for (let n = 2; n <= 3000; n++) sb.push(String(C.stoppingTimeBelow(n)));
  check("total stopping time n=1..3000  JS === Python", st.join(",") === ref.st);
  check("altitude (max value) n=1..3000  JS === Python (BigInt-exact)", mx.join(",") === ref.mx);
  check("Terras sigma (first descent) n=2..3000  JS === Python", sb.join(",") === ref.sb);

  // ---- OEIS record tables (independent recompute) ---------------------------
  const recs = C.totalStoppingRecords(1e5);
  check("totalStoppingRecords(1e5) START values JS === Python (OEIS A006877)",
        recs.map((r) => r[0]).join(",") === ref.rec_starts.join(","));
  check("totalStoppingRecords(1e5) STEP records JS === Python (OEIS A006878)",
        recs.map((r) => r[1]).join(",") === ref.rec_steps.join(","));
  const alt = C.altitudeRecords(1e5);
  check("altitudeRecords(1e5) START values JS === Python (OEIS A006884)",
        alt.map((r) => r[0]).join(",") === ref.alt_starts.join(","));
  check("altitudeRecords(1e5) PEAK values JS === Python (OEIS A006885)",
        alt.map((r) => String(r[1])).join(",") === ref.alt_peaks.join(","));

  // ---- the Terras bijection verdicts ----------------------------------------
  const bijT = [], bijC = [];
  for (let k = 1; k <= 14; k++) bijT.push(C.isParityBijection(k, C.tStep));
  for (let k = 2; k <= 8; k++) bijC.push(C.isParityBijection(k, C.collatzStep));
  check("parity bijection holds for T at k=1..14 (all true) JS === Python",
        bijT.every(Boolean) && bijT.join() === ref.bij_T.join());
  check("parity bijection FAILS for raw C at k=2..8 (all false) JS === Python",
        bijC.every((b) => !b) && bijC.join() === ref.bij_C.join());

  // ---- the descent sieve ----------------------------------------------------
  const pop = new Array(11).fill(0);
  for (let r = 0; r < 1024; r++) pop[C.numOddSteps(r, 10)]++;
  const binomK10 = Array.from({ length: 11 }, (_, a) => C.binom(10, a));
  check("popcount distribution mod 2^10 == Binomial(10,a) == Python",
        pop.join() === binomK10.join() && pop.join() === ref.pop_k10.join());
  const descOk = [5, 10, 15, 20, 25].every((k) =>
    C.descendingClassFraction(k).join() === ref.desc[String(k)].join());
  check("descendingClassFraction(k) [num,den] JS === Python (k=5,10,15,20,25)", descOk,
        `k=25 -> ${C.descendingClassFraction(25).join("/")}`);
  check("minCounterexampleSurvivors(5) === [7,15,27,31] === Python",
        C.minCounterexampleSurvivors(5).join() === "7,15,27,31"
        && C.minCounterexampleSurvivors(5).join() === ref.surv32.join());

  // ---- rational cycle + sibling cycles --------------------------------------
  check("rationalCycle((1,0,1,1,0,0,1)) -> 151/47 ... JS === Python",
        C.rationalCycle([1, 0, 1, 1, 0, 0, 1]).join() === ref.ratcyc.join(),
        C.rationalCycle([1, 0, 1, 1, 0, 0, 1]).join(" -> "));
  check("3n-1 cycle from 5 JS === Python (5,7,10,14,20 as a set)",
        C.findCycle(5, C.step3nMinus1).join() === ref.cyc_3m1_5.join());
  check("3n-1 cycle from 17 (18-cycle) JS === Python",
        C.findCycle(17, C.step3nMinus1).join() === ref.cyc_3m1_17.join()
        && C.findCycle(17, C.step3nMinus1).length === 18);
  check("5n+1 cycle from 1 JS === Python", C.findCycle(1, C.step5nPlus1).join() === ref.cyc_5p1_1.join());
  check("5n+1 cycle from 13 (no 1 in it) JS === Python",
        C.findCycle(13, C.step5nPlus1).join() === ref.cyc_5p1_13.join()
        && !C.findCycle(13, C.step5nPlus1).includes(1));

  // ---- landmark facts -------------------------------------------------------
  check("27 -> 111 steps, peak 9232",
        C.totalStoppingTime(27) === 111 && String(C.maxValue(27)) === "9232"
        && ref.s27[0] === 111 && ref.s27[1] === "9232");
  check("837799 -> 524 steps, peak 2,974,984,576 (~3 billion, from a < 1e6 start)",
        C.totalStoppingTime(837799) === 524 && String(C.maxValue(837799)) === "2974984576"
        && ref.s837799[0] === 524 && ref.s837799[1] === "2974984576");

  // ---- marked core region: self-contained, standalone, byte-identical in page
  const text = readFileSync(corePath, "utf8");
  const START = "/* === COLLATZ_CORE START === */";
  const END = "/* === COLLATZ_CORE END === */";
  const i0 = text.indexOf(START), i1 = text.indexOf(END);
  check("COLLATZ_CORE markers present (start + end)", i0 >= 0 && i1 > i0);
  if (i0 >= 0 && i1 > i0) {
    const region = text.slice(i0 + START.length, i1);
    check("marked core region has no import/export/require",
          !/\b(import|export|require)\b/.test(region));
    const tmp = path.join(mkdtempSync(path.join(tmpdir(), "collatzcore-")), "inlined.mjs");
    writeFileSync(tmp, region + "\nexport { totalStoppingTime, maxValue, isParityBijection, tStep, collatzStep };\n");
    const inl = await import(pathToFileURL(tmp).href);
    const ok = inl.totalStoppingTime(27) === 111 && String(inl.maxValue(27)) === "9232"
      && inl.isParityBijection(8, inl.tStep) === true && inl.isParityBijection(8, inl.collatzStep) === false;
    check("extracted core region runs standalone & matches", ok);

    const htmlPath = path.join(DIR, "index.html");
    if (existsSync(htmlPath)) {
      const html = readFileSync(htmlPath, "utf8");
      const j0 = html.indexOf(START), j1 = html.indexOf(END);
      const same = j0 >= 0 && j1 > j0 && html.slice(j0 + START.length, j1) === region;
      check("index.html inlines the COLLATZ_CORE region BYTE-FOR-BYTE", same,
            same ? "" : "page core region differs from core.js");
    } else {
      console.log("[INFO] index.html not present yet; byte-identity check deferred.");
    }
  }

  console.log(`\nRESULT: ${passes} passed, ${failures} failed.`);
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error("ERROR:", e); process.exit(2); });
