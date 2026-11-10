"""Step 19: real QEC detection events through the step 14 gate (specs/step19_real_qec16.md).

  python -m src.step19.run --instance RUN | --all | --report | --verify
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

from src.step19 import data as D
from src.step19.pilot import DEV_RUN, N_TRAIN, fit_run

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "step19"
SPEC = "specs/step19_real_qec16.md"
CLOSED_AT = "97648b2"
RUNS = tuple(r for r in D.RUNS if r != DEV_RUN)
SPLIT_SEED = 100
N_TEST = D.SHOTS - N_TRAIN
STOP_LOSS_H = 2.0
SENT = ("Step 19 was designed after a 2-split pilot on one development run; the 7 tested runs were not used in "
        "the pilot; the gate is step 14's, unchanged; completion is scored on held-out shots with test noise removed; "
        "this is error-correction syndrome data, not IQP-circuit output.")


def path(run: str) -> Path:
    return RESULTS / run / "metrics.json"


def run_all() -> int:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    t0 = time.time()
    ps = {subprocess.Popen([sys.executable, "-m", "src.step19.run", "--instance", r], cwd=ROOT, env=env): r
          for r in RUNS if not path(r).exists()}
    failed = []
    while ps:
        time.sleep(5)
        for p in [p for p in ps if p.poll() is not None]:
            r = ps.pop(p)
            print(f"done {r} rc={p.returncode} {(time.time() - t0) / 60:.1f} min", flush=True)
            if p.returncode:
                failed.append(r)
        if ps and time.time() - t0 > STOP_LOSS_H * 3600:
            print("STOP-LOSS; still running:", list(ps.values()))
            for p in ps:
                p.kill()
            return 1
    return 1 if failed else 0


def med_iqr(x) -> str:
    q = np.percentile(x, [25, 50, 75])
    return f"{q[1]:.3g} [{q[0]:.3g}, {q[2]:.3g}]"


def compute() -> dict:
    ds = [json.loads(path(r).read_text()) for r in RUNS if path(r).exists()]
    if len(ds) < len(RUNS):
        return {"complete": False, "verdicts": {"V1": {"PASS": None}, "V2": {"PASS": None}}}
    R = np.array([d["R"] for d in ds])
    pk = np.array([d["gate_picks_iqp"] for d in ds])
    losses = int((pk & (R >= 1)).sum())
    v = {"V1": {"picked": int(pk.sum()), "wins": int((pk & (R < 1)).sum()), "losses": losses,
                "PASS": bool(losses <= 1), "statement": "gate losses <= 1 of 7 runs"},
         "V2": {"R_ge_1": int((R >= 1).sum()), "PASS": bool((R >= 1).sum() >= 6),
                "statement": "ungated R >= 1 on >= 6/7"}}
    rows = [{"run": d["run"].replace("surface_code_", ""), "R": d["R"], "R_raw": d["R_raw"], "r_N": d["r_N"],
             "floor": d["floor"], "picks": d["gate_picks_iqp"], "val4_ratio": d["val4_iqp"] / d["val4_maxent"],
             "R_level": {l: d["G_iqp"]["per_level"][l] / d["G_maxent"]["per_level"][l] for l in ("4", "5", "6")},
             "D3": d["D3_train"]} for d in ds]
    st = {"R": med_iqr(R), "R_raw": med_iqr([d["R_raw"] for d in ds]), "rows": rows,
          "val4_flags": int(sum(r["val4_ratio"] >= 1 for r in rows))}
    return {"complete": True, "verdicts": v, "stats": st}


def report() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    c = compute()
    (RESULTS / "verdicts.json").write_text(json.dumps(c, indent=2))
    mark = lambda x: "**PASS**" if x else ("**FAIL**" if x is False else "incomplete")
    v = c["verdicts"]
    L = [SENT, "", f"Spec: `{SPEC}`.", "", "| ID | Statement | Counts | Verdict |", "|---|---|---|---|",
         f"| V1 | {v['V1'].get('statement', '')} | picked {v['V1'].get('picked')}, wins {v['V1'].get('wins')}, "
         f"losses {v['V1'].get('losses')} | {mark(v['V1']['PASS'])} |",
         f"| V2 | {v['V2'].get('statement', '')} | R ≥ 1 on {v['V2'].get('R_ge_1')}/7 | {mark(v['V2']['PASS'])} |"]
    if c["complete"]:
        st = c["stats"]
        L += ["", f"Exploratory: median R = {st['R']}; R_raw = {st['R_raw']}; order-4 validation flags G "
                  f"(val4 ratio >= 1) on {st['val4_flags']}/7.", "",
              "| run | picks | R | R_raw | R4 | R5 | R6 | r_N | floor | val4 ratio | D3 |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in st["rows"]:
            lv = r["R_level"]
            L.append(f"| {r['run']} | {r['picks']} | {r['R']:.3g} | {r['R_raw']:.3g} | {lv['4']:.3g} | {lv['5']:.3g} | "
                     f"{lv['6']:.3g} | {r['r_N']:.2g} | {r['floor']:.3g} | {r['val4_ratio']:.3g} | {r['D3']:.3g} |")
    txt = "\n".join(L) + "\n"
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
    closed = [f"src/step{i}/" for i in range(1, 19)]
    chk(git("diff", "--name-only", CLOSED_AT, "HEAD", "--", *closed).stdout.strip() == ""
        and git("diff", "--quiet", "HEAD", "--", *closed).returncode == 0, "closed", f"src/step1..18 unchanged since {CLOSED_AT}")
    ok = True
    for r in RUNS:
        if not path(r).exists():
            ok = False
            print(f"     missing {r}")
            continue
        d = json.loads(path(r).read_text())
        if not (d["run"] == r and d["seed"] == SPLIT_SEED and d["N_train"] == N_TRAIN and d["N_test"] == N_TEST
                and d["n_restarts"] == 3 and d["zip_md5"] == D.ZIP_MD5):
            ok = False
            print(f"     bad {r}")
    chk(ok, "grid", "7 runs: split seed 100, N_train 3e4, N_test 2e4, 3 restarts, zip md5")
    S = RESULTS / "SUMMARY.md"
    txt = S.read_text(encoding="utf-8") if S.exists() else ""
    chk(txt.startswith(SENT), "summary", "SUMMARY opens with the required sentence")
    chk(all(re.search(rf"\| V{i} \|.*\| \*\*(PASS|FAIL)\*\* \|", txt) for i in (1, 2)), "summary", "V1–V2 marked")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step19.py"], cwd=ROOT, capture_output=True, text=True)
    chk(t.returncode == 0, "tests", (t.stdout.strip().splitlines() or ["no output"])[-1])
    print("ALL CHECKS PASS (step 19)" if not bad else f"FAILED: {sorted(set(bad))}")
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if a.instance:
        assert a.instance in RUNS
        out = fit_run(a.instance, SPLIT_SEED)
        path(a.instance).parent.mkdir(parents=True, exist_ok=True)
        path(a.instance).write_text(json.dumps(out, indent=2))
    elif a.all:
        return run_all()
    elif a.report:
        return report()
    elif a.verify:
        return verify()
    return 0


if __name__ == "__main__":
    sys.exit(main())
