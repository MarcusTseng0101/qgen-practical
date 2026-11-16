# Step 32 spec: a coherence gate that picks CohIQP or FlipIQP from FlipIQP's own residual (N = 1e5)

Status: **frozen** once committed. Written 2026-11-16 after step 31 (K1). Claude chose this step under the user's
standing instruction to pick the recommended option and continue. The gate rule and its threshold come from step 31's
test seeds 1080–1093, which are now spent. Every number in §5 is fixed before any model is fitted on the test seeds
1100–1113.

**Deliverable.** A pre-registered test of one fixed model-choice rule (the gate), on coherent data and on Pauli data.
- It is **not** a new model: CohIQP (step 30) and FlipIQP (step 26) are unchanged.
- It is **not** a threshold sweep.

**Acceptance:** `python -m src.step32.run --verify` exits 0. A FAIL is a result, not a reason to edit the check, the
tests, or this spec.

## 1. Evidence so far (step 31, seeds 1080–1093, N = 1e5, correct graph)

- CohIQP beat FlipIQP on 11/14 coherent seeds, but lost to it on 0/14 Pauli seeds (median R 0.38 against 0.17). So
  neither model is the right default for both noise types.
- **FlipIQP's raw-floor ratio** is resid / Σ(1 − f̂²)/N.
  - Coherent data: above 1.0 on 12/14 seeds (the other two were 0.80 and 0.69).
  - Pauli data: above 1.0 on 1/14 seeds (1.23).
- **Gate.** Fit FlipIQP. If its ratio is above 1.0, fit CohIQP and use it; otherwise use FlipIQP.
  - Post hoc, on step 31's coherent seeds, the gate chose CohIQP on 12/14, and CohIQP was the better model on 10 of
    those 12.
  - On the Pauli seeds it chose FlipIQP on 13/14.
- The threshold 1.0 is a round number read off that data. It is not tuned further here.

## 2. Data and models (load-bearing)

**Conditions.** Both use 2% readout, N = 1e5, `training_moments(p, 100_000, seed, 16)`, and the correct given graph.
They are step 31's `cf` and `pf` exactly: `src.step31.run.data`.
- `cf`: coherent ε_std 0.2.
- `pf`: Pauli 1%.

**Arms.** These are fitted exactly as in step 31's `run_job`. Both fits run on every seed, so that the gate's choice
can be scored against both alternatives.
- `me3`;
- `flip`;
- `coh`.

**Gate.** `gate = "coh" if ratio_flip > 1.0 else "flip"`, and `G_gate = G_coh if gate == "coh" else G_flip`.

## 3. Failure modes

1. **Slow fits.** Step 31 took 9.3 h for the same 56 jobs. Keep the stop-loss.
2. **CohIQP iteration cap.** All step 31 restarts hit maxiter 3000. Report it; do not raise it.
3. **The threshold sits near the edge.** Step 31's coherent seeds had ratios as low as 0.69. Report every ratio within
   0.8–1.25 as "near threshold".

## 4. Instances

| Condition | Seeds | Jobs | Role |
|---|---|---|---|
| `cf` | 1100–1113 | coh, flip | test (primary) |
| `pf` | 1100–1113 | coh, flip | test |

- Seeds up to 1093 are spent, and 1094–1099 are skipped.
- That makes 56 jobs, with launch order cf-coh, pf-coh, cf-flip, pf-flip.

## 5. Hypotheses (fixed now)

| ID | Statement | PASS if |
|---|---|---|
| Z1 (primary) | the gated choice beats MaxEnt(3) on coherent data | G_gate < G_me3 on ≥ 11/14 (`cf`) |
| Z2 | the gated choice beats always-FlipIQP on coherent data | G_gate < G_flip on ≥ 9/14 (`cf`) |
| Z3 | the gate stays with FlipIQP on Pauli data | gate = flip on ≥ 12/14 (`pf`) |
| Z4 | the gated choice beats MaxEnt(3) on Pauli data | G_gate < G_me3 on ≥ 12/14 (`pf`) |

- **Ties.** Z2 counts a seed where the gate picks flip as **not** a win, because G_gate = G_flip there.
- **Missing seeds** count as failures.

Reported, with no verdict:
- the median R of gate, coh and flip in each condition;
- the oracle min(G_coh, G_flip) and how often the gate matches it;
- the ratios near the threshold;
- the coh restarts at maxiter;
- ε at the bound.

## 6. Readings

- **J1, all PASS.** One residual-based gate gives a recipe that handles coherent and stochastic noise on the correct
  graph at N = 1e5. The paper can state this recipe, with the gate threshold as a fixed constant at N = 1e5.
- **J2, Z3 or Z4 FAIL.** The gate misfires on Pauli data. A coherence diagnosis needs something other than FlipIQP's
  residual.
- **J3, Z1 or Z2 FAIL while Z3 and Z4 PASS.** The gate is safe but does not deliver CohIQP's advantage. Step 31's K1
  stays true only for an oracle model choice.

## 7. Budget, stop-loss, lever

- 20 workers. Step 31's 56 jobs took 9.3 h.
- **Stop-loss: 12 h.** Running jobs are killed and count as failures.
- **Lever:** there is none that keeps all four hypotheses testable. If the stop-loss fires, the missing jobs count as
  failures, and that is reported.

## 8. Verify (`--verify` exits 0 only if)

- every planned job has a metrics.json, or the stop-loss is recorded;
- `verdicts.json` is reproducible from the metrics;
- `tests/test_step32.py` passes. Its tests are written before the run, and they check that:
  - the data and arms are step 31's;
  - the seeds are fresh (≥ 1100);
  - the threshold is 1.0;
  - the gate logic is correct on synthetic records;
  - ties count as non-wins in Z2.

## 9. Build order

Tests → commit code → launch → after 3 min check that `errors.log` is empty → `--report`, `--verify` → note and README
row on master.

## Working style

- Guesses are marked in comments.
- Commit with explicit paths. Never push.
- Do not edit this spec, the tests, or `--verify` after launch.
