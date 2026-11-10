# Step 16 findings: the gated advantage holds at N = 3e4 (n = 16, fresh seeds 70–89)

Research note, 2026-11-11.

**Sources**
- Results: branch `step16-threshold`, code 5317a9d, results 6f8b620, with
  `results/step16/SUMMARY.md`, `verdicts.json`, `table.csv`, `verify.txt` and
  `figures/step16/gate_N3e4`.
- Spec: `specs/step16_shot_threshold.md`, frozen at 3da6d5b.

**Process:**
- `--verify` **exits 0**.
- 60 instances took 2.42 h on 16 workers × 1 thread, with no failures. The projection was 2.5 h
  and the stop-loss 5 h.
- Seeds 70–89 were fresh.

**Required caveat:**
- The gate is step 14's, unchanged: r_N − Σ(1 − f̂²)/N ≤ τ = 1e-2, using training data only.
- G is the generic IQP, with no oracle.
- n = 16 proxies are not hardness evidence.

## 1. Frozen hypotheses

| ID | Verdict | Numbers |
|---|---|---|
| T1 (iqp4, N = 3e4, gain) | **PASS** | 19/20 picked: 17 wins, 2 losses; p = 3.6e-4 |
| T2 (lcm + ising4, N = 3e4, safety) | **PASS** | 0/40 picked |

**Frozen reading:** T1 PASS places the n = 16 shot threshold between N = 1e4 and N = 3e4.

## 2. What the numbers show

**On iqp4 the gate is almost always-IQP.**
- The excess is −0.019 to −0.014 on every seed.
- Of the 2 losses, the worse has R = 1.10, so a loss costs little.
- The geometric mean of R_gate is 0.718 on iqp4 and 0.895 over the pool. The oracle min(R, 1)
  gives 0.893 over the pool, so the gate is within 0.2% of it.

**Out of family the gate keeps a wide margin.**
- The excess is 0.10 or more on all 40 instances, against τ = 0.01.
- At τ = 3e-2 nothing out of family would be picked either.

**The noise floor is matched.** On iqp4, r_true (0.022) ≈ floor (0.022). G sits at the noise level
of the moments, as at N = 1e5.

**Always-IQP median R across steps.** These are different seed sets:

| N | seeds | median R [IQR] |
|---|---|---|
| ∞ | 30–49 (step 13) | 0.66 |
| 1e5 | 50–69 (step 14) | 0.93 [0.68, 1.06] |
| **3e4** | **70–89 (step 16)** | **0.71 [0.65, 0.88]** |
| 1e4 | 50–69 (step 14) | 0.99 [0.84, 1.05] |

## 3. Caveats

**R does not decrease monotonically in N across seed sets.** N = 3e4 on seeds 70–89 looks better
than N = 1e5 on seeds 50–69. The step 15 pilot shows the same thing on *identical* seeds: the
always-IQP R on seeds 10–13 was

| | s10 | s11 | s12 | s13 |
|---|---|---|---|---|
| N = 3e4 | 1.09 | 0.78 | 0.44 | 0.53 |
| N = 1e5 | 1.46 | 0.73 | 0.62 | 0.60 |

The sampling stream and G's local optimum vary between runs by as much as the effect of N. The
"threshold" is therefore soft: per instance, the advantage at 3e4–1e5 is a coin weighted toward
the IQP, and at 1e4 it is roughly a fair coin.

**This is one N between 1e4 and 1e5, at n = 16 only.** The shot requirement should grow roughly as
the number of moments, n³/6 (step 14 note).

## 4. What this changes

The claim now reads:

> At n = 16, a training-only noise-corrected residual gate picks the generic IQP over MaxEnt(3) on
> IQP-like data and wins at N = 3e4 (17/2, p = 4e-4) and N = 1e5 (11/3, p = 0.03). It never picks
> the IQP on non-IQP data: 0/120 across N ∈ {1e4, 3e4, 1e5}. At N = 1e4 the advantage itself is
> gone (12/8, not significant).

Next, by the recommended path: test whether the shot requirement scales as n³. Run the same gate
at n = 14, with N chosen so that N / (number of moments) matches n = 16 at N = 3e4. That is about
N ≈ 2e4 for 469 moments. It is a direct, cheap check of the scaling caveat.
