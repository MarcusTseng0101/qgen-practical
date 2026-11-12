# Step 22 findings: interference explains the IQP's iqp4 wins, not its QEC losses

Spec: `specs/step22_xor_interference.md`. Results: branch `step18-adversarial`, commit 2ecfebd, `results/step22/`.
`--verify` passed. The Part A models reproduced step 21's R exactly (relative error 0).

## Verdicts

| ID | Data | Value | Verdict |
|---|---|---|---|
| X0 | synthetic XOR, 8 | G_xor < G_maxent on 8/8 | PASS (the fitter works) |
| C1 | r07 test, 8 | XOR better than MaxEnt: 0 resolved; MaxEnt better: 3 resolved; 5 unresolved | **FAIL** |
| C2 | r07 test, 8 | XOR better than IQP: 2 resolved; IQP better: 0; 6 unresolved | **FAIL** (needs ≥ 4) |
| X4 | iqp4, 14 | G_iqp < G_xor on 13/14 (G_xor is often 3–10× larger) | PASS |

**Fresh-data replication of the step 21 negative.** On the r07 runs:
- IQP better than MaxEnt: 0 resolved;
- MaxEnt better than IQP: 4 resolved;
- 4 unresolved.

r07 was never touched before this step, so the "no QEC advantage" finding now holds on held-out data too.

## What this means

1. **The interference hypothesis is half right.**
   - **Right on coherent data.** On iqp4 (X4), the classical model with the same 696 parameters and no
     interference completes orders 4–6 far worse than the IQP. The IQP's synthetic advantage really is its
     interference.
   - **Wrong on QEC.** Removing the interference does not help:
     - the XOR model is about as bad as the IQP (C2: 2 resolved XOR wins, 6 unresolved);
     - both lose to MaxEnt (C1; in Part A, MaxEnt is resolved better than XOR in 10/32 cells and XOR never
       resolvably better).
   - The QEC loss is therefore not caused by interference. It comes from the "independent parity mechanism"
     structure that the IQP and the XOR model share.
2. **A2 contradicts the mechanism.** ρ(I(q_g), ΔG_IQP−MaxEnt) = −0.36 (p_perm = 0.04). The IQP fits that depart
   *more* from the XOR completion lose *less*, not more.
3. **I(MaxEnt) ≈ 4 × I(IQP) on every QEC cell.** MaxEnt's completion is far from any XOR completion, and it is
   the best of the three. At orders 4–6, QEC detector data at d = 3 is not well described by independent
   weight-≤3 flip mechanisms.
   - Candidate reasons (not tested): weight-4 hyperedges (Y errors), correlated or leakage noise, or
     non-Pauli effects.
   - Do not add weight-4 mechanisms post hoc. That breaks the equal-parameter design of §2.
4. **X0 shows the reverse case.** When the data are truly XOR (synthetic), the XOR model beats MaxEnt 8/8.
   So the right inductive bias does win at N = 2.4e4. The real QEC data simply do not have that structure.

## Updated claim (for the paper)

- **Positive and mechanistic:** the IQP's completion advantage on IQP-family data comes from interference. The
  same parameter budget without interference loses badly (13/14).
- **Negative and replicated:** on Google surface-code data the IQP has no resolved advantage on fresh runs
  (r07: 0 wins, 4 resolved losses).
- **Why the IQP loses on QEC:** not interference, but the shared parity-mechanism bias. MaxEnt's
  log-linear completion fits these data better than any mechanism model of the same size.

## Next (recommended)

Write the paper draft with this three-part structure:
- the method and reporting rule;
- the coherent-data advantage, with its mechanism shown by X4;
- the QEC negative, replicated on r07, with C1/C2 ruling out the interference explanation.

No new runs are needed.
