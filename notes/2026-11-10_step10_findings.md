# Step 10 findings: more restarts do not rescue n = 14, because the losers sit on a moment-misfit floor (synthetic, n = 14)

Research note, 2026-11-10.

**Sources**
- Results: branch `step10-restarts`, commit a7dbff9, with `results/step10/SUMMARY.md`,
  `verdicts.json`, `table.csv`, `verify.txt` and `figures/step10/R_3_vs_10`.
- Spec: `specs/step10_more_restarts.md`, frozen at 278f69a and **designed after step 9**.

**Process:**
- `python -m src.step10.run --verify` **exits 0**.
- Restarts 0–2 reproduce step 9's three restarts exactly (relative difference 0).
- No hook or `BUDGET_OK` gate was installed, as in step 9.
- 20 seeds took 22.8 min on 16 workers × 1 thread.

**Required caveat:** this step changes G's restart budget, from 3 to 10, at n = 14 only. G is the
generic IQP (no oracle). n ≤ 16 proxies are not hardness evidence.

## 1. Frozen hypotheses (n = 14, level B, σ = 0.213, seeds 10–29)

| ID | Verdict | Numbers |
|---|---|---|
| K1 (≥ 15/20 win with 10 restarts) | **FAIL** | 11/20 (step 9: 10/20) |
| K2 (≤ 2/20 with residual > 1e-2) | **FAIL** | 7/20 (step 9: 8/20) |
| K3 (≥ 6 of step 9's 10 losers rescued) | **FAIL** | 1/10 (seed 24: 1.18 → 0.82) |
| K4 (≤ 1 of step 9's 10 winners flips) | **PASS** | 0/10. Winners mostly improve: median R 0.976 → 0.82 |

**Reading rule (spec section 3):** K2 fails, so 10 restarts do not fix the training, and the frozen
rule says "unresolved". The exploratory evidence below resolves *why* K2 fails.

## 2. A floor, not a search failure (exploratory)

- For the 7 seeds with residual above 1e-2, all 10 restarts converge within **1.18–1.57×** of the
  lowest residual. Examples:
  - seed 28: lowest 0.0354, median 0.0378;
  - seed 14: lowest 0.0328, median 0.0364.

  Different inits reach the same level. The weight-≤3 IQP **cannot match these targets' order-≤3
  moments**. This is a capacity limit of the misspecified model on those instances.
- **Step 9's label was wrong.** The n = 14 losses with high residual are not "under-training".
  They are **moment misfits**.
  - MaxEnt(3) always matches the order-≤3 moments exactly. A G that misses them starts orders 4–6
    from a worse base.
  - The weight-4 term of `iqp4` evidently moves the order-≤3 moments of some instances out of the
    reach of any weight-≤3 IQP.
- **Restart selection cannot help.**
  - The oracle, which picks the restart with the lowest true G and so uses the target, wins only
    **11/20**. That is the same as the residual rule.
  - Within an instance, residual and G are positively rank-correlated across restarts: median
    Spearman 0.69 [0.59, 0.82]. So the lowest-residual rule is a sensible choice, even though it
    hits the exact lowest-G restart only 8/20 times.
  - The restart-selection candidate from step 9 is therefore closed for n = 14.

## 3. A diagnostic that needs no target (exploratory, suggests the next test)

G's training residual uses only the training moments, so it is available in practice. At n = 14
with 10 restarts, it separates the instances well:
- residual ≤ 1e-2: **10 of 13 win**;
- residual > 1e-2: **1 of 7 wins** (seed 29: residual 0.021, R = 0.63).

At n = 16, in step 9 with 3 restarts, the separation is weaker: residual > 1e-2 in 4 seeds, 2 of
which win.

A practical rule follows: **use the IQP's completion only if it fits the training moments. If it
does not, fall back to MaxEnt(3).** A residual-gated estimator like this is a legitimate method,
because it uses no target information.
- This reading was built on these same 20 instances.
- It needs a frozen test on fresh seeds before it counts.

## 4. Where steps 5–10 now stand

- n = 16, level B, fresh seeds: the IQP wins 16/20 (step 9, H1). This is still the main positive
  result.
- n = 14, level B: about 10–11 of 20 win. More restarts (step 10) and better restart selection (the
  oracle bound) do not change that. The losers are mostly instances where the weight-≤3 IQP cannot
  even fit the order-≤3 moments.
- Why n = 14 has more misfits than n = 16 at "matched" peakedness is open. One candidate: the fresh
  n = 14 targets were more peaked than intended (median collision ratio 479 against 284).

## 5. Candidate next steps (not decided)

- **Frozen test of the residual-gated estimator** on fresh seeds (for example 30–49) at n = 14 and
  16:
  - the threshold is fixed in advance;
  - compare its G against MaxEnt(3) alone and against the IQP alone.

  This turns step 10's diagnostic into a usable method.
- **Per-seed σ matching**, so that fresh targets land at the intended peakedness.
- Practical relevance (the latent-class mixture baseline, real data) is still open. Real data has
  been deferred (it is a deep pit). A possible data and GPU partner is noted in memory (CYCU,
  Rioflorido).
