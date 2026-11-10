# Step 15 pilot: the split-sample gate does not fix N = 1e4 (development seeds, n = 16)

Research note, 2026-11-11. Development pilot only; no frozen hypothesis was tested.

**Sources:** branch `step15-split`, commit ee59b78, `src/step15/pilot.py`,
`results/step15/pilot/` (24 JSON files). Seeds: iqp4 10–13, lcm and ising4 10–11. These are the
step 14 pilot seeds. N ∈ {1e4, 3e4, 1e5}. All 24 jobs exited 0.

**What was tried.** The mid-term report recommended a split-sample gate:
- fit G on half A of the samples;
- score split_excess = ‖f_G(A) − f̂_B‖² − floor_B, where floor_B = Σ(1 − f̂_B²)/(N/2).

This is an unbiased estimate of G's true residual. The aim was to stop the step 14 gate from going
blind at N = 1e4, where G fits the noise.

## 1. Results

**split_excess tracks the truth.** It matches r_true_A, the residual of the half-A fit against the
exact moments, within about 10% on out-of-family instances. For example, lcm s10 at N = 3e4 gives
0.603 against 0.592. The estimator works as designed.

**At τ = 1e-2 it picks nothing.** On iqp4 the half-sample fit has r_true_A of
- 0.08–0.12 at N = 1e4;
- 0.028–0.041 at N = 3e4;
- 0.010–0.015 at N = 1e5.

That is at or above τ. Halving N makes G itself worse, so an absolute τ has no power at any N
tested.

**A threshold relative to the noise floor separates the families only at N ≥ 3e4.** The table
gives split_excess / floor_B:

| | iqp4 | lcm + ising4 |
|---|---|---|
| N = 1e4 | 0.69–1.82 | 1.40–4.62 (**overlaps**) |
| N = 3e4 | 0.46–0.96 | 2.34–14.7 |
| N = 1e5 | 0.82–1.75 | 6.6–98 |

**Within iqp4 it does not rank R.** The seed with the worst R has the *smallest* split excess at
both N = 3e4 and N = 1e5 (s10: R = 1.09 and 1.46). The gate can act as a family classifier only.
It cannot pick the iqp4 seeds on which G wins.

## 2. Reading

- At N = 1e4 the bottleneck is not the gate. Step 14 reported an always-IQP median R of 0.99 at
  N = 1e4, so the advantage itself is gone there. A better gate cannot recover an advantage that
  is not in the data. The split gate also overlaps across families at 1e4, so it is less safe than
  the in-sample gate, which picked 0/40.
- At N ≥ 3e4 the step 14 in-sample gate already separates the families on these seeds. Its excess
  is −0.019 to −0.014 on iqp4 and +0.10 to +0.56 out of family. The split gate adds nothing there,
  and it costs a second G fit.

**Decision.** No frozen grid for the split gate; the direction is dropped. The open quantitative
question is where, between 1e4 and 1e5, the advantage disappears. On these pilot seeds at
N = 3e4, the always-IQP R values are 1.09, 0.78, 0.44 and 0.53 (3 of 4 below 1).

The next step therefore tests the step 14 gate, unchanged, at N = 3e4 on fresh seeds (step 16).
