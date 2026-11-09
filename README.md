# qgen-practical: practical data for generative quantum advantage

Status: idea / scoping (opened 2026-11-05). Next paper after the 2026 competition (qgen-iqp line A).

## Question

Is there a *practical* data distribution (real-world classical or quantum-sensor data) on which a
quantum generative model is both

1. **trainable** — learns the distribution better than a *fair* classical baseline, and
2. **hard to sample** — the trained model stays outside classically simulable regimes
   (not Clifford, not low-order, not peaked)?

Huang et al. (arXiv 2509.09033, Discussion) name this as open: "sharpening the search for
practical data distributions ... compatible with models that exhibit generative quantum
advantage will be crucial."

## Why it is hard (the tension)

- Hardness proofs rest on anticoncentration; anticoncentrated models are untrainable.
  Peaked/low-order targets are trainable but lose hardness (Herbst, Brandic, Perez-Salinas,
  arXiv 2512.24801).
- Our own evidence (qgen-iqp line A, branch `line-A`):
  - **Hamming [15,11]:** 1+2-body IQP (exact NLL) reaches TV 0 where pairwise max-ent (M1) is
    uniform. But we proved any exact code-supported 1+2-body solution has all angles in
    (pi/4)Z → Clifford → classically simulable. (README "Theory notes"; `analysis/clifford_check.py`)
  - **Basket top-20 (real data):** IQP loses to M1 at every parity order. M1 + one constraint
    ("no empty basket") cuts MMD ~10x. The data is low-order + one forbidden state.
  - **Spectral view:** Gaussian-kernel MMD weights parity order |A| by p^|A|(1-p)^(n-|A|),
    so it cannot train high-order structure from samples.
- Prior "IQP competitive on real data" claims used weak baselines: Recio-Armengol et al.
  (2503.02934) vs RBM/EBM, trained on the scoring metric; Hibat-Allah et al. (2303.15626)
  edge only on synthetic Evens, smallest-data regime.

## Candidate directions (unranked, to scope)

- **A characterization:** which spectral/structural properties of a dataset (parity-order
  spectrum, support size, collision probability) are necessary for (1) and (2) together.
  Possibly a no-go: "if max-ent at order k matches the data within noise, no order-k IQP
  advantage".
- **Quantum-sensor data** (Huang's suggestion): data that is natively quantum, where
  route "quantum data + quantum memory" (2112.00778) already has proofs.
- **Beyond Clifford on codes:** 3-body gates or approximate code support; does the
  learned solution stay non-Clifford and still trainable?
- **Sample-estimable high-order loss** (Krawtchouk single-level kernel; SNR 3.4 at order 8
  on Hamming vs 0.011 for sigma=1) — trains Hamming without exact probabilities.
- **Benchmark protocol:** always include the matched max-ent baseline + constraint audit
  as the fair opponent.

## Reading list

| Ref | Take |
|---|---|
| Huang et al., arXiv 2509.09033 | Open-problem statement; provable generative advantage on circuit-generated data |
| Herbst, Brandic, Perez-Salinas, arXiv 2512.24801 | Trainability vs anticoncentration tension |
| Recio-Armengol et al., arXiv 2503.02934 | Large-scale IQP on real data (genomic, MNIST, D-Wave); weak baselines |
| Hibat-Allah et al., arXiv 2303.15626 | Generalization race; low-data edge only |
| Rudolph et al., arXiv 2305.02881 | MMD trainability vs high-order distinguishability |
| Cerezo et al., arXiv 2312.09121 | No barren plateaus ⇒ often classically simulable |
| Shepherd & Bremner 2009; arXiv 2308.07152 | pi/4 IQP = Clifford; IQP amplitudes and codes |
| Huang et al., Science 2022 (arXiv 2112.00778) | Quantum data advantage (unconditional) |
| Zhao, Huang et al., arXiv 2604.07639 | Memory advantage on massive classical data |
| Anschuetz, Hu, Huang, Gao, arXiv 2209.14353 | Contextuality expressivity separation |
| Note: [notes/2026-11-05_iqp-from-limits.md](notes/2026-11-05_iqp-from-limits.md) | Design note: reverse-derive an IQP from known limits; the "completion gap" reframing; kill gates S1–S5 |
| Note: [notes/2026-11-06_steps1-2_findings.md](notes/2026-11-06_steps1-2_findings.md) | Steps 1–2 (both killed): generic IQP not identifiable from order-≤3 moments; sign ambiguity at small σ but completion stable; exact recovery was the wrong criterion |
| Note: [notes/2026-11-06_step3_findings.md](notes/2026-11-06_step3_findings.md) | Step 3: generic IQP completes orders 4–6 ~5× better than MaxEnt(3) at σ = 0.1–0.2 (exploratory; well-specified, N = ∞, peaked regime); fails to train at σ ≥ 0.3; paired control vacuous at N = ∞ |
| Note: [notes/2026-11-07_step4_findings.md](notes/2026-11-07_step4_findings.md) | Step 4: all six frozen hypotheses PASS; IQP advantage survives IQP-like misspecification at σ = 0.2 (R ≈ 0.55–0.66, N ≥ 1e4) but reverses at σ = 0.1; none on a classical mixture (R ≈ 3–6, no fitted-mixture baseline); N = 1e3 is noise-dominated |
| Note: [notes/2026-11-07_step5_findings.md](notes/2026-11-07_step5_findings.md) | Step 5: iqp4 advantage crosses at σ* = 0.160 as predicted (floor flat, MaxEnt room ×22); window R < 1 only σ = 0.175–0.2, undecided at 0.25 (Q3 FAIL, not FM2); fixed-floor control barely moves σ*; finite-N shift prediction (Q5) FAILs narrowly |
| Note: [notes/2026-11-08_step6_findings.md](notes/2026-11-08_step6_findings.md) | Step 6: iqp4 window does not survive larger n at fixed layout counts — S1/S2/S3 FAIL, S4 PASS; window moves up (n=14: R<1 only at σ=0.25) and is absent at n=16 for σ≤0.2 (σ=0.25 cut); MaxEnt room shrinks with n while D3 does not; confounds: target peakedness, G under-training at n=16 |
| Note: [notes/2026-11-08_step7_findings.md](notes/2026-11-08_step7_findings.md) | Step 7: at collision-matched σ the iqp4 advantage mostly returns (n=14 R<1 at all 3 levels; n=16 medians 0.65–0.83 but undecided — seeds 1–2 lose at every level); C1/C2/C3 FAIL, C4 PASS (n=16 G residual ≤ 1e-2); step 6's collapse was mostly peakedness, but the margin still weakens with n; D3 grows with n at matched collision |
| Note: [notes/2026-11-09_step8_seed_diagnostic.md](notes/2026-11-09_step8_seed_diagnostic.md) | Step 8 (exploratory, no new fits): the two n=16 losing seeds lose for different reasons — seed 1 strong weight-4 part (r4 0.415 vs ~0.29; G_iqp high, mostly order 4), seed 2 least completion room (lowest D3; G_maxent3 low); log R ~ D3 + r4 gives R² 0.83 at n=16 and the r4 cost grows with n; seeds share angle draws across n; next test should control D3 and weight-4 share and use more seeds |
| Note: [notes/2026-11-05_quantum-opt-community-recsys.md](notes/2026-11-05_quantum-opt-community-recsys.md) | Quantum optimization / QMC for community-based recommendation: no proven advantage (dequantized or weak baselines); supports "fair baseline decides the claim" |

## Not yet decided

Venue, scope, collaborators, compute. Nothing run here yet.
