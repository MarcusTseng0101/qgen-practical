# Step 17 findings: on real data (MNIST-16) the IQP loses about 4×, and the gate correctly falls back

Research note, 2026-11-11.

**Sources**
- Results: branch `step16-threshold`, code b499b7a, results 3ed7fd1, with
  `results/step17/SUMMARY.md`, `verdicts.json`, `verify.txt` and `pilot/`.
- Spec: `specs/step17_real_mnist16.md`, frozen at 0b7b165.

**Process:**
- `--verify` **exits 0**.
- 20 splits, no failures, about 8 min per split under contention.

**Required caveat:**
- The 20 splits share one dataset: MNIST, reduced to 16 bits by a centre crop, 5×5 pooling and a
  median threshold.
- They show stability under resampling, not generality across datasets.
- Completion is scored on 4e4 held-out rows, with test noise removed. There is no exact target.

## 1. Frozen hypotheses

| ID | Verdict | Numbers |
|---|---|---|
| U1 (gate falls back) — **primary** | **PASS** | 0/20 picked, 0 losses |
| U2 (ungated IQP loses) | **PASS** | R ≥ 1 on 20/20; median 4.35 [4.14, 4.58], min 3.86 |

**Frozen reading:** MNIST-16 is not in the IQP-like regime.
- The real-data result is **negative for the IQP and positive for the gate**.
- The safety half of the claim carries over to one real dataset; the gain half is not shown on
  real data.

## 2. What the numbers show

**The IQP cannot fit the training moments.**
- G's residual on the order-≤3 moments is r_N = 0.75 [0.67, 0.82], about 33× the noise floor
  (0.023).
- The excess is 0.73, against τ = 0.01, so the gate's margin is about 70×.
- This is the step 12 pattern for `lcm` and `ising4`, only stronger.

**It loses at every order.** R is 4.4 at order 4, 4.9 at order 5 and 3.8 at order 6.

**D3 is high but does not help.**
- MNIST-16 has D3 = 0.57: MaxEnt(3) leaves *more* completion room than on the synthetic n = 16
  `iqp4` targets (D3 ≈ 0.33).
- Yet the IQP cannot use that room, because it cannot reproduce the low-order moments in the first
  place.
- So D3 measures room. It does not say whether the IQP fits, and the training residual, which the
  gate uses, is the operative test. This is consistent with steps 12–13.

## 3. Caveats

- One dataset and one 16-bit reduction. The reduction was fixed before any fit and not varied.
  Other reductions of the same images, such as different crops or thresholds, are untested.
- Natural-image pixels have local, mostly pairwise correlations plus higher-order shape structure.
  A latent-variable model, not a phase circuit, is the natural generative story. A negative
  result here is the expected outcome, not a surprising one.
- Data whose structure is parity- or phase-like, such as error-correction syndromes or some
  physics measurement records, remain untested. They are where an IQP advantage would be
  plausible.

## 4. What this changes

The claim adds one real-data clause:

> … It never picks the IQP on non-IQP data: 0/120 synthetic across N ∈ {1e4, 3e4, 1e5}, and 0/20
> splits of a real dataset (MNIST-16, where the ungated IQP loses about 4×). The gain is shown on
> IQP-like synthetic data only.

Next, by the recommended path:
- **Rank 3, an adversarial non-IQP family.** The safety half is now the part of the claim that
  generalises to real data. Its known weak spot is a target the IQP fits at low order but completes
  badly. No family tested so far does that: every non-IQP target so far, MNIST included, fails at
  low order already.
- **Then a real dataset with parity-like structure,** for the gain half.
