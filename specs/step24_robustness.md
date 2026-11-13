# Step 24 spec: robustness of the connectivity-prior IQP — wrong graph, extra candidates, readout noise

Status: **frozen** once committed. Written 2026-11-13 after step 23 (notes/2026-11-13_step23_local_iqp.md: A1, H1–H4
PASS 14/14). Claude chose this step under the user's standing instruction to take the recommended option. Every number
in §4 is fixed here, before any model is fitted on the test seeds 960–973.

**Acceptance:** `python -m src.step24.run --verify` must exit 0. It is the definition of done. A FAIL hypothesis is a
result, not a reason to change the check.

## 1. Why

Step 23 gave the local IQP the exact device graph, and its data were noiseless. On real hardware neither holds:
- the coupling map can be wrong, because a coupler can be dead or uncalibrated (**missing** candidates);
- a cautious user may allow more couplings than are active (**extra** candidates);
- readout flips bits with probability η ≈ 1–3% per qubit.

If the advantage disappears under any of these, step 23 is a lab curiosity. This step tests each departure separately on
fresh seeds, so a failure points at one cause.

## 2. Conditions (load-bearing details)

All conditions use the step 23 target `grid_iqp(seed)` (49 generators, σ = 0.251), N = 1e4 order-≤3 training moments
from `training_moments`, and the step 23 fit settings for every IQP arm: 20 restarts, init std 0.3.

| Condition | What changes | iqp candidates | me_local masks |
|---|---|---|---|
| `miss` | 2 grid edges, chosen by `default_rng(20_000 + seed)`, are absent from the model's graph. The target still uses them. Removed: the edge, every plaquette containing it, and every triple containing both of its endpoints. | 85 minus the removed | 76 minus the removed |
| `extra` | The model's graph adds the 18 plaquette diagonals as weight-2 candidates. The target does not use them. | 103 | 94 |
| `noise02` | The data distribution is `grid_iqp` passed through independent readout flips, η = 0.02: f_S → (1 − 2η)^{\|S\|} f_S. | 85 | 76 |
| `noise05` | The same with η = 0.05 (report only). | 85 | 76 |

- **Score.** G against the distribution the data were drawn from: the noisy p in the noise conditions, the target in the
  others. This is exact, orders 4–6, with no test noise.
- **Arms in every condition:** `me3`, `me_local` (on that condition's graph), and `iqp_local` (on that condition's
  candidates).
- **Extra arm in `noise02`: `iqp_mitig`**, the noise-aware variant. It is fitted on mitigated moments
  f̂_S / (1 − 2η)^{\|S\|} with the known η = 0.02. Its noiseless q is then pushed through the same channel before
  scoring. This is standard readout mitigation; η is assumed calibrated.
- Do not give any model the target's θ, its active set, or the identities of the removed edges. Any of these is oracle
  information.

## 3. Instances

Test seeds 960–973 (14): never used. The same seeds are used in every condition (paired). 4 conditions × 14 = 56 jobs.
Seeds 900–933 and 940–953 are spent.

## 4. Hypotheses (fixed now)

R = G_iqp_local / G_me3 within each condition.

| ID | Statement | PASS if | Sign-test p under H0 |
|---|---|---|---|
| M1 | with 2 couplers missing from the graph, local IQP still beats MaxEnt(3) | R < 1 on ≥ 11/14 (`miss`) | 0.029 |
| E1 | with 18 extra candidate couplings, local IQP still beats MaxEnt(3) | R < 1 on ≥ 11/14 (`extra`) | 0.029 |
| D1 | with 2% readout noise and no noise model, local IQP still beats MaxEnt(3) | R < 1 on ≥ 11/14 (`noise02`) | 0.029 |

Reported, with no verdict:
- median R vs me3 and vs me_local in every condition;
- `noise05`;
- `iqp_mitig` against me3 and against iqp_local in `noise02`;
- the paired ratio R_condition / R_step23-like. This one cannot be computed exactly, because step 23 used different
  seeds, so report the medians side by side only;
- the training residual over the noise floor.

## 5. Readings

- **B1, M1, E1 and D1 all PASS.** The advantage survives the departures a real device brings. Next is real data with a
  published coupling map.
- **B2, D1 FAILS.** Readout noise breaks the noiseless family. If `iqp_mitig` wins where `iqp_local` loses, the fix is
  calibration (report as the recommended practice). If both lose, the prior is fragile.
- **B3, M1 FAILS.** The model needs an accurate graph. A real coupling map comes from calibration data, but a wrong one
  is costly.
- **B4, E1 FAILS.** Over-complete candidates bring non-identifiability back. The prior must be tight.

## 6. Budget and stop-loss

- About 20 min per IQP fit with 8 jobs in parallel. 56 jobs, 70 IQP fits: about 2–3 h with 8 workers.
- **Stop-loss: 5 h wall clock.** Jobs still running at 5 h are killed and count as failures. Rerunning them needs a
  written amendment.
- Each job writes `results/step24/<cond>/seed_<s>/metrics.json`, so the run is resumable.

## 7. Verify (`--verify` exits 0 only if)

- every planned job has a metrics.json, or the stop-loss is recorded;
- `verdicts.json` is recomputed from the metrics and matches;
- `tests/test_step24.py` passes. Its tests are written before the run:
  - the candidate counts per condition (85, 103, and fewer than 85 for `miss`);
  - the removed edges are true target generators;
  - the readout channel preserves normalisation and positivity, and scales f_S by (1 − 2η)^{\|S\|};
  - mitigation then the channel is the identity on the moments.
