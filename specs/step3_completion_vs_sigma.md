# Step 3: completion ratio R as a function of angle scale σ (qgen-practical)

Status: draft for user approval, 2026-11-06. **Designed after seeing** the step 1 and step 2
diagnostics (`notes/2026-11-06_steps1-2_findings.md`). Every report must say so. The
hypotheses in section 4 are frozen when this file is committed.

## Project

On IQP-shaped targets, and on their paired max-ent controls, measure how well an IQP fitted to
the exact order-≤3 moments completes orders 4–6, compared with MaxEnt(3), across σ. Report
this next to the completion room D3 and the easiness proxies.

The deliverable is **one figure set, a table and a summary**. It is **not**:
- an exact-recovery test (that was steps 1–2);
- finite-sample results;
- evidence of advantage (n = 12, IQP-shaped targets).

## Changes from step 2 (and why)

- **No exact-recovery gate.** R is computed for the **lowest-training-residual restart**
  of each fit, always.
  - Why this is acceptable: misfit at orders ≤3 can only *raise* G_iqp at orders 4–6.
    Empirically, G tracks the residual (corr 0.96, step 2). So it biases R against the IQP,
    and R < 1 despite misfit is conservative.
  - The training residual is still reported next to every R.
- **Paired negative control at every σ.** `maxent_proj(σ, s)` = MaxEnt3 of the target
  `iqp(σ, s)`: the same order-≤3 moments, with a max-ent completion. At N = inf both models
  see identical inputs on the pair; only the truth above order 3 differs.

## Design

- **Targets:**
  - `iqp(σ, s)`: the step-2 construction, with the biased layout and z reused across σ.
    Import it from `src/step2/sweep.py`; do not re-implement it.
  - `maxent_proj(σ, s)`, as above.
  - σ ∈ {0.05, 0.1, 0.2, 0.3, 0.4, 0.6}; seeds 0–4; n = 12; N = inf.
  - That is 6 × 5 × 2 = 60 target instances.
- **Fits per instance:** each uses 10 restarts, init N(0, 0.05²), and the step-1 L-BFGS-B
  settings.
  - **O:** the IQP on the `iqp(σ, s)` layout. For `maxent_proj`, use the layout of its
    paired `iqp` target. It is an oracle by design; this is a landscape study, not a method.
  - **G:** the generic 298-generator IQP.
  - **MaxEnt(3).**
- **Record per instance** in `results/step3/<target>/sigma_<σ>/seed_<s>/metrics.json`:
  - for both O and G: G at the best restart, R, the training residual, and all 10 restart
    residuals and G values;
  - G_maxent, G_uniform;
  - D3 of the `iqp` target (the same number appears in both members of the pair);
  - hi_order_frac, collision ratio, Clifford distance median of the target angles;
  - `versions`.
- **Code:** `src/step3/run.py` only. Import `src/step1` and `src/step2`; never edit them.
  Both are closed records.

## Statistics

- Median and IQR over the 5 seeds.
- "R < 1 at σ" means the IQR lies entirely below 1. "R ≥ 1 at σ" means the IQR lies
  entirely at or above 1.
- Otherwise the result is "undecided" at that σ, and is reported as such.

## 4. Hypotheses (frozen at commit)

| ID | Statement | Type |
|---|---|---|
| K1 | `maxent_proj`, fit O: R ≥ 1 at every σ | **Kill.** If it fails, the pipeline favors the IQP. Stop; nothing else is interpretable. |
| K2 | `maxent_proj`, fit G: R ≥ 1 at every σ where G's training residual is ≤ G_maxent of the paired `iqp` target | Kill (the same logic for G) |
| C1 | `iqp`, fit O, σ = 0.05: R < 1 | **Confirmatory of data already seen** (step 2 diagnostic). It is not a prediction, and is reported as a replication. |
| M1 | `iqp`, fit O: the median R is non-decreasing in σ, with at most one violation | Expectation |
| M2 | `iqp`: at every σ, the median R_G ≥ the median R_O | Expectation |
| M3 | The main question. Window W = {σ : `iqp` R_O < 1 **and** the median D3 ≥ 1e-2}. **We expect W ⊆ {0.1}**: at most one grid point, at the small-σ edge. | Main result. Report W exactly, whatever it is. |

The 1e-2 threshold is carried over from step 2 (a guess). The summary must also show the
curves, so that M3 does not rest on the threshold alone.

## Artifacts

All as PNG (150 dpi) and PDF, readable without color.
1. `figures/step3/ratio_vs_sigma`:
   - median R with an IQR band against σ (log x axis) for four lines: O on `iqp`, G on `iqp`,
     O on `maxent_proj`, G on `maxent_proj`;
   - a reference line at R = 1;
   - the region W shaded.
   - This is the evidence for K1, K2, M1, M2 and M3.
2. `figures/step3/room_and_proxies`: D3, hi_order_frac, collision and Clifford median
   against σ.
3. `figures/step3/residual_vs_G`: a scatter of log training residual against log G over all
   restarts, colored by σ. It checks the "misfit is conservative" argument in each regime.
   **If the correlation breaks down at large σ, say so prominently**; the conservative
   argument would then not hold there.
4. `results/step3/table.csv` and `results/step3/SUMMARY.md`. The summary marks K1, K2, C1,
   M1, M2 and M3 as PASS or FAIL with the numbers, and contains verbatim: "Step 3 was designed
   after the step 1–2 diagnostics; C1 replicates data already seen; oracle-support fits are a
   landscape diagnostic; n = 12 proxies are not hardness evidence."

## Budget

- Time one `iqp` and one `maxent_proj` instance at σ = 0.4, seed 0 (O, G and MaxEnt).
- Write `results/step3/PROJECTION.json` as `{"projected_hours": h, "instances": 60}`.
- `--all` refuses to start without `BUDGET_OK`.
- If the projection is over 2 h, cut in this order: (1) G restarts 10 → 3, (2) drop
  σ = 0.6.
- Never cut `maxent_proj` (K1 and K2), and never cut σ = 0.05 (C1).

## Build order

1. Merge `master` into `step2-sigma`, then `git switch -c step3-ratio`.
2. `src/step3/run.py` and `tests/test_step3.py`:
   - `maxent_proj(σ, s)` has the same order-≤3 moments as `iqp(σ, s)`, to 1e-10;
   - the O fit is identical on both members of a pair (same inputs, same seed), so their
     training residuals match to 1e-12;
   - R uses the lowest-residual restart.
   - Checkpoint: `check.sh --stage 7`.
3. σ = 0.05 and 0.4 at seed 0, for both targets, plus the timing → PROJECTION.json →
   **wait for BUDGET_OK**. Checkpoint: `--stage 8`.
4. The full grid, figures, table and summary. Checkpoint: `--stage 9`.

## Working style

The same as steps 1–2:
- ask before installing;
- commit at checkpoints and never push;
- mark guesses as guesses;
- show diagnostics before changing anything, and change one thing at a time;
- "done" means `check.sh --stage <STAGE>` exits 0;
- never edit the harness, `prereg/`, `specs/` or `BUDGET_OK`;
- report blocks instead of rephrasing around them;
- keep `PROGRESS.md` current.
