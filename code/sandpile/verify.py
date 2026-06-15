"""
Independent verification of the claims featured in the explorable.
Run: python3 verify.py
"""
import numpy as np
import sandpile as sp


def hr(t): print("\n" + "=" * 64 + f"\n{t}\n" + "=" * 64)


# 1) ABELIAN PROPERTY -------------------------------------------------
hr("1) Abelian property: final config & total topplings are order-independent")
rng = np.random.default_rng(42)
h0 = rng.integers(0, 13, size=(6, 6))          # random unstable config
first  = sp.stabilize_serial(h0, lambda u: u[0])
last   = sp.stabilize_serial(h0, lambda u: u[-1])
def randpick(u):
    return u[int(np.random.default_rng(len(u)).integers(len(u)))]
randp  = sp.stabilize_serial(h0, randpick)
par, par_t = sp.stabilize(h0)
print("row-major order : total topples =", first[1])
print("reverse order   : total topples =", last[1])
print("random order    : total topples =", randp[1])
print("parallel        : total topples =", par_t)
ok = (np.array_equal(first[0], last[0]) and np.array_equal(first[0], randp[0])
      and np.array_equal(first[0], par) and first[1] == last[1] == randp[1] == par_t)
print("ALL identical (config + count)? ->", ok)

# 2) IDENTITY ELEMENT -------------------------------------------------
hr("2) Sandpile-group identity element")
for n in (4, 8, 64):
    e = sp.identity(n)
    ee, _ = sp.stabilize(e + e)
    idempotent = np.array_equal(ee, e)
    rec = sp.is_recurrent(e)
    all3 = np.full((n, n), 3, dtype=np.int64)
    acts = np.array_equal(sp.stabilize(all3 + e)[0], all3)  # e + (recurrent) == that recurrent
    print(f"n={n:3d}: idempotent(e⊕e==e)={idempotent}  recurrent(e)={rec}  "
          f"e acts as identity on max-stable={acts}")

# 3) #RECURRENT == #SPANNING TREES (Matrix-Tree) ----------------------
hr("3) #recurrent configs (brute force)  ==  #spanning trees (det reduced Laplacian)")
for n in (1, 2, 3):
    bf = sp.count_recurrent_bruteforce(n)
    st = sp.spanning_trees(n)
    print(f"n={n}: brute-force recurrent={bf:>8d}   spanning-trees(det)={st:>8d}   match={bf==st}")
print("\nGroup order (=#recurrent=#spanning trees) for larger n:")
for n in (4, 5, 6, 10, 20):
    print(f"  n={n:2d}: {sp.spanning_trees(n)}")

# 4) AVALANCHE STATS (quick sanity) -----------------------------------
hr("4) Driven sandpile avalanche stats (quick sanity, n=64)")
sizes, areas = sp.run_avalanches(64, 20000, seed=1, drop="random", warmup=5000)
nz = sizes[sizes > 0]
print(f"drops measured={len(sizes)}  fraction with topplings={len(nz)/len(sizes):.3f}")
print(f"avalanche size: mean={sizes.mean():.1f}  max={sizes.max()}  "
      f"99.9th pct={np.percentile(sizes,99.9):.0f}")
print(f"area:           mean={areas.mean():.1f}  max={areas.max()}")
print("(heavy tail expected; exponent/'true power law' analyzed separately & soberly)")
