from itertools import combinations

vertices = set(range(5))
edges = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2), (2, 4)]


def connected(choice):
    reached, pending = {0}, [0]
    while pending:
        u = pending.pop()
        for a, b in choice:
            if u not in (a, b):
                continue
            v = b if u == a else a
            if v not in reached:
                reached.add(v)
                pending.append(v)
    return reached == vertices


candidates = list(combinations(edges, len(vertices) - 1))
trees = [choice for choice in candidates if connected(choice)]
assert all((2, 4) in choice for choice in trees)
without_diagonal = [choice for choice in trees if (0, 2) not in choice]
print("candidate subsets:", len(candidates))
print("spanning trees:", len(trees))
print("pendant edge in every tree:", all((2, 4) in t for t in trees))
print("trees without diagonal:", len(without_diagonal))
