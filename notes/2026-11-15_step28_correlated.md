# Step 28 result: correlated gate noise does not break the step 27 recipe (reading F1, C1–C4 all PASS)

Spec: `specs/step28_correlated.md` (01a6b08, frozen before the run). Code: branch `step18-adversarial` b4b04df.
Results: `results/step28/` (125ae46 on that branch). `python -m src.step28.run --verify` → ALL PASS (exit 0).

The run took 2.8 h of the 7 h stop-loss. The projection after 12 jobs was 2.68 h, so the lever did not fire. There were
no errors and no missing jobs.

**Data.** After every gate on k qubits, a uniformly random non-identity k-qubit Pauli string is applied with
probability q_k. The rate q_k is chosen so that each qubit's marginal error rate is p, as in step 26. The only change from
step 26 is correlation within a gate.

**Model.** The recipe is step 27's, imported unchanged:
- FlipIQP on the given graph;
- an alarm when resid / raw floor exceeds 0.75;
- a refit on the 103-candidate geometric graph when the alarm fires.

FlipIQP's per-qubit damping is deliberately mis-specified for correlated noise.

**Setup.** Readout noise is 2%, N = 1e4, R = G / G_me3.

## Verdicts (fresh seeds 1040–1053)

| ID | Statement | Result | Verdict |
|---|---|---|---|
| C1 (primary) | wrong graph, correlated p = 0.01 | 14/14, median R 0.54 | **PASS** |
| C2 | correct graph, correlated p = 0.01 | 14/14, median R 0.53 | **PASS** |
| C3 | alarm quiet on the correct graph | 0/14 flagged | **PASS** |
| C4 | wrong graph, correlated p = 0.02 | 12/14, median R 0.80 | **PASS** |

## Reported (no verdict)

| cond | flow R (wins) | given only R (wins) | always-enlarged R (wins) | flags | missed alarms | flow R vs me_local |
|---|---|---|---|---|---|---|
| cm01 | 0.54 (14/14) | 1.30 (2/14) | 0.54 (14/14) | 14 | 0 | 0.10 |
| cf01 | 0.53 (14/14) | 0.53 (14/14) | 0.54 (14/14) | 0 | 0 | 0.16 |
| cm02 | 0.80 (12/14) | 1.15 (3/14) | 0.72 (14/14) | 10 | 2 | 0.22 |

- **At p = 0.01 the alarm separates the two conditions perfectly.** Correct-graph ratios are 0.37–0.64. Wrong-graph
  ratios are 0.76–4.92, all flagged. The separation is cleaner than step 27's independent-noise run at the same rate.
- **At p = 0.02 the alarm misses more often.** 4 of 14 wrong-graph seeds stay below 0.75 (0.63–0.71). Two of them lose:
  seed 1046 (R 1.16) and seed 1053 (R 1.21). These are the only two C4 losses.
- **At p = 0.02 "always enlarge" is better.** It wins 14/14 with median R 0.72, against the recipe's 12/14 and 0.80. As
  noise rises, the threshold gets close to the wrong-graph ratios.
- **Pinned λ.** 3 pinned on the given graph and 2 on the enlarged graph, out of 42 jobs.

## Reading: F1

Within-gate correlation at a matched marginal rate does not hurt the recipe. Per-qubit damping is a sufficient
effective noise model up to 2% on this circuit. That holds even though correlated noise is outside its family.

**One practical refinement for the paper, reported, not tested.** At gate error ≥ 2%, "always enlarge" is the safer
default. Across steps 27 and 28 its worst correct-graph cost was median R 0.71 against 0.57 (step 27), and here it costs
almost nothing.

## Status

Simulated robustness now covers the following, all pre-registered on fresh seeds, with the same recipe since step 27:
- ideal data;
- graph errors;
- readout noise;
- independent gate noise;
- the combination of graph errors and gate noise;
- correlated gate noise.

**Remaining open limits:**
- coherent errors that are not Pauli (over-rotations stay inside the IQP family; crosstalk ZZ is what enlargement
  covers);
- n > 16;
- real hardware data. This needs the user.
