Step 20 was designed after step 19 and a 12-instance development pilot; the 18 tested instances (8 QEC d3_r05 runs, iqp4 seeds 310–319) were never fit before; the validation rows never enter a fit.

Spec: `specs/step20_heldout_val_gate.md`.

| ID | Statement | Counts | Verdict |
|---|---|---|---|
| W1 | new gate losses <= 1 of 18 | picks 8, losses 2 | **FAIL** |
| W2 | new gate has fewer losses than the step 14 gate | new 2 vs step 14 7 | **PASS** |
| W3 | new gate keeps >= 50% of the R < 1 instances | kept 6 of 9 | **PASS** |

Per family (exploratory):

| family | n | R < 1 | step 14 losses | new losses | wins kept |
|---|---|---|---|---|---|
| qec | 8 | 3 | 5 | 2 | 1 |
| iqp4 | 10 | 6 | 2 | 0 | 5 |

Pooled order-4–6 rule disagrees with the order-4 rule on 0/18.

| instance | R | R_raw | step 14 picks | new picks | d4 | d5 | d6 | excess |
|---|---|---|---|---|---|---|---|---|
| bX_d3_r05_center_3_5 | 0.722 | 0.806 | True | True | -2.12e-05 | -4.32e-05 | -5.14e-05 | -0.0224 |
| bZ_d3_r05_center_3_5 | 1.69 | 1.37 | True | False | +1.22e-05 | +5.14e-05 | +1.33e-04 | -0.0225 |
| bX_d3_r05_center_5_3 | 0.5 | 0.665 | True | False | +2.01e-05 | +5.23e-05 | +9.44e-05 | -0.0227 |
| bZ_d3_r05_center_5_3 | 3.4 | 1.85 | True | False | +1.34e-05 | +5.27e-05 | +1.24e-04 | -0.0228 |
| bX_d3_r05_center_5_7 | 8.14 | 3.2 | True | True | -3.05e-05 | -4.41e-05 | -1.22e-05 | -0.0216 |
| bZ_d3_r05_center_5_7 | 4.28 | 2.43 | True | False | +1.03e-05 | +3.67e-05 | +8.35e-05 | -0.0219 |
| bX_d3_r05_center_7_5 | 4.06 | 1.97 | True | True | -1.15e-05 | -2.72e-05 | -3.23e-05 | -0.022 |
| bZ_d3_r05_center_7_5 | 0.528 | 0.702 | True | False | +3.06e-05 | +9.29e-05 | +1.80e-04 | -0.0223 |
| iqp4 310 | 0.928 | — | True | True | -7.92e-07 | -1.21e-05 | -2.77e-05 | -0.00621 |
| iqp4 311 | 1.15 | — | False | False | +2.78e-05 | +1.88e-05 | +3.98e-06 | 0.0195 |
| iqp4 312 | 0.596 | — | True | True | -1.75e-05 | -4.02e-05 | -4.63e-05 | -0.00538 |
| iqp4 313 | 0.435 | — | True | True | -4.82e-05 | -1.36e-04 | -2.37e-04 | -0.00538 |
| iqp4 314 | 0.957 | — | False | False | +1.86e-05 | -7.83e-06 | -2.83e-05 | 0.0107 |
| iqp4 315 | 1.29 | — | False | False | +1.13e-04 | +1.18e-04 | +5.87e-05 | 0.0171 |
| iqp4 316 | 1.03 | — | True | False | +1.52e-05 | -2.75e-06 | +3.79e-07 | 0.00874 |
| iqp4 317 | 2.27 | — | True | False | +3.15e-05 | +5.14e-05 | +6.64e-05 | 0.00153 |
| iqp4 318 | 0.386 | — | True | True | -6.09e-05 | -1.93e-04 | -3.50e-04 | -0.00471 |
| iqp4 319 | 0.858 | — | True | True | -1.26e-05 | -3.86e-05 | -6.31e-05 | -0.00351 |

## Verify (raw output)

```
ok   [spec] specs/step20_heldout_val_gate.md committed and unchanged
ok   [closed] src/step1..19 and step20/core.py unchanged since 28509d8
ok   [grid] 18 instances with the frozen N, restarts, md5
ok   [summary] SUMMARY opens with the required sentence
ok   [summary] W1–W3 marked
ok   [tests] 4 passed in 0.70s
ALL CHECKS PASS (step 20)
```

Run note: the first launch of 18 parallel jobs crashed 9 instances at start-up with numpy ArrayMemoryError (before any fit; log tail in run1_log.txt). They were rerun unchanged with `--all`, which only runs missing instances. No instance was dropped.
