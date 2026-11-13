# Step 25 spec: the full practical pipeline — readout mitigation + residual check + graph enlargement

Status: **frozen** once committed. Written 2026-11-14 after step 24 (notes/2026-11-13_step24_robustness.md, reading B3)
and the step 25 exploration on spent seeds (branch `step18-adversarial` `explore/step25/`). Claude chose this step under
the user's standing instruction to take the recommended option. Every number in §4 is fixed here, before any model is
fitted on the test seeds 980–993.

**Acceptance:** `python -m src.step25.run --verify` must exit 0. It is the definition of done. A FAIL hypothesis is a
result, not a reason to change the check.

## 1. Why

Step 24 showed three things:
- a coupling map with missing couplers breaks the advantage (M1 FAIL, R 2.86);
- an over-complete map is cheap (E1, R 0.46);
- readout noise needs mitigation (D1 at the threshold; mitigated 14/14).

Exploration on spent seeds:
- **Greedy gradient repair is unreliable.** Adding the pair with the largest |dL/dθ| fixed 2 of 5 seeds. On seed 970 it
  never found the dropped edges in 4 rounds. Not used.
- **The residual detects a wrong graph.** In step 24, the training residual over the noise floor was:
  - 0.27–0.83 on every correct-or-over-complete graph (56 fits, including steps 23 and 24);
  - 0.92–19.5 on every `miss` graph (14 fits).

  A threshold of 0.9 separates them on spent data. It was chosen after seeing those data, so it is a guess fixed here.
- **Mitigation at η = 5% wins on spent seeds:** R 0.28, 0.64, 0.41 on 3 seeds.

The test is the whole recipe on fresh seeds, with the departures combined as a user would meet them. It is not a test
of each piece separately; step 24 did that.

## 2. Pipeline and conditions (load-bearing details)

**Target:** `grid_iqp(seed)` (step 23), passed through independent readout flips at η (step 24 `readout_channel`).
**Training data:** N = 1e4 order-≤3 moments from `training_moments` on that noisy distribution.

**Pipeline `iqp_pipe`.** η is known, as from readout calibration.
1. Mitigate: f̃_S = f̂_S / (1 − 2η)^|S|.
2. Fit an IQP on the **given graph**'s candidates, with 20 restarts and init std 0.3 (step 23 settings).
3. Residual check. Compute the mitigated floor F = Σ_S (1 − f̂_S²) / N / (1 − 2η)^{2|S|}. If resid / F > **0.9**, refit
   on the **enlarged graph** with the same settings and keep that fit.
   - The enlarged graph is every geometrically local candidate: the 16 singles, 24 edges, 18 plaquette diagonals,
     36 triples and 9 plaquettes, 103 in all. It is defined by geometry only, with no knowledge of which couplers
     are missing.
4. Push the fitted noiseless q through the readout channel at η. Score it.

**Score:** G against the noisy data distribution (orders 4–6, exact).
**Baselines:** `me3` (MaxEnt(3)) and `me_local` (MaxEnt on the given graph's weight-≤3 masks), both fitted on the raw
noisy moments.

| Condition | Given graph | η |
|---|---|---|
| `miss02` | grid minus 2 couplers (step 24 rule, `default_rng(20_000 + seed)`) | 0.02 |
| `full02` (control) | the full grid, 85 candidates | 0.02 |
| `miss05` | grid minus 2 couplers | 0.05 |

Do not give the pipeline the target's θ, the identities of the missing couplers, or noiseless moments.

## 3. Instances

Test seeds 980–993 (14), never used. The same seeds are used in every condition (paired). 3 × 14 = 42 jobs. Every seed
below 980 that has been used before is spent.

## 4. Hypotheses (fixed now)

R = G_iqp_pipe / G_me3.

| ID | Statement | PASS if | Sign-test p |
|---|---|---|---|
| P1 (primary) | the pipeline beats MaxEnt(3) with 2 couplers missing and 2% readout noise | R < 1 on ≥ 11/14 (`miss02`) | 0.029 |
| P2 | the pipeline beats MaxEnt(3) on the correct graph with 2% noise | R < 1 on ≥ 11/14 (`full02`) | 0.029 |
| P3 | the residual check flags the missing couplers | flagged on ≥ 12/14 in `miss02` **and** ≤ 2/14 in `full02` | — |
| P4 | the pipeline beats MaxEnt(3) at 5% readout noise with 2 couplers missing | R < 1 on ≥ 11/14 (`miss05`) | 0.029 |

Reported, with no verdict:
- median R vs me3 and vs me_local;
- resid/F before and after enlargement;
- the flag rate in `miss05`;
- the R the step-2 fit would have had without the enlargement. This is the counterfactual and is always computed.

## 5. Readings

- **C1, P1–P4 all PASS.** There is a usable recipe for coherent device data: calibrated mitigation, a generous local
  graph, and a residual check. It is ready for real hardware data.
- **C2, P3 fails.** The residual is not a reliable alarm on fresh seeds. The practical advice falls back to "always use
  the enlarged local graph", which step 24 E1 supports.
- **C3, P1 or P4 fails, P3 passes.** Detection works, but the enlarged-graph refit does not recover under noise.
- **C4, P2 fails.** Mitigation does not reproduce step 24's 14/14 on fresh seeds.

## 6. Budget and stop-loss

- About 20 min per IQP fit, 8 in parallel. 42 jobs; `miss` jobs need up to 2 fits, `full02` jobs usually 1, so at
  most 84 fits. About 2–3.5 h with 8 workers.
- **Stop-loss: 5 h wall clock.** Jobs still running at 5 h are killed and count as failures. Rerunning them needs a
  written amendment.
- Each job writes `results/step25/<cond>/seed_<s>/metrics.json`, so the run is resumable.

## 7. Verify (`--verify` exits 0 only if)

- every planned job has a metrics.json, or the stop-loss is recorded;
- `verdicts.json` is recomputed from the metrics and matches;
- `tests/test_step25.py` passes. Its tests are written before the run:
  - the enlarged graph has 103 masks, contains every grid-local mask, and is independent of the seed;
  - the mitigated floor reduces to the step 23 floor at η = 0;
  - the pipeline at η = 0 on the full graph with N = ∞ moments, started from the true θ, reaches resid < 1e-6 and does
    not flag.
