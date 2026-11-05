# Steps 1–2 findings: fitting an IQP to order-≤3 moments (synthetic, n = 12)

Research note, 2026-11-06. It summarises two preregistered steps that both ended by their
kill rules, and what they taught us about the "completion gap" design
(`notes/2026-11-05_iqp-from-limits.md`).

Raw material:
- branch `step1-synthetic`: `diagnostics/step1_fm2/`, `diagnostics/step1_amend1/`;
- branch `step2-sigma`: `diagnostics/step2_h1/`.

Setting throughout:
- target = an IQP with a sparse layout (12 one-body, 18 pairs, 8 triples), θ = σ·z with
  z ~ N(0, 1);
- the models are fitted to the **exact** order-≤3 parity moments (N = inf);
- the completion error G is the mean squared parity error at orders 4–6 against the exact
  target;
- R = G_iqp / G_maxent3.

## 1. What failed, and why

| Step / check | Result | Mechanism |
|---|---|---|
| Step 1, generic 298-generator IQP, σ = 0.4 (P1) | 0/50 restarts reach the truth; residual 5.7e-3 to 2.1e-2 | Spurious stationary points with a near-singular Jacobian (sv_min 1e-9 to 1e-11). The true basin is narrow: σ_noise = 0.01 converges, 0.1 does not. `least_squares` is no better. |
| Step 1 amendment 1, small-angle NNLS selector, σ = 0.4 (P1′, P6′) | 0/5 seeds; support recall 0.05–0.13 | The second-order expansion m ≈ Mθ² is invalid at σ = 0.4 (NNLS residual 0.69–0.99) |
| Same selector at |θ| ≈ 0.05 | Ranking perfect, but the threshold admits 22 false generators | The spec's threshold guess was too low; the method itself is fine there |
| Step 2, oracle support (true 38 generators), σ = 0.05 (H1) | 0/5 seeds reach 1e-10; best residual 1e-6 to 9e-6 | Discrete wrong-sign basins: 7–8 of 18 pair signs wrong. Order-≤3 moments see pair signs only at O(θ³). The minima are well conditioned (sv_min 8e-3). |
| Step 1 `ising` control | Gap invalid (the IQP cannot fit its moments) | Design error: a negative control must be IQP-fittable |

## 2. What did *not* fail

**The completion survives the sign ambiguity** (step 2 diagnostic, 50 restart solutions at
σ = 0.05):
- Among solutions with residual < 1e-5, the spread in G_iqp is 0.1–1.0 × G_maxent. It is
  never larger.
- G_iqp tracks the training residual: corr(log) = 0.96, with G/residual ≈ 0.007–0.021.
- So wrong-sign solutions do not complete differently. Their completion error is their
  low-order misfit, carried upward.
- The best wrong-sign solution completes **better than MaxEnt(3)** on 4/5 seeds
  (G_iqp/G_maxent = 0.1–0.6) and equally on the fifth. This is *not* a preregistered result:
  the fits failed the exact-recovery gate, and R was defined only for successful fits.

## 3. Lessons for the design

1. **Exact parameter recovery is the wrong success criterion.** The question is the
   completion, and R measures it directly. Steps 1–2 gated R behind a residual threshold of
   1e-10, which tests something much finer than the completion differences in play. This was
   a spec-design error. It is corrected in step 3, which is designed after seeing these
   diagnostics and is labelled as such.
2. **Recoverability changes character with σ.** Small σ gives correct magnitudes, ambiguous
   signs and a stable completion. Large σ gives spurious minima. Where between them the
   completion breaks is now the measurable question.
3. **Completion room is small exactly where fitting is easy.** At σ = 0.05,
   D3 = KL(p ‖ MaxEnt3(p)) = 3.7e-3 to 8.4e-3. Small-σ targets are near-identity and
   classically easy. This is the recoverability/hardness tension of R1 versus R2 in the
   design note, now with numbers.
4. **Generic generator sets are not identifiable** from order-≤3 moments (step 1). Any
   practical version needs a structure prior: a sparse layout from the data, or Huang-style
   locality, not 298 free angles.
5. **Negative controls must be paired.** `maxent_proj` (MaxEnt3 of the target: same
   order-≤3 moments, max-ent completion) isolates the completion. It was specified in
   amendment 1 but never run, because step 1 stopped first.

## 4. Status of the thesis

- Not refuted: at small σ an IQP fitted to low-order moments can complete better than
  max-ent, on IQP-shaped targets.
- Not supported either: that regime is near-identity, with little completion room, and was
  not preregistered.
- The open question is whether a σ exists with both R < 1 and non-trivial completion room,
  outside the easy regime. Step 3 measures R(σ) directly.
