# Step 37 result: one recipe handles a wrong graph and coherent or Pauli noise at N = 1e5 (L1: A1–A5 all PASS)

**Provenance.**
- Spec: `specs/step37_wrong_graph_recipe.md` (d52a30b).
- Code: branch `step18-adversarial` 96705b0 (`src/step37/run.py`, `tests/test_step37.py`).
- Results: 3a79da4 (`results/step37/`).
- `python -m src.step37.run --verify` → ALL PASS.
- Pilot (spent seeds 1080–1086): `explore/step34/` on the same branch. It was called "step 34b" in the session and is
  not a pre-registered result.

**Recipe** (N = 1e5, 2% readout):
1. Fit FlipIQP on the given graph and on the ENLARGED graph.
2. drop = ratio_given / ratio_enl, where ratio = resid / Σ(1 − f̂²)/N.
3. If drop > 2.0, use the ENLARGED graph.
4. On the chosen graph, if FlipIQP's ratio > 1.0, fit CohIQP and use it; otherwise use FlipIQP.

The data are step 31's: `cf` is coherent ε_std 0.2, and `pf` is Pauli 1%. The given graph is either the correct one
(`full`) or one with 2 couplers missing (`miss`). Seeds 1230–1243 are fresh. R = G / G_me3, and lower is better.

## Verdicts

| ID | Statement | Count | Need | Verdict | As-spec at 05:04 |
|---|---|---|---|---|---|
| A1 (primary) | recipe beats MaxEnt(3), coherent, wrong graph | 13/14 | 11 | **PASS** | 12/14 PASS |
| A2 | recipe beats MaxEnt(3), Pauli, wrong graph | 13/14 | 12 | **PASS** | 13/14 PASS |
| A3 | alarm fires on the wrong graph | 28/28 | 26 | **PASS** | 28/28 PASS |
| A4 | alarm silent on the correct graph | 28/28 | 24 | **PASS** | 28/28 PASS |
| A5 | recipe beats MaxEnt(3), correct graph | 26/28 | 23 | **PASS** | 24/28 PASS |

**Reading: L1.** One recipe handles a missing-coupler graph and coherent or Pauli noise at N = 1e5.

## The run was interrupted once; both readings pass

| When (2026-11-18/19) | Event |
|---|---|
| 13:04 | Launch with 20 workers; the 16 h stop-loss falls at 05:04. |
| ~00:56 | A Claude session restart kills the launcher and all workers. 72/84 FlipIQP and 16 CohIQP fits are on disk. |
| ~01:37 | The user relaunches with the same resumable `--all`, which skips finished fits. |
| 05:25 | All 84 FlipIQP and all 25 needed CohIQP fits are done. There are no errors. |

- The fits are seeded, so a restarted fit gives the same result.
- The relaunch overwrote `run_log.txt`, so the first launch's log is lost; its metrics files remain. This is recorded
  in `results/step37/run_log_part1_note.txt`.
- Four CohIQP fits finished after 05:04, between 05:16 and 05:25. Counting them as missing, as the spec's stop-loss
  would, still passes every hypothesis (`verdicts_as_spec_0504.json`).

## Reported (no verdict)

| cond / given | alarm fired | drop range | picked | recipe median R | FlipIQP-on-given median R | recipe beats FlipIQP-on-given |
|---|---|---|---|---|---|---|
| cf / full | 0/14 | 1.17–1.47 | full/coh 12, full/flip 2 | 0.42 | 0.56 | 10/14 |
| cf / miss | 14/14 | 3.74–45.8 | enl/coh 11, enl/flip 3 | 0.48 | 2.02 | 14/14 |
| pf / full | 0/14 | 0.54–1.69 | full/flip 12, full/coh 2 | 0.20 | 0.20 | 1/14 |
| pf / miss | 14/14 | 4.98–41.5 | enl/flip 14 | 0.24 | 1.73 | 14/14 |

- **The alarm is far from its threshold.** The highest drop on the correct graph was 1.69, and the lowest on the
  wrong graph was 3.74. Only one drop fell inside the 1.6–2.5 near-threshold band: a correct-graph Pauli seed at 1.69.
- **Enlargement recovers the wrong graph.** FlipIQP on the miss graph is worse than MaxEnt(3) (median R about 2). After
  the recipe enlarges, R is close to the correct-graph values.
- **The four losses against MaxEnt(3):**
  - cf / miss, seed 1234: R 1.36 (enl/coh), against 5.29 for FlipIQP on the given graph.
  - pf / miss, seed 1230: R 1.03 (enl/flip).
  - cf / full, seed 1243: R 1.07 (full/coh).
  - pf / full, seed 1234: R 1.14. The gate fired at ratio 1.10, just over 1.0. FlipIQP would have given 1.05, which
    also loses.
- **The gate fired on Pauli data on 2 of 14 seeds** (pf / full), against 0/14 in step 32b.
  - Seed 1234, ratio 1.10: CohIQP gave R 1.14 against FlipIQP's 1.05, so this was a misfire.
  - Seed 1241, ratio 1.44: CohIQP gave R 0.51 against FlipIQP's 0.62, so switching helped.
  - In both conditions, several gate ratios fell within 0.8–1.25.
- **CohIQP convergence is as before.** 124 restarts hit the 3000-iteration cap, and ε reached the bound 34 times, over
  25 fits. CohIQP's R may therefore be pessimistic.

## For the paper

- **Full recipe at N = 1e5.**
  1. Fit FlipIQP on the given graph and on an enlarged graph.
  2. If the residual drops by more than a factor 2, use the enlarged graph.
  3. If FlipIQP's raw-floor ratio is above 1.0 on the chosen graph, also fit CohIQP and use it.
- **What it delivered.** On fresh seeds it beat MaxEnt(3) on 52/56 (graph × noise) instances. The alarm was right on
  56/56.
- **State plainly:**
  - the one interruption, and both readings;
  - the CohIQP iteration cap;
  - that the gate threshold sits close to some seeds in both noise types.
- The step 27 alarm (ratio > 0.75) does not transfer to N = 1e5 (step 31). This drop statistic replaces it there.
  Whether it works at N = 1e4 has not been tested.

## Next (recommended, not started)

- Test the drop alarm at N = 1e4, so that one alarm covers both shot counts.
- Optionally, extend the README's recipe summary and the paper's recipe section with this result.
