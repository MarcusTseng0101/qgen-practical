# Step 33: sampling quality, pre-registered (2026-11-17)

Spec: `specs/step33_sampling_quality.md` (b5d9599, frozen before any fit on the test seeds).
Code and tests: worktree `qgen-practical-step1`, commit 1124698. Results: commit 9f49191, `results/step33/`.
`python -m src.step33.run --verify` → **ALL PASS** (exit 0).

## Question

Does the fitted IQP model's advantage on the scored moments (orders 4–6) carry over to the whole distribution? The
test used 14 fresh seeds (1120–1133) in four settings at N = 1e4:
- `id`: ideal, local IQP;
- `g01`: FlipIQP at 1% gate noise;
- `mg01`: the recipe on the wrong (`miss`) graph at 1% gate noise;
- `xf02`: the recipe under coherent ε = 0.2 on the correct graph.

## Verdicts (reading L1, plus W1 and W2 PASS)

| ID | Statement | Count | Verdict |
|---|---|---|---|
| S1–S4 | TVD < MaxEnt(3): id, g01, mg01, xf02 | 13, 14, 12, 13 / 14 | PASS ×4 |
| S5–S8 | KL < MaxEnt(3): same | 13, 14, 13, 12 / 14 | PASS ×4 |
| W1 | xf02: model loses E_1 | 14/14 | PASS (the weakness is confirmed) |
| W2 | xf02: model loses MMD s = 2 | 14/14 | PASS (the weakness is confirmed) |

## Reported (no verdict)

Wins vs MaxEnt(3) / 14, with the median ratio in brackets.

| Metric | id | g01 | mg01 | xf02 |
|---|---|---|---|---|
| G | 13 (0.37) | 14 (0.47) | 12 (0.56) | 13 (0.58) |
| mean E_7..16 | 13 (0.10) | 13 (0.39) | 11 (0.48) | 13 (0.19) |
| E_1 | 3 | 2 | 3 | 0 |
| fidelity | 13 | 14 | 13 | 13 |
| MMD s = 0.5 | 13 | 13 | 10 | 13 |
| MMD s = 1 | 13 (0.57) | 14 (0.68) | 13 (0.80) | 14 (0.79) |
| MMD s = 2 | 5 (1.04) | 3 (1.10) | 4 (1.15) | 0 (1.23) |

Other reported quantities:
- **Median TVD** (model / ME3 / ME-on-graph):
  - id: 0.13 / 0.24 / 0.33
  - g01: 0.10 / 0.15 / 0.19
  - mg01: 0.11 / 0.15 / 0.22
  - xf02: 0.15 / 0.18 / 0.26
- **MaxEnt-on-graph** loses every metric to the model on at least 13/14 instances, except E_1, where its marginals
  equal ME3's.
- **Sample bound** m = 2 ln10 / (−ln F), model vs ME3:
  - id: 83 vs 36
  - g01: 240 vs 119
  - mg01: 214 vs 119
  - xf02: 99 vs 71
- **Alarms:** mg01 8/14, xf02 3/14.
- **Per-order wins** for mg01 at orders 5–16 are only 9–11, so the wrong-graph advantage rests mainly on orders 2–4.

## What it means

- The sampling advantage is now a tested result in all four settings, and paper §VI no longer says "exploratory".
- The single-bit weak spot is confirmed. A wide-kernel MMD reverses the ranking, so a paper should report the
  per-order errors and not a single MMD value.
- **xf02 G on these seeds: 13/14 (R 0.58).** Step 29's test on seeds 1060–1073 failed with 10/14 (R 0.74). This
  number is reported only and does not overturn step 29. It does suggest that the coherent G loss varies between
  instance sets. Any claim about it needs a pooled or larger test, not this number.

## Run log

The machine rebooted at about 03:39, 1 h 40 min into the run. At that point 14 of 56 jobs were complete and intact.
The run was resumed with unchanged code, which skips finished jobs. The fits are seeded, so the restart cannot
change a result. All 56 jobs finished with rc = 0 at 08:07, inside the 16 h stop-loss, which was counted from the
first launch. Details are in `results/step33/RESTART.txt`.

## Paper changes (master)

- §VI is rewritten on the step 33 data: Table III has four columns, and Fig. 2 is a 2×2 grid read from
  `results/step33/verdicts.json`.
- The abstract, intro and discussion now describe a test on fresh instances.
- §V gained `\label{sec:coherent}`.
- The PDF has 6 pages and no overfull boxes. Prose: 16.9 words per sentence on average.
