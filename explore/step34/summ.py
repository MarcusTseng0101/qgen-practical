"""Step 34b pilot summary (spent seeds 1080-1086, N = 1e5). Correct-graph ('full') fits come from results/step31.
python explore/step34/summ.py > explore/step34/summary.txt"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(r"C:\Users\tseng\qgen-practical-step1")
SEEDS = range(1080, 1087)


def get(cond, graph, arm, s):
    if graph == "full":
        f = ROOT / "results/step31" / cond / arm / f"seed_{s}" / "metrics.json"
    else:
        f = ROOT / "explore/step34/out" / f"{cond}_{graph}_{arm}_{s}.json"
    return json.loads(f.read_text()) if f.exists() else None


print("Per seed: R = G/G_me3 (ratio = resid/raw_floor)")
for cond in ("cf", "pf"):
    arms = ("flip", "coh") if cond == "cf" else ("flip",)
    for arm in arms:
        print(f"\n## {cond} {arm}")
        print("seed | full R (ratio) | miss R (ratio) | enl R (ratio) | drop_miss=r_miss/r_enl | drop_full=r_full/r_enl")
        for s in SEEDS:
            d = {g: get(cond, g, arm, s) for g in ("full", "miss", "enl")}
            cells = [f"{d[g]['R_me3']:.2f} ({d[g]['ratio']:.2f})" if d[g] else "-" for g in ("full", "miss", "enl")]
            dm = d["miss"]["ratio"] / d["enl"]["ratio"] if d["miss"] and d["enl"] else float("nan")
            df = d["full"]["ratio"] / d["enl"]["ratio"] if d["full"] and d["enl"] else float("nan")
            print(f"{s} | " + " | ".join(cells) + f" | {dm:.2f} | {df:.2f}")
        for g in ("full", "miss", "enl"):
            v = [get(cond, g, arm, s) for s in SEEDS]
            v = [x for x in v if x]
            R = [x["R_me3"] for x in v]
            r = [x["ratio"] for x in v]
            print(f"  {g}: n={len(v)} median R {np.median(R):.2f}, wins {sum(x < 1 for x in R)}/{len(R)}, "
                  f"ratio range [{min(r):.2f}, {max(r):.2f}]")

print("\n## Recipe candidates (flip-first, then gate) per cond x true graph")
# drop = ratio(given FlipIQP) / ratio(enlarged FlipIQP); enlarge if drop > D; then coh gate on chosen graph's flip ratio
for D in (1.1, 1.2, 1.3, 1.5):
    for T in (0.85, 1.0):
        line = []
        for cond in ("cf", "pf"):
            for g in ("full", "miss"):
                wins, enl, coh = 0, 0, 0
                for s in SEEDS:
                    fg, fe = get(cond, g, "flip", s), get(cond, "enl", "flip", s)
                    big = fg["ratio"] / fe["ratio"] > D
                    gg = "enl" if big else g
                    fl = get(cond, gg, "flip", s)
                    use_coh = fl["ratio"] > T
                    ch = get(cond, gg, "coh", s) if use_coh else fl
                    if ch is None:   # no CohIQP fit for this cell in the pilot (pf); fall back to flip
                        ch = fl
                    enl += big
                    coh += use_coh
                    wins += ch["R_me3"] < 1
                line.append(f"{cond}/{g}: enl {enl}/7 coh {coh}/7 wins {wins}/7")
        print(f"D={D} T={T}: " + "; ".join(line))
