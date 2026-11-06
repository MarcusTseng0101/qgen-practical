# Step 4 amendment 1: mix calibration and how to read P1 (qgen-practical)

Status: **draft for user approval**, 2026-11-06. It amends `specs/step4_misspec_finite_n.md`
(frozen at fe7d058), and is written **after** two blind pre-run diagnostics:
- builder diagnostics D1 and D2 on branch `step4-misspec`, commit 32cdd04,
  `diagnostics/step4_pre/`;
- my own D3-only scan, D2b.

No completion quantity (G_iqp, G_maxent, R or any order-4–6 error) has been computed on any
step-4 target. The hypotheses K, R1, P1, P2, F1 and F2 keep their wording. This amendment
changes only the `mix` construction and adds reading rules. Every report must cite it.

## 1. What the diagnostics showed

**D1, the iqp4 residual at σ = 0.2, seeds 0–4 (blind):** the residual is a misspecification
floor, not a spurious minimum.

| seed | truth's weight-≤3 angles, unoptimized | from those, optimized | best of 10 random | ratio | restarts within 2× |
|---|---|---|---|---|---|
| 0 | 0.69 | 2.5e-3 | 2.0e-3 | 1.26 | 10/10 |
| 1 | 3.1 | 1.4e-3 | 8.6e-4 | 1.68 | 8/10 |
| 2 | 0.64 | 1.6e-3 | 1.3e-3 | 1.30 | 7/10 |
| 3 | 1.26 | 5.0e-3 | 4.0e-3 | 1.23 | 10/10 |
| 4 | 0.80 | 2.1e-3 | 2.1e-3 | 0.98 | 9/10 |

- The 6 weight-4 generators move the order-≤3 moments a lot: dropping them gives a residual
  of 0.6–3.
- Starting from the truth does not beat random starts. 44 of the 50 random restarts land
  within 2× of the warm start.
- So the ~1e-3 residual is the best a weight-≤3 IQP does on these moments.

**D2 and D2b, mix D3 only (blind):** no K = 3 setting reaches the planned reference.
- With K = 3, D3 rises only slowly with δ: 2.9e-3 at δ = 0.8, 1.1e-2 at δ = 0.99.
- More components help, but only up to D3 ≈ 0.04:

| K | δ = 0.8 | δ = 0.9 | δ = 0.99 |
|---|---|---|---|
| 3 | 2.9e-3 | 6.0e-3 | 1.1e-2 |
| 6 | 7.2e-3 | 1.3e-2 | 2.1e-2 |
| 12 | 6.2e-3 | 1.3e-2 | 2.5e-2 |
| 24 | 7.1e-3 | 1.7e-2 | 3.6e-2 |
| 48 | 7.5e-3 | 1.8e-2 | 3.9e-2 |

Product-Bernoulli mixtures at n = 12 do not reach the completion room of `iqp` at σ = 0.2
(D3 ≈ 0.19). They do reach that of `iqp` at σ = 0.1 (D3 ≈ 0.046).

## 2. Changes

1. **The mix construction and its calibration.**
   - **Reference:** the median D3 of `iqp` at **σ = 0.1** (from the step-3 table, ≈ 0.046),
     replacing σ = 0.2.
   - **Candidates:** K ∈ {3, 6, 12, 24, 48} × δ ∈ {0.8, 0.9, 0.99}.
     - Weights are Dirichlet(1, …, 1) and u ~ U(−0.5, 0.5)^(K×n), drawn from
       `default_rng(5000 + s)`.
     - `K_MIX` becomes a parameter. The K = 3 draws must stay bit-identical to the current
       ones, so the old calibration remains reproducible.
   - **Rule:** choose the (K, δ) whose median D3 over seeds 0–4 is closest to the reference
     on a log scale. From D2b this is expected to be K = 48, δ = 0.99 (D3 ≈ 0.039); the rule
     decides, not this sentence.
   - **Record:** write every candidate's D3 to `results/step4/calibration_amend1.json`, with
     the keys `chosen_K`, `chosen_delta`, `D3_by_K_delta` and `reference_D3`. Keep
     `calibration.json` unchanged as the record of the original rule.
   - **Why:** under the original rule, P2 would have tested a target with about 1/64 of the
     comparison room. A null result there would say nothing.
   - **Consequence to report:** P2 compares IQP and MaxEnt(3) at the room level of σ = 0.1,
     not σ = 0.2. The SUMMARY must say so next to P2.
2. **Reading P1 and F2 (iqp4).**
   - The G fit on `iqp4` has a misspecification floor of about 1e-3 in its order-≤3
     residual. MaxEnt(3) matches those moments exactly.
   - So on `iqp4`, G enters the completion with a known low-order disadvantage. **The step-3
     "misfit is conservative" argument does not apply.** The misfit is not a training
     failure; it is the price of the family.
   - P1 and F2 are read as: "does the weight-≤3 IQP's completion beat MaxEnt(3) *despite* its
     low-order misfit?"
   - The SUMMARY must show G's training residual next to every R on `iqp4`, and cite D1.
3. **No other change.** G keeps 3 restarts: D1 shows the restarts cluster within 2× of the
   floor. The ridge, the grid, the seeds, the budget, the cut order and the hypotheses are
   unchanged.

## 3. Build items affected

- Item 2 is reopened only for the `mix` change, and is then re-checked at `check.sh --stage
  10`.
- `tests/test_step4.py` must add three tests:
  - `mix` with K = 3 reproduces the old draws bit for bit;
  - the grid's `mix` uses `chosen_K` and `chosen_delta` from `calibration_amend1.json`;
  - `calibration_amend1.json` has every candidate and no completion keys.
- Then item 3, the timing: `iqp4` at σ = 0.2, N = 1e4, and `mix` with the amended
  parameters at N = 1e4 → PROJECTION.json → wait for the budget-approval file.
