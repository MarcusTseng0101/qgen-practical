# Step 6: does the iqp4 advantage window survive larger n? Summary

Step 6 was designed after step 5; the n = 12 reference is data already seen; G is the generic IQP (no oracle); n ≤ 16 proxies are not hardness evidence.

Spec: `specs/step6_iqp4_scaling_n.md` (frozen at 567aab6; harness v7 bccacee). Branch
`step6-scaling`, 2026-11-07/08. Target `iqp4`, N = ∞ only.

- **45 of 50 instances.** n = 16 at σ = 0.25 (5 instances) was **cut per spec section 7, step 1**:
  the projection was 3.13 h against a 3 h budget, and the user chose the cut (decision A). No
  other cell was cut; no seeds, restarts or n = 14 cells.
- n = 12 is step 5's `iqp4` N = ∞ data, not rerun.
- Produced by the grid run of `src/step6/run.py` (log `results/step6/grid.log`) and
  `python -m src.step6.run --report`.
- Per-instance data: `results/step6/n_<14|16>/sigma_<σ>/seed_<s>/metrics.json`.
- `table.csv` (n = 12 rows taken from step 5), `verdicts.json` (σ\* and sign changes for n = 12,
  14, 16).
- Figures: `figures/step6/R_vs_sigma_by_n`, `G_vs_sigma_by_n`, `collision_vs_n`.

## Read first

- **G uses 3 restarts at every n**, never fewer, with the unchanged optimizer, maxiter and initial
  point. G has 469 generators at n = 14 and 696 at n = 16. MaxEnt(3) ridge is 1e-8.
- R = G_iqp / G_maxent3 at orders 4–6, at G's lowest-training-residual restart.
- "res" is G's order-≤3 training residual (a sum over all order-≤3 moments) at that restart.
- "coll" is the target's collision ratio 2ⁿ Σp². It is the design caveat of spec section 2: at
  fixed σ, iqp4 gets more peaked as n grows.
- Statistics are median [IQR] over 5 seeds.
  - "<1" means the IQR lies entirely below 1.
  - "≥1" means the IQR lies entirely at or above 1.
  - Otherwise the cell is "undecided".
- σ\* is the first downward crossing of median R through 1, interpolated in log R against log σ,
  exactly as in step 5.
- **Training is less complete at larger n (spec section 5).**
  - Median G residual at σ ≤ 0.175: 0.8–2.1e-2 at n = 14 and 1.2–2.0e-2 at n = 16, compared with
    4.5e-3 to 1.0e-2 at n = 12. Many of these are above 1e-2, though not ≫ 1e-2.
  - **Seed 1 at n = 16** is ≫ 1e-2 (see the "Failure modes" section). Its R values may be biased
    upward.
- **MaxEnt maxiter: 2 of 45 instances** hit the 20000-iteration limit: n = 16 seed 3 at
  σ = 0.125 and at σ = 0.15. Their training residuals are 3.6e-11 and 6.1e-12. The ridge was not
  changed.
- **G maxiter: 0 of 45.** Every G restart stopped on L-BFGS-B's relative-reduction criterion, so
  no cell reaches the "> 2 of 5 seeds at maxiter" flag.

## Hypotheses (iqp4, N = ∞)

| ID | Verdict | Numbers |
|---|---|---|
| S1 | S1: **FAIL** (prediction) | At σ = 0.2, neither n is R < 1. n = 14: R = 0.889 [0.720, 1.04], undecided (res 4.3e-3; coll 448). n = 16: R = 1.38 [0.623, 1.51], undecided (res 7.2e-3; coll 1673). For comparison, n = 12 gave 0.577 [0.450, 0.579] < 1 (res 2.1e-3; coll 134). |
| S2 | S2: **FAIL** (prediction) | σ\*(n = 14) = **0.185**, with 1 sign change. It lies inside [0.135, 0.185] by 0.0004. σ\*(n = 16) is **undefined**: median R ≥ 1 at all 4 run σ (10.9, 4.91, 1.81, 1.38), so there are 0 sign changes. The spec requires both to be defined, so S2 fails. n = 12 (step 5): 0.160. |
| S3 | S3: **FAIL** (prediction) | At σ = 0.175, n = 14: R = 1.08 [0.704, 1.32], undecided (res 8.1e-3; coll 986). n = 16: R = 1.81 [1.12, 2.02] **≥ 1** (res 1.2e-2; coll 3769). |
| S4 | S4: **PASS** (prediction; over 4 σ) | At n = 16, median G_iqp max/min = **1.54** (≤ 3): 1.36e-4 … 2.10e-4 over σ = 0.125, 0.15, 0.175, 0.2. σ = 0.25 was cut (spec section 7), so the ratio uses the 4 remaining σ. |

## Every cell: median R [IQR] (res = median G residual; coll = median collision ratio)

| σ | n = 12 (step 5, seen) | n = 14 | n = 16 |
|---|---|---|---|
| 0.125 | 2.82 [1.88, 3.23] ≥1 (res 1.0e-2; coll 1017) | 4.32 [3.75, 9.12] ≥1 (res 2.1e-2; coll 3763) | 10.9 [6.87, 19.0] ≥1 (res 2.0e-2; coll 14846) † |
| 0.15 | 1.35 [0.888, 1.39] undecided (res 8.7e-3; coll 561) | 1.88 [1.53, 2.41] ≥1 (res 1.3e-2; coll 2016) | 4.91 [2.68, 8.14] ≥1 (res 1.9e-2; coll 7850) † |
| 0.175 | 0.670 [0.467, 0.719] <1 (res 4.5e-3; coll 284) | 1.08 [0.704, 1.32] undecided (res 8.1e-3; coll 986) | 1.81 [1.12, 2.02] ≥1 (res 1.2e-2; coll 3769) † |
| 0.2 | 0.577 [0.450, 0.579] <1 (res 2.1e-3; coll 134) | 0.889 [0.720, 1.04] undecided (res 4.3e-3; coll 448) | 1.38 [0.623, 1.51] undecided (res 7.2e-3; coll 1673) † |
| 0.25 | 0.891 [0.836, 1.14] undecided (res 1.0e-3; coll 27) | 0.882 [0.859, 0.918] <1 (res 1.5e-3; coll 84) | **cut** (spec section 7, step 1) |
| σ\* | 0.160 (1 sign change) | 0.185 (1) | undefined (0) |

† This cell contains seed 1, whose residual is the highest at every n = 16 σ: ≫ 1e-2 at σ = 0.125
and 0.15. See "Failure modes".

Per-seed R (res), seeds 0–4:

| n, σ | seed 0 | seed 1 | seed 2 | seed 3 | seed 4 |
|---|---|---|---|---|---|
| 14, 0.125 | 3.36 (1.3e-2) | 9.12 (2.7e-2) | 4.32 (4.6e-3) | 3.75 (2.5e-2) | 10.8 (2.1e-2) |
| 14, 0.15 | 1.53 (1.3e-2) | 2.41 (1.2e-2) | 1.49 (3.1e-3) | 1.88 (3.1e-2) | 3.56 (2.0e-2) |
| 14, 0.175 | 0.687 (8.1e-3) | 1.32 (7.6e-3) | 0.704 (1.5e-3) | 1.08 (2.8e-2) | 2.28 (1.9e-2) |
| 14, 0.2 | 0.489 (4.3e-3) | 1.04 (2.8e-3) | 0.889 (1.8e-3) | 0.720 (2.2e-2) | 1.29 (1.2e-2) |
| 14, 0.25 | 0.494 (1.0e-3) | 1.37 (1.2e-3) | 0.882 (1.5e-3) | 0.859 (3.8e-3) | 0.918 (2.8e-3) |
| 16, 0.125 | 3.54 (1.3e-2) | **30.5 (1.6e-1)** | 10.9 (2.0e-2) | 6.87 (1.6e-2) | 19.0 (2.0e-2) |
| 16, 0.15 | 1.44 (1.3e-2) | **14.3 (1.8e-1)** | 4.91 (1.9e-2) | 2.68 (1.6e-2) | 8.14 (2.4e-2) |
| 16, 0.175 | 0.693 (9.5e-3) | **2.02 (3.6e-2)** | 1.81 (1.2e-2) | 1.12 (1.2e-2) | 3.68 (1.9e-2) |
| 16, 0.2 | 0.455 (6.7e-3) | **1.51 (3.0e-2)** | 1.38 (7.1e-3) | 0.623 (7.2e-3) | 1.87 (1.1e-2) |

## Failure modes (spec section 5)

- **Pattern: n = 16, seed 1 (possible FM2 or under-training; R possibly biased upward).**
  - Its G residual is ≫ 1e-2 at two σ:
    - σ = 0.125: 0.160; the three restarts give 0.163, 0.160 and 0.163.
    - σ = 0.15: 0.179; the restarts give 0.182, 0.181 and 0.179.
  - It is still the highest of the five seeds at σ = 0.175 (3.6e-2) and at σ = 0.2 (3.0e-2).
  - At σ = 0.175, two of its three restarts also stopped high: 0.131 and 0.122.
  - Its restarts agree with each other (spread ≤ 3.7×). So all three restarts land in the same
    high-residual region; this is not one unlucky restart.
  - Its G_iqp is about 5× the other seeds' at σ ≤ 0.15 (1.0e-3 against about 2e-4), and its R
    is the largest or second largest in every n = 16 cell.
  - No restarts were added, and maxiter and the optimizer were not changed.
- **Residual above 1e-2 elsewhere (not ≫).**
  - At n = 14 and n = 16, 26 of the other instances have residual between 1.0e-2 and 3.6e-2,
    mostly at σ ≤ 0.175.
  - Every n = 16 cell has a median residual above n = 12's at the same σ (figure
    `G_vs_sigma_by_n`).
- **Restart spread above 10×:** none. The largest is 3.7×, at n = 16, σ = 0.175, seed 1.
- **G at maxiter:** 0 of 45 instances. **MaxEnt at maxiter:** 2 of 45 (listed in "Read first").
- **Memory:** the peak working set at n = 16 was 1.5 GiB. There was no out-of-memory failure,
  and no float32 or sampling was used.
- **Code-path drift:** `tests/test_step6.py` reproduces step 5's n = 12, σ = 0.2, seed 0 R to a
  relative difference ≤ 1e-6, through the same `fit_instance` path.

## Timing

| | instances | sum of instance times | mean | max | projection (×25, from σ = 0.2 seed 0) |
|---|---|---|---|---|---|
| n = 14 | 25 | 1606 s (0.45 h) | 64 s | 192 s | 0.36 h |
| n = 16 | 20 | 16600 s (4.61 h) | 830 s | 3168 s | 2.78 h for 25; 2.22 h for the 20 run |

- Wall clock was about 4.9 h (21:35 to 02:31), against a projected 2.58 h for the cut grid. The
  user raised the stop limit to 7 h during the run.
- Per-iteration time at n = 16 varied about 15× between instances: 0.05 s per iteration in the
  timed instance, up to 0.7 s per iteration at σ = 0.125, seed 3. The cause was not identified.

## Exploratory (not hypotheses; no hypotheses were added)

- **At fixed σ, R grows with n.** Every common σ ≤ 0.2 has a larger median R at n = 16 than at
  n = 14, and at n = 14 than at n = 12. The window where R < 1 shrinks to an undecided band at
  n = 14 (σ = 0.2, with the IQR at 0.25 below 1) and does not appear at n = 16 on the σ run.
- **Both gaps shrink with n; the room shrinks faster** (figure `G_vs_sigma_by_n`).
  - At σ = 0.2, the median G_maxent3 is 7.3e-4, 2.6e-4 and 1.3e-4 at n = 12, 14 and 16.
  - The median G_iqp is 4.1e-4, 2.4e-4 and 1.4e-4.
  - D3 at σ = 0.2 stays at 0.24–0.25 for all three n, so the KL room is n-independent while the
    order 4–6 parity room is not.
- **The collision ratio rises about 3.3–4× per +2 qubits at every σ** (figure `collision_vs_n`;
  e.g. at σ = 0.2: 134, 448 and 1673). Within the run, R ≥ 1 cells coincide with
  coll ≳ 1000–2000.
- **The residual tracks R.** Pooled over σ, Spearman ρ(G residual, R) = 0.57 at n = 14
  (25 instances) and 0.80 at n = 16 (20 instances). Both residual and R fall with σ, so part of
  this is the σ effect.
- **Dropping seed 1 would not rescue any n = 16 cell.** The four other seeds give R ≥ 1 for at
  least two seeds at every σ.
