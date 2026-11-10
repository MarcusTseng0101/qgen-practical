Step 16 was designed after steps 14–15 and pilots on development seeds; seeds 70–89 are fresh; the gate is step 14's r_N − Σ(1 − f̂²)/N ≤ τ = 1e-2 from training data only; G is the generic IQP (no oracle); n = 16 proxies are not hardness evidence.

Spec: `specs/step16_shot_threshold.md`. Gate: use G iff r_N − Σ(1 − f̂²)/N ≤ τ = 0.01, else MaxEnt(3).

| ID | N | Statement | Counts | Verdict |
|---|---|---|---|---|
| T1 | 3e+04 | iqp4: wins >= 10/20 and one-sided sign-test p <= 0.05 | picked 19, wins 17, losses 2, ties 1, sign p = 0.000364 | **PASS** |
| T2 | 3e+04 | lcm + ising4 pooled: losses <= 2/40 | picked 0, wins 0, losses 0, ties 40 | **PASS** |

## N = 3e+04 (exploratory)

Pool of 60: geometric mean R_gate = 0.895; always-IQP = 2.88; oracle min(R, 1) = 0.893.

| | iqp4 | lcm | ising4 |
|---|---|---|---|
| picked / wins / losses / ties | 19 / 17 / 2 / 1 | 0 / 0 / 0 / 20 | 0 / 0 / 0 / 20 |
| R (always IQP) | 0.71 [0.649, 0.877] | 12.8 [8.58, 20.2] | 2.35 [1.73, 3.15] |
| excess residual | -0.0167 [-0.0187, -0.0141] | 0.641 [0.282, 0.824] | 0.121 [0.0975, 0.212] |
| r_N (raw) | 0.00591 [0.00362, 0.0079] | 0.663 [0.304, 0.846] | 0.144 [0.121, 0.235] |
| floor | 0.0222 [0.0219, 0.0225] | 0.0219 [0.0216, 0.0222] | 0.0229 [0.0226, 0.023] |
| r_true (vs exact moments) | 0.0224 [0.0205, 0.0259] | 0.683 [0.304, 0.858] | 0.155 [0.13, 0.243] |
| worst R among picked | 1.1 | — | — |
| gmean R_gate | 0.718 | 1 | 1 |
| uncorrected gate r_N ≤ τ: picked/wins/losses | 17/15/2 | 0/0/0 | 0/0/0 |
| τ = 3e-3: picked/wins/losses | 19/17/2 | 0/0/0 | 0/0/0 |
| τ = 3e-2: picked/wins/losses | 20/17/3 | 0/0/0 | 0/0/0 |
| D3 | 0.329 [0.307, 0.412] | 0.0485 [0.042, 0.0541] | 0.354 [0.208, 0.425] |
| median minutes | 45.5 | 19.4 | 16.5 |

Figure: `figures/step16/gate_N3e4.png`.

## --verify (raw)

```
ok   [spec] specs/step16_shot_threshold.md committed and unchanged
ok   [closed] src/step1..15 unchanged since ee59b78
ok   [grid] 60 instances: family/N/seed, n = 16, 3 G restarts, step-12 beta or level-B sigma
ok   [targets] every target p >= 0 and sums to 1 within 1e-12
ok   [summary] SUMMARY opens with the required sentence
ok   [summary] T1–T2 marked
ok   [figures] figures/step16/gate_N3e4
ok   [tests] 3 passed in 0.57s
ALL CHECKS PASS (step 16)
```
