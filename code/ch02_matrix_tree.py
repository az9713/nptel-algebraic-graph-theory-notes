from itertools import combinations, permutations
from sympy import Matrix, symbols, expand

n = 5
edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2), (2, 4)]
b = Matrix.zeros(n, len(edges))
l_direct = Matrix.zeros(n)
for j, (u, v) in enumerate(edges):
    b[u, j], b[v, j] = 1, -1
    l_direct[u, u] += 1
    l_direct[v, v] += 1
    l_direct[u, v] -= 1
    l_direct[v, u] -= 1
lap = b * b.T
assert lap == l_direct


def connected(indices):
    reached = {0}
    while True:
        enlarged = set(reached)
        for j in indices:
            u, v = edges[j]
            if u in reached or v in reached:
                enlarged.update((u, v))
        if enlarged == reached:
            return len(reached) == n
        reached = enlarged


reduced = b.copy()
reduced.row_del(2)
values = []
for choice in combinations(range(len(edges)), n - 1):
    value = int(reduced[:, choice].det())
    assert value in (-1, 0, 1)
    assert (value != 0) == connected(choice)
    values.append(value)
cofactors = [
    int((-1) ** (i + j) * lap.minor_submatrix(i, j).det())
    for i in range(n)
    for j in range(n)
]
assert set(cofactors) == {8}
reversed_b = b.copy()
reversed_b[:, 0] = -reversed_b[:, 0]
assert reversed_b * reversed_b.T == lap

t, ell = symbols("t ell")
weights = Matrix.diag(1, 1, 1, 1, t, ell)
weighted = b * weights * b.T
partition = expand(weighted.minor_submatrix(2, 2).det())
assert expand(partition - 4 * ell * (1 + t)) == 0
match = Matrix([[1, 1, 0], [1, 1, 1], [0, 1, 1]])
permanent = sum(
    match[0, p[0]] * match[1, p[1]] * match[2, p[2]]
    for p in permutations(range(3))
)
assert permanent == 3 and match.det() == -1
print("candidate edge sets:", len(values))
print("zero minors:", values.count(0))
print("sum of squared minors:", sum(v * v for v in values))
print("all signed cofactors:", sorted(set(cofactors)))
print("orientation reversal preserves L:", reversed_b * reversed_b.T == lap)
print("weighted partition:", partition)
print("matching determinant / permanent:", match.det(), "/", permanent)
