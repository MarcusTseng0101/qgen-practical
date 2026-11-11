"""Step 22: classical XOR model vs IQP vs MaxEnt(3) (specs/step22_xor_interference.md).

  python -m src.step22.run --synth S | --iqp4 S | --a RUN SPLIT | --b RUN | --all | --report | --verify
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from src.step1 import metrics as M1
from src.step1.bits import masks_up_to
from src.step1.models.maxent import MaxEntModel
from src.step1.targets import sample_indices
from src.step1.walsh import coefficients_by_order, empirical_distribution, parity_coefficients
from src.step4.targets import iqp4_target
from src.step14.run import SIGMA
from src.step17.pilot import LEVELS, corrected_gap
from src.step19 import data as D19
from src.step20 import pilot as P20
from src.step20.core import FIT_FRAC, fit_and_gate
from src.step21 import run as R21
from src.step22 import xor as X

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "step22"
MODELS = ROOT / "data" / "derived" / "step22"
SPEC = "specs/step22_xor_interference.md"
CLOSED_AT = "1f0050d"
n = 16
OPS = masks_up_to(n, 3)
RUNS_A, SPLITS_A = R21.RUNS, R21.SPLITS
RUNS_B = tuple(f"surface_code_b{b}_d3_r07_center_{c}" for c in ("3_5", "5_3", "5_7", "7_5") for b in ("X", "Z"))
SPLIT_B = 100
IQP4 = (300, 301, 302, 303) + tuple(range(310, 320))
SYNTH = tuple(range(8))
SEED_BOOT = 22000
MAX_PAR = 12
STOP_B_H, STOP_REST_H = 3.0, 1.5
SENT = ("Step 22 tests whether the IQP's QEC losses are its interference, using a classical XOR model with the same "
        "696 parameters; decisive hypotheses are on the unspent r07 runs.")


def path(kind: str, *a) -> Path:
    return RES / kind / ("_".join(str(x) for x in a) + ".json")


def coef(q):
    return coefficients_by_order(q, n, LEVELS)


def nonxor(q) -> float:
    """I(q): order-4..6 distance between q and the XOR model fitted to q's own order-<=3 parities."""
    fx = X.fit_to(q, n)
    a, b = coef(q), coef(X.prob(fx["w"], OPS, n))
    return float(np.mean([np.mean((a[l] - b[l]) ** 2) for l in LEVELS]))


def split(run: str, s: int):
    idx = D19.indices(P20.qec_bits(run))[np.random.default_rng(2000 + s).permutation(D19.SHOTS)]
    return idx[:P20.N_TRAIN], idx[P20.N_TRAIN:]


def xor_on_rows(rows) -> tuple[np.ndarray, dict]:
    fhat = parity_coefficients(empirical_distribution(rows, n))[OPS]
    fx = X.fit(fhat, OPS, OPS)
    return X.prob(fx["w"], OPS, n), {k: v for k, v in fx.items() if k != "w"}


def qec_compare(q_g, q_me, q_x, te) -> dict:
    q_te = empirical_distribution(te, n)
    G = {k: corrected_gap(q, q_te, len(te))["G"] for k, q in (("iqp", q_g), ("maxent", q_me), ("xor", q_x))}
    fG, fM, fX = coef(q_g), coef(q_me), coef(q_x)
    ci = {"xor_maxent": R21.boot_ci(fX, fM, te, LEVELS, SEED_BOOT),
          "xor_iqp": R21.boot_ci(fX, fG, te, LEVELS, SEED_BOOT),
          "iqp_maxent": R21.boot_ci(fG, fM, te, LEVELS, SEED_BOOT)}
    return {"G": G, "ci": ci, "I_iqp": nonxor(q_g), "I_maxent": nonxor(q_me)}


def cell_a(run: str, s: int) -> dict:
    t0 = time.time()
    tr, te = split(run, s)
    z = np.load(R21.MODELS / f"{run}_split_{s}.npz")
    q_g, q_me = z["q_g"], z["q_me"]
    q_x, fx = xor_on_rows(tr[:int(round(FIT_FRAC * len(tr)))])
    c = qec_compare(q_g, q_me, q_x, te)
    ref = json.loads(R21.out(run, s).read_text())["R"]
    return {"run": run, "split": s, "S0_rel_err": abs(c["G"]["iqp"] / c["G"]["maxent"] / ref - 1), "xor_fit": fx,
            **c, "seconds": time.time() - t0}


def cell_b(run: str) -> dict:
    t0 = time.time()
    tr, te = split(run, SPLIT_B)
    fg = fit_and_gate(tr, n, SPLIT_B, empirical_distribution(te, n))
    q_x, fx = xor_on_rows(tr[:fg["N_fit"]])
    MODELS.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(MODELS / f"{run}_split_{SPLIT_B}.npz", q_g=fg["q_g"], q_me=fg["q_me"], q_x=q_x)
    c = qec_compare(fg["q_g"], fg["q_me"], q_x, te)
    return {"run": run, "split": SPLIT_B, "xor_fit": fx, "picks14": fg["picks14"], "picks_val4": fg["picks_val4"],
            "N_fit": fg["N_fit"], **c, "seconds": time.time() - t0}


def iqp4(seed: int) -> dict:
    p = iqp4_target(SIGMA, seed, n)[0]
    idx = sample_indices(p, P20.N_IQP4, seed)
    q_x, fx = xor_on_rows(idx[:int(round(FIT_FRAC * len(idx)))])
    sub = "pilot/" if seed < 310 else ""
    m = json.loads((ROOT / "results" / "step20" / f"{sub}iqp4_seed_{seed}" / "metrics.json").read_text())
    return {"seed": seed, "G_xor": M1.completion_gap(q_x, p, n)["G"], "G_iqp": m["G_iqp"], "G_maxent": m["G_maxent"],
            "xor_fit": fx}


def synth(s: int) -> dict:
    mech = masks_up_to(n, 2)
    pe = np.random.default_rng(22100 + s).uniform(0, 0.03, len(mech))
    p = X.prob(-np.log(1 - 2 * pe), mech, n)
    p = p / p.sum()
    rows = np.random.default_rng(22200 + s).choice(2**n, size=24_000, p=p)
    q_x, fx = xor_on_rows(rows)
    fhat = parity_coefficients(empirical_distribution(rows, n))[OPS]
    me = MaxEntModel(n, 3)
    q_me = me.prob(me.fit_moments(fhat, OPS).params)
    return {"seed": s, "G_xor": M1.completion_gap(q_x, p, n)["G"], "G_maxent": M1.completion_gap(q_me, p, n)["G"],
            "xor_fit": fx}


def launch(jobs: list, stop_h: float) -> int:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    t0, ps, bad = time.time(), {}, []
    while jobs or ps:
        while jobs and len(ps) < MAX_PAR:
            a = jobs.pop(0)
            ps[subprocess.Popen([sys.executable, "-m", "src.step22.run", *a], cwd=ROOT, env=env)] = (a, time.time())
            time.sleep(10)
        time.sleep(5)
        for p in [p for p in ps if p.poll() is not None]:
            a = ps.pop(p)[0]
            print(f"done {a} rc={p.returncode} {(time.time() - t0) / 60:.1f} min", flush=True)
            bad += [a] if p.returncode else []
        for p in [p for p, (a, ts) in ps.items() if a[0] != "--b" and time.time() - ts > STOP_REST_H * 3600]:
            print("STOP-LOSS (1.5 h, non-Part-B job):", ps.pop(p)[0], flush=True)
            p.kill()
            bad.append("stop-loss")
        if time.time() - t0 > stop_h * 3600:
            print("STOP-LOSS; running:", [a for a, _ in ps.values()], "not started:", jobs, flush=True)
            for p in ps:
                p.kill()
            return 1
    return 1 if bad else 0


def todo() -> list:
    j = [["--b", r] for r in RUNS_B if not path("partB", r, SPLIT_B).exists()]
    j += [["--synth", str(s)] for s in SYNTH if not path("synth", s).exists()]
    j += [["--iqp4", str(s)] for s in IQP4 if not path("iqp4", s).exists()]
    j += [["--a", r, str(s)] for s in SPLITS_A for r in RUNS_A if not path("partA", r, s).exists()]
    return j


def cls(ci: dict) -> str:
    return "x" if ci["hi"] < 0 else ("y" if ci["lo"] > 0 else "u")


def counts(cells, key) -> dict:
    c = [cls(x["ci"][key]) for x in cells]
    return {"x_better": c.count("x"), "y_better": c.count("y"), "unresolved": c.count("u")}


def load(kind, keys):
    ps = [path(kind, *k) for k in keys]
    return [json.loads(p.read_text()) for p in ps if p.exists()], len(ps)


def compute() -> dict:
    S, nS = load("synth", [(s,) for s in SYNTH])
    Q, nQ = load("iqp4", [(s,) for s in IQP4])
    A, nA = load("partA", [(r, s) for s in SPLITS_A for r in RUNS_A])
    B, nB = load("partB", [(r, SPLIT_B) for r in RUNS_B])
    out = {"have": {"synth": [len(S), nS], "iqp4": [len(Q), nQ], "partA": [len(A), nA], "partB": [len(B), nB]}}
    if len(S) == nS:
        k = sum(x["G_xor"] < x["G_maxent"] for x in S)
        out["X0"] = {"value": f"{k}/8", "pass": k >= 7}
    if len(B) == nB:
        for h, key in (("C1", "xor_maxent"), ("C2", "xor_iqp")):
            c = counts(B, key)
            out[h] = {"counts": c, "pass": c["x_better"] >= 4 and c["y_better"] == 0}
        out["B_iqp_maxent"] = counts(B, "iqp_maxent")
    if len(Q) == nQ:
        k = sum(x["G_iqp"] < x["G_xor"] for x in Q)
        out["X4"] = {"value": f"{k}/14", "pass": k >= 11}
    if len(A) == nA:
        out["A1"] = {key: counts(A, key) for key in ("xor_maxent", "xor_iqp", "iqp_maxent")}
        Ig = np.array([x["I_iqp"] for x in A])
        dG = np.array([x["ci"]["iqp_maxent"]["point"] for x in A])
        rho = float(spearmanr(Ig, dG)[0])
        rng = np.random.default_rng(22300)
        perm = [spearmanr(Ig, rng.permutation(dG))[0] for _ in range(10_000)]
        out["A2"] = {"rho": rho, "p_perm": float(np.mean(np.abs(perm) >= abs(rho)))}
        out["S0_max_rel_err"] = float(max(x["S0_rel_err"] for x in A))
    out["A3"] = {x.get("run", f"synth/iqp4 {x.get('seed')}") + (f" s{x['split']}" if "split" in x else ""):
                 x["xor_fit"]["n_nonpos"] for x in A + B if x["xor_fit"]["n_nonpos"]}
    return out | {"_A": A, "_B": B, "_Q": Q, "_S": S}


def report() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    c = compute()
    (RES / "verdicts.json").write_text(json.dumps({k: v for k, v in c.items() if not k.startswith("_")}, indent=2))
    pf = lambda h: ("PASS" if c[h]["pass"] else "FAIL") if h in c else "incomplete"
    L = [SENT, "", f"Spec: `{SPEC}`. Completeness: {c['have']}.", "",
         "| ID | Data | Value | Verdict |", "|---|---|---|---|",
         f"| X0 | synthetic XOR, 8 | G_xor < G_maxent: {c.get('X0', {}).get('value')} | {pf('X0')} |",
         f"| C1 | r07, 8 | XOR vs MaxEnt: {c.get('C1', {}).get('counts')} | {pf('C1')} |",
         f"| C2 | r07, 8 | XOR vs IQP: {c.get('C2', {}).get('counts')} | {pf('C2')} |",
         f"| X4 | iqp4, 14 | G_iqp < G_xor: {c.get('X4', {}).get('value')} | {pf('X4')} |", "",
         f"r07 IQP vs MaxEnt (x = IQP better): {c.get('B_iqp_maxent')}.",
         f"A1 (32 spent cells; x = first model better): {c.get('A1')}.",
         f"A2: {c.get('A2')}. S0 max relative error: {c.get('S0_max_rel_err')}.",
         f"A3 (f-hat <= 0 counts, nonzero only): {c['A3'] or 'none'}.", ""]
    f = lambda x: f"{x['point']:+.1e} [{x['lo']:+.1e}, {x['hi']:+.1e}]"
    for name, cells in (("Part B (r07, test)", c["_B"]), ("Part A (spent)", c["_A"])):
        L += [f"### {name}", "", "| run | split | G iqp / maxent / xor | ΔG xor−maxent | ΔG xor−iqp | ΔG iqp−maxent | I(iqp) | I(maxent) |",
              "|---|---|---|---|---|---|---|---|"]
        for x in cells:
            g = x["G"]
            L.append(f"| {x['run'].replace('surface_code_', '')} | {x['split']} | {g['iqp']:.2e} / {g['maxent']:.2e} / "
                     f"{g['xor']:.2e} | {f(x['ci']['xor_maxent'])} | {f(x['ci']['xor_iqp'])} | {f(x['ci']['iqp_maxent'])} | "
                     f"{x['I_iqp']:.1e} | {x['I_maxent']:.1e} |")
        L.append("")
    L += ["### iqp4 (exact G)", "", "| seed | G iqp | G maxent | G xor |", "|---|---|---|---|"]
    L += [f"| {x['seed']} | {x['G_iqp']:.3e} | {x['G_maxent']:.3e} | {x['G_xor']:.3e} |" for x in c["_Q"]]
    L += ["", "### synthetic XOR (exact G)", "", "| seed | G xor | G maxent |", "|---|---|---|"]
    L += [f"| {x['seed']} | {x['G_xor']:.3e} | {x['G_maxent']:.3e} |" for x in c["_S"]]
    txt = "\n".join(L) + "\n"
    (RES / "SUMMARY.md").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


def verify() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    bad = []
    chk = lambda ok, name, msg: (print(("ok   " if ok else "FAIL ") + f"[{name}] {msg}"), ok or bad.append(name))
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    chk(git("ls-files", "--error-unmatch", SPEC).returncode == 0 and git("diff", "--quiet", "HEAD", "--", SPEC).returncode == 0,
        "spec", f"{SPEC} committed and unchanged")
    closed = [f"src/step{i}/" for i in range(1, 22)]
    chk(git("diff", "--name-only", CLOSED_AT, "HEAD", "--", *closed).stdout.strip() == ""
        and git("diff", "--quiet", "HEAD", "--", *closed).returncode == 0, "closed", f"src/step1..21 unchanged since {CLOSED_AT}")
    c = compute()
    chk(all(a == b for a, b in c["have"].values()), "files", f"all instance files exist {c['have']}")
    chk(c.get("S0_max_rel_err", 1) < 1e-9, "S0", "Part A models reproduce step 21's R (< 1e-9 relative)")
    S = RES / "SUMMARY.md"
    txt = S.read_text(encoding="utf-8") if S.exists() else ""
    chk(txt.startswith(SENT) and all(f"| {h} |" in txt and h in c for h in ("X0", "C1", "C2", "X4")), "summary",
        "sentence present; X0, C1, C2, X4 each reported")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step22.py"], cwd=ROOT, capture_output=True, text=True)
    chk(t.returncode == 0, "tests", (t.stdout.strip().splitlines() or ["no output"])[-1])
    print("ALL CHECKS PASS (step 22)" if not bad else f"FAILED: {sorted(set(bad))}")
    return 0 if not bad else 1


def save(res: dict, p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(res, indent=2, default=float))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--synth", type=int)
    ap.add_argument("--iqp4", type=int)
    ap.add_argument("--a", nargs=2)
    ap.add_argument("--b")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if a.synth is not None:
        assert a.synth in SYNTH
        save(synth(a.synth), path("synth", a.synth))
    elif a.iqp4 is not None:
        assert a.iqp4 in IQP4
        save(iqp4(a.iqp4), path("iqp4", a.iqp4))
    elif a.a:
        r, s = a.a[0], int(a.a[1])
        assert r in RUNS_A and s in SPLITS_A
        save(cell_a(r, s), path("partA", r, s))
    elif a.b:
        assert a.b in RUNS_B
        save(cell_b(a.b), path("partB", a.b, SPLIT_B))
    elif a.all:
        return launch(todo(), STOP_B_H)
    elif a.report:
        return report()
    elif a.verify:
        return verify()
    return 0


if __name__ == "__main__":
    sys.exit(main())
