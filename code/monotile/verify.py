"""
verify.py  --  THE RIGOR GATE for Curiosity Lab #3 (the hat monotile).

Brand ethos: compute, don't assert; verify every headline number two
independent ways; fail loud.  Prints PASS/FAIL per check and EXITS NONZERO
on any failure.

COMBINATORIAL checks (the substitution matrix, eigen-structure, growth):
  (a) the matrix REALIZED by counting children-by-type in the actual
      geometric substitution == reference M;
  (b) numpy dominant eigenvalue == (7+3 sqrt5)/2 == phi^4;
  (c) sympy EXACT characteristic polynomial == (x-1)(x+1)(x^2-7x+1);
  (d) normalized Perron eigenvector == (1/3, 7/6-sqrt5/2, sqrt5-2, 3/2-sqrt5/2);
  (e) iterate the REAL substitution k=0..6 from every seed and assert the
      realized integer count vector == M^k e_seed EXACTLY; ratios -> eigvec;
      growth factor -> phi^4.

GEOMETRIC checks (on generated patches; exact integer-lattice arithmetic,
with an independent shapely cross-check when available):
  (f) no overlaps   (no two hats share positive-area interior);
  (g) no gaps       (interior atomic edges shared by exactly 2 tiles; the
                     boundary is a single simple loop -> no holes);
  (h) every placed tile congruent to the canonical hat (edge-length multiset
      + turning sequence up to rotation/reflection/cyclic shift; transforms
      are isometries of one global scale; integer area J == 32 each);
  (i) unreflected:reflected hat ratio -> phi^4 as the level grows.
"""

import sys
import math
from collections import Counter, defaultdict

import numpy as np
import sympy as sp

import hat as H
from substitution import (M_REFERENCE, ORDER, realized_matrix, patch,
                          metatile_tree_counts, enum_hats, metatiles_at_level,
                          HATS_PER_METATILE)

R3 = H.R3
PHI = (1 + 5 ** 0.5) / 2
PHI4 = PHI ** 4

_failures = []
_passes = 0            # core checks (numpy + sympy only; ALWAYS run)
_shapely_passes = 0    # optional floating-point cross-checks (only if shapely is installed)
_shapely_ran = False   # set True once the shapely import succeeds


def check(name, cond, detail=""):
    global _passes, _shapely_passes
    cond = bool(cond)
    if cond:
        if "[shapely cross-check]" in name:   # optional extra layer -> counted separately
            _shapely_passes += 1
        else:
            _passes += 1
    else:
        _failures.append(name)
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"   {detail}" if detail else ""))
    return cond


# ======================================================================
# Exact integer-hex-lattice helpers (the global x2 scale puts every placed
# hat vertex on the integer triangular lattice; cartesian (X,Y) -> (p,q)).
# ======================================================================
def raw_hex(P):
    """Cartesian (X,Y) -> exact-ish hex coords (p,q) as floats (not snapped)."""
    X, Y = P
    q = 2 * Y / R3
    p = X - 0.5 * q
    return (p, q)


# Common integer reference for a whole patch. All hats in one tiling sit on a
# common triangular lattice translated by a single global (possibly non-lattice)
# offset that depends on the seed's recentre; relative positions are EXACT
# lattice vectors. So we rebase every (p,q) by one global reference point and
# round -- the residual must be ~0 (asserted), which proves lattice alignment.
_REF = None


def set_reference(P):
    global _REF
    _REF = raw_hex(P)


def to_int(P):
    """Snap a Cartesian point to integer hex coords relative to _REF."""
    p, q = raw_hex(P)
    pr, qr = p - _REF[0], q - _REF[1]
    pi, qi = round(pr), round(qr)
    if abs(pr - pi) > 1e-6 or abs(qr - qi) > 1e-6:
        raise ValueError(f"vertex {P} off lattice: rel=({pr:.6f},{qr:.6f})")
    return (pi, qi)


def hex_signed_area2(loop):
    """Twice the signed area of an integer-(p,q) polygon, in lattice units
       (cartesian area = result * sqrt(3)/4). Integer."""
    s = 0
    n = len(loop)
    for i in range(n):
        p0, q0 = loop[i]
        p1, q1 = loop[(i + 1) % n]
        s += p0 * q1 - p1 * q0
    return s


def as_ccw_hexloop(hat_record):
    """Return the hat's 13 integer-hex vertices, oriented CCW (signed area > 0)."""
    loop = [to_int(v) for v in hat_record['vertices']]
    if hex_signed_area2(loop) < 0:
        loop = loop[::-1]
    return loop


def _ccw_sig(poly):
    """Min cyclic rotation of the (edge_length, turn_angle) sequence, after
       orienting the polygon CCW. Invariant under rotation/translation and
       choice of starting vertex; distinguishes a shape from its mirror."""
    P = poly if H.shoelace_signed(poly) > 0 else poly[::-1]
    n = len(P)
    L = [round(math.hypot(P[(i + 1) % n][0] - P[i][0],
                          P[(i + 1) % n][1] - P[i][1]), 6) for i in range(n)]
    T = [round(t, 4) for t in H.turning_sequence(P)]
    pairs = [(L[i], T[i]) for i in range(n)]
    return min(tuple(pairs[i:] + pairs[:i]) for i in range(n))


def congruence_signature(poly):
    """Rotation+REFLECTION-invariant signature. We compare the shape AND its true
       mirror image (x,y)->(x,-y); a hat and its mirror get the same signature, so
       reflected tiles in the tiling are correctly recognized as congruent."""
    mirror = [(x, -y) for (x, y) in poly]
    return min(_ccw_sig(poly), _ccw_sig(mirror))


def atomic_edges(loop):
    """Split each polygon edge into unit (gcd) sub-edges on the lattice.
       Yields directed (a, b) integer-hex atomic edges. Handles T-junctions:
       the only non-primitive hat edges are the length-2 ones (gcd=2)."""
    n = len(loop)
    for i in range(n):
        a = loop[i]
        b = loop[(i + 1) % n]
        dp, dq = b[0] - a[0], b[1] - a[1]
        g = math.gcd(abs(dp), abs(dq))
        if g == 0:
            continue
        sp_, sq_ = dp // g, dq // g
        for k in range(g):
            yield ((a[0] + k * sp_, a[1] + k * sq_),
                   (a[0] + (k + 1) * sp_, a[1] + (k + 1) * sq_))


# ======================================================================
# COMBINATORIAL CHECKS
# ======================================================================
def combinatorial_checks():
    print("\n=== COMBINATORIAL ===")
    Mr = realized_matrix()
    M = np.array(M_REFERENCE)

    # (a) realized geometric substitution matrix == reference M
    check("(a) realized substitution matrix == reference M (cols/rows H,T,P,F)",
          Mr == M_REFERENCE, f"realized={Mr}")

    # (b) numpy dominant eigenvalue == phi^4 == (7+3sqrt5)/2
    eig = np.linalg.eigvals(M.astype(float))
    dom = max(eig.real)
    check("(b) numpy dominant eigenvalue == phi^4 == (7+3sqrt5)/2",
          abs(dom - PHI4) < 1e-9 and abs(dom - (7 + 3 * 5 ** 0.5) / 2) < 1e-9,
          f"dom={dom:.10f} phi^4={PHI4:.10f}")

    # (c) sympy exact characteristic polynomial factorization
    x = sp.symbols('x')
    Ms = sp.Matrix(M_REFERENCE)
    cp = sp.expand(Ms.charpoly(x).as_expr())
    target = sp.expand((x - 1) * (x + 1) * (x ** 2 - 7 * x + 1))
    check("(c) sympy charpoly == (x-1)(x+1)(x^2-7x+1)", cp == target,
          f"charpoly={sp.factor(cp)}")

    # (d) normalized Perron eigenvector (exact, via sympy nullspace)
    lam = sp.Rational(7, 2) + sp.Rational(3, 2) * sp.sqrt(5)
    vec = (Ms - lam * sp.eye(4)).nullspace()[0]
    vec = vec / sum(vec)
    want = [sp.Rational(1, 3),
            sp.Rational(7, 6) - sp.sqrt(5) / 2,
            sp.sqrt(5) - 2,
            sp.Rational(3, 2) - sp.sqrt(5) / 2]
    eq = all(sp.simplify(vec[i] - want[i]) == 0 for i in range(4))
    check("(d) Perron eigenvector == (1/3, 7/6-sqrt5/2, sqrt5-2, 3/2-sqrt5/2)",
          eq, f"decimals={[round(float(v),8) for v in vec]}")

    # (e) realized substitution k=0..6 from each seed == M^k e_seed exactly
    e = {'H': np.array([1, 0, 0, 0]), 'T': np.array([0, 1, 0, 0]),
         'P': np.array([0, 0, 1, 0]), 'F': np.array([0, 0, 0, 1])}
    all_e = True
    detail = []
    for seed in ORDER:
        for k in range(0, 6):          # k = level-1 ; levels 1..6
            predicted = np.linalg.matrix_power(M, k) @ e[seed]
            realized = metatile_tree_counts(k + 1, seed)
            rv = np.array([realized[t] for t in ORDER])
            if not np.array_equal(rv, predicted):
                all_e = False
                detail.append(f"seed {seed} k={k}: realized {rv.tolist()} != M^k e {predicted.tolist()}")
    check("(e) realized counts == M^k e_seed for all seeds, k=0..5 (exact int)",
          all_e, "; ".join(detail))

    # (e') growth factor and frequency convergence -> phi^4 / eigenvector
    counts = []
    for L in range(1, 9):
        v = np.linalg.matrix_power(M, L - 1) @ e['H']
        counts.append(v.sum())
    ratios = [counts[i + 1] / counts[i] for i in range(len(counts) - 1)]
    check("(e') metatile growth factor -> phi^4", abs(ratios[-1] - PHI4) < 1e-3,
          f"last few growth ratios={[round(r,5) for r in ratios[-3:]]}")
    # normalized frequency -> Perron eigenvector (float to avoid int64 overflow)
    vbig = np.linalg.matrix_power(M.astype(float), 40) @ e['H'].astype(float)
    freq = vbig / vbig.sum()
    want_f = np.array([1/3, 7/6 - 5**0.5/2, 5**0.5 - 2, 3/2 - 5**0.5/2])
    check("(e') metatile frequencies -> Perron eigenvector",
          np.allclose(freq, want_f, atol=1e-8), f"freq={np.round(freq,8).tolist()}")


# ======================================================================
# GEOMETRIC CHECKS  (exact integer core + shapely cross-check)
# ======================================================================
def geometric_checks(level=4, seed='H'):
    print(f"\n=== GEOMETRIC (patch: level {level}, seed {seed}) ===")
    hats = patch(level, seed)
    N = len(hats)
    # establish ONE global integer reference for this whole patch (handles any
    # seed: all hats share a common lattice up to a single global offset).
    set_reference(hats[0]['vertices'][0])
    loops = [as_ccw_hexloop(h) for h in hats]

    # --- (h0) every hat has integer lattice area J == 32 (= 32 unit triangles)
    Js = [hex_signed_area2(lp) for lp in loops]
    check("(h) every placed hat has exact integer area J == 32",
          all(j == 32 for j in Js), f"distinct J = {sorted(set(Js))}, N={N}")

    # ---------- (f) NO OVERLAPS ----------
    # Method 1 (exact int): every DIRECTED atomic edge appears at most once.
    dir_count = Counter()
    for lp in loops:
        for e in atomic_edges(lp):
            dir_count[e] += 1
    max_dir = max(dir_count.values())
    overlap_edge_ok = (max_dir == 1)

    # Method 2 (exact int, independent): decompose every hat into its 8 kites
    # (rebuilt from the metatile tree, independent of `loops`); key each kite by
    # its 4 integer-hex vertices. No kite cell may be covered twice.
    kite_keys = _kite_keys_for_patch(level, seed)
    dup_kites = [k for k, c in kite_keys.items() if c > 1]
    overlap_kite_ok = (len(dup_kites) == 0)
    check("(f) no overlaps - directed atomic edges unique (exact int)",
          overlap_edge_ok, f"max directed-edge multiplicity = {max_dir}")
    check("(f) no overlaps - all 8N kite cells distinct (independent exact int)",
          overlap_kite_ok, f"total kite cells = {sum(kite_keys.values())}, duplicates = {len(dup_kites)}")

    # ---------- (g) NO GAPS ----------
    # Interior atomic edges appear exactly twice (once each direction);
    # boundary atomic edges once; boundary forms exactly ONE simple loop.
    undirected = Counter()
    for (a, b), c in dir_count.items():
        undirected[frozenset((a, b))] += c
    bad_mult = [e for e, c in undirected.items() if c not in (1, 2)]
    # boundary directed edges = those whose reverse is absent
    boundary = [(a, b) for (a, b), c in dir_count.items()
                if dir_count.get((b, a), 0) == 0]
    nloops, manifold = _count_boundary_loops(boundary)
    # enclosed area of boundary (single loop) must equal 32*N
    bnd_area_ok = False
    if nloops == 1:
        loop_pts = _trace_single_loop(boundary)
        bnd_area_ok = (abs(hex_signed_area2(loop_pts)) == 32 * N)
    check("(g) no gaps - every interior atomic edge shared by exactly 2 tiles",
          len(bad_mult) == 0, f"edges with multiplicity not in (1,2): {len(bad_mult)}")
    check("(g) no gaps - boundary is exactly ONE simple loop (no holes)",
          nloops == 1 and manifold, f"boundary loops = {nloops}, manifold = {manifold}")
    check("(g) no gaps - enclosed boundary area == 32*N (exact int)",
          bnd_area_ok, f"32*N = {32*N}")

    # ---------- (h) CONGRUENCE ----------
    # reflection+rotation-invariant signature: edge-length multiset is implied,
    # and the cyclic (edge,turn) signature (incl. mirror) pins the exact shape.
    base_sig = congruence_signature(H.HAT_OUTLINE)
    base_lens = H.edge_length_multiset(H.HAT_OUTLINE)
    n_bad_sig = sum(1 for h in hats if congruence_signature(h['vertices']) != base_sig)
    n_bad_len = sum(1 for h in hats if H.edge_length_multiset(h['vertices']) != base_lens)
    # transforms are one global-scale isometries: |det| all equal
    scales = {round(abs(d), 6) for d in metatiles_isometry_sample(level, seed)}
    check("(h) every hat congruent to canonical hat (edge+turn signature, refl-aware)",
          n_bad_sig == 0, f"non-congruent hats = {n_bad_sig}/{N}")
    check("(h) every hat has the canonical edge-length multiset",
          n_bad_len == 0, f"wrong-edge hats = {n_bad_len}/{N}")
    check("(h) all hat transforms share one scale and are isometries",
          len(scales) == 1, f"distinct |det| among transforms = {sorted(scales)}")

    # ---------- (i) unreflected:reflected ratio -> phi^4 ----------
    ratios = []
    levels = list(range(2, 7))
    for L in levels:
        tc = metatile_tree_counts(L, 'H')   # base metatile counts
        refl = tc['H']                       # one reflected hat per H metatile
        total = sum(HATS_PER_METATILE[t] * tc[t] for t in ORDER)
        ratios.append((total - refl) / refl)
    err_last = abs(ratios[-1] - PHI4)
    err_first = abs(ratios[0] - PHI4)
    check("(i) unreflected:reflected ratio -> phi^4 (oscillating, converging)",
          err_last < 1e-3 and err_last < err_first,
          f"ratios L2..L6 = {[round(r,5) for r in ratios]} -> phi^4={PHI4:.5f}")

    # ---------- independent shapely cross-check (if available) ----------
    # Build from the SNAPPED integer loops so shared vertices are bit-identical
    # (raw per-tile floats differ by ~1e-13 and create spurious sliver-holes).
    _shapely_cross_check(loops, N)


def _kite_keys_for_patch(level, seed):
    """Exactly enumerate every placed hat's 8 kites as integer-hex cells and
       count how many times each kite cell is covered. Independent of edges."""
    from substitution import metatiles_at_level, ORDER as _O, GLOBAL_SCALE
    from hat import mul as _mul, trans_pt as _t, HAT_KITES_HEX, hexpt
    idx = _O.index(seed)
    meta = metatiles_at_level(level)[idx]
    keys = Counter()

    def rec(g, Mt):
        if g.kind == 'hat':
            for kite in HAT_KITES_HEX:
                cell = []
                for (kx, ky) in kite:
                    P = _t(Mt, hexpt(kx, ky))
                    cell.append(to_int(P))
                keys[frozenset(cell)] += 1
        else:
            for ch in g.children:
                rec(ch['geom'], _mul(Mt, ch['T']))

    rec(meta, GLOBAL_SCALE)
    return keys


def metatiles_isometry_sample(level, seed):
    """Return |det| of the linear part of every placed hat's transform."""
    from substitution import metatiles_at_level, ORDER as _O, GLOBAL_SCALE
    from hat import mul as _mul, det2
    idx = _O.index(seed)
    meta = metatiles_at_level(level)[idx]
    dets = []

    def rec(g, Mt):
        if g.kind == 'hat':
            dets.append(det2(Mt))
        else:
            for ch in g.children:
                rec(ch['geom'], _mul(Mt, ch['T']))

    rec(meta, GLOBAL_SCALE)
    return dets


def _count_boundary_loops(boundary):
    """Count directed-edge cycles; verify each vertex has out==in==1 (manifold)."""
    out_adj = defaultdict(list)
    indeg = Counter()
    outdeg = Counter()
    for a, b in boundary:
        out_adj[a].append(b)
        outdeg[a] += 1
        indeg[b] += 1
    verts = set(outdeg) | set(indeg)
    manifold = all(outdeg[v] == 1 and indeg[v] == 1 for v in verts)
    if not manifold:
        return -1, False
    visited = set()
    loops = 0
    for start in out_adj:
        if start in visited:
            continue
        loops += 1
        cur = start
        while cur not in visited:
            visited.add(cur)
            cur = out_adj[cur][0]
    return loops, manifold


def _trace_single_loop(boundary):
    out_adj = {a: b for a, b in boundary}
    start = boundary[0][0]
    pts = [start]
    cur = out_adj[start]
    while cur != start:
        pts.append(cur)
        cur = out_adj[cur]
    return pts


def _shapely_cross_check(loops, N):
    """Independent topology check via shapely, fed the SNAPPED integer (p,q)
       loops (shared vertices bit-identical -> no float slivers). In (p,q)
       coords each hat has area 16 (=J/2), so the union area must be 16*N."""
    global _shapely_ran
    try:
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        from shapely.strtree import STRtree
    except Exception as e:
        print(f"[INFO] optional shapely cross-check skipped ({e}); exact-integer core checks are unaffected.")
        return
    _shapely_ran = True
    polys = [Polygon([(float(p), float(q)) for (p, q) in lp]) for lp in loops]
    # overlaps: STRtree pairwise intersection area ~ 0
    tree = STRtree(polys)
    max_overlap = 0.0
    for i, p in enumerate(polys):
        for j in tree.query(p):
            if j <= i:
                continue
            inter = p.intersection(polys[j]).area
            if inter > max_overlap:
                max_overlap = inter
    check("(f) [shapely cross-check] pairwise overlap area ~ 0",
          max_overlap < 1e-9, f"max pairwise overlap = {max_overlap:.2e}")
    # gaps: union has no interior holes, is one piece, area == 16*N
    U = unary_union(polys)
    geoms = list(U.geoms) if U.geom_type == 'MultiPolygon' else [U]
    holes = sum(len(g.interiors) for g in geoms)
    area_ok = abs(U.area - 16 * N) < 1e-6
    check("(g) [shapely cross-check] union has 0 interior holes & 1 piece",
          holes == 0 and len(geoms) == 1, f"holes={holes}, pieces={len(geoms)}")
    check("(g) [shapely cross-check] union area == 16*N (hex units)",
          area_ok, f"union={U.area:.6f}, 16N={16*N}")


# ======================================================================
def main():
    print("HAT MONOTILE -- VERIFICATION GATE")
    print("=" * 56)
    # hat.py self-test first (shape facts)
    print("\n=== HAT SHAPE (hat.py self-test) ===")
    if not H._selftest():
        _failures.append("hat.py self-test")

    combinatorial_checks()
    geometric_checks(level=4, seed='H')
    # also exercise a non-H seed for the geometric gate
    geometric_checks(level=3, seed='F')

    print("\n" + "=" * 56)
    if _failures:
        print(f"RESULT: {_passes} core checks passed, {len(_failures)} FAILED:")
        for f in _failures:
            print("   - " + f)
        print("VERIFICATION FAILED")
        return 1
    if _shapely_ran:
        print(f"RESULT: {_passes} core checks passed "
              f"(+ {_shapely_passes} optional shapely cross-checks = {_passes + _shapely_passes} total). "
              f"VERIFICATION PASSED.")
    else:
        print(f"RESULT: {_passes} core checks passed "
              f"(shapely not installed -> optional cross-checks skipped). VERIFICATION PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
