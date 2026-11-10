# Step 13 findings: the residual-gated estimator holds on fresh seeds at n = 16 (synthetic, n = 14 and 16)

Research note, 2026-11-10.

**Sources**
- Results: branch `step13-gate`, code 91338a0, results b31cb7b, with
  `results/step13/SUMMARY.md`, `verdicts.json`, `table.csv`, `verify.txt` and
  `figures/step13/gate`.
- Spec: `specs/step13_residual_gate.md`, frozen at 70c8dbc.

**Process:**
- `--verify` **exits 0**.
- 120 instances took 2.39 h on 16 workers × 1 thread, with no failures.
- Seeds 30–49 were never used in steps 1–12, and a test checks that.

**Required caveat:** τ = 1e-2 was chosen on seeds 10–29 and frozen before this grid. The gate uses
training moments only. G is the generic IQP with no oracle. The targets are synthetic, and
n ≤ 16 proxies are not hardness evidence.

## 1. Frozen hypotheses

The gate uses G if its training residual is ≤ 1e-2, and MaxEnt(3) otherwise.

| ID | Verdict | Numbers |
|---|---|---|
| F1 (iqp4, n = 16, gain) — **primary** | **PASS** | picks IQP 15/20: 14 wins, 1 loss, 5 ties; sign p = 0.0005 |
| F2 (lcm + ising4, n = 16, safety) — **primary** | **PASS** | picks IQP 0/40: 0 losses |
| F3 (iqp4, n = 14, gain) | FAIL | 11 picked: 9 wins, 2 losses; p = 0.033. It fails only the frozen floor of ≥ 10 wins |
| F4 (lcm + ising4, n = 14, safety) | PASS | 0/40 picked |

**Frozen reading (F1 and F2 PASS):** at n = 16, a training-residual gate gives an estimator that
beats MaxEnt(3) on IQP-like data and falls back safely elsewhere. The fresh seeds reproduce the
development numbers closely: 14 wins and 1 loss here, against 14 and 2 on seeds 10–29.

## 2. Exploratory (pool of 60 instances per n, families mixed)

| | n = 16 | n = 14 |
|---|---|---|
| geometric mean R, always IQP | 3.43 | 18.1 |
| geometric mean R_gate | **0.867** | **0.93** |
| oracle min(R, 1) | 0.854 | 0.904 |
| worst R among picked | 1.46 | 1.48 |

- The gate recovers almost all of the oracle selector's gain, without seeing orders 4–6.
- **The residual separation is wide.**
  - iqp4 residual medians: 0.0057 at n = 16 and 0.0060 at n = 14.
  - lcm and ising4 never go below about 0.19, so the out-of-family fallback is not a near miss.
- **τ sensitivity at n = 16:**
  - τ = 3e-3: 6/6 wins, with no losses but fewer picks.
  - τ = 3e-2: 14 wins and 3 losses.
  - 1e-2 sits in a flat region.
- **n = 14 is weaker.** The IQP fits iqp4 less often there (11/20), and it loses on 2 of the
  picked seeds. That matches step 10's "residual floor" finding at n = 14.

## 3. Caveats

- The out-of-family test covers only two families. A target that the IQP fits at low order but
  completes badly would break F2. No such case appeared in 80 + 80 instances (steps 12–13).
- The real classical bar on `lcm` (a fitted latent-class model) still has not been run.
- Everything is exact moments with N = ∞. Finite-shot moments would inflate the residual and
  shift the effective τ. That is not tested.
- n = 14 vs n = 16: the gain does not grow cleanly with n. Two sizes are not a trend.

## 4. What this changes

The paper's main claim can now be stated as a pre-registered, fresh-seed result:

> At n = 16, a residual-gated IQP estimator beats MaxEnt(3) on IQP-like data
> (14/15 decided seeds), and never loses on non-IQP data (0/40), using training moments only.

Natural next steps:
- a finite-shot version of the gate (N < ∞), which the claim needs before any real data;
- the mid-term write-up.
