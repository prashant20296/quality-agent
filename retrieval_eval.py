from retrieval import vector_search, bm25_search, hybrid_search, hybrid_rerank

CASES = [
    ("bubbles and pinholes in the MIG weld bead on a loader frame", {"NCR-2026-001"}),
    ("bearing seat on the shaft came out oversize", {"NCR-2026-002"}),
    ("coating lifting off at the edges, adhesion test failed", {"NCR-2026-003"}),
    ("oil weeping from the hose end fitting under pressure test", {"NCR-2026-004"}),
    ("wheel hub fasteners found under torque in an audit", {"NCR-2026-005"}),
    ("gear teeth too soft, supplier heat treatment problem", {"NCR-2026-006"}),
    ("lack of fusion on axle housing, robot torch angle", {"NCR-2026-007", "NCR-2026-1187"}),
    ("metal burrs left in oil passages caused contamination", {"NCR-2026-008"}),
    ("orange peel and dirt specks on hood top coat", {"NCR-2026-009"}),
    ("dashboard fault from wiring connector not clicked in", {"NCR-2026-010"}),
    ("fuel tank weld leaking, supplier changed parameters", {"NCR-2026-011"}),
    ("steering valve spool stuck, high pressure drop", {"NCR-2026-012"}),
    ("NCR-2026-006", {"NCR-2026-006"}),
    ("PTO drive gear", {"NCR-2026-006"}),
    ("leak", {"NCR-2026-004", "NCR-2026-011"}),
]

MODES = {
    "vector": lambda q: vector_search(q, 10),
    "bm25": lambda q: bm25_search(q, 10),
    "hybrid": lambda q: hybrid_search(q, 10),
    "hybrid+rerank": lambda q: hybrid_rerank(q, k=10, pool=10),
}

def rank_of(ranking, expected):
    for i, id_ in enumerate(ranking, 1):
        if id_ in expected:
            return i
    return None

n = len(CASES)
for name, fn in MODES.items():
    h1 = h3 = 0
    rr = 0.0
    weak = []
    for q, expected in CASES:
        r = rank_of(fn(q), expected)
        h1 += r == 1
        h3 += bool(r and r <= 3)
        rr += (1.0 / r) if r else 0.0
        if r is None or r > 3:
            weak.append((q, r))
    print(f"{name:14} Hit@1 {h1}/{n}   Hit@3 {h3}/{n}   MRR {rr / n:.2f}")
    for q, r in weak:
        print(f"    weak: {q[:55]} -> rank {r}")