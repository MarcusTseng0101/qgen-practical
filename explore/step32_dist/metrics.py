"""Step 32 analysis: distribution-level metrics from the saved fits in out2/*.npz (exploration, spent seeds).

Metrics, all exact at n = 16 (the target p is known):
  tvd       0.5 * sum |p - q|                       best-possible single-sample distinguishing advantage
  kl        sum p log(p/q)                          excess held-out log-loss; punishes dropped modes
  fid       (sum sqrt(p q))^2                        classical (Bhattacharyya) fidelity
  E_k       mean over |S| = k of (f_S(p) - f_S(q))^2 per-order parity error, k = 1..16 (via Walsh transform)
  G         mean of E_4, E_5, E_6                   the paper's completion gap (check)
  G_hi      mean of E_7 .. E_16                     orders the paper never scored
  mmd_s     Gaussian-kernel MMD^2 with bandwidth s; equals sum_k C(n,k) a^(n-k) b^k E_k,
            a = (1+c)/2, b = (1-c)/2, c = exp(-1/(2 s^2))   (the metric of Recio-Armengol et al.)

python -m explore.step32_dist.metrics
"""
from __future__ import annotations

import json
from math import comb
from pathlib import Path

import numpy as np

OUT = Path("explore/step32_dist/out2")
N = 16
SIGMAS = (0.5, 1.0, 2.0)
POP = np.array([bin(m).count("1") for m in range(1 << N)])


def walsh(v):
    """f_S = sum_x v(x) (-1)^{S.x} for all masks S (fast Walsh-Hadamard transform)."""
    a = np.array(v, float).copy()
    h = 1
    while h < a.size:
        a = a.reshape(-1, 2 * h)
        x, y = a[:, :h].copy(), a[:, h:].copy()
        a[:, :h], a[:, h:] = x + y, x - y
        a = a.reshape(-1)
        h *= 2
    return a


def metrics(p, q):
    q = np.clip(q, 1e-300, None)
    q = q / q.sum()
    m = p > 0
    d2 = (walsh(p) - walsh(q)) ** 2
    E = np.array([d2[POP == k].mean() for k in range(N + 1)])
    out = {"tvd": 0.5 * np.abs(p - q).sum(),
           "kl": float(np.sum(p[m] * (np.log(p[m]) - np.log(q[m])))),
           "fid": float(np.sum(np.sqrt(p * q)) ** 2),
           "G": float(E[4:7].mean()), "G_low": float(E[1:4].mean()), "G_hi": float(E[7:].mean())}
    for s in SIGMAS:
        c = np.exp(-1 / (2 * s * s))
        a, b = (1 + c) / 2, (1 - c) / 2
        out[f"mmd_{s}"] = float(sum(comb(N, k) * a ** (N - k) * b ** k * E[k] for k in range(1, N + 1)))
    out["E"] = E[1:].tolist()
    return out


def main():
    rows = {}
    for f in sorted(OUT.glob("*.npz")):
        z = np.load(f)
        cond, seed = f.stem.split("_")
        rows.setdefault(cond, []).append({k: metrics(z["p"], z[k]) for k in ("model", "me3", "me_local")})
    keys = ["G", "G_low", "G_hi", "tvd", "kl", "fid"] + [f"mmd_{s}" for s in SIGMAS]
    report = {}
    for cond, R in rows.items():
        print(f"== {cond}  n={len(R)}")
        rc = {}
        for k in keys:
            better = (lambda m, o: m > o) if k == "fid" else (lambda m, o: m < o)
            line = {}
            for opp in ("me3", "me_local"):
                w = sum(better(r["model"][k], r[opp][k]) for r in R)
                ratio = np.median([r["model"][k] / r[opp][k] for r in R])
                line[opp] = {"wins": int(w), "median_ratio": float(ratio)}
            med = {m: float(np.median([r[m][k] for r in R])) for m in ("model", "me3", "me_local")}
            rc[k] = {"vs": line, "median": med}
            print(f"  {k:8s} vs ME3 {line['me3']['wins']:2d}/{len(R)} ({line['me3']['median_ratio']:.3f})"
                  f" | vs ME-graph {line['me_local']['wins']:2d}/{len(R)} ({line['me_local']['median_ratio']:.3f})"
                  f"   medians model={med['model']:.4g} me3={med['me3']:.4g} me_graph={med['me_local']:.4g}")
        Ek = {m: np.median([r[m]["E"] for r in R], axis=0).tolist() for m in ("model", "me3", "me_local")}
        wk = [sum(r["model"]["E"][k] < r["me3"]["E"][k] for r in R) for k in range(N)]
        print("  per-order wins vs ME3 (k=1..16):", wk)
        rc["E_median"], rc["E_wins_vs_me3"], rc["n"] = Ek, wk, len(R)
        report[cond] = rc
    (OUT.parent / "metrics.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
