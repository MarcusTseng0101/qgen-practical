# Amendment 1 (post-hoc, triggered by the FM2 diagnostics): P1′ and P6′ verdict

Date 2026-11-06. Target `biased`, n = 12, N = inf, seeds 0–4, `--gens sparse` with the
amendment's own guesses (threshold 1e-3·max θ², K_MAX = 60), unchanged. The outputs are in
this folder (`biased_Ninf_seed<s>_sparse_metrics.json`). They were written here, **not** to
`results/`, because the spec-mandated selector test fails (see below), so the pipeline
never passed its stage-1 gate.

## Five seeds

| seed | K | weights 1/2/3 | support recall | precision | NNLS residual ‖Mθ² − m‖ | IQP train residual (best of 10) | 10 restarts | Jacobian sv_min | MaxEnt residual | R | gap_valid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 60 | 1/0/59 | 5/38 = 0.132 | 0.083 | 0.990 | 1.162e-1 | 1.16e-1 to 1.66e-1 | 0.216 | 6.1e-16 | 2.645 | false |
| 1 | 60 | 1/0/59 | 2/38 = 0.053 | 0.033 | 0.865 | 9.360e-2 | 9.36e-2 to 1.14e-1 | 0.263 | 1.6e-14 | 3.528 | false |
| 2 | 60 | 1/0/59 | 2/38 = 0.053 | 0.033 | 0.988 | 7.709e-2 | 7.71e-2 to 1.12e-1 | 0.278 | 7.7e-16 | 3.194 | false |
| 3 | 60 | 2/0/58 | 3/38 = 0.079 | 0.050 | 0.693 | 6.866e-2 | 6.87e-2 to 9.35e-2 | 0.326 | 1.3e-15 | 2.599 | false |
| 4 | 60 | 1/0/59 | 4/38 = 0.105 | 0.067 | 0.971 | 8.918e-2 | 8.92e-2 to 1.49e-1 | 0.253 | 1.2e-15 | 3.168 | false |

Each true layout has 38 generators: 12 one-body, 18 pairs and 8 triples.

## Verdicts (amendment 1, section 4)

- **P1′ (kill): FAIL.** The IQP training residual is ≤ 1e-10 on 0/5 seeds (it needs ≥ 4/5).
  The best residual is 6.9e-2. R < 1 also fails: 0/5 gaps are valid (it needs ≥ 4/5), and all
  five R values are > 1 anyway (2.60 to 3.53).
- **P6′ (diagnostic): FAIL.** support_recall ≥ 0.9 on 0/5 seeds (it needs ≥ 4/5). The best
  recall is 0.132.

By the kill rule ("if it fails, the sparse selector cannot even recover a target it can
represent; stop"), **step 1 ends here.** No fix was started.

## What the numbers show (no re-derivation; for the next design)

- The selector always hits the cap (K = 60) and picks almost only triples: 58–59 of 60,
  against 8 in the truth, and never a pair (the truth has 18). The NNLS residual is
  0.69–0.99, so the second-order model m ≈ Mθ² is a poor description of these moments:
  at θ ~ N(0, 0.4²) the small-angle expansion does not hold.
- The fits are well conditioned (sv_min 0.22–0.33). These are genuine local minima of a
  wrongly specified model, not the near-singular stationary points of FM2.
- Even in the regime the selector was built for (|θ| in [0.04, 0.06],
  `test_nnls_selector_recovers_small_angle_support`), the amendment's threshold fails:
  - the NNLS ranking is perfect (the 38 true generators are exactly the top 38, with a 10×
    gap to the largest spurious value);
  - but about 180 spurious candidates clear 1e-3·max, so K = 60 keeps 22 false
    generators (`nnls_diag.log`).
  - With that superset, 2 restarts reach only 5.2e-6, not 1e-10
    (`test_sparse_fit_reaches_small_residual_on_small_angle_target`).
- The MaxEnt(3) baseline fits exactly on every seed (≤ 1.6e-14). The MaxEnt side of the
  pipeline is not the problem.

## State

- `bash scripts/check.sh --stage 1` fails on the three selector-related tests. This is the
  known state: the tests were not changed, and K_MAX and the threshold were not changed.
- `maxent_proj` and `random` were not run under amendment 1.
