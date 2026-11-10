Step 13 was designed after step 12; seeds 30–49 are fresh; the gate threshold τ = 1e-2 was chosen on seeds 10–29 and is frozen; the gate uses training moments only; G is the generic IQP (no oracle); n ≤ 16 proxies are not hardness evidence.

Spec: `specs/step13_residual_gate.md`. Gate: use G iff its training residual ≤ τ = 0.01, else MaxEnt(3).

| ID | n | Statement | Counts | Verdict |
|---|---|---|---|---|
| F1 | 16 | iqp4: wins >= 10/20 and one-sided sign-test p <= 0.05 | picked 15, wins 14, losses 1, ties 5, sign p = 0.000488 | **PASS** |
| F2 | 16 | lcm + ising4 pooled: losses <= 2/40 | picked 0, wins 0, losses 0, ties 40 | **PASS** |
| F3 | 14 | iqp4: wins >= 10/20 and one-sided sign-test p <= 0.05 | picked 11, wins 9, losses 2, ties 9, sign p = 0.0327 | **FAIL** |
| F4 | 14 | lcm + ising4 pooled: losses <= 2/40 | picked 0, wins 0, losses 0, ties 40 | **PASS** |

## n = 16 (exploratory)

Pool of 60: geometric mean R_gate = 0.867; always-IQP = 3.43; oracle min(R, 1) = 0.854.

| | iqp4 | lcm | ising4 |
|---|---|---|---|
| picked / wins / losses / ties | 15 / 14 / 1 / 5 | 0 / 0 / 0 / 20 | 0 / 0 / 0 / 20 |
| R (always IQP) | 0.663 [0.524, 0.865] | 21.4 [9.42, 44.7] | 2.54 [1.91, 3.07] |
| training residual | 0.00569 [0.00212, 0.00976] | 0.578 [0.308, 1.44] | 0.233 [0.19, 0.284] |
| worst R among picked | 1.46 | — | — |
| gmean R_gate | 0.651 | 1 | 1 |
| τ = 3e-3: picked/wins/losses | 6/6/0 | 0/0/0 | 0/0/0 |
| τ = 3e-2: picked/wins/losses | 17/14/3 | 0/0/0 | 0/0/0 |
| D3 | 0.356 [0.313, 0.442] | 0.0391 [0.0305, 0.0489] | 0.381 [0.265, 0.49] |
| collision ratio | 486 [311, 694] | 233 [189, 380] | 72 [53.1, 88.9] |
| median minutes | 50.8 | 13.7 | 10.4 |

## n = 14 (exploratory)

Pool of 60: geometric mean R_gate = 0.93; always-IQP = 18.1; oracle min(R, 1) = 0.904.

| | iqp4 | lcm | ising4 |
|---|---|---|---|
| picked / wins / losses / ties | 11 / 9 / 2 / 9 | 0 / 0 / 0 / 20 | 0 / 0 / 0 / 20 |
| R (always IQP) | 0.752 [0.59, 1.24] | 408 [201, 580] | 13.8 [9.5, 31.6] |
| training residual | 0.00597 [0.00309, 0.0321] | 1.72 [1.12, 2.63] | 0.744 [0.491, 1.22] |
| worst R among picked | 1.48 | — | — |
| gmean R_gate | 0.805 | 1 | 1 |
| τ = 3e-3: picked/wins/losses | 4/3/1 | 0/0/0 | 0/0/0 |
| τ = 3e-2: picked/wins/losses | 14/11/3 | 0/0/0 | 0/0/0 |
| D3 | 0.299 [0.248, 0.357] | 0.0153 [0.00966, 0.0202] | 0.21 [0.136, 0.333] |
| collision ratio | 485 [328, 672] | 274 [225, 475] | 490 [197, 796] |
| median minutes | 5.39 | 3.17 | 1.51 |

Figure: `figures/step13/gate.png`.

## Acceptance (`python -m src.step13.run --verify`, exit 0)

```
ok   [spec] specs/step13_residual_gate.md committed and unchanged
ok   [closed] src/step1..12 unchanged since 41df310
ok   [grid] 120 instances: family/n/seed, 3 G restarts, step-12 beta or level-B sigma
ok   [targets] every target p >= 0 and sums to 1 within 1e-12
ok   [summary] SUMMARY opens with the required sentence
ok   [summary] F1–F4 marked
ok   [figures] figures/step13/gate
ok   [tests] 4 passed in 0.70s
ALL CHECKS PASS (step 13)
```
