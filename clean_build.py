import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from scipy.sparse import csgraph
from scipy.sparse.linalg import eigsh

def idx(x, y, z, n):
    return x + n * y + n * n * z

def build_cubic_graph(n):
    G = nx.Graph()
    for x in range(n):
        for y in range(n):
            for z in range(n):
                G.add_node(idx(x, y, z, n), pos=(x, y, z))
                if x + 1 < n: G.add_edge(idx(x, y, z, n), idx(x + 1, y, z, n))
                if y + 1 < n: G.add_edge(idx(x, y, z, n), idx(x, y + 1, z, n))
                if z + 1 < n: G.add_edge(idx(x, y, z, n), idx(x, y, z + 1, n))
    return G

def laplacian_eigs(G, k=8):
    A = nx.to_scipy_sparse_array(G, dtype=float)
    L = csgraph.laplacian(A, normed=False)
    vals, vecs = eigsh(L, k=k, which="SM")
    return np.sort(vals)

def pick_two_paths(G, s, d):
    paths = list(nx.node_disjoint_paths(G, s, d))
    if len(paths) >= 2:
        return paths[0], paths[1]
    return nx.shortest_path(G, s, d), nx.shortest_path(G, s, d)

def phase_from_path(path, root):
    return np.pi if root in path else 0.0

def interferometer_signal(P1, P2, root):
    phi1 = phase_from_path(P1, root)
    phi2 = phase_from_path(P2, root)
    tau1 = tau2 = 5.0
    omega, sigma = 8.0, 0.8
    t = np.linspace(0, 12, 500)
    psi1 = np.exp(-((t - tau1)**2)/(2*sigma**2)) * np.exp(1j*(omega*t + phi1))
    psi2 = np.exp(-((t - tau2)**2)/(2*sigma**2)) * np.exp(1j*(omega*t + phi2))
    return np.max(np.abs(psi1 + psi2)**2), phi1, phi2

# MAIN - FIXED INDENTATION
n = 4
G = build_cubic_graph(n)
s, d = idx(0,0,0,n), idx(n-1,n-1,n-1,n)
root = idx(1,2,1,n)

print("Eigenvalues:", np.round(laplacian_eigs(G), 6))

# BASELINE
P1, P2 = pick_two_paths(G, s, d)
Imax_b, phi1_b, phi2_b = interferometer_signal(P1, P2, root)
tri_b = sum(nx.triangles(G).values()) // 3

print("\n=== BASELINE ({} triangles) ===".format(tri_b))
print("Root hits:", root in P1, root in P2)
print("Phases:", phi1_b, phi2_b)
print("Max I:", Imax_b)

# PERTURBED - FIXED SEED
Gp = G.copy()
nodes = list(Gp.nodes())
rng = np.random.default_rng(123)  # FIXED SEED
added = 0
while added < 15:  # 15 edges
    a, b = rng.choice(nodes, 2, replace=False)
    if not Gp.has_edge(a, b) and a != b:
        Gp.add_edge(a, b)
        added += 1

tri_p = sum(nx.triangles(Gp).values()) // 3
P1p, P2p = pick_two_paths(Gp, s, d)
Imax_p, phi1_p, phi2_p = interferometer_signal(P1p, P2p, root)

print("\n=== PERTURBED ({} triangles) ===".format(tri_p))
print("Root hits:", root in P1p, root in P2p)
print("Phases:", phi1_p, phi2_p)
print("Max I:", Imax_p)

print("\nFLIP: {:.1f} → {:.1f} (ΔI={:.1f})".format(Imax_b, Imax_p, abs(Imax_b-Imax_p)))

# PLOT
t = np.linspace(0, 12, 500)
tau, sigma, omega = 5.0, 0.8, 8.0
psi1b = np.exp(-((t-tau)**2)/(2*sigma**2)) * np.exp(1j*(omega*t + phi1_b))
psi2b = np.exp(-((t-tau)**2)/(2*sigma**2)) * np.exp(1j*(omega*t + phi2_b))
Ib = np.abs(psi1b + psi2b)**2

psi1p = np.exp(-((t-tau)**2)/(2*sigma**2)) * np.exp(1j*(omega*t + phi1_p))
psi2p = np.exp(-((t-tau)**2)/(2*sigma**2)) * np.exp(1j*(omega*t + phi2_p))
Ip = np.abs(psi1p + psi2p)**2

plt.figure(figsize=(12,4))
plt.subplot(121); plt.plot(t, Ib, 'b-', lw=2); plt.title('Base I=%.1f'%Imax_b); plt.ylabel('Intensity')
plt.subplot(122); plt.plot(t, Ip, 'r--', lw=2); plt.title('Perturbed I=%.1f'%Imax_p); plt.xlabel('Time')
plt.tight_layout()
plt.show()