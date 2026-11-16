# Step 33 spec: does the moment advantage carry over to sampling quality? (pre-registered, N = 1e4)

Status: **frozen** once committed. Written 2026-11-17 after the step 32 exploration (master note
`notes/2026-11-16_step32_sampling_quality.md`, worktree commit a73c98c). The user chose this step ("A").
The hypotheses and thresholds below come from that exploration, which used spent seeds 920–933, 1000–1013 and
1060–1073. Every number in §5 is fixed before any model is fitted on the test seeds 1120–1133.

**Deliverable.** A pre-registered test of whether the paper's fitted IQP models are closer to the target than MaxEnt(3)
as whole distributions, so that paper §VI can drop the word "exploratory".
- It is **not** a new model or a new recipe: every arm is fitted exactly as in steps 23, 26, 27 and 29.
- It is **not** a metric search: the primary metric is TVD, fixed here.

**Acceptance:** `python -m src.step33.run --verify` exits 0. A FAIL is a result, not a reason to edit the check, the
tests or this spec.

## 1. Evidence so far (exploration, spent seeds, N = 1e4; wins of the IQP model over MaxEnt(3) out of 14)

| Metric | ideal | 1% gate, FlipIQP | coherent ε 0.2, recipe |
|---|---|---|---|
| G | 14 | 13 | 10 |
| TVD | 14 | 13 | 12 |
| KL | 13 | 13 | 13 |
| E_1 (single-bit) | 5 | 2 | 1 |
| MMD, s = 2 | 9 | 7 | 1 |

The wrong-graph setting (step 27 `mg01`) was never scored for sampling. It is added here as a fresh condition.

## 2. Data and models (load-bearing)

All conditions use N = 1e4, `training_moments(p, 10_000, seed, 16)` and 20-restart fits as in their source step.

| Cond | Target p | IQP arm | Source |
|---|---|---|---|
| `id` | `Gd.grid_iqp(seed)` | `IQPModel(16, gens=LOCAL_GENS)`, 20 restarts, init_std 0.3 | step 23 |
| `g01` | `noisy_grid_iqp(seed, 0.01, 0.02)` (step 26) | `FlipIQP(16, LOCAL_GENS)` | step 26 |
| `mg01` | `noisy_grid_iqp(seed, 0.01, 0.02)` (step 26) | recipe on the `miss` graph `C24.model_masks("miss", seed)` | step 27 |
| `xf02` | `coherent_grid_iqp(seed, 0.2, 0.02)` (step 29) | recipe on the correct graph | step 29 |

- **Recipe.** Fit FlipIQP on the given graph. If resid / F > 0.75, with F = Σ(1 − f̂²)/N, refit FlipIQP on `ENLARGED`
  (103 candidates) and use that fit. `flow_choice` and `raw_floor` are imported from step 27, unchanged.
- **Classical arms.** `me3 = MaxEntModel(16, 3)` and `me_graph = MaxEntOn(16, masks)`, where the masks are those of the
  given graph (the `miss` graph in `mg01`).
- **Metrics** of each q against the exact p, all exact at n = 16:
  - TVD = ½ Σ|p − q|;
  - KL(p‖q) = Σ p log(p/q), with q clipped at 1e-300;
  - fidelity (Σ √(pq))²;
  - E_k for k = 1..16 (Walsh–Hadamard transform);
  - G = mean(E_4, E_5, E_6), which must equal `M1.completion_gap` to 1e-10;
  - MMD² at s = 0.5, 1, 2 by Σ_k C(n,k) a^(n−k) b^k E_k, with c = exp(−1/2s²), a = (1+c)/2, b = (1−c)/2.

## 3. Failure modes

1. **Wrong arm settings.** A refit that differs from the source step makes the test about a different model. The
   tests check that each condition calls the source step's functions with the source parameters.
2. **Metric bugs.** The tests check the Walsh transform against brute force, and the MMD identity against a direct
   kernel sum on n = 6.
3. **Slow fits.** Exploration jobs took 35–115 min each with 6 workers. Keep the stop-loss.
4. **Shared CPU.** Another session's step 32 may still run. Do not touch its processes.

## 4. Instances

| Condition | Seeds | Role |
|---|---|---|
| `id`, `g01`, `mg01`, `xf02` | 1120–1133 | test |

- Seeds up to 1113 are spent, and 1114–1119 are skipped.
- That makes 56 jobs, launched in the order `xf02`, `mg01`, `g01`, `id` (slowest first).

## 5. Hypotheses (fixed now)

A win is a strictly better value for the IQP arm than for MaxEnt(3) on a seed. Missing seeds count as failures.

| ID | Statement | PASS if |
|---|---|---|
| S1 (primary) | lower TVD than MaxEnt(3), ideal | wins ≥ 11/14 (`id`) |
| S2 (primary) | lower TVD, 1% gate noise | wins ≥ 11/14 (`g01`) |
| S3 (primary) | lower TVD, wrong graph + 1% gate noise | wins ≥ 11/14 (`mg01`) |
| S4 (primary) | lower TVD, coherent ε 0.2 | wins ≥ 11/14 (`xf02`) |
| S5–S8 | lower KL(p‖q), same four conditions | wins ≥ 11/14 each |
| W1 | the weak spot: **higher** E_1 than MaxEnt(3), coherent | model E_1 > me3 E_1 on ≥ 11/14 (`xf02`) |
| W2 | wide-kernel MMD (s = 2) is **lost**, coherent | model MMD_2 > me3 MMD_2 on ≥ 11/14 (`xf02`) |

- 11/14 is a one-sided sign test at p = 0.029, as in every earlier step. No multiplicity correction is applied; the
  four primary hypotheses are reported separately, not as one family claim.
- W1 and W2 predict a loss. A PASS confirms the weakness the paper states.

Reported, with no verdict:
- wins and median ratio model/me3 and model/me_graph for G, mean E_7..E_16, fidelity, MMD at s = 0.5, 1, 2;
- per-order wins over me3 for k = 1..16;
- median TVD of the three models;
- the Bhattacharyya sample bound m = 2 ln 10 / (−ln F) for the model and me3;
- in `mg01` and `xf02`, how often the alarm fired.

## 6. Readings

- **L1, S1–S4 all PASS.** The paper states as a tested result that the fitted IQP samples closer to the target than
  MaxEnt(3) in total variation, in all four settings.
- **L2, some of S1–S4 FAIL.** The paper states the sampling advantage only for the passing settings and reports the
  failures in Table III.
- **W1, W2.** If they PASS, §VI keeps its single-bit weak-spot paragraph as a tested statement; if they FAIL, it is
  removed or rewritten as not reproduced.

## 7. Budget, stop-loss, lever

- 14 workers, OMP threads 1.
- **Stop-loss: 16 h** from launch (about 40 other Python processes were running on the 32 cores at freeze time). Running jobs are killed and count as failures.
- **Lever:** none that keeps all hypotheses testable. Missing jobs count as failures, and that is reported.

## 8. Verify (`--verify` exits 0 only if)

- every planned job has a metrics.json, or the stop-loss is recorded;
- `verdicts.json` is reproducible from the metrics;
- `tests/test_step33.py` passes. Its tests are written before the run, and they check:
  - seeds are 1120–1133 and do not overlap any earlier test range;
  - the conditions call the source steps' functions with the source parameters;
  - the Walsh transform and the MMD identity on small n;
  - G from the per-order errors equals `completion_gap`;
  - the win counting on synthetic records (strict inequality, missing seeds fail, W1/W2 count losses).

## 9. Build order

Tests → commit code → launch → after 3 min check that `errors.log` is empty → `--report`, `--verify` → note,
README row and paper §VI update on master.

## Working style

- Guesses are marked in comments.
- Commit with explicit paths. Never push.
- Do not edit this spec, the tests or `--verify` after launch.
