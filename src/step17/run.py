"""Step 17: real-data probe, MNIST-16 through the step 14 gate (specs/step17_real_mnist16.md).

  python -m src.step17.run --instance 100   (one split)
  python -m src.step17.run --all            (20 splits, 16 workers x 1 thread, stop-loss 1 h)
  python -m src.step17.run --report         (verdicts.json, SUMMARY.md)
  python -m src.step17.run --verify         (acceptance check; exit 0 = done)
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

from src.step17 import data as D
from src.step17.pilot import N_TRAIN, fit_split

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "step17"
SPEC = "specs/step17_real_mnist16.md"
CLOSED_AT = "5317a9d"
SEEDS = tuple(range(100, 120))
N_TEST = 70_000 - N_TRAIN
RESTARTS = 3
WORKERS = 16
STOP_LOSS_H = 1.0
SHA = {"train-images-idx3-ubyte.gz": "440fcabf73cc546fa21475e81ea370265605f56be210a4024d2ca8f203523609",
       "t10k-images-idx3-ubyte.gz": "8d422c7b0a1c1c79245a5bcf07fe86e33eeafee792b84584aec276f5a2dbc4e6"}
SENT = ("Step 17 was designed after a 2-split pilot; split seeds 100–119 are fresh; the 20 splits share one dataset "
        "(MNIST reduced to 16 bits) and are not independent instances; the gate is step 14's, unchanged; completion "
        "is scored on held-out rows with test noise removed.")


def path(s: int) -> Path:
    return RESULTS / f"split_{s}" / "metrics.json"


def run_one(s: int) -> None:
    out = fit_split(s)
    path(s).parent.mkdir(parents=True, exist_ok=True)
    path(s).write_text(json.dumps(out, indent=2))


def run_all() -> int:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    todo = [s for s in SEEDS if not path(s).exists()]
    t0, running, failed = time.time(), {}, []
    while todo or running:
        while todo and len(running) < WORKERS and time.time() - t0 < STOP_LOSS_H * 3600:
            s = todo.pop(0)
            running[subprocess.Popen([sys.executable, "-m", "src.step17.run", "--instance", str(s)], cwd=ROOT, env=env)] = s
        if todo and not running:
            print("STOP-LOSS; not started:", todo); break
        time.sleep(3)
        for p in [p for p in running if p.poll() is not None]:
            s = running.pop(p)
            print(f"done split {s} rc={p.returncode}", flush=True)
            if p.returncode:
                failed.append(s)
    print(f"end {(time.time() - t0) / 60:.1f} min, failed {failed}")
    return 1 if failed else 0


def med_iqr(x) -> str:
    q = np.percentile(x, [25, 50, 75])
    return f"{q[1]:.3g} [{q[0]:.3g}, {q[2]:.3g}]"


def compute() -> dict:
    ds = [json.loads(path(s).read_text()) for s in SEEDS if path(s).exists()]
    if len(ds) < len(SEEDS):
        return {"complete": False, "verdicts": {"U1": {"PASS": None}, "U2": {"PASS": None}}}
    R = np.array([d["R"] for d in ds]); pk = np.array([d["gate_picks_iqp"] for d in ds])
    picked, losses = int(pk.sum()), int((pk & (R >= 1)).sum())
    v = {"U1": {"picked": picked, "wins": int((pk & (R < 1)).sum()), "losses": losses,
                "PASS": bool(picked <= 2 and losses <= 2), "statement": "gate picks IQP on <= 2/20 splits and <= 2 losses"},
         "U2": {"R_ge_1": int((R >= 1).sum()), "PASS": bool((R >= 1).sum() >= 15), "statement": "ungated R >= 1 on >= 15/20"}}
    lv = {l: [d["G_iqp"]["per_level"][l] / d["G_maxent"]["per_level"][l] for d in ds] for l in ("4", "5", "6")}
    st = {"R": med_iqr(R), "R_min": float(R.min()), "excess": med_iqr([d["excess"] for d in ds]),
          "r_N": med_iqr([d["r_N"] for d in ds]), "floor": med_iqr([d["floor"] for d in ds]),
          "D3": med_iqr([d["D3_train"] for d in ds]), "R_level": {l: med_iqr(x) for l, x in lv.items()},
          "G_iqp": med_iqr([d["G_iqp"]["G"] for d in ds]), "G_maxent": med_iqr([d["G_maxent"]["G"] for d in ds]),
          "minutes": float(np.median([d["seconds"] for d in ds]) / 60)}
    return {"complete": True, "verdicts": v, "stats": st}


def report() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    c = compute()
    (RESULTS / "verdicts.json").write_text(json.dumps(c, indent=2))
    mark = lambda x: "**PASS**" if x else ("**FAIL**" if x is False else "incomplete")
    v = c["verdicts"]
    L = [SENT, "", f"Spec: `{SPEC}`.", "", "| ID | Statement | Counts | Verdict |", "|---|---|---|---|",
         f"| U1 | {v['U1'].get('statement', '')} | picked {v['U1'].get('picked')}, wins {v['U1'].get('wins')}, "
         f"losses {v['U1'].get('losses')} | {mark(v['U1']['PASS'])} |",
         f"| U2 | {v['U2'].get('statement', '')} | R ≥ 1 on {v['U2'].get('R_ge_1')}/20 | {mark(v['U2']['PASS'])} |"]
    if c["complete"]:
        st = c["stats"]
        L += ["", "## Exploratory (median [IQR] over 20 splits)", "", "| quantity | value |", "|---|---|"]
        L += [f"| {k} | {st[k]} |" for k in ("R", "R_min", "G_iqp", "G_maxent", "r_N", "floor", "excess", "D3", "minutes")]
        L += [f"| R at level {l} | {x} |" for l, x in st["R_level"].items()]
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
    closed = [f"src/step{i}/" for i in range(1, 17)]
    chk(git("diff", "--name-only", CLOSED_AT, "HEAD", "--", *closed).stdout.strip() == ""
        and git("diff", "--quiet", "HEAD", "--", *closed).returncode == 0, "closed", f"src/step1..16 unchanged since {CLOSED_AT}")
    ok = True
    for s in SEEDS:
        if not path(s).exists():
            ok = False; print(f"     missing split {s}"); continue
        d = json.loads(path(s).read_text())
        if not (d["seed"] == s and d["N_train"] == N_TRAIN and d["N_test"] == N_TEST and d["n_restarts"] == RESTARTS
                and d["data_sha256"] == SHA):
            ok = False; print(f"     bad split {s}")
    chk(ok, "grid", "20 splits: N_train 3e4, N_test 4e4, 3 restarts, pinned SHA-256")
    S = RESULTS / "SUMMARY.md"
    txt = S.read_text(encoding="utf-8") if S.exists() else ""
    chk(txt.startswith(SENT), "summary", "SUMMARY opens with the required sentence")
    chk(all(re.search(rf"\| U{i} \|.*\| \*\*(PASS|FAIL)\*\* \|", txt) for i in (1, 2)), "summary", "U1–U2 marked")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step17.py"], cwd=ROOT, capture_output=True, text=True)
    chk(t.returncode == 0, "tests", (t.stdout.strip().splitlines() or ["no output"])[-1])
    print("ALL CHECKS PASS (step 17)" if not bad else f"FAILED: {sorted(set(bad))}")
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
        run_one(a.instance)
    elif a.all:
        return run_all()
    elif a.report:
        return report()
    elif a.verify:
        return verify()
    return 0


if __name__ == "__main__":
    sys.exit(main())
