from sympy import Matrix, Rational


def incidence(n, edges, unsigned=False):
    matrix = Matrix.zeros(n, len(edges))
    for j, (u, v) in enumerate(edges):
        matrix[u, j] = 1
        matrix[v, j] = 1 if unsigned else -1
    return matrix


edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2), (2, 4)]
b = incidence(5, edges)
u = incidence(5, edges, unsigned=True)
lap = b * b.T
z03 = Matrix([-1, -1, -1, 1, 0, 0])
z02 = Matrix([-1, -1, 0, 0, 1, 0])
cycles = Matrix.hstack(z03, z02)
assert b * cycles == Matrix.zeros(5, 2) and cycles.rank() == 2
assert b.rank() == lap.rank() == 4 and u.rank() == 5
assert len(b.nullspace()) == 2 and len(b.T.nullspace()) == 1

s = Matrix([1, 0, 0, 0, -1])
x = Matrix([Rational(1, 2), Rational(1, 4), 0, Rational(1, 4), -1])
flow = b.T * x
assert lap * x == s and b * flow == s
assert cycles.T * flow == Matrix.zeros(2, 1)
assert flow.dot(flow) == Rational(3, 2)
assert (flow + z03).dot(flow + z03) == Rational(11, 2)

parts = [(0, 1), (1, 2), (0, 2), (3, 4)]
b_parts = incidence(6, parts)
u_parts = incidence(6, parts, unsigned=True)
assert b_parts.rank() == 3 and u_parts.rank() == 4
triangle_u = incidence(3, parts[:3], unsigned=True)
assert abs(triangle_u.det()) == 2
print(
    "running oriented / Laplacian / unsigned ranks:",
    b.rank(),
    lap.rank(),
    u.rank(),
)
print(
    "left / right oriented nullities:",
    len(b.T.nullspace()),
    len(b.nullspace()),
)
print("fundamental cycle basis size:", cycles.rank())
print("minimum-norm flow:", list(flow))
print(
    "minimum / perturbed squared norms:",
    flow.dot(flow),
    "/",
    (flow + z03).dot(flow + z03),
)
print("triangle + edge + isolate ranks:", b_parts.rank(), u_parts.rank())
print("absolute unsigned triangle determinant:", abs(triangle_u.det()))
