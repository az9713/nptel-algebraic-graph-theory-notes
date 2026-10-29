"""Switching, cycle invariants and signed spectral equality checks."""

from itertools import combinations, product
import numpy as np
import sympy as s

edges = list(combinations(range(4), 2))
x = s.symbols("x")


def matrix(signs):
    a = s.zeros(4)
    for (u, v), z in zip(edges, signs):
        a[u, v] = a[v, u] = z
    return a


def gauge(signs):
    # Tree edges 01,02,03 are switched positive with root potential +1.
    eta = [1, signs[0], signs[1], signs[2]]
    return tuple(eta[u] * z * eta[v] for (u, v), z in zip(edges, signs))


classes = {}
balanced = anti = 0
for signs in product((-1, 1), repeat=6):
    canonical = gauge(signs)
    classes[canonical] = classes.get(canonical, 0) + 1
    a = matrix(signs)
    d = np.linalg.eigvalsh(np.array(a, dtype=float))
    isbal = all(z == 1 for z in canonical)
    isanti = all(z == 1 for z in gauge(tuple(-v for v in signs)))
    balanced += isbal
    anti += isanti
    assert (abs(d[-1] - 3) < 1e-10) == isbal
    assert (abs(max(abs(d)) - 3) < 1e-10) == (isbal or isanti)
assert len(classes) == 8 and set(classes.values()) == {8}
print(
    f"K4 signatures=64: switching classes={len(classes)}, each "
    f"size=8; balanced={balanced}, antibalanced={anti}"
)
print(
    "All K4 signatures: top-eigenvalue and absolute-radius "
    "equality classifications PASS"
)
a = matrix([-1, 1, 1, 1, 1, 1])
b = matrix([1, -1, 1, 1, 1, 1])
assert a.charpoly(x).as_expr() == b.charpoly(x).as_expr() and gauge(
    [-1, 1, 1, 1, 1, 1]
) != gauge([1, -1, 1, 1, 1, 1])
print("One-negative-edge K4 polynomial:", s.factor(a.charpoly(x).as_expr()))
print(
    "Equal spectra but different fixed-label cycle signs: not "
    "switching equivalent"
)
unsigned = s.ones(4) - s.eye(4)
assert s.trace(unsigned**3) - s.trace(a**3) == 24
print("K4 third-trace deficit=24=4*3*2 negative triangles")
triangle = s.ones(3) - s.eye(3)
negative = -triangle
assert negative.eigenvals() == {s.Integer(-2): 1, s.Integer(1): 2}
print(
    "All-negative triangle: largest eigenvalue 1, absolute "
    "radius 2; unbalanced but antibalanced"
)
# A positive K4 component hides the smaller unbalanced component from the top
# root.
unbalanced = triangle.copy()
unbalanced[0, 1] = unbalanced[1, 0] = -1
block = s.diag(unsigned, unbalanced)
assert max(block.eigenvals()) == 3
print(
    "Disconnected K4 plus unbalanced triangle: signed/unsigned "
    "top root both 3, whole graph unbalanced"
)
# Test explicit diagonal conjugation and a negative square.
d = s.diag(1, -1, 1, -1)
assert d * a * d == matrix(
    [int(d[u, u] * a[u, v] * d[v, v]) for u, v in edges]
)
c = s.zeros(4)
for u, v, z in [(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 0, -1)]:
    c[u, v] = c[v, u] = z
assert s.factor(c.charpoly(x).as_expr()) == (x * x - 2) ** 2
print("Unbalanced C4 polynomial=(x^2-2)^2; radius sqrt(2)<2")
