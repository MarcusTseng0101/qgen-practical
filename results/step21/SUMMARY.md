Step 21 is a diagnostic on 16 spent QEC runs; it adds no claim; models are step 20's procedure, unchanged.

Spec: `specs/step21_qec_resolvability.md`.

Reproduction of step 20's R at split 100: max relative error 0.0e+00.

| ID | Quantity | Value | Pre-declared reading |
|---|---|---|---|
| D1 | unresolved runs at split 100 | 9/16 | ≥ 8: QEC cannot test the claim at 5e4 shots |
| D2 | ΔG sign agreement, split 100 vs 101 | 8/16 | ≤ 11: outcome depends on the split |
| D3 | Δv₄ sign matches ΔG among resolved (run, split) | 10/12 | reported as is |

Class counts: split 100 {'win': 0, 'loss': 7, 'unresolved': 9}; split 101 {'win': 0, 'loss': 5, 'unresolved': 11}.
Resolved loss in both splits: bZ_d3_r03_center_3_5, bZ_d3_r03_center_5_7, bX_d3_r05_center_5_7.
Resolved win in both splits: none.

| run | R (100) | ΔG CI (100) | class | R (101) | ΔG CI (101) | class | Δv₄ CI (100) |
|---|---|---|---|---|---|---|---|
| bX_d3_r03_center_3_5 | 0.688 | -2.8e-05 [-1.0e-04, +4.5e-05] | unresolved | 3.37 | +6.7e-05 [-5.6e-06, +1.4e-04] | unresolved | -2.8e-05 [-7.3e-05, +1.5e-05] |
| bZ_d3_r03_center_3_5 | 3.97 | +1.5e-04 [+7.2e-05, +2.2e-04] | loss | 4.16 | +1.2e-04 [+4.9e-05, +1.9e-04] | loss | +5.6e-06 [-4.2e-05, +5.2e-05] |
| bX_d3_r03_center_5_3 | 0.621 | -2.9e-05 [-1.1e-04, +5.0e-05] | unresolved | 2.77 | +5.6e-05 [-1.9e-05, +1.4e-04] | unresolved | +5.5e-06 [-3.8e-05, +5.2e-05] |
| bZ_d3_r03_center_5_3 | 3.63 | +9.7e-05 [+3.6e-05, +1.6e-04] | loss | 1.57 | +2.3e-05 [-3.2e-05, +7.4e-05] | unresolved | +2.2e-05 [-1.8e-05, +5.8e-05] |
| bX_d3_r03_center_5_7 | 4.36 | +1.1e-04 [+2.7e-06, +2.0e-04] | loss | 0.528 | -5.9e-05 [-1.4e-04, +1.5e-05] | unresolved | +2.6e-05 [-3.1e-05, +8.5e-05] |
| bZ_d3_r03_center_5_7 | 3.17 | +2.5e-04 [+1.7e-04, +3.4e-04] | loss | 6.3 | +9.2e-05 [+7.7e-06, +1.8e-04] | loss | +3.8e-05 [-1.3e-05, +9.4e-05] |
| bX_d3_r03_center_7_5 | 0.897 | -6.1e-06 [-7.1e-05, +5.5e-05] | unresolved | 2.24 | +4.1e-05 [-3.1e-05, +1.0e-04] | unresolved | +1.6e-05 [-2.2e-05, +5.3e-05] |
| bZ_d3_r03_center_7_5 | 3.17 | +1.1e-04 [+3.5e-05, +1.8e-04] | loss | 2.34 | +4.0e-05 [-4.5e-05, +1.2e-04] | unresolved | +4.1e-05 [-4.6e-06, +8.7e-05] |
| bX_d3_r05_center_3_5 | 0.722 | -2.9e-05 [-1.2e-04, +5.8e-05] | unresolved | 1.94 | +2.2e-05 [-4.1e-05, +8.6e-05] | unresolved | -2.1e-05 [-7.5e-05, +3.6e-05] |
| bZ_d3_r05_center_3_5 | 1.69 | +3.6e-05 [-4.8e-05, +1.1e-04] | unresolved | 8.84 | +1.1e-04 [+1.8e-05, +1.9e-04] | loss | +1.2e-05 [-3.7e-05, +6.3e-05] |
| bX_d3_r05_center_5_3 | 0.5 | -4.6e-05 [-1.0e-04, +9.8e-06] | unresolved | 3.7 | +7.0e-05 [-6.2e-07, +1.3e-04] | unresolved | +2.0e-05 [-1.9e-05, +5.8e-05] |
| bZ_d3_r05_center_5_3 | 3.4 | +6.1e-05 [-2.3e-05, +1.4e-04] | unresolved | 0.721 | -2.2e-05 [-9.4e-05, +4.2e-05] | unresolved | +1.3e-05 [-4.1e-05, +6.8e-05] |
| bX_d3_r05_center_5_7 | 8.14 | +1.4e-04 [+3.3e-05, +2.3e-04] | loss | 4.64 | +2.6e-04 [+1.5e-04, +3.6e-04] | loss | -3.0e-05 [-8.3e-05, +2.3e-05] |
| bZ_d3_r05_center_5_7 | 4.28 | +1.1e-04 [+3.2e-05, +1.9e-04] | loss | 2.98 | +5.6e-05 [-2.3e-05, +1.4e-04] | unresolved | +1.0e-05 [-3.7e-05, +6.1e-05] |
| bX_d3_r05_center_7_5 | 4.06 | +6.4e-05 [-2.8e-06, +1.3e-04] | unresolved | 4.03 | +8.7e-05 [+1.0e-05, +1.6e-04] | loss | -1.1e-05 [-5.5e-05, +3.2e-05] |
| bZ_d3_r05_center_7_5 | 0.528 | -3.6e-05 [-9.3e-05, +1.6e-05] | unresolved | 2.02 | +2.9e-05 [-2.9e-05, +9.6e-05] | unresolved | +3.1e-05 [-5.0e-06, +6.5e-05] |

## Verify (raw output)

```
ok   [spec] specs/step21_qec_resolvability.md committed and unchanged
ok   [closed] src/step1..20 unchanged since 33712d6
ok   [grid] 32 files with B = 400
ok   [repro] split 100 reproduces step 20's R (< 1e-6 relative)
ok   [summary] sentence and D1–D3 present
ok   [tests] 3 passed in 0.81s
ALL CHECKS PASS (step 21)
```

Run note: the 4 h stop-loss fired at 27/32; per spec amendment 1 (written before reading results) the 5 killed split-101 fits were rerun unchanged (logs run1_log.txt, run2_log.txt).
