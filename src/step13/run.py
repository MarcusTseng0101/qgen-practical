"""Step 13: formal test of the residual-gated estimator on fresh seeds 30-49 (specs/step13_residual_gate.md).

  python -m src.step13.run --instance iqp4 16 30    (one instance)
  python -m src.step13.run --all                    (120 instances, 16 workers x 1 thread, n = 16 first, stop-loss 4 h)
  python -m src.step13.run --report                 (table.csv, verdicts.json, figure, SUMMARY.md)
  python -m src.step13.run --verify                 (acceptance check; exit 0 = done)
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
RESULTS = ROOT / "results" / "step13"
FIGS = ROOT / "figures" / "step13"
CAL12 = ROOT / "results" / "step12" / "CALIBRATION.json"
SPEC = "specs/step13_residual_gate.md"
CLOSED_AT = "41df310"
FAMS = ("iqp4", "lcm", "ising4")
NS_BITS = (16, 14)
SEEDS = tuple(range(30, 50))
LEVEL = "B"
SIGMA = {n: MATCHED_SIGMA[n][LEVEL] for n in NS_BITS}
RESTARTS = 3
WORKERS = 16
STOP_LOSS_H = 4.0
SENT = ("Step 13 was designed after step 12; seeds 30–49 are fresh; the gate threshold τ = 1e-2 was chosen on seeds "
        "10–29 and is frozen; the gate uses training moments only; G is the generic IQP (no oracle); n ≤ 16 proxies "
        "are not hardness evidence.")
IDS = {16: ("F1", "F2"), 14: ("F3", "F4")}


def beta_of(fam: str, n: int) -> float:
    return json.loads(CAL12.read_text())["beta"][f"{fam}/n_{n}"]["beta"]


def out_dir(fam: str, n: int, seed: int) -> Path:
    return RESULTS / fam / f"n_{n}" / f"seed_{seed}"


# ---------------- one instance ----------------
def run_one(fam: str, n: int, seed: int) -> Path:
    t0 = time.time()
    if fam == "iqp4":
        from src.step7.run import run_instance
        d = run_instance(n, LEVEL, seed)
        p = iqp4_target(SIGMA[n], seed, n)[0]
        out = {"family": fam, "n": n, "seed": seed, "sigma": d["sigma"], "level": LEVEL, "N": "inf",
               "versions": versions(), "G_iqp": d["G_iqp"], "G_maxent": d["G_maxent"], "R": d["R"],
               "G_train_residual": d["G_train_residual"], "G_n_restarts": d["G_n_restarts"],
               "G_restart_residuals": d["G_restart_residuals"], "G_restart_G": d["G_restart_G"],
               "G_best_restart": d["G_best_restart"], "D3": d["D3"],
               "collision_ratio_target": d["collision_ratio_target"], "maxent_train_residual": d["maxent_train_residual"]}
    else:
        beta = beta_of(fam, n)
        p = FAMILIES[fam](beta, seed, n)
        fhat, ops = training_moments(p, None, seed, n)
        me = MaxEntModel(n, 3)
        me_fit = me.fit_moments(fhat, ops)
        q_me = me.prob(me_fit.params)
        G_me = M1.completion_gap(q_me, p, n)["G"]
        r = fit_restarts(IQPModel(n), fhat, ops, seed, p, n, RESTARTS)
        b = r["rows"][r["best"]]
        out = {"family": fam, "n": n, "seed": seed, "beta": beta, "N": "inf", "versions": versions(),
               "G_iqp": b["G"], "G_maxent": G_me, "R": b["G"] / G_me, "G_train_residual": b["residual"],
               "G_n_restarts": len(r["rows"]), "G_restart_residuals": [x["residual"] for x in r["rows"]],
               "G_restart_G": [x["G"] for x in r["rows"]], "G_best_restart": r["best"], "D3": kl(p, q_me),
               "collision_ratio_target": M1.collision_ratio(p), "maxent_train_residual": me_fit.train_residual}
    out.update({"p_min": float(p.min()), "p_sum_err": float(abs(p.sum() - 1)), "tau": TAU,
                "R_gate": float(gated_ratio(out["R"], out["G_train_residual"])),
                "designed_after": "step 12 (notes/2026-11-10_step12_findings.md)",
                "blas_threads_env": os.environ.get("OMP_NUM_THREADS"), "total_seconds": time.time() - t0})
    return write(out, out_dir(fam, n, seed))


def worker_env() -> dict:
    env = dict(os.environ)
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[k] = "1"
    return env


def run_all() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    log = open(RESULTS / "grid.log", "a", encoding="utf-8")
    say = lambda m: (log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {m}\n"), log.flush(), print(m, flush=True))
    todo = [(f, n, s) for n in NS_BITS for s in SEEDS for f in FAMS if not (out_dir(f, n, s) / "metrics.json").exists()]
    say(f"start: {len(todo)} jobs, {WORKERS} workers x 1 thread, stop-loss {STOP_LOSS_H} h")
    t0, running, failed = time.time(), {}, []
    while todo or running:
        while todo and len(running) < WORKERS and time.time() - t0 < STOP_LOSS_H * 3600:
            f, n, s = todo.pop(0)
            err = RESULTS / f"err_{f}_{n}_{s}.log"
            pr = subprocess.Popen([sys.executable, "-m", "src.step13.run", "--instance", f, str(n), str(s)], cwd=ROOT,
                                  env=worker_env(), stdout=subprocess.DEVNULL, stderr=open(err, "w"))
            running[pr] = ((f, n, s), time.time(), err)
            say(f"launch {f} n={n} seed={s}")
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
def load(fam: str, n: int) -> list:
    return [json.loads((out_dir(fam, n, s) / "metrics.json").read_text()) for s in SEEDS
            if (out_dir(fam, n, s) / "metrics.json").exists()]


def gmean(x) -> float:
    return float(np.exp(np.mean(np.log(x))))


def med_iqr(x) -> str:
    q = np.percentile(x, [25, 50, 75])
    return f"{q[1]:.3g} [{q[0]:.3g}, {q[2]:.3g}]"


def compute() -> dict:
    c = {"verdicts": {}, "stats": {}, "complete": True}
    for n, (kg, ks) in IDS.items():
        D = {f: load(f, n) for f in FAMS}
        if any(len(D[f]) < len(SEEDS) for f in FAMS):
            c["complete"] = False
            c["verdicts"][kg] = c["verdicts"][ks] = {"PASS": None, "n": n}
            continue
        R = {f: np.array([d["R"] for d in D[f]]) for f in FAMS}
        r = {f: np.array([d["G_train_residual"] for d in D[f]]) for f in FAMS}
        o = outcomes(R["iqp4"], r["iqp4"])
        p = sign_p(o["wins"], o["losses"])
        c["verdicts"][kg] = {**o, "sign_p": p, "PASS": bool(o["wins"] >= 10 and p <= 0.05), "n": n,
                             "statement": "iqp4: wins >= 10/20 and one-sided sign-test p <= 0.05"}
        oo = outcomes(np.concatenate([R["lcm"], R["ising4"]]), np.concatenate([r["lcm"], r["ising4"]]))
        c["verdicts"][ks] = {**oo, "PASS": bool(oo["losses"] <= 2), "n": n,
                             "statement": "lcm + ising4 pooled: losses <= 2/40"}
        allR = np.concatenate([R[f] for f in FAMS]); allr = np.concatenate([r[f] for f in FAMS])
        st = {"pool_gmean_R_gate": gmean(gated_ratio(allR, allr)), "pool_gmean_oracle_min_R_1": gmean(np.minimum(allR, 1)),
              "pool_gmean_R_iqp_always": gmean(allR)}
        for f in FAMS:
            g = gated_ratio(R[f], r[f]); pk = r[f] <= TAU
            st[f] = {**outcomes(R[f], r[f]), "R": med_iqr(R[f]), "resid": med_iqr(r[f]),
                     "worst_R_gate_picked": float(R[f][pk].max()) if pk.any() else None,
                     "gmean_R_gate": gmean(g),
                     "tau_3e-3": outcomes(R[f], r[f], 3e-3), "tau_3e-2": outcomes(R[f], r[f], 3e-2),
                     "D3": med_iqr([d["D3"] for d in D[f]]),
                     "collision_ratio": med_iqr([d["collision_ratio_target"] for d in D[f]]),
                     "minutes": float(np.median([d["total_seconds"] for d in D[f]]) / 60)}
        c["stats"][f"n_{n}"] = st
    return c


def make_figures():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIGS.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    mk = {"iqp4": "o", "lcm": "s", "ising4": "^"}
    for ax, n in zip(axs, NS_BITS):
        for f in FAMS:
            ds = load(f, n)
            ax.loglog([d["G_train_residual"] for d in ds], [d["R"] for d in ds], mk[f], ms=5, alpha=0.8, label=f)
        ax.axhline(1.0, color="grey", ls="--", lw=0.8); ax.axvline(TAU, color="red", ls=":", lw=1)
        ax.set_title(f"n = {n}, seeds 30–49"); ax.set_xlabel("G training residual (gate picks IQP left of red line)")
        ax.set_ylabel("R = G_iqp / G_maxent3 (below 1: IQP wins)")
    axs[0].legend(fontsize=8)
    fig.tight_layout()
    for e in ("png", "pdf"):
        fig.savefig(FIGS / f"gate.{e}", dpi=150)
    plt.close(fig)


def summary(c: dict) -> str:
    v = c["verdicts"]
    mark = lambda x: "**PASS**" if x else ("**FAIL**" if x is False else "incomplete")
    L = [SENT, "", f"Spec: `{SPEC}`. Gate: use G iff its training residual ≤ τ = {TAU:g}, else MaxEnt(3).", "",
         "| ID | n | Statement | Counts | Verdict |", "|---|---|---|---|---|"]
    for k in ("F1", "F2", "F3", "F4"):
        d = v[k]
        cnt = (f"picked {d['picked']}, wins {d['wins']}, losses {d['losses']}, ties {d['ties']}"
               + (f", sign p = {d['sign_p']:.3g}" if "sign_p" in d else "")) if "wins" in d else "—"
        L.append(f"| {k} | {d['n']} | {d.get('statement', '')} | {cnt} | {mark(d['PASS'])} |")
    for n in NS_BITS:
        st = c["stats"].get(f"n_{n}")
        if not st:
            continue
        L += ["", f"## n = {n} (exploratory)", "",
              f"Pool of 60: geometric mean R_gate = {st['pool_gmean_R_gate']:.3g}; always-IQP = "
              f"{st['pool_gmean_R_iqp_always']:.3g}; oracle min(R, 1) = {st['pool_gmean_oracle_min_R_1']:.3g}.", "",
              "| | " + " | ".join(FAMS) + " |", "|---|" + "---|" * len(FAMS)]
        row = lambda lab, fn: L.append(f"| {lab} | " + " | ".join(fn(st[f]) for f in FAMS) + " |")
        row("picked / wins / losses / ties", lambda s: f"{s['picked']} / {s['wins']} / {s['losses']} / {s['ties']}")
        row("R (always IQP)", lambda s: s["R"])
        row("training residual", lambda s: s["resid"])
        row("worst R among picked", lambda s: "—" if s["worst_R_gate_picked"] is None else f"{s['worst_R_gate_picked']:.3g}")
        row("gmean R_gate", lambda s: f"{s['gmean_R_gate']:.3g}")
        row("τ = 3e-3: picked/wins/losses", lambda s: "{picked}/{wins}/{losses}".format(**s["tau_3e-3"]))
        row("τ = 3e-2: picked/wins/losses", lambda s: "{picked}/{wins}/{losses}".format(**s["tau_3e-2"]))
        row("D3", lambda s: s["D3"])
        row("collision ratio", lambda s: s["collision_ratio"])
        row("median minutes", lambda s: f"{s['minutes']:.3g}")
    L += ["", "Figure: `figures/step13/gate.png`.", ""]
    return "\n".join(L)


def write_table():
    with open(RESULTS / "table.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "n", "seed", "R", "G_iqp", "G_maxent", "G_train_residual", "R_gate", "D3", "collision_ratio"])
        for f in FAMS:
            for n in NS_BITS:
                for d in load(f, n):
                    w.writerow([f, n, d["seed"], d["R"], d["G_iqp"], d["G_maxent"], d["G_train_residual"], d["R_gate"],
                                d["D3"], d["collision_ratio_target"]])


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
    closed = [f"src/step{i}/" for i in range(1, 13)]
    chk(git("diff", "--name-only", CLOSED_AT, "HEAD", "--", *closed).stdout.strip() == ""
        and git("diff", "--quiet", "HEAD", "--", *closed).returncode == 0, "closed", f"src/step1..12 unchanged since {CLOSED_AT}")
    cal = json.loads(CAL12.read_text())["beta"]
    ok, pok = True, True
    for f in FAMS:
        for n in NS_BITS:
            for s in SEEDS:
                p = out_dir(f, n, s) / "metrics.json"
                if not p.exists():
                    ok = False; print(f"     missing {p.relative_to(ROOT)}"); continue
                d = json.loads(p.read_text())
                good = d["family"] == f and d["n"] == n and d["seed"] == s and d["G_n_restarts"] == RESTARTS
                good &= (d.get("sigma") == SIGMA[n] and d.get("level") == LEVEL) if f == "iqp4" else \
                    d.get("beta") == cal[f"{f}/n_{n}"]["beta"]
                if not good:
                    ok = False; print(f"     bad {p.relative_to(ROOT)}")
                if not (d["p_min"] >= 0 and d["p_sum_err"] <= 1e-12):
                    pok = False
    chk(ok, "grid", "120 instances: family/n/seed, 3 G restarts, step-12 beta or level-B sigma")
    chk(pok, "targets", "every target p >= 0 and sums to 1 within 1e-12")
    S = RESULTS / "SUMMARY.md"
    txt = S.read_text(encoding="utf-8") if S.exists() else ""
    chk(txt.startswith(SENT), "summary", "SUMMARY opens with the required sentence")
    chk(all(re.search(rf"\| F{i} \|.*\| \*\*(PASS|FAIL)\*\* \|", txt) for i in range(1, 5)), "summary", "F1–F4 marked")
    chk(all((FIGS / f"gate.{e}").exists() for e in ("png", "pdf")), "figures", "figures/step13/gate")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step13.py"], cwd=ROOT, capture_output=True, text=True)
    chk(t.returncode == 0, "tests", (t.stdout.strip().splitlines() or ["no output"])[-1])
    print("ALL CHECKS PASS (step 13)" if not bad else f"FAILED: {sorted(set(bad))}")
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", nargs=3, metavar=("FAMILY", "N", "SEED"))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if a.instance:
        f, n, s = a.instance[0], int(a.instance[1]), int(a.instance[2])
        assert f in FAMS and n in NS_BITS and s in SEEDS
        print(run_one(f, n, s))
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
