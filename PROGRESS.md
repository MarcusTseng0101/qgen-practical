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

## Next
- Waiting for `specs/step1_amendment1.md` (on master; given to me only after the user
  approves it). **Do not change `src/step1/` before that.**
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
