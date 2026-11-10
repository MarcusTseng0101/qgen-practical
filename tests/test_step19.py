"""Step 19 tests (written before the run; specs/step19_real_qec16.md section 4)."""
import re

from src.step14 import run as r14
from src.step19 import data as D
from src.step19 import pilot as P
from src.step19 import run as r19


def test_kept_detectors_are_t1_t2():
    lines = [l for l in (D.DIR / D.RUNS[0] / "circuit_ideal.stim").read_text().splitlines() if l.startswith("DETECTOR")]
    t = [int(re.match(r"DETECTOR\(([^)]*)\)", l).group(1).split(",")[2]) for l in lines]
    assert len(t) == D.N_DET and t[D.KEEP] == [1] * 8 + [2] * 8


def test_tested_runs_exclude_pilot():
    assert len(r19.RUNS) == 7 and P.DEV_RUN not in r19.RUNS and set(r19.RUNS) < set(D.RUNS)


def test_gate_is_step14s():
    assert P.floor_of is r14.floor_of and P.excess is r14.excess and P.TAU == 1e-2
