# Step 5 amendment 1: Q5 when a crossing is undefined (qgen-practical)

Status: **approved by the user**, 2026-11-07 (decision A). It amends `specs/step5_iqp4_sigma_scan.md`,
which was frozen at 53d28cf.

This amendment was written **before the grid ran**. At that point the only step-5 completion
numbers in existence were:
- the step-4 reproduction instance (`iqp4`, σ = 0.2, N = ∞, seed 0), which is data already seen;
- the two timing instances at σ = 0.25, N = 1e4, seed 0. Only their timings and training
  residuals were read.

No σ\*, and no median over seeds, has been computed.

## Change

Spec section 3 defines Q5 only for the case where σ\*(1e4) is undefined because R lies on one
side of 1 everywhere. Two further cases are now fixed, both as **FAIL**, with the reason stated in
the SUMMARY:

1. **σ\*(iqp4, N = ∞) is undefined.**
   - The comparison has no reference, so Q5 FAILs, whatever σ\*(1e4) is.
   - Q1 fails as well in this case.
2. **σ\*(iqp4, N = 1e4) is undefined, but median R − 1 changes sign on the grid.**
   - For example, R < 1 at small σ and R ≥ 1 at large σ: the only crossing goes upward, which is
     not the downward crossing that σ\* is defined by.
   - Q5 FAILs.

Every other rule stays as written:
- Q5 PASSes if R ≥ 1 everywhere at N = 1e4. It FAILs if R < 1 everywhere.
- If both crossings are defined, Q5 PASSes when σ\*(1e4) ≥ σ\*(∞).

**Why:** the builder chose this reading at build order item 2, and it is the conservative one.
Writing it down before the grid keeps it from becoming a rule chosen after the result.

No other change is made.
