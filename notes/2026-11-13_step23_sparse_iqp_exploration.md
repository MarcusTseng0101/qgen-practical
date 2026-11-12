# Step 23 exploration: a sparse IQP could amplify the iqp4 advantage, but generator selection fails

**Status:** exploration only.
- Seeds were 300–303, which were already spent, so none of this is a test.
- There is no spec, and nothing was pre-registered.
- Scripts and raw outputs are on branch `step18-adversarial`, commit 79d84ed, `explore/step23/`.

## Question

Can a variant designed from the step 14 bottlenecks keep the IQP's advantage at finite N?

- On iqp4, the median R of the generic IQP rises from 0.66 at N = ∞ to 0.99 at N = 1e4.
- **B1, noise absorption:** the model has 696 parameters for 696 moments.
- **B2, misspecification:** the target has weight-4 generators that the model lacks.

## Results (N = 1e4 unless stated; R = G_iqp / G_maxent3)

| Model | Seeds 300, 301, 302, 303 | Note |
|---|---|---|
| Generic IQP, 696 generators (step 14) | median ≈ 0.99 | reference |
| Existing NNLS sparse selector, K = 60, weight ≤ 3 | 19.1, 6.95, 4.46, 3.64 | N = 1e5 gives 24.1, 7.86, 4.66, 5.27 |
| Oracle support, 42 true weight-≤3 generators | 7.94, 7.91, 1.04, 8.47 | weight-4 generators omitted |
| **Oracle support, all 48 true generators** | **0.34, 0.19, 0.27, 0.21** | ceiling |
| L1-IQP v1 (weight ≤ 4, λ 1e-4 to 1e-2, validation choice) | 0.48, 0.63, 1.67, 0.93 | best λ in grid: 0.48, 0.43, 1.40, 0.61 |
| L1-IQP v2 (λ 1e-3 to 0.3, warm start downward) | validation choice 0.49, 0.42, 2.58, 2.41; discrepancy choice 2.04, 1.92, 2.58, 2.91 | path-dependent |

Notes on the rows:
- **NNLS sparse selector:** its training residual is 0.2–0.7, against a noise level of about 0.07. The small-angle linearisation picks the wrong generators at σ = 0.25.
- **Oracle, all 48 generators:** its training residual is 0.03–0.05, which is at the noise level. With the right support the IQP's error is 1/3 to 1/5 of MaxEnt's at N = 1e4.
- **L1-IQP v1:** it keeps 116–394 generators, against 48 true ones.
  - The validation split has 2,000 shots, so validation losses differ by about 1%. That is below their noise, so λ is effectively chosen at random.
- **L1-IQP v2:** at the same λ it reaches different solutions from v1. For example, seed 303 at λ = 1e-3 gives 2.41 here and 0.61 in v1.
  - Strong penalties pick mostly wrong weight-4 generators.
  - The discrepancy principle (choose the strongest λ whose residual is at the noise level) picks λ ≈ 1e-2 and loses.

## What this means

1. **The ceiling is real and large.** A sparse IQP with the right support, including weight-4 generators, has R ≈ 0.2–0.34 at N = 1e4. The generic IQP has 0.99. So B1 and B2 are the right diagnosis.
2. **Weight-4 candidates are necessary.** Without them, a sparse model cannot compensate (oracle weight-≤3: R ≈ 8).
3. **Selection is the open problem.** Neither L1-IQP version is stable.
   - The IQP loss is nonconvex in θ, so the L1 path depends on the initialisation.
   - The validation split is too noisy to choose λ.
   - The discrepancy principle chooses too sparse a model.
   - No variant here can go into a pre-registered test: on these seeds 1 of 4 (v1) and 2 of 4 (v2) lose to the generic IQP.

## Decision

- No step 23 spec yet. The pre-stated rule was to write one only if a selection method gave R < 1 on 4/4 dev seeds with a median clearly below 0.78. Neither run met it.
- **For the paper (discussion section):**
  - The oracle-support ceiling shows the finite-N loss is a model-selection problem, not a limit of the IQP.
  - Weight-4 generators matter.
  - Selection under strong interference is left open.
- **Possible follow-ups (not started):**
  - greedy forward selection with a full nonlinear refit at each step;
  - multiple restarts along the L1 path;
  - λ chosen by K-fold cross-validation instead of one 20% split.

  Each would need new dev seeds before any test, because 300–303 have now been used for tuning.
