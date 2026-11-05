# Step 1, amendment 1: sparse generator set + paired negative control (post-hoc)

Status: draft for user approval, 2026-11-06. **Post-hoc**: written after the N = inf runs and
the FM2 diagnostics (`diagnostics/step1_fm2/` on branch `step1-synthetic`). Everything that
reports results must label the amended pipeline "amendment 1 (post-hoc, triggered by the FM2
diagnostics)". The original `prereg/step1.md` stays frozen. The amended predictions are in
section 4 and are frozen once this file is committed.

## 1. Evidence (do not re-derive; act on it)

| Diagnostic (biased, n = 12, N = inf, seed 0) | Result |
|---|---|
| Generic 298-generator IQP, small init N(0, 0.05²), L-BFGS-B, 50 restarts | 50/50 stuck at 5.7e-3 to 2.1e-2, all at stationary points |
| Same, `least_squares` (trf, analytic Jacobian), 3 restarts | Also stuck (restart 0: 7.3e-3, versus 1.1e-2 with L-BFGS-B) |
| Start at the true angles + noise σ | σ = 0.01: 5/5 reach ~1e-12; σ = 0.1 and 0.3: all stuck |
| Smallest Jacobian singular value | ~1e-5 near the truth; 1e-9 to 1e-11 at the spurious points |
| `ising` target | The IQP cannot fit its moments (1.75e-2), so the gap is invalid and P3 is untestable |

Interpretation:
- The problem is **identifiability, not the optimizer**. With 298 generic generators,
  matching 298 order-≤3 moments is nearly singular even at the true solution. So requirement R1
  of `notes/2026-11-05_iqp-from-limits.md` (parameters identifiable from the statistics) fails
  for the generic set.
- More restarts or another optimizer will not fix this. **Do not** try either as the fix.
- The `ising` control was badly designed (spec author's error). A negative control must be a
  target the IQP *can* fit exactly but whose true completion is max-ent.

## 2. The change: a sparse generator set chosen from the training moments

This is the **only** change to the model. Everything else in the original spec stands unless
stated here.

**Small-angle selector.** For an IQP, ⟨Z_a⟩ = E_s cos(2 Σ_{g ∈ O(a)} θ_g s_g), where O(a) =
{g : |g ∩ a| odd}. Expanding to second order, and using E[s_g s_h] = 0 for g ≠ h:

    m_a := (1 − f̂_a) / 2  ≈  Σ_g M_ag θ_g²,   M_ag = 1[|g ∩ a| odd]

1. Solve this linear system for θ_g² ≥ 0 over all 298 candidate generators with
   `scipy.optimize.nnls`, using the **training** moments only.
2. Keep the generators with θ_g² ≥ 1e-3 · max θ², capped at **K_MAX = 60** by size. Both
   numbers are guesses; mark them in code. Record K and the selected set in `metrics.json`.
3. **Initialization:** |θ_g| = sqrt(NNLS value). Each restart draws random signs
   (`default_rng(seed*100 + r)`); restart 0 uses all-positive signs. Keep 10 restarts, then
   L-BFGS-B on the sparse set, exactly as before.

**Load-bearing:** the selector must see only the training moments. It must never see the
target's true layout. For the synthetic targets, also log `support_recall` and
`support_precision` against the true layout, as diagnostics only. Never use them for selection.
If the selector "works" only because it saw the truth, the whole step is void.

**Comparison and fairness.**
- The baseline stays **MaxEnt(3) with all 298 parities**. It sees the same statistics as the
  IQP and has more parameters (298 ≥ K).
- The parameter mismatch therefore favors the baseline. That is the conservative direction:
  a win for the IQP with fewer parameters is still meaningful, and a loss is not hidden.
- Replace the old `n_params_iqp == n_params_maxent` requirement with
  **`n_params_iqp ≤ n_params_maxent`**.
- `gap_valid` keeps its definition (IQP residual within 10× MaxEnt's, or below tau).

**The original generic model stays runnable** behind `--gens generic`, so the FM2 diagnostics
can be reproduced. The default becomes `--gens sparse`.

## 3. New paired negative control: `maxent_proj`

- `maxent_proj` (seed s) = the exact MaxEnt(3) distribution fitted to the **exact** order-≤3
  moments of `biased` (seed s).
- It has the same order-≤3 moments as `biased` (to ≤1e-10), but its true completion is
  max-ent.
- So `biased` and `maxent_proj` form a **matched pair that differs only in the completion**.
  At N = inf both models see identical training data on the two targets, and only the truth
  above order 3 differs.
- This is a stronger test than `ising`. A metric or pipeline that favors the IQP will show
  R < 1 on `maxent_proj`.

`ising` stays in the code and in the results as the original (invalid-gap) control. It is
reported, but no prediction rests on it.

**Grid:** targets {biased, maxent_proj, random} × N ∈ {inf, 1000, 10000, 100000} × seeds 0–4 =
60 runs. `ising` at N = inf, seed 0 is kept as already run.

## 4. Amended predictions (frozen when this file is committed)

R and the win rule are as in the original spec.

| ID | Prediction | Type |
|---|---|---|
| P1′ | `biased`, N = inf: the sparse IQP reaches a training residual ≤ 1e-10 on ≥ 4/5 seeds, and R < 1 | **Kill.** If it fails, the sparse selector cannot even recover a target it can represent. Stop. |
| P2′ | `biased`, N = 10000: R < 1 | Main result |
| P3′ | `maxent_proj`, all N: the IQR of R lies entirely at or above 1 | **Kill.** If it fails, the pipeline favors the IQP. Stop. |
| P4′ | `random`, N = 10000: the median of \|log R\| is < log 2 | Exploratory. Large angles break the small-angle selector, so `gap_valid = false` is likely and is reported as such. |
| P5′ | `biased`, N = 10000: the median of clifford_dist_median is ≥ 0.02 rad | Report only |
| P6′ | `biased`, N = inf: support_recall ≥ 0.9 on ≥ 4/5 seeds | Diagnostic. If it fails, report it together with P1′. |

Original P1 to P5 must also be reported, as PASS, FAIL or NOT EVALUABLE with a reason. The
original P3 (`ising`) is NOT EVALUABLE because the gap is invalid.

## 5. Build order for the amendment

1. Merge `master` into `step1-synthetic`, to get this file and the updated `check.sh` that
   the user installs.
2. Selector and init in `models/iqp.py`, plus `--gens`. Add tests to `tests/test_core.py`:
   - on an IQP target with angles ~0.05, NNLS recovers the support exactly and θ² to 1e-3;
   - the selector's input is only `(fhat, ops)` (a signature test).
3. Run `biased`, N = inf, seed 0 first; that is P1′. If the residual is > 1e-10, stop and show
   K, the support recall and the residual trace. **Do not** raise K_MAX or change the threshold
   on your own.
4. Then `maxent_proj` (P3′) and `random`, all at N = inf, seed 0. Checkpoint:
   `check.sh --stage 2`.
5. Then the original item 4: PROJECTION.json, then wait for BUDGET_OK.
