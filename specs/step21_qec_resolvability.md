# Step 21 spec: can 5e4 shots resolve IQP vs MaxEnt(3) on QEC data? (diagnostic)

Status: **frozen** once committed. Written after step 20. Claude chose this step under the user's
standing instruction to take the recommended option. This is a diagnostic: it adds no claim and uses only
spent data (the 16 d3_r03 and d3_r05 runs).

**Acceptance:** `python -m src.step21.run --verify` must exit 0.

## 1. Question

Steps 19 and 20 counted wins and losses on QEC runs. Two things suggest those counts may be noise:
- the same run gave R = 4.86 at one split and R = 0.69 at another;
- held-out validation agreed with the test outcome on only 10/16 runs.

Are the QEC outcomes resolved at all?

## 2. Design

**Runs.** The 16 runs `surface_code_b{X,Z}_d3_r{03,05}_center_{3_5,5_3,5_7,7_5}`, reduced as in steps 19–20
to detectors 4–19 (n = 16).

**Procedure.** Exactly step 20's `src/step20/core.fit_and_gate`, unchanged:
- train 3e4 (fit 2.4e4, validation 6e3), test 2e4;
- the fitted models are saved to `data/derived/step21/` (git-ignored).

**Splits.**
- Split seed 100, which reproduces the step 20 numbers. This is a check: R must match step 20 to 1e-6
  relative on the 8 r05 runs and the pilot's 8 r03 runs.
- Split seed 101, a second independent permutation.

**Bootstrap.**
- B = 400 resamples of the test rows, giving the 95% percentile CI of
  ΔG = G(IQP) − G(MaxEnt3), the corrected held-out gap.
- B = 400 resamples of the validation rows, giving the CI of Δv₄ = v₄(G) − v₄(MaxEnt3).
- Models are held fixed in both. Resample b uses `default_rng(21000 + b)`.

**Classification (per run and split):**
- **resolved loss** if the ΔG CI lies above 0;
- **resolved win** if it lies below 0;
- **unresolved** otherwise.

## 3. Pre-declared readings (no PASS/FAIL hypotheses)

| ID | Quantity | Reading |
|---|---|---|
| D1 | number of the 16 runs (split 100) that are unresolved | ≥ 8: QEC at 5e4 shots cannot test the claim either way; the paper reports it as unresolved, not as losses |
| D2 | sign agreement of ΔG between splits 100 and 101, over 16 runs | ≤ 11/16: the outcome depends on the split (training-sample noise), not only on test noise |
| D3 | among resolved runs, how often Δv₄'s sign matches ΔG's | reported as is |

Losses that stay resolved in both splits are real step 18-type failures, and the note lists them by name.

## 4. Artifacts

- `results/step21/<run>/split_<s>.json` and `SUMMARY.md`.
- The SUMMARY opens with: "Step 21 is a diagnostic on 16 spent QEC runs; it adds no claim; models are
  step 20's procedure, unchanged."
- `--verify` checks:
  - the spec is committed and unchanged;
  - `src/step1..20` are unchanged since 33712d6;
  - all 32 files exist with B = 400;
  - the split-100 reproduction check holds;
  - the SUMMARY sentence and D1–D3 are present;
  - `tests/test_step21.py` passes.

## 5. Budget

- 32 fits, at most 12 at a time (18 at once ran out of memory in step 20), about 3 × 65 min.
- **Stop-loss: 4 h.**

## Amendment 1 (written after the stop-loss, before any result was read)

The 4 h stop-loss fired with 27/32 fits done. Five split-101 fits were killed while running:
- bZ r03 5_3;
- bZ r05 5_3, 5_7 and 7_5;
- bX r05 7_5.

12 parallel jobs plus the bootstrap ran about 3× slower per fit than step 20.

No result had been read when this amendment was written. The amendment only completes the pre-declared
grid and changes no design choice:
- rerun exactly those 5 fits, unchanged, with `--all`, which skips existing files;
- the 5 jobs run in parallel;
- new stop-loss: 2 h.

If it fires again, the report uses the completed (run, split) pairs only, and D2 is reported over the
pairs available.
