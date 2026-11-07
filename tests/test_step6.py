"""Step 6 tests (specs/step6_iqp4_scaling_n.md, section 8 item 1)."""
import json
from pathlib import Path

import pytest

from src.step1.models.iqp import IQPModel
from src.step4.targets import iqp4_target
from src.step6.run import default_out, n_generic_generators, run_instance

ROOT = Path(__file__).resolve().parents[1]


def test_n12_reproduces_step5_sigma_0_2_seed_0():
    ref = json.loads((ROOT / "results/step5/iqp4/sigma_0.2/N_inf/seed_0/metrics.json").read_text())
    out = run_instance(12, 0.2, 0)
    assert out["n"] == 12 and out["G_n_params"] == 298
    assert abs(out["R"] - ref["R"]) <= 1e-6 * abs(ref["R"])
    assert out["G_restart_residuals"] == pytest.approx(ref["G_restart_residuals"], rel=1e-6)


@pytest.mark.parametrize("n,want", [(14, 469), (16, 696)])
def test_generic_G_generator_count(n, want):
    assert n_generic_generators(n) == want
    assert IQPModel(n).n_params == want


def test_iqp4_target_n14_has_46_generators():
    _, masks, theta, layout = iqp4_target(0.2, 0, 14)
    assert len(masks) == len(theta) == len(layout) == 14 + 18 + 8 + 6 == 46


def test_paths():
    assert default_out(16, 0.125, 3).as_posix().endswith("results/step6/n_16/sigma_0.125/seed_3")
