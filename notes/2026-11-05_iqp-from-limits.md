# Deriving a new IQP model from the known limits

Research note, 2026-11-05. The question: start from the known limits of quantum generative
models and work backward to an IQP design that is not already excluded by them.

Status: design hypothesis. Nothing has been run. Sections 1 and 2 are from the literature and
our earlier results; sections 3 to 6 are our own proposal and are not established results.

## 1. The limits, and what each one rules out

| # | Limit | Source | Rules out |
|---|---|---|---|
| L1 | Anticoncentrated models are untrainable on average: squared distance, MMD², TVD variance, and diagonal Pauli expectations all concentrate as exp(−O(n)). Advantage "must be distinct from anticoncentration". | Herbst, Brandic, Perez-Salinas, arXiv 2512.24801 | Training a random-like IQP with a global distance loss |
| L2 | Sparse or peaked distributions (support size K = poly(n)) are trainable, but a classical algorithm could store the support and sample from it. Peaked outputs "might be classically learnable from data". | 2512.24801; Zhang, arXiv 2510.00132 (hardness there concerns *estimating* the peak weight, not generation) | Poly-support targets as a source of generative advantage |
| L3 | An exact code-supported 1+2-body solution has all angles in (π/4)Z, so it is Clifford. More basically, uniform-on-an-affine-subspace targets are trivially classically samplable: pick a random codeword. | our Hamming result (`line-A`, `analysis/clifford_check.py`) | Affine/linear-code-supported data, whatever the circuit |
| L4 | Gaussian-kernel MMD weights parity order \|A\| by p^\|A\|(1−p)^(n−\|A\|), which acts as a low-pass filter. | our spectral analysis; Rudolph et al. arXiv 2305.02881 | Hoping a low-order loss *trains* high-order structure |
| L5 | An order-k max-ent model matches every order-≤k statistic by construction, so on order-≤k metrics it ties or wins. Basket: IQP loses to M1 at every order. | our basket result | Claims measured on order-≤k metrics only |
| L6 | Noisy IQP becomes classically samplable above a critical depth. Constant noise on an anticoncentrated IQP output is simulable. | Bremner–Montanaro–Shepherd arXiv 1610.01808; arXiv 2403.14607 | Deep IQP on near-term hardware |
| L7 | IQP ⟨Z_a⟩ can be estimated classically to 1/poly additive error, so training can be classical while sampling stays hard. | Van den Nest; Recio-Armengol et al. arXiv 2503.02934 | (an enabler, not a limit) |
| L8 | The positive example: learning succeeds because **local statistics uniquely determine the parameters**, while the global joint distribution stays hard to sample. Training is closed-form and classical, and the landscape is convex or has O(1) local minima. Inputs must be "locally decoupling". | Huang et al., arXiv 2509.09033 | (an enabler; this is the escape route from L1) |

## 2. The requirements that follow

- **R1, from L1 and L8.** Train on local or low-order statistics, never on a global distance.
  The parameters must be *identifiable* from those statistics: the Jacobian of θ ↦ {⟨Z_a⟩ :
  |a| ≤ k} must have full column rank.
- **R2, from L2 and L3.** The target support must be exponentially large, so not peaked, and
  not affine. Concentrated relative to 2ⁿ is fine.
- **R3, from L3.** The gate set must be able to reach non-Clifford solutions, and the data must
  *need* them. Caveat: a weight-3 Pauli rotation exp(iπ/4·XXX) is still Clifford, so "3-body
  gates" alone do not escape Clifford. What is non-Clifford is a degree-3 phase polynomial with
  angles off the π/4 grid (for example CCZ, which is π/8 rotations on weights 1, 2 and 3).
- **R4, from L4 and L5.** The low-order loss can stay, but the *claim* has to be measured on
  orders above k, against the order-k max-ent model.
- **R5, from L6.** Keep the circuits sparse and of constant depth.

## 3. The key reframing (our hypothesis): advantage as a *completion gap*

R1 and R4 together say this:

- Both the IQP model and the order-k max-ent model are fitted to the **same** order-≤k
  statistics.
- They then disagree only in how they **complete** the distribution above order k.
  - Max-ent chooses the highest-entropy completion: a log-linear model with no structure
    above order k.
  - The IQP chooses the completion implied by its circuit: interference between the phase
    polynomial terms.
- A generative advantage of this kind exists iff **the data's true high-order structure is
  closer to the IQP completion than to the max-ent completion**, and the IQP sits outside the
  known easy classes.

Why this helps:
- It explains our two failures. In basket, the true completion *is* max-ent plus one
  constraint, so the gap is 0. In Hamming, the true completion is affine, so a classical
  sampler is trivial (L3).
- The loss no longer has to see high order (L4 is avoided). Only the evaluation does.
- It is directly testable on held-out data.

Definition, for a fixed train/test split:

    G_k(model) = Σ_{k < |A| ≤ m} w_A · ( f̂_A(model) − f̂_A(test) )²

Here f̂_A is the parity (Walsh) coefficient E[(−1)^{A·x}]. The weights w_A could be uniform
per level, or the Krawtchouk single-level kernel already used for direction 4. The claim is
G_k(IQP) < G_k(maxent_k), with a confidence interval from bootstrapping the test set. A second,
harder tier compares against the best classical model trained on the *full* samples at the same
sample size N (autoregressive model or transformer), in the spirit of Hibat-Allah's
generalization framing.

## 4. The proposed model: "identifiable non-Clifford IQP" (working name)

**Circuit.**
- |+ⁿ⟩ → exp(i Σ_g θ_g Z_g) → H⊗ⁿ → measure. This is the standard X-program form.
- The generators g have weight ≤ 3 and lie on a sparse interaction graph chosen from the data,
  for example from the order-2 and order-3 Walsh support. This addresses R5.
- The angles θ_g are continuous and not quantized.
- Optional conditional version p(y|x), in the spirit of L8: input features switch gates on and
  off, so the local-decoupling condition can hold on real data such as user features → basket.

**Training (classical, from L7 and R1).**
1. Fit order-k max-ent first. It is the baseline, and its residual D_k = KL(p̂ ‖ maxent_k)
   says whether there is any high-order signal at all (screening gate S1).
2. Minimise Σ_{|a|≤k} (⟨Z_a⟩_θ − f̂_a(train))² using the Van den Nest/Recio-Armengol estimator.
3. **Initialisation (needed because of L1).** Do not start at random angles. A random IQP
   anticoncentrates, and Herbst shows its low-weight ⟨Z_a⟩ also concentrate. Start near a
   structured point where gradients are O(1): small angles near product, or a Clifford point
   matched to the data's affine part. Then let the angles move off the grid.
4. **Identifiability check.** Compute the Jacobian rank at the optimum. If it is
   rank-deficient, the high-order completion is not determined by the data, so report the
   spread of G_k over the null directions instead of a single number.

**Hardness audit (heuristic; there is no proof for a learned instance).**
- Distance of the trained angles from the (π/4)Z grid (Clifford), and from (π/8)Z.
- Magic, measured as stabilizer Rényi entropy at n ≤ 20.
- Attack the trained instance with a tensor-network sampler, low-weight Fourier/Pauli-path
  truncation, and Clifford+few-T. Report the best classical TV distance and its cost against n.
- An honest claim is "outside the known easy classes", not "provably hard".

## 5. Kill criteria (stop or switch direction if these happen)

| Gate | Test | If it fails |
|---|---|---|
| S1 | D_k(data) is not significantly above the bootstrap noise | No-go for this dataset (the basket case). Write it up as the screening result. |
| S2 | The support passes an affine-subspace test | Trivial classical sampler (the Hamming case). Drop the dataset. |
| S3 | Trained angles converge to within ε of the π/4 grid | Clifford collapse. Try degree-3 generators; if they collapse too, the data has no non-Clifford completion. |
| S4 | Jacobian rank-deficient and the G_k spread includes the max-ent value | Completion is not identifiable. Advantage can't be claimed. |
| S5 | G_k(IQP) ≥ G_k(maxent_k) | No completion gap. |

## 6. Minimal experiment ladder (build order)

1. **Synthetic sanity check.** Target: a random sparse degree-3 IQP with non-Clifford angles,
   n = 12–20. Does low-order training recover the angles, and does G_k(IQP) ≪ G_k(maxent)? If
   it fails even here, the design is wrong. Stop.
2. **Perturbed Hamming.** Take the [15,11] code with non-affine noise (for example
   codeword-dependent biases), so that S2 passes. Check S3: is the solution still Clifford?
3. **Real data.** Only datasets that pass S1 and S2 in a screening sweep (direction 1),
   plus quantum-sensor data (direction 2) as a separate arm.

## How this relates to the five README directions

The proposal merges four of them into one pipeline:
- Direction 1 becomes the screening gates S1 and S2.
- Direction 3 becomes R3 and gate S3.
- Direction 4 moves from training to the evaluation metric G_k.
- Direction 5 is the max-ent baseline built into G_k.

Direction 2 (quantum-sensor data) stays a separate arm, because it does not depend on L5.

## References

- Herbst, Brandic, Perez-Salinas, arXiv 2512.24801: limits of quantum generative models with
  classical sampling hardness
- Huang, Broughton, Eassa, Neven, Babbush, McClean, arXiv 2509.09033: generative quantum
  advantage (IDQNN, local-marginal learning, sewing)
- Zhang, arXiv 2510.00132: complexity and hardness of random peaked circuits
- Bremner, Montanaro, Shepherd, arXiv 1610.01808: sparse and noisy IQP
- arXiv 2403.14607: polynomial-time classical simulation of noisy IQP above a critical depth
- arXiv 2404.19005 (PRX Quantum 6, 020338): degree-D hypercube IQP, hardness at low depth
- Recio-Armengol et al., arXiv 2503.02934: train classically, deploy quantum
- Rudolph et al., arXiv 2305.02881: MMD trainability vs high-order distinguishability
- Hibat-Allah et al., arXiv 2303.15626: generalization benchmark for generative models
