"""Step 20 tests (written before the run; specs/step20_heldout_val_gate.md section 4)."""
import re

import numpy as np

from src.step19 import data as D19
from src.step20 import core as C
from src.step20 import pilot as P
from src.step20 import run as r20


def test_r05_kept_detectors_are_t1_t2():
    for run in r20.QEC:
        lines = [l for l in (D19.DIR / run / "circuit_ideal.stim").read_text().splitlines() if l.startswith("DETECTOR")]
        t = [int(re.match(r"DETECTOR\(([^)]*)\)", l).group(1).split(",")[2]) for l in lines]
        assert len(t) == 40 and t[4:20] == [1] * 8 + [2] * 8
        assert P.qec_bits(run).shape == (D19.SHOTS, 16)


def test_test_instances_disjoint_from_pilot():
    assert not set(r20.QEC) & set(P.DEV_QEC) and not set(r20.IQP4) & set(P.DEV_IQP4)
    assert len(r20.QEC) == 8 and len(r20.IQP4) == 10


def test_validation_rows_disjoint_from_fit_rows(monkeypatch):
    seen = {}
    real = C.empirical_distribution

    def spy(idx, n):
        seen.setdefault("calls", []).append(np.asarray(idx).copy())
        return real(idx, n)

    monkeypatch.setattr(C, "empirical_distribution", spy)
    monkeypatch.setattr(C, "fit_restarts", lambda *a, **k: (_ for _ in ()).throw(StopIteration))
    tr = np.random.default_rng(0).integers(0, 16, 1000)
    try:
        C.fit_and_gate(tr, 4, 0, None)
    except StopIteration:
        pass
    fit, val = seen["calls"][:2]
    # rows are positions: fit = first 800 rows, validation = the other 200, no row in both
    assert len(fit) == 800 and len(val) == 200
    assert np.array_equal(np.concatenate([fit, val]), tr)


def test_new_gate_is_step14_and_val4():
    import inspect
    src = inspect.getsource(C.fit_and_gate)
    assert '"picks_val4": bool(picks14 and v_g[4] < v_me[4])' in src
    assert "picks14 = bool(ex <= TAU)" in src and C.TAU == 1e-2
