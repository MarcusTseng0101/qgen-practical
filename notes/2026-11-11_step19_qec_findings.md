# Step 19 findings: real QEC detection events (Google surface code, d = 3)

Spec: `specs/step19_real_qec16.md` (frozen at 56cc051). Results: branch `step18-adversarial`, commit
b45bb65, `results/step19/`. `--verify` passed all checks (raw output is in `SUMMARY.md`).

## Verdicts

| ID | Statement | Counts | Verdict |
|---|---|---|---|
| V1 (primary) | gate losses ≤ 1 of 7 runs | picked 7, wins 2, losses 5 | **FAIL** |
| V2 | ungated R ≥ 1 on ≥ 6/7 | R ≥ 1 on 5/7 | **FAIL** |

Median R = 2.87 [1.60, 3.51]. Median R_raw = 1.84 [1.26, 2.33]. R_raw has the same sign as R on all 7 runs,
so the outcome does not come from the test-noise correction.

| run | R | R4 | R5 | R6 | r_N | floor | val4 ratio (train rows) |
|---|---|---|---|---|---|---|---|
| bZ 3_5 | 3.84 | 1.74 | 3.32 | 6.07 | 3.7e-4 | 0.018 | 0.65 |
| bX 5_3 | **0.60** | 0.69 | 0.51 | 0.61 | 2.3e-4 | 0.018 | 0.70 |
| bZ 5_3 | 2.87 | 1.58 | 3.03 | 4.68 | 1.4e-4 | 0.018 | 0.83 |
| bX 5_7 | 4.24 | 2.17 | 4.19 | 5.55 | 3.3e-4 | 0.018 | 0.60 |
| bZ 5_7 | 3.18 | 1.54 | 2.94 | 6.32 | 2.5e-4 | 0.018 | 0.67 |
| bX 7_5 | **0.70** | 0.83 | 0.68 | 0.63 | 2.3e-4 | 0.018 | 0.80 |
| bZ 7_5 | 2.50 | 1.48 | 2.40 | 3.54 | 1.7e-4 | 0.018 | 0.82 |

## What this means

1. **The step 14 gate is unsafe on real parity-structured hardware data.** The IQP fits the order-≤3
   moments far below the noise floor on every run, so the gate always picks it. It then loses on 5 of 7
   runs, by up to 4×. This is the step 18 failure mode, now observed on data nobody constructed.
   Under the rule fixed in the spec, **the safety clause of the claim must be restricted to data that the
   IQP fails to fit at low order** (as in MNIST, step 17). The gate is a fit check, not a completion check.
2. **The loss grows with order** (R4 < R5 < R6 on every losing run). G's extra structure is wrong in a way
   that compounds at high order.
3. **Both wins are X-basis runs** (5_3, 7_5); all 4 Z-basis runs lose. The pilot run (bX 3_5) lost, so the
   split is 2/4 in X and 0/4 in Z. This is exploratory: 8 runs, one split each.
4. **The step 18 suggested fix, as implemented here, does not work.** Order-4 validation against the
   *training* rows rates G better than MaxEnt(3) on all 7 runs (ratio 0.60–0.83, flags 0/7), including the
   5 losses. Likely mechanism: G over-fits the training sample, and the training rows' order-4 moments
   carry the same sampling noise, so the check rewards over-fitting. A real check must use rows the fit
   never saw.

## Limits

- One split per run. Each run is a separate hardware experiment, but the 8 runs share a chip and a day.
- MaxEnt(3)'s corrected gap is close to the test-noise correction, so the size of R is noisy. The sign
  agrees with R_raw.
- This is syndrome data, not IQP-circuit output. It speaks to the "practical data" question, not to
  sampling hardness.

## Next (recommended)

Step 20: a **held-out** order-4 validation gate. Split the 3e4 training shots into a fit part and a
validation part; pick G only if it beats MaxEnt(3) on the validation rows' order-4 moments (noise-corrected).
- Freeze it on these 8 runs as development data (they are now spent for testing).
- Test it on fresh runs from the same Zenodo archive, for example the d = 3 r05/r07 experiments with a new
  detector window, and re-check that the step 14–17 wins survive the new gate.
