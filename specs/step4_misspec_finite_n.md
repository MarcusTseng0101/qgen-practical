# Step 4: does R_G < 1 survive misspecification and finite N? (qgen-practical)

Status: **draft for user approval**, 2026-11-06. **Designed after** step 3
(`notes/2026-11-06_step3_findings.md`), whose R_G < 1 at σ = 0.1–0.2 was exploratory. Every
report must say so. The hypotheses in section 4 are frozen when this file is committed.

## Project

Fit the generic IQP (G) and MaxEnt(3) to order-≤3 parity moments: exact at N = ∞, empirical
at finite N. Compare how well each completes orders 4–6 (R = G_iqp / G_maxent3, both
measured against the exact target) on four targets:
- one well-specified target (the replication);
- two targets outside G's family;
- one paired control that is informative at finite N.

The deliverable is **one figure set, a table and a summary**. It is **not**:
- a hardness claim (the n = 12 proxies are reported, not interpreted);
- a method (no oracle layout; G is the generic 298-generator IQP);
- real data.

## Why each target (and what the unfair version would prove)

| Target | Definition | Why |
|---|---|---|
| `iqp(σ, s)` | The step-2/3 construction. Import it from `src/step2/sweep.py`. | Replication of step 3. Well-specified for G, so a win here says little alone. |
| `iqp4(σ, s)` | `iqp(σ, s)` plus 6 weight-4 generators. The weight-4 supports are drawn from `default_rng(4000 + s)`, the angles are σ·z' with z' ~ N(0, 1), and z' is reused across σ. | IQP-like, but **outside** G's weight-≤3 family. This tests the inductive bias, not well-specification. |
| `mix(s)` | A classical latent-class mixture: K = 3 product-Bernoulli components, weights Dirichlet(1,1,1), bit probabilities 0.5 + δ·u with u ~ U(−0.5, 0.5). Drawn from `default_rng(5000 + s)`. | Non-IQP "classical" structure. If R_G < 1 here, it is the most interesting outcome. If it is ≥ 1, IQP completion is specific to IQP-made data. |
| `maxent_proj(σ, s)` | MaxEnt3 of `iqp(σ, s)`, as in step 3 | At N = ∞ it is vacuous (step 3, K1/K2). At **finite N** both models fit noisy moments, and MaxEnt(3) must still win on its own truth. This is now a real kill test. |

- **Calibrating δ (before any fit):** pick δ from {0.2, 0.4, 0.6, 0.8} so that the median D3
  of `mix` over seeds 0–4 is closest to that of `iqp` at σ = 0.2 (D3 ≈ 0.19). Record the D3
  of every candidate in `results/step4/calibration.json`. No R is computed during
  calibration.
- **Fairness caveat, stated in advance:** on `mix`, a fitted latent-class mixture would be
  well-specified and should beat both models. That baseline is out of scope (stub
  `fit_mixture_moments`, not implemented). MaxEnt(3) is the opponent because it uses exactly
  the same information (order-≤3 moments) with the least extra structure.

## Design

- **Grid:**
  - σ ∈ {0.1, 0.2} for `iqp`, `iqp4` and `maxent_proj`; `mix` has no σ and runs once per
    seed.
  - N ∈ {1e3, 1e4, 1e5, ∞}; seeds 0–4.
  - Instances: (3 targets × 2 σ + 1) × 4 N × 5 seeds = **140**.
- **Finite N:** the samples come from `src/step1/targets.sample_indices(p, N, seed)`. The
  empirical order-≤3 moments are computed from those samples. Both models see the same vector.
- **Fits:**
  - G: the generic 298-generator IQP, 3 restarts (as in step 3), init N(0, 0.05²), step-1
    L-BFGS-B settings.
  - MaxEnt(3): ridge 1e-8, as in step 1. Do **not** tune the ridge per N. Tuning it only for
    the baseline, or only for the IQP, makes the comparison unfair.
  - R is taken at G's lowest-training-residual restart.
- **Record** per instance in `results/step4/<target>/<σ or none>/N_<N>/seed_<s>/metrics.json`:
  - G_iqp, G_maxent, G_uniform, R;
  - G's training residual and all of its restart residuals and G values;
  - MaxEnt's training residual;
  - D3 of the target; the sampling noise floor = mean over orders 1–3 of (1 − f_a²)/N;
  - hi_order_frac, collision ratio;
  - `versions`, `total_seconds`.
- **Code:** `src/step4/run.py` only, importing `src/step1`, `src/step2` and `src/step3`.
  Never edit those three; they are closed records.

## Statistics

The same rules as step 3: median and IQR over 5 seeds.
- "R < 1" means the IQR lies entirely below 1.
- "R ≥ 1" means the IQR lies entirely at or above 1.
- Otherwise the result is "undecided" and is reported as such.

## 4. Hypotheses (frozen at commit)

| ID | Statement | Type |
|---|---|---|
| K | `maxent_proj`, every finite N, both σ: R is **not** < 1 (IQR not entirely below 1) | **Kill.** If it fails, finite-sample fitting favors the IQP on data it did not make. Stop; nothing else is interpretable. |
| R1 | `iqp`, N = ∞, σ = 0.1 and 0.2: R < 1 | Replication of step 3 (data already seen) |
| P1 | `iqp4`, N = ∞, σ = 0.2: R < 1 | **Prediction** (main): the weight-≤3 IQP still completes better than MaxEnt(3) when the truth has 4-body terms. |
| P2 | `mix`, N = ∞: R is **not** < 1 | **Prediction:** no IQP advantage on non-IQP data. If R < 1, report it as the headline, with the caveat above. |
| F1 | `iqp`, σ = 0.2: R < 1 at N = 1e5 and not < 1 at N = 1e3 | Prediction: the advantage needs many samples |
| F2 | `iqp4`, σ = 0.2: R < 1 at N = 1e5 | Prediction: P1 survives realistic N |

These predictions are guesses written before any step-4 run. They are not tuned; the
summary must report each one as PASS or FAIL with its numbers, whatever happens.

## Artifacts

All as PNG (150 dpi) and PDF, readable without color.
1. `figures/step4/ratio_vs_N`: median R with an IQR band against N (log x axis, with N = ∞
   drawn at the right edge). One panel per σ; lines for `iqp`, `iqp4`, `mix` and
   `maxent_proj`; a reference line at R = 1. This is the evidence for K, F1 and F2.
2. `figures/step4/ratio_at_inf`: a strip plot of R per seed at N = ∞ for every target.
   This is the evidence for R1, P1 and P2.
3. `figures/step4/noise_floor`: G_iqp and G_maxent against N, next to the noise floor. It
   shows whether finite-N losses are sampling noise or model bias.
4. `results/step4/table.csv` and `results/step4/SUMMARY.md`. The summary marks K, R1, P1, P2,
   F1 and F2 as PASS or FAIL with the numbers, and contains verbatim:
   "Step 4 was designed after step 3; R1 replicates data already seen; G is the generic IQP
   (no oracle); n = 12 proxies are not hardness evidence."

## Budget

- Time one `iqp4` instance (σ = 0.2, N = 1e4, seed 0) and one `mix` instance (N = 1e4,
  seed 0).
- Write `results/step4/PROJECTION.json` as `{"projected_hours": h, "instances": 140}`, using
  the **slower** of the two per-instance times. Step 3 underestimated by 1.4×; say so in the
  file.
- The grid flag refuses to start without the budget-approval file (as in step 3).
- If the projection is over 3 h, cut in this order: (1) drop N = 1e3, then (2) σ = 0.1.
- Never cut `maxent_proj` at finite N (it is K), never cut `iqp4` at σ = 0.2 (P1, F2), and
  never cut seeds below 5.
- **Do not** cut G's restarts below 3. Fewer restarts raises R_G, and the residual–G link
  already breaks at large σ (step 3).

## Build order

1. Branch `step4-misspec` from `step3-ratio` (after the user merges or approves).
2. Targets and calibration:
   - `iqp4` and `mix` in `src/step4/targets.py`;
   - `tests/test_step4.py`:
     - `iqp4` has nonzero weight-4 content that is not reproducible in the weight-≤3 family
       (G's best residual on its exact moments is > 1e-8 at σ = 0.2, seed 0);
     - `mix` sums to 1;
     - the finite-N moments match `sample_indices` exactly.
   - Run the δ calibration (D3 only) → `calibration.json`. Checkpoint: `check.sh --stage 10`.
3. The two timed instances → PROJECTION.json → **wait for the budget-approval file**.
   Checkpoint: `--stage 11`.
4. The full grid, figures, table and summary. Checkpoint: `--stage 12`.

## Failure modes to expect

1. **FM-N1: MaxEnt(3) at small N.** Empirical moments may be infeasible or near the boundary,
   so the dual diverges and λ blows up.
   - Symptom: a MaxEnt training residual well above the noise floor, or a hit on the maxiter
     limit.
   - Report it; do not raise the ridge. The ridge is frozen, and changing it only for the
     baseline is an unfair comparison.
2. **FM-N2: the IQP overfits the noise.** At N = 1e3 the G fit may hit residual ~0 on noisy
   moments.
   - Expected, not a bug. R then measures how noise propagates to orders 4–6.
3. **FM2 (step 1): spurious minima.** At σ = 0.2 the step-3 G residual was 1.5e-4.
   - If `iqp4` G residuals are ~1e-3 (like σ ≥ 0.3 in step 3), say so prominently. P1 then
     tests training failure, not completion.

## Working style

The same as steps 1–3:
- ask before installing;
- commit at checkpoints and never push;
- mark guesses as guesses;
- show diagnostics before changing anything, and change one thing at a time;
- "done" means `check.sh --stage <STAGE>` exits 0;
- never edit the harness, `prereg/`, `specs/` or the budget-approval file;
- report blocks instead of rephrasing around them;
- keep `PROGRESS.md` current.
