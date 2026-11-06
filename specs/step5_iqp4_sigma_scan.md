# Step 5 spec: where does the iqp4 advantage reverse, and why? (qgen-practical)

Status: **frozen** (user approved 2026-11-07, decision A; harness v6 installed). Written **after step 4**
(`notes/2026-11-07_step4_findings.md`). The values at σ = 0.1 and σ = 0.2 below are data
already seen. Once this file is committed, the hypotheses in section 3 are frozen; any change
needs a numbered amendment written before the grid runs.

## 1. Question and the guess under test

Step 4 found that on `iqp4` (the step-3 IQP target plus 6 weight-4 generators, outside the
weight-≤3 family) at N = ∞:
- at σ = 0.2: R = 0.577 [0.450, 0.579];
- at σ = 0.1: R = 7.93 [5.50, 8.92].

Here R = G_iqp / G_maxent3 at orders 4–6. Median G values over the 5 seeds:

| σ | G_iqp | G_maxent3 | G training residual | D3 |
|---|---|---|---|---|
| 0.1 | 2.6e-4 | 3.3e-5 | 7.5e-3 | 0.068 |
| 0.2 | 4.1e-4 | 7.3e-4 | 2.1e-3 | 0.25 |

**Room-versus-floor guess.**
- **Floor:** G_iqp is set by the weight-≤3 family's misspecification floor, which depends
  weakly on σ (×1.6 from 0.1 to 0.2).
- **Room:** G_maxent3, the completion room, grows steeply with σ (×22 from 0.1 to 0.2).
- **Prediction:** so R ∝ σ^(−k) with k ≈ log(13.7)/log(2) ≈ 3.8. The crossing R = 1 is then
  near σ* ≈ 0.1 · 7.93^(1/3.8) ≈ 0.17.

The alternative is that the floor itself changes with σ in a way that drives R. To separate the
two explanations, step 5 adds a target whose weight-4 part does **not** scale with σ.

## 2. Design

**Targets**, seeds s = 0–4, n = 12:
- `iqp4(σ, s)`: unchanged from step 4 (`src/step4/targets.iqp4_target`).
- `iqp4f(σ, s)`: the same generators and z's. The weight-≤3 angles are σ·z, as in iqp4, but the
  6 weight-4 angles are fixed at **τ = 0.2**·z′, independent of σ.
  - Its floor source is therefore held at the σ = 0.2 level while the room varies.
  - **Identity check:** `iqp4f(0.2, s)` must equal `iqp4(0.2, s)` bit for bit (a test, not a
    hypothesis).

**Grid:**
- σ ∈ {0.1, 0.125, 0.15, 0.175, 0.2, 0.25};
- N ∈ {∞, 1e4};
- both targets, 5 seeds.

That is 2 × 6 × 2 × 5 = **120 instances**. At σ = 0.1 and 0.2, `iqp4` reruns step-4 cells; it
must reproduce step 4's numbers (same fits, same initial points).

**Fits** (unchanged from step 4):
- G: the generic 298-generator weight-≤3 IQP, 3 restarts, never fewer.
- MaxEnt(3): ridge 1e-8.
- R is taken at G's lowest-residual restart. Finite-N moments come from
  `training_moments(p, N, seed)` as in step 4.

**Statistics:**
- Median and IQR over 5 seeds.
- "R < 1" means the IQR lies entirely below 1; "R ≥ 1" means it lies entirely at or above 1;
  otherwise the cell is undecided.

**Crossing σ\*(target, N):**
1. Scan the grid σ upward.
2. Take the first adjacent pair with median R ≥ 1 at σ_i and median R < 1 at σ_{i+1}.
3. Interpolate log R linearly in log σ.

σ\* is undefined if no such pair exists. Also report the number of sign changes of
(median R − 1) across the grid.

## 3. Frozen hypotheses (all at N = ∞ unless stated)

| ID | Statement | Kind |
|---|---|---|
| Q0 | `iqp4`: R ≥ 1 at σ = 0.1 and R < 1 at σ = 0.2 | replication (data seen) |
| Q1 | `iqp4`: σ\* is defined, there is exactly one sign change over the grid, and σ\* ∈ [0.15, 0.20) | prediction (from the power law above) |
| Q2 | `iqp4`, floor versus room: max/min of median G_iqp over the 6 σ values ≤ 3, **and** median G_maxent3 at σ = 0.25 / at σ = 0.1 ≥ 10 | prediction (the 0.1 and 0.2 points were seen) |
| Q3 | `iqp4`: R < 1 at σ = 0.25 | prediction. Risk: in step 3, G failed to train on `iqp` at σ ≥ 0.3. |
| Q4 | `iqp4f`: at each σ ∈ {0.1, 0.125, 0.15, 0.175}, median R(iqp4f) ≥ median R(iqp4) | prediction, **low confidence**. A larger fixed floor at the same room should hurt, but the τ = 0.2 weight-4 part also adds room. |
| Q5 | σ\*(iqp4, N = 1e4) ≥ σ\*(iqp4, N = ∞). If σ\*(1e4) is undefined because R ≥ 1 everywhere, Q5 passes; if it is undefined because R < 1 everywhere, Q5 fails. | prediction (finite N mostly inflates both errors) |

No hypothesis is added after the grid. Anything else is labelled exploratory.

## 4. Failure modes to recognize

- **FM2 (spurious minima) at σ = 0.25.**
  - Symptom: G's training residual ≫ 1e-2, or a wide spread across restarts.
  - Report it next to Q3. Do **not** add restarts or change the optimizer: Q3 tests the
    method as specified.
- **Wiring error in iqp4f.**
  - Symptom: iqp4f(0.2) ≠ iqp4(0.2).
  - The pytest identity test catches it. Do not run the grid until it passes.
- **Reproduction drift.**
  - Symptom: `iqp4` at σ = 0.1 or 0.2, N = ∞, differs from step 4's `metrics.json`
    (R relative difference > 1e-6).
  - Stop and report. Something in the shared code path changed.
- **MaxEnt maxiter at N = 1e4** (step 4, FM-N1).
  - Report the count with the residuals. Do not change the ridge.

## 5. Artifacts

- `results/step5/<iqp4|iqp4f>/sigma_<σ>/N_<inf|10000>/seed_<s>/metrics.json`, with the step-4
  key set plus `tau` (iqp4f only) and `target`.
- `results/step5/table.csv` and `verdicts.json`, which include σ\* for each (target, N) and the
  sign-change counts.
- Figures in `figures/step5/` (png + pdf):
  - **`R_vs_sigma`:** median R and IQR against σ (log-log), both targets, N = ∞ solid and
    N = 1e4 dashed. Show a line at R = 1, a shaded band [0.15, 0.20) for Q1's prediction, and the
    k = 3.8 power law through σ = 0.1 as a reference. This figure is the direct test of Q1.
  - **`G_vs_sigma`:** median G_iqp, G_maxent3 and G's training residual against σ (log-y), for
    iqp4 and iqp4f at N = ∞. Q2 predicts a flat G_iqp and a steep G_maxent3.
- `results/step5/SUMMARY.md`:
  - It must open with this exact sentence: "Step 5 was designed after step 4; Q0 replicates data
    already seen; G is the generic IQP (no oracle); n = 12 proxies are not hardness evidence."
  - It must mark Q0–Q5 each PASS or FAIL with numbers, and show G's training residual next to
    every R.

## 6. Budget and stop gate

- **Timing step:** one instance each of `iqp4` and `iqp4f` at σ = 0.25, N = 1e4, seed 0.
  - Projection = per-target time × 60. Write `results/step5/PROJECTION.json`, then stop. Only the
    user creates `BUDGET_OK`.
  - Expected: ~7 s per instance, so ~15 min, ~30 min on a shared machine.
- **Budget:** 1 h.
- **If the projection exceeds the budget, cut in this order:**
  1. drop N = 1e4 for `iqp4f`;
  2. then drop N = 1e4 for `iqp4` (Q5 becomes untestable and must be reported as FAIL-untested).

  Never cut seeds, restarts, σ values or N = ∞ cells.

## 7. Build order

1. `src/step5/run.py` and `src/step5/targets.py` import from steps 1–4 and **do not modify
   them**; steps 1–4 are closed records. `tests/test_step5.py` must cover:
   - the iqp4f(0.2) = iqp4(0.2) identity;
   - iqp4f's weight-4 angles equal 0.2·z′ for every σ;
   - the σ\* interpolation on a synthetic series;
   - the Q5 undefined-σ\* rule.
2. Reproduction check: `iqp4` at σ = 0.2, N = ∞, seed 0 matches step 4. Then the timing step and
   PROJECTION.json, then stop.
3. After `BUDGET_OK`: the grid, the report, the figures and the SUMMARY. `check.sh --stage 15`
   must exit 0. Commit and update PROGRESS.md.
