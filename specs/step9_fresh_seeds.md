# Step 9 spec: do the n = 16 advantage and the step-8 two-mechanism story hold on fresh seeds? (qgen-practical)

Status: **frozen** (user approved 2026-11-09, decision A, plus "全部做完不要再問了" ("finish
everything, don't ask again")). Written **after the step 8 diagnostic**
(`notes/2026-11-09_step8_seed_diagnostic.md`). Once this file is committed, the hypotheses in
section 4 are frozen. Any change needs a numbered amendment, written before the grid runs.

**Harness note.** No harness v9 is installed, and no `BUDGET_OK` gate exists for this step.

- Installing either needs the user's hand.
- The user asked for the step to run to completion without further questions. That instruction
  stands in for the budget approval.
- The acceptance check is `python -m src.step9.run --verify`. It must exit 0, and its raw output
  goes into the SUMMARY and the note.
- This is a weaker guarantee than a hook, and the note must say so.

## 1. Question

Step 7 left n = 16 undecided at every collision-matched level. The medians were below 1, but at
level B seeds 1 and 2 lost (R = 1.28, 1.11). Step 8 built an exploratory story on the same 45
instances:

- a strong weight-4 part (`r4`) raises G_iqp;
- low completion room (D3) lowers G_maxent3.

log R ~ D3 + r4 gave R² = 0.83 at n = 16, and the r4 coefficient grew with n.

Two problems:

- Five seeds cannot separate "the IQP usually wins at n = 16" from chance.
- The story was fit on the data it explains.

Step 9 asks both questions on **20 fresh seeds (10–29)**, whose target angles have never been
drawn.

## 2. Why the decision rule changes

The step 5–7 rule calls R < 1 only when the whole IQR is below 1. That means at least about 75% of
instances win. It describes the spread; it is not a test. More seeds estimate the 75th percentile
more precisely, but they do not make the rule easier to pass.

So:

- **The primary test is a sign test.** It asks whether more than half of the instances win.
- The IQR rule is kept as a secondary continuity row (H5), so the result lines up with steps 5–7.

## 3. Design

- **Target:** `iqp4(σ, s)` from `src/step4/targets.iqp4_target`. The layout rule is unchanged.
- **σ:** level B of step 7 exactly. n = 14 uses σ = 0.213, n = 16 uses σ = 0.251.
- **Seeds:** 10–29 (20 per n). The same seed at both n shares its angle draws (rng 100 + s and
  4000 + s), so the n = 14 and n = 16 instances are **paired** by seed.
- **Fits:** unchanged from steps 6–7. Each instance is `src/step7/run.run_instance(n, "B", seed)`,
  imported and not edited:
  - G: the generic weight-≤3 IQP (469 / 696 generators), 3 restarts, unchanged optimizer and
    maxiter;
  - MaxEnt(3): ridge 1e-8;
  - N = ∞.
- **Grid:** 40 instances. Also one **reproduction instance**: n = 16, level B, seed 0, which must
  match step 7's R (relative difference ≤ 1e-6) under the same thread settings as the grid.
- **Parallelism:** up to 8 worker processes at a time, each with BLAS / OpenMP threads set to 4.
  - This changes wall-clock time only.
  - The reproduction instance and the test (n = 14, B, seed 0 against step 7, relative difference
    ≤ 1e-6) show that it does not change the numbers.
- **Features:** computed from `target_masks` and `target_theta`, exactly as in step 8's
  `d8_seeds.py`.
  - `r4` = ‖θ_{w=4}‖ / ‖θ_{w≤3}‖. Weight-≤3 includes the singles.
  - `D3` comes from metrics.json.

## 4. Frozen hypotheses (iqp4, N = ∞, level B, seeds 10–29)

| ID | Statement | Kind |
|---|---|---|
| H1 | **n = 16:** at least 15 of 20 seeds give R < 1 (one-sided sign test against 1/2, p ≈ 0.021) | primary: does the IQP usually win at n = 16 |
| H2 | **n = 14:** at least 15 of 20 seeds give R < 1 | same at n = 14 |
| H3 | **n = 16:** in the OLS fit log R = a + b·D3 + c·r4 over the 20 seeds, b < 0 **and** c > 0. Each 95% percentile-bootstrap CI excludes 0 (2000 resamples of seeds, `default_rng(9)`). | tests step 8's two mechanisms on fresh data |
| H4 | c(n = 16) − c(n = 14) > 0. The paired bootstrap 95% CI (seeds resampled jointly at both n, 2000 resamples, `default_rng(9)`) excludes 0. | tests "the weight-4 cost grows with n" |
| H5 | **n = 16:** the whole IQR of R is below 1 (the step 5–7 rule) | continuity with step 7 (prediction: R < 1) |
| H6 | **n = 16:** the median G training residual is ≤ 1e-2, **and** H1's verdict is unchanged when seeds with residual > 1e-2 are dropped (the threshold 15 is scaled to ⌈0.75·k⌉ of the k remaining seeds) | confound: under-training does not set the verdict |
| H7 | **n = 16, out of sample:** step 8's fit, frozen here as log R̂ = 0.3558 − 6.8247·D3 + 4.6597·r4, predicts the fresh seeds with Spearman ρ(log R̂, log R) ≥ 0.5 | does the step-8 model predict new instances |

**Reading rules, fixed now:**
- H1 passes: at n = 16 the IQP beats MaxEnt(3) on most instances at this peakedness. The step-7
  "undecided" was a 5-seed artifact.
- H1 fails with at least 10 of 20 wins: n = 16 is a coin-flip-to-modest regime, not a reliable
  advantage.
- H1 fails with fewer than 10 of 20 wins: MaxEnt(3) is at least as good on most n = 16 instances.
  The step-7 medians were optimistic.
- H3 and H7 pass: the two-mechanism story is supported out of sample.
  - If H3 passes only in b or only in c, report which mechanism survived.
- If H6 fails, the H1 verdict is unresolved between under-training and a real effect. The note
  must say so.

No hypothesis is added after the grid. Everything else is labelled exploratory. Exploratory items
include the step-8 n = 14 model (log R̂ = −0.2298 − 2.6888·D3 + 2.2920·r4) and `r4_23`.

## 5. Failure modes to recognize

- **Under-training at n = 16.** Report the residual next to every R. Do not add restarts, change
  maxiter or change the optimizer.
- **Code-path or thread drift.** The reproduction instance must reproduce step 7's R to 1e-6.
  - If it does not, every n = 16 R is flagged. The SUMMARY says so.
  - Do not "fix" it by changing the fit.
- **Memory.** About 1.5 GiB per n = 16 process. 8 workers use about 12 GiB, and the machine has
  about 38 GiB free. If a worker runs out of memory, rerun that instance with fewer workers. Never
  switch to float32 or to sampling.
- **Seed cherry-picking.** All 20 seeds are reported. A failed instance is rerun, not dropped. If an
  instance cannot finish, H1 counts it as a loss for the IQP (conservative).

## 6. Artifacts

- `results/step9/n_<14|16>/sigma_<σ>/seed_<s>/metrics.json`: the step-7 key set plus `r4` and
  `r4_23`.
- `results/step9/repro_n16_B_seed0/metrics.json`.
- `results/step9/table.csv`, `verdicts.json` and `SUMMARY.md`.
  - The SUMMARY opens with: "Step 9 was designed after step 8; seeds 10–29 are fresh; G is the
    generic IQP (no oracle); n ≤ 16 proxies are not hardness evidence."
  - It marks H1–H7 each PASS or FAIL with numbers, and pastes the `--verify` output.
- `figures/step9/` (png + pdf):
  - **`R_by_seed`:** per-seed R at n = 14 and 16, paired lines, with a line at 1.
  - **`R_vs_D3_r4`:** log R against D3, coloured by r4, one panel per n, with step 8's prediction.
- `--verify` checks:
  - the spec is committed and unchanged;
  - `src/step1..7` are unchanged since 72d47b1;
  - all 40 metrics files exist, with exact n, σ, level B and ≥ 3 restarts;
  - the reproduction instance is present and passes;
  - the SUMMARY sentence and H1–H7 are marked;
  - the figures exist;
  - the tests pass.

## 7. Budget and stop-loss

- **Projection:** step 7's level-B instances took about 20 min at n = 16 and 0.7 min at n = 14,
  serially. With 8 workers, 21 n = 16 jobs and 1.3× contention, the projection is about 2 h.
- **Stop-loss:** if wall-clock passes 6 h, stop and report. Completed instances are kept, and the
  grid resumes from them.
- No cells are cut: there is one cell per n, and seeds are never cut.

## 8. Build order

1. Branch `step9-seeds` from `step7-collision` (72d47b1) and merge master. `src/step9/run.py`
   imports steps 1–7 and does not modify them.
2. `tests/test_step9.py`:
   - the n = 14, B, seed 0 reproduction of step 7 (R relative difference ≤ 1e-6), run with 4 BLAS
     threads;
   - the seed list is 10–29 and σ comes from step 7's table at level B;
   - the `r4` feature reproduces step 8's value for step-7 seed 1 at n = 16 (0.415).
3. The grid (in the background, resumable, logged), then the report, figures and SUMMARY, then
   `--verify` exit 0. Commit, and update PROGRESS.md.

## Amendment 1 (2026-11-09, written before any grid instance ran)

**What happened.** The build-order test (n = 14, B, seed 0 against step 7) **failed** with 4 BLAS
threads: R = 0.4004 against step 7's 0.4453 (relative difference 0.10).

**Cause.** At 4 threads, restart 2 converged to a different point (residual 4.28e-3 against
3.74e-3). The lowest-residual restart therefore became restart 0.
- Restart 0 has G_iqp = 2.03e-4.
- Restart 2, chosen in step 7, has 2.25e-4.

**At other thread settings:**
- the default thread count reproduces step 7 exactly;
- 1 thread reproduces it to 1e-7 (it takes 83 s against 55 s).

**Change.** Workers run with **1 BLAS / OpenMP thread**, and up to **16 workers** run at a time
(about 24 GiB at n = 16). Everything else is unchanged: the fit, the selection rule and the
hypotheses. The n = 16 reproduction instance runs under the same setting and still has to pass at
1e-6.

**What this adds (exploratory, to be reported).** The per-instance R of the generic IQP carries a
numerical sensitivity of order 10%. It comes from which restart has the lowest residual: restarts
with nearly equal residuals give different G_iqp. Instances with R within about 10% of 1 can change
sign under floating-point noise. The note must say this next to H1.
