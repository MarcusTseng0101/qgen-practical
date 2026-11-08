# Step 7 spec: does the iqp4 advantage come back at matched peakedness? (qgen-practical)

Status: **frozen** (user approved 2026-11-08, decision A; harness v8). Written **after step 6**
(`notes/2026-11-08_step6_findings.md`) and after a blind pre-spec scan (section 2). Once this file
is committed, the hypotheses in section 4 are frozen; any change needs a numbered amendment
written before the grid runs.

## 1. Question

Step 6 found that, at fixed σ, the window where R < 1 moves to larger σ and shrinks as n grows:
- at n = 12, R < 1 at σ = 0.175–0.2;
- at n = 14, R < 1 only at σ = 0.25;
- at n = 16, R < 1 at no σ ≤ 0.2 (σ = 0.25 was cut).

Here R = G_iqp / G_maxent3 at orders 4–6. Because the layout counts are fixed, the target also
gets more peaked with n at fixed σ.

The exploratory reading in the step 6 note is that **the advantage tracks how peaked the target is,
not σ.** Step 7 tests that reading directly. It compares n = 12, 14 and 16 at σ values chosen so
that the target's collision ratio matches.

If R < 1 returns at matched collision ratio, the step-6 shrinkage is mostly a peakedness effect of
the design. If it does not, the advantage really shrinks with n in this family.

## 2. Blind pre-spec scan (my scratchpad, `d7_blind.py`; no G, no R, no MaxEnt)

The scan computed the collision ratio 2ⁿ Σp² of `iqp4(σ, s)` for seeds 0–4 at
σ ∈ {0.15, 0.175, …, 0.35, 0.4} and n ∈ {12, 14, 16}. Matched σ values come from interpolating the
median collision ratio in log–log against σ:

| Level | n = 12 σ (step 5, seen) | median collision ratio | matched σ at n = 14 | matched σ at n = 16 |
|---|---|---|---|---|
| A | 0.15 | 561 | **0.193** | **0.231** |
| B | 0.175 | 284 | **0.213** | **0.251** |
| C | 0.2 | 134 | **0.236** | **0.274** |

At each level, the matched σ rises by about 0.02 at n = 14 and 0.04 at n = 16.

**Data already seen near these points.** In step 6:
- n = 14 gave R = 0.889 (undecided) at σ = 0.2, near level A, and 0.882 (< 1) at σ = 0.25, just
  above level C.

The predictions below are therefore partly informed. n = 16 at σ ≥ 0.23 has never been run.

## 3. Design

- **Target:** `iqp4(σ, s)` from `src/step4/targets.iqp4_target`. The layout rule is unchanged.
- **Fits:** unchanged from step 6.
  - G: the generic IQP with every weight-≤3 generator (469 at n = 14, 696 at n = 16), 3 restarts,
    never fewer. Same initial-point rule, optimizer and maxiter.
  - MaxEnt(3): ridge 1e-8.
  - Exact moments (N = ∞) only.
- **Grid:** n ∈ {14, 16} × the 3 matched σ of section 2 × seeds 0–4, i.e. **30 instances**.
- **n = 12 reference:** step 5's `iqp4` N = ∞ cells at σ = 0.15, 0.175 and 0.2 (data already seen).
  They are not rerun.
- **Statistics:** as in steps 5–6.
  - Median and IQR over 5 seeds.
  - "R < 1" means the whole IQR lies below 1, and "R ≥ 1" means the whole IQR lies at or above 1.
    Otherwise the cell is undecided.

## 4. Frozen hypotheses (iqp4, N = ∞)

| ID | Statement | Kind |
|---|---|---|
| C1 | At level B (n = 12's σ = 0.175): R < 1 at n = 14 **and** at n = 16 | prediction from the peakedness reading |
| C2 | At level C (n = 12's σ = 0.2): R < 1 at n = 14 **and** at n = 16 | prediction from the peakedness reading |
| C3 | At level A (n = 12's σ = 0.15, where n = 12 was undecided at 1.35): median R ≥ 1 at n = 14 **and** at n = 16. That is, the crossing still lies between levels A and B in collision coordinates. | prediction: the crossing is fixed in collision coordinates |
| C4 | At n = 16, median G training residual ≤ 1e-2 at levels B and C | prediction about the confound: at these σ, under-training is not the explanation |

**Reading rules, fixed now:**
- C1 and C2 both pass: the step-6 shrinkage is mostly a peakedness effect.
- C1 and C2 both fail at n = 16 while C4 passes: the advantage shrinks with n even at matched
  peakedness, and under-training does not explain it.
- C1 and C2 fail at n = 16 and C4 fails too: the result is unresolved between under-training and a
  real effect. The note must say so, not pick one.

No hypothesis is added after the grid. Anything else is labelled exploratory. D3 at each cell is
reported as exploratory, to see whether matched collision ratio also matches the completion room.

## 5. Failure modes to recognize

- **Under-training at n = 16** (seen in step 6: seed 1 had a residual of 0.03–0.18).
  - Report G's residual and its restart spread next to every R.
  - Do **not** add restarts, raise maxiter or change the optimizer.
  - If G stops at maxiter in more than 2 of 5 seeds of a cell, say so and flag that cell's R as
    possibly biased upward.
- **Run time at n = 16.** In step 6, n = 16 instances took 4–53 min, against a 400 s timing
  instance. In step 6, larger σ ran slower at n = 14 (σ = 0.25 took about 3× longer).
  - The timing step therefore uses the **largest σ** at each n (section 7).
- **Memory.** About 1.5 GiB at n = 16 in step 6. If the fit runs out of memory, stop and report. Do
  not switch to float32 or to sampling.
- **Code-path drift.** `src/step7` at n = 14, σ = 0.2, seed 0 must reproduce step 6's R (relative
  difference ≤ 1e-6) before any grid instance runs.
- **Matched σ applied wrongly.**
  - The σ values are the six bold numbers in section 2, used exactly. They are not recomputed per
    seed, and not re-rounded.
  - Each metrics.json records the target's collision ratio. The SUMMARY reports the median per cell
    against the n = 12 level.

## 6. Artifacts

- `results/step7/n_<14|16>/sigma_<σ>/seed_<s>/metrics.json`. Keys: step 6's key set plus `level`
  (A, B or C).
- `results/step7/table.csv` and `verdicts.json`: per (n, level), the median and IQR of R, G's
  residual, the collision ratio and D3, with the n = 12 rows taken from step 5.
- Figures in `figures/step7/` (png + pdf):
  - **`R_vs_collision_by_n`:** median R and IQR against the target's median collision ratio
    (log–log, x-axis reversed so that less peaked lies to the right), for n = 12, 14 and 16. Plot
    step 6's fixed-σ points faintly for context, and show a line at R = 1. This figure is the
    direct test of C1–C3: if the peakedness reading holds, the three n curves collapse.
  - **`G_vs_level_by_n`:** median G_iqp, G_maxent3 and G's residual against level, one panel per n,
    with a line at residual 1e-2 (C4).
- `results/step7/SUMMARY.md`:
  - It must open with this exact sentence: "Step 7 was designed after step 6; the n = 12 reference
    and nearby n = 14 points are data already seen; G is the generic IQP (no oracle); n ≤ 16
    proxies are not hardness evidence."
  - It must mark C1–C4 each PASS or FAIL with numbers, and apply the reading rules of section 4.
  - It must show G's residual and the collision ratio next to every R, and give the per-n timing.

## 7. Budget and stop gate

- **Timing step:**
  1. One instance at n = 14, σ = 0.236, seed 0, then one at n = 16, σ = 0.274, seed 0. These are
     the largest σ at each n.
  2. Projection = per-n time × 15.
  3. Write `results/step7/PROJECTION.json`, then stop. Only the user creates `BUDGET_OK`.
- **Budget:** 5 h. Step 6's n = 16 cells ran at about 2× their projection, and this budget allows
  for that.
- **If the projection exceeds the budget**, there is one named cut: drop **n = 16 at level A**
  (σ = 0.231). C3 is then tested at n = 14 only and is reported as FAIL-untested for n = 16.
  - Never cut seeds, restarts, n = 14 cells, or n = 16 at levels B and C.
- **If even the cut grid exceeds 5 h:** stop and report. The user decides.
- **Stop-loss while running:** if the grid's wall-clock passes 8 h, stop and report. Completed
  `metrics.json` files are kept, and the run resumes from them.

## 8. Build order

1. Branch `step7-collision` from `step6-scaling` (at 8b94e19) and merge master.
2. `src/step7/run.py` imports from steps 1–6 and **does not modify them**; steps 1–6 are closed.
   `tests/test_step7.py` must cover:
   - the n = 14, σ = 0.2, seed 0 reproduction of step 6 (R relative difference ≤ 1e-6);
   - that the run's σ table equals section 2's six values exactly;
   - that each matched σ gives a median target collision ratio within ×1.25 of its n = 12 level,
     over seeds 0–4.
3. The timing step, then PROJECTION.json, then stop.
4. After `BUDGET_OK`: the grid (in the background, resumable, with a log file), the report, the
   figures and the SUMMARY. `check.sh --stage 21` must exit 0. Commit and update PROGRESS.md.
