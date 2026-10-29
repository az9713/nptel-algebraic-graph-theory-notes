from itertools import combinations
import sympy as sp


def adjacency(n, edges):
    A = sp.zeros(n)
    for u, v in edges:
        A[u, v] = A[v, u] = 1
    return A


def srg_parameters(A):
    n = A.rows
    degrees = list(A * sp.ones(n, 1))
    if len(set(degrees)) != 1 or not 0 < degrees[0] < n - 1:
        return None
    A2 = A * A
    adjacent = {A2[i, j] for i in range(n) for j in range(i + 1, n) if A[i, j]}
    nonadjacent = {
        A2[i, j] for i in range(n) for j in range(i + 1, n) if not A[i, j]
    }
    if len(adjacent) != 1 or len(nonadjacent) != 1:
        return None
    return n, degrees[0], adjacent.pop(), nonadjacent.pop()


def independence(A):
    best = ()
    for k in range(A.rows + 1):
        for S in combinations(range(A.rows), k):
            if all(A[i, j] == 0 for i, j in combinations(S, 2)):
                best = S
    return best


z = sp.Symbol("z")
C5 = adjacency(5, [(i, (i + 1) % 5) for i in range(5)])
C6 = adjacency(6, [(i, (i + 1) % 6) for i in range(6)])
pairs = list(combinations(range(5), 2))
P = adjacency(
    10,
    [
        (i, j)
        for i, j in combinations(range(10), 2)
        if set(pairs[i]).isdisjoint(pairs[j])
    ],
)
cells = list((i, j) for i in range(3) for j in range(3))
R = adjacency(
    9,
    [
        (i, j)
        for i, j in combinations(range(9), 2)
        if cells[i][0] == cells[j][0] or cells[i][1] == cells[j][1]
    ],
)
for name, A in [("C5", C5), ("Petersen", P), ("3x3 rook", R)]:
    n, d, a, b = srg_parameters(A)
    assert A * A == (d - b) * sp.eye(n) + (a - b) * A + b * sp.ones(n)
    assert d * (d - a - 1) == (n - d - 1) * b
    size = len(independence(A))
    print(f"{name}: parameters {(n, d, a, b)}, independence {size}")
print(
    "Petersen characteristic polynomial:", sp.factor(P.charpoly(z).as_expr())
)
S = [i for i, pair in enumerate(pairs) if 0 in pair]
assert len(S) == 4 and all(P[i, j] == 0 for i, j in combinations(S, 2))
y = sp.Matrix([int(i in S) - sp.Rational(2, 5) for i in range(10)])
assert P * y == -2 * y
assert all(sum(P[i, j] for j in S) == 2 for i in range(10) if i not in S)
print(
    "Petersen Hoffman equality: four-vertex witness; outside neighbor count 2"
)
assert srg_parameters(C6) is None
D = sp.diag(C5, C5)
assert len(D.eigenvals()) == 3 and srg_parameters(D) is None
print(
    "C6 is not strongly regular; two disjoint C5 have three "
    "distinct roots but are not SRG"
)
# Candidate parameters pass edge, triangle and two-distance double counts.
n, d, a, b = 10, 6, 2, 6
assert n * d % 2 == 0 and n * d * a % 6 == 0
assert d * (d - a - 1) == (n - d - 1) * b
r, s = 0, -4
f = sp.Rational(-d - (n - 1) * s, r - s)
g = n - 1 - f
assert (f, g) == (sp.Rational(15, 2), sp.Rational(3, 2))
print(f"Impossible candidate (10,6,2,6): multiplicities {f}, {g}")
# Three triangles share one hub; no edges connect distinct outer pairs.
F = adjacency(7, [(0, i) for i in range(1, 7)] + [(1, 2), (3, 4), (5, 6)])
deg = list(F * sp.ones(7, 1))
assert F * F == sp.diag(*deg) + sp.ones(7) - sp.eye(7)
assert deg == [6, 2, 2, 2, 2, 2, 2]
print("Friendship windmill: degrees", deg)
print(
    "Friendship windmill characteristic polynomial:",
    sp.factor(F.charpoly(z).as_expr()),
)
