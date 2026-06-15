"""
hat.py  --  The aperiodic monotile "the hat" (Smith, Myers, Kaplan,
            Goodman-Strauss, 2023) as exact geometry, plus its 8-kite
            decomposition.

Computational Curiosity Lab #3.  Brand ethos: compute, don't assert;
verify every headline number two independent ways; be honest about caveats.

THE HAT
-------
The hat is Tile(1, sqrt(3)) -- NOT Tile(1,1) (that is the equilateral
"spectre" base, a common confusion).  It is a 13-sided non-convex polygon,
the union of 8 kites of the [3.4.6.4] Laves / deltoidal-trihexagonal
("kisrhombille") grid.  Its edges have length 1 ("a"-edges) and sqrt(3)
("b"-edges), with one "a"-edge doubled to length 2.

GEOMETRY SOURCE (ported / adapted, BSD-3-Clause):
    Craig S. Kaplan, "hatviz", https://github.com/isohedral/hatviz
    (geometry.js: the affine helpers and `hat_outline`).
    See also the hat app https://cs.uwaterloo.ca/~csk/hat/app.html .
We adopt hatviz's `hat_outline` verbatim as the authoritative 13-gon and do
NOT re-derive the polygon from prose.  The 8-kite overlay below was found
computationally (kisrhombille kites, hexagon side 2) and verified to union
exactly to that 13-gon (see `verify.py` / self-test).

Numbers (area, vertex count, Tile(1,sqrt3)) are confirmed two independent
ways in verify.py.
"""

import math

# ---- constants (match hatviz geometry.js exactly so core.js can mirror) ----
R3 = 1.7320508075688772      # sqrt(3)
HR3 = 0.8660254037844386     # sqrt(3)/2

# ======================================================================
# Affine algebra.  A transform is a 6-list [a,b,c, d,e,f] meaning the
# 2x3 matrix [[a,b,c],[d,e,f]]; it acts on a point (x,y) as
#     (a*x + b*y + c,  d*x + e*y + f).
# Points are plain (x, y) tuples.  This mirrors hatviz/geometry.js.
# ======================================================================
IDENT = [1, 0, 0, 0, 1, 0]


def hexpt(x, y):
    """Triangular-lattice point: integer (x,y) -> Cartesian. hexPt in hatviz."""
    return (x + 0.5 * y, HR3 * y)


def mul(A, B):
    """Compose affine transforms (A after B)."""
    return [A[0]*B[0] + A[1]*B[3],
            A[0]*B[1] + A[1]*B[4],
            A[0]*B[2] + A[1]*B[5] + A[2],
            A[3]*B[0] + A[4]*B[3],
            A[3]*B[1] + A[4]*B[4],
            A[3]*B[2] + A[4]*B[5] + A[5]]


def inv(T):
    det = T[0]*T[4] - T[1]*T[3]
    return [T[4]/det, -T[1]/det, (T[1]*T[5] - T[2]*T[4])/det,
            -T[3]/det, T[0]/det, (T[2]*T[3] - T[0]*T[5])/det]


def trot(ang):
    c = math.cos(ang); s = math.sin(ang)
    return [c, -s, 0, s, c, 0]


def ttrans(tx, ty):
    return [1, 0, tx, 0, 1, ty]


def rot_about(p, ang):
    return mul(ttrans(p[0], p[1]), mul(trot(ang), ttrans(-p[0], -p[1])))


def trans_pt(M, P):
    return (M[0]*P[0] + M[1]*P[1] + M[2], M[3]*P[0] + M[4]*P[1] + M[5])


def padd(p, q):
    return (p[0] + q[0], p[1] + q[1])


def psub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def match_seg(p, q):
    """Spiral similarity sending the unit interval to segment p->q (det>0)."""
    return [q[0]-p[0], p[1]-q[1], p[0], q[1]-p[1], q[0]-p[0], p[1]]


def match_two(p1, q1, p2, q2):
    """Similarity sending segment p1->q1 to p2->q2 (no reflection)."""
    return mul(match_seg(p2, q2), inv(match_seg(p1, q1)))


def intersect(p1, q1, p2, q2):
    d = (q2[1]-p2[1])*(q1[0]-p1[0]) - (q2[0]-p2[0])*(q1[1]-p1[1])
    uA = ((q2[0]-p2[0])*(p1[1]-p2[1]) - (q2[1]-p2[1])*(p1[0]-p2[0])) / d
    return (p1[0] + uA*(q1[0]-p1[0]), p1[1] + uA*(q1[1]-p1[1]))


def det2(M):
    """Determinant of the linear part of an affine transform."""
    return M[0]*M[4] - M[1]*M[3]


# ======================================================================
# The hat: authoritative 13-gon (hatviz geometry.js `hat_outline`).
# Vertices given in integer triangular-lattice (hex) coordinates, then
# mapped to Cartesian.  All 13 vertices lie on the unit triangular lattice.
# ======================================================================
HAT_HEX = [(0, 0), (-1, -1), (0, -2), (2, -2), (2, -1), (4, -2), (5, -1),
           (4, 0), (3, 0), (2, 2), (0, 3), (0, 2), (-1, 2)]
HAT_OUTLINE = [hexpt(x, y) for (x, y) in HAT_HEX]   # 13 Cartesian vertices

# ----------------------------------------------------------------------
# The 8-kite decomposition (found computationally; kisrhombille kites of a
# side-2 hexagon grid). Each kite = [hexagon-center, midpoint, vertex,
# midpoint] in integer hex coordinates; area = sqrt(3); union = the hat.
# Hexagon centers touched by the hat: (0,0) [4 kites], (2,2) [2], (4,-2) [2].
# ----------------------------------------------------------------------
HAT_KITES_HEX = [
    [(0, 0), (2, -1), (2, 0), (1, 1)],
    [(0, 0), (1, 1), (0, 2), (-1, 2)],
    [(0, 0), (-1, -1), (0, -2), (1, -2)],
    [(0, 0), (1, -2), (2, -2), (2, -1)],
    [(2, 2), (0, 3), (0, 2), (1, 1)],
    [(2, 2), (1, 1), (2, 0), (3, 0)],
    [(4, -2), (5, -1), (4, 0), (3, 0)],
    [(4, -2), (3, 0), (2, 0), (2, -1)],
]


def hat_kites_cartesian():
    """The 8 kites as lists of Cartesian vertices."""
    return [[hexpt(x, y) for (x, y) in kite] for kite in HAT_KITES_HEX]


# ----------------------------------------------------------------------
# Geometry utilities used by verify / figures.
# ----------------------------------------------------------------------
def shoelace_signed(poly):
    """Signed polygon area (shoelace). Positive iff vertices are CCW."""
    n = len(poly)
    s = 0.0
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return s * 0.5


def shoelace_area(poly):
    """Unsigned polygon area."""
    return abs(shoelace_signed(poly))


def edge_length_multiset(poly, ndigits=6):
    n = len(poly)
    out = []
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        out.append(round(math.hypot(x1 - x0, y1 - y0), ndigits))
    return sorted(out)


def turning_sequence(poly, ndigits=4):
    """Signed exterior turning angles (degrees) at each vertex."""
    n = len(poly)
    out = []
    for i in range(n):
        a = psub(poly[i], poly[(i - 1) % n])
        b = psub(poly[(i + 1) % n], poly[i])
        cr = a[0]*b[1] - a[1]*b[0]
        dt = a[0]*b[0] + a[1]*b[1]
        out.append(round(math.degrees(math.atan2(cr, dt)), ndigits))
    return out


def hat_area():
    return shoelace_area(HAT_OUTLINE)


# ----------------------------------------------------------------------
# Self-test (run `python3 hat.py`): the headline facts about the hat,
# each checked two independent ways where possible.
# ----------------------------------------------------------------------
def _selftest():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    # 1) vertex / edge count = 13
    check("hat has 13 vertices/edges", len(HAT_OUTLINE) == 13,
          f"n={len(HAT_OUTLINE)}")

    # 2) area = 8*sqrt(3), two ways: shoelace of the 13-gon and 8 * kite area
    A = hat_area()
    kites = hat_kites_cartesian()
    kite_area_sum = sum(shoelace_area(k) for k in kites)
    check("area = 8*sqrt(3) via shoelace", abs(A - 8 * R3) < 1e-9,
          f"A={A:.9f}, 8sqrt3={8*R3:.9f}")
    check("area = sum of 8 kite areas", abs(A - kite_area_sum) < 1e-9,
          f"sum_kites={kite_area_sum:.9f}")
    check("each kite area = sqrt(3)",
          all(abs(shoelace_area(k) - R3) < 1e-9 for k in kites),
          f"kite0={shoelace_area(kites[0]):.6f}")
    check("area = 32 unit-triangles (32*sqrt3/4)", abs(A - 32 * (R3 / 4)) < 1e-9)

    # 3) Tile(1, sqrt3): edges are length 1 (one doubled to 2) and sqrt(3)
    lens = edge_length_multiset(HAT_OUTLINE)
    from collections import Counter
    c = Counter(lens)
    check("edges are {1 (x6), sqrt3 (x6), 2 (x1)} -> Tile(1,sqrt3)",
          c.get(1.0, 0) == 6 and c.get(round(R3, 6), 0) == 6 and c.get(2.0, 0) == 1,
          f"{dict(c)}")

    # 4) turning angles sum to 360 (simple closed CCW polygon)
    ts = turning_sequence(HAT_OUTLINE)
    check("turning angles sum to 360 deg", abs(sum(ts) - 360.0) < 1e-6,
          f"sum={sum(ts):.4f}")

    # 5) kite overlay equals the hat (shapely if available; else area+containment)
    try:
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        HP = Polygon(HAT_OUTLINE)
        U = unary_union([Polygon(k) for k in kites])
        symdiff = U.symmetric_difference(HP).area
        check("8 kites union == hat (shapely symmetric diff ~ 0)",
              symdiff < 1e-9, f"symdiff={symdiff:.2e}")
    except Exception as e:  # pragma: no cover
        check("8 kites union == hat (shapely unavailable -> area only)",
              abs(kite_area_sum - A) < 1e-9, f"(shapely skipped: {e})")

    print("\nHAT SELF-TEST:", "ALL PASS" if ok else "FAILURES ABOVE")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if _selftest() else 1)
