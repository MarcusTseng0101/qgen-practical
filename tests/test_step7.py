"""Step 7 tests (specs/step7_collision_matched.md, section 8 item 2)."""
import json
from pathlib import Path

import numpy as np
import pytest

from src.step1 import metrics as M1
from src.step4.targets import iqp4_target
from src.step6.run import run_instance as step6_instance
from src.step7.run import LEVELS, MATCHED_SIGMA, N12_LEVEL, default_out

ROOT = Path(__file__).resolve().parents[1]


def test_n14_sigma_0_2_reproduces_step6():
    ref = json.loads((ROOT / "results/step6/n_14/sigma_0.2/seed_0/metrics.json").read_text())
    out = step6_instance(14, 0.2, 0)    # the code path src/step7/run.run_instance wraps
    assert abs(out["R"] - ref["R"]) <= 1e-6 * abs(ref["R"])
    assert out["G_restart_residuals"] == pytest.approx(ref["G_restart_residuals"], rel=1e-6)


def test_sigma_table_equals_spec_section_2_exactly():
    assert MATCHED_SIGMA == {14: {"A": 0.193, "B": 0.213, "C": 0.236},
                             16: {"A": 0.231, "B": 0.251, "C": 0.274}}
    assert {k: v[0] for k, v in N12_LEVEL.items()} == {"A": 0.15, "B": 0.175, "C": 0.2}


@pytest.mark.parametrize("n", [14, 16])
@pytest.mark.parametrize("level", LEVELS)
def test_matched_sigma_collision_within_1_25x_of_n12_level(n, level):
    sigma = MATCHED_SIGMA[n][level]
    med = float(np.median([M1.collision_ratio(iqp4_target(sigma, s, n)[0]) for s in range(5)]))
    ref = N12_LEVEL[level][1]
    assert ref / 1.25 <= med <= ref * 1.25, (n, level, sigma, med, ref)


def test_paths():
    assert default_out(16, "C", 0).as_posix().endswith("results/step7/n_16/sigma_0.274/seed_0")
    assert default_out(14, "A", 3).as_posix().endswith("results/step7/n_14/sigma_0.193/seed_3")
