# Step 18: the gate's safety is a property of the data family, not a guarantee (identifiability demo)

Research note, 2026-11-11.

**Sources:** branch `step18-adversarial`, commit 97648b2, `src/step18/demo.py`,
`results/step18/iqp4_s{10..13}.json`. Setup: development seeds 10–13 of `iqp4`, n = 16, exact
moments.

This is a demonstration of a mathematical identity, not a hypothesis test. No spec was frozen,
because the outcome follows from the construction.

## 1. The argument

The gate and both models see only the order-≤3 moments. Take an IQP-like target p, and let
m = MaxEnt3(p), which has the same order-≤3 moments. Then every mixture

q_λ = λ·p + (1 − λ)·m, for 0 ≤ λ ≤ 1,

has **exactly** p's order-≤3 moments, because moments are linear in the distribution. So the fits
of G and MaxEnt(3), G's training residual and the gate's decision are the same for every λ. Only
the order-4–6 truth changes with λ.

Write d = f_p − f_m and e = f_G − f_m on the order-4–6 parities. Then:
- G_iqp(λ) = mean (e − λd)²;
- G_maxent(λ) = λ² mean d²;
- R(λ) = 1 at λ* = mean e² / (2 mean e·d).

## 2. Numbers

The low-order moments of q_λ match p to within 4e-8 at every λ. The gate picks G on all 4 seeds,
since the residual is 0.003–0.006, below τ = 0.01.

| seed | R(1) | R(0.75) | R(0.5) | R(0.25) | R(0) | λ* |
|---|---|---|---|---|---|---|
| 10 | 1.04 | 1.49 | 3.08 | 13.2 | ∞ | 1.04 |
| 11 | 0.66 | 0.97 | 2.21 | 10.9 | ∞ | 0.74 |
| 12 | 0.44 | 0.63 | 1.59 | 9.1 | ∞ | 0.60 |
| 13 | 0.55 | 0.78 | 1.80 | 9.4 | ∞ | 0.66 |

On the three seeds where G wins at λ = 1, mixing in 26–40% of the MaxEnt completion is enough to
make the gated choice lose. At λ = 0 the target *is* MaxEnt(3)'s model, so MaxEnt(3) is exact and
G must lose.

## 3. Reading

- **No gate built on order-≤3 moments can be universally safe.** Safety is an empirical property
  of the families tested:
  - `lcm` and `ising4`, 0/120 picked;
  - MNIST-16, 0/20 picked.

  In all of them the IQP already fails at low order. The adversarial q_λ has no such failure.
- **The gain half has the mirror caveat.** A target that is IQP-like at low order wins only if its
  high orders are IQP-like too. The data cannot tell us which, without high-order samples.
- **Practical fix (not run): hold out high orders.** Sampled data does contain order-4–6
  information, and steps 17 and 19 already score on held-out rows. A deployable rule could
  validate on held-out order-4 moments, instead of trusting the order-≤3 residual. That would
  detect q_λ directly. It changes what "gate" means: it uses information from the target orders,
  which the moment-only setting excludes.

## 4. What this changes

The claim's safety clause is restated as an empirical statement:

> … On every non-IQP family tested (2 synthetic, 1 real), the gate never picked the IQP. This is a
> property of those families: a target whose order-≤3 moments are IQP-realizable but whose higher
> orders follow MaxEnt(3) fools any order-≤3 gate (step 18).
