"""Step 20 instances and development pilot.

Two kinds of instance, both through src/step20/core.fit_and_gate:
  qec  RUN    Google surface-code detection events (any d3_rXX run), detectors at t = 1, 2 (n = 16).
              Shots permuted with default_rng(2000 + SPLIT_SEED); train = first 3e4, test = other 2e4.
              Completion is scored on the test shots with test noise removed (step 17's corrected gap).
  iqp4 SEED   step 14's iqp4 target (sigma level B); 125 000 shots sampled with seed SEED; completion is
              scored against the exact target. This is where G is known to win (step 14 S1), so it measures
              whether the new check throws away real wins.

Development (this pilot): the 8 spent d3_r03 runs and iqp4 seeds 300-303.

  python -m src.step20.pilot --qec RUN | --iqp4 SEED | --all | --show
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

from src.step1 import metrics as M1
from src.step1.targets import sample_indices
from src.step1.walsh import empirical_distribution
from src.step4.targets import iqp4_target
from src.step14.run import SIGMA
from src.step17.pilot import corrected_gap
from src.step19 import data as D19
from src.step20.core import fit_and_gate

ROOT = Path(__file__).resolve().parents[2]
n = 16
SPLIT_SEED = 100
N_TRAIN = 30_000
N_IQP4 = 125_000
DEV_QEC = D19.RUNS
DEV_IQP4 = (300, 301, 302, 303)
OUT = ROOT / "results" / "step20" / "pilot"


def qec_bits(run: str) -> np.ndarray:
    """(50000, 16): detectors 4..19 (all 8 stabilizers at t = 1, 2); a d3_rXX run has 8 * XX detectors."""
    n_det = 8 * int(run.split("_r")[1][:2])
    raw = np.fromfile(D19.DIR / run / "detection_events.b8", dtype=np.uint8)
    b = np.unpackbits(raw.reshape(-1, (n_det + 7) // 8), axis=1, bitorder="little")[:, :n_det]
    assert b.shape[0] == D19.SHOTS
    return b[:, 4:20].astype(np.int64)


def clean(fg: dict) -> dict:
    return {k: v for k, v in fg.items() if k not in ("q_g", "q_me")}


def run_qec(run: str) -> dict:
    t0 = time.time()
    idx = D19.indices(qec_bits(run))[np.random.default_rng(2000 + SPLIT_SEED).permutation(D19.SHOTS)]
    tr, te = idx[:N_TRAIN], idx[N_TRAIN:]
    q_te = empirical_distribution(te, n)
    fg = fit_and_gate(tr, n, SPLIT_SEED, q_te)
    gi, gm = corrected_gap(fg["q_g"], q_te, len(te)), corrected_gap(fg["q_me"], q_te, len(te))
    return {"kind": "qec", "run": run, "seed": SPLIT_SEED, "N_train": N_TRAIN, "N_test": len(te),
            "R": gi["G"] / gm["G"], "R_raw": gi["G_raw"] / gm["G_raw"], "G_iqp": gi, "G_maxent": gm,
            **clean(fg), "zip_md5": D19.zip_md5(), "seconds": time.time() - t0}


def run_iqp4(seed: int) -> dict:
    t0 = time.time()
    p = iqp4_target(SIGMA, seed, n)[0]
    idx = sample_indices(p, N_IQP4, seed)
    fg = fit_and_gate(idx, n, seed, p)
    gi, gm = M1.completion_gap(fg["q_g"], p, n), M1.completion_gap(fg["q_me"], p, n)
    return {"kind": "iqp4", "seed": seed, "sigma": SIGMA, "N_total": N_IQP4, "R": gi["G"] / gm["G"],
            "G_iqp": gi["G"], "G_maxent": gm["G"], "G_iqp_per_level": gi["per_level"],
            "G_maxent_per_level": gm["per_level"], **clean(fg), "seconds": time.time() - t0}


def save(out: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, default=float))


def launch(jobs: list, stop_h: float) -> int:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    t0 = time.time()
    ps = {subprocess.Popen([sys.executable, "-m", mod, *args], cwd=ROOT, env=env): args for mod, args in jobs}
    bad = []
    while ps:
        time.sleep(5)
        for p in [p for p in ps if p.poll() is not None]:
            a = ps.pop(p)
            print(f"done {a} rc={p.returncode} {(time.time() - t0) / 60:.1f} min", flush=True)
            bad += [a] if p.returncode else []
        if ps and time.time() - t0 > stop_h * 3600:
            print("STOP-LOSS; still running:", list(ps.values()), flush=True)
            for p in ps:
                p.kill()
            return 1
    return 1 if bad else 0


def show(d: Path) -> None:
    for f in sorted(d.rglob("metrics.json")):
        m = json.loads(f.read_text())
        v4 = m["val_iqp"]["4"] / m["val_maxent"]["4"]
        print(f"{m.get('run', m['kind'] + ' ' + str(m['seed'])):40s} R={m['R']:.3g} picks14={m['picks14']} "
              f"val ratio 4/5/6=" + "/".join(f"{m['val_iqp'][l] / m['val_maxent'][l]:.3g}" for l in "456")
              + f" picks_val4={m['picks_val4']} ex={m['excess']:.3g} min={m['seconds'] / 60:.0f}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--qec")
    ap.add_argument("--iqp4", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args(argv)
    if a.qec:
        assert a.qec in DEV_QEC
        save(run_qec(a.qec), OUT / a.qec / "metrics.json")
    elif a.iqp4 is not None:
        assert a.iqp4 in DEV_IQP4
        save(run_iqp4(a.iqp4), OUT / f"iqp4_seed_{a.iqp4}" / "metrics.json")
    elif a.all:
        jobs = [("src.step20.pilot", ["--qec", r]) for r in DEV_QEC if not (OUT / r / "metrics.json").exists()]
        jobs += [("src.step20.pilot", ["--iqp4", str(s)]) for s in DEV_IQP4
                 if not (OUT / f"iqp4_seed_{s}" / "metrics.json").exists()]
        return launch(jobs, 2.5)
    elif a.show:
        show(OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
