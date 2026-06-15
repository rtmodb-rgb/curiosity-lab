"""
Abelian sandpile model on the n x n grid graph (boundary = sink; chips that
fall off the edge are lost). Threshold = 4 for every site.

Core routines used by the Curiosity Lab explorable. Everything here is meant
to be independently re-runnable and checkable by the critic.
"""
import numpy as np


# ----------------------------------------------------------------------
# Fast parallel ("abelian") stabilization with numpy.
# By the abelian property the final stable config is order-independent, so we
# may topple every overloaded site as many times as currently possible each
# round. This converges quickly.
# ----------------------------------------------------------------------
def stabilize(h):
    """Return (stable_config, total_topplings)."""
    h = h.astype(np.int64).copy()
    total = 0
    while True:
        t = h >> 2                      # how many times each site topples now = h // 4
        s = int(t.sum())
        if s == 0:
            break
        total += s
        h -= 4 * t
        h[:-1, :] += t[1:, :]           # chips going up   (i,j) -> (i-1,j)
        h[1:, :]  += t[:-1, :]          # down
        h[:, :-1] += t[:, 1:]           # left
        h[:, 1:]  += t[:, :-1]          # right
    return h, total


def stabilize_measure(h):
    """Return (stable_config, total_topplings, area) where area = #distinct
    sites that toppled at least once (the avalanche 'footprint')."""
    h = h.astype(np.int64).copy()
    total = 0
    toppled = np.zeros(h.shape, dtype=bool)
    while True:
        t = h >> 2
        s = int(t.sum())
        if s == 0:
            break
        total += s
        toppled |= (t > 0)
        h -= 4 * t
        h[:-1, :] += t[1:, :]
        h[1:, :]  += t[:-1, :]
        h[:, :-1] += t[:, 1:]
        h[:, 1:]  += t[:, :-1]
    return h, total, int(toppled.sum())


# ----------------------------------------------------------------------
# Serial stabilization (topple ONE site at a time) — used only to DEMONSTRATE
# the abelian property: different toppling orders give the identical result.
# ----------------------------------------------------------------------
def stabilize_serial(h, picker):
    """picker(list_of_unstable_(i,j)) -> chosen (i,j). Returns (stable, total)."""
    h = h.astype(np.int64).copy()
    n, m = h.shape
    total = 0
    while True:
        unstable = list(zip(*np.where(h >= 4)))
        if not unstable:
            break
        i, j = picker(unstable)
        h[i, j] -= 4
        for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < n and 0 <= nj < m:
                h[ni, nj] += 1
        total += 1
    return h, total


# ----------------------------------------------------------------------
# Sandpile-group identity element  (the famous fractal).
# Recipe: e = stabilize( 2*max - stabilize(2*max) ),  max = all 3's  => 2*max = all 6's.
# ----------------------------------------------------------------------
def identity(n):
    six = np.full((n, n), 6, dtype=np.int64)
    s, _ = stabilize(six)
    diff = six - s
    e, _ = stabilize(diff)
    return e


# ----------------------------------------------------------------------
# Recurrence test via Dhar's "sink firing" (burning test, algebraic form).
# b(v) = number of edges from v to the sink (corner 2, edge 1, interior 0).
# A stable config c is recurrent  <=>  stabilize(c + b) == c.
# ----------------------------------------------------------------------
def sink_vector(n):
    b = np.zeros((n, n), dtype=np.int64)
    b[0, :]  += 1
    b[-1, :] += 1
    b[:, 0]  += 1
    b[:, -1] += 1
    return b


def is_recurrent(c, b=None):
    if b is None:
        b = sink_vector(c.shape[0])
    res, _ = stabilize(c + b)
    return np.array_equal(res, c)


def count_recurrent_bruteforce(n):
    """Enumerate all 4^(n*n) stable configs and count recurrent ones. Tiny n only."""
    b = sink_vector(n)
    cells = n * n
    cnt = 0
    for code in range(4 ** cells):
        flat = np.empty(cells, dtype=np.int64)
        x = code
        for k in range(cells):
            flat[k] = x & 3
            x >>= 2
        c = flat.reshape(n, n)
        if is_recurrent(c, b):
            cnt += 1
    return cnt


# ----------------------------------------------------------------------
# Spanning trees of the grid+sink graph via Matrix-Tree theorem:
# number of spanning trees = det(reduced Laplacian) = order of sandpile group.
# Reduced Laplacian: diagonal 4 (degree incl. sink edges), -1 for grid neighbors.
# ----------------------------------------------------------------------
def reduced_laplacian(n, dtype=np.float64):
    """Reduced Laplacian as a numpy array (handy for display / teaching only).

    WARNING: do NOT take its determinant with numpy (np.linalg.det / slogdet) for
    n >= 6. float64 carries only ~15-16 significant digits while the group order is
    far larger, so the result is silently corrupted past ~digit 15. For the exact
    count use spanning_trees(n), which runs the integer Bareiss routine below.
    """
    cells = n * n
    L = np.zeros((cells, cells), dtype=dtype)
    idx = lambda i, j: i * n + j
    for i in range(n):
        for j in range(n):
            v = idx(i, j)
            L[v, v] = 4
            for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < n and 0 <= nj < n:
                    L[v, idx(ni, nj)] -= 1
    return L


def _reduced_laplacian_int(n):
    """Reduced Laplacian as a list-of-lists of python ints (arbitrary precision)."""
    cells = n * n
    M = [[0] * cells for _ in range(cells)]
    idx = lambda i, j: i * n + j
    for i in range(n):
        for j in range(n):
            v = idx(i, j)
            M[v][v] = 4
            for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < n and 0 <= nj < n:
                    M[v][idx(ni, nj)] -= 1
    return M


def _det_bareiss_exact(M):
    """Fraction-free Bareiss determinant on an integer matrix. EXACT (python ints).

    NOTE: we deliberately do NOT use numpy float det / slogdet here: the sandpile
    group order grows astronomically (the 20x20 value is a 207-digit integer) and
    float64 only carries ~15-16 significant digits, so slogdet silently corrupts
    every digit past ~the 15th. Bareiss keeps everything in exact integers; we also
    assert each division is exact (a property guaranteed by Sylvester's identity).
    """
    M = [row[:] for row in M]
    N = len(M)
    prev, sign = 1, 1
    for k in range(N - 1):
        if M[k][k] == 0:
            s = next((i for i in range(k + 1, N) if M[i][k] != 0), -1)
            if s < 0:
                return 0
            M[k], M[s] = M[s], M[k]
            sign = -sign
        pk = M[k][k]
        for i in range(k + 1, N):
            mik = M[i][k]
            for j in range(k + 1, N):
                num = M[i][j] * pk - mik * M[k][j]
                q, r = divmod(num, prev)
                assert r == 0, "Bareiss division not exact (numerical bug)"
                M[i][j] = q
        prev = pk
    return sign * M[N - 1][N - 1]


def spanning_trees(n):
    """Exact order of the sandpile group = #spanning trees = det(reduced Laplacian)."""
    return _det_bareiss_exact(_reduced_laplacian_int(n))


# ----------------------------------------------------------------------
# Driven sandpile -> avalanche statistics (self-organized criticality).
# ----------------------------------------------------------------------
def run_avalanches(n, n_drops, seed=0, drop="random", warmup=0):
    rng = np.random.default_rng(seed)
    h = np.zeros((n, n), dtype=np.int64)
    sizes, areas = [], []
    c = n // 2
    for k in range(n_drops):
        if drop == "center":
            i = j = c
        else:
            i = int(rng.integers(n)); j = int(rng.integers(n))
        h[i, j] += 1
        h, topples, area = stabilize_measure(h)
        if k >= warmup:
            sizes.append(topples); areas.append(area)
    return np.array(sizes), np.array(areas)


def single_source(n, chips):
    """Drop `chips` grains at the center of an n x n grid and stabilize."""
    h = np.zeros((n, n), dtype=np.int64)
    h[n // 2, n // 2] = chips
    h, total = stabilize(h)
    return h, total
