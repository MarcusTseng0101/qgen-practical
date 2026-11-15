"""Per-instance completion ratio R for selected tests (Fig. 1 of paper/main.tex).

Usage: python fig_instances.py [results_dir]
results_dir defaults to the step-18 worktree's results/ folder, which holds one
metrics.json per seed. Every row reproduces a win count and median quoted in the paper.
"""
import glob
import json
import os
import statistics
import sys

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = sys.argv[1] if len(sys.argv) > 1 else "C:/Users/tseng/qgen-practical-step1/results"
HERE = os.path.dirname(os.path.abspath(__file__))

# (label, folder, key). Order is top to bottom in the figure.
ROWS = [
    ("Ideal, local IQP", "step23/grid_iqp/N_10000", "R_me3"),
    ("2 missing couplers, local IQP", "step24/miss", "R_me3"),
    ("2% readout, local IQP", "step24/noise02", "R_me3"),
    ("1% gate, mitigation only", "step26/g01", "R_pipe_me3"),
    ("1% gate, FlipIQP", "step26/g01", "R_flip_me3"),
    ("Wrong graph, 1% gate, no alarm", "step27/mg01", "R_given_me3"),
    ("Wrong graph, 1% gate, recipe", "step27/mg01", "R_flow_me3"),
    ("Wrong graph, 2% corr., recipe", "step28/cm02", "R_flow_me3"),
    ("Coherent $\\epsilon=0.2$, recipe", "step29/xf02", "R_flow_me3"),
]

WIN, LOSS = "#2a78d6", "#eb6834"  # validated pair (dataviz validator, light mode)
INK, MUTED = "#0b0b0b", "#52514e"

plt.rcParams.update({"font.size": 7, "font.family": "DejaVu Sans", "axes.linewidth": 0.6})
fig, ax = plt.subplots(figsize=(3.4, 2.6))

for i, (label, folder, key) in enumerate(ROWS):
    files = sorted(glob.glob(os.path.join(RES, folder, "*", "metrics.json")))
    vals = [json.load(open(f))[key] for f in files]
    assert len(vals) == 14, (folder, len(vals))
    y = -i
    # small deterministic vertical jitter so tied points stay visible
    jit = [((k % 5) - 2) * 0.07 for k in range(len(vals))]
    for v, j in zip(vals, jit):
        win = v < 1
        ax.scatter(v, y + j, s=12, marker="o" if win else "s",
                   facecolor=WIN if win else "none", edgecolor=WIN if win else LOSS,
                   linewidth=0.8, zorder=3)
    med = statistics.median(vals)
    ax.plot([med, med], [y - 0.32, y + 0.32], color=INK, lw=1.0, zorder=4)
    wins = sum(v < 1 for v in vals)
    ax.text(1.02, y, f"{wins}/14", transform=ax.get_yaxis_transform(), va="center",
            ha="left", color=MUTED)
    print(f"{label:40s} wins={wins:2d} median={med:.3f}")

ax.axvline(1.0, color=MUTED, lw=0.6, ls="--", zorder=1)
ax.set_xscale("log")
ax.set_xlim(0.12, 8)
ax.set_xticks([0.2, 0.5, 1, 2, 5])
ax.set_xticklabels(["0.2", "0.5", "1", "2", "5"])
ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax.set_yticks([-i for i in range(len(ROWS))])
ax.set_yticklabels([r[0] for r in ROWS])
ax.set_ylim(-len(ROWS) + 0.5, 0.5)
ax.set_xlabel(r"$R = G_{\rm model}/G_{\rm MaxEnt(3)}$")
ax.tick_params(axis="y", length=0)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", which="major", color="#e4e3df", lw=0.5, zorder=0)
ax.text(1.02, 0.62, "wins", transform=ax.get_yaxis_transform(), ha="left", color=MUTED)

fig.tight_layout(pad=0.3)
out = os.path.join(HERE, "fig_instances.pdf")
fig.savefig(out)
fig.savefig(os.path.join(HERE, "fig_instances.png"), dpi=200)
print("wrote", out)
