/* DOM smoke test: load the ACTUAL inlined core + page scripts from index.html into a
   minimal fake DOM, init every widget, then drive each control and assert sane readouts.
   Running core+page in one shared scope mirrors classic <script> global-lexical sharing,
   so this also proves `class Ant`/`class Turmite` are visible to the page controller. */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const HTML = fs.readFileSync(path.join(__dirname, "index.html"), "utf8");
const scripts = [...HTML.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
if (scripts.length !== 2) throw new Error("expected 2 inline scripts, got " + scripts.length);

let failures = 0;
const ok = (name, cond, extra) => { console.log((cond ? "[PASS] " : "[FAIL] ") + name + (extra ? "   " + extra : "")); if (!cond) failures++; };

// ---- fake 2D context (every method a no-op; numeric fields real) ----
function mkCtx() {
  const c = { fillStyle: "#000", strokeStyle: "#000", lineWidth: 1, globalAlpha: 1, font: "", textAlign: "", textBaseline: "", lineJoin: "" };
  for (const m of ["clearRect","fillRect","strokeRect","beginPath","moveTo","lineTo","closePath","fill","stroke","arc","setTransform","save","restore","translate","scale","fillText","rect"]) c[m] = () => {};
  return c;
}
// ---- fake element ----
function mkEl(tag) {
  const el = {
    tagName: (tag || "div").toUpperCase(), _text: "", _html: "", _value: "",
    children: [], _ln: {}, dataset: {}, style: {}, _attrs: {}, clientLeft: 0, clientTop: 0,
    classList: { _s: new Set(),
      add(c){this._s.add(c);}, remove(c){this._s.delete(c);},
      toggle(c,on){ if(on===undefined) on=!this._s.has(c); on?this._s.add(c):this._s.delete(c); return !!on; },
      contains(c){return this._s.has(c);} },
    setAttribute(k,v){ this._attrs[k]=String(v); },
    getAttribute(k){ return this._attrs[k]; },
    addEventListener(ev,fn){ (this._ln[ev]=this._ln[ev]||[]).push(fn); },
    removeEventListener(){},
    appendChild(c){ this.children.push(c); return c; },
    querySelectorAll(sel){ return sel.indexOf("button")>=0 ? this.children.filter(c=>c.tagName==="BUTTON") : []; },
    closest(sel){ const m=sel.match(/data-([a-z]+)/); if(m && this.dataset[m[1]]!==undefined) return this; return null; },
    getContext(){ return this._ctx || (this._ctx = mkCtx()); },
    getBoundingClientRect(){ return { left:0, top:0, width:680, height:420 }; },
    focus(){},
    get clientWidth(){ return 680; }, get clientHeight(){ return 420; },
    get textContent(){ return this._text; }, set textContent(v){ this._text=String(v); },
    get innerHTML(){ return this._html; }, set innerHTML(v){ this._html=String(v); },
    get value(){ return this._value; }, set value(v){ this._value=String(v); }
  };
  return el;
}

// ---- registry: one element per id in the page ----
const ids = [...new Set([...HTML.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]))];
const byId = {};
for (const id of ids) { const e = mkEl(id.startsWith("a")||/Btn|Go|Run|Play|Step|Reset|Jump|Fwd|Back|Clear|Random/.test(id) ? "button" : "div"); e.id = id; byId[id] = e; }
// ranges / inputs need an initial value matching the HTML defaults
byId.aSpeed._value = "3"; byId.dN._value = "1200"; byId.eRule._value = "RL";
// preset buttons inside #ePresets
const presets = [["RL","12000"],["RLLR","16000"],["LLRR","16000"],["RLR","60000"],["LRRRRRLLR","70000"]];
byId.ePresets.children = presets.map(([rule,steps]) => { const b = mkEl("button"); b.dataset.rule = rule; b.dataset.steps = steps; return b; });

const docEl = mkEl("html");
const document = {
  documentElement: docEl,
  getElementById: id => byId[id] || null,
  createElement: t => mkEl(t),
  addEventListener(){}, querySelectorAll(){ return []; }
};
const sandbox = {
  document, console,
  getComputedStyle: () => ({ getPropertyValue: () => "#888" }),
  requestAnimationFrame: () => 0, cancelAnimationFrame: () => {},
  setTimeout: () => 0, clearTimeout: () => {},
  Math, JSON, Date, Object, Array, Set, Map, Number, String, Boolean, isFinite, parseInt, parseFloat, RegExp, Error
};
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.devicePixelRatio = 1;
sandbox.matchMedia = () => ({ matches: true, addEventListener(){}, addListener(){} }); // reduce-motion ON -> Widget D is synchronous
sandbox.addEventListener = () => {};
vm.createContext(sandbox);

// ---- run core + page in ONE shared scope (mimics classic-script global lexical sharing) ----
try {
  vm.runInContext(scripts[0] + "\n;\n" + scripts[1], sandbox, { filename: "index.inline.js" });
  ok("page initializes (core classes visible to controller; no throw on init)", true);
} catch (e) {
  ok("page initializes (no throw on init)", false, String(e && e.stack || e));
  console.log("\nRESULT: " + failures + " failed (init crashed).");
  process.exit(1);
}

const T = id => byId[id]._text;
const H = id => byId[id]._html;
const fire = (id, type, target, extra) => {
  const el = byId[id]; const ev = Object.assign({ type, target: target || el, preventDefault(){}, key: undefined }, extra || {});
  (el._ln[type] || []).forEach(fn => fn(ev));
};

// ---- Widget A: initial readouts, step, jump ----
ok("A init readouts (step 0, all white)", T("aStepN") === "0" && T("aBlack") === "0" && H("aPhase") === "all white", "phase=" + H("aPhase"));
fire("aStep", "click");
ok("A step -> step 1, 1 black cell", T("aStepN") === "1" && T("aBlack") === "1");
fire("aJump", "click");
ok("A jump-to-highway -> step 11,000, highway phase", T("aStepN") === "11,000" && /highway/.test(H("aPhase")), "step=" + T("aStepN") + " phase=" + H("aPhase"));

// ---- Widget B: run & detect ----
fire("bRun", "click");
ok("B period = 104", T("bPeriod") === "104", "got " + T("bPeriod"));
ok("B drift shows 2√2", /2√2/.test(H("bDrift")) && /√8/.test(H("bDrift")), H("bDrift"));
ok("B cells/period = +12", T("bCells") === "+12", "got " + T("bCells"));
ok("B onset ≈ 9,977", /9,977/.test(H("bOnset")), H("bOnset"));
ok("B P=52 fails (104 minimal)", /fails/.test(H("b52")), H("b52"));

// ---- Widget C: randomize + run ----
fire("cRandom", "click");
fire("cRun", "click");
ok("C run produces a verdict (highway found / open)", /highway|open/.test(H("cVerdict")), H("cVerdict"));
// also a paint click must not throw
fire("cCanvas", "click", byId.cCanvas, { clientX: 340, clientY: 210 });
ok("C paint click handled (no throw)", true);

// ---- Widget D: forward then reverse (reduce-motion -> synchronous) ----
byId.dN._value = "2000"; fire("dN", "input");
ok("D run-length readout updates to 2,000", T("dNOut") === "2,000", T("dNOut"));
fire("dFwd", "click");
ok("D build forward -> some black cells", Number(T("dBlack").replace(/,/g,"")) > 0, "black=" + T("dBlack"));
fire("dBack", "click");
ok("D reverse -> round-trip error 0 cells", /^0\b/.test(T("dErr")) && /home|reversed/.test(T("dPhase")), "err=" + T("dErr") + " phase=" + T("dPhase"));

// ---- Widget E: preset + free text ----
ok("E default RL ran (colours 2, cells > 0)", T("eRuleOut") === "RL" && T("eColours") === "2" && Number(T("eCells").replace(/,/g,"")) > 0, "rule=" + T("eRuleOut") + " cols=" + T("eColours") + " cells=" + T("eCells"));
fire("ePresets", "click", byId.ePresets.children[1]); // RLLR
ok("E preset RLLR -> 4 colours, symmetric tag", T("eColours") === "4" && /symmetr/i.test(H("eTag")), "cols=" + T("eColours") + " tag=" + H("eTag"));
byId.eRule._value = "rl9zr"; fire("eGo", "click"); // sanitizes to RLR
ok("E free text sanitizes non-LR chars", T("eRuleOut") === "RLR", "got " + T("eRuleOut"));
byId.eRule._value = ""; fire("eGo", "click");
ok("E empty rule -> friendly error, no throw", /only the letters/.test(H("eTag")), H("eTag"));

console.log("\nRESULT: " + (failures === 0 ? "all widgets OK, 0 failed." : failures + " failed."));
process.exit(failures === 0 ? 0 : 1);
