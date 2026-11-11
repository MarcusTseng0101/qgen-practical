# Step 20 findings: held-out order-4 validation gate

Spec: `specs/step20_heldout_val_gate.md` (frozen at de0ea3b). Results: branch `step18-adversarial`, commit
33712d6, `results/step20/`. `--verify` passed all checks.

**Run note.** The first launch crashed 9 of 18 instances at start-up (numpy out of memory) before any fit.
They were rerun unchanged and no instance was dropped. The log is in `results/step20/run1_log.txt`.

## Verdicts

| ID | Statement | Counts | Verdict |
|---|---|---|---|
| W1 (primary) | new gate losses ≤ 1 of 18 | picks 8, losses 2 | **FAIL** |
| W2 | fewer losses than the step 14 gate | 2 vs 7 | **PASS** |
| W3 | keeps ≥ 50% of the R < 1 instances | 6 of 9 | **PASS** |

| family | n | R < 1 | step 14 gate losses | new gate losses | wins kept |
|---|---|---|---|---|---|
| QEC d3_r05 | 8 | 3 | 5 | **2** (bX 5_7 R = 8.1, bX 7_5 R = 4.1) | 1 of 3 |
| iqp4 | 10 | 6 | 2 | **0** | 5 of 6 |

## What this means

1. **On synthetic IQP-family data, held-out validation works.**
   - The new gate removed both step 14 losses and kept 5 of 6 wins.
   - The sign of the validation difference matched the test outcome on 9/10 instances.
   - Together with the pilot that is 13/14 iqp4 instances with 0 losses.
2. **On QEC data it is no better than a coin.**
   - The sign of v₄(G) − v₄(MaxEnt3) matched the held-out outcome on 4/8 r05 runs. Across the pilot and
     the test runs it matched 10/16.
   - Two runs that the validation rows rated in favour of G lost on the test rows, one by 8×.
   - Two wins were refused.
3. **The likely reason: on QEC the comparison is near the noise level of both the validation and the
   test sample.**
   - MaxEnt(3)'s corrected gap is of the same size as the test-noise correction.
   - The same run gave R = 4.86 at one split and R = 0.69 at another (bX r03 3_5).
   - So the "losses" and "wins" on QEC may themselves be partly noise. Neither the gate nor R can
     resolve them at N_val = 6e3 and N_test = 2e4.
   - This is an inference. It has not been measured yet.
4. **Claim status.**
   - The step 19 restriction stands: the safety clause holds for data that the IQP fails to fit at
     low order.
   - It now extends to the IQP-family targets, provided held-out validation is added: 0 losses on 14.
   - It is **not** established for real parity-structured data such as QEC syndromes. There, the honest
     statement is that the IQP's order-4–6 completion is not distinguishable from MaxEnt(3)'s at
     5e4 shots.

## Next (recommended)

Step 21, a diagnostic with no new hypothesis test: measure the QEC resolvability directly.
- Refit the 16 spent QEC runs (r03 and r05), saving the models.
- Bootstrap the test and validation rows to get CIs on G(IQP) − G(MaxEnt3) and on v₄.
- Classify each run as a resolved win, a resolved loss, or unresolved.

If most runs are unresolved, QEC at 5e4 shots cannot test the claim either way, and the paper should say
so rather than count wins and losses.
