# Step 29 result: coherent miscalibration is the recipe's limit (reading H3: X1, X4 PASS; X2, X3 FAIL)

Spec: `specs/step29_coherent.md` (5b2a871, frozen before the run). Code: branch `step18-adversarial` 955dd32. Results:
`results/step29/` (fd99a33 on that branch). `python -m src.step29.run --verify` → ALL PASS (exit 0). ALL PASS means the run is
complete and reproducible, not that the hypotheses passed.

The run took 2.7 h of the 6 h stop-loss. The projection after 12 jobs was 2.50 h, so the lever did not fire. There were
no errors and no missing jobs.

**Data.** After every gate, each qubit it touches gets a coherent RX(ε_j) over-rotation. ε_j is a fixed per-qubit
miscalibration drawn as N(0, ε_std²). The per-touch infidelity is about ε²/4, so ε_std 0.2 ≈ 1% and 0.1 ≈ 0.25%.

**Model.** The step 27 recipe, imported unchanged. 2% readout noise, N = 1e4, R = G / G_me3.

## Verdicts (fresh seeds 1060–1073)

| ID | Statement | Result | Verdict |
|---|---|---|---|
| X1 (primary) | wrong graph, ε 0.2 | 12/14, median R 0.68 | **PASS** |
| X2 | correct graph, ε 0.2 | 10/14, median R 0.74 | **FAIL** |
| X3 | alarm quiet on the correct graph, ε 0.2 | 3/14 flagged (max 2) | **FAIL** |
| X4 | wrong graph, ε 0.1 | 13/14, median R 0.66 | **PASS** |

## Reported (no verdict)

| cond | flow R (wins) | given only (wins) | always-enlarged (wins) | flags | median λ (given) |
|---|---|---|---|---|---|
| xm02 | 0.68 (12/14) | 1.19 (4/14) | 0.69 (12/14) | 13 | 1.00 |
| xf02 | 0.74 (10/14) | 0.70 (10/14) | 0.69 (12/14) | 3 | 0.99 |
| xm01 | 0.66 (13/14) | 1.09 (6/14) | 0.69 (14/14) | 11 | 1.00 |

- **The damping does nothing here.** The median λ is about 1.0 in every condition, against 0.86–0.94 under Pauli noise.
  A coherent rotation is unitary: it moves weight between parity moments instead of shrinking them. Per-qubit damping is
  the wrong effective model, so the residual stays higher than under Pauli noise.
- **On the correct graph, the given-graph fit itself wins only 10/14.** The 4 losses are:

  | seed | ratio | R |
  |---|---|---|
  | 1064 | 0.67 | 1.43 |
  | 1066 | 0.74 | 1.07 |
  | 1067 | 0.35 | 1.21 |
  | 1070 | 0.80, flagged | 1.08 |

  Seed 1067 has a low ratio, which means the fit matches the order-≤3 moments well yet completes orders 4–6 badly.
  The alarm cannot see this kind of failure, because it only checks order-≤3 fit.
- **False alarms.** The correct-graph ratio reached 1.03, against a maximum of 0.77 under all Pauli noise so far. The
  0.75 threshold is too close.
- **Always enlarging would have passed X2's count, though this is reported, not tested.** It won 12/14 on the correct
  graph, but its median R of 0.69 is barely better.

## Reading: H3

Coherent errors are the recipe's limit. On wrong graphs the alarm still works (X1, X4). On correctly specified data with
coherent miscalibration of about 1% per touch, the IQP prior wins only 10/14. The cause is model mis-specification that
the order-≤3 residual does not reveal.

**For the paper.** Pauli noise of every kind tested is handled. Coherent miscalibration of about 1% is the stated open
limit. At about 0.25% (X4) the recipe still wins 13/14 on wrong graphs, and the correct-graph case at 0.25% was not
tested.

**A remedy needs a coherent-aware model.** This cannot be an output-layer correction: an RX right before the final H
layer acts as a Z rotation after it and leaves p unchanged. Errors matter only because they do not commute with the
later diagonal gates. So the model must place unknown RX rotations inside the circuit, which needs an assumed gate
order. That is a new model, not a tuning of this one.

## Note on a test description

Spec §8 says a test checks that "a single RX(π) on qubit j equals flipping bit j". That wording is wrong. An X between
the H layers becomes a Z after the final H, so it changes the output phase only and leaves p unchanged. The test written
before the run checks the correct statement: the update rule at ε = π equals −i X_j, and the output probabilities are
unchanged with amplitudes multiplied by (−1)^{x_j}. The spec was not edited after launch.
