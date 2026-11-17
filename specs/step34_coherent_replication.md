# Step 34 spec: is the coherent limit real? Replication of step 29's xf02 test on 28 fresh seeds (pre-registered)

Status: **frozen** once committed. Written 2026-11-17 after step 33. The user chose this step ("A").

**Why.** The paper's stated limit (§V) rests on one test: step 29, condition `xf02`, where the step 27 recipe on the
correct graph beat MaxEnt(3) on G on only 10 of 14 seeds (1060–1073; median R 0.74; FAIL at 11).

Step 33 fitted the same recipe on the same condition for 14 other fresh seeds (1120–1133). There it won G on 13 of 14
(median R 0.58), but that number was reported only, with no verdict. Two sets of 14 disagree, so this step settles
the question on a larger fresh set.

**Deliverable.** One pre-registered verdict on the `xf02` win rate, at a sample size that the step 29 / step 33
difference cannot swing.
- It is **not** a new model, recipe or noise setting: the job function is step 29's `run_job`, imported unchanged.
- It is **not** a pooled test that reuses seen seeds: only the 28 fresh seeds count for the verdict. The pooled
  numbers are reported only.

**Acceptance:** `python -m src.step34.run --verify` exits 0. A FAIL is a result, not a reason to edit anything.

## 1. Data and model (load-bearing)

- Each job calls `src.step29.run.run_job("xf02", seed)` with `src.step29.run.RESULTS` pointed at `results/step34`.
  Nothing else in step 29 changes.
- The setting is therefore unchanged:
  - target `coherent_grid_iqp(seed, 0.2, 0.02)`, N = 1e4;
  - the recipe on the correct graph (FlipIQP on LOCAL_GENS; refit on ENLARGED if resid/F > 0.75);
  - opponent `MaxEntModel(16, 3)`.
- The scored quantity is `G_flow` vs `G_me3`.
- A win is `G_flow < G_me3`, strictly.

## 2. Failure modes

1. **Drift from step 29.** A copied or edited job function would test something else. The tests check that step 34
   calls step 29's `run_job` object itself and that the written records carry `cond = "xf02"` and `eps_std = 0.2`.
2. **Seed reuse.** The tests check that 1140–1167 overlaps no earlier test range (920–1133).
3. **Shared CPU.** At freeze time the load average was about 30 on 32 cores from another session's jobs. Do not touch
   them. The stop-loss covers the slowdown.

## 3. Instances

- Seeds 1140–1167, 28 jobs.
- 1134–1139 are skipped.

## 4. Hypothesis (fixed now)

| ID | Statement | PASS if |
|---|---|---|
| C1 (primary) | recipe beats MaxEnt(3) on G under coherent ε = 0.2, correct graph | wins ≥ 19/28 |

- 19/28 is a one-sided sign test at p = 0.044.
- Missing seeds count as failures.

**Reported, no verdict:**
- the median R (G_flow / G_me3) with a bootstrap 95% interval (10,000 resamples, rng seed 0);
- alarm count, and the median R of the given-graph and enlarged fits;
- **pooled** wins and the sign-test p over steps 29 + 33 + 34 (56 seeds), read from `results/step29/xf02` and from
  step 33's `xf02` records (`model.G` vs `me3.G`). These counts are descriptive because 28 of the seeds were seen
  before this spec.

## 5. Readings

- **C1 PASS.** Coherent over-rotations at ε = 0.2 weaken the advantage but do not remove it. Paper §V and the
  abstract are rewritten: step 29's 10/14 is described as an unfavourable instance set, and the limit moves to "a
  smaller margin" (median R from this step).
- **C1 FAIL (≤ 18).** The limit stands as written. The step 33 count of 13/14 is noted in §VI as instance variation.

## 6. Budget and stop-loss

- 14 workers, OMP threads 1.
- **Stop-loss: 10 h** from the first launch. Running jobs are then killed and count as failures.
- No lever.

## 7. Verify (`--verify` exits 0 only if)

- all 28 metrics.json files exist, or the stop-loss is recorded in run_log.txt;
- `verdicts.json` is reproducible from the records;
- `tests/test_step34.py` passes, with these tests written before the run:
  - fresh seeds;
  - the step 29 `run_job` is the one called, with output redirected;
  - win counting is strict, and missing seeds fail;
  - the threshold 19 matches p < 0.05 for n = 28.

## 8. Build order

Tests → commit code → launch → after 3 min check that `errors.log` is empty → `--report`, `--verify` → note,
README row and paper update on master.

## Working style

- Commit with explicit paths. Never push.
- Do not edit this spec, the tests or `--verify` after launch.
