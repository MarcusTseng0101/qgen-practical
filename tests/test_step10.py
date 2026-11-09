"""Step 10 tests (specs/step10_more_restarts.md)."""
import numpy as np

from src.step3.run import replay_inits
from src.step10 import run as r10


def test_constants():
    assert r10.N == 14 and r10.SIGMA == 0.213 and r10.RESTARTS == 10
    assert r10.SEEDS == tuple(range(10, 30))
    assert len(r10.STEP9_LOSERS) == 10
    for s in r10.SEEDS:   # the loser list matches step 9's stored R
        assert (r10.step9(s)["R"] >= 1) == (s in r10.STEP9_LOSERS)


def test_first_three_inits_are_step9s():
    a, b = replay_inits(469, 17, 3), replay_inits(469, 17, 10)[:3]
    assert all(np.array_equal(x, y) for x, y in zip(a, b))
