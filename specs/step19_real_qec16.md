# Step 19 spec: real quantum-hardware data, Google surface-code detection events (qgen-practical)

Status: **frozen** once committed. Written after steps 17 and 18 and a 2-split pilot on one
development run. Claude chose this step under the user's standing instruction to take the
recommended option. Sections 2–4 are frozen; any change needs a numbered amendment, written
before the run.

**Harness note.** No hook or `BUDGET_OK` is installed. The acceptance check is
`python -m src.step19.run --verify`, which must exit 0.

## 1. Question

Detection events are parities of sparse independent errors, so this is parity-structured data
from real hardware. Does the step 14 gate stay safe on it?

Step 18 showed that the gate *can* be fooled by data that the IQP fits at low order but completes
badly.

**Pilot** (`src/step19/pilot.py`, `results/step19/pilot/`; run bX centre 3_5, split seeds 10–11):

| | split 10 | split 11 |
|---|---|---|
| G's training residual r_N | 3.7e-4 | 1.9e-4 |
| noise floor | 0.019 | 0.019 |
| excess | −0.018 | −0.019 |
| gate picks the IQP | **yes** | **yes** |
| R (held-out) | **4.86** | **1.63** |

G loses at every order from 4 to 6. MaxEnt(3)'s corrected gap (2–4e-5) is close to the test-noise
correction, so the size of R is noisy; the sign was the same in both splits.

## 2. Design

**Data (`src/step19/data.py`, fixed before the pilot).**
- Zenodo 6804040, `google_qec3v5_experiment_data.zip`, md5 `a7fd8b48…dc217d`.
- The distance-3, 3-round surface-code experiments, keeping detectors 4–19, which are all 8
  stabilizers at t = 1 and t = 2. That gives n = 16, with 50 000 shots per run.

**Runs.**
- The 8 runs are bases X and Z at 4 chip centres.
- The **7 runs other than the pilot run** (bX centre 3_5) are tested. Each is a separate hardware
  experiment.
- One split per run, split seed 100: shots are permuted with `default_rng(2100)`. N_train = 3e4,
  N_test = 2e4.

**Fits, scoring and gate:** as in step 17.
- MaxEnt(3) and G (3 restarts) are fit to the same training moments.
- Completion is the noise-corrected held-out gap on orders 4–6. R = G(IQP) / G(MaxEnt3).
- The gate is step 14's, unchanged.

`src/step1..18` are never edited.

## 3. Frozen hypotheses

| ID | Statement | Kind |
|---|---|---|
| V1 | Safety: the gate has ≤ 1 loss over the 7 runs (a loss means picked and R ≥ 1) | **primary** |
| V2 | Ungated, R ≥ 1 on ≥ 6/7 runs | secondary |

**Reading rules, fixed now:**
- **V1 FAIL.** The order-≤3 gate is unsafe on real parity-structured hardware data. The step 18
  failure mode occurs in practice. The claim's safety clause must be restricted to data that the
  IQP fails to fit at low order. This is the outcome the pilot predicts.
- **V1 PASS.** The safety clause survives one real parity-structured dataset.
- **V2** tells whether the IQP loses on this data ungated, whatever the gate does.

**Exploratory:**
- R_raw, which is R without the test-noise correction;
- R per level;
- r_N against the floor;
- D3;
- a held-out order-4 validation: whether G's order-4 error on the training rows' order-4 moments
  would have flagged it. This is step 18's suggested fix, reported here and not used as a gate.

## 4. Artifacts and acceptance

- Results: `results/step19/<run>/metrics.json`, plus `verdicts.json` and `SUMMARY.md`.
- The SUMMARY opens with: "Step 19 was designed after a 2-split pilot on one development run;
  the 7 tested runs were not used in the pilot; the gate is step 14's, unchanged; completion is
  scored on held-out shots with test noise removed; this is error-correction syndrome data, not
  IQP-circuit output."
- `--verify` checks:
  - the spec is committed and unchanged;
  - `src/step1..18` are unchanged since 97648b2;
  - 7 metrics files exist, each with N_train = 3e4, N_test = 2e4, 3 restarts and the md5;
  - the SUMMARY sentence and V1–V2 are marked;
  - `tests/test_step19.py` passes.
- **Tests, written before the run:**
  - the reduction keeps the detectors with t ∈ {1, 2}, checked against the stim file;
  - the 7 tested runs exclude the pilot run;
  - the gate is step 14's.

## 5. Budget

- The pilot took 27 min per split with 2 jobs running. 7 jobs in parallel should take about
  40 min.
- **Stop-loss: 2 h.** Never drop runs silently.
