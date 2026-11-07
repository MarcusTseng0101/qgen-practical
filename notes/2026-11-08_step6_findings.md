# Step 6 findings: the iqp4 advantage window moves up and shrinks with n (synthetic, n = 12–16)

Research note, 2026-11-08.

**Sources**
- Results: branch `step6-scaling`, commit 8b94e19, with `results/step6/SUMMARY.md`, `verdicts.json`,
  `table.csv` and `figures/step6/`.
- Spec: `specs/step6_iqp4_scaling_n.md`, frozen at 567aab6 and **designed after step 5**. Harness v7
  is at bccacee.

**Checks**
- `check.sh --stage 18` exits 0. I re-ran it independently on the worktree.
- R, the verdicts, σ\* and G_iqp max/min were recomputed independently from the 45 `metrics.json`
  files and step 5's n = 12 data. They agree with `verdicts.json`.

**Required caveat:** the n = 12 reference is data already seen. G is the generic IQP (no oracle).
n ≤ 16 proxies are not hardness evidence.

## Setting

- **Target:** `iqp4(σ, s)` with layout counts fixed at every n (n singles, 18 pairs, 8 triples, 6
  weight-4 generators). N = ∞ only.
- **Fits:**
  - G: the generic weight-≤3 IQP (469 generators at n = 14, 696 at n = 16), 3 restarts, unchanged
    optimizer.
  - MaxEnt(3): ridge 1e-8.
- **Grid:** 45 of 50 instances. n = 16 at σ = 0.25 was cut, following spec section 7 (the
  projection was 3.13 h against a 3 h budget; user decision A).
- **Run time:** the grid took about 5.8 h (20:40 to 02:31) against a 2.58 h projection. The n = 16 instances took
  4–53 min each, against the 400 s timing instance. The other processes on the machine were idle,
  so this is the method's own cost at n = 16, not load from other jobs.

## 1. Frozen hypotheses: S1, S2 and S3 fail; S4 passes

| ID | Verdict | Numbers |
|---|---|---|
| S1 | **FAIL** | σ = 0.2: n = 14 gives R = 0.889 [0.720, 1.04], undecided; n = 16 gives 1.38 [0.623, 1.51], undecided. n = 12 gave 0.577, R < 1. |
| S2 | **FAIL** | σ\*(14) = 0.185, inside the band [0.135, 0.185] by 0.0004. σ\*(16) is undefined: median R ≥ 1 at every σ that was run (10.9 / 4.91 / 1.81 / 1.38). |
| S3 | **FAIL** | σ = 0.175: n = 14 gives 1.08 [0.704, 1.32], undecided; n = 16 gives 1.81 [1.12, 2.02], R ≥ 1. |
| S4 | PASS | n = 16: G_iqp max/min = 1.54 over 4 σ (σ = 0.25 was cut). |

## 2. The picture (medians; res is G's training residual, coll is the collision ratio)

| σ | n = 12: R (res, coll) | n = 14: R (res, coll) | n = 16: R (res, coll) |
|---|---|---|---|
| 0.125 | 2.82 (1.0e-2, 1017) | 4.32 (2.1e-2, 3763) | 10.9 (2.0e-2, 14846) |
| 0.15 | 1.35 (8.7e-3, 561) | 1.88 (1.3e-2, 2016) | 4.91 (1.9e-2, 7850) |
| 0.175 | **0.670** (4.5e-3, 284) | 1.08 (8.1e-3, 986) | 1.81 (1.2e-2, 3769) |
| 0.2 | **0.577** (2.1e-3, 134) | 0.889 (4.3e-3, 448) | 1.38 (7.2e-3, 1673) |
| 0.25 | 0.891 (1.0e-3, 27) | **0.882** (1.5e-3, 84) | cut |

- **The window moves to larger σ and narrows as n grows.**
  - At n = 12, R < 1 holds at σ = 0.175–0.2.
  - At n = 14, R < 1 holds only at σ = 0.25 (0.882 [0.859, 0.918]).
  - At n = 16, R < 1 holds at no σ that was run. The cut cell, σ = 0.25, is where n = 14's
    window lies, so whether n = 16 has any window is **untested**.
- **The floor stays flat, but the room shrinks faster than the floor.**
  - G_iqp falls slightly with n: about 4e-4 at n = 12, 2–3e-4 at n = 14 and 1.4–2.1e-4 at n = 16.
  - G_maxent3 falls faster at fixed σ: at σ = 0.2 it is 7.3e-4, 2.6e-4 and 1.3e-4.
  - So the completion room per σ shrinks with n even though D3 does not. The step-6 design reasoning
    ("D3 is n-independent, so σ\* should not move") is wrong. D3 does not predict MaxEnt(3)'s
    order-4–6 error across n.
- **This lines up with the peakedness caveat**, as an exploratory reading only. With fixed layout
  counts, the collision ratio grows about 3.5–3.7× per +2 bits. At the σ where R < 1, the collision
  ratio is about 130–280 at n = 12 and 84 at n = 14 (σ = 0.25). In this family, the advantage seems
  to need the target to stay only moderately peaked, which pushes σ up as n grows. This was not
  tested.

## 3. Training at larger n (spec section 5)

- Median G residual rises with n at fixed σ: at σ = 0.15 it is 8.7e-3, 1.3e-2 and 1.9e-2.
- **Seed 1 at n = 16 has the worst fit at every σ:** 0.16, 0.18, 3.6e-2 and 3.0e-2. Its R values
  (30.5, 14.3, 2.0, 1.5) may be biased upward.
  - Dropping it would not rescue any n = 16 cell: among the other four seeds, at least
    two give R ≥ 1 at every σ (SUMMARY, "Failure modes").
  - With an unchanged optimizer, under-training probably adds to R at n = 16, but it does not set the
    sign.
- MaxEnt hit maxiter in 2 of 45 instances (n = 16 seed 3 at σ = 0.125 and 0.15), with residuals
  ≤ 4e-11.

## 4. What this adds to steps 3–5

- The step-5 window is **not stable in n** under fixed-count misspecification. Its location tracks
  how peaked the target is rather than σ, and by n = 16 it is gone from σ ≤ 0.2.
- This weakens any practical reading of steps 4–5: the IQP advantage over MaxEnt(3) on IQP-like but
  misspecified data shrinks, or moves into a different regime, as n grows. That is the opposite of
  what a scalable advantage would need.
- Two confounds keep this from being clean:
  1. The fixed layout counts make the target more peaked with n.
  2. G under-trains more at n = 16.

  A design with layout counts that scale with n, or with σ matched by collision ratio, would separate
  them.

## 5. Candidate next steps (not decided)

- **Collision-matched comparison:** at n = 14 and 16, choose σ so that the collision ratio matches
  n = 12's at σ = 0.175–0.2, and ask whether R < 1 returns. This tests the reading in section 2
  directly. The n = 16, σ = 0.25 cell, or σ ≈ 0.3, would be part of it.
- **A well-specified `iqp` control at n = 16**, to separate "misspecification hurts more at larger
  n" from "G trains worse at larger n".
- **The latent-class mixture baseline** and the **real-data D3 probe** remain open from steps 4–5.
