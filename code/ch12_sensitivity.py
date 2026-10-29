"""Exact finite checks for signed cubes and Boolean sensitivity."""

from itertools import combinations
from math import comb
import numpy as np


def signed_cube(n):
    a = np.array([[0, 1], [1, 0]], dtype=np.int64)
    for _ in range(2, n + 1):
        eye = np.eye(len(a), dtype=np.int64)
        a = np.block([[a, eye], [eye, -a]])
    return a


for n in range(1, 7):
    a = signed_cube(n)
    size = 1 << n
    assert np.array_equal(a @ a, n * np.eye(size, dtype=np.int64))
    assert np.trace(a) == 0
    assert all(
        (abs(int(a[x, y])) == 1) == ((x ^ y).bit_count() == 1)
        for x in range(size)
        for y in range(size)
    )
print("Signed cube identities and exact supports: n=1..6 PASS")
for n in (2, 3, 4):
    a = abs(signed_cube(n))
    k = (1 << (n - 1)) + 1
    minimum = n
    witness = None
    count = 0
    for subset in combinations(range(1 << n), k):
        delta = int(a[np.ix_(subset, subset)].sum(axis=1).max())
        count += 1
        if delta < minimum:
            minimum, witness = delta, subset
    assert minimum * minimum >= n
    print(
        f"Q{n}: {count} subsets of size {k}; minimum maximum-degree {minimum}"
    )
    if n == 4:
        print("Q4 degree-two witness:", witness)


def paired_or(x, m):
    width = 2 * m
    mask = (1 << width) - 1
    for block in range(m):
        z = (x >> (width * block)) & mask
        if any(z == (3 << (2 * j)) for j in range(m)):
            return 1
    return 0


m = 2
n = 2 * m * m
values = [paired_or(x, m) for x in range(1 << n)]
s = max(
    sum(values[x] != values[x ^ (1 << j)] for j in range(n))
    for x in range(1 << n)
)
coeff = [(-1 if value else 1) for value in values]
step = 1
while step < len(coeff):
    for start in range(0, len(coeff), 2 * step):
        for j in range(start, start + step):
            u, v = coeff[j], coeff[j + step]
            coeff[j], coeff[j + step] = u + v, u - v
    step *= 2
degree = max(i.bit_count() for i, c in enumerate(coeff) if c)
assert s == 4 and degree == 8 and degree <= s * s
print(
    f"Paired-OR m=2: exhaustive sensitivity {s}; exact Fourier degree {degree}"
)
m = 3
blocks = [3 << (2 * m * b + 2 * j) for b in range(m) for j in range(m)]
assert all(paired_or(mask, m) == 1 for mask in blocks)
assert all(a & b == 0 for a, b in combinations(blocks, 2))
assert paired_or(0, m) == 0
print(
    "Paired-OR m=3: 9 disjoint sensitive pairs at zero; analytic sensitivity 6"
)


# Exact integer Fourier arithmetic for AND of two ORs on disjoint two-bit
# groups.
def and_or(x):
    return int(bool(x & 3) and bool(x & 12))


s = max(
    sum(and_or(x) != and_or(x ^ (1 << j)) for j in range(4)) for x in range(16)
)
c = [1 - 2 * and_or(x) for x in range(16)]
for step in (1, 2, 4, 8):
    for start in range(0, 16, 2 * step):
        for j in range(start, start + step):
            u, v = c[j], c[j + step]
            c[j], c[j + step] = u + v, u - v
assert s == 2 and c[15] != 0
print(
    "AND-of-two-ORs: sensitivity 2 and degree 4, attaining "
    "degree=sensitivity^2"
)
