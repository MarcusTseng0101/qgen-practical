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
| Note: [notes/2026-11-05_quantum-opt-community-recsys.md](notes/2026-11-05_quantum-opt-community-recsys.md) | Quantum optimization / QMC for community-based recommendation: no proven advantage (dequantized or weak baselines); supports "fair baseline decides the claim" |

## Not yet decided

Venue, scope, collaborators, compute. Nothing run here yet.
