# Step 11 findings: the decohered twin cannot even fit the low-order moments (synthetic, n = 14 and 16)

Research note, 2026-11-10.

**Sources**
- Results: branch `step11-bitflip`, code 17276d5, results 438fc80, with
  `results/step11/SUMMARY.md`, `verdicts.json`, `table.csv`, `verify.txt` and
  `figures/step11/G_iqp_vs_bitflip`.
- Spec: `specs/step11_bitflip_control.md`, frozen at 0896d9b.

**Process:**
- `--verify` **exits 0**.
- 40 seeds took 0.88 h on 12 workers × 1 thread.
- Targets match step 9 exactly.
- Tests T1–T5 pass, including enumeration, gradient finite differences, the cos = 0 case and
  second-order agreement with the IQP.

**Required caveat:** the bitflip model is a classical, decohered twin of G with the same
generators, inits and optimizer. The targets are coherent IQPs, so this tests coherence on
IQP-generated data only. n ≤ 16 proxies are not hardness evidence.

## 1. Frozen hypotheses (level B, seeds 10–29, bitflip best of 3 restarts)

| ID | Verdict | Numbers |
|---|---|---|
| C1 (n = 16, G_iqp < G_bitflip in ≥ 15/20) | **PASS** | 20/20, median Q = 0.39 [0.22, 0.56] |
| C2 (n = 16, G_bitflip < G_maxent3 in ≥ 15/20) | **FAIL** | 3/20, median R_B = 1.84 [1.19, 2.97] |
| C3 (n = 14, Q < 1 in ≥ 15/20) | **PASS** | 20/20, median Q = 0.32 |
| C4 (n = 14, R_B < 1 in ≥ 15/20) | **FAIL** | 2/20, median R_B = 3.66 |

**Frozen reading (C1 PASS, C2 FAIL):** the advantage over MaxEnt(3) needs coherence; the
decohered twin with the same generators does not have it.

## 2. Why: a training-moment misfit (exploratory, load-bearing)

- The bitflip model's best training residual is above 1e-2 in **40/40** seeds (median about 0.1).
  The coherent IQP is above 1e-2 in 4/20 at n = 16 and 8/20 at n = 14.
- No seed has both residuals ≤ 1e-2, so **completion cannot be separated from training misfit**.
  The decohered twin loses already at orders 1–3, before completion begins.
- Best of 10 restarts changes nothing: R_B < 1 in 3/20 and 2/20.
- **Mechanism:** with the s_g independent, ⟨Z_a⟩ = ∏ cos 2θ_g is a multiplicative family. It
  cannot produce the low-order correlation pattern that interference among parities of the same
  bits creates in an `iqp4` target. Formally, the two models agree only to second order in θ, and
  these targets have σ ≈ 0.2–0.25 per angle, where the higher orders matter.
- **Stated plainly:** this shows coherence is needed for the generic weight-≤3 model to **fit**
  these IQP targets. It does not separately show that coherence improves completion at matched
  fit.

## 3. What it means for the project

- It strengthens the steps 9–10 reading. The n = 16 IQP advantage is not something a cheap
  classical model with the same generator structure reproduces. The classical twin is worse than
  MaxEnt(3), let alone the IQP.
- It does **not** answer the reviewer's version of the question ("is the gap a quantum
  effect?") for non-IQP data. The targets are coherent IQPs, so model-family match favors the
  coherent model by construction.
- Spearman(R, R_B) across seeds is about 0.35 at both n: instances that are hard for one model are
  only weakly hard for the other.

## 4. Candidate next steps (not decided)

- A non-IQP-generated target family, for example a latent-class mixture or a sparse Ising model
  with higher-order terms, where neither model is favored by construction. Rerun IQP against
  bitflip against MaxEnt(3).
- The residual-gated estimator (step-10 idea), as a frozen test on fresh seeds.
- Baumann et al. reproduction with an order-cut MaxEnt(k).
