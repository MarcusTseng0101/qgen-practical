# Step 21 findings: QEC outcomes are mostly unresolved at 5e4 shots (diagnostic)

Spec: `specs/step21_qec_resolvability.md`, plus amendment 1. Results: branch `step18-adversarial`, commit
1f0050d, `results/step21/`. `--verify` passed. Split 100 reproduced step 20's R exactly (error 0).

**Run note.** The 4 h stop-loss fired at 27/32 fits. Amendment 1 was written before any result was read,
and the 5 killed fits were rerun unchanged.

## Pre-declared readings

| ID | Quantity | Value | Reading |
|---|---|---|---|
| D1 | unresolved runs at split 100 | **9/16** | ≥ 8: QEC at 5e4 shots cannot test the claim run by run |
| D2 | ΔG sign agreement, split 100 vs 101 | **8/16** | ≤ 11: the outcome depends on the split |
| D3 | Δv₄ sign matches ΔG among resolved (run, split) | 10/12 | — |

## What the 32 (run, split) cells show

- **Resolved wins for the IQP: 0 of 32.**
  - Every cell with R < 1 is unresolved.
  - So steps 19 and 20's QEC "wins" (R = 0.5–0.9) are all within test noise.
- **Resolved losses: 12 of 32.**
  - Three runs lose resolvably in **both** splits: bZ r03 3_5, bZ r03 5_7 and bX r05 5_7.
  - These are real step 18-type failures: the IQP fits order ≤ 3 below the noise floor and completes orders
    4–6 measurably worse than MaxEnt(3).
- **Point estimates lean against the IQP.** ΔG > 0 in 24/32 cells.
- **The validation check has no resolution.**
  - The Δv₄ CI excludes 0 in only 1 of 32 cells, because N_val = 6e3 is too small.
  - The step 20 new-gate decisions on QEC were therefore essentially noise. This explains the 4/8 agreement.
- **Training-sample noise matters as much as test noise.**
  - The same run can swing from R = 0.53 to R = 4.36 between splits (bX r03 5_7).
  - Single-split R values on this data should not be reported as outcomes.

## What this means for the claim

1. On QEC syndrome data the IQP **never** helps resolvably and **sometimes** hurts resolvably. There is no
   evidence of a completion advantage on this real parity-structured data at 5e4 shots.
2. The step 19 V1 FAIL stands in a sharper form:
   - the order-≤3 gate picks the IQP on every QEC run;
   - at least 3 runs are reproducible losses.
3. Held-out validation at 20% of 3e4 shots is too weak to guard against this on QEC.
   - It works on the iqp4 family (step 20: 0 losses on 14), where the differences are larger.
   - A usable guard on QEC-like data needs more validation shots, or the claim's safety clause stays
     restricted as in step 19.
4. **Reporting rule for the paper:** QEC results are given as resolved / unresolved counts with bootstrap
   CIs over at least two splits, not as win/loss counts of point R.

## Next (recommended)

Fold steps 19–21 into the mid-term report as an update box. This is writing only, with no new runs:
- the claim's safety clause is restricted;
- held-out validation works on IQP-family data;
- on QEC data there is no resolved advantage and there are 3 reproducible losses;
- the reporting rule above.
