# FM2 diagnostics: why the IQP cannot fit `biased` (n = 12, N = inf, seed 0)

Diagnostics only (2026-11-06). Not part of the pipeline; nothing here was written to
`results/`, and `src/step1/` was not changed. The script is `diag.py`, which imports the
production code; the raw outputs are `near.json`, `lbfgs.json` and `lsq.json` (+ `.log`).

Setup: the target's 38 true angles θ* are embedded in the 298-dim generic parameter vector
(other entries 0). At θ* the residual is 1.1e-31, the moment Jacobian has full rank 298,
sv_min 1.39e-5. So an exact solution exists inside the model and is non-degenerate.
Residual = Σ_{1≤|A|≤3} (f_A(model) − f_A(target))²; the gate is 1e-10.

## Comparison

| Diagnostic | Optimizer | Starts | Reached ≤ 1e-10 | Final residual (min / median / max) | Jacobian sv_min at end | Rank at end | Iterations |
|---|---|---|---|---|---|---|---|
| (1) θ* + N(0, 0.01²) | L-BFGS-B (production options) | 5 | **5/5** | 7.2e-13 / 1.7e-12 / 2.9e-12 | 4.6e-6 … 3.7e-5 | 298 | 4523–10423 |
| (1) θ* + N(0, 0.1²) | L-BFGS-B | 5 | 0/5 | 1.3e-4 / 5.1e-4 / 2.0e-3 | 5.4e-9 … 4.1e-8 | 297–298 | 626–1365 |
| (1) θ* + N(0, 0.3²) | L-BFGS-B | 5 | 0/5 | 3.5e-2 / 6.3e-2 / 1.0e-1 | 9.0e-10 … 4.1e-9 | 297 | 263–370 |
| (2) N(0, 0.05²) small-angle init | L-BFGS-B | 50 | 0/50 | 5.7e-3 / 9.5e-3 / 2.1e-2 | 3.4e-11 … 7.6e-9 (median 1.9e-9) | 297 (all 50) | 293–828 |
| (3) first 3 inits of (2) | least_squares trf, analytic Jacobian, x/f/gtol 1e-15 | **3 (truncated, see below)** | 0/3 | 7.3e-3 / 8.4e-3 / 1.1e-2 | 5.9e-10 … 1.7e-9 | — | 786–953 Jacobian evals (477–590 s each) |

(2) restarts 0–9 reproduce the production run's 10 restarts exactly (best 5.720e-3).

(2) sorted residuals (50): 5.720e-3 5.984e-3 6.456e-3 7.213e-3 7.256e-3 7.439e-3 7.455e-3
7.570e-3 7.869e-3 7.880e-3 8.035e-3 8.254e-3 8.454e-3 8.530e-3 8.616e-3 8.636e-3 8.735e-3
8.753e-3 9.006e-3 9.161e-3 9.192e-3 9.206e-3 9.231e-3 9.290e-3 9.428e-3 9.549e-3 9.659e-3
9.786e-3 1.011e-2 1.030e-2 1.045e-2 1.059e-2 1.075e-2 1.087e-2 1.097e-2 1.111e-2 1.130e-2
1.150e-2 1.151e-2 1.181e-2 1.221e-2 1.289e-2 1.365e-2 1.381e-2 1.411e-2 1.442e-2 1.481e-2
1.482e-2 1.848e-2 2.051e-2. Median 9.49e-3, min 5.72e-3. No tail toward 1e-10.

(3), same inits, side by side:

| init | L-BFGS-B residual (nit) | trf residual (Jacobian evals) |
|---|---|---|
| 0 | 1.097e-2 (338) | 7.281e-3 (786) |
| 1 | 9.231e-3 (492) | 1.112e-2 (953) |
| 2 | 1.442e-2 (300) | 8.386e-3 (937) |

**(3) has only 3 samples. The user chose to stop after 3 of the planned 10 restarts,
because each takes about 8–10 minutes.** `lsq.json` was rebuilt from `lsq.log`, because
the script writes its JSON only after all 10.

## Reading: initialization, optimizer, or landscape?

**Mainly the landscape. The optimizer is not the cause, and the initialization matters
only because a start has to be very close to θ* to work.**

- **Not the optimizer.** A second-order trust-region method with the exact Jacobian (trf)
  stops at the same kind of point as L-BFGS-B: residual ~1e-2, sv_min ~1e-9, an ftol stop.
  On 2 of 3 inits it ends a bit lower, on 1 higher. Neither gets within 3 orders of
  magnitude of the gate. Both optimizers also stop at real stationary points, not at an
  iteration limit.
- **Landscape: a narrow basin and many spurious stationary points.** The exact solution
  exists and is non-degenerate, but its basin is narrow. Noise of 0.01 per angle
  (|δ| ≈ 0.17) converges 5/5. Noise of 0.1 (|δ| ≈ 1.7) fails 5/5 and ends 1.4–2.0 away
  from θ*, i.e. it does not come back. Every failed run, from any start, ends at a point
  where the moment Jacobian loses one direction (rank 297, sv_min 1e-9 to 1e-11): a
  family of rank-deficient stationary points with residual 1e-4 to 1e-1. Because θ* has
  rank 298, this is not a global gauge symmetry of the parameterization.
- **Initialization, in the narrow sense.** N(0, 0.05²) starts farther out than any of the
  near-truth starts: initial residual ≈ 1.6, against 0.67–0.73 at σ = 0.3, 0.47–0.63 at
  σ = 0.1, and 0.009–0.014 at σ = 0.01. Note that the σ = 0.01 starts already sit at
  ~1e-2, the residual level of the spurious stationary points. A low residual does not mean
  "in the basin"; being close to θ* does. Only a start within ~0.01–0.1 per angle of the
  truth works, and no data-free init can know where that is. More restarts of the same init
  will not help: 0/50, with no tail.
- **Ill-conditioning even at the solution.** At θ*, sv_min = 1.4e-5 (condition number
  ~1e5), and L-BFGS-B needs 4.5k–10k iterations from 0.01 away. Convergence is slow even
  inside the basin.

## Caveats

- One target (`biased`, seed 0). The n = 6 xfail test shows the same signature, which
  suggests this is generic, but no other seed has been checked at n = 12.
- (3) has 3 samples (the user's truncation).
- The (1) noise draws use default_rng(10000 + 100·round(100σ) + rep). This is a diagnostic
  choice and is not used anywhere in the pipeline.
