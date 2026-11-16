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
| Note: [notes/2026-11-09_step9_findings.md](notes/2026-11-09_step9_findings.md) | Step 9 (fresh seeds 10–29, level B, frozen sign test): n=16 IQP wins 16/20 (H1 PASS, median R 0.637 [0.543, 0.889]); n=14 only 10/20 (H2 FAIL; 7 of 8 under-trained seeds lose, fresh n=14 targets more peaked than matched); step-8 two-mechanism model fails out of sample (H3/H4/H7 FAIL); verify fails only on repro (n=16 R drifts 6e-3 across BLAS thread counts; per-instance R sensitive 1–10% via restart selection) |
| Note: [notes/2026-11-10_step10_findings.md](notes/2026-11-10_step10_findings.md) | Step 10 (n=14, 10 G restarts, same fresh seeds): K1/K2/K3 FAIL, K4 PASS — 11/20 wins (was 10/20), 1/10 losers rescued; high residuals are a floor (10 restarts within 1.2–1.6×), so the n=14 losses are moment misfits, not under-training; oracle restart choice also 11/20; exploratory: training residual ≤ 1e-2 → 10/13 win vs 1/7 above, suggesting a residual-gated IQP/MaxEnt estimator |
| Note: [notes/2026-11-10_literature_positioning.md](notes/2026-11-10_literature_positioning.md) | Literature check: no prior work compares an IQP fitted to exact order-≤k moments against the information-matched MaxEnt(k) on held-out higher-order completion with misspecified targets; closest is Baumann et al. 2605.10258 (IQP ≫ a 512-param finite-sample MaxEnt-parity, likely overfitting); Xanadu 2503.02934 (MMD = moment matching, no info-matched baseline, bitflip control); trainability 2602.11042 and init 2603.14576 support step 10 floor = expressivity |
| Note: [notes/2026-11-10_step11_bitflip_findings.md](notes/2026-11-10_step11_bitflip_findings.md) | Step 11 (bitflip/decohered twin of G, same generators/inits/optimizer, step 9 targets): C1/C3 PASS — coherent IQP beats bitflip 20/20 at n=16 and n=14 (median Q 0.39, 0.32); C2/C4 FAIL — bitflip beats MaxEnt(3) only 3/20, 2/20; but bitflip misfits the order-≤3 training moments in 40/40 (median residual ~0.1), so coherence is needed to fit IQP targets at all; completion at matched fit not separable |
| Note: [notes/2026-11-10_step12_findings.md](notes/2026-11-10_step12_findings.md) | Step 12 (non-IQP targets lcm = latent-class mixture, ising4 = Boltzmann with weight-4 terms; peakedness calibrated to step 9 on seeds 0–4): E1/E3/E5/E7 FAIL — IQP beats MaxEnt(3) 0/20 in every cell (median R 25, 2.05, 160, 16.5); E2/E4/E6/E8 PASS — IQP still beats bitflip twin; IQP misfits training moments on all 80, residual-gated estimator falls back to MaxEnt(3) everywhere (0 losses); claim restricted to IQP-like data |
| Note: [notes/2026-11-10_step13_gate_findings.md](notes/2026-11-10_step13_gate_findings.md) | Step 13 (residual-gated estimator, tau=1e-2 frozen, fresh seeds 30–49, iqp4+lcm+ising4): F1 PASS — n=16 iqp4 gate picks IQP 15/20, 14 wins / 1 loss (p=0.0005); F2 PASS — 0/40 losses out of family (always falls back); F3 FAIL — n=14 9 wins / 2 losses (below the ≥10 floor); F4 PASS; pooled gmean R_gate 0.867 vs oracle 0.854 at n=16 |
| Note: [notes/2026-11-11_step14_finiteN_findings.md](notes/2026-11-11_step14_finiteN_findings.md) | Step 14 (noise-corrected gate r_N − Σ(1−f̂²)/N ≤ 1e-2, n=16, fresh seeds 50–69): S1 PASS — N=1e5 iqp4 11 wins / 3 losses (p=0.029); S2/S4 PASS — 0/80 picked out of family; S3 FAIL — N=1e4 12/8, G fits the noise and the gate goes blind; always-IQP median R 0.66 (N=∞) → 0.93 (1e5) → 0.99 (1e4) |
| Note: [notes/2026-11-11_midterm_report.md](notes/2026-11-11_midterm_report.md) | Mid-term report, steps 1–14 (+ update boxes for 15–16 and 17–21: synthetic advantage at N≥3e4, held-out val gate 0/14 losses on iqp4, order-≤3 gate not safe in general; QEC: 0/32 resolved wins, 3 reproducible losses; next = write-up): evidence path in four arcs, the current pre-registered claim with its exact support (13 F1/F2, 14 S1/S2), what is not shown, literature positioning, ranked next steps (recommended: split-sample gate between N=1e4 and 1e5) |
| Note: [notes/2026-11-11_step15_split_pilot.md](notes/2026-11-11_step15_split_pilot.md) | Step 15 pilot (dev seeds, no frozen test): split-sample gate is unbiased but has no power at τ=1e-2, does not rank R within iqp4, and overlaps across families at N=1e4 — dropped; at N=1e4 the advantage itself is gone |
| Note: [notes/2026-11-11_step16_threshold_findings.md](notes/2026-11-11_step16_threshold_findings.md) | Step 16 (step 14 gate unchanged, N=3e4, n=16, fresh seeds 70–89): T1 PASS — iqp4 17 wins / 2 losses (p=3.6e-4), gate within 0.2% of oracle; T2 PASS — 0/40 out of family; threshold between 1e4 and 3e4, but soft (R varies across seed sets/sample streams as much as with N) |
| Note: [notes/2026-11-11_step17_mnist16_findings.md](notes/2026-11-11_step17_mnist16_findings.md) | Step 17 (first real data: MNIST reduced to 16 bits, N_train=3e4, held-out completion, fresh split seeds 100–119): U1 PASS — gate picks IQP 0/20; U2 PASS — ungated R ≥ 1 on 20/20 (median 4.35); IQP cannot fit order ≤3 (r_N 0.75 ≈ 33× floor) despite high D3 0.57; safety carries to real data, gain not shown
| Note: [notes/2026-11-11_step18_identifiability.md](notes/2026-11-11_step18_identifiability.md) | Step 18 (identity demo, dev seeds, exact moments): q_λ = λp + (1−λ)MaxEnt3(p) keeps all order-≤3 moments, so the gate picks G at every λ; G loses below λ* = 0.60–0.74 — safety is a property of the families tested, not a guarantee; fix = validate on held-out high-order moments
| Note: [notes/2026-11-11_step19_qec_findings.md](notes/2026-11-11_step19_qec_findings.md) | Step 19 (Google surface-code detection events, 7 held-out hardware runs): V1 FAIL — gate picks G on 7/7 and loses 5 (median R 2.87); V2 FAIL (R ≥ 1 on 5/7; both wins X-basis); train-row order-4 check flags 0/7 — safety clause restricted to data the IQP fails to fit at low order
| Note: [notes/2026-11-11_step20_val_gate_findings.md](notes/2026-11-11_step20_val_gate_findings.md) | Step 20 (held-out order-4 validation gate, 18 fresh instances): W1 FAIL (2 losses, both QEC), W2 PASS (2 vs 7 for step 14 gate), W3 PASS (kept 6/9 wins); iqp4 0 losses on 14 incl. pilot, QEC decisions at chance (4/8) — QEC comparison likely noise-limited at 5e4 shots
| Note: [notes/2026-11-11_step21_qec_resolvability.md](notes/2026-11-11_step21_qec_resolvability.md) | Step 21 (diagnostic, 16 spent QEC runs × 2 splits, bootstrap CIs): 9/16 unresolved, sign agreement across splits 8/16; 0/32 resolved IQP wins, 12/32 resolved losses, 3 runs lose in both splits; val check resolves 1/32 — no completion advantage on QEC at 5e4 shots
| Note: [notes/2026-11-11_step22_xor_interference.md](notes/2026-11-11_step22_xor_interference.md) | Step 22 (classical XOR model, same 696 params): X0 PASS, X4 PASS (IQP beats XOR 13/14 on iqp4: the synthetic advantage is interference); C1 FAIL, C2 FAIL on unspent r07 (XOR does not beat MaxEnt or IQP: QEC losses are not interference); IQP vs MaxEnt on r07 0 wins / 4 resolved losses
| Note: [notes/2026-11-13_step23_local_iqp.md](notes/2026-11-13_step23_local_iqp.md) | Step 23 (grid-local IQP, 4x4 device graph, fresh seeds 920-933): H1-H4 all PASS 14/14 — local IQP beats MaxEnt(3) (median R 0.35 at 1e4, 0.19 at 1e5), MaxEnt-on-graph (0.07) and the generic IQP; safety grid-Ising loses 0/14 as expected. Non-identifiability fixed by connectivity prior; synthetic well-specified target, statistical not computational |
| Note: [notes/2026-11-13_step24_robustness.md](notes/2026-11-13_step24_robustness.md) | Step 24 (robustness, fresh seeds 960-973): M1 FAIL 3/14 (2 missing couplers, R 2.86), E1 PASS 14/14 (18 extra candidates, R 0.46), D1 PASS 11/14 (2% readout noise, R 0.78; mitigated 14/14, R 0.42); missing couplers show as residual 1.8x the noise floor — use the full coupling map plus spares, mitigate readout |
| Note: [notes/2026-11-14_step25_pipeline.md](notes/2026-11-14_step25_pipeline.md) | Step 25 (full pipeline: readout mitigation + residual alarm at 0.9 + 103-candidate geometric graph, fresh seeds 980-993): P1-P4 all PASS — missing couplers + 2% noise 14/14 (R 0.48), correct graph 13/14 (R 0.40), +5% noise 14/14 (R 0.46); alarm 13/14 hits, 0/14 false; without enlargement 2/14 and 4/14 |
| Note: [notes/2026-11-14_step26_gate_noise.md](notes/2026-11-14_step26_gate_noise.md) | Step 26 (gate-level Pauli noise + 2% readout, FlipIQP = local IQP + 16 learned per-qubit dampings, fresh seeds 1000-1013): D1, G1-G3 all PASS — beats MaxEnt3 13/14 at 1% (R 0.63), 14/14 at 0.5% (R 0.51), beats step 25 pipeline 14/14; 2% stress 13/14 (R 0.60) while pipeline 0/14 (R 1.6); alarm 0/42 |
| Note: [notes/2026-11-15_step27_combined.md](notes/2026-11-15_step27_combined.md) | Step 27 (missing couplers + gate noise + 2% readout; FlipIQP + residual alarm at 0.75 raw floor + 103-candidate enlargement, fresh seeds 1020-1033): E1, K1-K4 all PASS — wrong graph 12/14 at 1% (R 0.66), 13/14 at 0.5% (R 0.56); correct graph 13/14 (R 0.57), false alarms 1/14; without alarm 6/14 and 4/14 |
| Note: [notes/2026-11-15_step28_correlated.md](notes/2026-11-15_step28_correlated.md) | Step 28 (correlated gate noise at matched marginal rate, step 27 recipe unchanged, fresh seeds 1040-1053): F1, C1-C4 all PASS — wrong graph 14/14 at 1% (R 0.54), 12/14 at 2% (R 0.80); correct graph 14/14 (R 0.53), false alarms 0/14; at 2% always-enlarge 14/14 (R 0.72) |
| Note: [notes/2026-11-15_synthesis_steps23-28.md](notes/2026-11-15_synthesis_steps23-28.md) | Synthesis of steps 23-30 (updated 2026-11-16): evidence chain, final recipe (FlipIQP + residual alarm 0.75 + geometric enlargement), negative/boundary results, open limits (coherent RX miscalibration ~1% = tested limit, n>16, hardware) |
| Note: [notes/2026-11-15_step29_coherent.md](notes/2026-11-15_step29_coherent.md) | Step 29 (coherent RX miscalibration, step 27 recipe unchanged, fresh seeds 1060-1073): H3 — wrong graph PASS (12/14 at eps 0.2, 13/14 at 0.1) but correct graph FAIL 10/14 (R 0.74) and false alarms 3/14; damping lam ~1.0 does nothing for coherent errors; coherent miscalibration ~1% is the recipe's open limit |
| Note: [notes/2026-11-16_step30_coherent_model_exploration.md](notes/2026-11-16_step30_coherent_model_exploration.md) | Step 30 (exploration on spent seeds, no spec, no verdicts): coherent-aware layered IQP with in-circuit RX layers (untied 32 / tied 16 extra angles) fits order<=3 better but completes order 4-6 no better than FlipIQP (head-to-head 7/14 untied, 8/14 tied on coherent data; 2/14, 2/14 on Pauli data); no pre-registered test run; coherent limit stands |
| Note: [notes/2026-11-16_step31_coherent_shots.md](notes/2026-11-16_step31_coherent_shots.md) | Step 31 (step 30 CohIQP unchanged at N=1e5, correct graph, fresh seeds 1080-1093): K1, Y1-Y3 all PASS - coherent data 12/14 vs MaxEnt3 (R 0.51), beats FlipIQP 11/14 (0.51 vs 0.65); Pauli control 14/14 (R 0.38) but loses to FlipIQP 0/14 (0.17); coherent limit is a shot-dependent mis-specification, not fundamental; 0.75 alarm does not transfer to 1e5; all CohIQP restarts at the 3000-iteration cap |
| Paper: [paper/main.tex](paper/main.tex) | Draft 1 (2026-11-16), RevTeX/PRA: connectivity-prior IQP vs MaxEnt(3) for completing order 4-6 moments; sections: setup, why a prior (step 23), robustness and recipe (steps 24-28), coherent limit (steps 29-30), discussion; bib entries marked TODO verify |
| Note: [notes/2026-11-05_quantum-opt-community-recsys.md](notes/2026-11-05_quantum-opt-community-recsys.md) | Quantum optimization / QMC for community-based recommendation: no proven advantage (dequantized or weak baselines); supports "fair baseline decides the claim" |

## Not yet decided

Venue, scope, collaborators, compute. Nothing run here yet.
