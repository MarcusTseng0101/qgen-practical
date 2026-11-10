"""Step 16 tests (written before the grid; specs/step16_shot_threshold.md section 4)."""
from src.step13.gate import TAU
from src.step14 import run as r14
from src.step16 import run as r16


def test_gate_is_step14s():
    assert r16.floor_of is r14.floor_of and r16.excess is r14.excess and r16.TAU == TAU == 1e-2


def test_only_N_3e4():
    assert r16.NS_SHOTS == (30_000,) and r16.IDS == {30_000: ("T1", "T2")}


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
    for m in (sweep, r3, r4, r5, r6, r7, r9, r12, r13, r14):
        used |= set(m.SEEDS)
    used |= set(r12.CAL_SEEDS) | {10, 11, 12, 13}          # step 14 and step 15 pilot seeds
    assert r16.SEEDS == tuple(range(70, 90)) and not used & set(r16.SEEDS)
