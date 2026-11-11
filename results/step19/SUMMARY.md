Step 19 was designed after a 2-split pilot on one development run; the 7 tested runs were not used in the pilot; the gate is step 14's, unchanged; completion is scored on held-out shots with test noise removed; this is error-correction syndrome data, not IQP-circuit output.

Spec: `specs/step19_real_qec16.md`.

| ID | Statement | Counts | Verdict |
|---|---|---|---|
| V1 | gate losses <= 1 of 7 runs | picked 7, wins 2, losses 5 | **FAIL** |
| V2 | ungated R >= 1 on >= 6/7 | R ≥ 1 on 5/7 | **FAIL** |

Exploratory: median R = 2.87 [1.6, 3.51]; R_raw = 1.84 [1.26, 2.33]; order-4 validation flags G (val4 ratio >= 1) on 0/7.

| run | picks | R | R_raw | R4 | R5 | R6 | r_N | floor | val4 ratio | D3 |
|---|---|---|---|---|---|---|---|---|---|---|
| bZ_d3_r03_center_3_5 | True | 3.84 | 2.5 | 1.74 | 3.32 | 6.07 | 0.00037 | 0.0184 | 0.646 | 0.249 |
| bX_d3_r03_center_5_3 | True | 0.601 | 0.765 | 0.694 | 0.513 | 0.612 | 0.00023 | 0.0183 | 0.703 | 0.243 |
| bZ_d3_r03_center_5_3 | True | 2.87 | 1.84 | 1.58 | 3.03 | 4.68 | 0.00014 | 0.0184 | 0.828 | 0.25 |
| bX_d3_r03_center_5_7 | True | 4.24 | 2.18 | 2.17 | 4.19 | 5.55 | 0.00033 | 0.0178 | 0.598 | 0.233 |
| bZ_d3_r03_center_5_7 | True | 3.18 | 2.48 | 1.54 | 2.94 | 6.32 | 0.00025 | 0.0179 | 0.666 | 0.245 |
| bX_d3_r03_center_7_5 | True | 0.695 | 0.818 | 0.833 | 0.679 | 0.634 | 0.00023 | 0.0177 | 0.797 | 0.224 |
| bZ_d3_r03_center_7_5 | True | 2.5 | 1.71 | 1.48 | 2.4 | 3.54 | 0.00017 | 0.0178 | 0.815 | 0.226 |

## Verify (raw output)

```
ok   [spec] specs/step19_real_qec16.md committed and unchanged
ok   [closed] src/step1..18 unchanged since 97648b2
ok   [grid] 7 runs: split seed 100, N_train 3e4, N_test 2e4, 3 restarts, zip md5
ok   [summary] SUMMARY opens with the required sentence
ok   [summary] V1–V2 marked
ok   [tests] 3 passed in 0.62s
ALL CHECKS PASS (step 19)
```
