"""Step 36 tests (written before the run)."""
from pathlib import Path

from src.step29 import run as R29
from src.step36 import run as R

EARLIER = [(920, 934), (940, 954), (960, 974), (980, 994), (1000, 1014), (1020, 1034), (1040, 1054), (1060, 1074),
           (1080, 1094), (1100, 1114), (1120, 1134), (1140, 1168), (1168, 1182)]   # last one: timing pilot


def test_seeds_are_fresh():
    assert R.TEST == tuple(range(1190, 1218)) and len(R.jobs()) == 28 and R.SPENT_BELOW == 1182
    for a, b in EARLIER:
        assert not set(R.TEST) & set(range(a, b))


def test_job_is_step29s_run_job_with_output_redirected(monkeypatch):
    calls = []
    monkeypatch.setattr(R29, "run_job", lambda c, s: calls.append((c, s, R29.RESULTS)) or {"cond": c})
    R.run_job(1191)
    assert calls == [("xf02", 1191, Path("results/step36"))]
    assert R29.CONDS["xf02"] == ("full", 0.2) and R29.N_SHOTS == 10_000 and R29.ETA == 0.02
    assert R.out_path(1191) == R29.out_path("xf02", 1191)


def test_counting_strict_and_missing():
    seeds = list(R.TEST)
    X = {s: {"G_flow": 1.0, "G_me3": 2.0} for s in seeds[:19]}
    X[seeds[19]] = {"G_flow": 2.0, "G_me3": 2.0}            # tie is not a win
    V = R.verdicts(loader=lambda: X)                         # seeds 20-27 missing: failures
    assert V["D1"]["wins"] == 19 and V["D1"]["verdict"] == "PASS"
    X[seeds[0]] = {"G_flow": 3.0, "G_me3": 2.0}
    V = R.verdicts(loader=lambda: X)
    assert V["D1"]["wins"] == 18 and V["D1"]["verdict"] == "FAIL"


def test_threshold_is_sign_test_005():
    assert R.NEED == 19 and R.sign_p(19, 28) < 0.05 <= R.sign_p(18, 28)


def test_stop_loss_kills_process_tree():
    assert R.STOP_LOSS_H == 12.0
    assert R.kill_cmd(123) == ["taskkill", "/F", "/T", "/PID", "123"]
