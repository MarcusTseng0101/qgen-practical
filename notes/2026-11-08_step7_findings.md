# Step 7 findings: at matched peakedness the advantage mostly returns, but not cleanly at n = 16 (synthetic, n = 12–16)

Research note, 2026-11-08.

**Sources**
- Results: branch `step7-collision`, commit 72d47b1, with `results/step7/SUMMARY.md`,
  `verdicts.json`, `table.csv` and `figures/step7/`.
- Spec: `specs/step7_collision_matched.md`, frozen at 3407d50 and **designed after step 6**.

**Checks**
- `check.sh --stage 21` exits 0. I re-ran it independently on the worktree.
- R, the verdicts and the per-cell medians were recomputed independently from the 30
  `metrics.json` files and step 5's n = 12 data. They agree with the SUMMARY.

**Process caveat:** at the user's request, the harness hooks (the PreToolUse guard and the Stop
check) were removed from the worktree for this run, and the builder ran end to end without stops.
`check.sh` was run afterwards as an acceptance check, not as a hook. The method rules (no extra
restarts, unchanged optimizer, closed `src/step1..6`) were given in the prompt only. The check
confirms that the closed source and the matched σ were respected.

**Required caveat:** the n = 12 reference and nearby n = 14 points are data already seen. G is the
generic IQP (no oracle). n ≤ 16 proxies are not hardness evidence.

## Setting

- **Target:** `iqp4`, N = ∞. σ is chosen so that the target's median collision ratio matches
  n = 12's at σ = 0.15 / 0.175 / 0.2 (levels A / B / C: collision ratio 561 / 284 / 134).
  - Matched σ: n = 14 uses 0.193 / 0.213 / 0.236; n = 16 uses 0.231 / 0.251 / 0.274.
  - The achieved collision ratios are within 3% of each level.
- **Grid:** 30 instances, with nothing cut. Fits are unchanged from step 6.
- **Run time:** the grid took about 4.2 h (13:08 to 17:22) against a 3.38 h projection.

## 1. Frozen hypotheses: C1, C2 and C3 fail; C4 passes

| ID | Verdict | Numbers, median R [IQR] |
|---|---|---|
| C1 (level B: R < 1 at both n) | **FAIL** | n = 14: 0.870 [0.756, 0.884], R < 1. n = 16: 0.654 [0.651, 1.105], undecided. |
| C2 (level C: R < 1 at both n) | **FAIL** | n = 14: 0.706 [0.580, 0.888], R < 1. n = 16: 0.799 [0.593, 1.313], undecided. |
| C3 (level A: median R ≥ 1 at both n) | **FAIL** | n = 14: 0.754 [0.738, 0.825], R < 1. n = 16: 0.832 [0.576, 1.230]. |
| C4 (n = 16: G residual ≤ 1e-2 at B and C) | PASS | B: 2.1e-3 (max 9.7e-3); C: 1.6e-3 (max 4.8e-3) |

**Frozen reading rule (spec section 4):** C1 and C2 fail at n = 16 while C4 passes. The rule
therefore reads: *the advantage shrinks with n even at matched peakedness, and under-training does
not explain it.*

## 2. What the numbers show (medians; res is G's training residual)

| Level | n = 12 (step 5) | n = 14 | n = 16 |
|---|---|---|---|
| A (coll ≈ 561) | 1.35 (?) | **0.754** (< 1) | 0.832 (?) |
| B (coll ≈ 284) | **0.670** (< 1) | **0.870** (< 1) | 0.654 (?) |
| C (coll ≈ 134) | **0.577** (< 1) | **0.706** (< 1) | 0.799 (?) |

Per-seed R at n = 16:

| Level | seed 0 | seed 1 | seed 2 | seed 3 | seed 4 |
|---|---|---|---|---|---|
| A | 0.36 | 1.25 | 1.23 | 0.58 | 0.83 |
| B | 0.39 | 1.28 | 1.11 | 0.65 | 0.65 |
| C | 0.59 | 1.34 | 1.31 | 0.80 | 0.58 |

- **The frozen rule overstates the failure; this is the honest qualification.** The n = 16 cells
  fail because they are undecided, not because R ≥ 1.
  - Every median is below 1.
  - **Seeds 1 and 2 give R > 1 at all three levels**, and seeds 0, 3 and 4 give R < 1 at all three.
  - The split is by target instance, not by σ. G's residual is ≤ 1e-2 for both groups at B and C,
    so it is not under-training. Some iqp4 instances at n = 16 are completed better by MaxEnt(3)
    whatever the peakedness.
- **Matching peakedness undoes most of step 6's collapse.** At fixed σ = 0.2, n = 16 gave R = 1.38,
  and at σ = 0.175 it gave 1.81. At the matched σ, the medians are 0.65–0.83. Most of step 6's
  "window shrinks with n" was the target getting more peaked at fixed σ. Exploratory: this is an
  across-step comparison, not a frozen test.
- **The crossing does not stay fixed in collision coordinates (C3 fails).** At level A, where n = 12
  was undecided at 1.35, n = 14 is clearly R < 1. With n, the crossing moves toward *more* peaked
  targets.
  - One candidate reason: at matched collision ratio, D3 grows with n. At level B it is 0.216, 0.247
    and 0.304 for n = 12, 14 and 16. So matched peakedness gives MaxEnt(3) *more* to miss at larger
    n, which favours the IQP.
  - Collision ratio and completion room are therefore not the same axis. Neither one alone fixes
    where R crosses 1. This reading was not tested.
- **Both errors fall together at n = 16.** G_iqp and G_maxent3 are both about 1.2–1.5e-4 at every
  level. R ≈ 1 is a near tie, and the instance-level variation decides its sign.

## 3. What steps 5–7 add up to

- On IQP-like but misspecified targets (iqp4), the generic weight-≤3 IQP beats MaxEnt(3) at
  completing orders 4–6 only inside a window.
  - At n = 12 and 14 the window is clear (R ≈ 0.6–0.9).
  - At n = 16 it holds for the median but not for every instance: 2 of 5 seeds lose at every level.
- Step 6's apparent collapse with n was mostly a design artifact. The fixed layout counts made the
  target more peaked as n grew.
- Even at matched peakedness, the advantage at n = 16 is **weaker and less reliable** than at
  n = 12. The margin goes from about 2× in the IQP's favour to a near tie with instance-dependent
  sign. The data do not support a growing advantage with n.
- Peakedness and completion room (D3) both matter. A clean scaling test would have to match both,
  or match D3 directly.

## 4. Candidate next steps (not decided)

- **What separates the losing seeds at n = 16:** compare seeds 1–2 with 0, 3 and 4 on target
  structure, for example the weight-4 angle size relative to the weight-≤3 part, or the overlap of
  the weight-4 supports with the triples. This is diagnostic, cheap, and needs no new fits.
- **A D3-matched comparison at n = 14 and 16**, to test whether completion room, not peakedness, is
  the axis that fixes the crossing.
- **The latent-class mixture baseline** and the **real-data D3 probe** are still open from steps
  4–5. They are what decides practical relevance.
