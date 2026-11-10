# Step 16 spec: the step 14 gate at N = 3e4, to locate the shot threshold (qgen-practical)

Status: **frozen** once committed. Written after step 14
(`notes/2026-11-11_step14_finiteN_findings.md`) and the step 15 split-sample pilot
(`notes/2026-11-11_step15_split_pilot.md`). Claude chose this step under the user's standing
instruction to take the recommended option. Sections 2–4 are frozen; any change needs a numbered
amendment, written before the grid.

**Harness note.** As in steps 9–14, no hook or `BUDGET_OK` is installed. The acceptance check is
`python -m src.step16.run --verify`, which must exit 0; its raw output goes into the SUMMARY.

## 1. Question

At n = 16, step 14 found that the gated advantage holds at N = 1e5 (S1 PASS) but not at N = 1e4
(S3 FAIL). Step 15's pilot showed that a better gate does not rescue N = 1e4, because the
advantage itself is gone there.

This step asks: at N = 3e4, does the **unchanged** step 14 gate still win on iqp4 and stay safe
out of family?

**Pilot evidence** (step 15, development seeds, N = 3e4):

| | in-sample excess | always-IQP R |
|---|---|---|
| iqp4, seeds 10–13 | −0.019 to −0.014 | 1.09, 0.78, 0.44, 0.53 |
| lcm and ising4, seeds 10–11 | +0.10 to +0.56 | 3.2–16.5 |

## 2. Design (identical to step 14 except N and seeds)

- **Gate (frozen, unchanged):** use G iff r_N − Σ(1 − f̂²)/N ≤ τ = 1e-2, with training data only.
  Otherwise use MaxEnt(3).
- **Targets:** iqp4 at level B, and lcm and ising4 with step 12's β. n = 16.
- **N = 3e4** only.
- **Seeds 70–89, fresh.** They are disjoint from steps 1–15 and from all pilot seeds.
  - Samples come from `training_moments(p, N, seed, n)`.
  - 3 families × 20 seeds = **60 instances**.
- **Fits:** MaxEnt(3) and G are both fit to the same noisy moments. G uses 3 restarts via
  `fit_restarts`. R = G_iqp / G_maxent3, measured against the exact target.
- **Outcome:** a win if the gate picks G and R < 1; a loss if it picks G and R ≥ 1; a tie if it
  falls back to MaxEnt(3).
- `src/step1..15` are never edited.

## 3. Frozen hypotheses

The sign test is a one-sided binomial over the non-tied instances.

| ID | Statement | Kind |
|---|---|---|
| T1 | iqp4, N = 3e4: wins ≥ 10/20 **and** p ≤ 0.05 | **primary, gain** |
| T2 | lcm + ising4, N = 3e4: losses ≤ 2/40 | **primary, safety** |

**Reading rules, fixed now:**
- **T1 PASS:** the n = 16 shot threshold lies between 1e4 and 3e4.
- **T1 FAIL:** the threshold lies between 3e4 and 1e5.
- **T2 FAIL:** the gate is unsafe at N = 3e4. This contradicts steps 14 S2 and S4, and must be
  reported as such.

**Exploratory:**
- always-IQP median R against N, combined with steps 13 and 14. These are different seed sets and
  are labelled as such.
- the excess, r_true and the floor for each family;
- the geometric means of R_gate, always-IQP and the oracle.

## 4. Artifacts and acceptance

- Results:
  - `results/step16/<family>/N_30000/seed_<s>/metrics.json`, in the same schema as step 14;
  - `table.csv`, `verdicts.json` and `SUMMARY.md`;
  - `figures/step16/gate_N3e4`, png and pdf.
- The SUMMARY opens with: "Step 16 was designed after steps 14–15 and pilots on development
  seeds; seeds 70–89 are fresh; the gate is step 14's r_N − Σ(1 − f̂²)/N ≤ τ = 1e-2 from training
  data only; G is the generic IQP (no oracle); n = 16 proxies are not hardness evidence."
- `--verify` checks:
  - the spec is committed and unchanged;
  - `src/step1..15` are unchanged since the step 15 pilot commit ee59b78;
  - 60 metrics files are present and correct;
  - the targets are valid;
  - the SUMMARY sentence and T1–T2 are marked;
  - the figure exists;
  - `tests/test_step16.py` passes.
- **Tests, written before the grid:**
  - the gate function is step 14's, with the same floor and excess;
  - seeds 70–89 are disjoint from every earlier seed set and every pilot seed;
  - N = 3e4 only.

## 5. Budget

- The step 14 grid took 3.93 h for 120 jobs, with iqp4 about 2 h under contention. Here there are
  60 jobs, and iqp4 starts first. Projection: about 2.5 h.
- **Stop-loss: 5 h.**
- **Named lever:** drop ising4, so that T2 is tested on lcm only with losses ≤ 1/20. Never cut
  seeds or restarts, and never cut iqp4.
