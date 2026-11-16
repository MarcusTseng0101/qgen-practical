"""Step 32 tests (specs/step32_coherence_gate.md section 8), written before the run."""
from src.step31 import run as R31
from src.step32 import run as R


def test_data_and_arms_are_step31():
    assert R.R31 is R31
    assert R.CONDS == ("cf", "pf") and R.ARMS == ("coh", "flip")
    assert (R31.N_SHOTS, R31.ETA, R31.EPS_STD, R31.P_GATE) == (100_000, 0.02, 0.2, 0.01)


def test_fresh_seeds():
    assert R.TEST == tuple(range(1100, 1114)) and min(R.TEST) >= 1100
    assert len(R.jobs()) == 56


def test_threshold():
    assert R.THRESH == 1.0


def test_gate_logic():
    coh = {"G": 1.0}
    hi = {"G": 2.0, "G_me3": 3.0, "ratio": 1.01}
    lo = {"G": 2.0, "G_me3": 3.0, "ratio": 1.0}
    assert R.gate_record(coh, hi)["pick"] == "coh" and R.gate_record(coh, hi)["G_gate"] == 1.0
    assert R.gate_record(coh, lo)["pick"] == "flip" and R.gate_record(coh, lo)["G_gate"] == 2.0


def test_flip_pick_is_not_a_z2_win():
    d = R.gate_record({"G": 0.1}, {"G": 2.0, "G_me3": 3.0, "ratio": 0.5})
    assert not d["G_gate"] < d["G_flip"]
