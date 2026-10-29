import numpy as np
from sympy import Matrix, Rational

edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2), (2, 4)]
A = np.zeros((5, 5))
for i, j in edges:
    A[i, j] = A[j, i] = 1
values, vectors = np.linalg.eigh(A)
rho, p = values[-1], vectors[:, -1]
p *= np.sign(p.sum())
assert np.all(p > 0) and np.linalg.norm(A @ p - rho * p) < 1e-12
exact = Matrix(A.astype(int))
y = Matrix([4, 3, 5, 3, 2])
ratios = [v / y[i] for i, v in enumerate(exact * y)]
assert ratios == [Rational(11, 4), 3, Rational(12, 5), 3, Rational(5, 2)]
assert 2.4 <= rho <= 3
print(f"Running graph radius: {rho:.6f}")
print("Exact trial ratios:", ratios)
print(f"Positive unit Perron vector: {np.round(p, 6).tolist()}")
B = A.copy()
B[1, 3] = B[3, 1] = 1
increase = np.linalg.eigvalsh(B)[-1] - rho
bound = 2 * p[1] * p[3]
assert increase >= bound - 1e-12
print(
    f"Added edge 1-3: increase {increase:.6f}; Rayleigh lower "
    f"bound {bound:.6f}"
)
# Every single-edge deletion is a proper spanning subgraph.
for i, j in edges:
    H = A.copy()
    H[i, j] = H[j, i] = 0
    assert np.linalg.eigvalsh(H)[-1] < rho - 1e-9
print("All six single-edge deletions lower the radius")
# K3 plus an isolate: upper degree equality without global regularity.
D = np.zeros((4, 4))
D[:3, :3] = np.ones((3, 3)) - np.eye(3)
assert np.isclose(np.linalg.eigvalsh(D)[-1], 2)
assert list(D.sum(axis=1)) == [2, 2, 2, 0]
print(
    "Disconnected upper-bound counterexample: radius=Delta=2, "
    "degrees=[2,2,2,0]"
)
# A three-leaf star has radius sqrt(3) and an equally large negative mode.
S = np.zeros((4, 4))
S[0, 1:] = 1
S[1:, 0] = 1
sw, sv = np.linalg.eigh(S)
star_rho = sw[-1]
assert np.isclose(sw[0], -star_rho)
q = np.array([1.0, -1 / np.sqrt(3), -1 / np.sqrt(3), -1 / np.sqrt(3)])
assert np.allclose(S @ q, -star_rho * q)
assert np.allclose(np.linalg.matrix_power(S / star_rho, 4) @ q, q)
assert np.allclose(np.linalg.matrix_power(S / star_rho, 5) @ q, -q)
T = (np.eye(4) + S / star_rho) / 2
assert np.allclose(T @ q, 0)
print(
    "Star: raw powers alternate on the negative mode; averaged "
    "operator kills it"
)
for n in range(2, 8):
    K = np.ones((n, n)) - np.eye(n)
    m = n * (n - 1) // 2
    assert np.isclose(np.linalg.eigvalsh(K)[-1], np.sqrt(2 * m * (n - 1) / n))
print("Complete graphs K2 through K7 attain the edge-count bound")
