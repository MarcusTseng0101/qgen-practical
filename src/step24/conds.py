"""Step 24 (specs/step24_robustness.md §2): the four departures from step 23's ideal setting."""
from __future__ import annotations

import numpy as np

from src.step1.bits import fwht, popcount
from src.step23 import grid as Gd

N_DROP = 2                      # spec §2: couplers missing from the model's graph
ETA = {"noise02": 0.02, "noise05": 0.05}
CONDS = ("miss", "extra", "noise02", "noise05")

DIAGS = [(P[0], P[3]) for P in Gd.PLAQS] + [(P[1], P[2]) for P in Gd.PLAQS]   # 18 plaquette diagonals
DIAG_MASKS = np.array([Gd._mask(d) for d in DIAGS], dtype=np.int64)


def dropped_edges(seed: int) -> list[tuple[int, int]]:
    idx = np.random.default_rng(20_000 + seed).choice(len(Gd.EDGES), N_DROP, replace=False)
    return [Gd.EDGES[i] for i in sorted(idx)]


def _remove(masks: np.ndarray, edges) -> np.ndarray:
    """Drop each edge, every plaquette containing it, every triple containing both endpoints."""
    bad = set()
    for a, b in edges:
        e = (1 << a) | (1 << b)
        for m in masks.tolist():
            if (m & e) == e and popcount(np.array([m]))[0] in (2, 3, 4):
                bad.add(m)
    return np.array([m for m in masks.tolist() if m not in bad], dtype=np.int64)


def model_masks(cond: str, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """(iqp candidates, me_local masks) for a condition."""
    if cond == "miss":
        d = dropped_edges(seed)
        return _remove(Gd.LOCAL_GENS, d), _remove(Gd.LOCAL_ME, d)
    if cond == "extra":
        return (np.array(sorted(set(Gd.LOCAL_GENS.tolist()) | set(DIAG_MASKS.tolist())), dtype=np.int64),
                np.array(sorted(set(Gd.LOCAL_ME.tolist()) | set(DIAG_MASKS.tolist())), dtype=np.int64))
    return Gd.LOCAL_GENS, Gd.LOCAL_ME


def readout_channel(p: np.ndarray, eta: float) -> np.ndarray:
    """Independent bit flips with prob eta: f_S -> (1 - 2 eta)^|S| f_S."""
    f = fwht(np.asarray(p, dtype=np.float64))
    f = f * (1.0 - 2.0 * eta) ** popcount(np.arange(len(p)))
    q = fwht(f) / len(p)
    return np.clip(q, 0.0, None) / np.clip(q, 0.0, None).sum()


def mitigate(fhat: np.ndarray, ops: np.ndarray, eta: float) -> np.ndarray:
    return fhat / (1.0 - 2.0 * eta) ** popcount(np.asarray(ops, dtype=np.int64))


def data_dist(cond: str, seed: int) -> np.ndarray:
    p = Gd.grid_iqp(seed)
    return readout_channel(p, ETA[cond]) if cond in ETA else p
