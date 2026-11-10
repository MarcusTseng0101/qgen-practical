Step 17 was designed after a 2-split pilot; split seeds 100–119 are fresh; the 20 splits share one dataset (MNIST reduced to 16 bits) and are not independent instances; the gate is step 14's, unchanged; completion is scored on held-out rows with test noise removed.

Spec: `specs/step17_real_mnist16.md`.

| ID | Statement | Counts | Verdict |
|---|---|---|---|
| U1 | gate picks IQP on <= 2/20 splits and <= 2 losses | picked 0, wins 0, losses 0 | **PASS** |
| U2 | ungated R >= 1 on >= 15/20 | R ≥ 1 on 20/20 | **PASS** |

## Exploratory (median [IQR] over 20 splits)

| quantity | value |
|---|---|
| R | 4.35 [4.14, 4.58] |
| R_min | 3.856894893645085 |
| G_iqp | 0.00095 [0.000898, 0.001] |
| G_maxent | 0.000221 [0.000212, 0.000226] |
| r_N | 0.752 [0.672, 0.815] |
| floor | 0.0229 [0.0229, 0.0229] |
| excess | 0.729 [0.649, 0.792] |
| D3 | 0.573 [0.57, 0.577] |
| minutes | 8.322241153319677 |
| R at level 4 | 4.42 [4.21, 4.68] |
| R at level 5 | 4.94 [4.62, 5.06] |
| R at level 6 | 3.75 [3.6, 3.92] |

## --verify (raw)

```
ok   [spec] specs/step17_real_mnist16.md committed and unchanged
ok   [closed] src/step1..16 unchanged since 5317a9d
ok   [grid] 20 splits: N_train 3e4, N_test 4e4, 3 restarts, pinned SHA-256
ok   [summary] SUMMARY opens with the required sentence
ok   [summary] U1–U2 marked
ok   [tests] 4 passed in 1.13s
ALL CHECKS PASS (step 17)
```
