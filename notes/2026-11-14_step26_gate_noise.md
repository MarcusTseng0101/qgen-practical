# Step 26 result: learned per-qubit damping keeps the IQP ahead under gate noise (reading D1, G1–G3 all PASS)

Spec: `specs/step26_gate_noise.md` (132e9ec, frozen before the run). Code: branch `step18-adversarial` b0cb3ef.
Results: `results/step26/` (ff1d1eb on that branch). `python -m src.step26.run --verify` → ALL PASS (exit 0).
The run took 4.2 h of the 6 h stop-loss. The projection after 8 jobs was 4.59 h, so the lever did not fire and `g02` ran
in full. There were no errors and no missing jobs.

Data: full 4×4 grid IQP (49 target gates). Each gate is followed by single-qubit Pauli noise at rate p_gate. Readout
noise is 2%. The target is a fixed 4000-trajectory mixture. N = 1e4 shots, order-≤3 moments. R = G_model / G_me3.

## Verdicts (fresh seeds 1000–1013)

| ID | Statement | Result | Verdict |
|---|---|---|---|
| G1 (primary) | FlipIQP beats MaxEnt(3) at p = 0.01 | 13/14, median R 0.63 | **PASS** |
| G2 | FlipIQP beats MaxEnt(3) at p = 0.005 | 14/14, median R 0.51 | **PASS** |
| G3 | FlipIQP beats the step 25 pipeline at p = 0.01 | 14/14 | **PASS** |

## Reported (no verdict)

| p_gate | flip R vs me3 (wins) | pipe R vs me3 (wins) | flip R vs me_local | flip < pipe | pipe flags | pinned λ | median λ | flip resid/floor |
|---|---|---|---|---|---|---|---|---|
| 0.005 | 0.51 (14/14) | 0.70 (10/14) | 0.16 | 12/14 | 0 | 0 | 0.94 | 0.46 |
| 0.01 | 0.63 (13/14) | 0.97 (8/14) | 0.23 | 14/14 | 0 | 2 | 0.92 | 0.51 |
| 0.02 (stress) | 0.60 (13/14) | 1.60 (0/14) | 0.39 | 14/14 | 0 | 0 | 0.86 | 0.52 |

- **The single G1 loss is seed 1008, with R_flip 1.16.** The pipeline was worse on that seed too (R 1.56).
- **Pinned λ.** Two λ values sat at the 0.5 bound at p = 0.01: one on seed 1003 and one on seed 1009. Both seeds still
  won (R 0.74 and 0.59). Following the spec, the bound was not widened.

## Reading: D1

A 16-parameter local noise model is enough to keep the connectivity-prior advantage under gate noise up to 2%.

- **The step 25 pipeline cannot handle gate noise.** It removes only readout noise, so its advantage is gone by
  p = 0.01 (R ≈ 0.97) and reverses at p = 0.02 (R 1.6, 0/14 wins).
- **The pipeline's residual alarm never fired (0/42).** The alarm detects missing couplers, but it does not detect
  gate noise, so it cannot tell the pipeline to switch models. FlipIQP needs no alarm and no calibrated η.
- **FlipIQP's R does not grow with p** (0.51, 0.63, 0.60). The learned λ track the noise: the median falls from 0.94 to
  0.86.

**Paper recipe:** local IQP plus learned per-qubit damping (FlipIQP), fitted on raw moments. Step 25's mitigation and
alarm remain the tool for graph errors.

## Caveats

- **The noise model is idealised.** It uses single-qubit Pauli noise only and assumes the graph is correct. Correlated
  noise, crosstalk and coherent errors were not tested.
- **Graph errors combined with gate noise were not tested.** That is the natural next simulation, but real hardware data
  is now the bigger open question.
