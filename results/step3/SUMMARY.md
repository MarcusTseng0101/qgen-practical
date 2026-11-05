# Step 3: completion ratio R vs σ, summary

Step 3 was designed after the step 1–2 diagnostics; C1 replicates data already seen; oracle-support fits are a landscape diagnostic; n = 12 proxies are not hardness evidence.

Spec: `specs/step3_completion_vs_sigma.md` (frozen at ab2ecab). Branch `step3-ratio`, 2026-11-06.
60 instances (2 targets × 6 σ × 5 seeds), n = 12, N = ∞. Produced by
`python -m src.step3.run --all` (118 min wall clock) and `python -m src.step3.run --report`.
Per-instance data: `results/step3/<target>/sigma_<σ>/seed_<s>/metrics.json`; flat table
`table.csv`; all statistics `verdicts.json`; figures `figures/step3/*.{png,pdf}`.

## Deviations and caveats (read first)

- **Budget cut 1 applied: fit G used only 3 restarts** (the first 3 of the 10 init draws),
  not the spec's 10. This was the user's decision after the projection. Fit O and MaxEnt(3) are
  unchanged (O 10 restarts). Effect seen on one instance: iqp σ = 0.05 seed 0, the best G
  training residual is 5.3e-7 with 3 restarts vs 1.4e-7 with 10 (the best of the 10 was
  restart index 3). So G's misfit, and with it R_G, is biased upward relative to the spec.
- **K1 and K2 pass by construction; they check code correctness, not anything informative.**
  At N = ∞ with identical inputs on the pair, the truth of `maxent_proj` IS MaxEnt(3) of the
  shared moments. So G_maxent on `maxent_proj` is numerical zero (1e-19 to 1e-12 here), and R
  = G_iqp / G_maxent is a ratio over a ~0 denominator (1e5 to 1e15). Any IQP fit that does not
  reproduce MaxEnt(3) exactly gives R ≫ 1. K1 and K2 are marked PASS as observed, but they are
  only a check that the pipeline is wired correctly (the pair shares inputs, MaxEnt(3) is
  fitted correctly). They are not an informative kill test of the pipeline favoring the IQP.
- K2's condition is applied per instance (my reading, a choice): a `maxent_proj` seed counts at
  σ when its G-fit training residual ≤ G_maxent of the paired `iqp` instance (same σ, seed).
  The two numbers are differently normalized (sum of squared moment errors over 298 parities
  vs mean squared error over orders 4–6), as frozen in the spec.
- Statistics are median and IQR (numpy linear percentiles) over 5 seeds. "R < 1" means the
  IQR lies entirely below 1, "R ≥ 1" entirely at or above 1, otherwise "undecided".

## Hypotheses

| ID | Verdict | Numbers |
|---|---|---|
| K1 | K1: PASS (by construction; see caveat) | `maxent_proj`, O: R IQR ≥ 1 at every σ; medians 3.3e5, 4.8e8, 1.6e12, 4.2e13, 4.8e14, 1.8e15 for σ = 0.05 … 0.6 |
| K2 | K2: PASS (by construction; see caveat) | `maxent_proj`, G: qualifying seeds σ=0.05: {1,4}, 0.1: {0,1,4}, 0.2: all 5, 0.3: {3}, 0.4: {3}, 0.6: none (unconstrained). R ≥ 1 on all of them (min 1.8e5) |
| C1 | C1: PASS (replication of step 2, not a prediction) | `iqp`, O, σ = 0.05: median R_O = 0.42, IQR [0.39, 0.59] (per seed 0.090, 0.59, 0.39, 1.04, 0.42; seed 3 alone is above 1); O residual 1.1e-6 … 9.1e-6 |
| M1 | M1: FAIL | `iqp` median R_O by σ: 0.42, 0.60, 0.048, 4.2e-15, 2.5e-15, 8.6e-15. 3 decreases (allowed ≤ 1). R_O falls with σ because O recovers the target exactly at σ ≥ 0.3 |
| M2 | M2: FAIL | median R_G < median R_O at σ = 0.05 (0.15 vs 0.42) and σ = 0.1 (0.18 vs 0.60). Holds at σ ≥ 0.2 |
| M3 | M3: FAIL | W = {0.1, 0.2, 0.3, 0.4}; expected W ⊆ {0.1} |

## Per σ (iqp target; median [IQR])

| σ | D3 | R_O | O residual | O exact (≤1e-10) | R_G | G residual | G_maxent | G_uniform (seed 0) |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 5.0e-3 [4.6e-3, 7.7e-3] | 0.42 [0.39, 0.59] (<1) | 4.4e-6 | 0/5 | 0.15 [0.14, 0.32] (<1) | 2.0e-7 | 1.1e-7 | 0.82 |
| 0.1 | 4.6e-2 [4.5e-2, 6.8e-2] | 0.60 [0.11, 0.65] (<1) | 8.3e-4 | 0/5 | 0.18 [0.064, 0.24] (<1) | 1.8e-5 | 1.6e-5 | 0.46 |
| 0.2 | 0.19 [0.19, 0.23] | 0.048 [0.041, 0.072] (<1) | 2.6e-3 | 0/5 | 0.18 [0.12, 0.22] (<1) | 1.5e-4 | 5.7e-4 | 0.047 |
| 0.3 | 0.27 [0.26, 0.27] | 4.2e-15 [2.4e-15, 7.7e-15] (<1) | 3.3e-16 | 4/5 | 1.41 [1.33, 1.54] (≥1) | 1.3e-3 | 4.2e-4 | 2.0e-3 |
| 0.4 | 0.30 [0.29, 0.30] | 2.5e-15 [1.3e-15, 5.0e-15] (<1) | 1.0e-16 | 5/5 | 1.82 [1.75, 1.89] (≥1) | 2.3e-3 | 3.3e-4 | 4.5e-4 |
| 0.6 | 0.31 [0.29, 0.32] | 8.6e-15 [4.0e-15, 1.38] (undecided) | 3.0e-16 | 3/5 | 2.17 [2.13, 2.25] (≥1) | 8.8e-4 | 2.3e-4 | 2.6e-4 |

## Main result (M3) and what drives it

- **W = {0.1, 0.2, 0.3, 0.4}**, by the frozen definition (`iqp` R_O IQR below 1 and median
  D3 ≥ 1e-2). M3 expected W ⊆ {0.1}; it FAILS.
- At σ = 0.3 and 0.4, W membership comes from **exact recovery by the oracle O** (residual
  ~1e-16, R ~1e-15 on 4/5 and 5/5 seeds). O is given the target's own 38-generator layout, so
  this is a landscape statement: on the right support, L-BFGS-B finds the true angles at
  σ ≥ 0.3 (and gets stuck in wrong-sign basins at σ ≤ 0.2, as in step 2). It is not a
  statement about a method that does not know the layout.
- The non-oracle fit G gives a different picture (not a frozen hypothesis, reported for
  context): R_G < 1 at σ = 0.05, 0.1, 0.2, and R_G ≥ 1 at σ = 0.3, 0.4, 0.6. So for G, the
  set {σ : R_G < 1 and D3 ≥ 1e-2} is {0.1, 0.2}. At σ ≥ 0.3 G fails to train (residual 1e-3,
  about 3–7× G_maxent), the FM2 failure of step 1.
- The 1e-2 threshold matters only at σ = 0.05 (D3 = 5.0e-3, below it); every σ ≥ 0.1 has
  D3 ≥ 4.5e-2. See `room_and_proxies`.

## Residual vs G (figure `residual_vs_G`)

**The misfit–G correlation breaks down for fit G at large σ.** corr(log residual, log G_iqp)
over all restarts of the `iqp` targets:

| σ | 0.05 | 0.1 | 0.2 | 0.3 | 0.4 | 0.6 |
|---|---|---|---|---|---|---|
| fit O | 0.96 | 0.97 | 0.97 | 1.00 | 1.00 | 1.00 |
| fit G | 0.96 | 0.94 | 0.75 | 0.04 | −0.45 | −0.29 |

So the "misfit is conservative" argument (spec, Changes from step 2) holds for O at every σ
and for G at σ ≤ 0.2, but **not for G at σ ≥ 0.3**: there G_iqp sits in 4.5e-4 … 7.8e-4 regardless of
the training residual (G has 3 restarts per instance there, 15 points per σ). R_G at
σ ≥ 0.3 should not be read through that argument. In that regime R_G ≥ 1 anyway.

## Proxies (figure `room_and_proxies`)

As σ grows, D3 rises from 5e-3 to 0.31, the collision ratio falls from ~3300 to ~2.3, and the
Clifford-distance median rises from 0.03 to 0.20. hi_order_frac of `iqp` stays 0.5–0.9 while
that of `maxent_proj` drops to 0.07 at σ = 0.6.

## Timing

Projection (spec basis, σ = 0.4 pair × 60) 1.53 h with 10 G restarts; after the cut, 0.73 h
(spec basis) or 1.38 h (with the measured σ = 0.05 time), both linear guesses. Actual: 118
min, longer than either; σ = 0.05 and 0.1 instances dominate.
