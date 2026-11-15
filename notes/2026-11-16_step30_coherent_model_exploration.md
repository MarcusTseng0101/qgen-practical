# Step 30 exploration: a coherent-aware IQP does not fix step 29's limit (no pre-registered test)

**Status: exploration on spent seeds only. There are no verdicts and no spec.** Code: branch `step18-adversarial`
172ef9c (`src/step30/cohiqp.py`, `explore/step30/`). The results did not justify freezing a test, because its answer was
already visible: the new model does not beat the step 27 recipe head-to-head.

## Model (CohIQP)

Step 29 showed that coherent RX miscalibration inside the circuit is the recipe's limit, and that an output-layer
correction cannot fix it. CohIQP therefore puts unknown RX rotations inside the circuit:
- The local generators are split into layers by gate weight (1, 2, ≥3).
- Each layer applies its diagonal phase, then an RX layer on every qubit.
- No RX layer follows the last diagonal layer, because an RX right before the final H layer leaves p unchanged.
- The RX layer is computed in the Hadamard basis with two FWHTs.
- FlipIQP's readout damping λ is kept.

Two variants were tried:
- **Untied:** one angle per layer and qubit, 32 extra parameters.
- **Tied:** one angle per qubit. The layer-l rotation is that angle times the number of layer-l gates touching the qubit,
  which mirrors how step 29 generated the data. This adds 16 parameters.

**Checks.**
- The analytic gradient matches finite differences: worst relative error 4e-8 untied, 5e-9 tied.
- The forward pass matches a brute-force circuit to 3e-17.

**Fit settings.** L-BFGS-B with 5 restarts and maxiter 3000.
- **The 3000-iteration cap is a guess.** On seed 1067 the ratio moved from 0.167 to 0.165 between 3000 and 8000
  iterations.

## Results (spent seeds; R = G / G_me3, lower is better)

| Data | Model | n | Wins vs me3 | Median R | Beats the step 27/26 fit, same seed |
|---|---|---|---|---|---|
| coherent ε 0.2, correct graph (step 29 `xf02`, 1060–1073) | step 29 given-graph FlipIQP | 14 | 10 | 0.70 | — |
| same | CohIQP untied | 14 | 12 | 0.75 | 7/14 |
| same | CohIQP tied | 14 | 10 | 0.69 | 8/14 |
| Pauli 1% + 2% readout, correct graph (step 26 `g01`, 1000–1013) | FlipIQP | 14 | 13 | 0.62 | — |
| same | CohIQP untied | 14 | 13 | 0.79 | 2/14 |
| same | CohIQP tied | 14 | 11 | 0.74 | 2/14 |

**Update (after the note was first committed).** The six tied fits that were still running (xf02 1067, 1068; g01 1001, 1002, 1004, 1006) have finished; the table above now includes them. The tied model won both remaining coherent seeds head-to-head (8/14, the maximum the first version allowed) and lost all four Pauli seeds (2/14). The conclusion is unchanged: no better than FlipIQP on coherent data, worse under Pauli noise.

## Reading

- **More in-circuit freedom fits order ≤ 3 better but completes orders 4–6 no better.** The untied model's residual
  ratio is lower than FlipIQP's (max 0.68 against 1.03 on coherent data), which would remove step 29's false alarms.
  Its R is not lower, though. Under Pauli noise, where the extra angles have nothing true to learn, R gets worse (0.79
  against 0.62). This is overfitting to sampling noise in the order-≤3 moments.
- **Tying the angles to the true generative structure does not help either.** The tied model has only 16 extra
  parameters and reproduces the data's structure exactly, apart from gate order within a layer. It is still no better.
  So the limit is not just parameter count. With N = 1e4 shots, order-≤3 moments do not pin down the coherent angles
  well enough to improve the high-order completion.
- **A pre-registered test was not run.** It would have tested a model that already lost on these 28 spent-seed
  instances. Spending fresh seeds on that would be a formality, not evidence.

**For the paper.** Coherent miscalibration of about 1% per touch remains the stated open limit (step 29, H3). A natural
coherent-aware model was tried and did not remove it. This is reported as exploration, and the paper must not phrase it
as a tested negative.

## What might work (not done)

- **More shots.** The angles may become identifiable from order-≤3 moments at N = 1e5. This is untested.
- **Calibration data.** Hardware calibration (randomized benchmarking, or a per-qubit Rabi over-rotation estimate) could
  fix ε instead of fitting it. This needs a real device, so it is a decision for the user.
