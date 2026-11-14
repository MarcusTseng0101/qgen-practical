# Step 25 result: the practical pipeline works (reading C1, P1–P4 all PASS)

Spec: `specs/step25_pipeline.md` (830f413, frozen before the run). Code: branch `step18-adversarial` 5ae718c. Results:
`results/step25/` (step 25 results commit on that branch). `python -m src.step25.run --verify` → ALL PASS (exit 0).
The run took 2.6 h of the 5 h stop-loss, with no errors and no missing jobs.

The pipeline:
1. mitigate readout with the calibrated η;
2. fit the local IQP on the given graph;
3. if resid / mitigated floor > 0.9, refit on the 103-candidate geometric local graph;
4. push the output through the readout channel.

## Verdicts (fresh seeds 980–993, N = 1e4; R = G_pipe / G_me3)

| ID | Condition | Result | Verdict | median R |
|---|---|---|---|---|
| P1 (primary) | 2 couplers missing, 2% readout noise | 14/14 | PASS | 0.48 |
| P2 | correct graph, 2% noise | 13/14 | PASS | 0.40 |
| P3 | alarm | 13/14 flagged in miss02, 0/14 false alarms in full02 | PASS | — |
| P4 | 2 couplers missing, 5% noise | 14/14 | PASS | 0.46 |

## Reported

- **Without the enlargement step** (stage-1 counterfactual), the IQP loses:
  - miss02: median R 2.14, 2/14 wins;
  - miss05: median R 1.80, 4/14 wins.

  The residual check plus the enlargement is what turns these into 14/14.
- **The alarm.**
  - After enlargement, resid/F is 0.37–0.72, back at the level of a correct graph.
  - Correct-graph resid/F is 0.38–0.68 in full02.
  - Unflagged miss cases have ratio1 0.80–0.90 (980 in both noise levels, 985 at 5%). There the missing couplers are
    barely active, and the stage-1 fit still won (R 0.97, 0.76, 0.91).
- **The classical model with the same graph prior loses everywhere.** Pipeline vs MaxEnt-on-graph: 42/42 wins, median
  R 0.07–0.10.
- **The single loss** is full02 seed 988: R 1.33 on the correct graph with 2% noise.

## Reading: C1

There is a usable recipe for coherent device data with a known approximate coupling map:
- calibrated readout mitigation;
- a residual-vs-floor alarm;
- a generous geometric local graph when the alarm fires.

It beats MaxEnt(3) on 41/42 fresh instances under combined departures (missing couplers plus 2–5% readout noise).

## Limits

1. The target is still synthetic and inside the enlarged family. Hardware noise beyond readout flips (gate
   decoherence, crosstalk, coherent over-rotation) is untested.
2. The threshold of 0.9 was chosen on spent step 24 data. It generalised (13/14, 0 false alarms), but the margin is
   small: correct graphs reach 0.83 at most, unflagged misses sit at 0.80–0.90.
3. One graph (4×4), one size (n = 16), one σ.
4. The advantage is statistical only. There is no computational advantage claim.

## Next

The remaining gap to a paper result is **real or realistic device data**. The options:
- (a) publicly released hardware IQP or random-circuit samples with a published coupling map, if any exist with order-≥4
  structure;
- (b) a noisy simulation with a full gate-level noise model (depolarizing per gate plus readout) on the same grid. This
  is the next step that needs no outward contact;
- (c) real hardware. That needs the user (money or account access).
