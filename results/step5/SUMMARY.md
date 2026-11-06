# Step 5: where does the iqp4 advantage reverse, and why? Summary

Step 5 was designed after step 4; Q0 replicates data already seen; G is the generic IQP (no oracle); n = 12 proxies are not hardness evidence.

Spec: `specs/step5_iqp4_sigma_scan.md` (frozen at 53d28cf), amended by
`specs/step5_amendment1.md` (Q5's undefined-σ\* cases, approved before the grid). Branch
`step5-sigma`, 2026-11-07. 120/120 instances (2 targets × 6 σ × 2 N × 5 seeds), n = 12, no cut.
Produced by the grid run of `src/step5/run.py` (13.7 min wall clock; projection 0.19 h) and
`python -m src.step5.run --report`. Per-instance data
`results/step5/<iqp4|iqp4f>/sigma_<σ>/N_<inf|10000>/seed_<s>/metrics.json`; `table.csv`;
`verdicts.json` (σ\* and sign changes per target × N); figures `figures/step5/R_vs_sigma`,
`G_vs_sigma`.

## Read first

- **G uses 3 restarts** (as in steps 3–4; never fewer). R = G_iqp / G_maxent3 at G's
  lowest-training-residual restart. "G residual" below is G's order-≤3 training residual (a sum
  over 298 moments) at that restart.
- Statistics: median and IQR over 5 seeds; "R < 1" = IQR entirely below 1, "R ≥ 1" = entirely
  at or above 1, else "undecided".
- **Reproduction:** `iqp4` at σ = 0.1 and 0.2, N = ∞, reproduces step 4's R for all 5 seeds
  (checked by `check.sh --stage 15`, relative difference ≤ 1e-6; seed 0 at σ = 0.2 is
  bit-identical). The σ = 0.2 row of `iqp4f` equals `iqp4` exactly (identity tested).
- **MaxEnt maxiter (step 4 FM-N1): 0 of 120 instances** hit the 20000-iteration limit; MaxEnt's
  largest training residual over the grid is 6.6e-13.

## Hypotheses

| ID | Verdict | Numbers (N = ∞ unless stated) |
|---|---|---|
| Q0 | Q0: PASS (replication, data already seen) | `iqp4` σ = 0.1: R = 7.93 [5.50, 8.92] ≥ 1 (G residual 7.5e-3); σ = 0.2: R = 0.577 [0.450, 0.579] < 1 (G residual 2.1e-3) |
| Q1 | Q1: PASS (prediction) | σ\*(iqp4, ∞) = **0.160**, exactly 1 sign change over the grid, inside [0.15, 0.20). Crossing between σ = 0.15 (median R 1.35, G residual 8.7e-3) and 0.175 (0.670, 4.5e-3). The power law predicted ≈ 0.17. |
| Q2 | Q2: PASS (prediction; 0.1 and 0.2 seen) | Median G_iqp max/min over the 6 σ = **2.30** (≤ 3): 2.6e-4 … 6.0e-4. Median G_maxent3 at σ = 0.25 / at σ = 0.1 = 7.16e-4 / 3.33e-5 = **21.5** (≥ 10). |
| Q3 | Q3: FAIL (prediction) | `iqp4` σ = 0.25: R = **0.891 [0.836, 1.14]**, undecided (IQR straddles 1); G residual 1.0e-3 [7.5e-4, 1.5e-3]. Per seed R (G residual): 0.89 (1.5e-3), 1.47 (5.4e-4), 1.14 (7.5e-4), 0.77 (1.0e-3), 0.84 (2.0e-3). **FM2 not observed at σ = 0.25:** no residual ≫ 1e-2 (largest restart residual 3.2e-3 at N = ∞, 6.4e-3 at N = 1e4); the restart spread per seed is at most ~4×. R rises from 0.577 at σ = 0.2 because G_iqp rises (4.1e-4 → 6.0e-4) while G_maxent3 flattens (7.3e-4 → 7.2e-4). |
| Q4 | Q4: PASS (prediction, **low confidence** as stated in the spec) | median R(iqp4f) ≥ median R(iqp4) at all four σ: 0.1: 19.8 vs 7.93; 0.125: 4.63 vs 2.82; 0.15: 1.41 vs 1.35; 0.175: 0.709 vs 0.670. G residuals iqp4f vs iqp4: 0.114 vs 7.5e-3; 5.7e-2 vs 1.0e-2; 2.3e-2 vs 8.7e-3; 6.0e-3 vs 4.5e-3. The margins at 0.15 and 0.175 are small (5%, 6%) and within the IQRs. |
| Q5 | Q5: FAIL (prediction; rule: spec section 3, with `specs/step5_amendment1.md`) | Both crossings defined, so neither amendment-1 case applies; the spec's comparison decides. σ\*(iqp4, N = 1e4) = **0.151** < σ\*(iqp4, N = ∞) = 0.160. At N = 1e4 the median R crosses 1 between σ = 0.15 (1.02) and 0.175 (0.709), and has **2 sign changes** (it returns to 1.02 at σ = 0.25). |

## Every cell: median R [IQR] (G residual, median)

| σ | iqp4, N = ∞ | iqp4, N = 1e4 | iqp4f, N = ∞ | iqp4f, N = 1e4 |
|---|---|---|---|---|
| 0.1 | 7.93 [5.50, 8.92] ≥1 (7.5e-3) | 4.95 [3.13, 7.33] ≥1 (9.0e-3) | 19.8 [12.8, 26.3] ≥1 (1.1e-1) | 12.7 [10.3, 17.8] ≥1 (1.2e-1) |
| 0.125 | 2.82 [1.88, 3.23] ≥1 (1.0e-2) | 1.56 [1.36, 3.43] ≥1 (1.1e-2) | 4.63 [3.74, 7.90] ≥1 (5.7e-2) | 3.09 [2.95, 4.52] ≥1 (6.0e-2) |
| 0.15 | 1.35 [0.888, 1.39] undecided (8.7e-3) | 1.02 [0.743, 1.06] undecided (1.1e-2) | 1.41 [1.33, 1.99] ≥1 (2.3e-2) | 1.43 [1.27, 1.48] ≥1 (2.4e-2) |
| 0.175 | 0.670 [0.467, 0.719] <1 (4.5e-3) | 0.709 [0.508, 0.754] <1 (6.5e-3) | 0.709 [0.555, 0.725] <1 (6.0e-3) | 0.794 [0.604, 1.05] undecided (8.4e-3) |
| 0.2 | 0.577 [0.450, 0.579] <1 (2.1e-3) | 0.656 [0.446, 0.828] <1 (3.0e-3) | 0.577 [0.450, 0.579] <1 (2.1e-3) | 0.656 [0.446, 0.828] <1 (3.0e-3) |
| 0.25 | 0.891 [0.836, 1.14] undecided (1.0e-3) | 1.02 [0.715, 1.40] undecided (2.3e-3) | 0.923 [0.717, 1.07] undecided (1.4e-3) | 0.840 [0.680, 1.36] undecided (1.9e-3) |
| σ\* | 0.160 (1 sign change) | 0.151 (2 sign changes) | 0.162 (1) | 0.165 (1) |

## Exploratory (not hypotheses; no new hypotheses were added)

- **R is not monotone in σ.** For both targets and both N, median R is lowest at σ = 0.2 and
  rises again at σ = 0.25 (to 0.84–1.02, all undecided). The advantage window seen here is
  narrow: on iqp4, R < 1 (IQR) only at σ = 0.175–0.2.
- **Floor versus room (figure `G_vs_sigma`).** On `iqp4`, G_iqp stays within ×2.3 while
  G_maxent3 grows ×21.5, as Q2 predicted; the crossing comes from the room growing. The
  measured slope is shallower than the guessed k = 3.8 at the top of the grid: G_maxent3 is flat
  from 0.2 to 0.25 (7.3e-4, 7.2e-4).
- **iqp4f's larger fixed floor shows up in training, not just in R.** With the weight-4 part
  held at 0.2·z′, G's residual at small σ is 15× (σ = 0.1) and 5.5× (σ = 0.125) larger than on
  `iqp4`, and G_iqp is 2.3e-3 vs 2.6e-4 at σ = 0.1. Its room (G_maxent3) is also larger
  (9.7e-5 vs 3.3e-5 at σ = 0.1), which is the low-confidence caveat in Q4; the net R is higher.
  Despite this, σ\*(iqp4f) ≈ σ\*(iqp4) (0.162 vs 0.160).
- **Finite N = 1e4** lowers R at small σ (iqp4 σ = 0.1: 7.93 → 4.95) and raises it slightly at
  σ ≥ 0.175, which moves σ\* down (Q5).

## Timing

Projection 0.19 h; actual 13.7 min wall clock.
