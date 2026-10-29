import numpy as np

edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2), (2, 4)]
M = np.zeros((5, 5))
for u, v in edges:
    M[u, v] = M[v, u] = 1.0
d = M.sum(axis=0)
pi = d / d.sum()
s = np.sqrt(d)
W = M / d[None, :]
N = M / s[:, None] / s[None, :]
assert np.allclose(W.sum(axis=0), 1)
assert np.allclose(W @ pi, pi)
assert np.allclose(W * pi[None, :], (W * pi[None, :]).T)
assert np.allclose(W, s[:, None] * N / s[None, :])
lam = np.linalg.eigvalsh(N)[::-1]
print('degrees:', d.astype(int).tolist())
print('stationary:', np.round(pi, 6).tolist())
print('normalized spectrum:', np.round(lam, 6).tolist())
alpha = 0.5
K = alpha*np.eye(5) + (1-alpha)*W
mu = alpha + (1-alpha)*lam
r = max(abs(mu[1:]))
start = 4
p = np.eye(5)[:, start]
for t in range(41):
    err = p-pi
    point_bound = np.sqrt(d/d[start])*r**t*np.sqrt((1-pi)*(1-pi[start]))
    assert np.all(abs(err) <= point_bound + 2e-14)
    l2 = np.sqrt(np.sum(err**2/pi))
    l2_bound = r**t*np.sqrt(1/pi[start]-1)
    tv = 0.5*np.sum(abs(err))
    assert l2 <= l2_bound+2e-13
    assert tv <= 0.5*l2_bound+2e-13
    if t in (0, 5, 20):
        print(f't={t}: TV={tv:.8f}, TV bound={0.5*l2_bound:.8f}')
    p = K@p
# An edge alternates without laziness; half laziness mixes in one step.
E = np.array([[0., 1.], [1., 0.]])
assert np.allclose(np.linalg.matrix_power(E, 2), np.eye(2))
assert np.allclose((np.eye(2)+E)/2, np.ones((2, 2))/2)
# Three equal-degree vertices: the optimum alpha=1/3 gives J/3.
T = (np.ones((3, 3))-np.eye(3))/2
assert np.allclose(np.eye(3)/3 + 2*T/3, np.ones((3, 3))/3)
# C5 has a negative mode with larger modulus than lambda2.
C = np.zeros((5, 5))
for i in range(5):
    C[i, (i+1)%5] = C[(i+1)%5, i] = 1
cl = np.linalg.eigvalsh(C/2)[::-1]
aopt = -(cl[1]+cl[-1])/(2-cl[1]-cl[-1])
ropt = max(abs(aopt+(1-aopt)*cl[1:]))
print(f'C5: lambda2={cl[1]:.8f}, lambda_min={cl[-1]:.8f}')
print(f'C5: alpha_opt={aopt:.8f}, modulus={ropt:.8f}')
assert np.isclose(aopt, 0.2) and np.isclose(ropt, 1/np.sqrt(5))
# Exact symmetric similarity is structural; these checks use finite tolerance.
