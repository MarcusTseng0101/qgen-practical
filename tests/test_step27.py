"""Step 27 tests (written before the run)."""
import numpy as np

from src.step23 import grid as Gd
from src.step24 import conds as C24
from src.step25.run import ENLARGED
from src.step27 import run as R


def test_given_graph_lacks_dropped_edges_and_is_subset_of_enlarged():
    for s in R.TEST:
        gens, _ = R.given_graph("miss", s)
        gs = set(gens.tolist())
        for a, b in C24.dropped_edges(s):
            assert ((1 << a) | (1 << b)) not in gs
        assert gs <= set(ENLARGED.tolist())
        assert len(gens) < len(Gd.LOCAL_GENS)
    full, _ = R.given_graph("full", 1020)
    assert np.array_equal(full, Gd.LOCAL_GENS)


def test_flow_picks_enlarged_iff_ratio_above_threshold():
    assert R.THRESH == 0.75
    assert R.flow_choice(0.7499) == "given"
    assert R.flow_choice(0.75) == "given"
    assert R.flow_choice(0.7501) == "enl"
    assert R.flow_choice(5.0) == "enl"


def test_raw_floor():
    f = np.array([0.0, 0.5, -1.0])
    assert abs(R.raw_floor(f, 100) - (1 + 0.75 + 0) / 100) < 1e-15


def test_test_seeds_are_fresh():
    assert min(R.TEST) >= R.SPENT_BELOW and len(R.TEST) == 14
    assert len(R.jobs()) == 42
