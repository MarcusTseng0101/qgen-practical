"""Step 37 tests (specs/step37_wrong_graph_recipe.md section 8), written before the run."""
from src.step25.run import ENLARGED
from src.step31 import run as R31
from src.step37 import run as R


def test_data_are_step31():
    assert R.data is R31.data
    assert (R31.N_SHOTS, R31.ETA, R31.EPS_STD, R31.P_GATE) == (100_000, 0.02, 0.2, 0.01)
    assert R.CONDS == ("cf", "pf") and R.GIVENS == ("full", "miss")


def test_fresh_seeds():
    assert R.TEST == tuple(range(1230, 1244)) and min(R.TEST) >= 1230
    assert len(R.flip_jobs()) == 84


def test_thresholds():
    assert (R.DROP_T, R.GATE_T) == (2.0, 1.0)


def test_graphs():
    assert R.gens_for("enl", 1230) is ENLARGED
    assert len(R.gens_for("full", 1230)) == 85 and len(R.gens_for("miss", 1230)) < 85   # miss: 74-75 by seed


def test_recipe_logic():
    # drop > 2 -> enlarged graph; gate on the enlarged fit's ratio
    c = R.choose({"ratio": 5.0}, {"ratio": 2.0}, "miss")
    assert c["graph"] == "enl" and c["pick"] == "coh" and c["drop"] == 2.5
    c = R.choose({"ratio": 3.0}, {"ratio": 0.9}, "miss")
    assert c["graph"] == "enl" and c["pick"] == "flip"
    # drop == 2 -> stays on the given graph; gate on the given fit's ratio (strictly > 1.0)
    c = R.choose({"ratio": 2.0}, {"ratio": 1.0}, "full")
    assert c["graph"] == "full" and c["pick"] == "coh"
    c = R.choose({"ratio": 1.0}, {"ratio": 0.8}, "full")
    assert c["graph"] == "full" and c["pick"] == "flip"


def test_missing_coh_is_failure(tmp_path, monkeypatch):
    import json
    monkeypatch.setattr(R, "RESULTS", tmp_path)
    s = R.TEST[0]
    for g, ratio in (("miss", 6.0), ("enl", 2.0)):
        f = R.out_path("cf", "flip", g, s)
        f.parent.mkdir(parents=True)
        f.write_text(json.dumps({"ratio": ratio, "G": 1.0, "G_me3": 2.0}))
    r = R.recipe("cf", "miss", s)
    assert r["pick"] == "coh" and r["graph"] == "enl" and r["G_recipe"] is None
    assert ("cf", "coh", "enl", s) in R.needed_coh()
    assert R.verdicts()["A1"]["count"] == 0
