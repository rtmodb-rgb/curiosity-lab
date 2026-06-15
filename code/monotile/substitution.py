"""
substitution.py  --  The hat metatile substitution system (H, T, P, F)
                     and a generator of finite hat tilings ("supertiles").

Computational Curiosity Lab #3.

PORTED / ADAPTED (BSD-3-Clause) from Craig S. Kaplan's `hatviz`
(https://github.com/isohedral/hatviz, file hat.js):
    * the four base metatiles H_init / T_init / P_init / F_init,
    * constructPatch()  -- assemble a 29-tile patch from the 4 metatiles,
    * constructMetatiles() -- carve the patch into the next-level H,T,P,F.
We did NOT re-derive the metatile placement transforms from prose; getting
those right is the crux, so we lean on the authoritative source.

THE FOUR METATILES (clusters of hats):
    H  irregular hexagon, 4 hats (exactly ONE reflected -- the only place
       reflected hats live), T  triangle, 1 hat,  P  parallelogram, 2 hats,
       F  pentagon, 2 hats.

THE SUBSTITUTION MATRIX  (column = input metatile, row = output counts),
order [H, T, P, F]:
        from H  from T  from P  from F
   H  [   3       1       2       2  ]
   T  [   1       0       0       0  ]
   P  [   3       0       1       1  ]
   F  [   3       0       2       3  ]
This numeric matrix is per Adam P. Goucher / cp4space
(https://cp4space.hatsya.com/2023/03/21/aperiodic-monotile/); its
EIGEN-STRUCTURE is verified independently in verify.py (dominant eigenvalue
= phi^4 = (7+3 sqrt5)/2; charpoly (x-1)(x+1)(x^2-7x+1); Perron eigenvector
(1/3, 7/6-sqrt5/2, sqrt5-2, 3/2-sqrt5/2)).  CRUCIALLY, M is here REALIZED by
counting children by type in the actual geometric substitution (see
realized_matrix()), so we never just assert it.

IMPORTANT CAVEAT (do not misuse): the supertiles are NOT geometrically
similar to the metatiles at finite levels (except T).  This is a faithful
combinatorial+geometric substitution, not a naive self-similar inflation.
"""

import math
from hat import (HR3, IDENT, mul, trot, ttrans, rot_about, trans_pt, padd,
                 psub, match_two, intersect, det2, HAT_OUTLINE)

# Canonical metatile order used everywhere.
ORDER = ['H', 'T', 'P', 'F']
HATS_PER_METATILE = {'H': 4, 'T': 1, 'P': 2, 'F': 2}   # leaf hats per base metatile

# Reference substitution matrix M (per cp4space; eigen-structure verified).
M_REFERENCE = [
    [3, 1, 2, 2],   # H row
    [1, 0, 0, 0],   # T row
    [3, 0, 1, 1],   # P row
    [3, 0, 2, 3],   # F row
]


# ======================================================================
# Scene graph (mirrors hatviz: HatTile leaves, MetaTile groups).
# ======================================================================
class HatTile:
    """A single hat leaf, labelled by which metatile-interior it came from.
       Labels: 'H' (unreflected hat in an H metatile), 'H1' (the reflected
       hat in an H metatile), 'T', 'P', 'F'."""
    def __init__(self, label):
        self.label = label

    kind = 'hat'


class MetaTile:
    """A cluster: an outline `shape` plus transformed children."""
    kind = 'meta'

    def __init__(self, shape, width):
        self.shape = list(shape)
        self.width = width
        self.children = []   # list of {'T': transform, 'geom': HatTile|MetaTile}

    def add_child(self, T, geom):
        self.children.append({'T': T, 'geom': geom})

    def eval_child(self, n, i):
        ch = self.children[n]
        return trans_pt(ch['T'], ch['geom'].shape[i])

    def recentre(self):
        cx = sum(p[0] for p in self.shape) / len(self.shape)
        cy = sum(p[1] for p in self.shape) / len(self.shape)
        self.shape = [padd(p, (-cx, -cy)) for p in self.shape]
        Mt = ttrans(-cx, -cy)
        for ch in self.children:
            ch['T'] = mul(Mt, ch['T'])


# Shared hat-leaf singletons (their labels carry the metatile type / reflection).
_H1 = HatTile('H1')   # the single reflected hat
_H = HatTile('H')
_T = HatTile('T')
_P = HatTile('P')
_F = HatTile('F')


def base_metatiles():
    """The four level-1 metatiles (fresh objects each call)."""
    ho = HAT_OUTLINE

    # H : irregular hexagon, 3 unreflected hats + 1 reflected (H1)
    H_outline = [(0, 0), (4, 0), (4.5, HR3),
                 (2.5, 5 * HR3), (1.5, 5 * HR3), (-0.5, HR3)]
    H = MetaTile(H_outline, 2)
    H.add_child(match_two(ho[5], ho[7], H_outline[5], H_outline[0]), _H)
    H.add_child(match_two(ho[9], ho[11], H_outline[1], H_outline[2]), _H)
    H.add_child(match_two(ho[5], ho[7], H_outline[3], H_outline[4]), _H)
    H.add_child(mul(ttrans(2.5, HR3),
                    mul([-0.5, -HR3, 0, HR3, -0.5, 0],
                        [0.5, 0, 0, 0, -0.5, 0])), _H1)   # reflection (det<0)

    # T : triangle, 1 hat
    T_outline = [(0, 0), (3, 0), (1.5, 3 * HR3)]
    T = MetaTile(T_outline, 2)
    T.add_child([0.5, 0, 0.5, 0, 0.5, HR3], _T)

    # P : parallelogram, 2 hats
    P_outline = [(0, 0), (4, 0), (3, 2 * HR3), (-1, 2 * HR3)]
    P = MetaTile(P_outline, 2)
    P.add_child([0.5, 0, 1.5, 0, 0.5, HR3], _P)
    P.add_child(mul(ttrans(0, 2 * HR3),
                    mul([0.5, HR3, 0, -HR3, 0.5, 0],
                        [0.5, 0.0, 0.0, 0.0, 0.5, 0.0])), _P)

    # F : pentagon, 2 hats
    F_outline = [(0, 0), (3, 0), (3.5, HR3), (3, 2 * HR3), (-1, 2 * HR3)]
    F = MetaTile(F_outline, 2)
    F.add_child([0.5, 0, 1.5, 0, 0.5, HR3], _F)
    F.add_child(mul(ttrans(0, 2 * HR3),
                    mul([0.5, HR3, 0, -HR3, 0.5, 0],
                        [0.5, 0.0, 0.0, 0.0, 0.5, 0.0])), _F)
    return [H, T, P, F]


# ----------------------------------------------------------------------
# The substitution: build a patch, then carve the next-level metatiles.
# (constructPatch / constructMetatiles, ported from hatviz hat.js.)
# ----------------------------------------------------------------------
_PATCH_RULES = [
    ['H'],
    [0, 0, 'P', 2], [1, 0, 'H', 2], [2, 0, 'P', 2], [3, 0, 'H', 2],
    [4, 4, 'P', 2], [0, 4, 'F', 3], [2, 4, 'F', 3], [4, 1, 3, 2, 'F', 0],
    [8, 3, 'H', 0], [9, 2, 'P', 0], [10, 2, 'H', 0], [11, 4, 'P', 2],
    [12, 0, 'H', 2], [13, 0, 'F', 3], [14, 2, 'F', 1], [15, 3, 'H', 4],
    [8, 2, 'F', 1], [17, 3, 'H', 0], [18, 2, 'P', 0], [19, 2, 'H', 2],
    [20, 4, 'F', 3], [20, 0, 'P', 2], [22, 0, 'H', 2], [23, 4, 'F', 3],
    [23, 0, 'F', 3], [16, 0, 'P', 2], [9, 4, 0, 2, 'T', 2], [4, 0, 'F', 3],
]

# Which patch children become each next-level metatile (the substitution).
_KEEP = {
    'H': [0, 9, 16, 27, 26, 6, 1, 8, 10, 15],
    'T': [11],
    'P': [7, 2, 3, 4, 28],
    'F': [21, 20, 22, 23, 24, 25],
}


def construct_patch(H, T, P, F):
    shapes = {'H': H, 'T': T, 'P': P, 'F': F}
    ret = MetaTile([], H.width)
    for r in _PATCH_RULES:
        if len(r) == 1:
            ret.add_child(IDENT, shapes[r[0]])
        elif len(r) == 4:
            poly = ret.children[r[0]]['geom'].shape
            Tm = ret.children[r[0]]['T']
            P_ = trans_pt(Tm, poly[(r[1] + 1) % len(poly)])
            Q = trans_pt(Tm, poly[r[1]])
            nshp = shapes[r[2]]; npoly = nshp.shape
            ret.add_child(match_two(npoly[r[3]], npoly[(r[3] + 1) % len(npoly)], P_, Q), nshp)
        else:
            chP = ret.children[r[0]]; chQ = ret.children[r[2]]
            P_ = trans_pt(chQ['T'], chQ['geom'].shape[r[3]])
            Q = trans_pt(chP['T'], chP['geom'].shape[r[1]])
            nshp = shapes[r[4]]; npoly = nshp.shape
            ret.add_child(match_two(npoly[r[5]], npoly[(r[5] + 1) % len(npoly)], P_, Q), nshp)
    return ret


def construct_metatiles(patch):
    bps1 = patch.eval_child(8, 2)
    bps2 = patch.eval_child(21, 2)
    rbps = trans_pt(rot_about(bps1, -2.0 * math.pi / 3.0), bps2)
    p72 = patch.eval_child(7, 2)
    p252 = patch.eval_child(25, 2)
    llc = intersect(bps1, rbps, patch.eval_child(6, 2), p72)
    w = psub(patch.eval_child(6, 2), llc)

    nH = [llc, bps1]
    w = trans_pt(trot(-math.pi / 3), w); nH.append(padd(nH[1], w))
    nH.append(patch.eval_child(14, 2))
    w = trans_pt(trot(-math.pi / 3), w); nH.append(psub(nH[3], w))
    nH.append(patch.eval_child(6, 2))
    new_H = MetaTile(nH, patch.width * 2)
    for c in _KEEP['H']:
        new_H.add_child(patch.children[c]['T'], patch.children[c]['geom'])

    nP = [p72, padd(p72, psub(bps1, llc)), bps1, llc]
    new_P = MetaTile(nP, patch.width * 2)
    for c in _KEEP['P']:
        new_P.add_child(patch.children[c]['T'], patch.children[c]['geom'])

    nF = [bps2, patch.eval_child(24, 2), patch.eval_child(25, 0),
          p252, padd(p252, psub(llc, bps1))]
    new_F = MetaTile(nF, patch.width * 2)
    for c in _KEEP['F']:
        new_F.add_child(patch.children[c]['T'], patch.children[c]['geom'])

    AAA = nH[2]
    BBB = padd(nH[1], psub(nH[4], nH[5]))
    CCC = trans_pt(rot_about(BBB, -math.pi / 3), AAA)
    new_T = MetaTile([BBB, CCC, AAA], patch.width * 2)
    new_T.add_child(patch.children[11]['T'], patch.children[11]['geom'])

    for m in (new_H, new_P, new_F, new_T):
        m.recentre()
    return [new_H, new_T, new_P, new_F]   # order H, T, P, F


# ----------------------------------------------------------------------
# Public API.
# ----------------------------------------------------------------------
# Global scale 2: with this, EVERY placed hat vertex lands exactly on the
# integer triangular (hex) lattice, and each placed hat is congruent to the
# canonical HAT_OUTLINE up to a rigid motion (verified in verify.py).
GLOBAL_SCALE = [2, 0, 0, 0, 2, 0]


def metatiles_at_level(level):
    """The 4 metatiles [H,T,P,F] at the given level (level 1 = base)."""
    if level < 1:
        raise ValueError("level must be >= 1")
    tiles = base_metatiles()
    for _ in range(level - 1):
        tiles = construct_metatiles(construct_patch(*tiles))
    return tiles


def _orientation_deg(Mt):
    """Rotation angle (deg) of the transform's linear part, applied to +x."""
    return round(math.degrees(math.atan2(Mt[3], Mt[0])), 4)


def enum_hats(meta, transform=None):
    """Recurse a metatile tree, returning placed hats as records:
       {vertices, reflected, orientation, mtype}.
       mtype in {'H','T','P','F'} = which metatile the hat belongs to."""
    if transform is None:
        transform = GLOBAL_SCALE
    out = []

    def rec(g, Mt):
        if g.kind == 'hat':
            verts = [trans_pt(Mt, p) for p in HAT_OUTLINE]
            mtype = 'H' if g.label in ('H', 'H1') else g.label
            out.append({
                'vertices': verts,
                'reflected': det2(Mt) < 0,
                'orientation': _orientation_deg(Mt),
                'mtype': mtype,
                'label': g.label,
            })
        else:
            for ch in g.children:
                rec(ch['geom'], mul(Mt, ch['T']))

    rec(meta, transform)
    return out


def patch(level, seed='H'):
    """A finite hat tiling: all hats inside the level-`level` `seed` supertile.
       Returns a list of records (see enum_hats). seed in {'H','T','P','F'}."""
    idx = ORDER.index(seed)
    return enum_hats(metatiles_at_level(level)[idx])


def metatile_tree_counts(level, seed='H'):
    """Realized count of BASE (level-1) metatiles by type inside a level-`level`
       seed supertile, derived purely from the geometric tree (via hat labels).
       Returns dict {'H','T','P','F': int}.  Should equal M^(level-1) e_seed."""
    hats = patch(level, seed)
    from collections import Counter
    c = Counter(h['label'] for h in hats)
    nH1 = c.get('H1', 0)
    # consistency: each base H metatile has 1 H1 + 3 H; P,F have 2 hats each.
    assert c.get('H', 0) == 3 * nH1, "H/H1 ratio broken"
    assert c.get('P', 0) % 2 == 0 and c.get('F', 0) % 2 == 0, "P/F parity broken"
    return {'H': nH1, 'T': c.get('T', 0), 'P': c.get('P', 0) // 2, 'F': c.get('F', 0) // 2}


def realized_matrix():
    """Build the substitution matrix by COUNTING children-by-type in the actual
       geometric substitution (one step from the base metatiles). Returns a
       4x4 list in [H,T,P,F] order (column = input metatile)."""
    base = base_metatiles()
    patch_ = construct_patch(*base)
    # type of each patch child = which base metatile its geom is.
    ident_of = {id(base[i]): ORDER[i] for i in range(4)}
    child_type = [ident_of[id(ch['geom'])] for ch in patch_.children]
    Mr = [[0, 0, 0, 0] for _ in range(4)]   # rows H,T,P,F ; cols H,T,P,F
    ri = {t: i for i, t in enumerate(ORDER)}
    for col, out_type in enumerate(ORDER):
        for child_idx in _KEEP[out_type]:
            produced = child_type[child_idx]
            Mr[ri[produced]][col] += 1
    return Mr


if __name__ == "__main__":
    Mr = realized_matrix()
    print("Realized substitution matrix (rows/cols = H,T,P,F):")
    for row in Mr:
        print("  ", row)
    print("matches reference M:", Mr == M_REFERENCE)
    for L in range(1, 5):
        hats = patch(L, 'H')
        nref = sum(h['reflected'] for h in hats)
        print(f"level {L} (H seed): {len(hats)} hats, {nref} reflected, "
              f"base-metatile counts {metatile_tree_counts(L, 'H')}")
