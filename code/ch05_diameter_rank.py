from collections import deque
from sympy import Matrix, Symbol, eye, gcd, expand


def adjacency(n, edges):
    a = Matrix.zeros(n)
    for u, v in edges:
        a[u, v] = a[v, u] = 1
    return a


def diameter(a):
    n = a.rows
    largest = 0
    for start in range(n):
        distance = {start: 0}
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in range(n):
                if a[u, v] != 0 and v not in distance:
                    distance[v] = distance[u] + 1
                    queue.append(v)
        assert len(distance) == n
        largest = max(largest, max(distance.values()))
    return largest


edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2), (2, 4)]
a = adjacency(5, edges)
z = Symbol("z")
p = a.charpoly(z).as_expr()
assert gcd(p, p.diff(z)) == 1
assert a**5 - 6 * a**3 - 4 * a**2 + 2 * a == Matrix.zeros(5)
assert diameter(a) == 2 and len(a.eigenvals()) == 5 and a.rank() == 4
for n in range(1, 8):
    path = adjacency(n, [(i, i + 1) for i in range(n - 1)])
    assert diameter(path) == n - 1
    assert path.rank() == n - (n % 2)
for n in range(3, 9):
    cycle = adjacency(n, [(i, (i + 1) % n) for i in range(n)])
    assert diameter(cycle) == n // 2
    assert len(cycle.eigenvals()) == n // 2 + 1
    assert cycle.rank() == n - (2 if n % 4 == 0 else 0)
p, q = 2, 3
bip = adjacency(p + q, [(i, p + j) for i in range(p) for j in range(q)])
assert (
    bip.rank() == 2
    and expand(bip.charpoly(z).as_expr() - z**3 * (z * z - 6)) == 0
)
path3 = adjacency(3, [(0, 1), (1, 2)])
b = Matrix([0, 1, 0])
krylov = Matrix.hstack(b, path3 * b, path3**2 * b)
assert krylov.rank() == 2 and path3**2 * b == 2 * b
signed = Matrix([[0, 1, 0, -1], [1, 0, 1, 0], [0, 1, 0, 1], [-1, 0, 1, 0]])
assert signed * signed == 2 * eye(4)
assert diameter(signed) == 2 and len(signed.eigenvals()) == 2
print(
    "running diameter / distinct eigenvalues / adjacency rank:",
    diameter(a),
    len(a.eigenvals()),
    a.rank(),
)
print("square-free polynomial and fifth-power recurrence: True")
print("paths P1-P7 and cycles C3-C8: all distance/rank checks passed")
print("K2,3 characteristic polynomial:", bip.charpoly(z).as_expr())
print("P3 middle-input Krylov dimension:", krylov.rank())
print(
    "signed-square diameter / distinct eigenvalues:",
    diameter(signed),
    len(signed.eigenvals()),
)
