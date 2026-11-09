"""Step 9: the n = 16 advantage and the step-8 two-mechanism story on fresh seeds (specs/step9_fresh_seeds.md).

Designed after step 8 (notes/2026-11-09_step8_seed_diagnostic.md).

  python -m src.step9.run --instance 16 12        (one instance, level B, N = inf)
  python -m src.step9.run --repro                 (n = 16, B, seed 0 against step 7)
  python -m src.step9.run --all                   (grid + repro, 16 workers x 1 BLAS thread (amendment 1), resumable)
  python -m src.step9.run --report                (table.csv, verdicts.json, figures, SUMMARY.md)
  python -m src.step9.run --verify                (acceptance check; exit 0 = done)

One instance = src/step7/run.run_instance(n, "B", seed), imported unchanged. src/step1..7 are
never edited. Parallelism changes wall-clock only; the reproduction instance checks that.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from src.step5.run import write
from src.step7.run import MATCHED_SIGMA

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "step9"
FIGS = ROOT / "figures" / "step9"
STEP7 = ROOT / "results" / "step7"
SPEC = "specs/step9_fresh_seeds.md"
CLOSED_AT = "72d47b1"
LEVEL = "B"
NS_BITS = (14, 16)
SEEDS = tuple(range(10, 30))
SIGMA = {n: MATCHED_SIGMA[n][LEVEL] for n in NS_BITS}   # 0.213, 0.251 (step 7 level B, exact)
WORKERS = 16
THREADS = 1                  # amendment 1: 4 threads failed the reproduction test
STOP_LOSS_H = 6.0
N_BOOT = 2000
BOOT_SEED = 9
H7_MODEL = (0.3558, -6.8247, 4.6597)    # step 8 n = 16 fit, frozen in spec section 4
N14_MODEL = (-0.2298, -2.6888, 2.2920)  # exploratory
SENT = ("Step 9 was designed after step 8; seeds 10–29 are fresh; G is the generic IQP (no oracle); "
        "n ≤ 16 proxies are not hardness evidence.")


def popcount(m: int) -> int:
    return bin(int(m)).count("1")


def features(masks, theta) -> dict:
    """r4 = ||theta_w4|| / ||theta_w<=3||, r4_23 = ||theta_w4|| / ||theta_w2,3|| (step 8, d8_seeds.py)."""
    w = np.array([popcount(m) for m in masks])
    t = np.asarray(theta, dtype=np.float64)
    t4 = t[w == 4]
    return {"r4": float(np.linalg.norm(t4) / np.linalg.norm(t[w <= 3])),
            "r4_23": float(np.linalg.norm(t4) / np.linalg.norm(t[(w >= 2) & (w <= 3)]))}


def out_dir(n: int, seed: int) -> Path:
    return RESULTS / f"n_{n}" / f"sigma_{SIGMA[n]:g}" / f"seed_{seed}"


REPRO_DIR = RESULTS / "repro_n16_B_seed0"


def run_one(n: int, seed: int, dest: Path) -> Path:
    from src.step7.run import run_instance
    out = run_instance(n, LEVEL, seed)
    out.update(features(out["target_masks"], out["target_theta"]))
    out["designed_after"] = "step 8 (notes/2026-11-09_step8_seed_diagnostic.md)"
    out["blas_threads_env"] = os.environ.get("OMP_NUM_THREADS")
    return write(out, dest)


def worker_env() -> dict:
    env = dict(os.environ)
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[k] = str(THREADS)
    return env


def jobs():
    js = [("repro", 16, 0)] + [("grid", 16, s) for s in SEEDS] + [("grid", 14, s) for s in SEEDS]
    return [j for j in js if not ((REPRO_DIR if j[0] == "repro" else out_dir(j[1], j[2])) / "metrics.json").exists()]


def run_all():
    RESULTS.mkdir(parents=True, exist_ok=True)
    log = open(RESULTS / "grid.log", "a", encoding="utf-8")
    say = lambda m: (log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {m}\n"), log.flush(), print(m, flush=True))
    todo = jobs()
    say(f"start: {len(todo)} jobs, {WORKERS} workers x {THREADS} threads, stop-loss {STOP_LOSS_H} h")
    t0, running, failed = time.time(), {}, []
    while todo or running:
        while todo and len(running) < WORKERS and time.time() - t0 < STOP_LOSS_H * 3600:
            kind, n, s = todo.pop(0)
            args = ["--repro"] if kind == "repro" else ["--instance", str(n), str(s)]
            p = subprocess.Popen([sys.executable, "-m", "src.step9.run", *args], cwd=ROOT, env=worker_env(),
                                 stdout=subprocess.DEVNULL, stderr=open(RESULTS / f"err_{kind}_{n}_{s}.log", "w"))
            running[p] = ((kind, n, s), time.time())
            say(f"launch {kind} n={n} seed={s}")
        if todo and time.time() - t0 >= STOP_LOSS_H * 3600 and not running:
            say(f"STOP-LOSS: {len(todo)} jobs not started"); break
        time.sleep(5)
        for p in [p for p in running if p.poll() is not None]:
            job, ts = running.pop(p)
            say(f"done {job} rc={p.returncode} {(time.time() - ts) / 60:.1f} min")
            if p.returncode != 0:
                failed.append(job)
    say(f"end: {(time.time() - t0) / 3600:.2f} h, failed {failed}")
    return 1 if failed else 0


# ---------------- report ----------------
def load(n: int) -> dict:
    g = {}
    for s in SEEDS:
        f = out_dir(n, s) / "metrics.json"
        if f.exists():
            g[s] = json.loads(f.read_text())
    return g


def ols(D3, r4, y):
    X = np.c_[np.ones(len(y)), D3, r4]
    return np.linalg.lstsq(X, y, rcond=None)[0]


def iqr(x):
    return [float(v) for v in np.percentile(np.asarray(x, dtype=np.float64), [25, 50, 75])]


def spearman(a, b):
    from scipy.stats import spearmanr
    return float(spearmanr(a, b).statistic)


def compute() -> dict:
    g = {n: load(n) for n in NS_BITS}
    st = {}
    for n in NS_BITS:
        R = {s: g[n][s]["R"] for s in g[n]}
        wins = sum(1 for s in SEEDS if s in R and R[s] < 1)     # missing counts as a loss (spec 5)
        res = {s: g[n][s]["G_train_residual"] for s in g[n]}
        st[n] = {"k": len(R), "wins": wins, "R": R, "res": res,
                 "D3": {s: g[n][s]["D3"] for s in g[n]}, "r4": {s: g[n][s]["r4"] for s in g[n]},
                 "r4_23": {s: g[n][s]["r4_23"] for s in g[n]},
                 "coll": {s: g[n][s]["collision_ratio_target"] for s in g[n]},
                 "G_iqp": {s: g[n][s]["G_iqp"] for s in g[n]}, "G_maxent": {s: g[n][s]["G_maxent"] for s in g[n]},
                 "R_iqr": iqr(list(R.values())) if R else None,
                 "res_median": float(np.median(list(res.values()))) if res else None}
    v = {}
    v["H1"] = {"wins": st[16]["wins"], "of": 20, "need": 15, "pass": st[16]["wins"] >= 15}
    v["H2"] = {"wins": st[14]["wins"], "of": 20, "need": 15, "pass": st[14]["wins"] >= 15}
    full = all(st[n]["k"] == 20 for n in NS_BITS)
    if full:
        arr = {n: (np.array([st[n]["D3"][s] for s in SEEDS]), np.array([st[n]["r4"][s] for s in SEEDS]),
                   np.log([st[n]["R"][s] for s in SEEDS])) for n in NS_BITS}
        coef = {n: ols(*arr[n]) for n in NS_BITS}
        rng = np.random.default_rng(BOOT_SEED)
        bs = np.array([ols(*(a[i] for a in arr[16])) for i in (rng.integers(0, 20, 20) for _ in range(N_BOOT))])
        b_ci = np.percentile(bs[:, 1], [2.5, 97.5]); c_ci = np.percentile(bs[:, 2], [2.5, 97.5])
        v["H3"] = {"a_b_c": coef[16].tolist(), "b_ci95": b_ci.tolist(), "c_ci95": c_ci.tolist(),
                   "b_neg": bool(b_ci[1] < 0), "c_pos": bool(c_ci[0] > 0), "pass": bool(b_ci[1] < 0 and c_ci[0] > 0)}
        rng = np.random.default_rng(BOOT_SEED)
        d = []
        for _ in range(N_BOOT):
            i = rng.integers(0, 20, 20)
            d.append(ols(*(a[i] for a in arr[16]))[2] - ols(*(a[i] for a in arr[14]))[2])
        d_ci = np.percentile(d, [2.5, 97.5])
        v["H4"] = {"c16": float(coef[16][2]), "c14": float(coef[14][2]), "diff": float(coef[16][2] - coef[14][2]),
                   "diff_ci95": d_ci.tolist(), "pass": bool(d_ci[0] > 0)}
        q1, med, q3 = st[16]["R_iqr"]
        v["H5"] = {"median": med, "iqr": [q1, q3], "pass": bool(q3 < 1)}
        keep = [s for s in SEEDS if st[16]["res"][s] <= 1e-2]
        need_k = math.ceil(0.75 * len(keep))
        wins_k = sum(1 for s in keep if st[16]["R"][s] < 1)
        same = (wins_k >= need_k) == v["H1"]["pass"]
        v["H6"] = {"res_median": st[16]["res_median"], "kept": len(keep), "wins_kept": wins_k, "need_kept": need_k,
                   "verdict_unchanged": bool(same), "pass": bool(st[16]["res_median"] <= 1e-2 and same)}
        a, b, c = H7_MODEL
        pred = a + b * arr[16][0] + c * arr[16][1]
        rho = spearman(pred, arr[16][2])
        a, b, c = N14_MODEL
        rho14 = spearman(a + b * arr[14][0] + c * arr[14][1], arr[14][2])
        v["H7"] = {"spearman": rho, "need": 0.5, "pass": bool(rho >= 0.5)}
        y16, X16 = arr[16][2], np.c_[np.ones(20), arr[16][0], arr[16][1]]
        r2 = 1 - ((y16 - X16 @ coef[16]) ** 2).sum() / ((y16 - y16.mean()) ** 2).sum()
        y14, X14 = arr[14][2], np.c_[np.ones(20), arr[14][0], arr[14][1]]
        r2_14 = 1 - ((y14 - X14 @ coef[14]) ** 2).sum() / ((y14 - y14.mean()) ** 2).sum()
        v["exploratory"] = {
            "n14_model_spearman": rho14, "fit_n14_a_b_c": coef[14].tolist(), "R2_n16_in_sample": float(r2),
            "R2_n14_in_sample": float(r2_14),
            "n14_R_iqr": st[14]["R_iqr"], "n14_res_median": st[14]["res_median"],
            "spearman_logR_r4_23_n16": spearman(arr[16][2], [st[16]["r4_23"][s] for s in SEEDS]),
            "spearman_logR_D3_n16": spearman(arr[16][2], arr[16][0]),
            "spearman_logR_r4_n16": spearman(arr[16][2], arr[16][1]),
            "paired_both_win": sum(1 for s in SEEDS if st[14]["R"][s] < 1 and st[16]["R"][s] < 1),
            "paired_win14_lose16": sum(1 for s in SEEDS if st[14]["R"][s] < 1 <= st[16]["R"][s]),
            "paired_lose14_win16": sum(1 for s in SEEDS if st[16]["R"][s] < 1 <= st[14]["R"][s]),
        }
    rp = REPRO_DIR / "metrics.json"
    if rp.exists():
        r_new = json.loads(rp.read_text())["R"]
        r_old = json.loads((STEP7 / "n_16" / "sigma_0.251" / "seed_0" / "metrics.json").read_text())["R"]
        v["repro"] = {"R_step9": r_new, "R_step7": r_old, "rel_diff": abs(r_new - r_old) / abs(r_old),
                      "pass": abs(r_new - r_old) / abs(r_old) <= 1e-6}
    return {"stats": st, "verdicts": v, "complete": full}


def make_figures(c: dict):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIGS.mkdir(parents=True, exist_ok=True)
    st = c["stats"]

    def save(fig, name):
        for e in ("png", "pdf"):
            fig.savefig(FIGS / f"{name}.{e}", dpi=150, bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    for s in SEEDS:
        y = [st[n]["R"].get(s, np.nan) for n in NS_BITS]
        ax.plot([0, 1], y, "-o", color="0.55" if y[1] < 1 else "tab:red", alpha=0.8, lw=1, ms=4)
    ax.axhline(1, color="k", lw=1, ls="--")
    ax.set_yscale("log"); ax.set_xticks([0, 1]); ax.set_xticklabels(["n = 14 (σ = 0.213)", "n = 16 (σ = 0.251)"])
    ax.set_ylabel("R = G_iqp / G_maxent3 (orders 4–6)")
    ax.set_title(f"Fresh seeds 10–29, level B: wins n=14 {st[14]['wins']}/20, n=16 {st[16]['wins']}/20\n"
                 "red = R ≥ 1 at n = 16", fontsize=10)
    save(fig, "R_by_seed")

    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, n, mdl in zip(axs, NS_BITS, (N14_MODEL, H7_MODEL)):
        D3 = np.array([st[n]["D3"][s] for s in SEEDS if s in st[n]["R"]])
        r4 = np.array([st[n]["r4"][s] for s in SEEDS if s in st[n]["R"]])
        R = np.array([st[n]["R"][s] for s in SEEDS if s in st[n]["R"]])
        sc = ax.scatter(D3, R, c=r4, cmap="viridis", s=36, edgecolor="k", lw=0.4)
        xs = np.linspace(D3.min(), D3.max(), 50)
        for q, ls in ((np.percentile(r4, 25), ":"), (np.percentile(r4, 75), "--")):
            ax.plot(xs, np.exp(mdl[0] + mdl[1] * xs + mdl[2] * q), ls, color="0.3", lw=1,
                    label=f"step-8 model, r4 = {q:.2f}")
        ax.axhline(1, color="k", lw=0.8)
        ax.set_yscale("log"); ax.set_xlabel("D3 (completion room)"); ax.set_title(f"n = {n}")
        ax.legend(fontsize=8)
    axs[0].set_ylabel("R")
    fig.colorbar(sc, ax=axs, label="r4 = ‖θ₄‖ / ‖θ≤3‖")
    save(fig, "R_vs_D3_r4")


def write_table(c: dict):
    st = c["stats"]
    cols = ["n", "sigma", "seed", "R", "G_iqp", "G_maxent", "G_train_residual", "D3", "r4", "r4_23", "collision_ratio"]
    lines = [",".join(cols)]
    for n in NS_BITS:
        for s in SEEDS:
            if s in st[n]["R"]:
                lines.append(",".join(str(x) for x in (n, SIGMA[n], s, st[n]["R"][s], st[n]["G_iqp"][s],
                                                        st[n]["G_maxent"][s], st[n]["res"][s], st[n]["D3"][s],
                                                        st[n]["r4"][s], st[n]["r4_23"][s], st[n]["coll"][s])))
    (RESULTS / "table.csv").write_text("\n".join(lines) + "\n")


def f3(x):
    return f"{x:.3g}"


def summary(c: dict) -> str:
    st, v = c["stats"], c["verdicts"]
    P = lambda h: "**PASS**" if v[h]["pass"] else "**FAIL**"
    L = [SENT, "", "# Step 9 summary: fresh seeds 10–29 at level B (n = 14 σ = 0.213, n = 16 σ = 0.251)", "",
         "## Frozen hypotheses (spec section 4)", "", "| ID | Verdict | Numbers |", "|---|---|---|",
         f"| H1 | {P('H1')} | n = 16: {v['H1']['wins']}/20 seeds with R < 1 (need ≥ 15) |",
         f"| H2 | {P('H2')} | n = 14: {v['H2']['wins']}/20 seeds with R < 1 (need ≥ 15) |",
         f"| H3 | {P('H3')} | n = 16 OLS log R = a + b·D3 + c·r4: b = {f3(v['H3']['a_b_c'][1])} "
         f"[{f3(v['H3']['b_ci95'][0])}, {f3(v['H3']['b_ci95'][1])}], c = {f3(v['H3']['a_b_c'][2])} "
         f"[{f3(v['H3']['c_ci95'][0])}, {f3(v['H3']['c_ci95'][1])}] (95% bootstrap) |",
         f"| H4 | {P('H4')} | c(16) − c(14) = {f3(v['H4']['c16'])} − {f3(v['H4']['c14'])} = {f3(v['H4']['diff'])} "
         f"[{f3(v['H4']['diff_ci95'][0])}, {f3(v['H4']['diff_ci95'][1])}] |",
         f"| H5 | {P('H5')} | n = 16 median R {f3(v['H5']['median'])} IQR [{f3(v['H5']['iqr'][0])}, {f3(v['H5']['iqr'][1])}] |",
         f"| H6 | {P('H6')} | n = 16 median G residual {f3(v['H6']['res_median'])}; residual ≤ 1e-2 in "
         f"{v['H6']['kept']}/20, wins among them {v['H6']['wins_kept']} (need {v['H6']['need_kept']}); "
         f"H1 verdict unchanged: {v['H6']['verdict_unchanged']} |",
         f"| H7 | {P('H7')} | step-8 n = 16 model out of sample: Spearman ρ = {f3(v['H7']['spearman'])} (need ≥ 0.5) |",
         ""]
    rp = v.get("repro")
    L += ["## Reproduction instance (n = 16, B, seed 0; 16 workers × 1 thread, amendment 1)", "",
          (f"R = {rp['R_step9']!r} vs step 7 {rp['R_step7']!r}, relative difference {rp['rel_diff']:.2e} → "
           f"{'PASS' if rp['pass'] else 'FAIL: every n = 16 R is flagged'}") if rp else "missing", ""]
    L += ["## Per-seed results", "", "| seed | R n=14 | res n=14 | R n=16 | res n=16 | G_iqp 16 | G_maxent3 16 | D3 16 | r4 | coll 16 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for s in SEEDS:
        L.append(f"| {s} | {f3(st[14]['R'][s])} | {f3(st[14]['res'][s])} | {f3(st[16]['R'][s])} | {f3(st[16]['res'][s])} | "
                 f"{f3(st[16]['G_iqp'][s])} | {f3(st[16]['G_maxent'][s])} | {f3(st[16]['D3'][s])} | {f3(st[16]['r4'][s])} | "
                 f"{f3(st[16]['coll'][s])} |")
    e = v["exploratory"]
    L += ["", "## Exploratory (not frozen)", "",
          f"- n = 14 median R {f3(e['n14_R_iqr'][1])} IQR [{f3(e['n14_R_iqr'][0])}, {f3(e['n14_R_iqr'][2])}], median residual {f3(e['n14_res_median'])}.",
          f"- In-sample fit on the fresh seeds: n = 16 R² = {f3(e['R2_n16_in_sample'])}; n = 14 a, b, c = "
          f"{', '.join(f3(x) for x in e['fit_n14_a_b_c'])}, R² = {f3(e['R2_n14_in_sample'])}.",
          f"- Step-8 n = 14 model out of sample: Spearman ρ = {f3(e['n14_model_spearman'])}.",
          f"- n = 16 Spearman of log R with D3 {f3(e['spearman_logR_D3_n16'])}, r4 {f3(e['spearman_logR_r4_n16'])}, "
          f"r4_23 {f3(e['spearman_logR_r4_23_n16'])}.",
          f"- Paired by seed: win at both n {e['paired_both_win']}, win 14 / lose 16 {e['paired_win14_lose16']}, "
          f"lose 14 / win 16 {e['paired_lose14_win16']}.", ""]
    log = RESULTS / "grid.log"
    if log.exists():
        lines = log.read_text(encoding="utf-8").splitlines()
        L += ["## Timing", "", f"- {lines[0]}", f"- {lines[-1]}", ""]
    return "\n".join(L)


def report():
    c = compute()
    if not c["complete"]:
        print("incomplete grid:", {n: c["stats"][n]["k"] for n in NS_BITS}); return 1
    write_table(c)
    (RESULTS / "verdicts.json").write_text(json.dumps(c["verdicts"], indent=1))
    make_figures(c)
    (RESULTS / "SUMMARY.md").write_text(summary(c), encoding="utf-8")
    print(json.dumps({h: c["verdicts"][h]["pass"] for h in ("H1", "H2", "H3", "H4", "H5", "H6", "H7")}))
    return 0


# ---------------- verify (acceptance) ----------------
def verify() -> int:
    bad = []
    chk = lambda ok, name, msg: (print(("ok   " if ok else "FAIL ") + f"[{name}] {msg}"), ok or bad.append(name))
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    chk(git("ls-files", "--error-unmatch", SPEC).returncode == 0, "spec", f"{SPEC} committed")
    chk(git("diff", "--quiet", "HEAD", "--", SPEC).returncode == 0, "spec", "spec unchanged since commit")
    closed = [f"src/step{i}/" for i in range(1, 8)]
    chk(git("diff", "--name-only", CLOSED_AT, "HEAD", "--", *closed).stdout.strip() == ""
        and git("diff", "--quiet", "HEAD", "--", *closed).returncode == 0, "closed", f"src/step1..7 unchanged since {CLOSED_AT}")
    for n in NS_BITS:
        for s in SEEDS:
            f = out_dir(n, s) / "metrics.json"
            if not f.exists():
                chk(False, "grid", f"missing {f.relative_to(ROOT)}"); continue
            d = json.loads(f.read_text())
            ok = (d["n"] == n and abs(d["sigma"] - SIGMA[n]) < 1e-12 and d["level"] == LEVEL and d["seed"] == s
                  and len(d["G_restart_residuals"]) >= 3 and "r4" in d and "r4_23" in d)
            if not ok:
                chk(False, "metrics", f"{f.relative_to(ROOT)} wrong n/sigma/level/seed/restarts/features")
    chk(not [b for b in bad if b in ("grid", "metrics")], "grid", "40 instances, exact n / σ / level B / seed, ≥ 3 restarts")
    c = compute()
    rp = c["verdicts"].get("repro")
    chk(bool(rp and rp["pass"]), "repro", f"n = 16 B seed 0 reproduces step 7 R: {rp and rp['rel_diff']:.2e}" if rp else "missing")
    S = RESULTS / "SUMMARY.md"
    txt = S.read_text(encoding="utf-8") if S.exists() else ""
    chk(txt.startswith(SENT), "summary", "SUMMARY opens with the required sentence")
    import re
    chk(all(re.search(rf"\| {h} \| \*\*(PASS|FAIL)\*\*", txt) for h in ("H1", "H2", "H3", "H4", "H5", "H6", "H7")),
        "summary", "SUMMARY marks H1–H7 PASS/FAIL")
    for a in ("table.csv", "verdicts.json"):
        chk((RESULTS / a).exists(), "artifacts", f"results/step9/{a}")
    chk(all((FIGS / f"{f}.{e}").exists() for f in ("R_by_seed", "R_vs_D3_r4") for e in ("png", "pdf")), "figures", "figures/step9/*")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step9.py"], cwd=ROOT, capture_output=True, text=True)
    chk(t.returncode == 0, "tests", (t.stdout.strip().splitlines() or ["no output"])[-1])
    print("ALL CHECKS PASS (step 9)" if not bad else f"FAILED: {sorted(set(bad))}")
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", nargs=2, type=int, metavar=("N", "SEED"))
    ap.add_argument("--repro", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if a.instance:
        n, s = a.instance
        assert n in NS_BITS and s in SEEDS, "spec: n in {14, 16}, seeds 10-29"
        print(run_one(n, s, out_dir(n, s)))
    elif a.repro:
        print(run_one(16, 0, REPRO_DIR))
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
