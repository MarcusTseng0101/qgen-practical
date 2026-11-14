# Step 27 spec: graph errors and gate noise together — FlipIQP with a residual alarm and geometric enlargement

Status: **frozen** once committed. Written 2026-11-15 after step 26 (D1). Exploration ran on spent seeds 980–985
(branch `step18-adversarial`, `explore/step27/`). Claude chose this step under the user's standing instruction to
continue without asking. Every number in §5 is fixed before any model is fitted on the test seeds 1020–1033.

**Deliverable.** A pre-registered test of one complete recipe on data that has both a wrong coupling graph and gate
noise, with verdicts. It is **not** a new model and **not** a threshold sweep. The threshold is fixed here, on spent
data.

**Acceptance (the one definition of done):** `python -m src.step27.run --verify` exits 0. A FAIL hypothesis is a result,
not a reason to edit the check, the tests, or this spec.

## 1. Evidence so far (do not re-derive; act on it)

Spent seeds 980–985. Two couplers are missing from the given graph (step 24 `dropped_edges`). There is gate noise at
rate p and 2% readout noise, N = 1e4. Every fit is FlipIQP (step 26). "ratio" = resid / raw floor, where the raw floor
is Σ(1 − f̂²)/N. R = G / G_me3.

| | given (missing) graph | enlarged 103-gen graph | true graph |
|---|---|---|---|
| ratio, 12 fits | 0.65–7.95 | 0.33–0.54 | 0.36–0.64 |
| R < 1 | 5/12 | 12/12 | 12/12 |
| median R | 1.50 | 0.66 | 0.50 |

- **Correct-graph ratios are low.** Step 26 had 42 more FlipIQP fits on the correct graph, with ratio 0.31–0.63. All 54
  correct-graph fits are ≤ 0.64.
- **Wrong-graph ratios are higher.** Every given-graph fit with R > 1 has ratio ≥ 0.77.
- **Why the step 25 threshold does not carry over.** Step 25 used 0.9 on the *mitigated* floor. FlipIQP has no η, so it
  uses the *raw* floor, and its correct-graph ratios sit lower (median about 0.5).
- **The threshold is 0.75.** It is 0.11 above the largest correct-graph ratio seen. At 0.9 it would have missed seed 981
  at p = 0.005 (ratio 0.77, R 1.21).
- **Always fitting the enlarged graph also won 12/12, but it costs accuracy.** On the correct graph its median R is
  about 0.66, against 0.50 for the true graph. It is reported as an arm, not tested.

## 2. Data and models (load-bearing details)

- **Data.** `src.step26.noise.noisy_grid_iqp(seed, p_gate, eta=0.02)`, unchanged and frozen. The target is the full
  4×4 grid IQP.
- **Given graph.**
  - For `mg*` conditions it is `src.step24.conds.model_masks("miss", seed)`: two edges are dropped, together with every
    plaquette and triple that contains both endpoints.
  - For `fg01` it is the full 85-candidate grid.
  - me_local uses the matching masks.
- **Arms.** All are fitted to the same N = 1e4 order-≤3 raw moments, with no η anywhere.
  - `me3`: MaxEnt(3).
  - `me_local`: MaxEnt on the given grid masks.
  - `given`: FlipIQP on the given graph (20 restarts, θ init 0.3, λ ∈ [0.5, 1], init 1). These settings are step 26's
    and are guesses.
  - `enl`: FlipIQP on the 103-gen enlarged graph (`src.step25.run.ENLARGED`) with the same settings. It is fitted on
    every job.
  - **`flow` (the recipe under test).** Use `given` if its ratio ≤ 0.75 (`THRESH`, a guess fixed in §1); otherwise use
    `enl`.
- **Blindness.** No arm may see θ, p_gate, the dropped edges (other than through the given graph), or N = ∞ moments.

## 3. Failure modes to recognise (symptom → mechanism → what to do)

1. **False alarm on the correct graph.**
   - Symptom: `fg01` ratio > 0.75.
   - Mechanism: gate noise beyond what 16 dampings absorb.
   - Do: report it. A flag sends `flow` to `enl`, which still usually wins. Do not move the threshold.
2. **Missed alarm.**
   - Symptom: an `mg*` seed with ratio ≤ 0.75 and R_given > 1.
   - Do: report the count. It is the cost of the threshold.
3. **λ pinned at 0.5.** Report the count. Do not widen the bound.
4. **Slow fits.** About 30–60 min per FlipIQP fit with 12 parallel jobs. Keep the stop-loss. Never cut restarts.

## 4. Instances

| Condition | Given graph | p_gate | Seeds | Role |
|---|---|---|---|---|
| `mg01` | missing 2 edges | 0.01 | 1020–1033 | test (primary) |
| `fg01` | full | 0.01 | 1020–1033 | test (false alarms) |
| `mg005` | missing 2 edges | 0.005 | 1020–1033 | test |

All seeds below 1014 are spent. 42 jobs, launched in the order above.

## 5. Hypotheses (fixed now)

| ID | Statement | PASS if |
|---|---|---|
| K1 (primary) | the recipe beats MaxEnt(3) with a wrong graph at p = 0.01 | G_flow < G_me3 on ≥ 11/14 (`mg01`); sign test p = 0.029 |
| K2 | the same at p = 0.005 | G_flow < G_me3 on ≥ 11/14 (`mg005`) |
| K3 | the alarm is quiet on the correct graph | flag on ≤ 2/14 (`fg01`) |
| K4 | the recipe still beats MaxEnt(3) on the correct graph | G_flow < G_me3 on ≥ 11/14 (`fg01`) |

Reported, with no verdict, per condition:
- median R against me3 and against me_local of `flow`, `given` and `enl`;
- flag rate and missed-alarm count;
- `flow` < `given` count;
- pinned λ;
- median λ;
- ratio range.

## 6. Readings

- **E1, all PASS.** One recipe (FlipIQP + residual alarm at 0.75 + geometric enlargement) handles graph errors and
  gate noise together. This is the paper's practical pipeline.
- **E2, K3 FAIL, others PASS.** The alarm is not quiet under gate noise. The recipe still wins, but report "always
  enlarge" (`enl`) as the simpler alternative and its cost against `given` on `fg01`.
- **E3, K1 or K2 FAIL.** Graph errors combined with gate noise defeat the recipe at that rate. Report the open limit.

## 7. Budget, stop-loss, lever

- Per job: two FlipIQP fits plus MaxEnt. 12 workers. 42 jobs are about 4–5 h.
- **Stop-loss: 7 h wall clock.** Jobs still running are killed and count as failures.
- **Lever, if the projection after the first 12 jobs exceeds 7 h:** drop `mg005` before it starts. K2 is then
  "not tested" and counts as FAIL. Never cut restarts or `mg01`/`fg01` seeds.
- Each job writes `results/step27/<cond>/seed_<s>/metrics.json`, so the run is resumable.

## 8. Verify (`--verify` exits 0 only if)

- every planned job has a metrics.json, or the stop-loss or the lever is recorded in `run_log.txt`;
- `verdicts.json` is recomputed from the metrics and matches;
- `tests/test_step27.py` passes. Its tests are written before the run:
  - the given graph lacks the dropped edges and is a subset of ENLARGED;
  - `flow` picks `enl` iff ratio > 0.75;
  - the raw floor formula is correct;
  - the test seeds are disjoint from every spent seed (< 1014).

## 9. Build order

1. Tests pass.
2. Commit the code.
3. Launch. After 3 min, check that `errors.log` is empty.
4. `--report`, `--verify`, then the note and the README row on master.

## Working style

- Guesses are marked in code comments.
- Commit with explicit paths. Never push.
- If blocked by a hook, report it; do not rephrase around it.
- Do not edit this spec, the tests, or `--verify` after launch.
