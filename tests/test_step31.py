"""Step 31 tests (specs/step31_coherent_shots.md section 8), written before the run."""
import json
from pathlib import Path

import numpy as np

from src.step1 import metrics as M1
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step26 import noise as N26
from src.step26.flipiqp import FlipIQP
from src.step29 import noise as N29
from src.step30 import cohiqp as C30
from src.step31 import run as R

ROOT = Path(__file__).resolve().parents[1]


def test_objects_unchanged():
    assert R.FlipIQP is FlipIQP
    assert R.C30.CohIQP is C30.CohIQP
    assert C30.COH_OPTS["maxiter"] == 3000 and C30.EPS_MAX == 1.5
    assert R.N29.coherent_grid_iqp is N29.coherent_grid_iqp
    assert R.N26.noisy_grid_iqp is N26.noisy_grid_iqp
    assert (R.N_SHOTS, R.ETA, R.EPS_STD, R.P_GATE) == (100_000, 0.02, 0.2, 0.01)


def test_fresh_seeds():
    assert R.TEST == tuple(range(1080, 1094)) and min(R.TEST) >= 1080
    assert len(R.jobs()) == 56


def test_cf_data_equals_step29_xf02():
    assert np.array_equal(R.data("cf", 1060), N29.coherent_grid_iqp(1060, 0.2, 0.02))


def test_me3_matches_pilot_seed_1060():
    pilot = json.loads((ROOT / "explore/step31/out/recipe5_1060.json").read_text())
    p = R.data("cf", 1060)
    fhat, ops = training_moments(p, 100_000, 1060, 16)
    me = MaxEntModel(16, 3)
    G = M1.completion_gap(me.prob(me.fit_moments(fhat, ops).params), p, 16)["G"]
    assert abs(G - pilot["G_me3"]) <= 1e-9 * max(1.0, abs(pilot["G_me3"]))


def test_nitlog_passthrough():
    log = R._NitLog(lambda *a, **k: type("r", (), {"nit": 7})())
    log()
    assert log.nit == [7]
    assert R.C30.minimize is not log   # the patch is only applied inside run_job
