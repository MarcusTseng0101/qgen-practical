# Step 31 result: with N = 1e5, the coherent-aware model beats the coherent limit on the correct graph (K1: Y1, Y2, Y3 PASS)

- **Spec:** `specs/step31_coherent_shots.md` (a6c5b53), frozen before the test seeds were fitted.
- **Code:** branch `step18-adversarial` 387b113 (`src/step31/run.py`, `tests/test_step31.py`).
- **Pilot:** 846a7a8, on spent seeds 1060–1073.
- **Results:** f68011a, in `results/step31/`.

`python -m src.step31.run --verify` → ALL PASS (exit 0). ALL PASS means the run is complete and reproducible. It does
not mean the hypotheses passed.

**Run.** 56 jobs with 20 workers took 9.3 h, against an 11 h stop-loss. There were no errors and no missing jobs.
- The projection after 20 finished jobs was 13.41 h, so the lever fired.
- It dropped nothing, because every `pf` coh job had already started.
- The projection was too high: no flip job had finished yet, so it used the coh mean (about 4.7 h) for the flip jobs.
  They actually took 1.1–1.6 h.

**Setup.** All jobs used N = 1e5 shots, 2% readout and the correct graph. R = G / G_me3, with MaxEnt(3) fitted on the
same shots; lower is better.
- `cf`: coherent RX miscalibration with ε_std 0.2, about 1% per touch (the step 29 data).
- `pf`: independent Pauli gate noise at 1% (the step 26 data).
- `coh`: step 30's untied CohIQP, unchanged.
- `flip`: FlipIQP fitted on the given graph (the step 26/27 recipe's given-graph fit).

## Verdicts (fresh seeds 1080–1093)

| ID | Statement | Result | Verdict |
|---|---|---|---|
| Y1 (primary) | CohIQP beats MaxEnt(3), coherent data | 12/14, median R 0.51 | **PASS** |
| Y2 | CohIQP beats FlipIQP head-to-head, coherent data | 11/14 | **PASS** |
| Y3 (control) | CohIQP beats MaxEnt(3), Pauli data | 14/14, median R 0.38 | **PASS** |

**Reading K1.** With 1e5 shots, the coherent-aware model removes step 29's limit on the correct graph, and it is safe
under Pauli noise.

## Reported (no verdict)

| cond | CohIQP: wins vs me3, median R | FlipIQP: wins vs me3, median R | coh beats flip | ratio > 0.75 (coh / flip) |
|---|---|---|---|---|
| cf | 12/14, 0.51 | 12/14, 0.65 | 11/14 | 10 / 13 |
| pf | 14/14, 0.38 | 14/14, 0.17 | **0/14** | 2 / 2 |

- **Under Pauli noise CohIQP is safe but strictly worse.** It loses to FlipIQP on every seed: median 0.38 against 0.17.
  The extra in-circuit angles have nothing true to learn and overfit, as in step 30.
  - So K1 does not mean "always use CohIQP".
  - The choice between the two models needs a diagnosis of coherent against stochastic noise, and that is untested.
- **On these fresh seeds FlipIQP itself also wins 12/14 on coherent data at 1e5.** Step 29 at 1e4 got 10/14 on seeds
  1060–1073.
  - Part of step 29's limit may therefore be seed variation and not just a shot-count effect.
  - Y2 is the test that matters, and CohIQP wins it 11/14 with a lower median (0.51 against 0.65).
- **The alarm does not transfer to N = 1e5.** On the correct graph, FlipIQP's ratio exceeds 0.75 on 13/14 coherent
  seeds (range 0.69–6.1) and on 2/14 Pauli seeds (0.39–1.23).
  - The noise floor shrinks with N, but model bias does not.
  - The 0.75 threshold is an N = 1e4 setting. It must not be used at 1e5 without recalibration.
- **Convergence.**
  - Every CohIQP restart stopped at the 3000-iteration cap: 70/70 in each condition. The cap is step 30's guess and was
    not raised, as the spec required. R may therefore be pessimistic for CohIQP.
  - ε reached the bound of 1.5 in 14 angle slots (cf) and 15 (pf), out of 14 × 32 per condition.
  - No FlipIQP λ was pinned. The median λ is 0.96 on coherent data and 0.88 on Pauli data.
- **Pilot vs test.**
  - Pilot (spent seeds 1060–1073, 1e5): CohIQP won 12/14 with median 0.58, beat FlipIQP's given-graph fit 11/14, and
    beat the recipe's flow 10/14.
  - FlipIQP with exact moments (N = ∞) won only 10/14 with median 0.79, so it is bias-limited.
  - The test reproduces the pilot closely.

## Exploratory: a possible coherence diagnostic (post hoc, untested)

FlipIQP's own residual ratio separates the two noise types almost cleanly on the test seeds:
- coherent data: ratio > 1 on 12/14 seeds (the other two are 0.80 and 0.69);
- Pauli data: ratio > 1 on 1/14 seeds (1.23).

A rule "fit FlipIQP; if its ratio exceeds about 1 at N = 1e5, also fit CohIQP and use it" would have picked:
- on coherent data: CohIQP on 12/14 seeds, where CohIQP beat FlipIQP on 10 of those 12;
- on Pauli data: FlipIQP on 13/14 seeds.

This rule was found after looking at the data. Testing it needs fresh seeds and its own spec.

## For the paper

- The coherent limit of step 29 is not fundamental. It is a model mis-specification that a coherent-aware IQP fixes once
  the order-≤3 moments are sharp enough (N = 1e5 on 16 qubits).
- The cost is about 3× the compute per fit, plus a choice between models that needs a coherence diagnosis.
- At N = 1e4 (step 30) the same model did not help.
- State the shot dependence, the iteration cap, and that the diagnosis is untested.
