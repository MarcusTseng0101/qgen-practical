# Step 4 findings: does R_G < 1 survive misspecification and finite N? (synthetic, n = 12)

Research note, 2026-11-07. Sources:
- branch `step4-misspec`, commit 1c6921e: `results/step4/SUMMARY.md`, `verdicts.json`,
  `table.csv`, `figures/step4/`;
- the blind pre-run diagnostics in `diagnostics/step4_pre/` (commit 32cdd04).

The spec (`specs/step4_misspec_finite_n.md`, hypotheses frozen at fe7d058) was **designed after
step 3**. It is amended by `specs/step4_amendment1.md` (189a445), which was written after the
blind diagnostics and before any completion quantity was computed.

**Required caveat:** R1 replicates data already seen; G is the generic IQP (no oracle); n = 12
proxies are not hardness evidence.

`check.sh --stage 12` exits 0 (re-run independently on the worktree). The verdicts were also
recomputed independently from the 140 `metrics.json` files.

Setting:
- **Targets**, 5 seeds each:
  - `iqp`: well specified, the step-3 target;
  - `iqp4`: misspecified but IQP-like; the step-3 target plus 6 weight-4 generators;
  - `mix`: misspecified and non-IQP; a product-Bernoulli mixture with K = 48 and δ = 0.99;
  - `maxent_proj`: the paired kill control.
- **Sample sizes:** N ∈ {1e3, 1e4, 1e5, ∞}.
- **Fits:** G (generic 298-generator IQP, 3 restarts) and MaxEnt(3) (ridge 1e-8), both fitted to
  the order-≤3 moments, possibly noisy.
- **R** = G_iqp / G_maxent3 at orders 4–6, both measured against the exact target. R < 1 means
  the IQP completes orders 4–6 better.
- **Statistics:** median [IQR] over 5 seeds. "R < 1" means the whole IQR lies below 1.

## 1. Frozen hypotheses: all six PASS

| ID | Verdict | Median R [IQR] |
|---|---|---|
| K | PASS | `maxent_proj`, finite N: R ≥ 1 in all 6 cells (1.22 to 78). Unlike step 3 (N = ∞), this is an informative kill test. |
| R1 | PASS (replication) | `iqp`, N = ∞: σ = 0.1 gives 0.179 [0.064, 0.236]; σ = 0.2 gives 0.176 [0.122, 0.215] |
| **P1** | **PASS** | `iqp4`, σ = 0.2, N = ∞: **0.577 [0.450, 0.579]**. G's training residual is 2.1e-3. |
| P2 | PASS | `mix`, N = ∞: 5.02 [4.59, 5.63], so the IQP shows no advantage. Tested at the **σ = 0.1 room level** only (amendment 1). |
| F1 | PASS | `iqp`, σ = 0.2: R < 1 at N = 1e5 (0.227 [0.088, 0.248]); undecided at N = 1e3 (1.05 [0.98, 1.17]) |
| F2 | PASS | `iqp4`, σ = 0.2, N = 1e5: 0.546 [0.471, 0.723]. G's residual is 2.3e-3. |

## 2. What the grid shows

| target, σ | N = 1e3 | 1e4 | 1e5 | ∞ |
|---|---|---|---|---|
| iqp, 0.1 | 1.28 (≥ 1) | 1.13 (undecided) | 0.247 (< 1) | 0.179 (< 1) |
| iqp, 0.2 | 1.05 (undecided) | 0.425 (< 1) | 0.227 (< 1) | 0.176 (< 1) |
| iqp4, 0.1 | 1.43 (≥ 1) | 4.95 (≥ 1) | 5.47 (≥ 1) | 7.93 (≥ 1) |
| iqp4, 0.2 | 0.89 (undecided) | 0.656 (< 1) | 0.546 (< 1) | 0.577 (< 1) |
| mix | 3.08 (≥ 1) | 4.67 (≥ 1) | 5.79 (≥ 1) | 5.02 (≥ 1) |

- **The IQP advantage survives IQP-like misspecification, but only at σ = 0.2.**
  - On `iqp4` at σ = 0.2, R ≈ 0.55–0.66 from N = 1e4 up, about 2× in favour of the IQP. That is
    a smaller margin than the 5× on the well-specified `iqp`.
  - This holds although G has a known order-≤3 misfit there (~2e-3), which D1 showed is the
    floor of the weight-≤3 family, not a training failure.
  - **At σ = 0.1 the advantage reverses.** R ≥ 1 at every N (7.9 at N = ∞), with a larger G
    residual (7.5e-3). This cell is not a frozen hypothesis, but it bounds P1: the advantage is
    not robust across σ.
  - A guess, not tested: at σ = 0.1 the completion room is small, so the misspecification floor
    outweighs the IQP's inductive-bias gain.
- **No advantage on non-IQP data.** On `mix`, R ≈ 3–6 at every N. The IQP's inductive bias
  hurts when the truth is a classical mixture. Two limits apply:
  - The comparison is at the σ = 0.1 room level (D3 = 0.0385): no product-Bernoulli mixture
    with n = 12 reached σ = 0.2's D3 ≈ 0.19.
  - There is no fitted latent-class mixture baseline. It would be well specified on `mix`, so
    the real classical bar there is higher than MaxEnt(3).
- **Finite N needs about N ≥ 1e4 at n = 12.**
  - At N = 1e3, both fits sit near the noise floor and R ≈ 1 or above in every cell.
  - At N = 1e3, G fits most of the sampling noise: its summed residual is 3.5e-3 to 8.9e-2,
    against 298 × the per-moment noise floor of 0.13–0.30.
  - The σ = 0.2 targets cross to R < 1 by N = 1e4. `iqp` at σ = 0.1 needs N = 1e5, presumably
    because MaxEnt(3)'s bias there is small and noise hides it until then (not checked).

## 3. What this does and does not show

- **Supported:** a generic weight-≤3 IQP fitted only to order-≤3 moments can complete orders 4–6
  better than MaxEnt(3), on data it did not exactly generate. This holds with realistic sample
  sizes (N ≥ 1e4), in the regime of `iqp` and `iqp4` at σ = 0.2.
- **Not supported:**
  - Robustness across σ: `iqp4` at σ = 0.1 reverses.
  - Any advantage on non-IQP structure (`mix`).
  - Any comparison against a well-specified classical model.
- **The target class decides the result.** The IQP wins when the data are close to an IQP and
  loses otherwise. The practical question is therefore whether real data look IQP-like at orders
  4–6, which step 4 cannot answer.
- **Regime:** as in step 3, the winning window is strongly peaked (collision ratio 180–1800 ×
  uniform at σ = 0.1–0.2). The n = 12 proxies are not hardness evidence.
- **Process caveats:**
  - G used 3 restarts.
  - MaxEnt hit maxiter in 19 of 140 instances, all at finite N, with residuals ≤ 1.4e-8, so
    those fits still match the noisy moments.
  - The grid took 80 min against a 0.67 h projection on a shared machine, so the timings are
    not a clean speed measurement.
  - My own spec errors are recorded in the amendment: the mix δ range was too narrow, and
    step 3's K1 and K2 were vacuous at N = ∞.

## 4. Candidate next steps (not decided)

- **σ scan on `iqp4`**, for example σ ∈ {0.1, 0.125, 0.15, 0.175, 0.2, 0.25}: locate where the
  advantage reverses, and test the room-versus-floor guess against D3 and G's residual.
- **A latent-class mixture baseline** (the `fit_mixture_moments` stub) on `mix` and on `iqp4`:
  the fair classical bar for P2-type claims.
- **Larger n** (for example 16) at σ = 0.2, to see whether the advantage and the N threshold
  scale.
