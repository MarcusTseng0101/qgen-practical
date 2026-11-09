"""Step 10: is step 9's n = 14 failure under-training? (specs/step10_more_restarts.md)

  python -m src.step10.run --instance 12    (one seed, n = 14, level B, 10 G restarts)
  python -m src.step10.run --all            (20 seeds, 16 workers x 1 thread, resumable)
  python -m src.step10.run --report         (table.csv, verdicts.json, figure, SUMMARY.md)
  python -m src.step10.run --verify         (acceptance check; exit 0 = done)

One instance = src/step6/run.run_instance(14, 0.213, seed, g_restarts=10), imported unchanged.
Restarts 0-2 replay step 9's three restarts exactly (inits drawn in order from default_rng(seed)).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from src.step5.run import write
from src.step9 import run as r9

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "step10"
FIGS = ROOT / "figures" / "step10"
SPEC = "specs/step10_more_restarts.md"
CLOSED_AT = "e55c4b6"
N = 14
SIGMA = r9.SIGMA[14]          # 0.213, exact
SEEDS = r9.SEEDS              # 10..29
RESTARTS = 10
WORKERS = 16
STOP_LOSS_H = 1.0
STEP9_LOSERS = (10, 11, 13, 14, 15, 16, 17, 19, 24, 28)   # spec section 3 (from step 9)
SENT = ("Step 10 was designed after step 9; it changes G's restart budget from 3 to 10 at n = 14 only; "
        "G is the generic IQP (no oracle); n ≤ 16 proxies are not hardness evidence.")


def out_dir(seed: int) -> Path:
    return RESULTS / f"seed_{seed}"


def step9(seed: int) -> dict:
    return json.loads((r9.out_dir(N, seed) / "metrics.json").read_text())


def run_one(seed: int, dest: Path) -> Path:
    from src.step6.run import run_instance
    out = run_instance(N, SIGMA, seed, g_restarts=RESTARTS)
    out["level"] = "B"
    out.update(r9.features(out["target_masks"], out["target_theta"]))
    old = step9(seed)
    a, b = np.array(out["G_restart_residuals"][:3]), np.array(old["G_restart_residuals"])
    out["restarts_0_2_match"] = bool(np.all(np.abs(a - b) <= 1e-6 * np.abs(b)))
    out["restarts_0_2_max_rel_diff"] = float(np.max(np.abs(a - b) / np.abs(b)))
    out["step9_R"], out["step9_best_restart"] = old["R"], old["G_best_restart"]
    out["designed_after"] = "step 9 (notes/2026-11-09_step9_findings.md)"
    out["blas_threads_env"] = os.environ.get("OMP_NUM_THREADS")
    return write(out, dest)


def run_all():
    RESULTS.mkdir(parents=True, exist_ok=True)
    log = open(RESULTS / "grid.log", "a", encoding="utf-8")
    say = lambda m: (log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {m}\n"), log.flush(), print(m, flush=True))
    todo = [s for s in SEEDS if not (out_dir(s) / "metrics.json").exists()]
    say(f"start: {len(todo)} seeds, {WORKERS} workers x 1 thread, {RESTARTS} restarts")
    t0, running, failed = time.time(), {}, []
    while todo or running:
        while todo and len(running) < WORKERS and time.time() - t0 < STOP_LOSS_H * 3600:
            s = todo.pop(0)
            p = subprocess.Popen([sys.executable, "-m", "src.step10.run", "--instance", str(s)], cwd=ROOT,
                                 env=r9.worker_env(), stdout=subprocess.DEVNULL,
                                 stderr=open(RESULTS / f"err_{s}.log", "w"))
            running[p] = (s, time.time()); say(f"launch seed={s}")
        if todo and not running:
            say(f"STOP-LOSS: {len(todo)} not started"); break
        time.sleep(5)
        for p in [p for p in running if p.poll() is not None]:
            s, ts = running.pop(p)
            say(f"done seed={s} rc={p.returncode} {(time.time() - ts) / 60:.1f} min")
            if p.returncode != 0:
                failed.append(s)
    say(f"end: {(time.time() - t0) / 60:.1f} min, failed {failed}")
    return 1 if failed else 0


def compute() -> dict:
    g = {s: json.loads((out_dir(s) / "metrics.json").read_text()) for s in SEEDS if (out_dir(s) / "metrics.json").exists()}
    if len(g) < 20:
        return {"complete": False, "k": len(g)}
    R10 = {s: g[s]["R"] for s in SEEDS}
    R3 = {s: g[s]["step9_R"] for s in SEEDS}
    res10 = {s: g[s]["G_train_residual"] for s in SEEDS}
    winners9 = [s for s in SEEDS if s not in STEP9_LOSERS]
    v = {
        "K1": {"wins": sum(R10[s] < 1 for s in SEEDS), "need": 15},
        "K2": {"res_gt_1e2": sum(res10[s] > 1e-2 for s in SEEDS), "max": 2,
               "step9": sum(step9(s)["G_train_residual"] > 1e-2 for s in SEEDS)},
        "K3": {"rescued": sum(R10[s] < 1 for s in STEP9_LOSERS), "need": 6},
        "K4": {"flipped": sum(R10[s] >= 1 for s in winners9), "max": 1},
    }
    v["K1"]["pass"] = v["K1"]["wins"] >= 15
    v["K2"]["pass"] = v["K2"]["res_gt_1e2"] <= 2
    v["K3"]["pass"] = v["K3"]["rescued"] >= 6
    v["K4"]["pass"] = v["K4"]["flipped"] <= 1
    rho, minboth, best_changed = [], 0, 0
    for s in SEEDS:
        rr, gg = g[s]["G_restart_residuals"], g[s]["G_restart_G"]
        rho.append(r9.spearman(rr, gg))
        minboth += int(np.argmin(rr) == np.argmin(gg))
        best_changed += int(g[s]["G_best_restart"] != g[s]["step9_best_restart"])
    q = lambda x: [float(t) for t in np.percentile(list(x), [25, 50, 75])]
    v["exploratory"] = {
        "R_iqr_10": q(R10.values()), "R_iqr_3": q(R3.values()),
        "res_median_10": float(np.median(list(res10.values()))),
        "res_median_3": float(np.median([step9(s)["G_train_residual"] for s in SEEDS])),
        "spearman_res_G_within_instance_median": float(np.median(rho)),
        "spearman_res_G_within_instance_iqr": q(rho),
        "min_residual_is_min_G": minboth,
        "best_restart_changed_from_step9": best_changed,
        "restarts_0_2_all_match": all(g[s]["restarts_0_2_match"] for s in SEEDS),
        "restarts_0_2_max_rel_diff": max(g[s]["restarts_0_2_max_rel_diff"] for s in SEEDS),
        "oracle_min_G_wins": sum(min(g[s]["G_restart_G"]) / g[s]["G_maxent"] < 1 for s in SEEDS),
    }
    return {"complete": True, "g": g, "R10": R10, "R3": R3, "res10": res10, "verdicts": v}


def make_figure(c):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIGS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.2, 5))
    for s in SEEDS:
        lost9 = s in STEP9_LOSERS
        ax.scatter(c["R3"][s], c["R10"][s], c="tab:red" if lost9 else "0.4", s=30, zorder=3)
        ax.annotate(str(s), (c["R3"][s], c["R10"][s]), fontsize=7, xytext=(3, 2), textcoords="offset points")
    lim = [0.2, 3]
    ax.plot(lim, lim, color="0.7", lw=1); ax.axhline(1, color="k", lw=0.8, ls="--"); ax.axvline(1, color="k", lw=0.8, ls="--")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("R with 3 restarts (step 9)"); ax.set_ylabel("R with 10 restarts (step 10)")
    v = c["verdicts"]
    ax.set_title(f"n = 14, σ = 0.213: wins {20 - len(STEP9_LOSERS)}/20 → {v['K1']['wins']}/20\nred = step-9 losers", fontsize=10)
    for e in ("png", "pdf"):
        fig.savefig(FIGS / f"R_3_vs_10.{e}", dpi=150, bbox_inches="tight")
    plt.close(fig)


def report():
    c = compute()
    if not c["complete"]:
        print("incomplete:", c["k"]); return 1
    v, g = c["verdicts"], c["g"]
    cols = ["seed", "R_10", "R_3", "res_10", "res_3", "best_10", "best_3", "G_iqp_10", "G_maxent", "restarts_0_2_match"]
    lines = [",".join(cols)] + [",".join(str(x) for x in (s, c["R10"][s], c["R3"][s], c["res10"][s], step9(s)["G_train_residual"],
                                                         g[s]["G_best_restart"], g[s]["step9_best_restart"], g[s]["G_iqp"],
                                                         g[s]["G_maxent"], g[s]["restarts_0_2_match"])) for s in SEEDS]
    (RESULTS / "table.csv").write_text("\n".join(lines) + "\n")
    (RESULTS / "verdicts.json").write_text(json.dumps(v, indent=1))
    make_figure(c)
    P = lambda k: "**PASS**" if v[k]["pass"] else "**FAIL**"
    f3 = lambda x: f"{x:.3g}"
    e = v["exploratory"]
    L = [SENT, "", "# Step 10 summary: n = 14, level B, seeds 10–29, G with 10 restarts", "",
         "## Frozen hypotheses (spec section 3)", "", "| ID | Verdict | Numbers |", "|---|---|---|",
         f"| K1 | {P('K1')} | {v['K1']['wins']}/20 seeds with R < 1 (need ≥ 15; step 9 with 3 restarts: 10/20) |",
         f"| K2 | {P('K2')} | {v['K2']['res_gt_1e2']}/20 seeds with best residual > 1e-2 (need ≤ 2; step 9: {v['K2']['step9']}/20) |",
         f"| K3 | {P('K3')} | {v['K3']['rescued']}/10 step-9 losers now R < 1 (need ≥ 6) |",
         f"| K4 | {P('K4')} | {v['K4']['flipped']}/10 step-9 winners now R ≥ 1 (need ≤ 1) |", "",
         "## Per seed", "", "| seed | step-9 result | R (3) | R (10) | residual (3) | residual (10) | best restart 3 → 10 |",
         "|---|---|---|---|---|---|---|"]
    for s in SEEDS:
        L.append(f"| {s} | {'loss' if s in STEP9_LOSERS else 'win'} | {f3(c['R3'][s])} | {f3(c['R10'][s])} | "
                 f"{f3(step9(s)['G_train_residual'])} | {f3(c['res10'][s])} | {g[s]['step9_best_restart']} → {g[s]['G_best_restart']} |")
    L += ["", "## Exploratory (not frozen)", "",
          f"- Median R: 3 restarts {f3(e['R_iqr_3'][1])} [{f3(e['R_iqr_3'][0])}, {f3(e['R_iqr_3'][2])}] → "
          f"10 restarts {f3(e['R_iqr_10'][1])} [{f3(e['R_iqr_10'][0])}, {f3(e['R_iqr_10'][2])}]. Median residual "
          f"{f3(e['res_median_3'])} → {f3(e['res_median_10'])}.",
          f"- The best restart changed from step 9's in {e['best_restart_changed_from_step9']}/20 seeds.",
          f"- Within an instance, Spearman(residual, G_iqp) across the 10 restarts: median {f3(e['spearman_res_G_within_instance_median'])} "
          f"[{f3(e['spearman_res_G_within_instance_iqr'][0])}, {f3(e['spearman_res_G_within_instance_iqr'][2])}].",
          f"- The lowest-residual restart is also the lowest-G restart in {e['min_residual_is_min_G']}/20 seeds.",
          f"- Oracle (pick the lowest-G restart, which uses the target, so it is not a valid method): "
          f"{e['oracle_min_G_wins']}/20 wins. This is an upper bound on any selection rule.",
          f"- Restarts 0–2 reproduce step 9: all match = {e['restarts_0_2_all_match']}, max relative "
          f"difference {e['restarts_0_2_max_rel_diff']:.1e}.", ""]
    lg = (RESULTS / "grid.log").read_text(encoding="utf-8").splitlines()
    L += ["## Timing", "", f"- {lg[0]}", f"- {lg[-1]}", ""]
    (RESULTS / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print(json.dumps({k: v[k]["pass"] for k in ("K1", "K2", "K3", "K4")}))
    return 0


def verify() -> int:
    bad = []
    chk = lambda ok, name, msg: (print(("ok   " if ok else "FAIL ") + f"[{name}] {msg}"), ok or bad.append(name))
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    chk(git("ls-files", "--error-unmatch", SPEC).returncode == 0 and git("diff", "--quiet", "HEAD", "--", SPEC).returncode == 0,
        "spec", f"{SPEC} committed and unchanged")
    closed = [f"src/step{i}/" for i in range(1, 10)]
    chk(git("diff", "--name-only", CLOSED_AT, "HEAD", "--", *closed).stdout.strip() == ""
        and git("diff", "--quiet", "HEAD", "--", *closed).returncode == 0, "closed", f"src/step1..9 unchanged since {CLOSED_AT}")
    ok = True
    for s in SEEDS:
        f = out_dir(s) / "metrics.json"
        if not f.exists():
            ok = False; print(f"     missing {f.relative_to(ROOT)}"); continue
        d = json.loads(f.read_text())
        if not (d["n"] == N and abs(d["sigma"] - SIGMA) < 1e-12 and d["seed"] == s and d["G_n_restarts"] == RESTARTS
                and d["restarts_0_2_match"]):
            ok = False; print(f"     bad {f.relative_to(ROOT)}")
    chk(ok, "grid", "20 seeds, exact σ, 10 restarts, restarts 0–2 reproduce step 9")
    S = RESULTS / "SUMMARY.md"
    txt = S.read_text(encoding="utf-8") if S.exists() else ""
    chk(txt.startswith(SENT), "summary", "SUMMARY opens with the required sentence")
    chk(all(re.search(rf"\| {k} \| \*\*(PASS|FAIL)\*\*", txt) for k in ("K1", "K2", "K3", "K4")), "summary", "K1–K4 marked")
    chk(all((FIGS / f"R_3_vs_10.{e}").exists() for e in ("png", "pdf")), "figures", "figures/step10/R_3_vs_10")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step10.py"], cwd=ROOT, capture_output=True, text=True)
    chk(t.returncode == 0, "tests", (t.stdout.strip().splitlines() or ["no output"])[-1])
    print("ALL CHECKS PASS (step 10)" if not bad else f"FAILED: {sorted(set(bad))}")
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if a.instance is not None:
        assert a.instance in SEEDS
        print(run_one(a.instance, out_dir(a.instance)))
    elif a.all:
        return run_all()
    elif a.report:
        return report()
    elif a.verify:
        return verify()
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
