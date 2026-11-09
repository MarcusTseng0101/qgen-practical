Step 11 was designed after step 10; the bitflip model is a classical, decohered twin of G with the same generators, inits and optimizer; the targets are coherent IQPs, so this tests coherence on IQP-generated data only; n ≤ 16 proxies are not hardness evidence.

Spec: `specs/step11_bitflip_control.md`. Reading (n = 16, spec section 3): **advantage needs coherence (decohered twin lacks it)**.

| ID | Statement | Count | Verdict |
|---|---|---|---|
| C1 | n = 16: G_iqp < G_bitflip | 20/20 (need ≥ 15) | **PASS** |
| C2 | n = 16: G_bitflip < G_maxent3 | 3/20 (need ≥ 15) | **FAIL** |
| C3 | n = 14: G_iqp < G_bitflip | 20/20 (need ≥ 15) | **PASS** |
| C4 | n = 14: G_bitflip < G_maxent3 | 2/20 (need ≥ 15) | **FAIL** |

## Medians [IQR] and exploratory counts

| | n = 16 | n = 14 |
|---|---|---|
| Q = G_iqp / G_bitflip | 0.39 [0.222, 0.558] | 0.324 [0.116, 0.486] |
| R_B = G_bitflip / G_maxent3 | 1.84 [1.19, 2.97] | 3.66 [2.21, 5.44] |
| R = G_iqp / G_maxent3 (step 9) | 0.637 [0.543, 0.889] | 0.976 [0.579, 1.54] |
| R < 1 (step 9) | 16 | 10 |
| bitflip training residual | 0.0937 [0.055, 0.224] | 0.0998 [0.0623, 0.292] |
| bitflip residual > 1e-2 | 20 | 20 |
| IQP residual > 1e-2 (step 9) | 4 | 8 |
| seeds where both residuals ≤ 1e-2 | 0 | 0 |
| … of which Q < 1 | 0 | 0 |
| … of which R_B < 1 | 0 | 0 |
| … of which R < 1 | 0 | 0 |
| best-of-10 bitflip: R_B < 1 | 3 | 2 |
| G_iqp (3) < G_bitflip (best of 10) | 20 | 20 |
| Spearman(R, R_B) across seeds | 0.349 | 0.343 |
| min bitflip p | 3.25e-11 | 2.7e-10 |
| max |Σp − 1| | 3.33e-16 | 4.44e-16 |
| median minutes per seed | 18.2 | 5.12 |
| n = 14 only: G_iqp (10, step 10) < G_bitflip (10) | — | 19 |

Figure: `figures/step11/G_iqp_vs_bitflip.png`.

## Verify (raw output of `PYTHONIOENCODING=utf-8 python -m src.step11.run --verify`, exit 0)

```
ok   [spec] specs/step11_bitflip_control.md committed and unchanged
ok   [closed] src/step1..10 unchanged since a7dbff9
ok   [grid] 40 seeds, exact σ, 10 restarts, targets match step 9
ok   [prob] every bitflip p ≥ −1e-12 and sums to 1 within 1e-10
ok   [summary] SUMMARY opens with the required sentence
ok   [summary] C1–C4 marked
ok   [figures] figures/step11/G_iqp_vs_bitflip
ok   [tests] 5 passed in 0.50s
ALL CHECKS PASS (step 11)
```
