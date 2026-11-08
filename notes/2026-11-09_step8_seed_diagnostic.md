# Step 8 diagnostic: why seeds 1 and 2 lose at n = 16 (exploratory, no new fits)

Research note, 2026-11-09.

**Sources**
- Data: the existing `metrics.json` files.
  - Step 7 (branch `step7-collision`, 72d47b1): n = 14 and 16, 30 instances.
  - Step 5: the n = 12 `iqp4` N = ∞ cells at σ = 0.15 / 0.175 / 0.2, 15 instances.
- No fit was rerun, and nothing in the worktree was changed.
- Script: `d8_seeds.py` in the session scratchpad. It reads `target_masks`, `target_theta`,
  `per_level`, `D3`, `collision_ratio_target`, `hi_order_frac` and `G_train_residual`.

**Status: exploratory.** No spec was frozen. The candidate features were listed in advance, and
all of them are reported:
1. which error moves: G_iqp or G_maxent3;
2. ‖θ₄‖/‖θ≤3‖ (`r4`), ‖θ₄‖/‖θ₂,₃‖ (`r4_23`) and max |θ₄|;
3. overlap of the weight-4 supports with the triples and pairs;
4. D3, the collision ratio, hi_order_frac, and the per-order (4, 5, 6) errors;
5. whether the same seeds lose at n = 12 and n = 14.

**Main caveat:**
- There are only 5 seeds per n, and many features were looked at, so some of them will separate
  2 of 5 by chance.
- The seeds are **not independent across n**. `r4` is almost the same for a given seed at every n
  (seed 1: 0.417 / 0.417 / 0.415), so the seeds' angle draws carry over across n. In effect there
  are about 5 angle vectors in total, not 15.

## 1. Two different reasons for losing

Per-seed n = 16 numbers at level B (σ = 0.251). Seeds 1 and 2 are the losers; the same pattern
holds at levels A and C.

| seed | R | G_iqp | G_maxent3 | D3 | r4 | max \|θ₄\| | G residual |
|---|---|---|---|---|---|---|---|
| 0 | 0.39 | 8.8e-5 | 2.24e-4 | 0.372 | 0.288 | 0.33 | 1.7e-3 |
| **1** | **1.28** | **1.77e-4** | 1.39e-4 | 0.304 | **0.415** | **0.57** | 9.7e-3 |
| **2** | **1.11** | 1.32e-4 | **1.19e-4** | **0.222** | 0.273 | 0.29 | 1.6e-3 |
| 3 | 0.65 | 1.28e-4 | 1.95e-4 | 0.293 | 0.301 | 0.32 | 2.1e-3 |
| 4 | 0.65 | 8.6e-5 | 1.32e-4 | 0.309 | 0.282 | 0.30 | 2.2e-3 |

- **Seed 1 is a misspecification loss.**
  - Its weight-4 part is the strongest of the five, at every n: `r4` is 0.415, against
    0.27–0.30 for the others, and max |θ₄| is about 1.8× the others'.
  - Its G_iqp is the largest of the five, about 1.3–2× the others. Most of the gap is at order 4:
    G's order-4 error is about 1.1e-4, against 3.5–6e-5 for the other seeds.
  - The weight-≤3 IQP cannot represent the weight-4 part. The bigger that part is, the more it
    costs.
  - Its G residual is the highest at every level: 1.8e-2 / 9.7e-3 / 4.8e-3. Some under-training
    may add to its R, but its residual at C (4.8e-3) is small and it still loses there
    (R = 1.34).
  - This is not new at n = 16. Seed 1 already loses at n = 14 at levels B and C (R = 1.17, 1.30).
    It is a loser at both n, but at n = 14 it is the only one, so the IQR stays below 1.
- **Seed 2 is a no-room loss.**
  - It has the lowest D3 of the five at every level at n = 16 (0.205 / 0.222 / 0.244), and also
    the lowest or second lowest at n = 12 and n = 14.
  - Its G_maxent3 is the lowest of the five. MaxEnt(3) has little to miss, so even an average
    G_iqp loses.
  - At n = 14, seed 2 wins narrowly (R = 0.74–0.89). At n = 16 it flips to a loss.
- Across all 45 instances (n = 12–16), seed 2 at n = 12 level A (R = 2.13) and seed 4 at n = 14
  level A (R = 1.30) fit the no-room pattern too: both have the lowest-group D3 in their cell.

## 2. How much the two features explain (rank correlation with log R, and a two-feature fit)

| set | D3 | r4 | r4_23 | max\|θ₄\| | coll | hi_order_frac | G res | overlap |
|---|---|---|---|---|---|---|---|---|
| n = 12 (15) | −0.72 | −0.05 | +0.20 | −0.44 | +0.56 | +0.41 | +0.62 | −0.13 |
| n = 14 (15) | −0.59 | +0.05 | +0.55 | −0.01 | −0.29 | −0.41 | −0.03 | +0.07 |
| n = 16 (15) | −0.59 | +0.09 | **+0.88** | +0.29 | −0.39 | −0.66 | +0.51 | +0.52 |

- Fit: log R ~ D3 + r4 within each n. R² is 0.46 at n = 12, 0.64 at n = 14 and **0.83 at n = 16**.
  The D3 coefficient is negative at every n (−5.3 / −2.7 / −6.8).
  - The r4 coefficient goes from ≈ 0 at n = 12 to +2.3 at n = 14 and +4.7 at n = 16. So the cost
    of a strong weight-4 part grows with n.
- r4 alone barely correlates with R, because it is constant per seed and the levels dominate the
  ranking. r4_23 mixes in the size of the weight-2/3 part and tracks R best at n = 16.
- The overlap features are uninformative. Every bit of every weight-4 support is covered by some
  pair or triple (`cov = 4` in all 45 instances). The "max shared bits with a triple" feature
  varies only between 1.5 and 2.3.
- The collision ratio does not separate the seeds within a cell. This fits step 7: matching the
  collision ratio fixes the median, but not the instance.

## 3. Reading (exploratory)

- At n = 16 the IQR crosses 1 because two separate mechanisms each knock out one seed:
  - **strong misspecification** (large weight-4 angles relative to weight ≤ 3) raises G_iqp;
  - **little completion room** (low D3) lowers G_maxent3.
- The first mechanism grows with n: the r4 coefficient rises. That fits an IQP whose missing
  weight-4 part costs more as the state space grows. It is a candidate explanation for why the
  margin weakens with n at matched peakedness.
- **Implication for the next test.** A cleaner scaling test would control D3 **and** the weight-4
  share r4_23, not the collision ratio. Alternatively, it would report R conditional on them, for
  example with more seeds and a regression on D3 and r4_23 per n.
  - With 5 seeds, losing one or two to either mechanism is enough to flip a frozen "IQR < 1"
    verdict.
  - **More seeds**, not more σ, would most improve the power of any step-9 test.
- None of this is a frozen test. The two-mechanism story was built on the same 45 instances it
  explains.
