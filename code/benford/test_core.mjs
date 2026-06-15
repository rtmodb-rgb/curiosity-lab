/*
 * test_core.mjs  --  Node test (no external deps): does core.js reproduce
 * benford.py EXACTLY?  We cross-check the two engines across the language
 * boundary:
 *   - the leading-digit SEQUENCES of 2**n (n=1..2000), Fibonacci (1..2000) and
 *     n! (1..500) from JS BigInt === from Python big int, character for char;
 *   - benfordP(1..9) and benfordTwo(D) agree to 1e-12;
 *   - primesUpto(1e6).length === 78498 === Python len;
 *   - maxdev / chi-square / total-variation over the 2**n sequence agree to 1e-9;
 *   - the JS two-method generator (exact BigInt vs floor(10**frac)) agrees with
 *     itself over n=1..20000 (the in-browser analogue of the Python HP check);
 *   - the region between the BENFORD_CORE markers is self-contained (no
 *     import/export/require) and works when inlined alone.
 *
 * Run:  node test_core.mjs        (exits nonzero on any failure)
 * Paths resolve relative to this script (import.meta.url), so it runs from a
 * fresh clone of the repository.
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
    if (existsSync(path.join(c, "core.js")) && existsSync(path.join(c, "benford.py"))) {
      return c;
    }
  }
  throw new Error("could not locate core.js + benford.py (looked in: " + cands.join(", ") + ")");
}
const DIR = resolveDir();

let passes = 0, failures = 0;
function check(name, cond, detail = "") {
  if (cond) { passes++; console.log(`[PASS] ${name}` + (detail ? `   ${detail}` : "")); }
  else { failures++; console.log(`[FAIL] ${name}` + (detail ? `   ${detail}` : "")); }
}
const approx = (a, b, tol = 1e-12) => Math.abs(a - b) <= tol;

// ---- Python reference dump (imports benford.py from DIR) ------------------
const PY = [
  "import json, sys",
  "sys.path.insert(0, sys.argv[1])",
  "import benford as B",
  "def seq(gen):",
  "    return ''.join(str(B.lead_str(x)) for x in gen)",
  "pow2 = seq(B.powers(2, 2000))",
  "fib  = seq(B.fibonacci(2000))",
  "fac  = seq(B.factorials(500))",
  "c2   = B.leading_counts(B.powers(2, 2000))",
  "out = {",
  "  'pow2_seq': pow2,",
  "  'fib_seq': fib,",
  "  'fac_seq': fac,",
  "  'benfordP': B.BENFORD,",
  "  'benfordTwo': {str(D): B.benford_two(D) for D in (10, 11, 50, 90, 99)},",
  "  'pi_1e6': len(B.primes_upto(10**6)),",
  "  'pow2_maxdev_2000': B.maxdev(B.freqs(c2)),",
  "  'pow2_chi2_2000': B.chi_square(c2),",
  "  'pow2_tv_2000': B.total_variation(B.freqs(c2)),",
  "}",
  "print(json.dumps(out))",
].join("\n");

function pythonRef() {
  const buf = execFileSync("python3", ["-c", PY, DIR], { cwd: DIR, maxBuffer: 64 * 1024 * 1024 });
  return JSON.parse(buf.toString());
}

// ======================================================================
(async function main() {
  console.log("core.js  vs  benford.py   (dir: " + DIR + ")\n");

  const corePath = path.join(DIR, "core.js");
  const C = await import(pathToFileURL(corePath).href);
  const ref = pythonRef();

  // ---- leading-digit SEQUENCES agree exactly across the language boundary ----
  const jsSeq = (gen, lead = C.leadStr) => {
    let s = "";
    for (const x of gen) s += lead(x);
    return s;
  };
  const pow2js = jsSeq(C.powers(2, 2000));
  const fibjs = jsSeq(C.fibonacci(2000));
  const facjs = jsSeq(C.factorials(500));
  check("2**n leading-digit sequence n=1..2000  JS === Python",
        pow2js === ref.pow2_seq, `len ${pow2js.length}, py ${ref.pow2_seq.length}`);
  check("Fibonacci leading-digit sequence n=1..2000  JS === Python",
        fibjs === ref.fib_seq, `len ${fibjs.length}`);
  check("n! leading-digit sequence n=1..500  JS === Python",
        facjs === ref.fac_seq, `len ${facjs.length}`);

  // ---- canonical Benford targets agree ----
  check("benfordP(1..9) JS === Python (1e-12)",
        C.BENFORD.every((v, i) => approx(v, ref.benfordP[i])),
        `P(1)=${C.BENFORD[0].toFixed(6)}`);
  check("benfordTwo(D) JS === Python for D in {10,11,50,90,99} (1e-12)",
        [10, 11, 50, 90, 99].every((D) => approx(C.benfordTwo(D), ref.benfordTwo[String(D)])),
        `P(10)=${C.benfordTwo(10).toFixed(6)}`);

  // ---- prime sieve count matches (and the known literature value) ----
  const piJs = C.primesUpto(1e6).length;
  check("primesUpto(1e6).length === 78498 === Python",
        piJs === 78498 && piJs === ref.pi_1e6, `js=${piJs} py=${ref.pi_1e6}`);

  // ---- statistics over the 2**n sequence agree to tolerance ----
  const c2 = C.leadingCounts(C.powers(2, 2000));
  const mdJs = C.maxdev(C.freqs(c2));
  const chiJs = C.chiSquare(c2);
  const tvJs = C.totalVariation(C.freqs(c2));
  check("2**n maxdev (N=2000) JS === Python (1e-9)",
        approx(mdJs, ref.pow2_maxdev_2000, 1e-9), `js=${mdJs.toFixed(8)} py=${ref.pow2_maxdev_2000.toFixed(8)}`);
  check("2**n chi-square (N=2000) JS === Python (1e-9)",
        approx(chiJs, ref.pow2_chi2_2000, 1e-9), `js=${chiJs.toFixed(6)} py=${ref.pow2_chi2_2000.toFixed(6)}`);
  check("2**n total-variation (N=2000) JS === Python (1e-9)",
        approx(tvJs, ref.pow2_tv_2000, 1e-9), `js=${tvJs.toFixed(8)} py=${ref.pow2_tv_2000.toFixed(8)}`);

  // ---- JS two-method (exact BigInt vs floor(10**frac)) agree over n=1..20000 ----
  // The in-browser analogue of the Python high-precision check: even in double
  // precision (with the 1e-9 boundary snap) the log method matches the exact
  // digit across the whole range, because no 2**n mantissa comes within ~6e-6
  // of a digit boundary for n<=20000.
  let jsDisagree = 0, firstBad = -1;
  for (const [n, a, b] of C.powersLeadingTwoMethods(2, 20000)) {
    if (a !== b) { jsDisagree++; if (firstBad < 0) firstBad = n; }
  }
  check("JS two-method 2**n leading digit agree for ALL n=1..20000",
        jsDisagree === 0, `disagreements = ${jsDisagree}` + (firstBad > 0 ? ` (first at n=${firstBad})` : ""));

  // ---- generators sanity: known exact values ----
  const fib10 = [...C.fibonacci(10)].map(String);
  check("fibonacci(10) === 1,1,2,3,5,8,13,21,34,55",
        fib10.join(",") === "1,1,2,3,5,8,13,21,34,55", fib10.join(","));
  const fac5 = [...C.factorials(5)].map(String);
  check("factorials(5) === 1,2,6,24,120", fac5.join(",") === "1,2,6,24,120", fac5.join(","));
  check("leadStr(2**100) === 1 (1267650600228229401496703205376)",
        C.leadStr([...C.powers(2, 100)].pop()) === 1);

  // ---- the marked core region is self-contained & runs when inlined alone ----
  const text = readFileSync(corePath, "utf8");
  const START = "/* === BENFORD_CORE START === */";
  const END = "/* === BENFORD_CORE END === */";
  const i0 = text.indexOf(START), i1 = text.indexOf(END);
  check("BENFORD_CORE markers present (start + end)", i0 >= 0 && i1 > i0);
  if (i0 >= 0 && i1 > i0) {
    const region = text.slice(i0 + START.length, i1);
    check("marked core region has no import/export/require",
          !/\b(import|export|require)\b/.test(region));
    const tmp = path.join(mkdtempSync(path.join(tmpdir(), "benfordcore-")), "inlined.mjs");
    writeFileSync(tmp, region + "\nexport { benfordP, leadStr, primesUpto, powers };\n");
    const inl = await import(pathToFileURL(tmp).href);
    const okP = approx(inl.benfordP(1), Math.log10(2));
    const okPrime = inl.primesUpto(100).length === 25;       // 25 primes < 100
    const okLead = inl.leadStr([...inl.powers(2, 10)].pop()) === 1; // 2^10 = 1024
    check("extracted core region runs standalone & matches", okP && okPrime && okLead,
          `benfordP(1)=${inl.benfordP(1).toFixed(6)}, pi(100)=${inl.primesUpto(100).length}`);
  }

  console.log(`\nRESULT: ${passes} passed, ${failures} failed.`);
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error("ERROR:", e); process.exit(2); });
