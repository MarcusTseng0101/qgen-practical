# Step 17 spec: first real-data probe, MNIST reduced to 16 bits (qgen-practical)

Status: **frozen** once committed. Written after the step 16 findings and the mid-term update box,
which recommends a real-data probe, and after a 2-split pilot on development splits. Claude chose
this step under the user's standing instruction to take the recommended option. Sections 2–4 are
frozen; any change needs a numbered amendment, written before the run.

**Harness note.** As in steps 9–16, no hook or `BUDGET_OK` is installed. The acceptance check is
`python -m src.step17.run --verify`, which must exit 0.

## 1. Question

Does a real binary dataset sit in the IQP-like regime where the gated IQP beats MaxEnt(3)? Or does
the gate correctly fall back to MaxEnt(3)?

**Pilot** (`src/step17/pilot.py`, `results/step17/pilot/`; split seeds 10 and 11):

| | split 10 | split 11 |
|---|---|---|
| G's training residual r_N | 1.08 | 0.94 |
| noise floor | 0.023 | 0.023 |
| excess | +1.06 | +0.92 |
| gate picks the IQP | no | no |
| R (held-out) | 4.72 | 4.59 |
| D3 | 0.58 | 0.57 |

The IQP loses at every level from 4 to 6.

## 2. Design

**Data (fixed before the pilot; `src/step17/data.py`).**
- The 70 000 MNIST images, train plus t10k. Pinned by SHA-256:
  - train-images: `440fcabf…3609`;
  - t10k-images: `8d422c7b…4e6`.
- Reduction:
  1. crop the centre 20×20;
  2. average-pool 5×5 blocks to 4×4;
  3. threshold each block at its median over all 70 000 images.

  This gives n = 16. MNIST labels are not used.

**Splits.**
- Split seed s permutes the rows with `default_rng(2000 + s)`.
- The first N_train = 3e4 rows train, and the other 4e4 rows test. N_train = 3e4 is the N at
  which step 16 validated the gate.
- **Split seeds 100–119**, which are fresh: the pilot used 10 and 11.
- The 20 splits share one dataset. They are **not** independent instances. They measure stability
  under resampling, not generality across datasets.

**Fits.** MaxEnt(3) and G (3 restarts, `fit_restarts`) are fit to the same training moments, as
in step 14.

**Completion.** This is the noise-corrected held-out gap:

G = mean_l mean_{|A|=l} [(f_A(model) − f̂_A(test))² − (1 − f̂_A(test)²)/N_test], for l = 4, 5, 6.

R = G(IQP) / G(MaxEnt3).

**Gate.** Step 14's rule, unchanged: use G iff r_N − Σ(1 − f̂²)/N_train ≤ τ = 1e-2.

`src/step1..16` are never edited.

## 3. Frozen hypotheses

| ID | Statement | Kind |
|---|---|---|
| U1 | The gate picks the IQP on ≤ 2/20 splits **and** has ≤ 2 losses | **primary** |
| U2 | Ungated, R ≥ 1 on ≥ 15/20 splits | secondary |

**Reading rules, fixed now:**
- **U1 and U2 PASS.** MNIST-16 is not in the IQP-like regime. The IQP loses there, and the gate
  correctly falls back to MaxEnt(3). The real-data result is **negative for the IQP and positive
  for the gate**: the safety half carries over to one real dataset; the gain half is not shown on
  real data.
- **U1 FAIL with losses > 2.** The gate is unsafe on real data. This contradicts steps 12–16 and
  must be reported as such.
- **U1 FAIL with wins** (picked > 2 and losses ≤ 2). Real data reached the IQP-like regime. This
  is unexpected from the pilot.

**Exploratory:**
- R per level;
- D3;
- the gap between r_N and the floor;
- the median and IQR of R.

## 4. Artifacts and acceptance

- Results: `results/step17/split_<s>/metrics.json`, plus `verdicts.json` and `SUMMARY.md`.
- The SUMMARY opens with: "Step 17 was designed after a 2-split pilot; split seeds 100–119 are
  fresh; the 20 splits share one dataset (MNIST reduced to 16 bits) and are not independent
  instances; the gate is step 14's, unchanged; completion is scored on held-out rows with test
  noise removed."
- `--verify` checks:
  - the spec is committed and unchanged;
  - `src/step1..16` are unchanged since the step 16 code commit 5317a9d;
  - 20 metrics files are present, each with N_train = 3e4, N_test = 4e4, 3 restarts and the pinned
    SHA-256;
  - the SUMMARY sentence and U1–U2 are marked;
  - `tests/test_step17.py` passes.
- **Tests, written before the run:**
  - the corrected gap equals the raw gap minus the noise term, on a hand example;
  - the data are pinned (shape (70000, 16), the SHA-256 matches);
  - split seeds 100–119, disjoint from the pilot;
  - the gate is step 14's.

## 5. Budget

- The pilot took 3–4 min per split. 20 splits on 16 workers take about 10 min.
- **Stop-loss: 1 h. Named lever:** none is needed at this cost. If the stop-loss is hit, report
  the split seeds completed. Never drop splits silently.
