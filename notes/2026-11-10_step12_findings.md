# Step 12 findings: on non-IQP targets the IQP loses to MaxEnt(3) on every seed (synthetic, n = 14 and 16)

Research note, 2026-11-10.

**Sources**
- Results: branch `step12-nonIQP`, code and calibration ee5afc4, results 41df310, with
  `results/step12/SUMMARY.md`, `verdicts.json`, `table.csv`, `verify.txt`, `CALIBRATION.json`
  and `figures/step12/R_by_family`.
- Spec: `specs/step12_nonIQP_targets.md`, frozen at df0eea9.

**Process:**
- `--verify` **exits 0**.
- 80 instances took 0.97 h on 16 workers × 1 thread, with no failures.
- Peakedness was calibrated on seeds 0–4. All four (family, n) medians are within 0.04% of
  step 9's `iqp4` reference.

**Required caveat:** the targets are not IQPs. `lcm` is a latent-class mixture with K = 4, and
`ising4` is a Boltzmann model with weight-4 terms. G is the generic weight-≤3 IQP with no oracle.
n ≤ 16 proxies are not hardness evidence.

## 1. Frozen hypotheses (seeds 10–29)

| ID | Verdict | Numbers |
|---|---|---|
| E1 (lcm, 16, R < 1) — **primary** | **FAIL** | 0/20, median R = 25 [17, 44] |
| E2 (lcm, 16, Q < 1) | PASS | 20/20, median Q = 0.28 |
| E3 (ising4, 16, R < 1) | FAIL (expected) | 0/20, median R = 2.05 [1.85, 2.6] |
| E4 (ising4, 16, Q < 1) | PASS | 20/20, median Q = 0.44 |
| E5 (lcm, 14, R < 1) | FAIL | 0/20, median R = 160 |
| E6 (lcm, 14, Q < 1) | PASS | 20/20 |
| E7 (ising4, 14, R < 1) | FAIL | 0/20, median R = 16.5 |
| E8 (ising4, 14, Q < 1) | PASS | 19/20 |

**Frozen reading (E1 FAIL):** the completion advantage of steps 9–11 is specific to IQP-like
targets. The main claim must be restricted to "the generic IQP completes IQP-like data better
than MaxEnt(3)". This agrees with step 4's mixture result, and the weak peakedness that limited
step 4 has now been removed.

E2 and E4 pass, so the coherent IQP still beats its decohered twin everywhere. Both models lose
to MaxEnt(3): bitflip beats MaxEnt(3) on 0/80 instances. Coherence helps the IQP, but not
enough to make it competitive on these families.

## 2. Mechanism: misspecification at training time

- **Training residual.** The IQP misfits the order-≤3 training moments on **every** seed. Median
  residuals are 0.61 (lcm, 16), 0.20 (ising4, 16), 1.57 (lcm, 14) and 0.80 (ising4, 14).
  - In step 9, by contrast, most IQP seeds fit to ≤ 1e-2.
  - So on these families R mostly measures the IQP's failure to represent the low-order data,
    not how well it completes higher orders.
- **Residual-gated estimator** (use the IQP when its residual is ≤ 1e-2, otherwise MaxEnt(3)).
  It falls back to MaxEnt(3) on all 80 instances, giving 0 wins and 0 losses. That is the
  desired safe behaviour: the gate never picks the IQP when the IQP is misspecified.
- **Spearman(R, D3)** is negative in every cell, and at n = 14 it is strongly negative (−0.82
  for lcm, −0.81 for ising4). Where MaxEnt(3) itself completes worse (larger D3), the IQP's
  relative loss is smaller.

## 3. Caveats

- **ising4 at n = 16 came out less peaked on the test seeds than on the calibration seeds.**
  - The median collision ratio is 42 on seeds 10–29, against 319 on calibration seeds 0–4.
  - The frozen procedure was followed, but this family has a large seed spread at fixed β.
  - The other three cells are close to their references: lcm 16 at 291, lcm 14 at 381, ising4 14
    at 314.
  - The E3 FAIL is expected either way, but the ising4/16 cell is not peakedness-matched in
    practice.
- **The real classical bar is higher than MaxEnt(3).** A fitted latent-class model would be well
  specified on `lcm`, and it was not run (stub only). This makes E1 FAIL only more decisive.
- **Two families is not "all natural data".** The finding rules out a generic advantage; it does
  not rule out other IQP-friendly structure (for example parity-structured data).

## 4. What this changes

- The paper claim becomes conditional: "when the data is IQP-like (the IQP fits the low-order
  moments), the IQP completes higher orders better than MaxEnt(3), and coherence is necessary."
- The natural deployable form is the **residual-gated estimator**. Step 10 suggested it, and
  here it gives 0 losses on 80 out-of-family instances. Its in-family win rate is the open
  number.
