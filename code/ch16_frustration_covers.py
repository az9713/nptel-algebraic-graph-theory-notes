"""Exact signed Laplacian, frustration and cycle-cover certificates."""
from itertools import combinations,permutations,product
from collections import Counter
import sympy as s

edges=list(combinations(range(4),2));n=4

def signed_matrices(signs):
    a=s.zeros(n);h=s.zeros(n,len(edges))
    for j,((u,v),z) in enumerate(zip(edges,signs)):
        a[u,v]=a[v,u]=z;h[u,j]=1;h[v,j]=-z
    return a,3*s.eye(n)-a,h

def balanced_after(signs,removed_vertices=(),removed_edges=()):
    retained=[v for v in range(n) if v not in removed_vertices];eta={}
    for root in retained:
        if root in eta:continue
        eta[root]=1;stack=[root]
        while stack:
            u=stack.pop()
            for j,((a,b),z) in enumerate(zip(edges,signs)):
                if j in removed_edges or a not in retained or b not in retained:continue
                if u not in (a,b):continue
                v=b if u==a else a
                if v in eta:
                    if eta[v]!=eta[u]*z:return False
                else:eta[v]=eta[u]*z;stack.append(v)
    return True
for signs in product((-1,1),repeat=6):
    a,l,h=signed_matrices(signs);assert l==h*h.T
    isbal=balanced_after(signs)
    assert (l.det()==0)==isbal
    frustration=min(sum(z!=eta[u]*eta[v] for (u,v),z in zip(edges,signs))
                    for eta in product((-1,1),repeat=n))
    vertex=min(k for k in range(n+1) if any(balanced_after(signs,removed_vertices=removed)
               for removed in combinations(range(n),k)))
    assert vertex<=frustration
print('All64 K4 signatures: signed incidence Gram/nullity and vertex<=edge frustration PASS')
a,l,h=signed_matrices([-1]*6)
assert l.det()==48 and l.eigenvals()=={s.Integer(6):1,s.Integer(2):3}
minor_squares=Counter(int(h[:,cols].det()**2) for cols in combinations(range(6),4))
assert minor_squares=={0:3,4:12}
print('All-negative K4: Laplacian eigenvalues 2,2,2,6; determinant48=12*4')
print('Unicyclic incidence-minor squares:',dict(sorted(minor_squares.items())))
frustration=min(sum(-1!=eta[u]*eta[v] for u,v in edges) for eta in product((-1,1),repeat=4))
assert frustration==2
print('All-negative K4: edge frustration2, vertex frustration2, smallest eigenvalue2')

def cycle_cover_values(a):
    size=a.rows;det=per=0;covers=0
    for p in permutations(range(size)):
        weight=s.prod(a[i,p[i]] for i in range(size))
        if weight==0:continue
        seen=set();cycles=0
        for i in range(size):
            if i not in seen:
                cycles+=1;j=i
                while j not in seen:seen.add(j);j=p[j]
        det+=(-1)**(size-cycles)*weight;per+=weight;covers+=1
    return s.expand(det),s.expand(per),covers
m=s.Matrix([[2,1,0],[-1,3,4],[5,0,6]])
det,per,covers=cycle_cover_values(m)
assert det==m.det() and per==m.per()
print(f'Directed weighted example: determinant={det}, permanent={per}, nonzero cycle covers={covers}')
k4=s.ones(4)-s.eye(4);det,per,covers=cycle_cover_values(k4)
assert (det,per,covers)==(-3,9,9)
print('Unsigned K4: three matching covers + six directed Hamilton covers; det=-3, per=9')
c4=s.Matrix([[0,1,0,1],[1,0,1,0],[0,1,0,1],[1,0,1,0]])
assert cycle_cover_values(c4)==(0,4,4)
print('Unsigned C4: determinant0 from cancellation; permanent4')
negative_triangle=s.eye(3)-s.ones(3)
assert cycle_cover_values(negative_triangle)==(-2,-2,2)
print('All-negative triangle adjacency: determinant=-2, permanent=-2; not an unsigned count')
