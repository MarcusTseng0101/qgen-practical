Step 9 was designed after step 8; seeds 10–29 are fresh; G is the generic IQP (no oracle); n ≤ 16 proxies are not hardness evidence.

# Step 9 summary: fresh seeds 10–29 at level B (n = 14 σ = 0.213, n = 16 σ = 0.251)

## Frozen hypotheses (spec section 4)

| ID | Verdict | Numbers |
|---|---|---|
| H1 | **PASS** | n = 16: 16/20 seeds with R < 1 (need ≥ 15) |
| H2 | **FAIL** | n = 14: 10/20 seeds with R < 1 (need ≥ 15) |
| H3 | **FAIL** | n = 16 OLS log R = a + b·D3 + c·r4: b = -2.49 [-4.43, 0.00691], c = 1.49 [-0.328, 4.14] (95% bootstrap) |
| H4 | **FAIL** | c(16) − c(14) = 1.49 − 1.36 = 0.132 [-1.78, 2.23] |
| H5 | **PASS** | n = 16 median R 0.637 IQR [0.543, 0.889] |
| H6 | **PASS** | n = 16 median G residual 0.00266; residual ≤ 1e-2 in 16/20, wins among them 14 (need 12); H1 verdict unchanged: True |
| H7 | **FAIL** | step-8 n = 16 model out of sample: Spearman ρ = 0.353 (need ≥ 0.5) |

## Reproduction instance (n = 16, B, seed 0; 16 workers × 1 thread, amendment 1)

R = 0.3912465385517786 vs step 7 0.39361873837543654, relative difference 6.03e-03 → FAIL: every n = 16 R is flagged

## Per-seed results

| seed | R n=14 | res n=14 | R n=16 | res n=16 | G_iqp 16 | G_maxent3 16 | D3 16 | r4 | coll 16 |
|---|---|---|---|---|---|---|---|---|---|
| 10 | 1.76 | 0.0131 | 1.04 | 0.0037 | 9.51e-05 | 9.19e-05 | 0.201 | 0.278 | 454 |
| 11 | 1.63 | 0.0125 | 0.663 | 0.00296 | 0.000103 | 0.000155 | 0.339 | 0.304 | 669 |
| 12 | 0.52 | 0.00437 | 0.436 | 0.00334 | 8.14e-05 | 0.000187 | 0.403 | 0.41 | 154 |
| 13 | 1.24 | 0.00303 | 0.553 | 0.00588 | 7.96e-05 | 0.000144 | 0.286 | 0.368 | 299 |
| 14 | 1.47 | 0.0343 | 1.36 | 0.033 | 0.000237 | 0.000174 | 0.334 | 0.39 | 282 |
| 15 | 1.61 | 0.0175 | 1 | 0.00863 | 0.000131 | 0.000131 | 0.219 | 0.281 | 1.62e+03 |
| 16 | 1.13 | 0.00196 | 0.605 | 0.000372 | 6.7e-05 | 0.000111 | 0.235 | 0.268 | 426 |
| 17 | 1.59 | 0.0126 | 2.9 | 0.0113 | 0.000194 | 6.69e-05 | 0.133 | 0.479 | 514 |
| 18 | 0.398 | 0.000835 | 0.761 | 0.00226 | 0.000121 | 0.000159 | 0.38 | 0.273 | 92.8 |
| 19 | 1.63 | 0.014 | 0.74 | 0.00236 | 9.93e-05 | 0.000134 | 0.235 | 0.411 | 490 |
| 20 | 0.292 | 0.00215 | 0.879 | 0.018 | 0.000135 | 0.000153 | 0.337 | 0.397 | 270 |
| 21 | 0.33 | 0.00189 | 0.282 | 0.000466 | 0.000107 | 0.00038 | 0.655 | 0.314 | 273 |
| 22 | 0.599 | 0.00343 | 0.514 | 0.00763 | 0.000133 | 0.000259 | 0.366 | 0.44 | 317 |
| 23 | 0.821 | 0.00441 | 0.611 | 0.000657 | 7.49e-05 | 0.000123 | 0.176 | 0.206 | 855 |
| 24 | 1.18 | 0.00295 | 0.397 | 0.0023 | 6.19e-05 | 0.000156 | 0.3 | 0.349 | 500 |
| 25 | 0.766 | 0.00153 | 0.321 | 0.00218 | 6.98e-05 | 0.000217 | 0.451 | 0.262 | 321 |
| 26 | 0.705 | 0.00126 | 0.919 | 0.000258 | 8.87e-05 | 9.65e-05 | 0.358 | 0.346 | 46 |
| 27 | 0.402 | 0.00104 | 0.601 | 0.000766 | 4.86e-05 | 8.08e-05 | 0.201 | 0.159 | 917 |
| 28 | 1.52 | 0.0359 | 0.855 | 0.0228 | 0.000293 | 0.000343 | 0.528 | 0.471 | 249 |
| 29 | 0.707 | 0.0214 | 0.582 | 0.000123 | 0.000149 | 0.000256 | 0.327 | 0.653 | 236 |

## Exploratory (not frozen)

- n = 14 median R 0.976 IQR [0.579, 1.54], median residual 0.0039.
- In-sample fit on the fresh seeds: n = 16 R² = 0.396; n = 14 a, b, c = 0.391, -4.05, 1.36, R² = 0.435.
- Step-8 n = 14 model out of sample: Spearman ρ = 0.436.
- n = 16 Spearman of log R with D3 -0.424, r4 0.128, r4_23 0.108.
- Paired by seed: win at both n 10, win 14 / lose 16 0, lose 14 / win 16 6.

## Timing

- 2026-11-09 11:34:07 start: 41 jobs, 16 workers x 1 threads, stop-loss 6.0 h
- 2026-11-09 12:52:53 end: 1.31 h, failed []

## Acceptance check (`python -m src.step9.run --verify`, raw output)

```
ok   [spec] specs/step9_fresh_seeds.md committed
ok   [spec] spec unchanged since commit
ok   [closed] src/step1..7 unchanged since 72d47b1
ok   [grid] 40 instances, exact n / σ / level B / seed, ≥ 3 restarts
FAIL [repro] n = 16 B seed 0 reproduces step 7 R: 6.03e-03
ok   [summary] SUMMARY opens with the required sentence
ok   [summary] SUMMARY marks H1–H7 PASS/FAIL
ok   [artifacts] results/step9/table.csv
ok   [artifacts] results/step9/verdicts.json
ok   [figures] figures/step9/*
ok   [tests] 3 passed in 70.52s (0:01:10)
FAILED: ['repro']
exit 1
```

**The check FAILS on one item: the reproduction instance.**
- Under amendment 1 (1 BLAS thread), n = 16, B, seed 0 gives R = 0.39125, against step 7's
  0.39362. The relative difference is 6.0e-3, against a tolerance of 1e-6.
- Under spec section 5, **every n = 16 R is flagged** as carrying numerical drift of this order.
- The check was not loosened.

**How much the flag matters for H1:**
- 16 of 20 n = 16 seeds have R < 1 − 0.006, so a drift of the observed size changes no sign.
- 15 of 20 have R < 0.9. H1's threshold still holds even under the 10% restart-selection
  sensitivity found in amendment 1.
- The seeds within 10% of 1 are seed 10 (1.036), seed 15 (1.004) and seed 26 (0.919).

**n = 14 (exploratory):**
- G residual is above 1e-2 in 8 of 20 seeds, and 7 of those 8 lose (R = 1.47–1.76).
- Among the 12 seeds with residual ≤ 1e-2, 9 win, which is ⌈0.75·12⌉ = 9.
- The fresh n = 14 targets are more peaked than the level they were matched to: median collision
  ratio 479 against 284.
- No G restart hit maxiter. All stopped on the relative-reduction criterion, so these are poor
  local minima, not truncated runs.
