# Step 2: the recoverability / completion-room boundary in angle scale σ (qgen-practical)

Status: draft for user approval, 2026-11-06. Step 1 ended by its kill rule (amendment 1 P1′
and P6′ FAIL 5/5, `diagnostics/step1_amend1/SUMMARY.md` on `step1-synthetic`). This step asks
a **new, narrower question**. It is not a repair of step 1.

## Project

Measure, as a function of the target IQP's angle scale σ, three things on the same targets:

1. **Recoverability:** can an IQP fitted to the exact order-≤3 moments reach the target, from
   a small-angle start?
2. **Completion room:** how much of the target lies beyond what MaxEnt(3) explains, measured
   by D3 = KL(p ‖ MaxEnt3(p)).
3. **Classical-easiness proxies:** Clifford distance, collision ratio, and the fraction of
   high-order Walsh weight.

The question is whether there is a **window** of σ where the IQP is both recoverable and has
room for a completion gap. Step 1's evidence suggests there is none: recovery fails at
σ = 0.4, and small σ is near-identity. This step measures that instead of assuming it.

The deliverable is **one boundary figure, a table, and a summary**. It is **not** a new model
or selector, not finite-sample results, and not evidence of advantage. n = 12 is trivially
simulable, so the proxies are proxies only.

## Evidence (do not re-derive; act on it)

| Source | Finding |
|---|---|
| Step 1 FM2 diagnostics (σ = 0.4) | Generic 298-generator IQP: 0/50 small-angle restarts reach the truth. Starting near the truth works only within ~0.01 per angle. `least_squares` is also stuck. |
| Step 1 amendment 1 (σ = 0.4) | The small-angle NNLS selector fails: the second-order expansion does not hold (NNLS residual 0.69–0.99). |
| Step 1 amendment 1 test (σ ≈ 0.05) | The NNLS **ranking** of the true generators is perfect. The small-angle expansion holds there. |

So, interpreted: recoverability is good at small σ and bad at σ = 0.4. Where it breaks, and
how that compares with where completion room appears, is unknown.

## Design

- **Targets.** The `biased` layout from step 1 (target seed s fixes 12 one-body terms, 18
  pairs and 8 triples) with θ = σ·z.
  - z ~ N(0, 1) is drawn once per seed and **reused across σ**, so each seed traces a path in σ.
    This matters: independent draws per σ would add noise to every curve.
  - σ ∈ {0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6}; seeds 0–4; n = 12; **N = inf only**.
- **Fits.** Each uses 10 restarts, init N(0, 0.05²), and L-BFGS-B with the step 1 settings.
  - **O (oracle support):** the IQP restricted to the target's own 38 generators. This is an
    *oracle* by design. It isolates the landscape from generator selection, and must never be
    reported as a practical method.
  - **G (generic):** the step 1 generic 298-generator IQP (`--gens generic`).
  - **MaxEnt(3):** as in step 1. It gives D3 and R.
- **Per (σ, seed), record** in `results/step2/sigma_<σ>/seed_<s>/metrics.json`:
  - for both O and G: best residual, number of restarts reaching ≤ 1e-10, `success` (any
    restart ≤ 1e-10), and R = G_iqp/G_maxent (from step 1's `metrics.py`) when the fit
    succeeds;
  - D3;
  - `hi_order_frac` = Σ_{|A|≥4} f_A² / Σ_{|A|≥1} f_A² for the target;
  - the target's collision ratio;
  - the Clifford distance median of the target angles;
  - `versions`.
- **Reuse, do not rewrite.** Import `src/step1` (IQPModel with `gens`, MaxEnt, `metrics`,
  `bits`, `walsh`, `targets.iqp_distribution`). Put the new code in `src/step2/sweep.py` only.
  Do not edit `src/step1/`. Step 1's results are a closed record.
- Leave a stub `pauli_path_tv(theta, gens, max_weight)`, a classical low-weight Pauli-path
  sampler proxy for a later step. **Raise NotImplementedError; do not implement it.**

## Hypotheses (frozen when this file is committed)

| ID | Statement | Type |
|---|---|---|
| H1 | O succeeds on ≥ 4/5 seeds at σ = 0.05 | **Kill.** If it fails, the fitting machinery itself is broken at its easiest point. Stop and show traces. |
| H2 | The O success count is non-increasing in σ, with at most one violation over the grid | Expectation |
| H3 | The median D3 increases with σ, with at most one violation | Expectation |
| H4 | At every σ, G succeeds on no more seeds than O | Expectation (an oracle support should only help) |
| H5 | The main question. Let σ_rec = the largest σ where O succeeds on ≥ 4/5 seeds, and σ_room = the smallest σ where median D3 ≥ 1e-2 (the threshold is a guess, frozen now). **We expect "no window": σ_rec < σ_room.** | Main result; **both outcomes are reported** |

The summary must also give the curve shapes, so that the conclusion does not rest on the 1e-2
threshold alone.

## Artifacts

All figures as PNG (150 dpi) and PDF, readable without color.
1. `figures/step2/boundary`:
   - x axis: σ (log scale);
   - left y axis: success fraction of O and G (seeds out of 5);
   - right y axis: median D3 with an IQR band (log scale);
   - vertical lines at σ_rec and σ_room. This is the direct evidence for H5.
2. `figures/step2/proxies`: hi_order_frac, collision ratio and Clifford distance median
   against σ (median with IQR).
3. `results/step2/table.csv` (one row per run) and `results/step2/SUMMARY.md`. The summary
   marks H1–H5 as PASS or FAIL with the numbers, and contains verbatim: "Oracle-support
   fits are a diagnostic of the landscape, not a practical method; n = 12 proxies are not
   hardness evidence."

## Budget

- Time O and G at σ = 0.4, seed 0. Write `results/step2/PROJECTION.json` as
  `{"projected_hours": h, "runs": 35}`.
- `python -m src.step2.sweep --all` refuses to start without `BUDGET_OK`. Only the user
  creates it.
- If the projection is over 2 h, cut in this order: (1) G restarts 10 → 3, (2) drop σ = 0.15.
  Never cut O, and never cut σ = 0.05 (H1).

## Build order (stop for review at each checkpoint)

1. Merge `master` into `step1-synthetic`, to get this file, `check.sh` v3 and guard v3, both
   installed by the user. Then work on a new branch `step2-sigma` from there.
2. `src/step2/sweep.py` and `tests/test_step2.py`:
   - targets reuse z across σ (same z, scaled);
   - O at σ = 0.05, seed 0, reaches ≤ 1e-10;
   - D3 = 0 (to 1e-10) for a target that is itself MaxEnt(3).
   - Checkpoint: `check.sh --stage 4`.
3. σ = 0.05 and σ = 0.4 at seed 0 only. This is H1's first look plus the timing, giving
   PROJECTION.json. **Stop and wait for BUDGET_OK.** Checkpoint: `--stage 5`.
4. The full sweep, figures, table and summary. Checkpoint: `--stage 6`.

## Working style

The same as step 1:
- ask before installing;
- commit at each checkpoint and never push;
- mark guesses as guesses;
- show diagnostics before changing anything, and change one thing at a time;
- "done" means `bash scripts/check.sh --stage <.harness/STAGE>` exits 0;
- never edit the harness, `prereg/` or `specs/` (they are frozen), or `BUDGET_OK`;
- report a block instead of rephrasing around it;
- update `PROGRESS.md` at each checkpoint.
