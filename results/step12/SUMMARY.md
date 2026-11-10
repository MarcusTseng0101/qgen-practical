Step 12 was designed after step 11; the targets are not IQPs (`lcm` is a latent-class mixture, `ising4` a Boltzmann model with weight-4 terms), with peakedness calibrated to step 9 on seeds 0–4; G is the generic IQP (no oracle); n ≤ 16 proxies are not hardness evidence.

Spec: `specs/step12_nonIQP_targets.md`.

| ID | Family, n | Statement | Count | Verdict |
|---|---|---|---|---|
| E1 | lcm, 16 | R = G_iqp / G_maxent3 < 1 | 0/20 (need ≥ 15) | **FAIL** |
| E2 | lcm, 16 | Q = G_iqp / G_bitflip < 1 | 20/20 (need ≥ 15) | **PASS** |
| E3 | ising4, 16 | R = G_iqp / G_maxent3 < 1 | 0/20 (need ≥ 15) | **FAIL** |
| E4 | ising4, 16 | Q = G_iqp / G_bitflip < 1 | 20/20 (need ≥ 15) | **PASS** |
| E5 | lcm, 14 | R = G_iqp / G_maxent3 < 1 | 0/20 (need ≥ 15) | **FAIL** |
| E6 | lcm, 14 | Q = G_iqp / G_bitflip < 1 | 20/20 (need ≥ 15) | **PASS** |
| E7 | ising4, 14 | R = G_iqp / G_maxent3 < 1 | 0/20 (need ≥ 15) | **FAIL** |
| E8 | ising4, 14 | Q = G_iqp / G_bitflip < 1 | 19/20 (need ≥ 15) | **PASS** |

## Medians [IQR] and exploratory counts

| | lcm/n_16 | ising4/n_16 | lcm/n_14 | ising4/n_14 |
|---|---|---|---|---|
| R | 25.4 [17.4, 43.5] | 2.05 [1.85, 2.6] | 160 [57.4, 692] | 16.5 [8.34, 36.6] |
| Q | 0.28 [0.139, 0.424] | 0.443 [0.376, 0.517] | 0.349 [0.214, 0.438] | 0.447 [0.269, 0.523] |
| R_B | 132 [55.3, 152] | 5.06 [3.54, 6.69] | 559 [262, 1.52e+03] | 48.8 [20, 145] |
| bitflip beats MaxEnt(3) | 0 | 0 | 0 | 0 |
| IQP training residual | 0.605 [0.385, 1.5] | 0.2 [0.168, 0.225] | 1.57 [0.889, 3.06] | 0.802 [0.657, 1.44] |
| IQP residual > 1e-2 | 20 | 20 | 20 | 20 |
| bitflip residual > 1e-2 | 20 | 20 | 20 | 20 |
| D3 | 0.0428 [0.0377, 0.048] | 0.339 [0.2, 0.465] | 0.0178 [0.0136, 0.0243] | 0.222 [0.131, 0.368] |
| collision ratio | 291 [225, 418] | 41.6 [31.8, 69.3] | 381 [260, 650] | 314 [172, 829] |
| Spearman(R, D3) | -0.194 | -0.335 | -0.824 | -0.805 |
| residual-gated: wins / losses | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| median minutes per instance | 18.3 | 14.8 | 3.78 | 2.16 |

Figure: `figures/step12/R_by_family.png`.

## Acceptance (`python -m src.step12.run --verify`, exit 0)

```
ok   [spec] specs/step12_nonIQP_targets.md committed and unchanged
ok   [closed] src/step1..11 unchanged since 438fc80
ok   [calibration] CALIBRATION.json: each median collision ratio within 1% of step 9
ok   [grid] 80 instances, calibrated beta, 3 G and 3 bitflip restarts
ok   [targets] every target p >= 0 and sums to 1 within 1e-12
ok   [summary] SUMMARY opens with the required sentence
ok   [summary] E1–E8 marked
ok   [figures] figures/step12/R_by_family
ok   [tests] 3 passed in 0.11s
ALL CHECKS PASS (step 12)
```
