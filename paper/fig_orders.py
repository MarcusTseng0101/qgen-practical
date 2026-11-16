# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "matplotlib",
#     "seaborn",
#     "numpy",
#     "pandas",
# ]
# ///
"""Per-order parity error E_k of the full fitted distributions (Fig. 2 of paper/main.tex).

Run: uv run fig_orders.py [metrics.json]
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def main():
    """Plot the median per-order error E_k, k = 1..16, for three models in three settings.

    Parameters
    ----------
    sys.argv[1] : str, optional
        The metrics.json written by explore/step32_dist/metrics.py in the step-18 worktree.

    Saves
    -----
    figures/fig_orders.pdf, figures/fig_orders.png (next to this script)
    """
    # --- Style Setup ---
    sns.set_theme(font_scale=1.0, style="whitegrid", font="DejaVu Sans")
    plt.rcParams.update({"font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 7,
                         "ytick.labelsize": 7, "axes.titlesize": 7.5})

    # --- Data ---
    src = sys.argv[1] if len(sys.argv) > 1 else \
        "C:/Users/tseng/qgen-practical-step1/explore/step32_dist/metrics.json"
    rep = json.load(open(src))
    panels = [("ideal", "(a) Ideal, local IQP"), ("g01", "(b) 1% gate noise, FlipIQP"),
              ("xf02", r"(c) Coherent $\epsilon=0.2$, recipe")]
    series = [("model", "IQP model", "#4575b4", "o", "-"),
              ("me3", "MaxEnt(3)", "#333333", "s", "-"),
              ("me_local", "MaxEnt-on-graph", "#999999", "^", "--")]
    k = np.arange(1, 17)

    # --- Plot ---
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.3), dpi=150, sharey=True)
    for ax, (cond, title) in zip(axes, panels):
        r = rep[cond]
        ax.axvspan(3.5, 6.5, color="#fee090", alpha=0.5, lw=0, zorder=0)
        ax.axhline(1e-4, color="dimgrey", lw=0.8, ls=":", zorder=1)
        for key, label, c, m, ls in series:
            ax.plot(k, r["E_median"][key], color=c, marker=m, ms=3.2, lw=1.2, ls=ls, label=label, zorder=3,
                    markeredgecolor="white", markeredgewidth=0.3)
        wins = r["E_wins_vs_me3"]
        for kk, w in zip(k, wins):  # wins of the IQP model over MaxEnt(3) at each order, out of 14
            ax.text(kk, 3.2e-7, f"{w}", ha="center", va="bottom", fontsize=5.5,
                    color="#4575b4" if w >= 11 else "#d73027")
        ax.set_title(title, color="dimgrey", loc="left")
        ax.set_yscale("log")
        ax.set_ylim(2e-7, 3e-2)
        ax.set_xlim(0.4, 16.6)
        ax.set_xticks([1, 4, 6, 8, 12, 16])
        ax.set_xlabel("order $k$", color="dimgrey")
        ax.tick_params(axis="both", which="both", length=0, labelcolor="dimgrey")
        ax.grid(axis="x", visible=False)
        ax.grid(axis="y", which="major", alpha=0.6, linewidth=0.6)
    axes[0].set_ylabel(r"median $E_k$", color="dimgrey")
    axes[1].text(10.0, 1.2e-4, "shot noise $1/N$", ha="center", va="bottom", color="dimgrey", fontsize=6)
    axes[0].text(5.0, 1.5e-2, "scored\nin $G$", ha="center", va="top", color="#8c6d1f", fontsize=6)
    axes[0].text(0.6, 8.5e-7, "wins over MaxEnt(3), of 14", ha="left", va="bottom", color="dimgrey", fontsize=5.5)
    sns.despine(left=True, bottom=True)
    axes[0].legend(loc="lower left", bbox_to_anchor=(0.0, 1.12), ncol=3, frameon=True, facecolor="white",
                   framealpha=0.8, edgecolor="lightgrey", labelcolor="dimgrey", fontsize=6.5,
                   handletextpad=0.3, borderpad=0.4)
    fig.subplots_adjust(wspace=0.08)
    for cond, _ in panels:
        print(cond, "order wins vs ME3:", rep[cond]["E_wins_vs_me3"])

    # --- Save ---
    out = Path(__file__).resolve().parent / "figures"
    out.mkdir(exist_ok=True)
    fig.savefig(out / "fig_orders.pdf", dpi=150, bbox_inches="tight")
    fig.savefig(out / "fig_orders.png", dpi=150, bbox_inches="tight")
    print("wrote", out / "fig_orders.pdf")


if __name__ == "__main__":
    main()
