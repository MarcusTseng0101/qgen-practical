# Step 4 pre-amendment diagnostics D1, D2 (blind)

Date 2026-11-06. User chose A: two diagnostics before step 4 amendment 1. **Blind:** no
G_iqp, G_maxent, R or any order-4..6 error was computed or printed; only training residuals,
Jacobian singular values and D3. Standalone scripts here; `src/step4`, the spec,
`results/step4/calibration.json` and the harness are unchanged.

## D1: iqp4, σ = 0.2, seeds 0–4 (`d1_iqp4_warmstart.py`, `.json`, `.log`)

Generic 298-generator G, exact order-≤3 moments of iqp4. (a) the truth's weight-≤3 angles
(38 generators, zeros elsewhere) plugged in, no optimization; (b) one L-BFGS-B run from (a);
(c) 10 restarts from N(0, 0.05²) (fit_moments' own draws). All runs use the production
`fit_moments` with step-1 settings. All 55 runs stopped with "RELATIVE REDUCTION OF F <=
FACTR*EPSMCH" (nit 968–2838), none at maxiter.

| seed | (a) truth w≤3, no opt | (b) warm-start residual | (c) best of 10 random | (b)/(c) | restarts within 2× of (b) | σ_min(J) at (b) | σ_min(J) over the 10 restarts |
|---|---|---|---|---|---|---|---|
| 0 | 0.689 | 2.49e-3 | 1.98e-3 | 1.26 | 10/10 | 6.4e-9 | 6.5e-10 – 2.3e-8 |
| 1 | 3.13 | 1.44e-3 | 8.58e-4 | 1.68 | 8/10 | 1.8e-8 | 2.5e-9 – 3.6e-8 |
| 2 | 0.641 | 1.62e-3 | 1.25e-3 | 1.30 | 7/10 | 1.2e-9 | 3.7e-10 – 4.0e-8 |
| 3 | 1.26 | 4.96e-3 | 4.03e-3 | 1.23 | 10/10 | 9.6e-9 | 1.2e-9 – 2.4e-8 |
| 4 | 0.798 | 2.08e-3 | 2.12e-3 | 0.98 | 9/10 | 3.0e-9 | 3.3e-10 – 1.7e-8 |

Observations (no completion quantities):
- Dropping the 6 weight-4 generators from the truth gives a residual of 0.6–3.1: at σ = 0.2
  the weight-4 terms move the order-≤3 moments a lot.
- Starting from those truth angles, L-BFGS-B ends at 1.4e-3 – 5.0e-3, the same level as
  random restarts (ratio 0.98–1.68; 44/50 restarts within 2× of the warm-start residual).
  Random restarts are not worse than the informed start; on 4/5 seeds they are slightly better.
- Every solution (warm and random) has σ_min(J) between 3e-10 and 4e-8: a near-singular
  298 × 298 moment Jacobian, as in step 1's FM2.
- So the ~1e-3 residual looks like a floor that every start reaches, not a bad-init effect.
  Whether that floor is the best weight-≤3 approximation (misspecification) or a family of
  spurious stationary points (FM2) is not separable from these numbers; both fit.

## D2: mix, δ extended (`d2_mix_delta.py`, `.json`, `.log`)

Same Dirichlet weights and u (default_rng(5000 + s)); D3 = KL(p ‖ MaxEnt3(p)) via
`src/step2/sweep.d3`, as in calibration.json. Rows 0.2–0.8 are read from calibration.json.

| δ | median D3 | per seed 0–4 | source |
|---|---|---|---|
| 0.2 | 1.15e-7 | 1.08e-8, 4.93e-8, 3.46e-7, 1.15e-7, 2.17e-6 | calibration.json |
| 0.4 | 2.35e-5 | 6.20e-6, 1.10e-5, 8.15e-5, 2.35e-5, 3.06e-4 | calibration.json |
| 0.6 | 4.35e-4 | 1.96e-4, 1.67e-4, 1.45e-3, 4.35e-4, 3.57e-3 | calibration.json |
| 0.8 | 2.92e-3 | 1.64e-3, 6.84e-4, 8.18e-3, 2.92e-3, 1.45e-2 | calibration.json |
| 0.9 | 6.04e-3 | 3.47e-3, 1.48e-3, 1.46e-2, 6.04e-3, 2.22e-2 | new |
| 0.95 | 8.35e-3 | 4.73e-3, 2.35e-3, 1.82e-2, 8.35e-3, 2.54e-2 | new |
| 0.99 | 1.07e-2 | 5.88e-3, 3.42e-3, 2.09e-2, 1.07e-2, 2.68e-2 | new |

Reference: iqp at σ = 0.2, median D3 = 0.187. Even δ = 0.99 (bit probabilities up to
0.005 / 0.995) reaches only 1.07e-2, about 17× below it; the largest single seed is 2.7e-2.
The growth slows as δ → 1 (×2.1, ×1.4, ×1.3 over the last three steps); δ < 1 is required
for bit probabilities in (0, 1). Extrapolation, not measured: no δ in this family with K = 3
and these (w, u) is likely to reach the iqp reference.
