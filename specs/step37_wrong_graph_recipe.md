# Step 37 spec: one recipe for wrong graphs and coherent noise at N = 1e5 (enlargement alarm + coherence gate)

Status: **frozen** once committed. Written 2026-11-18. Claude chose this step under the user's standing instruction to
pick the recommended option and continue (the user's choice "A": recalibrate the wrong-graph alarm at N = 1e5 together
with the gate). The pilot that motivates the alarm (called "step 34b" in the session, `explore/step34/` on branch
`step18-adversarial`) used seeds 1080–1086, which are spent. Every number in §5 is fixed before any model is fitted on
the test seeds 1230–1243.

**Deliverable.** A pre-registered test of one fixed model-choice recipe at N = 1e5: a wrong-graph alarm that decides
whether to enlarge the graph, followed by step 32b's coherence gate on the chosen graph.
- It is **not** a new model: FlipIQP (step 26), CohIQP (step 30) and the ENLARGED graph (step 25) are unchanged.
- It is **not** a threshold sweep: the alarm threshold 2.0 and the gate threshold 1.0 are fixed here.

**Acceptance:** `python -m src.step37.run --verify` exits 0. A FAIL is a result, not a reason to edit the check, the
tests, or this spec.

## 1. Evidence so far

- **Step 31.** At N = 1e5 the step 27 alarm (FlipIQP ratio > 0.75) fires on 14/14 correct-graph seeds, so it cannot
  tell a wrong graph from noise there.
- **Step 32b.** On the correct graph, the gate "CohIQP if FlipIQP's ratio > 1.0" beat MaxEnt(3) on 28/28 seeds.
- **Pilot (spent seeds 1080–1086).** FlipIQP was fitted on the given graph and on the ENLARGED graph. The **drop**
  is ratio_given / ratio_enl, where both ratios are resid / Σ(1 − f̂²)/N on the same data.

  | | given = full (correct) | given = miss (2 couplers missing) |
  |---|---|---|
  | coherent `cf`, drop range | 1.21–1.63 | 2.95–6.49 |
  | Pauli `pf`, drop range | 0.99–1.47 | 2.50–9.09 |

  - The ranges do not overlap. 2.0 is a round number in the gap.
  - FlipIQP on the miss graph beat MaxEnt(3) on 2/7 (`cf`) and 4/7 (`pf`) seeds.
  - FlipIQP on ENLARGED beat it on 7/7 in both conditions, so enlarging on a correct graph costs little.
- The gate threshold stays 1.0, as in step 32b. A threshold of 0.85 was suggested post hoc in step 32b, but one Pauli
  ENLARGED ratio in the pilot was 0.84, so it is not adopted.

## 2. Data, models and recipe (load-bearing)

**Conditions.** These are step 31's `cf` and `pf` exactly (`src.step31.run.data`): 2% readout, N = 1e5,
`training_moments(p, 100_000, seed, 16)`.
- `cf`: coherent ε_std 0.2.
- `pf`: Pauli 1%.

**Given graph.** The data do not change with the given graph; only the model's graph does.
- `full`: the correct graph, `given_graph("full", seed)`.
- `miss`: two couplers missing, `given_graph("miss", seed)`.

**Fits.** Each is step 31's `run_job` fit, unchanged, except that the graph is an argument:
- `flip` on `full`, `miss` and `enl` (ENLARGED) for every (cond, seed);
- `coh` (untied CohIQP) only on a graph the recipe chooses with the gate firing. These are computed lazily once the
  three FlipIQP fits of that (cond, seed) exist.
- `me3` (MaxEnt(3)), as in step 31.

**Recipe**, for a (cond, given, seed):
1. drop = ratio_flip(given) / ratio_flip(enl).
2. graph\* = `enl` if drop > 2.0 else `given`.
3. pick = `coh` if ratio_flip(graph\*) > 1.0 else `flip`.
4. G_recipe = G of the `pick` fit on graph\*.

## 3. Failure modes

1. **Slow fits.** In the pilot, under CPU contention, FlipIQP fits took 1.5–5.3 h and CohIQP fits took 7.6–8.5 h.
   Check the load before launch. Keep the stop-loss.
2. **CohIQP iteration cap.** All earlier restarts hit maxiter 3000. Report it; do not raise it.
3. **Drop near the threshold.** Report every drop within 1.6–2.5 as "near threshold".
4. **A coh fit is missing** because the stop-loss fired before it finished. That (cond, given, seed) counts as a
   failure in every hypothesis that needs G_recipe.

## 4. Instances

| Condition | Seeds | Fits | Role |
|---|---|---|---|
| `cf` | 1230–1243 | flip on full, miss, enl; coh where the recipe needs it | test (primary) |
| `pf` | 1230–1243 | same | test |

- Seeds up to 1217 are used or claimed by other steps, and 1218–1229 are skipped.
- That makes 84 FlipIQP fits plus the CohIQP fits the recipe needs. The pilot suggests about 20 coh fits.
- Launch order: FlipIQP fits are ordered by seed, then cond, then (full, miss, enl). An eligible coh fit goes to the
  front of the queue.

## 5. Hypotheses (fixed now)

| ID | Statement | PASS if |
|---|---|---|
| A1 (primary) | the recipe beats MaxEnt(3) on a wrong graph with coherent noise | G_recipe < G_me3 on ≥ 11/14 (`cf`, miss) |
| A2 | the recipe beats MaxEnt(3) on a wrong graph with Pauli noise | G_recipe < G_me3 on ≥ 12/14 (`pf`, miss) |
| A3 | the alarm fires on the wrong graph | drop > 2.0 on ≥ 26/28 (miss, both conds) |
| A4 | the alarm stays silent on the correct graph | drop ≤ 2.0 on ≥ 24/28 (full, both conds) |
| A5 | the recipe beats MaxEnt(3) on the correct graph | G_recipe < G_me3 on ≥ 23/28 (full, both conds) |

- **Missing fits** count as failures.

Reported, with no verdict:
- the median R = G / G_me3 of the recipe and of FlipIQP on the given graph, per (cond, given);
- wins of the recipe against FlipIQP on the given graph;
- what the recipe picked (graph\*, arm);
- the drops and gate ratios near their thresholds;
- the coh restarts at maxiter and ε at the bound.

## 6. Readings

- **L1, all PASS.** One recipe (alarm at 2.0, then gate at 1.0) handles a missing-coupler graph and coherent or
  Pauli noise at N = 1e5. The paper can state the full N = 1e5 recipe.
- **L2, A3 or A4 FAIL.** The drop statistic does not separate wrong from correct graphs on fresh seeds; the pilot gap
  was luck at n = 7.
- **L3, A1 or A2 FAIL while A3 and A4 PASS.** The alarm works, but enlargement plus the gate does not recover a wrong
  graph at 1e5.
- **L4, only A5 FAIL.** The recipe costs too much on the correct graph.

## 7. Budget, stop-loss, lever

- 20 workers. Estimate: about 84 × 1.5 h + 20 × 5 h ≈ 230 core-hours, so about 12 h if the machine is not shared.
- **Stop-loss: 16 h.** Running fits are killed with their process tree and count as failures.
- **Lever:** none. If the stop-loss fires, the missing fits count as failures, and that is reported.

## 8. Verify (`--verify` exits 0 only if)

- every FlipIQP fit, and every coh fit the recipe needs, has a metrics.json, or the stop-loss is recorded;
- `verdicts.json` is reproducible from the metrics;
- `tests/test_step37.py` passes. Its tests are written before the run, and they check that:
  - the data are step 31's;
  - the seeds are fresh (≥ 1230);
  - the thresholds are 2.0 and 1.0;
  - the recipe logic is correct on synthetic records;
  - a missing coh fit counts as a failure.

## 9. Build order

Tests → commit code → check the load → launch → after 3 min check that `errors.log` is empty → `--report`, `--verify`
→ note and README row on master.

## Working style

- Guesses are marked in comments.
- Commit with explicit paths. Never push.
- Do not edit this spec, the tests, or `--verify` after launch.
