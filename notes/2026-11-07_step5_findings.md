# Step 5 findings: where the iqp4 advantage reverses (synthetic, n = 12)

Research note, 2026-11-07.

**Sources**
- Results: branch `step5-sigma`, commit bdc4cea, with `results/step5/SUMMARY.md`,
  `verdicts.json`, `table.csv` and `figures/step5/`.
- Spec: `specs/step5_iqp4_sigma_scan.md`, frozen at 53d28cf and **designed after step 4**.
- Amendment: `specs/step5_amendment1.md` (f6a3ca7). It was written before the grid ran and adds
  the rules for Q5 when σ\* is undefined.

**Checks**
- `check.sh --stage 15` exits 0. I re-ran it independently on the worktree.
- The verdicts and σ\* were recomputed independently from the 120 `metrics.json` files.

**Required caveat:** Q0 replicates data already seen. G is the generic IQP (no oracle). n = 12
proxies are not hardness evidence.

## Setting

- **Targets.** `iqp4` is the step-3 IQP plus 6 weight-4 generators, all angles ∝ σ. `iqp4f` is
  the same, but with the weight-4 angles fixed at τ = 0.2.
  - iqp4f(0.2) = iqp4(0.2) holds bit for bit (pytest).
- **Grid.** σ ∈ {0.1, 0.125, 0.15, 0.175, 0.2, 0.25}, N ∈ {∞, 1e4}, 5 seeds.
- **Fits.** G uses 3 restarts. MaxEnt(3) uses ridge 1e-8.
- **Reproduction.** iqp4 at σ = 0.1 and 0.2 (N = ∞) reproduces step 4 exactly on all 5 seeds.
- **MaxEnt maxiter.** Hit on 0 of 120 instances.
- **R.** R = G_iqp / G_maxent3 at orders 4–6. "< 1" means the IQR is entirely below 1, and "?"
  means undecided.
- **σ\*.** The first downward crossing of median R through 1, interpolated in log–log.

## 1. Frozen hypotheses: Q0, Q1, Q2 and Q4 pass; Q3 and Q5 fail

| ID | Verdict | Numbers |
|---|---|---|
| Q0 | PASS (replication) | iqp4, N = ∞: R = 7.93 [5.50, 8.92] at σ = 0.1; R = 0.577 [0.450, 0.579] at σ = 0.2 |
| Q1 | PASS | σ\*(iqp4, ∞) = **0.160**, one sign change, inside the predicted [0.15, 0.20). The power-law guess was 0.17. |
| Q2 | PASS | max/min of G_iqp over σ = 2.30 (≤ 3). G_maxent3(0.25)/G_maxent3(0.1) = 21.5 (≥ 10). |
| Q3 | **FAIL** | σ = 0.25: R = 0.891 [0.836, 1.14], undecided. **Not FM2:** G's residual is 1.0e-3 and its largest restart residual is 3.2e-3. |
| Q4 | PASS (low confidence) | R(iqp4f) ≥ R(iqp4) at all four σ < 0.2: 19.8 vs 7.93, 4.63 vs 2.82, 1.41 vs 1.35, 0.709 vs 0.670. The last two differ by only 5–6%, well inside the IQRs. |
| Q5 | **FAIL** | σ\*(1e4) = 0.151 < σ\*(∞) = 0.160. **Fragile:** at N = 1e4 the median R at σ = 0.15 is 1.02, essentially at 1. The N = 1e4 series also changes sign twice, coming back to 1.02 at σ = 0.25. Neither amendment-1 case applied. |

## 2. The picture (iqp4, N = ∞, medians)

| σ | 0.1 | 0.125 | 0.15 | 0.175 | 0.2 | 0.25 |
|---|---|---|---|---|---|---|
| R | 7.93 | 2.82 | 1.35 (?) | **0.670** | **0.577** | 0.891 (?) |
| G_iqp | 2.6e-4 | 4.0e-4 | 4.3e-4 | 3.5e-4 | 4.1e-4 | 6.0e-4 |
| G_maxent3 | 3.3e-5 | 1.3e-4 | 3.1e-4 | 5.6e-4 | 7.3e-4 | 7.2e-4 |
| G residual | 7.5e-3 | 1.0e-2 | 8.7e-3 | 4.5e-3 | 2.1e-3 | 1.0e-3 |

- **The room-versus-floor guess predicted the crossing.**
  - G_iqp barely moves: it stays within 2.3× across the grid.
  - G_maxent3 grows 22× from σ = 0.1 to 0.2.
  - The two cross near σ\* = 0.16, as Q1 predicted.
- **The advantage window is narrow.** Under misspecification, R < 1 holds only at
  σ = 0.175–0.2.
  - Above 0.2, G_maxent3 levels off (7.3e-4 → 7.2e-4) while G_iqp keeps rising, so R climbs
    back toward 1.
  - The k = 3.8 power law therefore holds only on the rising side.
  - Q3 fails for this reason, not because G failed to train.
- **Fixing the weight-4 part (iqp4f) moves the crossing very little.**
  - At small σ the fixed τ = 0.2 part dominates: G's residual is 15× that of iqp4 at σ = 0.1, and
    G_iqp is 9× higher.
  - G_maxent3 also rises, and σ\* is 0.162, against 0.160 for iqp4.
  - Exploratory reading: the crossing is set mainly by how fast MaxEnt(3)'s completion error
    grows with the weight-≤3 scale, not by the size of the weight-4 misspecification. This
    reading is not tested.
- **Finite N (1e4) blurs the crossing rather than shifting it in a clear direction.**
  - For iqp4 it moves slightly down (0.151, with a median R of 1.02 at σ = 0.15).
  - For iqp4f it moves slightly up (0.165).
  - Q5's directional prediction failed by a margin smaller than the grid resolution.

## 3. What this adds to steps 3–4

- The step-4 claim, that the IQP advantage survives IQP-like misspecification, is **local**. It
  holds in a window of about σ ∈ [0.175, 0.2] at n = 12, and is undecided or reversed on either
  side.
- Below that window, MaxEnt(3) has too little to miss.
- Above it, MaxEnt(3)'s error saturates while the IQP's misfit keeps growing.
- The window overlaps the strongly peaked regime of step 3, where the collision ratio is about
  130–1800 × uniform. The tension with anticoncentration is unchanged.
- Within this synthetic family, the mechanism is now partly explained: Q1 and Q2 pass. Its
  practical reach is still the open question from step 4. Do real data sit in such a window?

## 4. Candidate next steps (not decided)

- **Larger n at σ = 0.175–0.2.** Does the window widen, shrink or move as n grows? This is the
  scaling question, and the most informative next test.
- **A latent-class mixture baseline**, carried over from step 4. It is still missing, and any
  claim about "data the IQP did not generate" needs it.
- **Real-data probe.** Compute D3 and an order-4–6 completion check on one small real binary
  dataset. That would tell us whether the window is ever reached in practice.
