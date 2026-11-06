# Step 3 findings: completion ratio R vs angle scale σ (synthetic, n = 12, N = ∞)

Research note, 2026-11-06. Source: branch `step3-ratio`, commit 372ad38;
`results/step3/SUMMARY.md`, `verdicts.json`, `table.csv`, `figures/step3/`. The spec
(`specs/step3_completion_vs_sigma.md`) was **designed after** the step 1–2 diagnostics.

Setting:
- Targets: `iqp(σ, s)` (sparse 38-generator IQP, θ = σ·z) and its paired control
  `maxent_proj` (MaxEnt3 of the same target), with σ ∈ {0.05, 0.1, 0.2, 0.3, 0.4, 0.6} and
  5 seeds each.
- Fits to the exact order-≤3 moments: O (the oracle layout), G (the generic 298-generator
  IQP) and MaxEnt(3).
- R = G_iqp / G_maxent3 at orders 4–6, taken at the lowest-residual restart.
- Budget cut: G used 3 restarts instead of 10, which biases R_G upward.

## 1. Frozen hypotheses

| ID | Verdict | Note |
|---|---|---|
| K1, K2 | PASS | **Vacuous by construction.** On `maxent_proj` the truth *is* MaxEnt(3), so G_maxent ≈ 1e-19–1e-12 and R is ≫ 1 for any fit. This is a spec-design error. At N = ∞ the paired control only checks the wiring. It becomes informative only at finite N. |
| C1 | PASS | R_O = 0.42 [0.39, 0.59] at σ = 0.05 (a replication) |
| M1 | FAIL | R_O falls with σ, because O recovers the target exactly at σ ≥ 0.3 (residual ~1e-16) |
| M2 | FAIL | R_G < R_O at σ ≤ 0.1: the generic fit beats the oracle there (the oracle sits in wrong-sign basins) |
| M3 | FAIL | W = {0.1, 0.2, 0.3, 0.4}. The predicted W was ⊆ {0.1}. W at 0.3 and 0.4 comes from the oracle's exact recovery, which is a landscape statement only. |

## 2. Main exploratory result (not frozen): the generic IQP completes better than MaxEnt(3)

| σ | D3 | R_G (median [IQR]) | G residual | collision ratio | Clifford median |
|---|---|---|---|---|---|
| 0.05 | 5.0e-3 | 0.15 [0.14, 0.32] | 2.0e-7 | 3300 | 0.03 |
| 0.1 | 4.6e-2 | 0.18 [0.06, 0.24] | 1.8e-5 | 1800 | 0.06 |
| 0.2 | 0.19 | 0.18 [0.12, 0.22] | 1.5e-4 | 180 | 0.13 |
| 0.3 | 0.27 | 1.41 [1.33, 1.54] | 1.3e-3 | 11 | 0.18 |
| 0.4–0.6 | ~0.3 | 1.8–2.2 | ~1e-3 | ~2 | ~0.2 |

- At σ = 0.1–0.2, an IQP that does not know the layout completes orders 4–6 about 5× better
  than MaxEnt(3), and there is real completion room there (D3 = 0.05–0.19). This is the
  first R < 1 outside the near-identity regime without an oracle.
- At σ ≥ 0.3, G fails to train (FM2 spurious minima, as in step 1). The residual–G correlation
  for G also breaks down there (r = 0.04 to −0.45), so the "misfit is conservative" argument
  does not hold at those σ.

## 3. What this does and does not show

- **Well-specified.** The target is itself an IQP with weight ≤ 3 generators, which is inside
  G's family. MaxEnt(3) loses because the truth is outside *its* family. The real question,
  whether the IQP inductive bias helps on data it did not generate, is untested.
- **N = ∞.** Finite-sample noise in the moments may erase a 5× advantage, or reverse it.
- **The tension is still visible.** The window where G trains and wins (σ = 0.1–0.2) is
  strongly peaked: collision ratio 180–1800 × uniform, angles 0.06–0.13 from Clifford. Where
  the target approaches anticoncentration (σ ≥ 0.4, ratio ~2), G does not train. This is the
  Herbst trade-off, measured on the completion task. The n = 12 proxies are not hardness
  evidence either way.

## 4. Next (step 4)

Test whether R_G < 1 at σ ≈ 0.1–0.2 survives:
- **misspecification**: truth outside the weight-≤3 IQP family, both IQP-like (added 4-body
  generators) and non-IQP (a classical latent-class mixture);
- **finite N**, where the paired `maxent_proj` control finally becomes a real kill test.
