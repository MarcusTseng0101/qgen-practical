"""Step 9 tests (specs/step9_fresh_seeds.md, build order item 2)."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from src.step9 import run as r9

ROOT = Path(__file__).resolve().parents[1]


def test_seeds_and_sigma():
    assert r9.SEEDS == tuple(range(10, 30))
    assert r9.SIGMA == {14: 0.213, 16: 0.251}
    assert r9.LEVEL == "B"


def test_r4_reproduces_step8():
    d = json.loads((ROOT / "results/step7/n_16/sigma_0.251/seed_1/metrics.json").read_text())
    f = r9.features(d["target_masks"], d["target_theta"])
    assert f["r4"] == pytest.approx(0.415, abs=5e-4)
    assert f["r4_23"] == pytest.approx(0.511, abs=5e-4)


def test_n14_reproduces_step7_with_worker_threads():
    """n = 14, B, seed 0 under the grid's thread settings reproduces step 7's R (rel diff <= 1e-6)."""
    old = json.loads((ROOT / "results/step7/n_14/sigma_0.213/seed_0/metrics.json").read_text())["R"]
    with tempfile.TemporaryDirectory() as td:
        code = ("import sys; from pathlib import Path; from src.step9 import run as r; "
                f"r.run_one(14, 0, Path(r'{td}'))")
        subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=r9.worker_env(), check=True,
                       stdout=subprocess.DEVNULL)
        new = json.loads((Path(td) / "metrics.json").read_text())["R"]
    assert abs(new - old) / abs(old) <= 1e-6, (new, old)
