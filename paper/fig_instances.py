# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "matplotlib",
#     "seaborn",
#     "numpy",
#     "pandas",
# ]
# ///
"""Per-instance completion ratio R for selected tests (Fig. 1 of paper/main.tex).

Run: uv run fig_instances.py [results_dir]
"""
import glob
import json
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
import seaborn as sns


def main():
    """Plot the per-instance ratio R for nine tests and print each row's wins and median.

    Parameters
    ----------
    sys.argv[1] : str, optional
        Results folder holding <step>/<cond>/seed_*/metrics.json.
        Defaults to the step-18 worktree's results folder.

    Saves
    -----
    figures/fig_instances.pdf, figures/fig_instances.png (next to this script)
    """
    # --- Style Setup ---
    sns.set_theme(font_scale=1.0, style="whitegrid", font="DejaVu Sans")
    plt.rcParams.update({"font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 7,
                         "ytick.labelsize": 7})  # 3.4 in journal column
    win_c, loss_c = "#4575b4", "#d73027"  # DIVERGING_COLORBLIND blue / red

    # --- Data ---
    res = sys.argv[1] if len(sys.argv) > 1 else "C:/Users/tseng/qgen-practical-step1/results"
    rows = [  # (label, folder, key), top to bottom; each reproduces numbers quoted in the paper
        ("Ideal, local IQP", "step23/grid_iqp/N_10000", "R_me3"),
        ("2 missing couplers, local IQP", "step24/miss", "R_me3"),
        ("2% readout, local IQP", "step24/noise02", "R_me3"),
        ("1% gate, mitigation only", "step26/g01", "R_pipe_me3"),
        ("1% gate, FlipIQP", "step26/g01", "R_flip_me3"),
        ("Wrong graph, 1% gate, no alarm", "step27/mg01", "R_given_me3"),
        ("Wrong graph, 1% gate, recipe", "step27/mg01", "R_flow_me3"),
        ("Wrong graph, 2% corr., recipe", "step28/cm02", "R_flow_me3"),
        (r"Coherent $\epsilon=0.2$, recipe", "step29/xf02", "R_flow_me3"),
    ]
    recs = []
    for i, (label, folder, key) in enumerate(rows):
        files = sorted(glob.glob(os.path.join(res, folder, "*", "metrics.json")))
        for k, f in enumerate(files):
            recs.append({"row": i, "label": label, "k": k, "R": json.load(open(f)).get(key)})
    df = pd.DataFrame(recs).dropna()
    assert (df.groupby("row").size() == 14).all()
    df["y"] = -df["row"] + ((df["k"] % 5) - 2) * 0.07  # deterministic jitter
    df["win"] = df["R"] < 1

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(3.4, 2.7), dpi=150)
    ax.axvline(1.0, color="dimgrey", lw=0.8, ls="--", zorder=1)
    w, l = df[df["win"]], df[~df["win"]]
    ax.scatter(w["R"], w["y"], s=11, marker="o", color=win_c, edgecolor="white",
               linewidth=0.3, zorder=3, label=r"win ($R<1$)")
    ax.scatter(l["R"], l["y"], s=11, marker="s", facecolor="none", edgecolor=loss_c,
               linewidth=0.8, zorder=3, label="loss")
    for i, g in df.groupby("row"):
        med, n_win = float(np.median(g["R"])), int(g["win"].sum())
        ax.plot(med, -i, marker="|", color="#333333", markersize=11, markeredgewidth=1.6, zorder=5)
        ax.text(1.02, -i, f"{n_win:>2d}/14  {med:.2f}", transform=ax.get_yaxis_transform(),
                va="center", ha="left", color="dimgrey", family="DejaVu Sans Mono", fontsize=6.5)
        print(f"{rows[i][0]:40s} wins={n_win:2d} median={med:.3f}")
    ax.text(1.02, 0.62, "wins median", transform=ax.get_yaxis_transform(), ha="left",
            color="dimgrey", weight="bold", fontsize=6.5, family="DejaVu Sans Mono")

    ax.set_xscale("log")
    ax.set_xlim(0.12, 8)
    ax.set_xticks([0.2, 0.5, 1, 2, 5])
    ax.set_xticklabels(["0.2", "0.5", "1", "2", "5"])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_yticks([-i for i in range(len(rows))])
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_ylim(-len(rows) + 0.5, 0.6)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", which="major", alpha=0.7, linewidth=0.8)
    ax.set_xlabel(r"$R = G_{\rm model}/G_{\rm MaxEnt(3)}$   (left of dashed line: model wins)",
                  color="dimgrey", labelpad=4)
    ax.tick_params(axis="both", which="both", length=0, labelcolor="dimgrey")
    sns.despine(left=True, bottom=True)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, frameon=True, facecolor="white",
              framealpha=0.8, edgecolor="lightgrey", labelcolor="dimgrey", fontsize=6,
              handletextpad=0.2, borderpad=0.4)

    # --- Save ---
    out = Path(__file__).resolve().parent / "figures"
    out.mkdir(exist_ok=True)
    fig.savefig(out / "fig_instances.pdf", dpi=150, bbox_inches="tight")
    fig.savefig(out / "fig_instances.png", dpi=150, bbox_inches="tight")
    print("wrote", out / "fig_instances.pdf")


if __name__ == "__main__":
    main()
