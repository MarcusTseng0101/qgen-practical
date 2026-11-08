# Step 7 summary: R at collision-matched σ (iqp4, N = ∞, n = 14 and 16)

Step 7 was designed after step 6; the n = 12 reference and nearby n = 14 points are data already seen; G is the generic IQP (no oracle); n ≤ 16 proxies are not hardness evidence.

Spec: `specs/step7_collision_matched.md` (frozen at 3407d50). The grid is 2 n × 3 levels × 5 seeds = 30
instances, all run, with no cut. The user decided this after the harness was removed; the projection had
been 3.38 h, under the 5 h budget, so no cut was needed anyway. The n = 12 rows are step 5's iqp4 N = ∞
data at σ = 0.15, 0.175, 0.2 (already seen).

## Verdicts (frozen hypotheses, spec section 4)

Cell verdict: "<1" if the IQR over 5 seeds lies wholly below 1, "≥1" if wholly at or above 1, otherwise
"undecided".

| ID | Statement | n = 14 | n = 16 | Result |
|---|---|---|---|---|
| C1 | level B: R < 1 at n = 14 and 16 | 0.870 [0.756, 0.884] → <1 | 0.654 [0.651, 1.105] → undecided | **FAIL** |
| C2 | level C: R < 1 at n = 14 and 16 | 0.706 [0.580, 0.888] → <1 | 0.799 [0.593, 1.313] → undecided | **FAIL** |
| C3 | level A: median R ≥ 1 at n = 14 and 16 | median 0.754 | median 0.832 | **FAIL** |
| C4 | n = 16: median G residual ≤ 1e-2 at B and C | — | B 2.11e-3, C 1.57e-3 | **PASS** |

**Reading rule (spec section 4).** C1 and C2 both fail at n = 16 while C4 passes. The frozen reading
is therefore: **the advantage shrinks with n even at matched peakedness, and under-training does not
explain it.**

Qualification, needed to read the rule correctly. At n = 16, C1 and C2 fail because the cells are
**undecided**, not because R ≥ 1. The n = 16 medians are below 1 at all three levels (0.83, 0.65,
0.80). The IQR reaches above 1 because seeds 1 and 2 give R > 1 at every level. At n = 14, all three
levels are "<1". So "shrinks" here means that R < 1 is no longer established across seeds at n = 16.
It does not mean that R crosses to ≥ 1. The rule was fixed before the grid, and this note applies it
as written. It does not replace the rule with a different reading.

C3 fails in the direction opposite to the prediction. Level A is "<1" at n = 14 (IQR 0.738–0.825) and
has median 0.83 at n = 16. In collision coordinates, the crossing that n = 12 placed between levels A
and B has not stayed there. At n = 14 it lies at or beyond level A, at a more peaked target.

## Per-cell table (median [q1, q3] over 5 seeds)

R = G_iqp / G_maxent3 at orders 4–6, taken at G's lowest-residual restart. G residual is the sum of the
training residual over orders ≤ 3. Spread is the largest, over seeds, of max/min restart residual.
Collision is 2ⁿ Σp² of the target. "vs n=12" is the collision median divided by the n = 12 level's
median.

| n | level | σ | R | verdict | G residual | spread max | G maxiter seeds | collision | vs n=12 | D3 (exploratory) |
|---|---|---|---|---|---|---|---|---|---|---|
| 12 | A | 0.15 | 1.346 [0.888, 1.390] | undecided | 8.74e-3 [6.96e-3, 1.16e-2] | 1.40 | 0/5 | 561 [458, 627] | 1.00 | 0.175 [0.170, 0.188] |
| 12 | B | 0.175 | 0.670 [0.467, 0.719] | <1 | 4.54e-3 [3.60e-3, 6.20e-3] | 2.03 | 0/5 | 284 [216, 328] | 1.00 | 0.216 [0.212, 0.231] |
| 12 | C | 0.2 | 0.577 [0.450, 0.579] | <1 | 2.13e-3 [1.52e-3, 2.39e-3] | 2.60 | 0/5 | 134 [95, 159] | 1.00 | 0.248 [0.244, 0.270] |
| 14 | A | 0.193 | 0.754 [0.738, 0.825] | <1 | 5.10e-3 [2.25e-3, 1.39e-2] | 4.01 | 0/5 | 562 [464, 659] | 1.00 | 0.240 [0.177, 0.346] |
| 14 | B | 0.213 | 0.870 [0.756, 0.884] | <1 | 3.74e-3 [2.59e-3, 8.71e-3] | 1.62 | 0/5 | 292 [243, 350] | 1.03 | 0.247 [0.198, 0.372] |
| 14 | C | 0.236 | 0.706 [0.580, 0.888] | <1 | 1.85e-3 [1.78e-3, 4.67e-3] | 2.24 | 0/5 | 134 [118, 166] | 1.00 | 0.251 [0.218, 0.380] |
| 16 | A | 0.231 | 0.832 [0.576, 1.230] | undecided | 3.69e-3 [3.31e-3, 4.21e-3] | 2.19 | 0/5 | 573 [529, 652] | 1.02 | 0.283 [0.281, 0.285] |
| 16 | B | 0.251 | 0.654 [0.651, 1.105] | undecided | 2.11e-3 [1.67e-3, 2.19e-3] | 2.35 | 0/5 | 287 [285, 313] | 1.01 | 0.304 [0.293, 0.309] |
| 16 | C | 0.274 | 0.799 [0.593, 1.313] | undecided | 1.57e-3 [1.10e-3, 2.29e-3] | 1.80 | 0/5 | 134 [132, 153] | 1.00 | 0.325 [0.295, 0.332] |

The matched σ were applied as intended. Every cell's collision-ratio median is within 3 % of its n = 12
level (largest: n = 14 B, ×1.03).

Per-seed R and G residual (seeds 0–4):

| n | level | R | G residual |
|---|---|---|---|
| 14 | A | 0.543, 0.754, 0.738, 0.825, 1.302 | 5.1e-3, 2.3e-3, 1.4e-3, 2.3e-2, 1.4e-2 |
| 14 | B | 0.445, 1.167, 0.870, 0.756, 0.884 | 3.7e-3, 2.4e-3, 2.6e-3, 1.5e-2, 8.7e-3 |
| 14 | C | 0.423, 1.304, 0.888, 0.580, 0.706 | 1.9e-3, 1.8e-3, 1.2e-3, 7.3e-3, 4.7e-3 |
| 16 | A | 0.358, 1.246, 1.230, 0.576, 0.832 | 2.9e-3, 1.8e-2, 3.7e-3, 3.3e-3, 4.2e-3 |
| 16 | B | 0.394, 1.277, 1.105, 0.654, 0.651 | 1.7e-3, 9.7e-3, 1.6e-3, 2.1e-3, 2.2e-3 |
| 16 | C | 0.593, 1.336, 1.313, 0.799, 0.583 | 9.7e-4, 4.8e-3, 2.3e-3, 1.1e-3, 1.6e-3 |

## Failure-mode checks (spec section 5)

- **Under-training.** No cell has G at maxiter in any seed (0/30 instances; more than 2/5 would flag a
  cell). No R is flagged as possibly biased upward.
  - The highest G residual is 2.3e-2, at n = 14 level A seed 3.
  - At n = 16 the highest is 1.8e-2, at level A seed 1. n = 16 seed 1 has the largest residual at
    every level (1.8e-2, 9.7e-3, 4.8e-3). This repeats the step-6 pattern for n = 16 seed 1, though
    10× smaller than step 6's 0.16–0.18.
  - The restart spread (max/min) is at most 4.0, at n = 14 A.
- **MaxEnt(3).** No instance hit maxiter (0/30). The largest training residual is 1.3e-12.
- **Code-path drift.** `tests/test_step7.py` reproduces step 6's R at n = 14, σ = 0.2, seed 0 within a
  relative 1e-6. All 9 tests pass.
- **Memory.** Peak process memory is 319 MiB at n = 14 and 1479 MiB at n = 16. Neither n ran out of
  memory, and there was no float32 and no sampling.
- **Unchanged.** No restarts were added, and maxiter, optimizer, ridge and src/step1..6 are unchanged.

## Timing

- **Timed instances** (largest σ, seed 0):
  - n = 14, σ = 0.236: 48.6 s (G fit 35.8 s);
  - n = 16, σ = 0.274: 762.4 s (G fit 733.9 s).
- **Projection** (×15 per n): 3.38 h (`PROJECTION.json`), against a 5 h budget, so no cut.
- **Actual** (sum of instance times, including the two timed instances, which the grid reused):
  - n = 14: 15 instances, 686 s in total (34–62 s each);
  - n = 16: 15 instances, 15384 s = 4.27 h (230–1641 s each);
  - total 4.46 h, 32 % over the projection.
- **Wall clock** (timing start to grid end): 12:55 → 17:22 on 2026-11-08, 4 h 27 min. This is under the
  user's 8 h stop.
- At n = 16, run time varies ×7 across seeds. It does not track σ monotonically (level A ranges
  230–1641 s).

## Exploratory (not frozen hypotheses)

- **Seed dependence at n = 16.** Seeds 1 and 2 give R > 1 at all three levels. Seeds 0, 3 and 4 give
  R < 1 at all three levels. Whether a seed is above or below 1 looks like a property of the target
  instance (its layout or angles), not of the collision level. Seed 1 also has the largest G residual
  at n = 16, but seed 2's residual is ordinary (1.6e-3–3.7e-3). Under-training therefore does not
  account for both seeds.
- **No collapse in collision coordinates.** The n = 12, 14 and 16 curves in `R_vs_collision_by_n` do
  not collapse:
  - n = 12 runs from 1.35 (A) down to 0.58 (C);
  - n = 14 and n = 16 are roughly flat at 0.65–0.87 over the three levels.
  - Against step 6 at fixed σ, matching collision removes most of the large R values at n = 14 and 16:
    those came from the very peaked low-σ targets. What remains does not depend on peakedness the way
    n = 12 does.
- **D3 does not match.** D3 grows with n at matched collision ratio. At level C it is 0.248, 0.251 and
  0.325 for n = 12, 14 and 16. A matched collision ratio does not give a matched completion room
  (D3).
- **G and G_maxent3 both fall with n.** Both fall by about 3× from n = 12 to 16 at every level (G_iqp
  4e-4 → 1.2e-4–1.4e-4). Their ratio stays within the IQR bands of 1.

## Files

- `results/step7/n_{14,16}/sigma_*/seed_*/metrics.json` (30 files)
- `table.csv`, `verdicts.json`, `PROJECTION.json`
- logs: `timing_runs.log`, `projection.log`, `grid.log`, `report.log`
- `figures/step7/R_vs_collision_by_n.{png,pdf}` and `figures/step7/G_vs_level_by_n.{png,pdf}`
