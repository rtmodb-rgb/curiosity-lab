/*
 * core.js  --  The hat metatile substitution, in dependency-free JavaScript.
 *
 * Computational Curiosity Lab #3.  This is a faithful, line-by-line port of
 * hat.py + substitution.py (which are themselves ported, BSD-3-Clause, from
 * Craig S. Kaplan's `hatviz`, https://github.com/isohedral/hatviz).  Given a
 * level it returns the placed hats as records {vertices, reflected,
 * orientation, mtype, label}, in the SAME coordinate frame as the Python
 * (global scale 2), so the two outputs are identical -- test_core.mjs checks
 * this for several levels and seeds.
 *
 * The region between the HAT_CORE markers is self-contained (no import /
 * export / require) so a web page can inline it verbatim into a <script>.
 */

/*===HAT_CORE_START===*/
const R3 = 1.7320508075688772;     // sqrt(3)
const HR3 = 0.8660254037844386;    // sqrt(3)/2
const IDENT = [1, 0, 0, 0, 1, 0];

// ---- affine algebra (transform = [a,b,c,d,e,f] acting as the 2x3 matrix) ----
function hexPt(x, y) { return [x + 0.5 * y, HR3 * y]; }

function mul(A, B) {
  return [A[0] * B[0] + A[1] * B[3],
          A[0] * B[1] + A[1] * B[4],
          A[0] * B[2] + A[1] * B[5] + A[2],
          A[3] * B[0] + A[4] * B[3],
          A[3] * B[1] + A[4] * B[4],
          A[3] * B[2] + A[4] * B[5] + A[5]];
}

function inv(T) {
  const det = T[0] * T[4] - T[1] * T[3];
  return [T[4] / det, -T[1] / det, (T[1] * T[5] - T[2] * T[4]) / det,
          -T[3] / det, T[0] / det, (T[2] * T[3] - T[0] * T[5]) / det];
}

function trot(ang) {
  const c = Math.cos(ang), s = Math.sin(ang);
  return [c, -s, 0, s, c, 0];
}

function ttrans(tx, ty) { return [1, 0, tx, 0, 1, ty]; }

function rotAbout(p, ang) {
  return mul(ttrans(p[0], p[1]), mul(trot(ang), ttrans(-p[0], -p[1])));
}

function transPt(M, P) {
  return [M[0] * P[0] + M[1] * P[1] + M[2], M[3] * P[0] + M[4] * P[1] + M[5]];
}

function padd(p, q) { return [p[0] + q[0], p[1] + q[1]]; }
function psub(p, q) { return [p[0] - q[0], p[1] - q[1]]; }

function matchSeg(p, q) {
  return [q[0] - p[0], p[1] - q[1], p[0], q[1] - p[1], q[0] - p[0], p[1]];
}

function matchTwo(p1, q1, p2, q2) {
  return mul(matchSeg(p2, q2), inv(matchSeg(p1, q1)));
}

function intersect(p1, q1, p2, q2) {
  const d = (q2[1] - p2[1]) * (q1[0] - p1[0]) - (q2[0] - p2[0]) * (q1[1] - p1[1]);
  const uA = ((q2[0] - p2[0]) * (p1[1] - p2[1]) - (q2[1] - p2[1]) * (p1[0] - p2[0])) / d;
  return [p1[0] + uA * (q1[0] - p1[0]), p1[1] + uA * (q1[1] - p1[1])];
}

function det2(M) { return M[0] * M[4] - M[1] * M[3]; }

// ---- the hat: authoritative 13-gon (hatviz hat_outline) ----
const HAT_HEX = [[0, 0], [-1, -1], [0, -2], [2, -2], [2, -1], [4, -2], [5, -1],
                 [4, 0], [3, 0], [2, 2], [0, 3], [0, 2], [-1, 2]];
const HAT_OUTLINE = HAT_HEX.map(([x, y]) => hexPt(x, y));   // 13 cartesian verts

// ---- scene graph: hat leaves + metatile groups (mirrors substitution.py) ----
function HatTile(label) { return { kind: 'hat', label }; }

function MetaTile(shape, width) {
  return {
    kind: 'meta',
    shape: shape.map((p) => [p[0], p[1]]),
    width,
    children: [],
    addChild(T, geom) { this.children.push({ T, geom }); },
    evalChild(n, i) {
      const ch = this.children[n];
      return transPt(ch.T, ch.geom.shape[i]);
    },
    recentre() {
      const cx = this.shape.reduce((s, p) => s + p[0], 0) / this.shape.length;
      const cy = this.shape.reduce((s, p) => s + p[1], 0) / this.shape.length;
      this.shape = this.shape.map((p) => padd(p, [-cx, -cy]));
      const Mt = ttrans(-cx, -cy);
      for (const ch of this.children) ch.T = mul(Mt, ch.T);
    },
  };
}

const ORDER = ['H', 'T', 'P', 'F'];
// shared hat-leaf singletons; labels carry the metatile type / reflection.
const _H1 = HatTile('H1');   // the single reflected hat (lives only in H)
const _H = HatTile('H'), _T = HatTile('T'), _P = HatTile('P'), _F = HatTile('F');

function baseMetatiles() {
  const ho = HAT_OUTLINE;

  // H : irregular hexagon, 3 unreflected hats + 1 reflected (H1)
  const H_outline = [[0, 0], [4, 0], [4.5, HR3],
                     [2.5, 5 * HR3], [1.5, 5 * HR3], [-0.5, HR3]];
  const H = MetaTile(H_outline, 2);
  H.addChild(matchTwo(ho[5], ho[7], H_outline[5], H_outline[0]), _H);
  H.addChild(matchTwo(ho[9], ho[11], H_outline[1], H_outline[2]), _H);
  H.addChild(matchTwo(ho[5], ho[7], H_outline[3], H_outline[4]), _H);
  H.addChild(mul(ttrans(2.5, HR3),
                 mul([-0.5, -HR3, 0, HR3, -0.5, 0],
                     [0.5, 0, 0, 0, -0.5, 0])), _H1);   // reflection (det<0)

  // T : triangle, 1 hat
  const T_outline = [[0, 0], [3, 0], [1.5, 3 * HR3]];
  const T = MetaTile(T_outline, 2);
  T.addChild([0.5, 0, 0.5, 0, 0.5, HR3], _T);

  // P : parallelogram, 2 hats
  const P_outline = [[0, 0], [4, 0], [3, 2 * HR3], [-1, 2 * HR3]];
  const P = MetaTile(P_outline, 2);
  P.addChild([0.5, 0, 1.5, 0, 0.5, HR3], _P);
  P.addChild(mul(ttrans(0, 2 * HR3),
                 mul([0.5, HR3, 0, -HR3, 0.5, 0],
                     [0.5, 0.0, 0.0, 0.0, 0.5, 0.0])), _P);

  // F : pentagon, 2 hats
  const F_outline = [[0, 0], [3, 0], [3.5, HR3], [3, 2 * HR3], [-1, 2 * HR3]];
  const F = MetaTile(F_outline, 2);
  F.addChild([0.5, 0, 1.5, 0, 0.5, HR3], _F);
  F.addChild(mul(ttrans(0, 2 * HR3),
                 mul([0.5, HR3, 0, -HR3, 0.5, 0],
                     [0.5, 0.0, 0.0, 0.0, 0.5, 0.0])), _F);
  return [H, T, P, F];
}

// build a 29-tile patch, then carve the next-level metatiles.
const _PATCH_RULES = [
  ['H'],
  [0, 0, 'P', 2], [1, 0, 'H', 2], [2, 0, 'P', 2], [3, 0, 'H', 2],
  [4, 4, 'P', 2], [0, 4, 'F', 3], [2, 4, 'F', 3], [4, 1, 3, 2, 'F', 0],
  [8, 3, 'H', 0], [9, 2, 'P', 0], [10, 2, 'H', 0], [11, 4, 'P', 2],
  [12, 0, 'H', 2], [13, 0, 'F', 3], [14, 2, 'F', 1], [15, 3, 'H', 4],
  [8, 2, 'F', 1], [17, 3, 'H', 0], [18, 2, 'P', 0], [19, 2, 'H', 2],
  [20, 4, 'F', 3], [20, 0, 'P', 2], [22, 0, 'H', 2], [23, 4, 'F', 3],
  [23, 0, 'F', 3], [16, 0, 'P', 2], [9, 4, 0, 2, 'T', 2], [4, 0, 'F', 3],
];

// which patch children become each next-level metatile (the substitution).
const _KEEP = {
  H: [0, 9, 16, 27, 26, 6, 1, 8, 10, 15],
  T: [11],
  P: [7, 2, 3, 4, 28],
  F: [21, 20, 22, 23, 24, 25],
};

function constructPatch(H, T, P, F) {
  const shapes = { H, T, P, F };
  const ret = MetaTile([], H.width);
  for (const r of _PATCH_RULES) {
    if (r.length === 1) {
      ret.addChild(IDENT, shapes[r[0]]);
    } else if (r.length === 4) {
      const poly = ret.children[r[0]].geom.shape;
      const Tm = ret.children[r[0]].T;
      const P_ = transPt(Tm, poly[(r[1] + 1) % poly.length]);
      const Q = transPt(Tm, poly[r[1]]);
      const nshp = shapes[r[2]], npoly = nshp.shape;
      ret.addChild(matchTwo(npoly[r[3]], npoly[(r[3] + 1) % npoly.length], P_, Q), nshp);
    } else {
      const chP = ret.children[r[0]], chQ = ret.children[r[2]];
      const P_ = transPt(chQ.T, chQ.geom.shape[r[3]]);
      const Q = transPt(chP.T, chP.geom.shape[r[1]]);
      const nshp = shapes[r[4]], npoly = nshp.shape;
      ret.addChild(matchTwo(npoly[r[5]], npoly[(r[5] + 1) % npoly.length], P_, Q), nshp);
    }
  }
  return ret;
}

function constructMetatiles(patchM) {
  const bps1 = patchM.evalChild(8, 2);
  const bps2 = patchM.evalChild(21, 2);
  const rbps = transPt(rotAbout(bps1, -2.0 * Math.PI / 3.0), bps2);
  const p72 = patchM.evalChild(7, 2);
  const p252 = patchM.evalChild(25, 2);
  const llc = intersect(bps1, rbps, patchM.evalChild(6, 2), p72);
  let w = psub(patchM.evalChild(6, 2), llc);

  const nH = [llc, bps1];
  w = transPt(trot(-Math.PI / 3), w); nH.push(padd(nH[1], w));
  nH.push(patchM.evalChild(14, 2));
  w = transPt(trot(-Math.PI / 3), w); nH.push(psub(nH[3], w));
  nH.push(patchM.evalChild(6, 2));
  const new_H = MetaTile(nH, patchM.width * 2);
  for (const c of _KEEP.H) new_H.addChild(patchM.children[c].T, patchM.children[c].geom);

  const nP = [p72, padd(p72, psub(bps1, llc)), bps1, llc];
  const new_P = MetaTile(nP, patchM.width * 2);
  for (const c of _KEEP.P) new_P.addChild(patchM.children[c].T, patchM.children[c].geom);

  const nF = [bps2, patchM.evalChild(24, 2), patchM.evalChild(25, 0),
              p252, padd(p252, psub(llc, bps1))];
  const new_F = MetaTile(nF, patchM.width * 2);
  for (const c of _KEEP.F) new_F.addChild(patchM.children[c].T, patchM.children[c].geom);

  const AAA = nH[2];
  const BBB = padd(nH[1], psub(nH[4], nH[5]));
  const CCC = transPt(rotAbout(BBB, -Math.PI / 3), AAA);
  const new_T = MetaTile([BBB, CCC, AAA], patchM.width * 2);
  new_T.addChild(patchM.children[11].T, patchM.children[11].geom);

  for (const m of [new_H, new_P, new_F, new_T]) m.recentre();
  return [new_H, new_T, new_P, new_F];   // order H, T, P, F
}

// global scale 2 -> every placed hat vertex on the integer triangular lattice.
const GLOBAL_SCALE = [2, 0, 0, 0, 2, 0];

function metatilesAtLevel(level) {
  if (level < 1) throw new Error('level must be >= 1');
  let tiles = baseMetatiles();
  for (let i = 0; i < level - 1; i++) tiles = constructMetatiles(constructPatch(...tiles));
  return tiles;
}

function _orientationDeg(Mt) {
  const deg = Math.atan2(Mt[3], Mt[0]) * 180 / Math.PI;
  return Math.round(deg * 1e4) / 1e4;
}

function enumHats(meta, transform) {
  if (transform === undefined) transform = GLOBAL_SCALE;
  const out = [];
  (function rec(g, Mt) {
    if (g.kind === 'hat') {
      const verts = HAT_OUTLINE.map((p) => transPt(Mt, p));
      const mtype = (g.label === 'H' || g.label === 'H1') ? 'H' : g.label;
      out.push({
        vertices: verts,
        reflected: det2(Mt) < 0,
        orientation: _orientationDeg(Mt),
        mtype,
        label: g.label,
      });
    } else {
      for (const ch of g.children) rec(ch.geom, mul(Mt, ch.T));
    }
  })(meta, transform);
  return out;
}

function patch(level, seed) {
  if (seed === undefined) seed = 'H';
  const idx = ORDER.indexOf(seed);
  return enumHats(metatilesAtLevel(level)[idx]);
}
/*===HAT_CORE_END===*/

export {
  R3, HR3, IDENT, hexPt, mul, inv, trot, ttrans, rotAbout, transPt, padd, psub,
  matchSeg, matchTwo, intersect, det2, HAT_OUTLINE, HAT_HEX, ORDER, GLOBAL_SCALE,
  baseMetatiles, constructPatch, constructMetatiles, metatilesAtLevel, enumHats,
  patch,
};
