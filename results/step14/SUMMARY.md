Step 14 was designed after step 13 and a pilot on development seeds; seeds 50–69 are fresh; the gate uses r_N − Σ(1 − f̂²)/N ≤ τ = 1e-2 from training data only; G is the generic IQP (no oracle); n = 16 proxies are not hardness evidence.

Spec: `specs/step14_finiteN_gate.md`. Gate: use G iff r_N − Σ(1 − f̂²)/N ≤ τ = 0.01, else MaxEnt(3).

| ID | N | Statement | Counts | Verdict |
|---|---|---|---|---|
| S1 | 1e+05 | iqp4: wins >= 10/20 and one-sided sign-test p <= 0.05 | picked 14, wins 11, losses 3, ties 6, sign p = 0.0287 | **PASS** |
| S2 | 1e+05 | lcm + ising4 pooled: losses <= 2/40 | picked 0, wins 0, losses 0, ties 40 | **PASS** |
| S3 | 1e+04 | iqp4: wins >= 10/20 and one-sided sign-test p <= 0.05 | picked 20, wins 12, losses 8, ties 0, sign p = 0.252 | **FAIL** |
| S4 | 1e+04 | lcm + ising4 pooled: losses <= 2/40 | picked 0, wins 0, losses 0, ties 40 | **PASS** |

## N = 1e+05 (exploratory)

Pool of 60: geometric mean R_gate = 0.953; always-IQP = 3.5; oracle min(R, 1) = 0.941.

| | iqp4 | lcm | ising4 |
|---|---|---|---|
| picked / wins / losses / ties | 14 / 11 / 3 / 6 | 0 / 0 / 0 / 20 | 0 / 0 / 0 / 20 |
| R (always IQP) | 0.931 [0.68, 1.06] | 16.5 [9.62, 31] | 2.65 [1.97, 3.42] |
| excess residual | -0.000368 [-0.00231, 0.0121] | 0.516 [0.299, 0.826] | 0.178 [0.111, 0.3] |
| r_N (raw) | 0.00619 [0.00431, 0.0185] | 0.523 [0.305, 0.832] | 0.185 [0.118, 0.306] |
| floor | 0.00663 [0.00648, 0.00666] | 0.00648 [0.00642, 0.00659] | 0.00684 [0.00679, 0.00686] |
| r_true (vs exact moments) | 0.0108 [0.00891, 0.0227] | 0.524 [0.31, 0.837] | 0.185 [0.124, 0.308] |
| worst R among picked | 1.36 | — | — |
| gmean R_gate | 0.864 | 1 | 1 |
| uncorrected gate r_N ≤ τ: picked/wins/losses | 14/11/3 | 0/0/0 | 0/0/0 |
| τ = 3e-3: picked/wins/losses | 14/11/3 | 0/0/0 | 0/0/0 |
| τ = 3e-2: picked/wins/losses | 20/12/8 | 0/0/0 | 0/0/0 |
| D3 | 0.319 [0.296, 0.417] | 0.0449 [0.0418, 0.0536] | 0.341 [0.219, 0.401] |
| median minutes | 51.3 | 13.7 | 16.6 |

## N = 1e+04 (exploratory)

Pool of 60: geometric mean R_gate = 0.985; always-IQP = 2.61; oracle min(R, 1) = 0.961.

| | iqp4 | lcm | ising4 |
|---|---|---|---|
| picked / wins / losses / ties | 20 / 12 / 8 / 0 | 0 / 0 / 0 / 20 | 0 / 0 / 0 / 20 |
| R (always IQP) | 0.992 [0.842, 1.05] | 7.49 [5, 9.23] | 2.44 [1.85, 2.88] |
| excess residual | -0.0511 [-0.0559, -0.0338] | 0.486 [0.186, 0.915] | 0.116 [0.0758, 0.216] |
| r_N (raw) | 0.0152 [0.00935, 0.0305] | 0.551 [0.252, 0.982] | 0.185 [0.144, 0.285] |
| floor | 0.0663 [0.0649, 0.0666] | 0.0648 [0.0641, 0.0658] | 0.0684 [0.0678, 0.0686] |
| r_true (vs exact moments) | 0.0581 [0.0554, 0.0693] | 0.542 [0.283, 0.976] | 0.23 [0.184, 0.311] |
| worst R among picked | 2.18 | — | — |
| gmean R_gate | 0.955 | 1 | 1 |
| uncorrected gate r_N ≤ τ: picked/wins/losses | 6/4/2 | 0/0/0 | 0/0/0 |
| τ = 3e-3: picked/wins/losses | 20/12/8 | 0/0/0 | 0/0/0 |
| τ = 3e-2: picked/wins/losses | 20/12/8 | 1/0/1 | 0/0/0 |
| D3 | 0.351 [0.334, 0.453] | 0.0772 [0.074, 0.0848] | 0.372 [0.253, 0.433] |
| median minutes | 43.7 | 15.2 | 12.6 |

Figure: `figures/step14/gate_finiteN.png`.

## Acceptance (`python -m src.step14.run --verify`, exit 0)

```
ok   [spec] specs/step14_finiteN_gate.md committed and unchanged
ok   [closed] src/step1..13 unchanged since b31cb7b
ok   [grid] 120 instances: family/N/seed, n = 16, 3 G restarts, step-12 beta or level-B sigma
ok   [targets] every target p >= 0 and sums to 1 within 1e-12
ok   [summary] SUMMARY opens with the required sentence
ok   [summary] S1–S4 marked
ok   [figures] figures/step14/gate_finiteN
ok   [tests] 4 passed in 0.58s
ALL CHECKS PASS (step 14)
```
