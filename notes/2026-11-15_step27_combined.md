# Step 27 result: one recipe handles a wrong graph and gate noise together (reading E1, K1–K4 all PASS)

Spec: `specs/step27_combined.md` (62d2e7e, frozen before the run). Code: branch `step18-adversarial` 48fa86e. Results:
`results/step27/` (dd3e481 on that branch). `python -m src.step27.run --verify` → ALL PASS (exit 0).

The run took 4.0 h of the 7 h stop-loss. The projection after 12 jobs was 4.59 h, so the lever did not fire. There were no
errors and no missing jobs.

**The recipe under test (`flow`):**
1. Fit FlipIQP (local IQP + 16 learned per-qubit dampings, raw moments, no η) on the given graph.
2. If resid / raw floor > 0.75, refit FlipIQP on the 103-candidate geometric graph.

**Data.** Full 4×4 grid IQP with gate-level Pauli noise and 2% readout noise, N = 1e4. In the `mg*` conditions the
given graph lacks 2 couplers. R = G / G_me3.

## Verdicts (fresh seeds 1020–1033)

| ID | Statement | Result | Verdict |
|---|---|---|---|
| K1 (primary) | recipe beats MaxEnt(3), wrong graph, p = 0.01 | 12/14, median R 0.66 | **PASS** |
| K2 | the same, p = 0.005 | 13/14, median R 0.56 | **PASS** |
| K3 | alarm quiet on the correct graph, p = 0.01 | 1/14 flagged (max 2) | **PASS** |
| K4 | recipe beats MaxEnt(3) on the correct graph, p = 0.01 | 13/14, median R 0.57 | **PASS** |

## Reported (no verdict)

| cond | flow R (wins) | given only R (wins) | always-enlarged R (wins) | flags | missed alarms | flow R vs me_local |
|---|---|---|---|---|---|---|
| mg01 | 0.66 (12/14) | 1.11 (6/14) | 0.71 (12/14) | 8 | 1 | 0.16 |
| mg005 | 0.56 (13/14) | 1.26 (4/14) | 0.55 (13/14) | 12 | 0 | 0.13 |
| fg01 | 0.57 (13/14) | 0.57 (13/14) | 0.71 (12/14) | 1 | 1 | 0.20 |

**The alarm is needed.** Without it, a wrong graph loses to MaxEnt(3) on most seeds: 6/14 wins at p = 0.01 and 4/14 at
p = 0.005.

**The alarm separates the conditions less cleanly at p = 0.01 than at p = 0.005.** 6 of the 14 wrong-graph seeds at
p = 0.01 stay below 0.75, because gate noise blurs the evidence of the missing couplers. On 5 of those 6 the given-graph
fit still wins. The single missed alarm is seed 1032 (ratio 0.65, R 1.01).

**Always enlarging is a close alternative.** It also wins 12/14 and 13/14 on wrong graphs, but costs accuracy on the
correct graph (median R 0.71 against 0.57).

**Correct-graph ratios.** Across 14 fresh seeds the ratio was 0.29–0.77. The one flag is seed 1020 at 0.77, just above
the threshold. After enlargement that seed still won (R 0.72).

**The losses** are 4 seeds in all:

| cond | seed | flow R | note |
|---|---|---|---|
| mg01 | 1024 | 1.12 | flagged; the same seed loses on the correct graph too (R 1.07) |
| mg01 | 1032 | 1.01 | missed alarm |
| fg01 | 1024 | 1.07 | correct graph |
| mg005 | 1028 | 1.01 | flagged |

**Pinned λ.** One λ pinned at 0.5 on the given graph, and 7 on the enlarged graph across all conditions.

## Reading: E1

A single recipe handles both departures with no calibration: FlipIQP + residual alarm at 0.75 (raw floor) + geometric
enlargement. It handles missing couplers and gate noise up to 1%, and it barely touches correctly specified data.

This replaces the step 25 pipeline as the paper's practical pipeline. Step 25 needed a calibrated η and failed under gate
noise (step 26).

## Status of the simulation programme

The pre-registered steps 23–27 close the simulated-robustness story for the 4×4 connectivity-prior IQP:
- ideal data (23);
- missing couplers, extra candidates and readout noise (24, 25);
- gate noise (26);
- both together (27).

**Open limits:**
- correlated and coherent noise, crosstalk;
- larger devices (n > 16, where exact G is no longer available);
- real hardware data.

The last needs the user, either through money or outside contact.
