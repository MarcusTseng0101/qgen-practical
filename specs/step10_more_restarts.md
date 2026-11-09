# Step 10 spec: is step 9's n = 14 failure under-training? (qgen-practical)

Status: **frozen** (user approved 2026-11-09, decision A). Written **after step 9**
(`notes/2026-11-09_step9_findings.md`). Once this file is committed, section 3 is frozen. Any
change needs a numbered amendment, written before the runs.

**Harness note.** As in step 9, no hook or `BUDGET_OK` is installed. The run is small, about 15
minutes. The acceptance check is `python -m src.step10.run --verify`, which must exit 0, and its
raw output goes into the SUMMARY.

## 1. Question

In step 9, n = 14 at level B (σ = 0.213) won only 10/20 fresh seeds, so H2 failed. G's training
residual was above 1e-2 in 8 seeds, and 7 of those 8 lost. All restarts stopped on the
relative-reduction criterion, which means poor local minima, not truncation.

Step 10 asks: if G gets **10 restarts instead of 3**, does n = 14 win most instances?

**This changes the method.** "G with 10 restarts" is a different, stronger optimizer budget. Its
results are reported as such. They do not replace the verdicts of steps 5–9.

**Design choice.** All 20 seeds are rerun, not just the 10 losers.
- Rerunning only the losers would be selection on the outcome.
- A winner can also flip to a loss: more restarts may pick a restart with a lower residual but a
  worse completion.

## 2. Design

- **Instances:** n = 14, level B, σ = 0.213 (exact), seeds 10–29, `iqp4`, N = ∞.
- **Fit:** `src/step6/run.run_instance(14, 0.213, seed, g_restarts=10)`, imported unchanged.
  - The inits are drawn in order from `default_rng(seed)`, so restarts 0–2 are exactly step 9's
    three restarts. The 10-restart run is a superset.
  - The selection rule is unchanged: the lowest training residual.
  - MaxEnt(3) is unchanged, so G_maxent3 equals step 9's.
- **Threads:** 1 BLAS / OpenMP thread per worker (step 9 amendment 1), and up to 16 workers.
- **Check:** for every seed, restarts 0–2 must reproduce step 9's restart residuals to a relative
  difference of 1e-6. Otherwise that seed is flagged.

## 3. Frozen hypotheses

| ID | Statement | Kind |
|---|---|---|
| K1 | With 10 restarts, at least 15 of 20 seeds give R < 1 at n = 14 (same threshold as step 9's H2) | primary |
| K2 | With 10 restarts, at most 2 of 20 seeds have a best training residual above 1e-2 (step 9: 8 of 20) | does more search fix the training |
| K3 | Of step 9's 10 n = 14 losers (seeds 10, 11, 13, 14, 15, 16, 17, 19, 24, 28), at least 6 give R < 1 | losers are rescued |
| K4 | Of step 9's 10 n = 14 winners, at most 1 flips to R ≥ 1 | more restarts do not create new losses |

**Reading rules, fixed now:**
- **K1 and K2 pass:** step 9's n = 14 failure was under-training. With enough search, the generic
  IQP wins most n = 14 instances at this level.
- **K2 passes but K1 fails:** better training does not rescue n = 14. Those losses are real under
  this model.
- **K2 fails:** 10 restarts do not fix the optimization, and the question stays unresolved.
- **K4 fails:** the lowest-residual selection rule is unreliable for completion. That is direct
  motivation for the restart-selection candidate.

**Exploratory, reported but not tested:**
- Within each instance, across its 10 restarts: the Spearman correlation between training residual
  and G_iqp.
- How often the lowest-residual restart is also the lowest-G restart.
- The R a "best of 3" rule would give against the "best of 10" rule.

## 4. Artifacts and acceptance

- Results:
  - `results/step10/seed_<s>/metrics.json`, with step 9's key set plus `step9_R`,
    `step9_best_restart` and `restarts_0_2_match`;
  - `results/step10/table.csv`, `verdicts.json` and `SUMMARY.md`;
  - `figures/step10/R_3_vs_10` (png + pdf).
- The SUMMARY opens with: "Step 10 was designed after step 9; it changes G's restart budget from 3
  to 10 at n = 14 only; G is the generic IQP (no oracle); n ≤ 16 proxies are not hardness
  evidence."
- `--verify` checks:
  - the spec is committed and unchanged;
  - `src/step1..9` are unchanged since e55c4b6;
  - 20 metrics files exist, with exact σ, `G_n_restarts` = 10 and `restarts_0_2_match` true;
  - the SUMMARY sentence and K1–K4 are marked;
  - the figure exists;
  - the tests pass.

## 5. Budget

At 1 thread, an n = 14 restart takes about 0.3–0.5 min, so one seed is about 5 min. 20 seeds on
16 workers take about 10–15 min.

**Stop-loss:** 1 h.
