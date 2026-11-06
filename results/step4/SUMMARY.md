# Step 4: does R_G < 1 survive misspecification and finite N? Summary

Step 4 was designed after step 3; R1 replicates data already seen; G is the generic IQP (no oracle); n = 12 proxies are not hardness evidence.

Spec: `specs/step4_misspec_finite_n.md` (hypotheses frozen at fe7d058), amended by
`specs/step4_amendment1.md` (mix calibration, reading rules for P1/F2), which was written after
the blind diagnostics D1/D2 (`diagnostics/step4_pre/SUMMARY.md`). Branch `step4-misspec`,
2026-11-06/07. 140/140 instances, n = 12. Produced by the grid run of `src/step4/run.py`
(80 min wall clock; projection 0.67 h) and `python -m src.step4.run --report`.
Per-instance data `results/step4/<target>/<sigma_σ|none>/N_<N>/seed_<s>/metrics.json`; flat
table `table.csv`; all statistics `verdicts.json`; figures `figures/step4/*.{png,pdf}`.

## Read first

- **G uses only 3 restarts** per instance (as in step 3, where it was budget cut 1; the spec
  keeps it and forbids fewer). Fewer restarts can only raise G's residual, and so R_G.
- R = G_iqp / G_maxent3 at G's lowest-training-residual restart, both against the exact target.
  Statistics: median and IQR (numpy linear percentiles) over 5 seeds; "R < 1" = IQR entirely
  below 1, "R ≥ 1" = entirely at or above 1, else "undecided".
- MaxEnt(3) keeps step 1's ridge (1e-8) at every N, untuned (spec).

## Hypotheses

| ID | Verdict | Numbers: median R [IQR] (G training residual, median) |
|---|---|---|
| K | K: PASS | `maxent_proj`, finite N, R never < 1 (all six cells "R ≥ 1"): σ = 0.1: N = 1e3 1.22 [1.02, 1.29], 1e4 1.73 [1.19, 2.33], 1e5 7.0 [3.9, 11.5]; σ = 0.2: 1e3 1.82 [1.56, 1.91], 1e4 5.46 [5.42, 9.98], 1e5 78 [59, 147]. Unlike N = ∞ (vacuous, step 3), this is an informative kill test: both models fit noisy moments. |
| R1 | R1: PASS (replication of step 3, data already seen) | `iqp`, N = ∞: σ = 0.1: 0.179 [0.064, 0.236] (res 1.8e-5); σ = 0.2: 0.176 [0.122, 0.215] (res 1.5e-4). Identical to step 3's R_G (same fits, same inits). |
| P1 | P1: PASS (prediction) | `iqp4`, N = ∞, σ = 0.2: **0.577 [0.450, 0.579]**, G training residual 2.1e-3 [1.5e-3, 2.4e-3] (see "iqp4" below: the residual is the family's floor). |
| P2 | P2: PASS (prediction: no IQP advantage on non-IQP data) | `mix`, N = ∞: **5.02 [4.59, 5.63]** (res 1.9e-2), R ≥ 1. **Room level: σ = 0.1, not σ = 0.2** (amendment 1): mix uses K = 48, δ = 0.99, median D3 = 0.0385 vs iqp σ = 0.1's 0.046; no product-Bernoulli mixture reached σ = 0.2's D3 ≈ 0.19. **Fairness limit:** a fitted latent-class mixture would be well specified on mix and should beat both models; that baseline is out of scope (stub `fit_mixture_moments`). P2 only says the IQP does not beat MaxEnt(3), which uses the same order-≤3 information. |
| F1 | F1: PASS (prediction) | `iqp`, σ = 0.2: N = 1e5 0.227 [0.088, 0.248] (R < 1); N = 1e3 1.05 [0.98, 1.17] (undecided, i.e. not < 1). Also N = 1e4: 0.425 [0.349, 0.427]. |
| F2 | F2: PASS (prediction) | `iqp4`, σ = 0.2, N = 1e5: **0.546 [0.471, 0.723]**, G residual 2.3e-3 (floor; see below). |

## iqp4: every R with G's training residual (amendment 1, section 2.2)

D1 (`diagnostics/step4_pre/SUMMARY.md`) showed that G's ~1e-3 order-≤3 residual on iqp4 at
σ = 0.2 is the **floor of the weight-≤3 family** (a warm start from the truth's weight-≤3 angles
ends at the same level as random restarts; 44/50 within 2×), not a training failure. MaxEnt(3)
matches those moments exactly. So G enters the completion with a known low-order disadvantage,
and **step 3's "misfit is conservative" argument does not apply**: the misfit is the price of the
family. P1 and F2 read: the weight-≤3 IQP completes orders 4–6 better than MaxEnt(3) *despite*
that misfit.

| σ | N | median R [IQR] | median G residual [IQR] | per seed: R (G residual) |
|---|---|---|---|---|
| 0.2 | 1e3 | 0.89 [0.84, 1.21] undecided | 2.7e-2 [2.4e-2, 2.8e-2] | 0.74 (3.7e-2), 0.89 (2.7e-2), 1.34 (2.4e-2), 1.21 (1.2e-2), 0.84 (2.8e-2) |
| 0.2 | 1e4 | 0.656 [0.446, 0.828] < 1 | 3.0e-3 [3.0e-3, 4.8e-3] | 0.45 (2.9e-3), 1.24 (3.0e-3), 0.83 (3.0e-3), 0.66 (4.8e-3), 0.43 (5.1e-3) |
| 0.2 | 1e5 | 0.546 [0.471, 0.723] < 1 | 2.3e-3 [2.0e-3, 2.7e-3] | 0.47 (2.3e-3), 0.84 (2.0e-3), 0.72 (1.4e-3), 0.55 (5.0e-3), 0.28 (2.7e-3) |
| 0.2 | ∞ | 0.577 [0.450, 0.579] < 1 | 2.1e-3 [1.5e-3, 2.4e-3] | 0.45 (2.1e-3), 0.80 (1.3e-3), 0.58 (1.5e-3), 0.58 (4.4e-3), 0.38 (2.4e-3) |
| 0.1 | 1e3 | 1.43 [1.35, 1.74] ≥ 1 | 1.7e-2 [1.3e-2, 2.7e-2] | 1.35 (1.3e-2), 2.02 (6.2e-2), 1.74 (9.3e-3), 1.43 (1.7e-2), 1.17 (2.7e-2) |
| 0.1 | 1e4 | 4.95 [3.13, 7.33] ≥ 1 | 9.0e-3 [9.0e-3, 1.1e-2] | 4.95 (1.1e-2), 12.5 (4.8e-2), 7.33 (9.0e-3), 2.81 (9.0e-3), 3.13 (7.5e-3) |
| 0.1 | 1e5 | 5.47 [4.32, 9.03] ≥ 1 | 7.9e-3 [7.5e-3, 9.2e-3] | 4.32 (9.2e-3), 14.1 (5.1e-2), 9.03 (6.1e-3), 4.21 (7.5e-3), 5.47 (7.9e-3) |
| 0.1 | ∞ | 7.93 [5.50, 8.92] ≥ 1 | 7.5e-3 [7.2e-3, 8.8e-3] | 4.49 (8.8e-3), 12.4 (4.9e-2), 8.92 (5.6e-3), 5.50 (7.2e-3), 7.93 (7.5e-3) |

Not a frozen hypothesis, reported because it bounds P1: **at σ = 0.1, iqp4 gives R ≥ 1 at every
N** (R = 7.9 at N = ∞), with a larger G residual (7.5e-3) than at σ = 0.2. So P1's IQP advantage
under misspecification holds at σ = 0.2 and reverses at σ = 0.1. The spec's P1 is stated at
σ = 0.2 only; it passes as stated, but it does not generalize across σ.

## Other cells (medians; full IQRs in verdicts.json)

| cell | N = 1e3 | 1e4 | 1e5 | ∞ |
|---|---|---|---|---|
| iqp σ = 0.1: R | 1.28 (≥1) | 1.13 (undecided) | 0.247 (<1) | 0.179 (<1) |
| iqp σ = 0.2: R | 1.05 (undecided) | 0.425 (<1) | 0.227 (<1) | 0.176 (<1) |
| mix: R (G residual) | 3.08 (8.9e-2) | 4.67 (2.8e-2) | 5.79 (2.4e-2) | 5.02 (1.9e-2) |
| maxent_proj σ = 0.1: R | 1.22 | 1.73 | 7.0 | 6.9e8 (vacuous) |
| maxent_proj σ = 0.2: R | 1.82 | 5.46 | 78 | 2.8e12 (vacuous) |

On `mix`, G's training residual is 1.9e-2 at N = ∞, i.e. 6.4e-5 per moment (the residual is a
sum over the 298 order-≤3 moments; the noise floor is a per-moment mean). Per moment it is above
the noise floor at N = 1e4 and 1e5 (9.3e-5 vs 1.0e-4 at 1e4 is about equal; 8.1e-5 vs 1.0e-5 at
1e5) and below it at N = 1e3: G is misspecified on mix, visibly once N ≥ 1e5.

## Noise floor (figure `noise_floor`)

- At N = 1e3, G_iqp and G_maxent3 are both close to the order-1..3 noise floor (e.g. iqp
  σ = 0.2: 1.3e-3, 1.2e-3 vs 9.0e-4): finite-N losses there are mostly sampling noise, and R ≈ 1.
- As N grows, G_maxent3 on `iqp` and `iqp4` (σ = 0.2) levels off at its model bias
  (~5.5e-4, ~7e-4), while G_iqp keeps falling on `iqp` (to 7.7e-5) and levels lower on `iqp4`
  (~4e-4). On `mix` and `iqp4` σ = 0.1 the order is reversed (G_iqp levels above G_maxent3).

## Failure modes seen

Scale note: training residuals are sums over the 298 order-≤3 moments; the noise floor is a
per-moment mean, so the expected sum of squared sampling errors is about 298 × noise floor.

- **FM-N1 (MaxEnt at small N): maxiter (20000) hit on 19/140 instances**, all at finite N:
  iqp σ = 0.1 N = 1e3 (5/5) and 1e4 (1/5), iqp σ = 0.2 N = 1e3 (1/5), iqp4 σ = 0.1 N = 1e3
  (5/5), maxent_proj σ = 0.1 N = 1e3 (4/5) and 1e4 (3/5). In all of them MaxEnt's training
  residual is ≤ 1.4e-8 (sum), far below 298 × noise floor (≥ 1e-2): the dual converges slowly
  but matches the noisy moments. The spec's other symptom (residual well above the noise floor)
  did not occur. Twelve further MaxEnt runs stopped with L-BFGS-B "ABNORMAL" (line search) at
  residuals ≤ 6.3e-13. The ridge was not changed.
- **FM-N2 (IQP fits the noise): observed at N = 1e3.** G's residuals there (3.5e-3 to 8.9e-2,
  medians by cell) are far below 298 × noise floor (0.13 to 0.30): G reproduces most of the
  sampling noise in its training moments, as expected (spec: "not a bug"). At N = 1e3, R
  therefore measures how that noise propagates to orders 4–6, and R ≈ 1 or above in every cell.
- **FM2 / misspecification floor:** on iqp4 (table above; D1) and mix, G's residual stays at
  ~1e-3 to ~2e-2 as N grows.

## Timing

Projection 0.67 h (each target's measured time × its count). Actual: 80 min wall clock (the
sum of instance times, 1.34 h, agrees). The machine was shared: other python processes ran
during the grid, and maxent_proj σ = 0.1 N = 1e4 seed 0 took 138 s in the grid vs 25 s when
timed alone, so timings here are not a clean speed measurement.
