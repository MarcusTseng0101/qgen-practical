# Step 14 findings: the gated advantage survives N = 1e5 shots but not N = 1e4 (synthetic, n = 16)

Research note, 2026-11-11.

**Sources**
- Results: branch `step14-finiteN`, code df5bdfe, results 56f91fc, with
  `results/step14/SUMMARY.md`, `verdicts.json`, `table.csv`, `verify.txt`, `pilot/` and
  `figures/step14/gate_finiteN`.
- Spec: `specs/step14_finiteN_gate.md`, frozen at 4baf9c1.

**Process:**
- `--verify` **exits 0**.
- 120 instances took 3.93 h on 16 workers × 1 thread, with no failures. That is under the 5 h
  stop-loss, but above the 2.5 h projection: iqp4 jobs at N = 1e4 took about 2 h each under
  contention.
- Seeds 50–69 were fresh.

**Required caveat:**
- The gate is r_N − Σ(1 − f̂²)/N ≤ τ = 1e-2, computed from training samples only. The rule was
  chosen on a pilot over development seeds, and τ was carried over from step 13.
- G is the generic IQP with no oracle. MaxEnt(3) and G see the same noisy moments.
- n = 16 proxies are not hardness evidence.

## 1. Frozen hypotheses

| ID | Verdict | Numbers |
|---|---|---|
| S1 (iqp4, N = 1e5, gain) — **primary** | **PASS** | picks IQP 14/20: 11 wins, 3 losses; p = 0.029 |
| S2 (lcm + ising4, N = 1e5, safety) — **primary** | **PASS** | 0/40 picked |
| S3 (iqp4, N = 1e4, gain) | FAIL | picks 20/20: 12 wins, 8 losses; p = 0.25 |
| S4 (lcm + ising4, N = 1e4, safety) | PASS | 0/40 picked |

**Frozen reading:**
- S1 and S2 PASS, so the gated claim survives N = 1e5 at n = 16.
- S3 FAIL with S1 PASS states the shot requirement: at n = 16, somewhere between 1e4 and 1e5
  shots are needed. It is not a contradiction.

## 2. What the numbers show

- **Noise erodes the underlying advantage**, even before gating. On iqp4 the always-IQP median R
  is:
  - 0.66 at N = ∞ (step 13, seeds 30–49);
  - 0.93 at N = 1e5;
  - 0.99 at N = 1e4.

  At finite N, MaxEnt(3) and G both fit the noisy moments, and G's extra freedom absorbs noise.
- **At N = 1e5 the gate still discriminates.** It rejected 6 iqp4 seeds, and 5 of them had R > 1
  (up to 3.85). The pooled geometric mean of R_gate is 0.953, against an oracle 0.941 and
  always-IQP 3.5.
- **At N = 1e4 the gate goes blind on iqp4.**
  - The floor (0.066) is 3–4× G's raw residual (0.015), so the excess is negative on every iqp4
    seed and the gate picks all 20.
  - G's residual against the exact moments, r_true ≈ 0.058, is about the noise level. G is fitting
    noise, so the residual no longer measures misspecification.
  - The uncorrected gate (r_N ≤ τ) is no better at N = 1e4: 6 picked, 4 wins, 2 losses.
- **Out of family the gate stays safe at both N** (0/80 picked). The excess residual of `lcm` and
  `ising4` (medians 0.12–0.52) is far above τ even with the noise correction.
  - At τ = 3e-2 a single `lcm` instance would be picked at N = 1e4, and it loses. So τ = 1e-2 has
    margin, but not unlimited margin.

## 3. Caveats

- There are two N values, so the threshold N between 1e4 and 1e5 is not located.
- The noise floor assumes independent moment errors with variance (1 − f²)/N. That is right per
  moment, but G's 696 parameters equal the number of moments, so G can absorb noise. The
  split-sample gate (stub) would avoid this and is the natural fix for small N.
- This is n = 16 only. The floor scales as (number of moments)/N ≈ n³/(6N), so the shot
  requirement grows roughly as n³.

## 4. What this changes

The claim now reads:

> At n = 16, with N = 1e5 samples, a training-only residual gate picks the generic IQP over
> MaxEnt(3) on IQP-like data and wins 11 of 14 decided seeds (p = 0.03). It never picks the IQP on
> non-IQP data (0/40). At N = 1e4 the advantage is gone.

Next, by the recommended path: a mid-term write-up of steps 1–14. The result is now pre-registered
across fresh seeds, families and shot counts, and further compute has diminishing returns until
the claim is written down.
