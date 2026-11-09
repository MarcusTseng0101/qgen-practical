# Progress: qgen-practical

## Done (checkpoint, commit)
- Scoping README, the recsys note, and the iqp-from-limits note.
- Step 1 spec, prereg and harness written (2026-11-06), before any code.
- Step 1 item 1 (2026-11-06): scaffold `src/step1/`, `.venv`, pinned `requirements.txt`
  (Python 3.12.10, numpy 2.5.4, scipy 1.18.1, pytest 9.2.0, matplotlib 3.11.2);
  `src/step1/versions.py` prints them. Commit 2640b1b.
- Step 1 item 2 (2026-11-06): `bits.py`, `walsh.py`, `models/base.py` (shared interface),
  `models/iqp.py` (FWHT forward + adjoint gradient, moment Jacobian, 10 restarts,
  `iqp_moments_mc` stub), `models/maxent.py` (convex dual, ridge 1e-8),
  `tests/test_core.py`. `bash scripts/check.sh --stage 1` exits 0
  (14 passed, 1 xfailed). Tests that pass:
  - FM1: FWHT, cos closed form and explicit statevector moments agree to 1e-12 at n = 6
    (all 63 parities, 3 random theta ~ N(0,1)); a factor-2 negative control;
  - adjoint gradient vs central finite differences, rel. err < 1e-6 at n = 6 and n = 12;
    the moment Jacobian vs finite differences at n = 6;
  - MaxEnt(2) recovers Ising lambda to 1e-6 at n = 8;
  - fit machinery reaches < 1e-10 from a start near the truth (n = 6).

## In progress: item 3, STOPPED at the biased residual gate (2026-11-06)
- Written: `targets.py`, `metrics.py` (no model imports), `run.py` (model discovery via
  `build(n)` in each models/ module; `--all` refuses without BUDGET_OK; not run).
- Run (L-BFGS-B, hyperparameters unchanged, 10 restarts, init N(0, 0.05^2)):
  | target, N = inf, seed 0 | R | G_iqp | G_maxent | G_uniform | resid IQP | resid MaxEnt | gap_valid |
  |---|---|---|---|---|---|---|---|
  | ising  | 1.10e13 | 4.67e-4 | 4.2e-17 | 3.53e-3 | 1.75e-2 | 6.4e-15 | false |
  | biased | 1.92 | 6.56e-4 | 3.42e-4 | 4.49e-4 | 5.72e-3 | 6.1e-16 | false |
- ising: R >> 1, so the P3 stop rule did not fire (gap invalid anyway: IQP underfit).
- biased: **IQP cannot reach 1e-10** -> stopped per spec and user instruction; `random`
  not run, so `check.sh --stage 2` fails only on the missing random metrics.json
  (the repro check passed).
  - restart residuals: 1.10e-2, 9.23e-3, 1.44e-2, 1.15e-2, 9.01e-3, 9.19e-3, 7.44e-3,
    9.79e-3, 9.16e-3, 5.72e-3; every restart ends "RELATIVE REDUCTION OF F <= FACTR*EPSMCH"
    after 296-546 iterations, i.e. at a stationary point, not at an iteration limit.
  - best trace: it0 1.59, it5 0.345, it10 8.95e-2, it20 3.51e-2, it50 1.63e-2,
    it100 1.07e-2, it200 5.76e-3, it388 5.72e-3 (flat).
  - moment Jacobian at the solution: rank 297/298, sv max 1.73, **sv min 2.70e-9**
    (ising: 297/298, 4.98 / 1.56e-9). The same near-singular-stationary-point signature
    as the n = 6 xfail diagnostic.
  - trained angles: max|theta| 0.63, clifford dist median 0.079.
  - G_iqp > G_uniform at biased: the underfit IQP completes worse than uniform.

## FM2 diagnostics (user chose option A; 2026-11-06), `diagnostics/step1_fm2/SUMMARY.md`
- biased, N = inf, seed 0, n = 12. Diagnostics only: no change to `src/step1/`, nothing
  written to `results/`.
- At the embedded truth θ*: residual 1.1e-31, Jacobian rank 298, sv_min 1.4e-5.
- (1) θ* + noise, L-BFGS-B: σ = 0.01 → 5/5 reach ~1e-12 (4.5k–10k iterations);
  σ = 0.1 → 0/5 (1.3e-4 to 2.0e-3); σ = 0.3 → 0/5 (3.5e-2 to 1.0e-1).
- (2) 50 small-angle restarts, L-BFGS-B: 0/50; min 5.72e-3, median 9.49e-3, max 2.05e-2;
  all end at rank 297, sv_min 3e-11 to 8e-9. Restarts 0–9 reproduce production exactly.
- (3) least_squares trf with the analytic Jacobian, first 3 inits (**truncated at 3 of 10
  by the user**): 7.3e-3, 1.1e-2, 8.4e-3; ~8–10 min each.
- Reading: landscape, not optimizer. The exact solution exists but its basin is narrow
  (between 0.01 and 0.1 per angle), and every failed run ends at a rank-deficient
  stationary point. More restarts or trf do not help.

## Amendment 1 (approved, master f25c205, merged): STOPPED at build step 2/3 (2026-11-06)
- Implemented (amendment 1, post-hoc): `select_sparse_generators(fhat, ops)` (NNLS,
  threshold 1e-3·max, K_MAX 60, both guesses and unchanged), sparse init with
  |θ| = sqrt(NNLS) and signs from default_rng(seed*100 + r) (restart 0 all +),
  `--gens sparse|generic` (default sparse; generic reproduces FM2 bit for bit),
  `maxent_proj` target (own dual solver in targets.py; moment residual vs biased 5e-16),
  support_recall/precision logged after the fit only, grid targets biased/maxent_proj/random.
- **Spec-mandated selector test fails** (`test_nnls_selector_recovers_small_angle_support`,
  biased layout with |θ| in [0.04, 0.06], n = 12, seeds 0 and 1):
  - The ranking is perfect: the 38 true generators are exactly the top 38 NNLS values
    (smallest true 1.15e-3, largest spurious 1.09e-4 / 1.21e-4).
  - θ² error max 7.8e-4 / 6.1e-4 (< 1e-3: passes).
  - But 184 / 176 spurious candidates (28 / 23 pairs and 156 / 153 triples) are ≥ the
    threshold 1e-3·max ≈ 3.3e-6, so the K_MAX = 60 cap keeps 38 true + 22 spurious.
  - Cause: second-order truncation. ‖M θ²_true − m‖ = 2.0e-2, while the NNLS residual is
    3.2e-4. NNLS absorbs the fourth-order terms with small spurious θ².
    `diagnostics/step1_amend1/nnls_diag.{py,log}`.
  - Threshold and K_MAX not changed (user instruction).
- My own test `test_sparse_fit_reaches_small_residual_on_small_angle_target` also fails:
  with the 60 selected generators (a superset of the truth) and 2 restarts, the residual
  is 5.2e-6, not < 1e-10.
- **P1′ (biased, N = inf, seed 0), run as a diagnostic into
  `diagnostics/step1_amend1/biased_Ninf_seed0_sparse_metrics.json`, not into results/**
  (tests were failing):
  - K = 60 (the cap): 1 one-body and 59 triples.
  - support recall 5/38 = 0.13, precision 5/60 = 0.083. The hits are (6,), (0,4,5),
    (0,8,9), (2,3,11), (8,10,11).
  - NNLS residual 0.99: at θ ~ N(0, 0.4²) (median |θ| 0.26, max 0.90) the small-angle
    expansion does not hold.
  - IQP residual 0.116 (best of 10; restarts 0.116 to 0.166).
  - Trace: it0 1.54, it5 0.445, it20 0.175, it50 0.120, it100 0.1162, it130 0.1162 (flat).
  - Jacobian rank 60/60, sv min/max 0.216 / 1.60 (well conditioned: a genuine local
    minimum of an under-specified model, not a near-singular point).
  - R = 2.65, gap_valid false. P1′ fails on seed 0 and P6′ fails on seed 0.
- Not run: maxent_proj, random. `results/step1/biased/Ninf/seed_0` is still the old generic
  run, so check v2 rejects it (no gens_mode/support keys).

## P1′ / P6′ verdict over 5 seeds (user chose A; 2026-11-06), `diagnostics/step1_amend1/SUMMARY.md`
| seed | K | support recall | precision | NNLS residual | IQP residual | R | gap_valid |
|---|---|---|---|---|---|---|---|
| 0 | 60 | 0.132 | 0.083 | 0.990 | 1.16e-1 | 2.645 | false |
| 1 | 60 | 0.053 | 0.033 | 0.865 | 9.36e-2 | 3.528 | false |
| 2 | 60 | 0.053 | 0.033 | 0.988 | 7.71e-2 | 3.194 | false |
| 3 | 60 | 0.079 | 0.050 | 0.693 | 6.87e-2 | 2.599 | false |
| 4 | 60 | 0.105 | 0.067 | 0.971 | 8.92e-2 | 3.168 | false |
- **P1′: FAIL** (residual ≤ 1e-10 on 0/5; 0/5 valid gaps). **P6′: FAIL** (recall ≥ 0.9 on 0/5).
- **Step 1 ends by the P1′ kill rule.** No fix started. Outputs are in diagnostics/, not results/.
- check.sh --stage 1 fails on the three selector tests (known state; tests, K_MAX and
  threshold unchanged).

# Step 2 (specs/step2_sigma_boundary.md, master 619c63b; branch step2-sigma)

## Build item 2 (2026-11-06): code done, STOPPED on the spec-mandated O test
- Merged master into step1-synthetic, then `git switch -c step2-sigma`.
- `src/step2/sweep.py`:
  - targets: θ = σ·z on the step-1 biased layout, with z reused across σ; σ = 0.4 is
    step 1's biased bit for bit;
  - fits O (oracle support, 38 gens) and G (generic 298), plus MaxEnt(3);
  - D3 = KL(p ‖ MaxEnt3(p)), hi_order_frac, collision, Clifford median of the target;
  - R only on success;
  - `--all` gated on BUDGET_OK; `pauli_path_tv` raises NotImplementedError.
  - `src/step1/` is imported, never edited.
- `tests/test_step2.py`: 7 pass (z reuse, σ = 0.4 equals step-1 biased, D3 = 0 on a
  MaxEnt(3) target to 1e-10, the stub, KL and hi_order_frac sanity).
  **`test_oracle_support_fit_reaches_1e10_at_sigma_005` fails** → `check.sh --stage 4` fails.
- Diagnostic for O at σ = 0.05, seed 0: `diagnostics/step2_h1/o_sigma005_seed0.{py,log,json}`.
  - All 10 restarts stop at stationary points with ftol: 1.05e-6 to 4.20e-6 (|grad| 4.5e-8).
  - Trace: it0 1.25e-1, it10 5.0e-3, it20 1.5e-4, it50 5.4e-6, it100 1.3e-6,
    it584 1.05e-6 (flat).
  - Jacobian at the fit: rank 38/38, sv min 8.0e-3 (at the truth: 2.2e-2; residual 1.9e-29).
    So these are well-conditioned local minima, not FM2's near-singular points.
  - After aligning the signs over the exact gauge group (θ_g → (−1)^{|g∩B|} θ_g, and
    global −θ): magnitudes match to 3.6e-3, but **8/38 signs are wrong, all on pairs**:
    (0,3), (0,7), (2,6), (2,7), (3,11), (4,8), (5,6), (5,9).
  - Interpretation: at small σ the order-≤3 moments see pair signs only through
    third-order products (~θ³), so wrong-sign configurations are near-degenerate minima
    (residual ~1e-6).
  - This is H1's first look (seed 0 only). Nothing was changed.

## H1 verdict over 5 seeds (user chose A; 2026-11-06), `diagnostics/step2_h1/SUMMARY.md`
| seed | best residual | O success | wrong-sign pairs / triples (best restart) | G_maxent | G_iqp min / median / max over 10 restarts |
|---|---|---|---|---|---|
| 0 | 1.05e-6 | 0/10 | 8 / 0 | 1.70e-7 | 1.3e-8 / 2.2e-8 / 3.2e-8 |
| 1 | 9.06e-6 | 0/10 | 8 / 3 | 2.75e-7 | 1.6e-7 / 1.9e-7 / 2.7e-7 |
| 2 | 4.41e-6 | 0/10 | 7 / 5 | 1.10e-7 | 4.3e-8 / 1.0e-7 / 1.3e-7 |
| 3 | 6.51e-6 | 0/10 | 7 / 3 | 6.92e-8 | 7.2e-8 / 2.9e-7 / 5.2e-7 |
| 4 | 1.72e-6 | 0/10 | 7 / 4 | 7.99e-8 | 2.5e-8 / 6.7e-8 / 1.4e-7 |
- **H1: FAIL (0/5 seeds).** **Step 2 ends by its kill rule.** No fix started.
- The sign counts use a canonical gauge fixing: B chosen so that all one-body signs match,
  for each global sign. The first, min-over-all-B count had ties; the canonical one
  reproduces the seed-0 result (8, all pairs).
- Completion spread: among solutions with residual < 1e-5, the G_iqp spread is
  0.1–1.0 × G_maxent (4 evaluable seeds), never larger. G_iqp tracks the residual
  (log–log corr 0.96). G_true = 0. G_uniform ≈ 0.8.
- check.sh --stage 4 still fails on `test_oracle_support_fit_reaches_1e10_at_sigma_005`
  (the test is unchanged).

# Step 3 (specs/step3_completion_vs_sigma.md, master ab2ecab; branch step3-ratio)
Designed after the step 1–2 diagnostics (notes/2026-11-06_steps1-2_findings.md).

## Build item 2 (2026-11-06): DONE, `check.sh --stage 7` passes
- Merged master into step2-sigma, then `git switch -c step3-ratio`.
- `src/step3/run.py` (imports src/step1 and src/step2; both unchanged since 163fe19):
  - targets: `iqp(σ, s)` from `step2.sweep.sigma_target`. `maxent_proj(σ, s)` comes from
    step 1's `maxent_projection`, polished by Newton steps on the same convex dual
    (`refine_projection`, new in step 3: max 20 steps, tol 1e-14, both guesses).
    - Why the polish: step 1's projection meets 1e-10 only as a sum of squares. Its max
      |moment error| was 2e-9 to 3.4e-8. After 1–2 Newton steps it is ≤ 6.4e-15 at every σ
      (seed 0).
  - **Training input shared by the pair:** the exact order-≤3 moments of `iqp(σ, s)`. Spec:
    "identical inputs on the pair". Sharing one vector makes the O, G and MaxEnt fits
    bit-identical on both members; the pair mismatch is recorded (`pair_moment_*`).
  - fits O (38 oracle gens), G (298 generic) and MaxEnt(3). No recovery gate.
    R = G / G_maxent at the lowest-training-residual restart (first on ties).
  - All 10 restarts are kept: replayed with fit_moments' own init draws, each optimized by
    the production `fit_moments(..., n_restarts=1, theta0=...)`.
  - The record has every key that check v4 requires, plus per-restart nit/messages, per-level
    errors and the best params. `--all` is gated on BUDGET_OK (not run).
- `tests/test_step3.py`, 10 tests, all pass:
  - maxent_proj vs iqp order-≤3 moments ≤ 1e-10 as both sum of squares and max |diff|,
    for all 6 σ;
  - O identical on the pair (residuals per restart to 1e-12, same best restart and params);
  - R at the lowest-residual restart (not the lowest G);
  - the replay equals fit_moments with 10 restarts.
- check.sh --stage 7: ALL CHECKS PASS (it runs the tests, about 2 min 10 s).

## Build item 3 (2026-11-06): first runs + projection DONE, waiting for BUDGET_OK
- 4 instances at seed 0 (σ = 0.05, 0.4 × iqp, maxent_proj), each O, G, MaxEnt(3), written to
  `results/step3/<target>/sigma_<σ>/seed_0/metrics.json`; console log `results/step3/first_runs.log`.
- `src/step3/projection.py` → `results/step3/PROJECTION.json`.
- PRELIMINARY (one seed, not an IQR):

  | target | σ | R_O | R_G | G train residual | G_maxent (paired iqp) | instance s |
  |---|---|---|---|---|---|---|
  | iqp | 0.05 | 0.0903 | 0.121 | 1.38e-7 | 1.70e-7 | 546 |
  | iqp | 0.4 | 8.6e-16 | 1.92 | 5.72e-3 | 3.41e-4 | 92 |
  | maxent_proj | 0.05 | 7.6e5 | 6.3e5 | 1.38e-7 | 1.70e-7 | 494 |
  | maxent_proj | 0.4 | 1.7e15 | 1.7e15 | 5.72e-3 | 3.41e-4 | 92 |

  - K1: R_O ≥ 1 at both σ. K2: applies at σ = 0.05 only (1.38e-7 ≤ 1.70e-7), R_G ≥ 1 there;
    at σ = 0.4 G's residual is above the paired G_maxent, so K2 does not constrain it.
  - On maxent_proj, G_maxent is ~1e-13 / 1e-19 (MaxEnt(3) IS the target), so R there is a
    ratio over a numerically ~zero denominator: huge, and K1/K2 pass by construction.
  - C1 (iqp, O, σ = 0.05): R_O = 0.090 < 1, replicates step 2.
- Projection (spec basis, σ = 0.4 pair × 60): 1.53 h, under 2 h → no cut by the spec rule.
  But σ = 0.05 is measured ~5.6× slower (546 / 494 s vs 92 s; G fit 336–359 s and the
  projection/MaxEnt ~107–167 s). Using the measured σ = 0.05 time for its 10 instances:
  2.72 h. σ = 0.1–0.3, 0.6 are untimed.

- User chose A (2026-11-06): budget cut (1), G restarts 10 -> 3, applied to `--all` only
  (`ALL_GRID_RESTARTS` in run.py; the first 3 of the 10 init draws; each metrics.json records
  `G_n_restarts` and `budget_cut`). The grid run will redo the seed-0 instances with the
  same setting. Projection after the cut (linear guess, untimed): 0.73 h (spec basis),
  1.38 h (with measured σ = 0.05).
- Committed as 0836290 after the user created BUDGET_OK (the guard then let it through).

## Build item 4 (2026-11-06): DONE, `check.sh --stage 9` passes
- Full grid, 60/60 instances, G with 3 restarts: 118 min wall clock (`results/step3/grid.log`).
- `python -m src.step3.run --report` → `table.csv`, `verdicts.json`, `figures/step3/*`.
- `results/step3/SUMMARY.md`: K1 PASS, K2 PASS (both by construction: maxent_proj's truth is
  MaxEnt(3), G_maxent ≈ 0, so only a correctness check), C1 PASS (R_O median 0.42),
  M1 FAIL (3 violations), M2 FAIL (σ = 0.05, 0.1), M3 FAIL (W = {0.1, 0.2, 0.3, 0.4};
  0.3 and 0.4 come from oracle exact recovery). Residual–G correlation breaks down for G at
  σ ≥ 0.3 (stated prominently). Non-oracle G: R_G < 1 at σ ≤ 0.2.

## Next
- Step 3 is complete. Waiting for the user.
- Left in the worktree, not committed: `.harness/STAGE` (changed by the user, not by me).

## Open questions for the user
1. **FM2 already visible at n = 6 (xfail test, kept as a diagnostic).** Fitting the IQP to
   the exact order-<=3 moments of an IQP-generated target (all 41 generators of weight <= 3,
   theta* ~ N(0, 0.4^2)) from theta ~ N(0, 0.05^2): every restart stops at a different
   stationary point, residual 1e-4 to 6e-3, |grad| ~ 1e-8, smallest Jacobian singular value
   ~ 1e-8 (rank 40-41 of 41). From theta* + 0.01 noise the same code reaches 1e-15. So the
   gradient is right, and the landscape has many spurious minima. Trace for target seed 11
   (every 25 iterations): 1.6e0, 1.2e-2, 3.8e-3, 1.6e-3, 2.5e-4, 2.3e-4, 2.2e-4 (flat).
   This predicts a real risk for P1 (`biased`, N = inf, residual <= 1e-10) in item 3. No
   hyperparameter was changed. When it shows up at n = 12, I will stop and show the trace,
   as the spec says.
2. **check.sh stage 1 requires `src/step1/metrics.py`,** but the build order puts
   metrics.py in item 3. I added a docstring-only placeholder (no code, no imports) so the
   architecture-rule grep has a file to check. Two wording side effects of the greps:
   the arch-rule regex `(from|import)[^#]*models` also matches prose in a docstring, and
   the isolation grep also matches the repo name in comments and in stale `__pycache__`
   files. I reworded my docstrings; the checks themselves are unchanged.

## Guesses (not tuned)
- n = 12; target angle scale 0.4; init scale 0.05; 10 restarts; MaxEnt ridge 1e-8; levels 4–6.
- L-BFGS-B options (both models): maxiter 20000, maxfun 40000, ftol 1e-16, maxcor 20;
  gtol 1e-13 (IQP) / 1e-12 (MaxEnt). scipy's ftol is effectively absolute once L < 1.

# Step 4 (specs/step4_misspec_finite_n.md, master fe7d058 + harness v5 ceeef36; branch step4-misspec)

## Build items 1-2 (2026-11-06): DONE, `check.sh --stage 10` passes
- master merged into step3-ratio (e231798), then `git switch -c step4-misspec`.
- `src/step4/targets.py`: iqp4 (iqp + 6 weight-4 generators, supports then z' from
  default_rng(4000+s), angles sigma*z'), mix (K = 3 product-Bernoulli, from default_rng(5000+s):
  Dirichlet weights then u; the same (w, u) for every delta), stub fit_mixture_moments.
- `src/step4/run.py`: targets, training moments (exact or from sample_indices), noise floor,
  delta calibration, run_instance (G 3 restarts via step 3's fit_restarts, MaxEnt(3) frozen
  ridge), CLI, grid flag gated by the budget-approval file. Paths/keys as check.sh v5.
- `tests/test_step4.py`: 10 tests pass (about 20 s).
- **Calibration** (`results/step4/calibration.json`, D3 only): iqp sigma=0.2 median D3 = 0.187.
  mix median D3: delta 0.2 → 1.1e-7, 0.4 → 2.3e-5, 0.6 → 4.3e-4, 0.8 → 2.9e-3. Rule picks
  **delta = 0.8, but its D3 is ~64x below the reference**: no candidate reaches the
  iqp D3. Reported; candidates and rule not changed.
- **FM2 warning (spec failure mode 3):** G on iqp4's exact moments, sigma=0.2 seed 0, 3
  restarts: best residual 2.1e-3 (restarts 3.1e-3, 2.1e-3, 2.7e-3), versus 1.5e-4 for iqp at
  sigma=0.2 in step 3. The test (> 1e-8) passes, but at this level P1 would test training
  failure, not completion.

## Pre-amendment diagnostics D1, D2 (user chose A; 2026-11-06), `diagnostics/step4_pre/SUMMARY.md`
Blind: no G_iqp / G_maxent / R / order-4..6 error computed. src/step4, spec, calibration.json
and harness unchanged.
- D1 (iqp4, sigma = 0.2, seeds 0-4): truth weight-<=3 angles alone give residual 0.6-3.1;
  warm start from them ends at 1.4e-3-5.0e-3, the same level as the best of 10 random
  restarts (ratio 0.98-1.68; 44/50 restarts within 2x of warm). sigma_min(J) 3e-10-4e-8 at every
  solution. The ~1e-3 floor is reached from every start; misspecification floor vs FM2 not
  separable from these numbers.
- D2 (mix): median D3 at delta 0.9 / 0.95 / 0.99 = 6.0e-3 / 8.3e-3 / 1.07e-2, vs the iqp
  sigma = 0.2 reference 0.187 (~17x below even at 0.99).

## Amendment 1 (specs/step4_amendment1.md, approved; master merged 2026-11-06)
- mix: K_MIX is a parameter (K = 3 bit-identical to the original draws; tested).
  `results/step4/calibration_amend1.json` (D3 only): reference = median D3 of iqp at
  sigma = 0.1 from the step-3 table = 0.0462; rule (closest on log scale) → **K = 48,
  delta = 0.99** (median D3 0.0385). calibration.json unchanged. The grid's mix reads
  calibration_amend1.json (tested). 13 tests pass; check.sh --stage 10 passes (2ecbd53).

## Build item 3 (2026-11-06): timing + PROJECTION.json DONE, waiting for the budget-approval file
- iqp4 sigma=0.2 N=1e4 seed 0: 7.0 s (G fit 6.3 s); G residual 2.9e-3 (restarts 3.2e-3,
  2.9e-3, 3.6e-3); MaxEnt residual 8.2e-15; noise floor 9.2e-5.
- mix (K=48, delta=0.99) N=1e4 seed 0: 1.9 s (G fit 1.6 s); G residual 2.4e-2 (restarts
  3.7e-2, 2.9e-2, 2.4e-2); MaxEnt residual 9.6e-16; noise floor 1.0e-4.
- R is in the two metrics.json files only (not reported, per the user).
- PROJECTION.json: spec rule 140 x 7.0 s = 0.27 h (x1.43 step-3 slowdown: 0.39 h). Caution
  (assumption, untimed): step-3 iqp/maxent_proj instances at sigma 0.1/0.2, N = inf took
  ~145 s each; if the 80 iqp/maxent_proj instances cost that, 3.3 h (over the 3 h cut line).
- `python -m src.step4.run --projection` writes PROJECTION.json; check.sh --stage 11 passes.

- User chose A: two more timed instances (production run_instance):
  - iqp sigma=0.1 N=inf seed 0: 27.4 s (G fit 23.5 s); G residual 4.9e-7 (restarts 4.7e-5,
    4.9e-7, 4.3e-6), identical to step 3's G fit for this instance; MaxEnt residual 7.1e-14.
  - maxent_proj sigma=0.1 N=1e4 seed 0: 25.3 s (G fit 5.0 s; most of the rest is the
    projection pair); G residual 3.3e-4 (restarts 5.0e-4, 3.3e-4, 3.5e-4); MaxEnt residual
    2.1e-13 but nit 15311 of maxiter 20000 (close to FM-N1's symptom; not hit).
  - Step 3's per-instance times were inflated: the same G fit took 193 s there vs 23.5 s now.
- PROJECTION.json: projected_hours = sum over targets of own time x count =
  40x27.4 + 40x7.0 + 40x25.3 + 20x1.9 s = **0.67 h** (x1.43 step-3 slowdown: 0.96 h). Spec rule
  kept as projected_hours_spec_rule = 0.27 h. Under 3 h: no cut needed.

## Build item 4 (2026-11-07): DONE, `check.sh --stage 12` passes
- Full grid 140/140 (80 min wall clock; machine shared). `python -m src.step4.run --report`
  → table.csv, verdicts.json, figures/step4/{ratio_vs_N, ratio_at_inf, noise_floor}.
- `results/step4/SUMMARY.md`: K PASS (maxent_proj finite N, R >= 1 in all 6 cells), R1 PASS
  (identical to step 3's R_G), P1 PASS (iqp4 sigma=0.2 N=inf R 0.58 [0.45, 0.58], G residual
  2.1e-3 = family floor, D1), P2 PASS (mix R 5.0 [4.6, 5.6]; room level sigma = 0.1, K=48,
  delta=0.99; latent-class baseline out of scope), F1 PASS, F2 PASS (0.55 [0.47, 0.72]).
- Not a hypothesis, reported: iqp4 at sigma = 0.1 gives R >= 1 at every N (7.9 at N = inf).
- FM-N1: MaxEnt hit maxiter on 19/140 (finite N), residual still <= 1.4e-8. FM-N2: G fits the
  sampling noise at N = 1e3 (residual << 298 x noise floor).

# Step 5 (specs/step5_iqp4_sigma_scan.md, master 53d28cf + harness v6 cbacddc; branch step5-sigma)

## Build items 1-2 (2026-11-07): DONE, `check.sh --stage 14` passes; waiting for BUDGET_OK
- Branch step5-sigma from step4-misspec, master merged (cbd0cfd). src/step1..4 untouched.
- `src/step5/targets.py`: iqp4f (weight-<=3 angles sigma*z, the 6 weight-4 angles fixed at
  tau*z' with tau = 0.2); iqp4 re-exported from step 4.
- `src/step5/run.py`: one instance path (fit_instance) for both targets, mirroring step 4's
  run_instance with its pieces imported; sigma* (log-log interpolation), sign changes, Q5 rule
  (unnamed cases: FAIL with the reason; my reading), projection, BUDGET_OK-gated grid.
- `tests/test_step5.py`: 14 tests (identity iqp4f(0.2) == iqp4(0.2) for 5 seeds; weight-4
  angles = 0.2 z' at all 6 sigma; sigma* on synthetic series; Q5 undefined rule; paths).
- Reproduction: iqp4 sigma=0.2 N=inf seed 0 equals step 4 bit for bit (R 0.4496178750620470,
  relative difference 0; same 3 restart residuals).
- Timing (sigma=0.25, N=1e4, seed 0): iqp4 5.4 s (G residual 2.6e-3; restarts 2.9e-3, 6.4e-3,
  2.6e-3), iqp4f 6.3 s (G residual 1.9e-3; restarts 1.9e-3, 5.4e-3, 2.4e-3).
- PROJECTION.json: 60 x 5.4 s + 60 x 6.3 s = 0.19 h (x2 shared machine: 0.39 h); budget 1 h,
  no cut.

- Step 5 amendment 1 (master f6a3ca7, merged): Q5's two unnamed cases are FAIL. run.py's
  q5_verdict now follows it, with case 1 (sigma*(inf) undefined) checked FIRST, so it FAILs even
  when R >= 1 everywhere at 1e4 (my earlier order would have PASSed that). Each verdict records
  the rule it used (spec section 3 or amendment 1 case 1/2); the SUMMARY must cite the amendment
  next to Q5. 14 tests pass.

## Build item 3 (2026-11-07): DONE, `check.sh --stage 15` passes
- Full grid 120/120, no cut (13.7 min; projection 0.19 h). `python -m src.step5.run --report`
  → table.csv, verdicts.json (sigma* and sign changes per target x N), figures/step5/{R_vs_sigma, G_vs_sigma}.
- `results/step5/SUMMARY.md`: Q0 PASS; Q1 PASS (sigma*(iqp4, inf) = 0.160, 1 sign change);
  Q2 PASS (G_iqp max/min 2.30, G_maxent 0.25/0.1 = 21.5); Q3 FAIL (sigma = 0.25: R 0.891
  [0.836, 1.14], undecided; no FM2); Q4 PASS (low confidence; margins 5-6% at 0.15/0.175);
  Q5 FAIL (sigma*(1e4) = 0.151 < 0.160; spec rule, amendment 1 cited, its cases not triggered).
- MaxEnt maxiter: 0/120. Reproduction of step 4 (sigma 0.1/0.2, N = inf, 5 seeds) checked by stage 15.
- Exploratory: R is lowest at sigma = 0.2 and rises again at 0.25 for every target x N.

## Next
- Step 5 is complete. Waiting for the user.

# Step 6 (specs/step6_iqp4_scaling_n.md, frozen 567aab6; harness v7 bccacee)

## Build items 1-2 (2026-11-07): DONE, `check.sh --stage 17` passes; stopped for BUDGET_OK
- Branch `step6-scaling` from `step5-sigma` (bdc4cea), master merged. src/step1..5 untouched.
- `src/step6/run.py`: one instance = `src.step5.run.fit_instance("iqp4", sigma, N=None, seed, n)`
  imported unchanged, plus G_n_params, peak memory (Windows peak working set), IO, projection with
  the spec's cut order, BUDGET_OK-gated grid.
- `tests/test_step6.py`: 5 pass (n = 12 reproduces step 5 sigma = 0.2 seed 0 within 1e-6;
  G generators 469 / 696; iqp4_target at n = 14 has 46 generators; paths).
- Timing (sigma = 0.2, seed 0, N = inf, 3 restarts, all L-BFGS-B converged, not maxiter):
  - n = 14: 51.2 s (G fit 30.0 s); G residual 4.3e-3 (restarts 4.3e-3, 5.8e-3, 4.8e-3; nit
    2213, 1203, 1438); MaxEnt residual 3.4e-14 (nit 1976); peak 318 MiB.
  - n = 16: 399.6 s (G fit 334.4 s); G residual 6.7e-3 (restarts 6.7e-3, 7.4e-3, 7.2e-3; nit
    2356, 2568, 2093); MaxEnt residual 1.9e-13 (nit 875); peak 1476 MiB.
- PROJECTION.json: 25 x 51.2 s + 25 x 399.6 s = 0.36 + 2.78 = 3.13 h > 3 h. Cut step 1 (drop
  n = 16 sigma = 0.25) -> 45 instances, 2.58 h, within budget. x2 shared-machine: 6.3 h.

- User chose A (cut n = 16 sigma = 0.25), created BUDGET_OK, STAGE 18; stop limit raised 5 h -> 7 h mid-run.

## Build item 3 (2026-11-08): DONE, `check.sh --stage 18` passes
- Grid 45/45 (n = 16 sigma = 0.25 cut per spec section 7), resumable (`--all` skips existing
  metrics.json; the two timed instances were reused). Wall clock ~4.9 h (21:35-02:31); sum of
  instance times n = 14 0.45 h, n = 16 4.61 h (projected 2.58 h; n = 16 per-iteration time varied ~15x).
- `--report` -> table.csv (n = 12 from step 5), verdicts.json, figures/step6/{R_vs_sigma_by_n,
  G_vs_sigma_by_n, collision_vs_n}; SUMMARY.md.
- S1 FAIL (sigma 0.2: n14 0.889 [0.720, 1.04], n16 1.38 [0.623, 1.51], both undecided);
  S2 FAIL (sigma*(14) = 0.185 in band; sigma*(16) undefined, median R >= 1 at all 4 sigma);
  S3 FAIL (sigma 0.175: n14 undecided 1.08, n16 >= 1 1.81); S4 PASS (n16 G_iqp max/min 1.54 over 4 sigma).
- Failure modes: n = 16 seed 1 residual >> 1e-2 at sigma 0.125 (0.160) and 0.15 (0.179), highest
  at every n = 16 sigma -> flagged as a pattern (possible FM2/under-training, R possibly biased
  up); 26 other instances 1e-2..3.6e-2; G maxiter 0/45; MaxEnt maxiter 2/45 (n16 seed 3,
  sigma 0.125/0.15, residual <= 3.6e-11); peak memory 1.5 GiB.
- Exploratory: at fixed sigma R grows with n; G_maxent3 (room) shrinks faster with n than G_iqp
  while D3 stays ~0.24; collision ratio x3.3-4 per +2 qubits.

## Next (at step 6 close)
- Step 6 was complete; step 7 spec (3407d50) and harness v8 (d401a18) followed.

# Step 7: collision-matched sigma (specs/step7_collision_matched.md), branch step7-collision

## Build items 1-4 (2026-11-08): DONE in one pass (user removed the harness hooks and created BUDGET_OK; told to run through without stopping)
- src/step7/run.py wraps src.step6.run.run_instance at the six exact matched sigma
  (n14 A/B/C 0.193/0.213/0.236; n16 0.231/0.251/0.274) and records level + n = 12 reference.
- tests/test_step7.py: 9 pass (step 6 R reproduced at n14 sigma 0.2 seed 0 within 1e-6; sigma table
  exact; each matched sigma's median collision within x1.25 of its n = 12 level).
- Timing (largest sigma, seed 0): n14 48.6 s, residual 1.85e-3, nit 1360/2244/2436, 318 MiB;
  n16 762.4 s, residual 9.69e-4, nit 6213/3088/7654, 1477 MiB. PROJECTION 3.38 h < 5 h -> no cut.
- Grid 30/30, no cut (user decision), resumable; wall clock 12:55-17:22 (4 h 27 min); sum of
  instance times 4.46 h (n16 4.27 h, 230-1641 s per instance).
- Report: table.csv, verdicts.json, figures/step7/{R_vs_collision_by_n, G_vs_level_by_n}, SUMMARY.md.
- C1 FAIL (B: n14 0.870 <1, n16 0.654 [0.651, 1.105] undecided); C2 FAIL (C: n14 0.706 <1, n16 0.799
  [0.593, 1.313] undecided); C3 FAIL (A medians 0.754, 0.832 < 1); C4 PASS (n16 residual B 2.1e-3,
  C 1.6e-3). Reading rule: advantage shrinks with n at matched peakedness, not under-training;
  qualified: n16 cells are undecided (medians < 1), driven by seeds 1 and 2 having R > 1 at all levels.
- Failure modes: G maxiter 0/30, MaxEnt maxiter 0/30, max G residual 2.3e-2 (n14 A seed 3); n16 seed 1
  highest residual at every level (1.8e-2 / 9.7e-3 / 4.8e-3), smaller than step 6.
- Exploratory: n14/n16 R flat 0.65-0.87 across levels (no collapse onto n = 12); D3 grows with n at
  matched collision (level C 0.248 / 0.251 / 0.325).

## Next
- Step 7 is complete. Waiting for the user.

## Step 9 (2026-11-09): fresh seeds 10–29 at level B (specs/step9_fresh_seeds.md, amendment 1)
- Done: 40-instance grid plus the n = 16 reproduction instance; 1.31 h with 16 workers × 1 thread; no
  failures. Report, figures and SUMMARY are written.
- Verdicts:
  - H1 PASS: 16/20 win at n = 16, robust to a 10% margin.
  - H5 PASS: median 0.637, IQR [0.543, 0.889].
  - H6 PASS.
  - H2 FAIL: 10/20 at n = 14, with under-training in 8/20 seeds.
  - H3, H4 and H7 FAIL: step 8's two-mechanism model does not hold out of sample.
- `--verify` exits 1 on [repro] only: n = 16 seed 0 is off by 6.0e-3 at 1 thread. Every n = 16 R
  is flagged; this changes no sign. The check was not loosened.
- Harness: no v9 hooks or BUDGET_OK. The user said "全部做完不要再問了" ("finish everything,
  don't ask again"); this is noted in the spec.

## Step 10 (2026-11-10): n = 14 with 10 G restarts (specs/step10_more_restarts.md)
- Done: 20 seeds in 22.8 min; `--verify` exits 0.
- Verdicts:
  - K1 FAIL: 11/20 wins.
  - K2 FAIL: 7/20 residual > 1e-2.
  - K3 FAIL: 1/10 losers rescued.
  - K4 PASS: 0/10 winners flipped.
- High residuals are a floor: 10 restarts land within 1.2–1.6×. So step 9's n = 14 losses are not
  under-training but moment misfit and real losses.
- Oracle restart choice gives only 11/20, so no selection rule rescues n = 14.

## Step 11 (2026-11-10): bitflip (decohered) control (specs/step11_bitflip_control.md)
- Done: 40 seeds in 0.88 h (12 workers x 1 thread); `--verify` exits 0. Code 17276d5.
- Verdicts:
  - C1 PASS: n = 16, G_iqp < G_bitflip in 20/20.
  - C2 FAIL: n = 16, bitflip beats MaxEnt(3) in 3/20.
  - C3 PASS: n = 14, 20/20.
  - C4 FAIL: n = 14, 2/20.
  - Frozen reading: the advantage needs coherence.
- **Caveat (load-bearing):** the bitflip model misfits the order-<=3 training moments in all 40
  seeds (median residual ~0.1, against 4/20 and 8/20 IQP seeds above 1e-2). No seed has both
  residuals <= 1e-2, so completion cannot be separated from training misfit. The decohered twin
  lacks the expressivity to match these targets' low-order moments at all.
- Minor: `--report`'s final print crashes on cp950. SUMMARY and the other files were already
  written. Run it with PYTHONIOENCODING=utf-8.
