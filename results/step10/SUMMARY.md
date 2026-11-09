Step 10 was designed after step 9; it changes G's restart budget from 3 to 10 at n = 14 only; G is the generic IQP (no oracle); n ≤ 16 proxies are not hardness evidence.

# Step 10 summary: n = 14, level B, seeds 10–29, G with 10 restarts

## Frozen hypotheses (spec section 3)

| ID | Verdict | Numbers |
|---|---|---|
| K1 | **FAIL** | 11/20 seeds with R < 1 (need ≥ 15; step 9 with 3 restarts: 10/20) |
| K2 | **FAIL** | 7/20 seeds with best residual > 1e-2 (need ≤ 2; step 9: 8/20) |
| K3 | **FAIL** | 1/10 step-9 losers now R < 1 (need ≥ 6) |
| K4 | **PASS** | 0/10 step-9 winners now R ≥ 1 (need ≤ 1) |

## Per seed

| seed | step-9 result | R (3) | R (10) | residual (3) | residual (10) | best restart 3 → 10 |
|---|---|---|---|---|---|---|
| 10 | loss | 1.76 | 1.76 | 0.0131 | 0.0129 | 2 → 6 |
| 11 | loss | 1.63 | 1.63 | 0.0125 | 0.0125 | 0 → 0 |
| 12 | win | 0.52 | 0.381 | 0.00437 | 0.0017 | 0 → 4 |
| 13 | loss | 1.24 | 1.28 | 0.00303 | 0.00288 | 1 → 9 |
| 14 | loss | 1.47 | 1.49 | 0.0343 | 0.0328 | 2 → 8 |
| 15 | loss | 1.61 | 1.72 | 0.0175 | 0.0169 | 0 → 3 |
| 16 | loss | 1.13 | 1.13 | 0.00196 | 0.00196 | 0 → 0 |
| 17 | loss | 1.59 | 1.21 | 0.0126 | 0.0074 | 0 → 3 |
| 18 | win | 0.398 | 0.553 | 0.000835 | 0.000758 | 2 → 3 |
| 19 | loss | 1.63 | 1.73 | 0.014 | 0.0114 | 0 → 6 |
| 20 | win | 0.292 | 0.292 | 0.00215 | 0.00215 | 2 → 2 |
| 21 | win | 0.33 | 0.333 | 0.00189 | 0.00128 | 2 → 7 |
| 22 | win | 0.599 | 0.511 | 0.00343 | 0.00304 | 2 → 9 |
| 23 | win | 0.821 | 0.821 | 0.00441 | 0.00441 | 1 → 1 |
| 24 | loss | 1.18 | 0.819 | 0.00295 | 0.00292 | 1 → 3 |
| 25 | win | 0.766 | 0.565 | 0.00153 | 0.00147 | 2 → 3 |
| 26 | win | 0.705 | 0.525 | 0.00126 | 0.000324 | 1 → 4 |
| 27 | win | 0.402 | 0.335 | 0.00104 | 0.000901 | 1 → 4 |
| 28 | loss | 1.52 | 1.49 | 0.0359 | 0.0354 | 1 → 5 |
| 29 | win | 0.707 | 0.627 | 0.0214 | 0.0211 | 2 → 8 |

## Exploratory (not frozen)

- Median R: 3 restarts 0.976 [0.579, 1.54] → 10 restarts 0.82 [0.522, 1.49]. Median residual 0.0039 → 0.00298.
- The best restart changed from step 9's in 16/20 seeds.
- Within an instance, Spearman(residual, G_iqp) across the 10 restarts: median 0.685 [0.591, 0.821].
- The lowest-residual restart is also the lowest-G restart in 8/20 seeds.
- Oracle (pick the lowest-G restart, which uses the target, so it is not a valid method): 11/20 wins. This is an upper bound on any selection rule.
- Restarts 0–2 reproduce step 9: all match = True, max relative difference 0.0e+00.

## Timing

- 2026-11-09 23:41:07 start: 20 seeds, 16 workers x 1 thread, 10 restarts
- 2026-11-10 00:03:57 end: 22.8 min, failed []

## Acceptance check (`python -m src.step10.run --verify`, raw output)

```
ok   [spec] specs/step10_more_restarts.md committed and unchanged
ok   [closed] src/step1..9 unchanged since e55c4b6
ok   [grid] 20 seeds, exact σ, 10 restarts, restarts 0–2 reproduce step 9
ok   [summary] SUMMARY opens with the required sentence
ok   [summary] K1–K4 marked
ok   [figures] figures/step10/R_3_vs_10
ok   [tests] 2 passed in 0.59s
ALL CHECKS PASS (step 10)
exit 0
```

## Residual floor (exploratory, computed after the verdicts)

For the 7 seeds with best residual above 1e-2, all 10 restarts land within 1.18–1.57× of the
lowest residual, for example seed 28: 0.0354 lowest, 0.0378 median. Restarts from different inits
converge to about the same residual. This is a **floor**: the weight-≤3 IQP cannot match these
targets' order-≤3 moments. The cause is the model's capacity, not too little search.

Step 9's label for these seeds, "under-training", is therefore wrong. They are **moment misfits**.

The residual alone still does not decide the sign. Seed 29 has a residual of 0.021 and wins
(R = 0.63).
