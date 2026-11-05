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

## In progress
- (nothing; stopped at the item-2 checkpoint for review)

## Next
- Item 3: `targets.py`, `metrics.py` (currently a placeholder), `run.py`; N = inf, seed 0,
  all three targets; ising first, then biased (residual 1e-10 or show the trace).

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
