# Step 24 result: extra candidates and 2% readout noise are tolerated; missing couplers are not (reading B3)

Spec: `specs/step24_robustness.md` (507cca8, frozen before the run). Code: branch `step18-adversarial` 4a1b0e4. Results:
`results/step24/` (64ebce5). `python -m src.step24.run --verify` → ALL PASS (exit 0). The run took 1.6 h of the 5 h
stop-loss, with no errors and no missing jobs.

## Verdicts (fresh seeds 960–973, N = 1e4; R = G_iqp_local / G_me3)

| ID | Departure | Wins | Need | Verdict | median R |
|---|---|---|---|---|---|
| M1 | 2 true couplers missing from the model graph | 3/14 | 11 | **FAIL** | 2.86 |
| E1 | 18 extra (inactive) diagonal candidates | 14/14 | 11 | PASS | 0.46 |
| D1 | 2% readout flips, no noise model | 11/14 | 11 | PASS (at the threshold) | 0.78 |

## Reported (no verdict)

- **Readout mitigation helps.** In `noise02`, `iqp_mitig` is fitted on f̂_S/(1−2η)^|S| and its output pushed through the
  channel.
  - It beats MaxEnt(3) on 14/14 seeds, median R 0.42.
  - It beats the noise-blind iqp_local on 14/14, median ratio 0.59.
- **`noise05`** (η = 5%, no mitigation): R 1.22, 1/14 wins. The mitigated arm was not run at 5%.
- **The classical model with the same graph does not catch up.** Even when the IQP loses to MaxEnt(3), it beats
  MaxEnt-on-graph: `miss` 14/14 (R 0.36), `noise05` 13/14.
- **A missing coupler shows in the training residual.** Residual over noise floor is 1.77 in `miss`, against 0.42–0.65 in
  the other conditions (step 23: 0.49). The model cannot reach the floor without the absent generators.
- Step 23 reference on its own seeds: median R 0.35.

## Reading

- **B3 holds.** The prior has to include every active coupler. Dropping 2 of 24 edges, together with their plaquettes
  and triples (8–14 of 85 candidates), turns a 0.35 win into a 2.9× loss.
- **Over-complete is safe.** 18 extra inactive candidates cost little (0.35 → 0.46). In practice, err on the side of
  including couplings.
- **Noise is manageable with calibration.** Readout noise erodes the noise-blind model: 2% brings it to the threshold
  and 5% makes it lose. Standard mitigation with known η restores a clear win at 2%.

## Practical recipe implied (not yet tested as a whole)

Use the full hardware coupling map, plus spare candidates, never fewer. Mitigate readout with calibrated η. Check that
the training residual reaches the noise floor: a residual well above the floor is a symptom of missing couplers.

## Next candidates

1. A residual-triggered graph enlargement, so a missing coupler is detected and repaired. Use spent seeds for exploration.
2. The mitigated arm at η = 5%.
3. Real hardware data with a published coupling map. This involves outward contact or hardware, so it waits for the user.
