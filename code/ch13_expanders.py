"""Finite expansion, lift-spectrum and normalized zig-zag checks."""
from itertools import combinations
from fractions import Fraction
import numpy as np
import sympy as s

def cheeger(a):
    n=len(a);best=None
    for k in range(1,n//2+1):
        for subset in combinations(range(n),k):
            outside=[i for i in range(n) if i not in subset]
            q=Fraction(int(a[np.ix_(subset,outside)].sum()),k)
            if best is None or q<best:best=q
    return best

def cycle(n):
    a=np.zeros((n,n),dtype=int)
    for i in range(n):a[i,(i+1)%n]=a[(i+1)%n,i]=1
    return a
for n in (5,6,9):
    h=cheeger(cycle(n));assert h==Fraction(2,n//2)
    print(f'C{n} exact edge expansion: {h}')
subsets=list(combinations(range(5),2))
p=np.array([[int(set(u).isdisjoint(v)) for v in subsets] for u in subsets])
h=cheeger(p);e=np.linalg.eigvalsh(p);mu=3-e[-2]
assert h==1 and mu/2<=float(h)<=np.sqrt(6*mu)
print('Petersen exact edge expansion 1; gap 2; Cheeger bounds 1 and sqrt(12)')
# K4 lift with every edge crossed is the bipartite double cover, isomorphic to Q3.
a=np.ones((4,4),dtype=int)-np.eye(4,dtype=int);z=np.zeros_like(a)
lift=np.block([[z,a],[a,z]])
x=s.symbols('x')
assert s.expand(s.Matrix(lift).charpoly(x).as_expr()-s.Matrix(a).charpoly(x).as_expr()*s.Matrix(-a).charpoly(x).as_expr())==0
assert sorted(round(v) for v in np.linalg.eigvalsh(lift))==[-3,-1,-1,-1,1,1,1,3]
print('All-crossed K4 lift: exact spectrum {-3,-1^3,1^3,3}; old/new factorization PASS')
# Ports at v are neighbors in increasing order; the rotation reverses the base edge.
neighbors=[[w for w in range(4) if w!=v] for v in range(4)]
r=np.zeros((12,12),dtype=int)
for v in range(4):
    for port,w in enumerate(neighbors[v]):
        back=neighbors[w].index(v);r[3*v+port,3*w+back]=1
assert np.array_equal(r@r,np.eye(12,dtype=int))
hsmall=np.ones((3,3),dtype=int)-np.eye(3,dtype=int)
big=np.kron(np.eye(4,dtype=int),hsmall)
zz=big@r@big
assert np.array_equal(zz,zz.T) and np.all(zz.sum(axis=1)==4)
char=s.factor(s.Matrix(zz).charpoly(x).as_expr())
print('K4 zig-zag C3 adjacency polynomial:',char)
normalized=np.linalg.eigvalsh(zz/4);rho=max(abs(normalized[:-1]))
assert rho<=1/3+1/2+1/4+1e-12
print(f'Zig-zag: 12 vertices, degree 4; normalized nonconstant norm {rho:.9f}')
# Mixing uses oriented counts; with S=T each internal edge contributes twice.
S=np.array([1,1,0,0]);count=int(S@a@S);center=Fraction(3*4,4)
assert count==2 and abs(Fraction(count)-center)<=Fraction(1)
print('K4 S=T={0,1}: oriented count 2, baseline 3, sharp centered bound 1')
