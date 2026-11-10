# Step 14 spec: the residual gate at finite shot count N (qgen-practical)

Status: **frozen** once committed. Written after step 13
(`notes/2026-11-10_step13_gate_findings.md`) and after a 16-instance pilot on development seeds.
Claude chose this step under the user's standing instruction to take the recommended option.
Sections 2–4 are frozen; any change needs a numbered amendment, written before the grid.

**Harness note.** As in steps 9–13, no hook or `BUDGET_OK` is installed. The acceptance check is
`python -m src.step14.run --verify`, which must exit 0; its raw output goes into the SUMMARY.

## 1. Question

Step 13's gate (use G iff its training residual is ≤ τ = 1e-2) was tested with exact moments. Real
data gives moments estimated from N samples.

At n = 16 there are 696 order-≤3 moments. The expected squared sampling error,
floor = Σ_a (1 − f̂_a²)/N, is about 0.065 at N = 1e4 and 0.0065 at N = 1e5. That is the same scale
as τ or larger, so the exact-moment gate cannot be used unchanged.

**Pilot (development seeds; `src/step14/pilot.py`, `results/step14/pilot/`).** Setup: iqp4 seeds
10–13, lcm and ising4 seeds 10–11, n = 16, N ∈ {1e4, 1e5}.

| | excess = r_N − floor | R |
|---|---|---|
| iqp4, N = 1e4 | −0.059 to −0.052 (G fits part of the noise) | 0.49–1.08 |
| iqp4, N = 1e5 | −0.0031 to +0.0005 | 0.60–1.46 |
| lcm and ising4, both N | +0.047 to +0.94 | 2.4–38 |

The pilot looked at these seeds only. It chose the rule below; the threshold was not tuned.

## 2. Design

- **Gate (frozen):** use G iff r_N − floor ≤ τ, with τ = 1e-2 (step 13's value, unchanged).
  Otherwise use MaxEnt(3).
  - floor = Σ_a (1 − f̂_a²)/N over the training moments. It is computed from training data only.
  - At N = ∞ the floor is 0, and this is exactly step 13's gate.
- **Targets:** `iqp4` at level B (σ = 0.251), `lcm` and `ising4` with step 12's β. n = 16 only.
- **Seeds 50–69.** They are fresh: no seed in 50–69 was used in steps 1–13 or in the pilot.
- **N:** 1e5 (primary) and 1e4 (secondary). The samples come from
  `training_moments(p, N, seed, n)`, so the sampling stream equals the target seed. That gives
  3 × 2 × 20 = **120 instances**.
- **Fits:** MaxEnt(3) and G are both fit to the **same** noisy moments. G uses 3 restarts via
  `fit_restarts`; MaxEnt(3) uses ridge 1e-8. Completion G is measured against the exact target.
  R = G_iqp / G_maxent3.
- **Outcome:** a win if the gate picks G and R < 1; a loss if it picks G and R ≥ 1; a tie if it
  falls back.
- `src/step1..13` are never edited.

## 3. Frozen hypotheses

Sign test: one-sided binomial p over the non-tied instances.

| ID | Statement | Kind |
|---|---|---|
| S1 | `iqp4`, N = 1e5: wins ≥ 10/20 **and** p ≤ 0.05 | **primary, gain** |
| S2 | `lcm` + `ising4`, N = 1e5: losses ≤ 2/40 | **primary, safety** |
| S3 | S1 at N = 1e4 | secondary |
| S4 | S2 at N = 1e4 | secondary |

**Reading rules, fixed now:**
- **S1 and S2 PASS:** the gated claim survives realistic shot counts (N = 1e5 at n = 16).
- **S1 FAIL:** the advantage needs more shots than 1e5. The claim is restricted to near-exact
  moments.
- **S2 FAIL:** the noise-corrected gate is unsafe; a split-sample gate (stub only, below) is needed.
- **S3 FAIL with S1 PASS:** this states the shot requirement and is not a contradiction. The pilot
  R values at N = 1e4 straddle 1.

**Exploratory:**
- the excess residual per family;
- r_true, G's residual against the exact moments;
- the geometric means of R_gate, always-IQP and the oracle min(R, 1);
- the counts with the uncorrected gate (r_N ≤ τ);
- the counts at τ ∈ {3e-3, 3e-2}.

**Out of scope (stub only):** a split-sample gate, which fits on half the samples and scores the
residual on the other half.

## 4. Artifacts and acceptance

- Results:
  - `results/step14/<family>/N_<N>/seed_<s>/metrics.json`;
  - `table.csv`, `verdicts.json` and `SUMMARY.md`;
  - `figures/step14/gate_finiteN`, png and pdf. It plots R against excess residual, with one panel
    per N, a symlog x-axis, a line at R = 1 and a line at excess = τ.
- The SUMMARY opens with: "Step 14 was designed after step 13 and a pilot on development seeds;
  seeds 50–69 are fresh; the gate uses r_N − Σ(1 − f̂²)/N ≤ τ = 1e-2 from training data only;
  G is the generic IQP (no oracle); n = 16 proxies are not hardness evidence."
- `--verify` checks:
  - the spec is committed and unchanged;
  - `src/step1..13` are unchanged since step 13's results commit b31cb7b;
  - 120 metrics files exist, with the right family, N and seed, 3 G restarts, and step 12's β or
    level-B σ;
  - every target p ≥ 0 and sums to 1 within 1e-12;
  - the SUMMARY sentence and S1–S4 are marked;
  - the figure exists;
  - `tests/test_step14.py` passes.
- **Tests, written before the grid:**
  - the floor formula on a hand example;
  - the gate equals step 13's gate when the floor is 0;
  - the gate is inclusive at τ;
  - seeds 50–69 are disjoint from every earlier seed set and from the pilot.

## 5. Budget

- From the pilot, iqp4 takes about 32 min and lcm or ising4 about 13 min per instance,
  single-threaded. 120 jobs on 16 workers is about 2.5 h.
- **Stop-loss: 5 h. Named lever:** drop N = 1e4 (S3, S4). Never cut seeds, restarts or a family.
