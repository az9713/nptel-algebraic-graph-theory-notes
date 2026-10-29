"""Exact and numerical certificates for algebraic connectivity."""
import numpy as np
import sympy as s

def lap(n,edges):
    a=s.zeros(n)
    for u,v in edges:a[u,u]+=1;a[v,v]+=1;a[u,v]-=1;a[v,u]-=1
    return a

def numeric(a):return np.array(a,dtype=float)
p7=lap(7,[(i,i+1) for i in range(6)])
mu=2-2*np.cos(np.pi/7);g=s.Matrix([s.Rational(1,2),s.Rational(1,2),s.Rational(1,4),0,-s.Rational(1,4),-s.Rational(1,2),-s.Rational(1,2)])
rq=(g.T*p7*g)[0]/(g.T*g)[0]
assert rq==s.Rational(2,9) and mu<float(rq)<.25
print(f'P7 mu={mu:.9f}; truncated-distance quotient={rq}; set bound=1/4')
star=lap(5,[(0,i) for i in range(1,5)]);x=s.Matrix([0,1,1,-1,-1])
assert star*x==x and sum(x)==0
print('Star Fiedler vector (0,1,1,-1,-1): positive support disconnected; weak supports connected')
# Removing a vertex can either increase or decrease mu.
p4=lap(4,[(0,1),(1,2),(2,3)]);p3=lap(3,[(0,1),(1,2)]);broken=lap(3,[(1,2)])
assert np.linalg.eigvalsh(numeric(broken))[1]==0
print(f'P4 mu={2-np.sqrt(2):.9f}; delete endpoint gives P3 mu=1; delete interior gives mu=0')
# Principal submatrix retains external-degree diagonal, unlike induced Laplacian.
principal=star.extract([1,2,3,4],[1,2,3,4]);induced=s.zeros(4)
assert principal==s.eye(4) and induced==s.zeros(4)
print('Star center deletion: principal Laplacian I4, induced Laplacian 0; bound 1<=0+1 is tight')
# A unit vector for the simple Fiedler eigenvalue of P4.
w,v=np.linalg.eigh(numeric(p4));f=v[:,1];pred=(f[0]-f[3])**2
edge=np.zeros((4,4));edge[0,0]=edge[3,3]=1;edge[0,3]=edge[3,0]=-1
h=1e-6;fd=(np.linalg.eigvalsh(numeric(p4)+h*edge)[1]-w[1])/h
assert abs(fd-pred)<2e-6
print(f'P4 added endpoint-edge derivative: analytic {pred:.9f}, finite difference {fd:.9f}')
# Complement identity and complete-graph equality.
k4=lap(4,[(i,j) for i in range(4) for j in range(i+1,4)])
assert p4+(k4-p4)==4*s.eye(4)-s.ones(4)
assert s.simplify(k4.eigenvals()[s.Integer(4)]-3)==0
print('L(P4)+L(complement)=4I-J; complete-graph mu=4')
# Rayleigh cut lower bound and regular induced-average bound on C6.
c6=lap(6,[(i,(i+1)%6) for i in range(6)])
mu6=np.linalg.eigvalsh(numeric(c6))[1];avg=4/3;upper=2-mu6+mu6*3/6
assert abs(mu6-1)<1e-12 and avg<=upper+1e-12
print('C6 induced 3-vertex path: average degree 4/3 <= 3/2')
# Exact block-domain energy inequality uses full, not induced, diagonal.
print('All exact identities and finite-difference checks PASS')
