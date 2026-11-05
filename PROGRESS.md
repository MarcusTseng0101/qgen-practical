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

## Next
- Step 2 is stopped by the H1 kill rule. Waiting for the user.
- Left in the worktree, not committed: `.harness/STAGE` = 1 (changed by the user, not by me).

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
