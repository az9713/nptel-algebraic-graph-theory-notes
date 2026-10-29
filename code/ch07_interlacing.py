from itertools import combinations
import numpy as np
from sympy import Matrix, sqrt, symbols, expand

A = np.zeros((5, 5))
for i, j in [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2), (2, 4)]:
    A[i, j] = A[j, i] = 1
lam = np.linalg.eigvalsh(A)[::-1]
count = 0
for m in range(1, 5):
    for indices in combinations(range(5), m):
        beta = np.linalg.eigvalsh(A[np.ix_(indices, indices)])[::-1]
        assert np.all(beta <= lam[:m] + 1e-12)
        assert np.all(beta >= lam[5 - m:] - 1e-12)
        count += 1
print(f"All {count} nonempty proper principal subsets interlace")
# An edge deletion is not a principal compression.
cycle = np.zeros((4, 4))
for i, j in [(0, 1), (1, 2), (2, 3), (3, 0)]:
    cycle[i, j] = cycle[j, i] = 1
path = cycle.copy()
path[0, 3] = path[3, 0] = 0
assert np.linalg.eigvalsh(path)[-2] > np.linalg.eigvalsh(cycle)[-2] + 0.6
print("C4 to P4 edge deletion raises the second eigenvalue")
C = np.array([[1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
G = C @ C.T
bound = np.linalg.eigvalsh(G[:2, :2])[-1] + G[2, 2]
assert np.isclose(np.linalg.eigvalsh(G)[-1], 3)
assert 3 <= bound
print(f"PSD block bound: 3.000000 <= {bound:.6f}")
z = symbols("z")
B = Matrix(
    [
        [0, sqrt(2), 1, 0],
        [sqrt(2), 0, sqrt(2), 0],
        [1, sqrt(2), 0, 1],
        [0, 0, 1, 0],
    ]
)
poly = expand(B.charpoly(z).as_expr())
assert poly == z**4 - 6 * z**2 - 4 * z + 2
assert Matrix(A.astype(int)).charpoly(z).as_expr() == expand(z * poly)
H = np.zeros((5, 4))
for col, cell in enumerate([[0], [1, 3], [2], [4]]):
    H[cell, col] = 1
S = H / np.sqrt(H.sum(axis=0))
assert np.allclose(A @ S, S @ np.array(B, dtype=float))
print("Twin quotient polynomial:", poly)
H2 = np.zeros((5, 2))
H2[[0, 1, 2], 0] = 1
H2[[3, 4], 1] = 1
S2 = H2 / np.sqrt(H2.sum(axis=0))
B2 = S2.T @ A @ S2
w, v = np.linalg.eigh(B2)
beta = w[-1]
y = v[:, -1]
res = np.linalg.norm(A @ (S2 @ y) - beta * (S2 @ y))
assert np.isclose(beta, 1 + np.sqrt(2.5))
assert np.min(np.abs(lam - beta)) <= res + 1e-12
assert beta < lam[0]
print(f"Two-cell top Ritz value: {beta:.6f}; lifted residual: {res:.6f}")
print(
    "Principal compression, block bound and exact/approximate "
    "quotient checks passed"
)
