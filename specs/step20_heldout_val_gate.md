# Step 20 spec: a held-out order-4 validation gate (qgen-practical)

Status: **frozen** once committed. Written after step 19 and a 12-instance development pilot. Claude chose
this step under the user's standing instruction to take the recommended option. Sections 2–4 are frozen;
any change needs a numbered amendment, written before the run.

**Harness note.** No hook or `BUDGET_OK` is installed. The acceptance check is
`python -m src.step20.run --verify`, which must exit 0.

## 1. Question

Step 19 found that the step 14 gate is unsafe on real QEC detection events:
- it picked G on 7/7 runs and lost on 5;
- an order-4 check against the *training* rows flagged none of the 5 losses.

Does an order-4 check against **held-out validation rows**, which never enter a fit, make the gate safe
without throwing away G's real wins?

**Development pilot** (`src/step20/pilot.py`, `results/step20/pilot/`). The data were the 8 spent d3_r03
runs and iqp4 seeds 300–303, using the same procedure as section 2.

| | instances | step 14 gate: picks / losses | new gate: picks / losses | wins kept |
|---|---|---|---|---|
| QEC r03 | 8 | 8 / 5 | 1 / 0 | 1 of 3 |
| iqp4 | 4 | 4 / 2 | 2 / 0 | 2 of 2 |

- Orders 4 alone and 4–6 pooled give the same decision on all 12 instances. Order 4 is kept, because it
  was fixed in the code before the pilot.
- On QEC the size of R depends strongly on the split: bX 3_5 had R = 4.86 at step 19's pilot split 10 and
  R = 0.69 here.

## 2. Design

**Procedure (`src/step20/core.py`, unchanged from the pilot).**
- Split the training shots into fit (first 80%) and validation (last 20%).
- Fit MaxEnt(3) and G (3 restarts) to the fit part's order-≤3 moments.
- Step 14 gate: r_N − floor ≤ τ = 1e-2, on the fit part.
- **New gate:** pick G iff the step 14 gate picks it **and** v₄(G) < v₄(MaxEnt3). Here
  v₄(q) = mean over |A| = 4 of [(f_q − f_val)² − (1 − f_val²)/N_val].

**Fresh test instances:**
- **QEC:** the 8 d3_r05 runs (bases X and Z at 4 centres), never fit before.
  - Detectors 4–19, which are the 8 stabilizers at t = 1 and t = 2, giving n = 16.
  - Permutation `default_rng(2100)`; train 3e4 (fit 2.4e4, validation 6e3); test 2e4.
  - Score: noise-corrected held-out gap on orders 4–6.
- **iqp4:** step 14's iqp4 target (σ level B), seeds 310–319, never used before.
  - 125 000 shots (fit 1e5, validation 2.5e4).
  - Score: the exact completion gap.

That is 18 instances. R = G(IQP) / G(MaxEnt3).
- A **loss** is a pick with R ≥ 1.
- A **win kept** is a pick with R < 1.

`src/step1..19` and `src/step20/core.py` are never edited.

## 3. Frozen hypotheses

| ID | Statement | Kind |
|---|---|---|
| W1 | Safety: the new gate has ≤ 1 loss over the 18 instances | **primary** |
| W2 | The new gate has fewer losses than the step 14 gate on the same 18 instances | secondary |
| W3 | Power: the new gate keeps ≥ 50% of the instances with R < 1 (if any) | secondary |

**Reading rules, fixed now:**
- **W1 PASS and W3 PASS.** Held-out validation repairs the gate on both real and synthetic data. The claim
  can use it in place of the step 14 gate.
- **W1 PASS and W3 FAIL.** The new gate is safe but conservative. It falls back too often to be useful
  at these N.
- **W1 FAIL.** Even held-out order-4 validation misses losses. The safety clause stays restricted as in
  step 19.

**Exploratory:**
- per-level validation differences;
- the pooled order-4–6 rule;
- per-family counts;
- R_raw on QEC.

## 4. Artifacts and acceptance

- Results: `results/step20/<instance>/metrics.json`, plus `verdicts.json` and `SUMMARY.md`.
- The SUMMARY opens with: "Step 20 was designed after step 19 and a 12-instance development pilot; the
  18 tested instances (8 QEC d3_r05 runs, iqp4 seeds 310–319) were never fit before; the validation rows
  never enter a fit."
- `--verify` checks:
  - the spec is committed and unchanged;
  - `src/step1..19` and `src/step20/core.py` are unchanged since the pilot code commit 28509d8;
  - 18 metrics files exist with the frozen N and restarts (plus the zip md5 for QEC);
  - the SUMMARY sentence and W1–W3 are marked;
  - `tests/test_step20.py` passes.
- **Tests, written before the run:**
  - the r05 reduction keeps the detectors with t ∈ {1, 2}, checked against the stim file;
  - the test instances are disjoint from the pilot instances;
  - the validation rows are disjoint from the fit rows;
  - the new gate's decision is the step 14 decision AND v₄(G) < v₄(MaxEnt3).

## 5. Budget

- In the pilot, 12 jobs in parallel took 67 min.
- 18 jobs on 32 cores should take about 75 min.
- **Stop-loss: 2.5 h.** Never drop instances silently.
