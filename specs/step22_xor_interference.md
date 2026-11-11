# Step 22 spec: is the IQP's QEC loss its interference? A classical XOR model as the third arm

Status: **frozen** once committed. Written after step 21. Claude chose this step under the user's standing
instruction to take the recommended option. Part A uses spent data (development); Part B uses the unspent
d3_r07 runs (test). The hypotheses in §4 are fixed here, before any XOR fit has been run on any data.

**Acceptance:** `python -m src.step22.run --verify` must exit 0. It is the definition of done; a FAIL
hypothesis is a result, not a reason to change the check.

## 1. Why (the theory this step tests)

Write the IQP state as |ψ⟩ = Π_g exp(iθ_g X_g)|0⟩ over generators g (bit masks). Each factor, alone, flips
the bits of g with probability sin²θ_g. Then:

- **Classical XOR model.** Independent mechanisms e, each flipping mask e with probability p_e. Its parities are
  f(A) = Π_{e : |e∩A| odd} (1 − 2p_e). This is the standard detector-error model of surface-code data
  under independent Pauli noise.
- **IQP.** If the generators are linearly independent over GF(2), or their only dependencies have odd
  length, the IQP output equals the XOR model with p_g = sin²θ_g exactly. Dependencies of **even** length
  (e.g. a 4-cycle {0,1},{2,3},{0,2},{1,3}) add interference terms that the XOR model does not have.
  A 4-bit check (scratchpad, 2026-11-11) gave max |p_iqp − p_xor| = 1e-16 (independent), 6e-17 (3-cycle)
  and 5.5e-2 (4-cycle).
- The weight-≤3 generator set on 16 bits is full of 4-cycles, so the fitted IQP always carries interference.

**Hypothesis.** QEC detector data is incoherent (XOR-like). The IQP's only non-classical freedom,
interference, is then the wrong inductive bias: matching order ≤ 3 with interference terms completes orders
4–6 wrongly. This would explain step 21: 0 resolved IQP wins and 3 reproducible losses. It also predicts the
regime where the IQP should win: data with coherent structure (the iqp4 family).

**What must not happen.** The theory came from looking at steps 19–21. Testing it only on those 16 runs
would be circular. That is why Part B uses fresh runs and the decisive hypotheses live there.

## 2. The XOR model (load-bearing details)

- **Mechanisms.** E = `masks_up_to(16, 3)`: the 696 masks of weight 1–3. This is **the same set as the IQP
  generators**, so the parameter count is identical (696) for the XOR model, the IQP and MaxEnt(3).
  - Do not use Google's published detector error model or any circuit knowledge. That would be oracle
    information the other two models do not get, and the comparison would prove nothing.
- **Parameters.** w_e ≥ 0, p_e = (1 − e^{−w_e})/2 ∈ [0, ½). Model parities are f(A) = exp(−Σ_e [|e∩A| odd] w_e).
- **Fit.** Minimise Σ_{a ∈ ops} (f(a) − f̂_a)², ops = `masks_up_to(16, 3)`, by L-BFGS-B with bounds w ≥ 0.
  - This is the same loss and the same moments as the IQP fit, on the **same fit rows**:
    - QEC: the first 80% of the 3e4 training shots, N_fit = 2.4e4;
    - iqp4: N_fit = 1e5.
  - Initialise from NNLS on −log(max(f̂, 1e-3)) = M w, where M_ae = [|e∩a| odd]. The 1e-3 clip is a guess.
  - One deterministic fit; no restarts.
  - The model cannot produce f ≤ 0. Report the count of f̂_a ≤ 0 per instance; do not "fix" it.
- **Distribution.** q_xor is computed by 696 sequential XOR convolutions on 2^16 states. It is exact; no
  sampling.

## 3. Instances and scoring

**Part A (development, spent).**
- The 16 runs and 2 splits of step 21 (r03 and r05, splits 100 and 101).
- q_g and q_me are loaded from `data/derived/step21/*.npz`, not refitted.
- S0 check: the loaded models must reproduce step 21's R to 1e-9 relative.

**Part B (test, unspent).**
- The 8 runs `surface_code_b{X,Z}_d3_r07_center_{3_5,5_3,5_7,7_5}`, detectors 4–19 (n = 16), split seed 100.
- All three models are fitted with step 20's `fit_and_gate` procedure, unchanged, plus the XOR model.
- **iqp4 control:** the 14 iqp4 seeds of step 20 (300–303, 310–319). Same fit rows; G is exact against the
  target. G_iqp and G_maxent are read from `results/step20/**/metrics.json`.
- **Synthetic XOR control:** 8 seeds `default_rng(22100+s)`.
  - Mechanisms are the 120 weight-2 masks plus 16 weight-1 masks, p_e ~ U(0, 0.03), which is QEC-like.
  - The target is exact; 2.4e4 fit rows are sampled with `default_rng(22200+s)`.
  - Only the XOR model and MaxEnt are fitted (no IQP).

**Score.** The corrected held-out gap G of step 17 on QEC, and the exact completion gap on synthetic data.

**Comparison CIs.** ΔG(X − Y) with a 95% bootstrap CI: step 21's `boot_ci`, B = 400, `default_rng(22000+b)`,
test rows resampled, models fixed.
- **resolved X-better** if CI < 0;
- **resolved Y-better** if CI > 0;
- **unresolved** otherwise.

**Non-XOR component.** For a model q: fit the XOR model to q's own exact order-≤3 parities, then
I(q) = mean over l ∈ {4, 5, 6} of mean over |A| = l of (f_q(A) − f_xor[q](A))².
- It measures how far q's completion departs from the classical XOR completion of the same low orders.
- This is a proxy for interference, not a direct measure, because θ was not saved in step 21.

## 4. Pre-declared hypotheses

| ID | Data | Statement | PASS iff |
|---|---|---|---|
| X0 | synthetic XOR, 8 | the XOR fitter works (control) | G_xor < G_maxent on ≥ 7/8 |
| C1 | r07 test, 8 | the correct classical bias beats MaxEnt(3) on real QEC | resolved XOR-better ≥ 4/8 **and** resolved MaxEnt-better = 0 |
| C2 | r07 test, 8 | the XOR model beats the IQP on real QEC | resolved XOR-better ≥ 4/8 **and** resolved IQP-better = 0 |
| X4 | iqp4, 14 | the IQP beats the XOR model where data is coherent | G_iqp < G_xor on ≥ 11/14 |

**Readings, no PASS/FAIL (Part A and B):**
- **A1:** the C1 and C2 counts on the 32 spent cells.
- **A2:** Spearman ρ between I(q_g) and the ΔG(IQP − MaxEnt) point estimate over the 32 spent cells, with a
  permutation p-value (10 000 permutations, `default_rng(22300)`). The cells are not independent, because each
  run appears in two splits, so p is indicative only.
- **A3:** the count of f̂ ≤ 0 per instance.

**What each outcome means (fixed now):**
- **C1, C2 and X4 all PASS:** the IQP's advantage tracks coherent structure. On incoherent real data the right
  model is classical, and it wins resolvably. This is the paper's main claim.
- **C2 PASS, X4 FAIL:** the IQP loses to the classical model on QEC, but the iqp4 wins are not explained by
  interference. The paper reports the classical model as the QEC baseline and drops the interference story.
- **C1 FAIL:** the XOR model does not resolvably beat MaxEnt on fresh QEC either. Either the data are not
  XOR-like at order 4–6 (correlated noise, leakage, or mechanisms of weight > 3), or 5e4 shots cannot
  resolve it. The theory stays unconfirmed on real data.
- **X0 FAIL:** the fitter is broken. Stop; read nothing else.

## 5. Failure modes to watch

- **FM1, "XOR beats everything on the control and loses on QEC by a lot".**
  - Check A3 first: f̂ ≤ 0 entries cap the fit.
  - Do not add mechanisms of weight 4. That changes the parameter count and breaks the fairness of §2.
- **FM2, "S0 reproduction fails".** The npz models do not belong to the split. Stop; do not refit Part A.
- **FM3, r07 extraction.** The r07 runs have 56 detectors. Columns 4:20 are still t = 1 and t = 2 (8 per
  round, after 4 at t = 0). A test asserts n_det = 56 and the 50 000-shot shape.

## 6. Artifacts

- `results/step22/{partA,partB,iqp4,synth}/…json`, plus `SUMMARY.md`, which opens with: "Step 22 tests
  whether the IQP's QEC losses are its interference, using a classical XOR model with the same 696
  parameters; decisive hypotheses are on the unspent r07 runs."
- **`--verify` checks:**
  - the spec is committed and unchanged;
  - `src/step1..21` are unchanged since the step 21 results commit (1f0050d);
  - S0 holds;
  - all instance files exist;
  - X0, C1, C2 and X4 are each reported as PASS/FAIL;
  - `tests/test_step22.py` passes.
- **Tests:**
  - the XOR prob agrees with the formula f(A) via FWHT;
  - IQP with independent generators equals XOR, and the 4-cycle differs;
  - the fitter recovers p from exact moments at n = 6;
  - r07 shape;
  - Part B runs are disjoint from steps 19–21.

## 7. Budget

- **XOR fits** are seconds to minutes each. Part A, iqp4 and synth together should take under 1 h.
- **Part B:** 8 IQP fits, about 65–100 min each, 8 in parallel. That is within MAX_PAR = 12, which ran out of
  memory at 18.
- **Stop-loss: 3 h for Part B; 1.5 h for the rest.** The lever is B = 400 → 200 for the bootstrap. The IQP
  restarts and the fit rows must not be cut, because they define the procedure under test.
- No new data is downloaded: r07 is already in `qec3v5.zip`.
