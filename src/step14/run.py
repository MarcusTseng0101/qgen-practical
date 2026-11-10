"""Step 14: the noise-corrected residual gate at finite N (specs/step14_finiteN_gate.md).

  python -m src.step14.run --instance iqp4 100000 50   (one instance: FAMILY N SEED, n = 16)
  python -m src.step14.run --all                       (120 instances, 16 workers x 1 thread, N = 1e5 first, stop-loss 5 h)
  python -m src.step14.run --report                    (table.csv, verdicts.json, figure, SUMMARY.md)
  python -m src.step14.run --verify                    (acceptance check; exit 0 = done)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from src.step1 import metrics as M1
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.versions import versions
from src.step2.sweep import kl
from src.step3.run import fit_restarts
from src.step4.run import training_moments
from src.step4.targets import iqp4_target
from src.step5.run import write
from src.step7.run import MATCHED_SIGMA
from src.step12.targets import FAMILIES
from src.step13.gate import TAU, gated_ratio, outcomes, sign_p

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "step14"
FIGS = ROOT / "figures" / "step14"
CAL12 = ROOT / "results" / "step12" / "CALIBRATION.json"
SPEC = "specs/step14_finiteN_gate.md"
CLOSED_AT = "b31cb7b"
FAMS = ("iqp4", "lcm", "ising4")
N_BITS = 16
NS_SHOTS = (100_000, 10_000)
SEEDS = tuple(range(50, 70))
LEVEL = "B"
SIGMA = MATCHED_SIGMA[N_BITS][LEVEL]
RESTARTS = 3
WORKERS = 16
STOP_LOSS_H = 5.0
SENT = ("Step 14 was designed after step 13 and a pilot on development seeds; seeds 50–69 are fresh; the gate uses "
        "r_N − Σ(1 − f̂²)/N ≤ τ = 1e-2 from training data only; G is the generic IQP (no oracle); n = 16 proxies are "
        "not hardness evidence.")
IDS = {100_000: ("S1", "S2"), 10_000: ("S3", "S4")}


def floor_of(fhat, N: int) -> float:
    """Expected squared sampling error of the training moments: sum_a (1 - fhat_a^2) / N."""
    fhat = np.asarray(fhat, dtype=float)
    return float(np.sum(1.0 - fhat**2) / N)


def excess(r_N: float, floor: float) -> float:
    return r_N - floor


def beta_of(fam: str) -> float:
    return json.loads(CAL12.read_text())["beta"][f"{fam}/n_{N_BITS}"]["beta"]


def out_dir(fam: str, N: int, seed: int) -> Path:
    return RESULTS / fam / f"N_{N}" / f"seed_{seed}"


def target(fam: str, seed: int):
    if fam == "iqp4":
        return iqp4_target(SIGMA, seed, N_BITS)[0], {"sigma": SIGMA, "level": LEVEL}
    b = beta_of(fam)
    return FAMILIES[fam](b, seed, N_BITS), {"beta": b}


# ---------------- one instance ----------------
def run_one(fam: str, N: int, seed: int) -> Path:
    t0, n = time.time(), N_BITS
    p, meta = target(fam, seed)
    fhat, ops = training_moments(p, N, seed, n)
    ftrue, _ = training_moments(p, None, seed, n)
    me = MaxEntModel(n, 3)
    mf = me.fit_moments(fhat, ops)
    q_me = me.prob(mf.params)
    G_me = M1.completion_gap(q_me, p, n)["G"]
    model = IQPModel(n)
    r = fit_restarts(model, fhat, ops, seed, p, n, RESTARTS)
    b = r["rows"][r["best"]]
    fl = floor_of(fhat, N)
    ex = excess(b["residual"], fl)
    R = b["G"] / G_me
    out = {"family": fam, "n": n, "N": N, "seed": seed, **meta, "versions": versions(),
           "G_iqp": b["G"], "G_maxent": G_me, "R": R, "G_train_residual": b["residual"], "floor": fl, "excess": ex,
           "r_true": float(np.sum((model.moments(b["params"], ops) - ftrue) ** 2)),
           "noise_true": float(np.sum((fhat - ftrue) ** 2)),
           "G_n_restarts": len(r["rows"]), "G_restart_residuals": [x["residual"] for x in r["rows"]],
           "G_restart_G": [x["G"] for x in r["rows"]], "G_best_restart": r["best"],
           "D3": kl(p, q_me), "collision_ratio_target": M1.collision_ratio(p),
           "maxent_train_residual": mf.train_residual, "maxent_nit": mf.nit,
           "p_min": float(p.min()), "p_sum_err": float(abs(p.sum() - 1)), "tau": TAU,
           "R_gate": float(gated_ratio(R, ex)),
           "designed_after": "step 13 (notes/2026-11-10_step13_gate_findings.md) and the step 14 pilot",
           "blas_threads_env": os.environ.get("OMP_NUM_THREADS"), "total_seconds": time.time() - t0}
    return write(out, out_dir(fam, N, seed))


def worker_env() -> dict:
    env = dict(os.environ)
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[k] = "1"
    return env


def run_all() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    log = open(RESULTS / "grid.log", "a", encoding="utf-8")
    say = lambda m: (log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {m}\n"), log.flush(), print(m, flush=True))
    # iqp4 first within each N: it is the slowest family, so the tail is short
    todo = [(f, N, s) for N in NS_SHOTS for f in FAMS for s in SEEDS if not (out_dir(f, N, s) / "metrics.json").exists()]
    say(f"start: {len(todo)} jobs, {WORKERS} workers x 1 thread, stop-loss {STOP_LOSS_H} h")
    t0, running, failed = time.time(), {}, []
    while todo or running:
        while todo and len(running) < WORKERS and time.time() - t0 < STOP_LOSS_H * 3600:
            f, N, s = todo.pop(0)
            err = RESULTS / f"err_{f}_{N}_{s}.log"
            pr = subprocess.Popen([sys.executable, "-m", "src.step14.run", "--instance", f, str(N), str(s)], cwd=ROOT,
                                  env=worker_env(), stdout=subprocess.DEVNULL, stderr=open(err, "w"))
            running[pr] = ((f, N, s), time.time(), err)
            say(f"launch {f} N={N} seed={s}")
        if todo and time.time() - t0 >= STOP_LOSS_H * 3600 and not running:
            say(f"STOP-LOSS: {len(todo)} jobs not started: {todo}"); break
        time.sleep(5)
        for pr in [pr for pr in running if pr.poll() is not None]:
            job, ts, err = running.pop(pr)
            say(f"done {job} rc={pr.returncode} {(time.time() - ts) / 60:.1f} min")
            if pr.returncode != 0:
                failed.append(job)
            elif err.exists() and err.stat().st_size == 0:
                err.unlink()
    say(f"end: {(time.time() - t0) / 3600:.2f} h, failed {failed}")
    return 1 if failed else 0


# ---------------- report ----------------
def load(fam: str, N: int) -> list:
    return [json.loads((out_dir(fam, N, s) / "metrics.json").read_text()) for s in SEEDS
            if (out_dir(fam, N, s) / "metrics.json").exists()]


def gmean(x) -> float:
    return float(np.exp(np.mean(np.log(x))))


def med_iqr(x) -> str:
    q = np.percentile(x, [25, 50, 75])
    return f"{q[1]:.3g} [{q[0]:.3g}, {q[2]:.3g}]"


def compute() -> dict:
    c = {"verdicts": {}, "stats": {}, "complete": True}
    for N, (kg, ks) in IDS.items():
        D = {f: load(f, N) for f in FAMS}
        if any(len(D[f]) < len(SEEDS) for f in FAMS):
            c["complete"] = False
            c["verdicts"][kg] = c["verdicts"][ks] = {"PASS": None, "N": N}
            continue
        R = {f: np.array([d["R"] for d in D[f]]) for f in FAMS}
        ex = {f: np.array([d["excess"] for d in D[f]]) for f in FAMS}
        raw = {f: np.array([d["G_train_residual"] for d in D[f]]) for f in FAMS}
        o = outcomes(R["iqp4"], ex["iqp4"])
        p = sign_p(o["wins"], o["losses"])
        c["verdicts"][kg] = {**o, "sign_p": p, "PASS": bool(o["wins"] >= 10 and p <= 0.05), "N": N,
                             "statement": "iqp4: wins >= 10/20 and one-sided sign-test p <= 0.05"}
        oo = outcomes(np.concatenate([R["lcm"], R["ising4"]]), np.concatenate([ex["lcm"], ex["ising4"]]))
        c["verdicts"][ks] = {**oo, "PASS": bool(oo["losses"] <= 2), "N": N,
                             "statement": "lcm + ising4 pooled: losses <= 2/40"}
        allR = np.concatenate([R[f] for f in FAMS]); allx = np.concatenate([ex[f] for f in FAMS])
        st = {"pool_gmean_R_gate": gmean(gated_ratio(allR, allx)), "pool_gmean_oracle_min_R_1": gmean(np.minimum(allR, 1)),
              "pool_gmean_R_iqp_always": gmean(allR)}
        for f in FAMS:
            pk = ex[f] <= TAU
            st[f] = {**outcomes(R[f], ex[f]), "R": med_iqr(R[f]), "excess": med_iqr(ex[f]), "r_N": med_iqr(raw[f]),
                     "r_true": med_iqr([d["r_true"] for d in D[f]]), "floor": med_iqr([d["floor"] for d in D[f]]),
                     "worst_R_gate_picked": float(R[f][pk].max()) if pk.any() else None,
                     "gmean_R_gate": gmean(gated_ratio(R[f], ex[f])),
                     "uncorrected": outcomes(R[f], raw[f]),
                     "tau_3e-3": outcomes(R[f], ex[f], 3e-3), "tau_3e-2": outcomes(R[f], ex[f], 3e-2),
                     "D3": med_iqr([d["D3"] for d in D[f]]),
                     "minutes": float(np.median([d["total_seconds"] for d in D[f]]) / 60)}
        c["stats"][f"N_{N}"] = st
    return c


def make_figures():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIGS.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    mk = {"iqp4": "o", "lcm": "s", "ising4": "^"}
    for ax, N in zip(axs, NS_SHOTS):
        for f in FAMS:
            ds = load(f, N)
            ax.plot([d["excess"] for d in ds], [d["R"] for d in ds], mk[f], ms=5, alpha=0.8, label=f)
        ax.set_xscale("symlog", linthresh=1e-3); ax.set_yscale("log")
        ax.axhline(1.0, color="grey", ls="--", lw=0.8); ax.axvline(TAU, color="red", ls=":", lw=1)
        ax.set_title(f"n = 16, N = {N:.0e}, seeds 50–69")
        ax.set_xlabel("excess residual r_N − Σ(1 − f̂²)/N (gate picks IQP left of red line)")
        ax.set_ylabel("R = G_iqp / G_maxent3 (below 1: IQP wins)")
    axs[0].legend(fontsize=8)
    fig.tight_layout()
    for e in ("png", "pdf"):
        fig.savefig(FIGS / f"gate_finiteN.{e}", dpi=150)
    plt.close(fig)


def summary(c: dict) -> str:
    v = c["verdicts"]
    mark = lambda x: "**PASS**" if x else ("**FAIL**" if x is False else "incomplete")
    L = [SENT, "", f"Spec: `{SPEC}`. Gate: use G iff r_N − Σ(1 − f̂²)/N ≤ τ = {TAU:g}, else MaxEnt(3).", "",
         "| ID | N | Statement | Counts | Verdict |", "|---|---|---|---|---|"]
    for k in ("S1", "S2", "S3", "S4"):
        d = v[k]
        cnt = (f"picked {d['picked']}, wins {d['wins']}, losses {d['losses']}, ties {d['ties']}"
               + (f", sign p = {d['sign_p']:.3g}" if "sign_p" in d else "")) if "wins" in d else "—"
        L.append(f"| {k} | {d['N']:.0e} | {d.get('statement', '')} | {cnt} | {mark(d['PASS'])} |")
    for N in NS_SHOTS:
        st = c["stats"].get(f"N_{N}")
        if not st:
            continue
        L += ["", f"## N = {N:.0e} (exploratory)", "",
              f"Pool of 60: geometric mean R_gate = {st['pool_gmean_R_gate']:.3g}; always-IQP = "
              f"{st['pool_gmean_R_iqp_always']:.3g}; oracle min(R, 1) = {st['pool_gmean_oracle_min_R_1']:.3g}.", "",
              "| | " + " | ".join(FAMS) + " |", "|---|" + "---|" * len(FAMS)]
        row = lambda lab, fn: L.append(f"| {lab} | " + " | ".join(fn(st[f]) for f in FAMS) + " |")
        row("picked / wins / losses / ties", lambda s: f"{s['picked']} / {s['wins']} / {s['losses']} / {s['ties']}")
        row("R (always IQP)", lambda s: s["R"])
        row("excess residual", lambda s: s["excess"])
        row("r_N (raw)", lambda s: s["r_N"])
        row("floor", lambda s: s["floor"])
        row("r_true (vs exact moments)", lambda s: s["r_true"])
        row("worst R among picked", lambda s: "—" if s["worst_R_gate_picked"] is None else f"{s['worst_R_gate_picked']:.3g}")
        row("gmean R_gate", lambda s: f"{s['gmean_R_gate']:.3g}")
        row("uncorrected gate r_N ≤ τ: picked/wins/losses", lambda s: "{picked}/{wins}/{losses}".format(**s["uncorrected"]))
        row("τ = 3e-3: picked/wins/losses", lambda s: "{picked}/{wins}/{losses}".format(**s["tau_3e-3"]))
        row("τ = 3e-2: picked/wins/losses", lambda s: "{picked}/{wins}/{losses}".format(**s["tau_3e-2"]))
        row("D3", lambda s: s["D3"])
        row("median minutes", lambda s: f"{s['minutes']:.3g}")
    L += ["", "Figure: `figures/step14/gate_finiteN.png`.", ""]
    return "\n".join(L)


def write_table():
    with open(RESULTS / "table.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "N", "seed", "R", "G_iqp", "G_maxent", "r_N", "floor", "excess", "r_true", "R_gate", "D3"])
        for f in FAMS:
            for N in NS_SHOTS:
                for d in load(f, N):
                    w.writerow([f, N, d["seed"], d["R"], d["G_iqp"], d["G_maxent"], d["G_train_residual"], d["floor"],
                                d["excess"], d["r_true"], d["R_gate"], d["D3"]])


def report() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    c = compute()
    (RESULTS / "verdicts.json").write_text(json.dumps(c, indent=2))
    write_table()
    make_figures()
    txt = summary(c)
    (RESULTS / "SUMMARY.md").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


def verify() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    bad = []
    chk = lambda ok, name, msg: (print(("ok   " if ok else "FAIL ") + f"[{name}] {msg}"), ok or bad.append(name))
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    chk(git("ls-files", "--error-unmatch", SPEC).returncode == 0 and git("diff", "--quiet", "HEAD", "--", SPEC).returncode == 0,
        "spec", f"{SPEC} committed and unchanged")
    closed = [f"src/step{i}/" for i in range(1, 14)]
    chk(git("diff", "--name-only", CLOSED_AT, "HEAD", "--", *closed).stdout.strip() == ""
        and git("diff", "--quiet", "HEAD", "--", *closed).returncode == 0, "closed", f"src/step1..13 unchanged since {CLOSED_AT}")
    cal = json.loads(CAL12.read_text())["beta"]
    ok, pok = True, True
    for f in FAMS:
        for N in NS_SHOTS:
            for s in SEEDS:
                p = out_dir(f, N, s) / "metrics.json"
                if not p.exists():
                    ok = False; print(f"     missing {p.relative_to(ROOT)}"); continue
                d = json.loads(p.read_text())
                good = (d["family"] == f and d["N"] == N and d["seed"] == s and d["n"] == N_BITS
                        and d["G_n_restarts"] == RESTARTS)
                good &= (d.get("sigma") == SIGMA and d.get("level") == LEVEL) if f == "iqp4" else \
                    d.get("beta") == cal[f"{f}/n_{N_BITS}"]["beta"]
                if not good:
                    ok = False; print(f"     bad {p.relative_to(ROOT)}")
                if not (d["p_min"] >= 0 and d["p_sum_err"] <= 1e-12):
                    pok = False
    chk(ok, "grid", "120 instances: family/N/seed, n = 16, 3 G restarts, step-12 beta or level-B sigma")
    chk(pok, "targets", "every target p >= 0 and sums to 1 within 1e-12")
    S = RESULTS / "SUMMARY.md"
    txt = S.read_text(encoding="utf-8") if S.exists() else ""
    chk(txt.startswith(SENT), "summary", "SUMMARY opens with the required sentence")
    chk(all(re.search(rf"\| S{i} \|.*\| \*\*(PASS|FAIL)\*\* \|", txt) for i in range(1, 5)), "summary", "S1–S4 marked")
    chk(all((FIGS / f"gate_finiteN.{e}").exists() for e in ("png", "pdf")), "figures", "figures/step14/gate_finiteN")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step14.py"], cwd=ROOT, capture_output=True, text=True)
    chk(t.returncode == 0, "tests", (t.stdout.strip().splitlines() or ["no output"])[-1])
    print("ALL CHECKS PASS (step 14)" if not bad else f"FAILED: {sorted(set(bad))}")
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", nargs=3, metavar=("FAMILY", "N", "SEED"))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if a.instance:
        f, N, s = a.instance[0], int(a.instance[1]), int(a.instance[2])
        assert f in FAMS and N in NS_SHOTS and s in SEEDS
        print(run_one(f, N, s))
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
