from itertools import combinations, permutations, product
import sympy as sp


def adjacency(n, edges):
    A = sp.zeros(n)
    for u, v in edges:
        A[u, v] = A[v, u] = 1
    return A


def laplacian(A):
    return sp.diag(*list(A*sp.ones(A.rows, 1)))-A


def polynomial(A):
    return tuple(A.charpoly().all_coeffs())


def canonical(A):
    pairs = list(combinations(range(A.rows), 2))
    return min(tuple(A[p[i], p[j]] for i, j in pairs)
               for p in permutations(range(A.rows)))


z = sp.Symbol('z')
star = adjacency(5, [(0, i) for i in range(1, 5)])
cycle4plus = adjacency(5, [(0, 1), (1, 2), (2, 3), (0, 3)])
assert polynomial(star) == polynomial(cycle4plus)
assert polynomial(laplacian(star)) != polynomial(laplacian(cycle4plus))
print('Five-vertex adjacency pair:', sp.factor(star.charpoly(z).as_expr()))
# All labeled simple graphs on one through four vertices; no graph-library oracle.
counts = []
for n in range(1, 5):
    edges = list(combinations(range(n), 2))
    spectra = {}
    classes = set()
    for mask in range(1 << len(edges)):
        A = adjacency(n, [e for k, e in enumerate(edges) if mask >> k & 1])
        key, iso = polynomial(A), canonical(A)
        assert key not in spectra or spectra[key] == iso
        spectra[key] = iso
        classes.add(iso)
    counts.append(len(classes))
print('Orders 1..4: distinct isomorphism classes and spectra:', counts)
G = adjacency(6, [(0,2),(0,5),(1,3),(1,4),(2,3),(3,4),(3,5)])
H = adjacency(6, [(0,2),(1,2),(1,3),(1,4),(2,5),(3,5),(4,5)])
assert polynomial(laplacian(G)) == polynomial(laplacian(H))
assert sp.trace(G**3) == 6 and sp.trace(H**3) == 0
print('Six-vertex Laplacian pair:', sp.factor(laplacian(G).charpoly(z).as_expr()))
# A star and triangle+isolate share the same signless spectrum via their line graph.
T = adjacency(4, [(0,1),(1,2),(0,2)])
U = adjacency(4, [(0,i) for i in range(1,4)])
Q = lambda A: sp.diag(*list(A*sp.ones(A.rows,1)))+A
assert polynomial(Q(T)) == polynomial(Q(U))
print('Signless pair:', sp.factor(Q(T).charpoly(z).as_expr()))
# Exact seven-vertex Godsil-McKay certificate, X={0,1,2,3}.
B = adjacency(7, [(0,4),(1,4),(0,5),(2,5),(0,6),(3,6)])
reflection = sp.diag(sp.ones(4)/2-sp.eye(4), sp.eye(3))
Bs = reflection*B*reflection
assert reflection**2 == sp.eye(7)
assert all(x in (0,1) for x in Bs) and all(Bs[i,i] == 0 for i in range(7))
assert polynomial(B) == polynomial(Bs)
assert polynomial(sp.ones(7)-sp.eye(7)-B) == polynomial(sp.ones(7)-sp.eye(7)-Bs)
print('GM degree lists:', sorted(B*sp.ones(7,1)), sorted(Bs*sp.ones(7,1)))
# Cartesian rook graph and switching on its four diagonal cells.
V = list(product(range(4), repeat=2))
R = adjacency(16, [(i,j) for i,j in combinations(range(16),2)
                   if V[i][0] == V[j][0] or V[i][1] == V[j][1]])
X = [i for i,v in enumerate(V) if v[0] == v[1]]
F = sp.eye(16)
for i in X:
    for j in X:
        F[i,j] = sp.Rational(1,2)-int(i==j)
S = F*R*F
assert polynomial(S) == polynomial(R)
expected = (z-6)*(z-2)**6*(z+2)**9
assert sp.expand(R.charpoly(z).as_expr()-expected) == 0
# Each switched neighborhood is a connected 6-cycle: degree2 and no triangle,
# with six vertices, rules out any disconnected simple2-regular alternative.
for i in range(16):
    N = [j for j in range(16) if S[i,j]]
    local = S.extract(N,N)
    assert len(N) == 6 and local*sp.ones(6,1) == 2*sp.ones(6,1)
    assert sp.trace(local**3) == 0
assert any(all(R[i,j] for i,j in combinations(C,2)) for C in combinations(range(16),4))
assert not any(all(S[i,j] for i,j in combinations(C,2)) for C in combinations(range(16),4))
print('Rook/Shrikhande polynomial:', sp.factor(expected))
# Explicit isomorphism to Cayley(Z4 x Z4, +/-e1,+/-e2,+/-(e1+e2)).
generators = {(1,0),(3,0),(0,1),(0,3),(1,1),(3,3)}
C = adjacency(16, [(i,j) for i,j in combinations(range(16),2)
                   if ((V[j][0]-V[i][0])%4,(V[j][1]-V[i][1])%4) in generators])
f = [0,7,6,11,13,10,1,12,14,3,8,15,9,4,5,2]
assert sorted(f) == list(range(16))
assert all(S[i,j] == C[f[i],f[j]] for i in range(16) for j in range(16))
print('Rook/Shrikhande clique numbers: 4 / 3; explicit Cayley isomorphism PASS')
for n in range(2,9):
    P = adjacency(n, [(i,i+1) for i in range(n-1)])
    assert sp.trace(P**4) == 6*n-10
claw = adjacency(4, [(0,i) for i in range(1,4)])
p4 = adjacency(4, [(i,i+1) for i in range(3)])
assert sp.trace(claw**4)-sp.trace(p4**4) == 4
print('Path fourth moments n=2..8 and single-branch difference4: PASS')
