from itertools import combinations
import numpy as np
from sympy import Matrix, prod, Rational

edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2), (2, 4)]
n, m = 5, len(edges)
a, d = Matrix.zeros(n), Matrix.zeros(n)
neighbours = [[] for _ in range(n)]
for u, v in edges:
    a[u, v] = a[v, u] = 1
    d[u, u] += 1
    d[v, v] += 1
    neighbours[u].append(v)
    neighbours[v].append(u)
lap = d - a
counts = [1, 0, 0, 0, 0]
for _ in range(8):
    counts = [sum(counts[u] for u in neighbours[v]) for v in range(n)]
assert counts == list((a**8)[0, :])
triangles = int((a**3).trace() / 6)
wedges = sum(len(row) * (len(row) - 1) // 2 for row in neighbours)
four_cycles = int(((a**4).trace() - 2 * m - 4 * wedges) / 8)
assert triangles == 2 and four_cycles == 1
coefficients = a.charpoly().all_coeffs()
for k in range(n + 1):
    minor_sum = sum(a.extract(s, s).det() for s in combinations(range(n), k))
    assert coefficients[k] == (-1) ** k * minor_sum
vectors = [
    Matrix(v)
    for v in [
        (1, 1, 1, 1, 1),
        (-1, -1, 0, -1, 3),
        (0, -1, 0, 1, 0),
        (-2, 1, 0, 1, 0),
        (1, 1, -4, 1, 1),
    ]
]
spectrum = [0, 1, 2, 4, 5]
for i, vector in enumerate(vectors):
    assert lap * vector == spectrum[i] * vector
    assert all(vector.dot(vectors[j]) == 0 for j in range(i))
trees = Rational(prod(spectrum[1:]), n)
assert trees == lap.minor_submatrix(2, 2).det() == 8
real_a = np.array(a, dtype=float)
values, q = np.linalg.eigh(real_a)
residual = np.max(np.abs(real_a @ q - q @ np.diag(values)))
reconstruction = q @ np.diag(values**8) @ q.T
spectral_check = residual < 1e-12 and np.allclose(
    reconstruction, np.array(a**8, dtype=float), rtol=0, atol=1e-8
)
assert spectral_check
print("eight-step endpoint counts from 0:", counts)
print("trace A2 / A3 / A4:", (a**2).trace(), (a**3).trace(), (a**4).trace())
print("triangles / four-cycles:", triangles, "/", four_cycles)
print("all principal-minor coefficient checks: True")
print("exact Laplacian spectrum:", spectrum)
print("spectral tree count:", trees)
print(
    "approximate spectral reconstruction and residual checks:",
    bool(spectral_check),
)
