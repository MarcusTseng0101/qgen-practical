# Step 1 predictions (written 2026-11-06, before any code or run; frozen)

Definitions are in `specs/step1_synthetic_completion_gap.md`:
- R = G(IQP)/G(MaxEnt3) on parity levels 4–6 against the exact target;
- "R < 1" means the 5-seed IQR of the valid R values lies entirely below 1, with at least 4 of
  5 valid.

| ID | Prediction | Type |
|---|---|---|
| P1 | `biased`, N = inf: the IQP training residual is ≤ 1e-10 on ≥ 4/5 seeds, and R < 1. | **Kill.** If it fails, the design or the code is wrong; stop. |
| P2 | `biased`, N = 10000: R < 1. | **Main result** of step 1 |
| P3 | `ising`, all N: the IQR of R lies entirely at or above 1. The IQP never "wins" on max-ent data. | **Kill.** If it fails, the metric favors the IQP; stop. |
| P4 | `random`, N = 10000: the median of \|log R\| is < log 2. | Exploratory. The scale is a guess and n = 12 is small. A failure is informative, not a stop. |
| P5 | `biased`, N = 10000: the median of the trained IQP's clifford_dist_median is ≥ 0.02 rad. | Report only |

Expected direction in N for `biased`: R increases toward 1 as N falls, because sampling noise
in the order-≤3 moments dominates both completions. If R does not depend monotonically on N,
report that; it is not a failure.
