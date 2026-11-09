# Literature check after step 10: where qgen-practical sits (2026-11-10)

**Method:**
- Searched with searchcrawl.
- Three full texts were read by sub-agents. All three scrapes were truncated before their
  discussion sections, so the claims below cover what was readable.
- Quotes marked [answer-block] come from the scraper's summary and were not checked against the
  paper body.

## The four closest papers

| Paper | What they do | Overlap with us | What they lack that we have |
|---|---|---|---|
| Baumann, Hein, Udluft, Rohe, Linnhoff-Popien, Stein (LMU / Siemens), *Parity Supervision as a Driver of Generalization in Quantum Generative Modeling*, arXiv 2605.10258 v2 | Weight-2 ring IQP (24 parameters, n = 12; sweep n = 10–20), trained on K = 512 random mixed-order parity masks from 200 samples. Targets are Boltzmann score distributions on the even-parity support. Metrics are KL and coverage of unseen high-value states. 200 paired instances. | **Closest.** IQP fitted to parity moments against a "MaxEnt-parity" model on the same moments. The IQP wins strongly: mean KL 0.385 against 1.804, lowest in 190/200. | Their MaxEnt has 512 parameters, no order cutoff, and is fitted to **noisy 200-sample moments**, so it likely overfits. They report no restarts and no training residuals, use no misspecified targets, and do not test completion of held-out higher-order parities. |
| Recio-Armengol, Ahmed, Bowles (Xanadu), *Train on classical, deploy on quantum*, arXiv 2503.02934 | IQP with an MMD loss, trained classically up to 1000 qubits. Datasets: 2D Ising, blobs, D-Wave quench, MNIST, scale-free Ising, genomics. Baselines: RBM, an MLP energy-based model, and a decohered "bitflip" IQP. | MMD² = E_{a∼P_σ}[(⟨Z_a⟩_p − ⟨Z_a⟩_q)²]: a bandwidth-weighted **moment-matching** loss. "Lower bandwidths effectively probe higher order correlations." | No baseline is given the same moments (no MaxEnt). They concede the classical models are under-tuned ("much better results are likely possible for the classical models"). The EBM beats the IQP on log-likelihood. IQP without ancillas is "not a universal approximator". |
| Shen, Pielawa, Dunjko, Wang (Leiden / BMW), *Characterizing Trainability of IQP-QCBMs*, arXiv 2602.11042 | Gradient variance of the MMD loss at initialization. | A small-variance Gaussian init gives **polynomial** gradient variance for every architecture (Thm 3.13). We use small N(0, σ²) inits. | No local minima, no misspecified targets, no residual floors. |
| Lerch, Bowles, Puig, Armengol, Holmes, Thanasilp (EPFL / Xanadu), *IQP Born Machines under Data-dependent and Agnostic Initialization*, arXiv 2603.14576 | Barren plateaus under random full-range initialization. Variance lower bounds for identity and unbiased initializations. A data-dependent initialization gives provable gradients and faster convergence (150 qubits, genomics). | Initialization as a lever on which minimum is reached. | Not about completion or misspecification. |

## What this means for us

1. **Our niche is real and not taken.** We found no work that combines all of these:
   - an IQP fitted to **exact order-≤k moments**;
   - compared against **MaxEnt(k), the information-matched classical completion**;
   - on **completion of held-out orders k+1…**;
   - with **misspecified** targets;
   - reporting training residuals, restarts and per-instance statistics.

   The phrase "information-matched baseline" is our main methodological selling point. Both
   Xanadu and LMU say their baselines are not that.
2. **Baumann et al. is the paper to engage with directly.** Their headline (an IQP beats MaxEnt on
   the same parity moments by about 4.7× in KL) is far larger than ours: at n = 16, 16/20 wins,
   median R ≈ 0.64.
   - **Our hypothesis, untested:** much of their gap is finite-sample overfitting by a
     512-parameter MaxEnt with no order cutoff. That is not an inductive-bias advantage of the IQP.
   - This can be tested by rerunning their setup with MaxEnt(k), order-cut and/or regularized.
3. **Step 10's residual floor is consistent with the trainability literature.**
   - In our init regime, barren plateaus are ruled out (Shen et al.).
   - Ten restarts converging to the same nonzero residual points to expressivity.
   - The IQP is not universal (Xanadu), and our model lacks the target's weight-4 generators.
   - **Possible check:** a data-dependent init in the style of Lerch et al. If it ends at the
     same floor, the expressivity reading is confirmed.
4. **A cheap control we lack:** Xanadu's decohered "bitflip" model, where ⟨Z_a⟩ is a product of
   cosines. It answers whether the IQP's completion advantage needs coherence. It would slot into
   the step-9 setup.
5. **A practical use (from step 10):** gating on the IQP's training residual and falling back to
   MaxEnt(3). We found no prior work proposing this. It is still exploratory.
