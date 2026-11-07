# Step 6 spec: does the iqp4 advantage window survive larger n? (qgen-practical)

Status: **frozen** (user approved 2026-11-07, decision A; harness v7). Written **after step 5**
(`notes/2026-11-07_step5_findings.md`) and after a blind pre-spec scan (section 2). Once this file
is committed, the hypotheses in section 4 are frozen; any change needs a numbered amendment
written before the grid runs.

## 1. Question

At n = 12, the generic weight-≤3 IQP beats MaxEnt(3) at completing orders 4–6 on `iqp4` (truth
outside its family) only in a narrow window:
- R < 1 at σ = 0.175–0.2;
- σ\* = 0.160;
- undecided at σ = 0.25.

Step 6 asks whether that window **persists, moves or closes** at n = 14 and n = 16, with the
target family and the method unchanged.

## 2. Blind pre-spec scan (my scratchpad, `d6_blind.py`; no G, no R computed)

`iqp4(σ, seed 0)` keeps the same layout counts at every n: n singles, 18 pairs, 8 triples and 6
weight-4 generators.

| n | σ | generators | D3 | collision ratio | MaxEnt projection time |
|---|---|---|---|---|---|
| 12 | 0.15 / 0.2 / 0.25 | 44 | 0.279 / 0.385 / 0.398 | 627 / 159 / 33 | ≤ 0.3 s |
| 14 | 0.15 / 0.2 / 0.25 | 46 | 0.268 / 0.387 / 0.411 | 2318 / 560 / 109 | 3.5–13 s |
| 16 | 0.2 | 48 | 0.346 | 1917 | 17 s |

Two consequences:
- **D3 at fixed σ is nearly n-independent.** The completion room is comparable across n, so
  comparing σ\* across n is meaningful.
- **The collision ratio grows about 3.5× per +2 bits at fixed σ.** Because the layout counts are
  fixed, larger n makes the target *more* peaked, which moves it away from anticoncentration.
  This is a known limit of the design, not a quantity under test. It must be reported next to
  every result.

## 3. Design

- **Target:** `iqp4(σ, s)` from `src/step4/targets.iqp4_target`, called with n = 14 and n = 16.
  The layout rule is unchanged, so the layout counts stay fixed.
- **Fits** (unchanged):
  - G: the generic IQP with every weight-≤3 generator (469 at n = 14, 696 at n = 16), 3 restarts,
    never fewer. Same initial-point rule.
  - MaxEnt(3): ridge 1e-8.
  - Exact moments (N = ∞) only.
- **R** = G_iqp / G_maxent3 at orders 4–6, both measured against the exact target, at G's
  lowest-residual restart.
- **Grid:** n ∈ {14, 16} × σ ∈ {0.125, 0.15, 0.175, 0.2, 0.25} × seeds 0–4, i.e. **50
  instances**.
- **n = 12 reference:** step 5's `iqp4` N = ∞ cells (data already seen); they are not rerun.
- **Statistics and σ\*:** exactly as in step 5, including amendment 1's rules for an undefined
  crossing. σ\* is the first downward crossing of median R through 1, interpolated linearly in
  log R against log σ.

## 4. Frozen hypotheses (iqp4, N = ∞)

| ID | Statement | Kind |
|---|---|---|
| S1 | At n = 14 and at n = 16, R < 1 at σ = 0.2 (IQR entirely below 1) | prediction: the window persists |
| S2 | σ\*(n = 14) and σ\*(n = 16) are both defined and both lie in [0.135, 0.185], i.e. within ±0.025 of n = 12's 0.160 | prediction, from D3 being n-independent at fixed σ |
| S3 | At n = 14 and at n = 16, R < 1 at σ = 0.175 | prediction: the window does not narrow |
| S4 | At n = 16, max/min of median G_iqp over the 5 σ values ≤ 3 (the floor stays flat, as in step 5's Q2) | prediction |

No hypothesis is added after the grid. Anything else is labelled exploratory.

## 5. Failure modes to recognize

- **FM2 or under-training at larger n.** G has more parameters and a larger state space.
  - Symptom: G's training residual ≫ 1e-2, or a restart spread above 10×.
  - Report it next to the affected cell. Do **not** add restarts, raise maxiter or change the
    optimizer. If G stops at maxiter in more than 2 of 5 seeds of any cell, say so and flag that
    cell's R as possibly biased upward.
- **Memory.** At n = 16, a 2^16 × 696 float64 matrix is about 365 MB.
  - If the fit runs out of memory, stop and report.
  - Do not switch to float32 or to sampling: that would change the method.
- **MaxEnt maxiter.** Report the count and the residuals. Do not change the ridge.
- **Code-path drift.** `src/step6` at n = 12, σ = 0.2, seed 0 must reproduce step 5's R
  (relative difference ≤ 1e-6) before any n > 12 run.

## 6. Artifacts

- `results/step6/n_<14|16>/sigma_<σ>/seed_<s>/metrics.json`. Keys: the step-5 key set plus `n`,
  `G_n_params` and `G_restart_nit`.
- `results/step6/table.csv` and `verdicts.json`: σ\* and sign-change counts for n = 12 (taken from
  step 5), 14 and 16.
- Figures in `figures/step6/` (png + pdf):
  - **`R_vs_sigma_by_n`:** median R and IQR against σ (log–log), for n = 12, 14 and 16. Show a line
    at R = 1 and a band [0.135, 0.185] for S2. This figure is the direct test of S1–S3.
  - **`G_vs_sigma_by_n`:** median G_iqp, G_maxent3 and G's residual against σ, one panel per n.
  - **`collision_vs_n`:** collision ratio of the target against n at each σ (the caveat of
    section 2).
- `results/step6/SUMMARY.md`:
  - It must open with this exact sentence: "Step 6 was designed after step 5; the n = 12 reference
    is data already seen; G is the generic IQP (no oracle); n ≤ 16 proxies are not hardness
    evidence."
  - It must mark S1–S4 each PASS or FAIL with numbers, show G's residual and the collision ratio
    next to every R, and give the per-n timing.

## 7. Budget and stop gate

- **Timing step:**
  1. One instance at n = 14, σ = 0.2, seed 0, then one at n = 16, σ = 0.2, seed 0.
  2. Projection = per-n time × 25.
  3. Write `results/step6/PROJECTION.json`, then stop. Only the user creates `BUDGET_OK`.
- **Budget:** 3 h.
- **If the projection exceeds the budget, cut in this order** (the n = 16 cells first, because
  they cost the most):
  1. drop n = 16 at σ = 0.25;
  2. then drop n = 16 at σ = 0.125.

  σ\* at n = 16 stays defined as long as σ = 0.15 is above 1 and σ = 0.175 is below. Never cut
  seeds, restarts, n = 14 cells, or σ ∈ {0.15, 0.175, 0.2} at n = 16.
- **If even the cut grid exceeds 3 h:** stop and report. The fallback is n = 14 only, and it needs
  a user decision.

## 8. Build order

1. `src/step6/run.py` imports from steps 1–5 and **does not modify them**; steps 1–5 are closed.
   `tests/test_step6.py` must cover:
   - the n = 12 reproduction of step 5 at σ = 0.2, seed 0;
   - the G generator count at n = 14 (469) and n = 16 (696);
   - that `iqp4_target` at n = 14 has 14 + 18 + 8 + 6 generators.
2. The timing step, then PROJECTION.json, then stop.
3. After `BUDGET_OK`: the grid, the report, the figures and the SUMMARY. `check.sh --stage 18` must
   exit 0. Commit and update PROGRESS.md.
