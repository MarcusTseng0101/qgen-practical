# Step 28 spec: correlated gate noise — does the step 27 recipe survive when a gate's errors hit its qubits together?

Status: **frozen** once committed. Written 2026-11-15 after step 27 (E1). Exploration ran on spent seeds 980–985
(branch `step18-adversarial`, `explore/step28/`). Claude chose this step under the user's standing instruction to
continue without asking. Every number in §5 is fixed before any model is fitted on the test seeds 1040–1053.

**Deliverable.** A pre-registered test of the **unchanged** step 27 recipe on correlated gate noise, with verdicts. It is
**not** a new model; FlipIQP's per-qubit damping is deliberately left mis-specified for correlated noise. It is **not**
a noise-model zoo either.

**Acceptance (the one definition of done):** `python -m src.step28.run --verify` exits 0. A FAIL hypothesis is a result,
not a reason to edit the check, the tests, or this spec.

## 1. Evidence so far (do not re-derive; act on it)

**Why this is the stress test.** FlipIQP models noise as independent per-qubit dampings, which matches step 26's
independent noise. Here each gate on k qubits gets a uniformly random non-identity k-qubit Pauli string with
probability q_k. The rate q_k = p · (4^k − 1)/(3 · 4^(k−1)) is chosen so that each qubit's marginal error rate is p, as
in step 26. The only change is correlation within a gate.

Spent seeds 980–985, p = 0.01, 2% readout, N = 1e4, the step 27 recipe unchanged (threshold 0.75):

| given graph | flow R < 1 | median flow R | given ratio | flags |
|---|---|---|---|---|
| full | 6/6 | 0.57 | 0.34–0.60 | 0/6 |
| missing 2 edges | 6/6 | 0.61 | 0.62–6.91 | 4/6 |

- **The correlated data really differ.** TV distance to step 26's independent-noise data at the same seed is
  0.045–0.069. Part of that is the different trajectory draws.
- **Correlation at 1% does not break the recipe on 6 seeds.** That is not evidence about 2%. The 2% stress was not
  explored. That is deliberate: C4 is a genuine prediction, not a fitted one.

## 2. Data and models (load-bearing details)

- **Data.** `src.step28.noise.correlated_grid_iqp(seed, p_gate, eta=0.02)`. The trajectory rng is
  `default_rng(40_000 + seed)` with 4000 trajectories, and that mixture is the defined target. The module is frozen at
  the spec commit.
- **Recipe.** Identical to step 27 (`src.step27.run`): `given_graph`, `raw_floor`, `flow_choice` with THRESH 0.75,
  ENLARGED (103), and FlipIQP settings (20 restarts, init 0.3, λ ∈ [0.5, 1]). Import them; do not copy-and-tune.
- **Arms.** me3, me_local, `given`, `enl` and `flow`, defined as in step 27.

## 3. Failure modes to recognise

1. **False alarms rise at p = 0.02.** Correlated errors leave residual that the damping cannot absorb. Report it; the
   flagged seeds go to `enl`. Do not move the threshold.
2. **λ pinned at 0.5.** Report the count. Do not widen the bound.
3. **Slow fits.** About 55–70 min per job with 12 parallel jobs. Keep the stop-loss.

## 4. Instances

| Condition | Given graph | p_gate | Seeds | Role |
|---|---|---|---|---|
| `cm01` | missing 2 edges | 0.01 | 1040–1053 | test (primary) |
| `cf01` | full | 0.01 | 1040–1053 | test |
| `cm02` | missing 2 edges | 0.02 | 1040–1053 | test (stress) |

All seeds below 1034 are spent. 42 jobs, launched in the order above.

## 5. Hypotheses (fixed now)

| ID | Statement | PASS if |
|---|---|---|
| C1 (primary) | recipe beats MaxEnt(3), wrong graph, correlated p = 0.01 | G_flow < G_me3 on ≥ 11/14 (`cm01`); sign p = 0.029 |
| C2 | recipe beats MaxEnt(3), correct graph, correlated p = 0.01 | ≥ 11/14 (`cf01`) |
| C3 | alarm quiet on the correct graph | flags ≤ 2/14 (`cf01`) |
| C4 | recipe beats MaxEnt(3), wrong graph, correlated p = 0.02 | ≥ 11/14 (`cm02`) |

Reported, with no verdict, per condition:
- median R of flow / given / enl against me3 and me_local;
- flags and missed alarms;
- pinned λ;
- median λ;
- ratio ranges.

## 6. Readings

- **F1, all PASS.** Within-gate correlation at a matched marginal rate does not hurt. Per-qubit damping is a sufficient
  noise model up to 2%.
- **F2, C1–C3 PASS, C4 FAIL.** Correlated noise sets a ceiling between 1% and 2% on wrong-graph data. Report it as the
  limit.
- **F3, C1 or C2 FAIL.** Correlated noise breaks the recipe at 1%. The open limit for hardware is then a correlated
  noise model.
- **C3 FAIL with C1/C2 PASS.** Report "always enlarge" as the fallback, as in step 27's E2.

## 7. Budget, stop-loss, lever

- 12 workers. 42 jobs are about 4–5 h.
- **Stop-loss: 7 h.** Jobs still running are killed and count as failures.
- **Lever, if the projection after the first 12 jobs exceeds 7 h:** drop `cm02` before it starts. C4 is then
  "not tested" and counts as FAIL. Never cut restarts or `cm01`/`cf01` seeds.

## 8. Verify (`--verify` exits 0 only if)

- every planned job has a metrics.json, or the stop-loss or the lever is recorded;
- `verdicts.json` is reproducible from the metrics;
- `tests/test_step28.py` passes. Its tests are written before the run:
  - zero noise equals `grid_iqp`;
  - normalisation holds;
  - the per-qubit marginal error rate implied by q_k equals p for k = 1, 2, 4;
  - the recipe objects are step 27's (same THRESH, same functions);
  - the seeds are fresh (≥ 1034).

## 9. Build order

Tests → commit code → launch → after 3 min check `errors.log` is empty → `--report`, `--verify` → note and README row on
master.

## Working style

- Guesses are marked in comments.
- Commit with explicit paths. Never push.
- If blocked by a hook, report it; do not rephrase around it.
- Do not edit this spec, the tests, or `--verify` after launch.
