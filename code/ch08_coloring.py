from itertools import combinations, product
import numpy as np
from sympy import Matrix, Rational, symbols


def graph(n, edges):
    A = np.zeros((n, n), dtype=int)
    for i, j in edges:
        A[i, j] = A[j, i] = 1
    return A


def exact_parameters(A):
    n = len(A)
    alpha = omega = 1
    for r in range(1, n + 1):
        for S in combinations(range(n), r):
            values = [A[i, j] for i, j in combinations(S, 2)]
            if not any(values):
                alpha = max(alpha, r)
            if all(values):
                omega = max(omega, r)
    edges = [(i, j) for i in range(n) for j in range(i) if A[i, j]]
    for k in range(1, n + 1):
        if any(
            all(c[i] != c[j] for i, j in edges)
            for c in product(range(k), repeat=n)
        ):
            return k, omega, alpha


def inertia(M):
    w = np.linalg.eigvalsh(M)
    return int(sum(w > 1e-9)), int(sum(w < -1e-9)), int(sum(abs(w) <= 1e-9))


A = graph(5, [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2), (2, 4)])
C5 = graph(5, [(i, (i + 1) % 5) for i in range(5)])
star = graph(10, [(0, i) for i in range(1, 10)])
K4 = np.ones((4, 4), dtype=int) - np.eye(4, dtype=int)
K23 = graph(5, [(i, j) for i in range(2) for j in range(2, 5)])
# Avoid enumerating color assignments for the ten-vertex star: its two parts
# are exact witnesses.
examples = [("running", A), ("C5", C5), ("K4", K4), ("K2,3", K23)]
for name, M in examples:
    chi, clique, alpha = exact_parameters(M)
    w = np.linalg.eigvalsh(M)
    rho, least = w[-1], w[0]
    pos, neg, zero = inertia(M)
    assert chi + 1e-10 >= 1 - rho / least
    assert chi <= 1 + rho + 1e-10 and clique <= 1 + rho + 1e-10
    assert alpha <= zero + min(pos, neg)
    print(
        f"{name}: chi={chi}, clique={clique}, alpha={alpha}; "
        f"inertia={pos}/{neg}/{zero}"
    )
assert np.isclose(np.linalg.eigvalsh(star)[-1], 3)
print("K1,9: explicit two-part coloring uses 2; spectral upper endpoint is 4")
z = symbols("z")
q = z**4 - 6 * z**2 - 4 * z + 2
assert Matrix(A).charpoly(z).as_expr().expand() == (z * q).expand()
points = [-2, Rational(-3, 2), -1, 0, Rational(1, 2), 2, 3]
expected = [2, Rational(-7, 16), 1, 2, Rational(-23, 16), -14, 17]
assert [q.subs(z, t) for t in points] == expected
print(
    "Exact quartic signs certify two positive, two negative and "
    "one zero adjacency mode"
)
triangle = np.ones((3, 3), dtype=int) - np.eye(3, dtype=int)
D = np.zeros((8, 8), dtype=int)
D[:3, :3] = triangle
D[3:, 3:] = C5
W = D.copy()
W[3:, 3:] *= -1
assert inertia(D) == (4, 4, 0) and inertia(W) == (3, 5, 0)
assert exact_parameters(D)[2] == 3
print(
    "K3 disjoint C5: ordinary inertia bound 4; signed-block "
    "bound 3; exact alpha 3"
)
print(
    "All finite coloring, clique, independence and "
    "signed-pattern checks passed"
)
