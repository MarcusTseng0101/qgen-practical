# Step 36 spec: clean rerun of the coherent-limit replication (28 fresh seeds, timed stop-loss, pre-registered)

Status: **frozen** once committed. Written 2026-11-18 after step 34
(`specs/step34_coherent_replication.md`, note `notes/2026-11-17_step34_coherent_replication.md`). The user chose
this step ("A", then `/loop advice`).

Step number 35 is skipped. Another session uses `explore/step34` in the same worktree and will likely take 35 next.

**Why.** Step 34 failed (C1 15/28) because 8 of its 28 jobs were killed by a 10 h stop-loss under heavy CPU
contention. The recipe won 15 of the 20 jobs that finished. That FAIL measures compute, not the method.

This step reruns the same test on new fresh seeds, with a stop-loss sized from a timing pilot under the current load.

**Deliverable.** One verdict on whether the recipe beats MaxEnt(3) on G under coherent ε = 0.2 on the correct graph.
- It is **not** a change of model, setting or threshold: the job and the threshold are step 34's.
- Step 34's verdict stays as recorded. This step does not overwrite it, and the paper reports both.

**Acceptance:** `python -m src.step36.run --verify` exits 0.

## 1. Data and model (identical to step 34, load-bearing)

- Each job calls `src.step29.run.run_job("xf02", seed)` with `src.step29.run.RESULTS` pointed at `results/step36`.
- A win is `G_flow < G_me3`, strictly.

## 2. Timing pilot (done before this spec; no test seed was used)

- 14 parallel jobs on seeds 1168–1181, started 2026-11-17 22:22, under a load of about 25 from other processes.
- Per-job times: 98–176 min, median 141 min. All 14 jobs finished, with no errors.
- These seeds are now spent. Their G values are not used anywhere.

## 3. Failure modes

1. **Stop-loss kills jobs again.**
   - Two waves at the pilot maximum need about 6 h, so the stop-loss is 12 h, a 2× margin.
   - If the foreign load rises a lot, jobs can still run out of time. Missing jobs count as failures, and that is
     reported.
2. **Orphaned workers.**
   - `.venv/Scripts/python.exe` is a launcher, so `Popen.kill()` stops only the launcher and leaves the real
     interpreter running.
   - The stop-loss therefore kills the whole process tree with `taskkill /F /T /PID`.
3. **Drift from step 29/34.** The tests check that the step 29 `run_job` object is the one called.

## 4. Instances

- Test seeds 1190–1217, 28 jobs.
- Seeds 1168–1181 are the pilot. Seeds 1182–1189 are skipped.

## 5. Hypothesis (fixed now; same as step 34)

| ID | Statement | PASS if |
|---|---|---|
| D1 (primary) | recipe beats MaxEnt(3) on G under coherent ε = 0.2, correct graph | wins ≥ 19/28 (one-sided sign test, p = 0.044) |

- Missing seeds count as failures.

**Reported, no verdict:**
- the median R with a bootstrap 95% interval (10,000 resamples, rng seed 0);
- the alarm count;
- the given-graph and enlarged median R;
- pooled wins over steps 29 + 33 + 34 + 36. This count is descriptive only: it includes seen seeds, and only finished
  step 34 jobs.

## 6. Readings

- **D1 PASS.**
  - Paper §V states that the recipe beat MaxEnt(3) under coherent errors in this test, with the margin reduced
    (median R from this step).
  - It states that step 29 (10/14) and step 34 (15/28, cut by compute) did not pass.
  - The abstract's "the limit" sentence becomes "the hardest case: the advantage shrinks and two of three tests did
    not pass".
- **D1 FAIL.** The limit stands, and §V adds this third test.

## 7. Budget and stop-loss

- 14 workers, OMP threads 1.
- **Stop-loss: 12 h** from launch. The process tree is killed, and killed jobs count as failures.
- No lever.

## 8. Verify (`--verify` exits 0 only if)

- all 28 metrics.json files exist, or the stop-loss is recorded;
- `verdicts.json` is reproducible from the records;
- `tests/test_step36.py` passes, with tests written before the run:
  - fresh seeds, with no overlap with any earlier test range or the pilot;
  - the step 29 `run_job` is the one called, with output redirected;
  - win counting is strict, and missing seeds fail;
  - the threshold is 19 of 28;
  - the stop-loss kill uses `taskkill /F /T`.

## 9. Build order

Tests → commit code → launch → after 3 min check that `errors.log` is empty → `--report`, `--verify` → note,
README row and paper update on master.

## Working style

- Commit with explicit paths. Never push.
- Do not edit this spec, the tests or `--verify` after launch.
