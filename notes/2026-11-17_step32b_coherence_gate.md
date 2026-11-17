# Step 32b result: a residual coherence gate picks CohIQP or FlipIQP correctly at N = 1e5 (completed run: J1, Z1–Z4 PASS; as-spec at the stop-loss: Z1 PASS only)

**Name.** This is the step of `specs/step32_coherence_gate.md` (f674f40). It is called **32b** here because
`notes/2026-11-16_step32_sampling_quality.md`, written by another session the same evening, also used the number 32.

**Provenance.**
- Code: branch `step18-adversarial` ebfd930 (`src/step32/run.py`, `tests/test_step32.py`).
- Results: dd3445c (`results/step32/`).
- `python -m src.step32.run --verify` → ALL PASS. ALL PASS means the run is complete and reproducible, not that the
  hypotheses passed.

**Gate.** Fit FlipIQP on the correct graph. If its raw-floor ratio resid / Σ(1 − f̂²)/N is above 1.0, use CohIQP;
otherwise use FlipIQP. Both fits are step 31's, unchanged. The data are N = 1e5 with 2% readout:
- `cf`: coherent miscalibration, ε_std 0.2;
- `pf`: Pauli noise, 1%.

R = G / G_me3, and lower is better.

## The run was interrupted twice; two readings are reported

| When (2026-11-16/17) | Event |
|---|---|
| 18:46 | Launch, 56 jobs with 20 workers. The spec stop-loss is 12 h, so it falls at **06:46**. |
| ~01:44–01:52 | The launcher and workers die when the Claude session exits. 31/56 metrics are on disk. |
| 01:56 | Relaunched by Claude, as a resumable `--all` that skips finished jobs. |
| ~03:39 | **The machine reboots** (also recorded in `results/step33/RESTART.txt`). Every worker dies, with no progress kept. |
| ~05:15 | The user relaunches the remaining 25 jobs (decision A). |
| ~09:50 | All 56 done. There are no errors. |

All of this is in `results/step32/run_log_part1.txt`; `run_log.txt` is the third launch.

The fits are seeded, so a restarted job computes the same result it would have computed without the interruption.
The 25 jobs finished after the spec's 06:46 stop-loss, though. Two readings are therefore reported:

| ID | Statement | **Completed run** (all 56) | **As-spec** (metrics written after 06:46 count as missing) |
|---|---|---|---|
| Z1 (primary) | gate beats MaxEnt(3), coherent | 14/14 **PASS** (need 11) | 11/14 **PASS** |
| Z2 | gate beats always-FlipIQP, coherent | 9/14 **PASS** (need 9) | 8/14 **FAIL** |
| Z3 | gate stays with FlipIQP, Pauli | 14/14 **PASS** (need 12) | 0/14 **FAIL**, not tested |
| Z4 | gate beats MaxEnt(3), Pauli | 14/14 **PASS** (need 12) | 0/14 **FAIL**, not tested |

- `verdicts.json` holds the completed-run reading. `verdicts_as_spec_0646.json` holds the as-spec reading, with the 25
  late files listed.
- **The as-spec FAILs come from infrastructure, not from the data.** Before 06:46, no Pauli job had finished in the
  relaunch, and 3 coherent FlipIQP jobs were also late.
- **The completed run is what the data say.** Its main caveat is that Z2 passes at exactly its threshold (9/14).

**Reading, completed run: J1.** One residual-based gate gives a recipe that handles both coherent and stochastic noise on
the correct graph at N = 1e5. It chose CohIQP on 12/14 coherent seeds and on 0/14 Pauli seeds.

## Reported (no verdict)

| cond | gate: median R (wins vs me3) | CohIQP | FlipIQP | oracle min | gate = oracle |
|---|---|---|---|---|---|
| cf | 0.37 (14/14) | 0.26 (14/14) | 0.50 (12/14) | 0.26 | 9/14 |
| pf | 0.16 (14/14) | 0.24 (14/14) | 0.16 (14/14) | 0.16 | 13/14 |

- **The gate gives up part of CohIQP's advantage on coherent data.** Its median is 0.37 against CohIQP's 0.26.
  - There are two misses of the expected kind: seeds 1105 and 1109 have ratios 0.91 and 0.89, just under 1.0. The gate
    kept FlipIQP there, although CohIQP was better on both (0.21 against 0.41, and 0.18 against 0.34).
  - On 3 seeds the gate picked CohIQP while FlipIQP was better: 1102 (ratio 1.01), 1107 and 1113.
  - Five coherent seeds had ratios between 0.8 and 1.25. Only one Pauli seed was in that band (1104, 0.80).
  - A lower threshold such as 0.85 would have caught both misses while keeping every Pauli ratio (max 0.80) below it.
    **This is post hoc and untested.**
- **Under Pauli noise the gate never fired.** Every ratio was at most 0.80. The gate matched the oracle on 13/14 seeds;
  the exception is 1106, where CohIQP was marginally better (0.386 against 0.410).
- **CohIQP convergence is the same as in step 31.**
  - All 70 restarts hit the 3000-iteration cap in both conditions.
  - ε reached the bound 14 times (cf) and 10 times (pf).
  - CohIQP's R may therefore be pessimistic.
- **CohIQP did better on these seeds than on step 31's.** Its coherent median is 0.26 here against 0.51 in step 31. That
  is seed-to-seed variation, which is why fresh seeds are used.

## For the paper

- **Recipe at N = 1e5 on the correct graph.**
  1. Fit FlipIQP.
  2. If its raw-floor ratio is above 1.0, also fit CohIQP and use it.
- **What it delivered (completed run).** It beat MaxEnt(3) on 28/28 seeds across coherent and Pauli noise. It never
  switched under Pauli noise. On coherent data it beat always-FlipIQP on 9/14, exactly at the pre-registered bar.
- **State plainly:**
  - two interruptions;
  - the as-spec reading;
  - the CohIQP iteration cap;
  - that the threshold sits close to some coherent seeds.

Wrong-graph cases at 1e5 were not tested with this gate, and the 0.75 enlargement alarm does not transfer to 1e5 (step 31).

## Next (recommended, not started)

The open pieces of the recipe at N = 1e5 are:
- the wrong-graph alarm, because its threshold must be recalibrated for 1e5;
- the gate threshold, where 0.85 against 1.0 is the open question.

Testing either needs a spec and fresh seeds.
