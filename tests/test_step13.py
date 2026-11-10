"""Step 13 tests (written before the grid; specs/step13_residual_gate.md section 4)."""
import csv
from pathlib import Path

import numpy as np

from src.step13.gate import TAU, gated_ratio, outcomes, sign_p

ROOT = Path(__file__).resolve().parents[1]


def test_gate_tie_pick_inclusive():
    R = np.array([0.5, 2.0, 0.5, 3.0])
    r = np.array([1e-3, 1e-3, 0.5, TAU])
    assert gated_ratio(R, r).tolist() == [0.5, 2.0, 1.0, 3.0]
    assert outcomes(R, r) == {"picked": 3, "wins": 1, "losses": 2, "ties": 1}
    assert outcomes([1.0], [0.0])["losses"] == 1          # exact R = 1 when picked counts as a loss


def test_sign_p():
    assert abs(sign_p(14, 2) - 0.00209) < 1e-4
    assert abs(sign_p(9, 3) - 299 / 4096) < 1e-12
    assert sign_p(0, 0) == 1.0


def test_dev_counts_step9():
    rows = list(csv.DictReader(open(ROOT / "results" / "step9" / "table.csv")))
    for n, want in (("16", (16, 14, 2)), ("14", (12, 9, 3))):
        g = [r for r in rows if r["n"] == n]
        o = outcomes([float(r["R"]) for r in g], [float(r["G_train_residual"]) for r in g])
        assert (o["picked"], o["wins"], o["losses"]) == want


def test_fresh_seeds():
    from src.step13.run import SEEDS
    from src.step2 import sweep
    from src.step3 import run as r3
    from src.step4 import run as r4
    from src.step5 import run as r5
    from src.step6 import run as r6
    from src.step7 import run as r7
    from src.step9 import run as r9
    from src.step12 import run as r12
    used = set()
    for m in (sweep, r3, r4, r5, r6, r7, r9, r12):
        used |= set(m.SEEDS)
    used |= set(r12.CAL_SEEDS)
    assert SEEDS == tuple(range(30, 50)) and not used & set(SEEDS)
