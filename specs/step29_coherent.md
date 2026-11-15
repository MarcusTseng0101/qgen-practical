# Step 29 spec: coherent (non-Pauli) over-rotation errors — the last simulated noise class for the step 27 recipe

Status: **frozen** once committed. Written 2026-11-15 after step 28 (F1). Exploration ran on spent seeds 980–982
(branch `step18-adversarial`, `explore/step29/`). Claude chose this step under the user's standing instruction to
continue without asking. Every number in §5 is fixed before any model is fitted on the test seeds 1060–1073.

**Deliverable.** A pre-registered test of the **unchanged** step 27 recipe on coherent miscalibration errors, with
verdicts. It is **not** a new model and **not** a coherent-error characterisation.

**Acceptance:** `python -m src.step29.run --verify` exits 0. A FAIL is a result, not a reason to edit the check, the
tests, or this spec.

## 1. Evidence so far (do not re-derive)

**Why this noise class.** Pauli noise (steps 26 and 28) is a stochastic mixture that damps correlations, which is what
FlipIQP's per-qubit λ model. A coherent RX(ε_j) after every gate touching qubit j is different:
- it is unitary, so it does not just damp — it rotates amplitude out of the diagonal (IQP) family;
- ε_j is a fixed per-qubit miscalibration drawn as N(0, ε_std²), so the error is the same every time that qubit is
  touched;
- the per-touch infidelity is about ε²/4, so ε_std 0.1 ≈ 0.25% and ε_std 0.2 ≈ 1%;
- TV distance to the ideal distribution is about 0.14 at ε_std 0.1 and 0.22 at 0.2 (seed 980).

Spent seeds 980–982, 2% readout, N = 1e4, the recipe unchanged:

| ε_std | graph | flow R | given ratio |
|---|---|---|---|
| 0.1 | full | 0.92, 0.44, 0.35 | 0.39–0.55 |
| 0.1 | missing | 0.93, 0.54, 0.49 | 0.79–3.24 (all flagged) |
| 0.2 | full | 0.93, 0.58, 0.56 | 0.39–0.71 |
| 0.2 | missing | 1.16, 0.52, 0.46 | 0.83–3.14 (all flagged) |

- **The recipe won 11/12.** The single loss is seed 980 at ε 0.2, which is also the weakest seed on the correct graph.
- **The correct-graph ratio reached 0.71 at ε 0.2,** close to the threshold of 0.75. False alarms are a real risk,
  which is why X3 is tested.

## 2. Data and models (load-bearing)

- **Data.** `src.step29.noise.coherent_grid_iqp(seed, eps_std, eta=0.02)`.
  - It is deterministic: one state vector, ε from `default_rng(50_000 + seed)`.
  - The module is frozen at the spec commit.
- **Recipe.** Imported unchanged from `src.step27.run`: `given_graph`, `raw_floor`, `flow_choice` with THRESH 0.75,
  ENLARGED, and step 26's FlipIQP settings.
- **Arms.** me3, me_local, `given`, `enl` and `flow`, defined as in step 27.

## 3. Failure modes

1. **False alarms at ε 0.2.** Coherent errors leave residual that λ cannot absorb. Report it. Do not move the threshold.
2. **λ pinned at 0.5.** Report the count. Do not widen the bound.
3. **Slow fits.** About 35–50 min per job with 12 parallel jobs. Keep the stop-loss.

## 4. Instances

| Condition | Given graph | ε_std | Seeds | Role |
|---|---|---|---|---|
| `xm02` | missing 2 edges | 0.2 | 1060–1073 | test (primary) |
| `xf02` | full | 0.2 | 1060–1073 | test |
| `xm01` | missing 2 edges | 0.1 | 1060–1073 | test |

All seeds below 1054 are spent. 42 jobs, launched in the order above.

## 5. Hypotheses (fixed now)

| ID | Statement | PASS if |
|---|---|---|
| X1 (primary) | recipe beats MaxEnt(3), wrong graph, ε 0.2 | G_flow < G_me3 on ≥ 11/14 (`xm02`); sign p = 0.029 |
| X2 | recipe beats MaxEnt(3), correct graph, ε 0.2 | ≥ 11/14 (`xf02`) |
| X3 | alarm quiet on the correct graph, ε 0.2 | flags ≤ 2/14 (`xf02`) |
| X4 | recipe beats MaxEnt(3), wrong graph, ε 0.1 | ≥ 11/14 (`xm01`) |

Reported, with no verdict:
- median R of flow / given / enl against me3 and me_local;
- flags and missed alarms;
- pinned λ;
- median λ;
- ratio ranges.

## 6. Readings

- **H1, all PASS.** The recipe also survives coherent miscalibration at about 1% per-touch infidelity. Every simulated
  noise class tested (readout, independent Pauli, correlated Pauli, coherent) is handled by one recipe.
- **H2, X3 FAIL only.** Coherent errors trigger false alarms. The recipe still wins via enlargement. Recommend "always
  enlarge" for coherent-dominated devices.
- **H3, X1, X2 or X4 FAIL.** Coherent errors are the recipe's limit. Name it as the open problem for hardware.

## 7. Budget, stop-loss, lever

- 12 workers. 42 jobs are about 2.5–3.5 h.
- **Stop-loss: 6 h.** Running jobs are killed and count as failures.
- **Lever, if the projection after the first 12 jobs exceeds 6 h:** drop `xm01` before it starts. X4 then counts as
  FAIL. Never cut restarts.

## 8. Verify (`--verify` exits 0 only if)

- every planned job has a metrics.json, or the stop-loss or the lever is recorded;
- `verdicts.json` is reproducible from the metrics;
- `tests/test_step29.py` passes. Its tests are written before the run:
  - zero ε equals `grid_iqp`;
  - normalisation holds;
  - a single RX(π) on qubit j equals flipping bit j;
  - the recipe objects are step 27's;
  - the seeds are fresh (≥ 1054).

## 9. Build order

Tests → commit code → launch → after 3 min check `errors.log` is empty → `--report`, `--verify` → note and README row on
master.

## Working style

- Guesses are marked in comments.
- Commit with explicit paths. Never push.
- If blocked by a hook, report it; do not rephrase around it.
- Do not edit this spec, the tests, or `--verify` after launch.
