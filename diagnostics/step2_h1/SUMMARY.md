# Step 2, H1: the oracle-support IQP at σ = 0.05 (diagnostic)

Date 2026-11-06. Target: θ = 0.05·z on the step-1 `biased` layout, seeds 0–4, n = 12,
N = inf. The fit is O, the IQP restricted to the target's own 38 generators: 10 restarts,
init N(0, 0.05²), step-1 L-BFGS-B settings, all unchanged. Diagnostic only: nothing was
written to `results/`, and `src/` and the tests are unchanged.

`h1_all_seeds.py` replays the 10 restarts of `fit_moments` (same init draws, same options)
so that every restart's solution is kept. Its best residual matches `fit_moments` on every
seed. Raw output: `h1_all_seeds.json` / `.log`, `spread_table.log`. The seed-0 single-run
diagnostic is `o_sigma005_seed0.*`.

## (1) H1 verdict

| seed | best residual | restarts ≤ 1e-10 | success | wrong-sign pairs (of 18) | wrong-sign triples (of 8) | D3 |
|---|---|---|---|---|---|---|
| 0 | 1.05e-6 | 0/10 | no | 8 | 0 | 7.65e-3 |
| 1 | 9.06e-6 | 0/10 | no | 8 | 3 | 8.41e-3 |
| 2 | 4.41e-6 | 0/10 | no | 7 | 5 | 4.98e-3 |
| 3 | 6.51e-6 | 0/10 | no | 7 | 3 | 3.74e-3 |
| 4 | 1.72e-6 | 0/10 | no | 7 | 4 | 4.62e-3 |

The sign columns are for the best restart.

**H1 (kill): FAIL.** O succeeds on 0/5 seeds; H1 needs ≥ 4/5. By the stop rule, step 2
ends here. No fix was started.

How signs are counted. The distribution is exactly invariant under θ_g → (−1)^{|g∩B|} θ_g
for any bit set B, and under θ → −θ. One-body signs are therefore pure gauge. For each global
sign I choose the unique B that makes all 12 one-body signs match θ*, then count wrong signs
on pairs and triples, keeping the global sign with fewer.
- The first seed-0 diagnostic minimized the total over all B. That has ties between gauges
  that split the mismatches differently between pairs and one-body terms, so its pair count
  depended on tie-breaking.
- The fixing above has no ties. It reproduces the seed-0 result: 8 mismatches, all pairs.

The magnitudes match closely (seed 0: within 3.6e-3). Every restart, on every seed, has
5–9 wrong-sign pairs. The minima are well conditioned (seed 0: Jacobian rank 38/38,
sv_min 8e-3). So these are discrete wrong-sign basins, not FM2's near-singular points.

## (2) Completion spread across the 50 restart solutions

G_iqp = mean over levels 4–6 of the mean squared parity error against the exact target. For
the true parameters, G = 0 exactly on every seed.

| seed | G_iqp min (its residual) | G_iqp median | G_iqp max (its residual) | residual range | G_maxent | G_uniform | solutions with residual < 1e-5 | G_iqp spread among them | spread / G_maxent | min G_iqp / G_maxent |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.32e-8 (1.5e-6) | 2.24e-8 | 3.18e-8 (3.7e-6) | 1.1e-6 to 4.2e-6 | 1.70e-7 | 0.821 | 10/10 | 1.86e-8 | 0.1 | 0.1 |
| 1 | 1.63e-7 (9.1e-6) | 1.85e-7 | 2.72e-7 (2.0e-5) | 9.1e-6 to 2.0e-5 | 2.75e-7 | 0.793 | 1/10 | n/a (one solution) | n/a | 0.6 |
| 2 | 4.26e-8 (4.4e-6) | 1.03e-7 | 1.29e-7 (8.5e-6) | 4.4e-6 to 8.5e-6 | 1.10e-7 | 0.800 | 10/10 | 8.61e-8 | 0.8 | 0.4 |
| 3 | 7.20e-8 (6.5e-6) | 2.87e-7 | 5.17e-7 (4.2e-5) | 6.5e-6 to 4.2e-5 | 6.92e-8 | 0.837 | 4/10 | 2.71e-8 | 0.4 | 1.0 |
| 4 | 2.53e-8 (2.5e-6) | 6.73e-8 | 1.38e-7 (1.2e-5) | 1.7e-6 to 1.2e-5 | 7.99e-8 | 0.814 | 9/10 | 7.70e-8 | 1.0 | 0.3 |

**Answer.** Among solutions with residual < 1e-5, the spread of G_iqp is 0.1–1.0 × G_maxent
on the 4 seeds where it is defined. Seed 1 has only one such solution. So the spread is of
the same order as G_maxent, or smaller, and never larger. On every seed it is about six
orders of magnitude below G_uniform.

Other observations (no re-derivation, for the record):
- G_iqp tracks the training residual closely: corr(log residual, log G_iqp) = 0.96 over all
  50 solutions, with G_iqp / residual between 0.007 and 0.021. The completion error of these
  wrong-sign solutions is mostly their training misfit, carried up to orders 4–6.
- The best wrong-sign solution completes better than MaxEnt(3) on 4/5 seeds
  (min G_iqp / G_maxent = 0.1–0.6), and equally on seed 3 (1.0). This is not an R result:
  these fits fail the 1e-10 success rule, and the spec defines R only for successful fits.
  It does say that at σ = 0.05 the distinction H1 tests (exact versus ~1e-6 residual) is
  much finer than the completion differences in play.
- D3 at σ = 0.05 is 3.7e-3 to 8.4e-3, already close to the frozen σ_room threshold of 1e-2.
