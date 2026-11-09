# Step 9 findings: on 20 fresh seeds the IQP wins most n = 16 instances, but step 8's explanation does not survive (synthetic, n = 14–16)

Research note, 2026-11-09.

**Sources**
- Results: branch `step9-seeds`, commit e55c4b6, with `results/step9/SUMMARY.md`, `verdicts.json`,
  `table.csv`, `verify.txt` and `figures/step9/`.
- Spec: `specs/step9_fresh_seeds.md`, frozen at 24fa9bd and **designed after step 8**.
  Amendment 1 (12886dc) was committed before any grid instance ran.

**Process:**
- No harness v9 hooks or `BUDGET_OK` gate were installed. The user asked for the step to run to
  completion without further questions ("全部做完不要再問了": "finish everything, don't ask
  again"). Installing a gate needs the user's hand.
- The acceptance check is `python -m src.step9.run --verify`. It **exits 1, on one item** (the
  reproduction instance, below). It was not loosened.
- The grid took 1.31 h: 41 jobs, 16 workers × 1 thread, no failures.

**Required caveat:** seeds 10–29 are fresh. G is the generic IQP (no oracle). n ≤ 16 proxies are
not hardness evidence.

## 1. Frozen hypotheses (iqp4, N = ∞, level B: n = 14 σ = 0.213, n = 16 σ = 0.251)

| ID | Verdict | Numbers |
|---|---|---|
| H1 (n = 16: ≥ 15/20 seeds with R < 1) | **PASS** | 16/20. The sign test p ≈ 0.006 |
| H2 (n = 14: ≥ 15/20) | **FAIL** | 10/20 |
| H3 (n = 16: b(D3) < 0 and c(r4) > 0, bootstrap CIs exclude 0) | **FAIL** | b = −2.49 [−4.43, +0.007]; c = 1.49 [−0.33, 4.14] |
| H4 (c(16) − c(14) > 0) | **FAIL** | 0.13 [−1.78, 2.23] |
| H5 (n = 16: whole IQR < 1) | **PASS** | median 0.637 [0.543, 0.889] |
| H6 (n = 16: median residual ≤ 1e-2, and H1 unchanged without the residual > 1e-2 seeds) | **PASS** | median 2.7e-3; 14/16 well-trained seeds win |
| H7 (step 8's n = 16 model predicts the fresh seeds, Spearman ρ ≥ 0.5) | **FAIL** | ρ = 0.35 |

**Reading rules (spec section 4):**
- H1 passes, so at n = 16 and this peakedness the IQP beats MaxEnt(3) on most instances. Step 7's
  "undecided" at n = 16 was a 5-seed artifact.
- H3 and H7 fail, so step 8's two-mechanism model is **not** supported out of sample.
  - Only the D3 direction survives, and only marginally: b's CI reaches +0.007, and the rank
    correlation of log R with D3 is −0.42.
  - The weight-4 strength (r4) does not predict R on fresh seeds (ρ = 0.13). The "weight-4 cost
    grows with n" reading (H4) is not supported.

## 2. Reproduction flag (spec section 5; amendment 1)

**4 threads.** The build-order test failed: R = 0.400 against step 7's 0.445.
- A restart with a residual close to the best flipped which restart was selected.
- The default thread count and 1 thread reproduced the n = 14 instance, the latter to 1e-7.

**1 thread at n = 16.** The reproduction instance still differs from step 7 by **6.0e-3** in R
(0.39125 against 0.39362). It fails the 1e-6 tolerance, so every n = 16 R is flagged.

**What the flag does to H1:**
- 16/20 seeds have R < 1 − 0.006, so the observed drift changes no sign.
- 15/20 have R < 0.9. H1's threshold therefore still holds under the 10% restart-selection
  sensitivity seen at n = 14.
- The seeds within 10% of 1 are seed 10 (1.036), seed 15 (1.004) and seed 26 (0.919).

**General lesson.** The per-instance R of the generic IQP is only reproducible to about 1–10%
across BLAS thread counts. G's selection rule (lowest training residual) chooses between restarts
whose residuals are nearly equal but whose orders 4–6 differ. Single-instance R values near 1
should not be read as signs. Counts over many seeds should.

## 3. The n = 14 surprise (exploratory)

At the matched level, n = 14 did *worse* than n = 16: median R 0.976 [0.579, 1.54] against 0.637.
Paired by seed:
- 10 seeds win at both n;
- 6 lose at n = 14 but win at n = 16;
- none go the other way.

Two things contribute:

- **Under-training at n = 14.**
  - G's residual is above 1e-2 in 8/20 seeds, and 7 of those 8 lose (R = 1.47–1.76).
  - Among the 12 well-trained seeds, 9 win: exactly ⌈0.75·12⌉.
  - No restart hit maxiter. All stopped on the relative-reduction criterion, so these are poor
    local minima, not truncated runs.
  - log R correlates with the residual: ρ = 0.68 at n = 14 and 0.48 at n = 16.
- **The level match did not transfer to fresh seeds at n = 14.**
  - σ = 0.213 was matched using seeds 0–4's median collision ratio (284).
  - The fresh n = 14 seeds have median collision ratio 479 and median D3 0.24, so they are more
    peaked with less room.
  - At n = 16 the fresh seeds are near the target (319) and have D3 0.33.

Step 7's n = 14 level-B cell (R < 1, 0.870) was therefore partly a lucky 5-seed draw.

## 4. What steps 5–9 add up to now

- On IQP-like but misspecified targets (`iqp4`) at moderate peakedness, the generic weight-≤3
  IQP completes orders 4–6 better than MaxEnt(3) **on most instances, at n = 16 as well**: 16/20,
  median R ≈ 0.64.
  - This is the cleanest positive result of the project so far, on fresh seeds with a pre-frozen
    sign test.
- The advantage is **instance-dependent, and for this generic IQP the dependence is largely an
  optimization question**:
  - losers cluster where G trains poorly (n = 14, 7 of 8 high-residual seeds lose);
  - per-instance R is sensitive at 1–10% to which restart is selected.
- No simple target feature predicts which instances lose. The weight-4 share does not; D3 does
  weakly. Step 8's story was overfit to 5 seeds.
- The n-trend is not settled. n = 16 looked better than n = 14 here, but n = 14 suffered more
  under-training and drifted off the intended peakedness. Neither n alone says the advantage grows
  or shrinks.

## 5. Candidate next steps (not decided)

- **Separate the optimizer from the model.** Rerun the n = 14 losers with more restarts, and
  compare against the current 3-restart rule. If R < 1 then returns, the n = 14 failure is
  under-training. This changes the method, so it needs its own spec.
- **A selection rule that is less fragile than "lowest residual"**, for example averaging the
  completion over restarts within 10% of the best residual. Pre-register it before use.
- **Per-seed σ matching** (hitting the collision ratio per instance), so that fresh seeds land on
  the intended peakedness.
- The **latent-class mixture baseline** and the **real-data D3 probe** are still open. They decide
  practical relevance.
