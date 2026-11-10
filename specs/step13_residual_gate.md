# Step 13 spec: a formal test of the residual-gated estimator on fresh seeds (qgen-practical)

Status: **frozen** once committed. The user chose A on 2026-11-10 and asked Claude to take the
recommended option from now on. Written **after step 12**
(`notes/2026-11-10_step12_findings.md`). Sections 2–4 are frozen; any change needs a numbered
amendment, written before the grid.

**Harness note.** As in steps 9–12, no hook or `BUDGET_OK` is installed. The acceptance check is
`python -m src.step13.run --verify`, which must exit 0; its raw output goes into the SUMMARY.

## 1. Question

Steps 9–12 give a split picture:
- On IQP-like targets (`iqp4`), the IQP beats MaxEnt(3) when it fits the training moments.
- On non-IQP targets (`lcm`, `ising4`), it loses on every seed, but there it also misfits the
  training moments on every seed (median residual 0.2–1.6).

That suggests a deployable estimator that uses **only the training data**:

> **Gate:** fit G. If its training residual is ≤ τ = 1e-2, output G's distribution; otherwise
> output MaxEnt(3).

The gate uses the order-≤3 moments only, never orders 4–6 or the target, so it is a legitimate
estimator rather than an oracle.

**Why fresh seeds are load-bearing.** τ = 1e-2 was suggested in step 10 after looking at seeds
10–29. Re-scoring those same seeds would test the gate on the data that chose it. On that
development data:

| n | IQP picked | wins | losses | ties |
|---|---|---|---|---|
| 16 | 16/20 | 14 | 2 | 4 |
| 14 | 12/20 | 9 | 3 | 8 |

On step 12's data the gate picks the IQP 0/80 times. All of that is development data. This step
re-tests it on **seeds 30–49**, which no step has used.

## 2. Design

- **Targets** (seeds 30–49, N = ∞):
  - `iqp4` at level B: `src/step7/run.run_instance(n, "B", seed)`, imported unchanged. σ = 0.251
    at n = 16 and 0.213 at n = 14.
  - `lcm` and `ising4`: `src/step12/targets.py`, with β read from
    `results/step12/CALIBRATION.json`. β is not recalibrated.
- **n:** 16 (primary) and 14 (secondary). That gives 3 × 2 × 20 = **120 instances**.
- **Fits:**
  - MaxEnt(3) with ridge 1e-8;
  - G with 3 restarts via `fit_restarts`, selected by lowest training residual;
  - the same code and budget as steps 9 and 12;
  - no bitflip.
- **Per-instance quantities:**
  - R = G_iqp / G_maxent3 and the training residual r.
  - The gated ratio is R_gate = R if r ≤ τ, else exactly 1.
  - **Outcome:** a win if R_gate < 1, a loss if R_gate > 1, a tie if the gate fell back. A picked
    instance with R exactly 1 counts as a loss.
- τ = 1e-2 is frozen. The comparison is ≤ τ, inclusive.
- `src/step1..12` are never edited.

## 3. Frozen hypotheses

Sign test: one-sided binomial p over the non-tied instances, P(X ≥ wins | m, 1/2).

| ID | Statement | Kind |
|---|---|---|
| F1 | `iqp4`, n = 16: wins ≥ 10/20 **and** sign-test p ≤ 0.05 | **primary, gain**: the gate turns the IQP's in-family advantage into a deployable win |
| F2 | `lcm` + `ising4` pooled, n = 16: losses ≤ 2/40 | **primary, safety**: out of family the gate does no harm |
| F3 | F1 at n = 14 | secondary. Development data would FAIL it (9 wins, p = 0.073), so a FAIL is expected and not alarming |
| F4 | F2 at n = 14 | secondary |

**Reading rules, fixed now:**
- **F1 and F2 PASS:** the paper's deployable claim is "a training-residual gate gives an
  estimator that beats MaxEnt(3) on IQP-like data and falls back safely elsewhere (n = 16)".
- **F1 FAIL:** the step 9 advantage does not survive gating on fresh seeds. The claim stays at
  the descriptive level of step 9.
- **F2 FAIL:** the gate is not safe. The IQP can fit non-IQP low-order moments and still complete
  them worse. The gate claim is withdrawn.

**Exploratory, descriptive only:**
- the geometric mean of R_gate over all 60 instances at each n (the mixed pool);
- the oracle bound, geometric mean of min(R, 1);
- the worst R_gate among picked instances;
- the counts at τ ∈ {3e-3, 3e-2};
- the residual distribution per family;
- a check that development-data counts are reproduced by the same gate code on step 9's table.

## 4. Artifacts and acceptance

- Results:
  - `results/step13/<family>/n_<n>/seed_<s>/metrics.json`;
  - `table.csv`, `verdicts.json` and `SUMMARY.md`;
  - `figures/step13/gate`, png and pdf. It plots R against training residual for every instance,
    one marker per family, both n, on log–log axes, with lines at R = 1 and r = τ. The
    prediction is that iqp4 wins cluster bottom-left, while lcm and ising4 sit right of τ.
- The SUMMARY opens with: "Step 13 was designed after step 12; seeds 30–49 are fresh; the gate
  threshold τ = 1e-2 was chosen on seeds 10–29 and is frozen; the gate uses training moments
  only; G is the generic IQP (no oracle); n ≤ 16 proxies are not hardness evidence."
- `--verify` checks:
  - the spec is committed and unchanged;
  - `src/step1..12` are unchanged since step 12's results commit 41df310;
  - 120 metrics files exist, with the right family, n and seed, 3 G restarts, β from step 12's
    calibration for `lcm` and `ising4`, and level B with step 9's σ for `iqp4`;
  - every target p ≥ 0 and sums to 1 within 1e-12;
  - the SUMMARY sentence and F1–F4 are marked;
  - the figure exists;
  - `tests/test_step13.py` passes.
- **Tests, written before the grid:**
  - the gate is a tie when r > τ, returns R when r ≤ τ, and is inclusive at τ;
  - the sign-test p for 14 of 16 is 0.00209 within 1e-4;
  - the gate code on step 9's `table.csv` reproduces the development counts above (16/14/2 and
    12/9/3);
  - seeds 30–49 do not overlap any seed used in steps 9–12.

## 5. Budget

- From steps 9 and 12, G at n = 16 takes about 15–35 min per instance single-threaded, and n = 14
  takes about 1–5 min.
- Projection: 60 n = 16 jobs on 16 workers is about 4 rounds × 30 min, so about 2 h. The n = 14
  half adds about 0.3 h.
- **Stop-loss: 4 h. Named lever:** drop the n = 14 half (F3, F4). Never cut seeds, restarts or a
  family.
