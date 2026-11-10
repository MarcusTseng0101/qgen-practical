"""Step 14 tests (written before the grid; specs/step14_finiteN_gate.md section 4)."""
import numpy as np

from src.step13.gate import TAU, gated_ratio, outcomes
from src.step14.run import SEEDS, excess, floor_of


def test_floor_hand_example():
    assert abs(floor_of([0.0, 0.5, -1.0], 100) - (1 + 0.75 + 0) / 100) < 1e-15


def test_reduces_to_step13_when_floor_zero():
    R = np.array([0.5, 2.0, 0.7]); r = np.array([1e-3, 5e-3, 0.3])
    ex = np.array([excess(x, 0.0) for x in r])
    assert gated_ratio(R, ex).tolist() == gated_ratio(R, r).tolist()
    assert outcomes(R, ex) == outcomes(R, r)


def test_inclusive_at_tau():
    assert outcomes([0.5], [TAU])["picked"] == 1
    assert outcomes([0.5], [np.nextafter(TAU, 1)])["picked"] == 0


def test_fresh_seeds():
    from src.step2 import sweep
    from src.step3 import run as r3
    from src.step4 import run as r4
    from src.step5 import run as r5
    from src.step6 import run as r6
    from src.step7 import run as r7
    from src.step9 import run as r9
    from src.step12 import run as r12
    from src.step13 import run as r13
    used = set()
    for m in (sweep, r3, r4, r5, r6, r7, r9, r12, r13):
        used |= set(m.SEEDS)
    used |= set(r12.CAL_SEEDS) | {10, 11, 12, 13}          # pilot seeds
    assert SEEDS == tuple(range(50, 70)) and not used & set(SEEDS)
