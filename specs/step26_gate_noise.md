# Step 26 spec: gate-level noise — does a learned local damping keep the IQP ahead?

Status: **frozen** once committed. Written 2026-11-14 after step 25 (C1) and the step 26 exploration on spent seeds
980–983 (branch `step18-adversarial` `explore/step26/`). Claude chose this step under the user's standing instruction to
take the recommended option. Every number in §5 is fixed before any model is fitted on the test seeds 1000–1013.

**Deliverable.** A pre-registered test of two IQP variants on gate-noisy grid data, with verdicts. It is **not** a
noise-characterisation study and **not** a hardware-accurate simulator: the noise model is a stand-in for "the data are
not exactly in the noiseless family".

**Acceptance (the one definition of done):** `python -m src.step26.run --verify` exits 0. A FAIL hypothesis is a result,
not a reason to edit the check, the tests, or this spec.

## 1. Evidence so far (do not re-derive; act on it)

Spent seeds 980–983, full 4×4 graph, 2% readout, N = 1e4. R = G_model / G_me3, so R < 1 means the IQP wins.

| Gate noise p | step 25 pipeline R | FlipIQP R | residual alarm (pipeline) |
|---|---|---|---|
| 0.005 | 1.15, 0.74, 0.40, 0.68 | 0.76, 0.58, 0.40, 0.82 | 0/4 fired (ratio 0.43–0.66) |
| 0.01 | 1.03, 0.93, 0.72, 0.94 | 0.53, 0.35, 0.46, 0.71 | 0/4 fired (ratio 0.61–0.70) |

**Interpretation.**
- Gate noise moves the data out of the noiseless IQP family. The step 25 pipeline only removes readout noise, so its win
  erodes toward R ≈ 1 at p = 0.01.
- FlipIQP is the 85-gen local IQP plus 16 learned per-qubit damping factors λ_j, with f_S = Π_{j∈S} λ_j · f_S^IQP(θ).
  It absorbs most of the effect. Learned λ were 0.63–0.96, never at the bound.
- It needs no calibrated η.

## 2. Data and models (load-bearing details)

- **Data.** `src.step26.noise.noisy_grid_iqp(seed, p_gate, eta=0.02)`.
  - The circuit is H layer → the 49 target gates (in TARGET_GENS order) → H layer.
  - After every gate, each of its qubits gets X, Y or Z with probability p_gate/3 each.
  - Readout flips at η = 0.02 follow.
  - The distribution is **defined** as the mean over 4000 trajectories from `default_rng(30_000 + seed)`, so it is a
    fixed mixture and G is exact against it. Do not "improve" it by raising the trajectory count mid-run: that changes
    the target, and the seeds are then no longer comparable.
- **Graph.** The full 4×4 grid (85 candidates) is given correctly. Graph errors were step 25's question; mixing them in
  here would leave a failure with two possible causes.
- **Arms.** All are fitted to the same N = 1e4 order-≤3 moments.
  - `me3`: MaxEnt(3).
  - `me_local`: MaxEnt on the 76 grid masks.
  - `pipe`: the step 25 pipeline (`src.step25.run.pipeline`) with η = 0.02 and the full graph. It includes the 0.9
    alarm and the enlargement.
  - `flip`: `src.step26.flipiqp.FlipIQP` on the 85 local gens, fitted on **raw** moments (no η), 20 restarts.
    - θ init N(0, 0.3²), λ init 1, λ ∈ [0.5, 1]. The bound and the init are guesses.
    - Its output is the IQP distribution pushed through the learned flip channel.
- No arm may see θ, p_gate, the trajectory seed, or N = ∞ moments.

## 3. Failure modes to recognise (symptom → mechanism → what to do)

1. **λ pinned at the bound.**
   - Symptom: any λ_j = 0.5.
   - Mechanism: the damping absorbs signal that θ should carry (λ–θ trade-off on the singles).
   - Do: report the count of pinned λ per condition. Do **not** widen the bound and rerun; that is a new spec.
2. **False alarm in `pipe`.**
   - Symptom: flag = True on the correct graph.
   - Mechanism: gate noise raises the residual above 0.9 × floor.
   - Do: report the flag rate. A flag sends `pipe` to the 103-gen graph, which is a legitimate pipeline outcome. Do
     not change the threshold.
3. **Slow fits.** FlipIQP fits took 15–33 min in exploration, against about 10 for `pipe`.
   - Do: keep the stop-loss in §6. If it trips, missing seeds count as failures. Do not cut restarts mid-run.
4. **Simulator drift.**
   - Symptom: `test_zero_noise_equals_ideal` fails after an edit.
   - Mechanism: a phase or sign convention changed.
   - Do: stop. The noise module is frozen at the commit that froze this spec.

## 4. Instances

| Condition | p_gate | Seeds | Role |
|---|---|---|---|
| `g005` | 0.005 | 1000–1013 | test |
| `g01` | 0.01 | 1000–1013 | test (primary) |
| `g02` | 0.02 | 1000–1013 | stress, report only |

All seeds below 1000 are spent. 42 jobs.

## 5. Hypotheses (fixed now)

| ID | Statement | PASS if | Sign-test p |
|---|---|---|---|
| G1 (primary) | FlipIQP beats MaxEnt(3) at p = 0.01 | R_flip < 1 on ≥ 11/14 (`g01`) | 0.029 |
| G2 | FlipIQP beats MaxEnt(3) at p = 0.005 | R_flip < 1 on ≥ 11/14 (`g005`) | 0.029 |
| G3 | the learned damping matters at p = 0.01 | G_flip < G_pipe on ≥ 11/14 (`g01`) | 0.029 |

Reported, with no verdict:
- median R of every arm against me3 and against me_local, in every condition (including `g02`);
- pipe flag rate;
- pinned-λ count;
- median λ;
- resid / floor.

## 6. Readings

- **D1, G1–G3 PASS.** A 16-parameter local noise model is enough to keep the connectivity-prior advantage under gate
  noise at realistic rates. Paper recipe: local IQP + learned per-qubit damping.
- **D2, G1 and G2 PASS, G3 FAIL.** Both IQP variants win and the damping is not needed. Use the simpler pipeline.
- **D3, G2 PASS, G1 FAIL.** The advantage holds at 0.5% gate error but not at 1%. Report the noise ceiling.
- **D4, G2 FAIL.** Gate noise removes the advantage even at 0.5%. This is the main open limit for real hardware.

## 7. Budget, stop-loss, lever

- Per job: target about 0.5–1.5 min, `pipe` about 10–20 min, `flip` about 15–33 min (8 parallel). 42 jobs is about
  3–4 h with 8 workers.
- **Stop-loss: 6 h wall clock.** Jobs still running are killed and count as failures. Rerunning them needs a written
  amendment.
- **Lever, if a projection made after the first 8 jobs exceeds 6 h:** drop `g02` (report-only) before it starts. Never
  cut restarts or seeds of `g005`/`g01`.
- Each job writes `results/step26/<cond>/seed_<s>/metrics.json`, so the run is resumable.

## 8. Verify (`--verify` exits 0 only if)

- every planned job has a metrics.json, or the stop-loss or the lever is recorded in `run_log.txt`;
- `verdicts.json` is recomputed from the metrics and matches;
- `tests/test_step26.py` passes. Its tests are written before the run:
  - zero noise reproduces `grid_iqp` exactly;
  - a final Z equals a bit flip;
  - noise preserves normalisation and shrinks orders 4–6;
  - the FlipIQP gradient matches finite differences;
  - FlipIQP at λ = 1 equals the plain IQP.

## 9. Build order (each step gates the next)

1. Tests pass (`pytest tests/test_step26.py`). Do not launch before they do.
2. Commit the code before the run.
3. Launch. After 3 min check that `errors.log` is empty. If it is not, stop, fix, and relaunch from a clean
   `results/step26`.
4. `--report`, `--verify`, then the note and the README row on master.

## Working style

- Hyperparameters marked "guess" stay marked in the code comments.
- Commit at each checkpoint with explicit paths. Never push.
- If a hook or permission rule blocks an action, report it; do not rephrase the command around it.
- Do not edit this spec, the tests, or `--verify` after the run starts.
