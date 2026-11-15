# Synthesis of steps 23–30: the connectivity-prior IQP as a practical moment-completion method

(Updated 2026-11-16 to add step 29, a pre-registered test, and step 30, spent-seed exploration with no verdict. The file
name still says 23–28.)

This note collects the evidence chain for the paper's main positive result. Every row below except step 30 is a
pre-registered test on fresh seeds: the spec was frozen on master before the run, the sign test needed ≥ 11/14, and missing seeds counted
as failures. The details are in each step's note.

The question asked of every model is the same: complete the order-4–6 parity moments from N = 1e4 shots' order-≤3
moments. G is the completion gap, computed exactly against the target. R = G_model / G_MaxEnt(3); R < 1 means the
model beats MaxEnt(3).

## 1. Why a prior is needed

- **Steps 18–22.** A generic IQP with 696 generators is not identifiable from order-≤3 moments (condition number about
  1e9). Its "advantage" there was not robust.
- **Step 23.** The fix is the device's connectivity. A 4×4 grid gives 85 local candidates, while the target uses 49.
  With this prior the IQP wins 14/14 (median R 0.35 at N = 1e4, 0.19 at 1e5).
  - **MaxEnt on the same graph cannot use the prior.** Interference makes log p non-local, and the IQP beats it at
    median R 0.07.
  - **The advantage is statistical, not computational.** It comes from the prior matching the data's generative
    structure.
  - **It is not universal.** On a classical grid-Ising target the IQP wins 0/14.

## 2. Robustness chain (all on the 4×4 grid)

| Step | Departure from the ideal | Method | Key result |
|---|---|---|---|
| 24 | 2 missing couplers | plain local IQP | **fails**: 3/14, R 2.86 |
| 24 | 18 extra candidates | plain local IQP | 14/14, R 0.46 |
| 24 | 2% readout noise | plain local IQP | 11/14, R 0.78; with mitigation 14/14, R 0.42 |
| 25 | missing couplers + 2–5% readout | mitigation + residual alarm + 103-candidate enlargement | 41/42 wins; alarm 13/14 hits, 0/14 false |
| 26 | independent gate noise 0.5–2% | the step 25 pipeline | erodes: R 0.70, 0.97, 1.60 |
| 26 | independent gate noise 0.5–2% | **FlipIQP** (+16 learned per-qubit dampings) | 14/14, 13/14, 13/14; R 0.51, 0.63, 0.60 |
| 27 | missing couplers + gate noise 0.5–1% | **FlipIQP + alarm (0.75) + enlargement** | 13/14, 12/14; correct graph 13/14; false alarms 1/14 |
| 28 | correlated gate noise 1–2% | same recipe, unchanged | 14/14, 12/14; correct graph 14/14; false alarms 0/14 |
| 29 | coherent RX miscalibration, ε 0.1–0.2 (≈0.25–1% per touch) | same recipe, unchanged | wrong graph 13/14 (ε 0.1), 12/14 (ε 0.2); **correct graph 10/14 (FAIL)**; false alarms 3/14 (FAIL) |
| 30 | same as step 29, correct graph | coherent-aware layered IQP (exploration, spent seeds) | no better than FlipIQP head-to-head (7/14 untied, 8/14 tied); worse under Pauli noise |

## 3. The recipe (final, since step 27)

1. **Fit FlipIQP** on the device's coupling graph, using order-≤3 moments from raw shots.
   - FlipIQP is a local IQP whose output moments are multiplied by Π_{j∈S} λ_j, with λ_j ∈ [0.5, 1].
   - It needs no readout calibration.
2. **Check the fit.** If resid / Σ(1 − f̂²)/N > 0.75, refit on the geometric enlargement (the grid plus the 18 plaquette
   diagonals).
3. **Use the fitted model** to predict the order-4–6 moments.

**Refinement (observed, not tested).** At gate error ≥ 2%, always enlarging is the safer default. It won 14/14 with
median R 0.72 in step 28, and its cost on correct graphs is small.

## 4. Negative and boundary results to keep in the paper

- **Generic (non-local) IQP:** not identifiable. Its wins were not robust (steps 18–22).
- **QEC detection-event data** (Google surface code, step 19): no advantage, and the gate fails 7/7.
- **Classical targets** (grid Ising): the IQP prior loses. The method is a structural prior, not a universal improvement.
- **The residual alarm thins out as noise grows.** In steps 27 and 28, 3 of the 4 wrong-graph losses at p ≥ 1% were
  missed alarms.

## 5. Open limits (not done)

- **Coherent non-Pauli errors: tested, and this is the recipe's limit (step 29, H3).**
  - Over-rotations of the diagonal gates stay inside the IQP family, and unwanted ZZ crosstalk is the case enlargement
    covers.
  - Off-diagonal RX miscalibration of about 1% per touch is different. It breaks the correct-graph case (10/14) and
    gives false alarms, because per-qubit damping is the wrong effective model for a unitary error (λ ≈ 1.0).
  - The wrong-graph cases still pass.
  - A coherent-aware model with in-circuit RX layers did not fix it (step 30, exploration only). It fits order ≤ 3
    better, but it completes orders 4–6 no better. Candidate remedies are more shots or hardware calibration of ε,
    and both are untested.
- **n > 16.** Exact G needs 2^n. At 20 qubits a FlipIQP fit with 20 restarts would take roughly 8 h per job on this
  machine, so this needs a cheaper fitter or estimated G.
- **Real hardware data.** This needs the user, because it means money, a collaborator, or an outside request.

Every step so far is simulation, and the target is always generated by a local IQP circuit. The paper must say that the
claim covers data from IQP-like devices with a known approximate coupling graph.
