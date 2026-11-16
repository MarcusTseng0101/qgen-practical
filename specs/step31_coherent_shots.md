# Step 31 spec: does N = 1e5 make the coherent-aware model (CohIQP) beat the coherent limit?

Status: **frozen** once committed. Written 2026-11-16 after step 30. Claude chose this step under the user's standing
instruction to pick the recommended option and continue. The pilot ran on spent seeds 1060–1073 (branch
`step18-adversarial`, `explore/step31/`). Every number in §5 is fixed before any model is fitted on the test seeds
1080–1093.

**Deliverable.** A pre-registered test of step 30's **untied CohIQP, unchanged**, at N = 1e5 shots. The data are the
coherent-miscalibration data of step 29 on the correct graph, plus a Pauli-noise control. The deliverable is **not** a new
model, **not** a new alarm threshold, and **not** a hardware claim.

**Acceptance:** `python -m src.step31.run --verify` exits 0. A FAIL is a result, not a reason to edit the check, the
tests, or this spec.

## 1. Evidence so far (spent seeds 1060–1073, step 29 `xf02` data: ε_std 0.2, correct graph, 2% readout)

R = G / G_me3, with MaxEnt(3) fitted on the same shots. Lower is better.

| Model | N | Wins vs me3 | Median R |
|---|---|---|---|
| step 27 recipe (flow) | 1e4 (step 29) | 10/14 | 0.74 |
| CohIQP untied | 1e4 (step 30) | 12/14 | 0.75 |
| step 27 recipe (flow) | 1e5 | 9/12 | 0.77 |
| FlipIQP, given graph | 1e5 | 8/12 | 0.89 |
| **CohIQP untied** | **1e5** | **12/14** | **0.58** |
| FlipIQP, given graph | ∞ (exact moments) | 9/13 | 0.80 |

- **FlipIQP is bias-limited.** More shots do not help it. Even with exact moments it wins only 9/13, because per-qubit
  damping is the wrong model for a unitary error.
- **CohIQP improves with shots.** Its median R falls from 0.75 to 0.58.
  - On the hardest seed, 1067, R falls from 0.74 to 0.43; the recipe got 1.21 at 1e4.
  - The two seeds it loses, 1064 and 1066, are also lost by every other arm.
- **Head-to-head at N = 1e5,** CohIQP beats the recipe's flow on 8/12 seeds.
- **The alarm does not transfer to N = 1e5.**
  - On the correct graph, the given-graph ratio resid / Σ(1 − f̂²)/N is 1.3–4.5, so all 12 seeds are flagged.
  - The 0.75 threshold was set at N = 1e4. At 1e5 the noise floor shrinks 10×, but the model bias does not.
  - This is reported only. No threshold is tested here.
- **No pilot was run for the Pauli control (Y3).** The step 30 control at N = 1e4 (g01, 1000–1013) gave CohIQP
  13/14 wins with median R 0.79, against FlipIQP's 0.62.

## 2. Data and models (load-bearing)

**Conditions.** Both use 2% readout, N = 1e5, `training_moments(p, 100_000, seed, 16)`, and the correct (full) given
graph from `src.step27.run.given_graph("full", seed)`.
- `cf`: coherent data, `src.step29.noise.coherent_grid_iqp(seed, 0.2, 0.02)`.
- `pf`: Pauli data, `src.step26.noise.noisy_grid_iqp(seed, 0.01, 0.02)`.

**Arms.** Each is fitted on the same moments.
- `me3`: `MaxEntModel(16, 3)`.
- `flip`: `FlipIQP(16, gens).fit(fhat, ops, seed=seed)`, the recipe's given-graph fit with step 26 settings.
- `coh`: `CohIQP(16, gens, tied=False).fit(fhat, ops, seed=seed)`, step 30 unchanged (5 restarts, maxiter 3000,
  EPS_MAX 1.5).

`src/step26`, `src/step29` and `src/step30` are imported unchanged.

## 3. Failure modes

1. **Slow fits.** One coh fit took 2.9–3.8 h in the pilot with 16 parallel jobs.
   - Keep the stop-loss.
   - Do not cut restarts or maxiter.
2. **maxiter 3000 is a guess (step 30).** Report the count of coh restarts that hit it. Do not raise it.
3. **ε at the bound 1.5.** Report the count. Do not widen the bound.

## 4. Instances

| Condition | Seeds | Jobs | Role |
|---|---|---|---|
| `cf` | 1080–1093 | coh, flip | test (primary) |
| `pf` | 1080–1093 | coh, flip | control |

Seeds up to 1073 are spent, and 1074–1079 are skipped. This gives 56 jobs: `me3` runs inside every job (it is cheap),
and coh and flip are separate jobs. Launch order is cf-coh, pf-coh, cf-flip, pf-flip.

## 5. Hypotheses (fixed now)

| ID | Statement | PASS if |
|---|---|---|
| Y1 (primary) | CohIQP beats MaxEnt(3), coherent data, N = 1e5 | G_coh < G_me3 on ≥ 11/14 (`cf`); sign p = 0.029 |
| Y2 | CohIQP beats FlipIQP head-to-head, coherent data, N = 1e5 | G_coh < G_flip on ≥ 10/14 (`cf`); sign p = 0.090 |
| Y3 (control) | CohIQP still beats MaxEnt(3) under Pauli noise, N = 1e5 | G_coh < G_me3 on ≥ 11/14 (`pf`) |

Missing seeds count as failures.

Reported, with no verdict:
- median R of coh and flip in both conditions;
- head-to-head coh vs flip on `pf`;
- the ratio ranges (alarm transfer);
- coh restarts at maxiter;
- ε at the bound;
- median flip λ.

## 6. Readings

- **K1, Y1 Y2 Y3 all PASS.** With 1e5 shots, the coherent-aware model removes step 29's limit on the correct graph,
  and it is safe under Pauli noise. For coherent-dominated devices, the recipe becomes CohIQP at N ≥ 1e5. The alarm
  threshold is then an open item, because it does not transfer.
- **K2, Y1 PASS, Y2 FAIL.** CohIQP beats MaxEnt(3) but not FlipIQP. Then more shots do not justify the coherent model,
  and the limit stands in practice.
- **K3, Y1 FAIL.** The limit stands even at 1e5 shots with a coherent-aware model.
- **Y3 FAIL** in any reading: CohIQP is not safe under Pauli noise. Any use of it must then be gated on a coherence
  diagnosis, and that gate is untested.

## 7. Budget, stop-loss, lever

- 20 workers. About 117 core-hours in total, so about 6–7 h of wall time.
- **Stop-loss: 11 h.** Running jobs are killed and count as failures.
- **Lever, if the projection after the first 20 finished jobs exceeds 11 h:** drop the `pf` coh jobs not yet started.
  Y3 then counts as FAIL ("not tested"). Never cut restarts or maxiter.

## 8. Verify (`--verify` exits 0 only if)

- every planned job has a metrics.json, or the stop-loss or the lever is recorded;
- `verdicts.json` is reproducible from the metrics;
- `tests/test_step31.py` passes. Its tests are written before the run, and they check that:
  - the model and data objects are steps 26, 29 and 30's, unchanged (the same constants and functions);
  - the seeds are fresh (≥ 1080);
  - the cf data at seed 1060 equal step 29's xf02 data;
  - the `me3` G at N = 1e5 for spent seed 1060 matches the pilot's to 1e-9.

## 9. Build order

Tests → commit code → launch → after 3 min check that `errors.log` is empty → `--report`, `--verify` → note and README
row on master.

## Working style

- Guesses are marked in comments.
- Commit with explicit paths. Never push.
- Do not edit this spec, the tests, or `--verify` after launch.
