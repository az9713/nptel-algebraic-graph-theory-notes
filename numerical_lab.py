"""Exact and numerical graph checks used by the independent study edition.

Run with Python, NumPy and SymPy. The program performs no network or file writes.
Enumeration is deliberately restricted to small teaching graphs.
"""

# This standalone check uses row probability vectors, unlike chapter 9.
# Its incidence columns use -tail/+head, the reverse orientation of chapter 2;
# BB^T and all orientation-independent checks are unchanged.
from itertools import combinations

import numpy as np
from sympy import Matrix


def adjacency(n, edges):
    """Return a real adjacency matrix of an undirected simple graph."""
    if n < 1:
        raise ValueError('at least one vertex is required')
    result = np.zeros((n, n), dtype=int)
    seen = set()
    for u, v in edges:
        if u == v or not 0 <= u < n or not 0 <= v < n:
            raise ValueError('each edge needs two distinct valid endpoints')
        edge = tuple(sorted((u, v)))
        if edge in seen:
            raise ValueError('duplicate undirected edge')
        seen.add(edge)
        result[u, v] = result[v, u] = 1
    return result


def incidence(n, edges):
    """Orient each supplied edge u->v: -1 at its tail, +1 at its head."""
    adjacency(n, edges)
    result = np.zeros((n, len(edges)), dtype=int)
    for column, (u, v) in enumerate(edges):
        result[u, column], result[v, column] = -1, 1
    return result


def components(n, edges):
    """Count connected components, including isolated vertices."""
    a = adjacency(n, edges)
    unseen = set(range(n))
    count = 0
    while unseen:
        pending = [unseen.pop()]
        while pending:
            u = pending.pop()
            neighbors = {int(v) for v in np.flatnonzero(a[u])} & unseen
            unseen -= neighbors
            pending.extend(neighbors)
        count += 1
    return count


def spanning_trees(n, edges):
    """Enumerate all spanning trees for a small finite simple graph."""
    adjacency(n, edges)
    return [choice for choice in combinations(edges, n - 1)
            if components(n, choice) == 1]


def main():
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (2, 4)]
    n = 5
    a = adjacency(n, edges)
    degree = a.sum(axis=1)
    laplacian = np.diag(degree) - a
    b = incidence(n, edges)
    trees = spanning_trees(n, edges)
    cofactors = [int(Matrix(np.delete(np.delete(laplacian, i, 0), i, 1)).det())
                 for i in range(n)]
    assert np.array_equal(b @ b.T, laplacian)
    assert len(trees) == 8 and cofactors == [8] * n
    assert np.linalg.matrix_rank(b) == n - components(n, edges)
    assert int(np.trace(a @ a)) == 2 * len(edges)
    assert int(np.trace(a @ a @ a)) == 12
    spectrum = np.linalg.eigvalsh(a)
    laplace_spectrum = np.linalg.eigvalsh(laplacian)
    assert abs(np.prod(laplace_spectrum[1:]) / n - len(trees)) < 1e-10
    lazy = (np.eye(n) + a / degree[:, None]) / 2
    stationary = degree / degree.sum()
    assert np.allclose(stationary @ lazy, stationary)
    start = np.eye(n)[4]
    error = 0.5 * np.abs(start @ np.linalg.matrix_power(lazy, 20)
                         - stationary).sum()
    print('vertices=5 edges=6 components=1 cycle_rank=2')
    print('spanning_trees=8 cofactor_counts=[8, 8, 8, 8, 8]')
    print('closed_walks_length_3=12 triangles=2')
    print('adjacency_eigenvalues=' + np.array2string(
        spectrum, precision=6, suppress_small=True))
    print('laplacian_eigenvalues=' + np.array2string(
        laplace_spectrum, precision=6, suppress_small=True))
    print('lazy_walk_stationary=' + np.array2string(stationary, precision=6))
    print(f'lazy_walk_TV_after_20={error:.8f}')
    print('incidence, determinant, spectral and Markov checks: PASS')


if __name__ == '__main__':
    main()
