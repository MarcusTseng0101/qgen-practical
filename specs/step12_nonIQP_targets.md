# Step 12 spec: does the completion advantage survive on targets that are not IQPs? (qgen-practical)

Status: **frozen** (user chose A on 2026-11-10). Written **after step 11**
(`notes/2026-11-10_step11_bitflip_findings.md`). Once this file is committed, sections 2–3 are
frozen. The calibration in section 2 runs on seeds 0–4 only and is part of the frozen procedure,
not a free choice. Any other change needs a numbered amendment, written before the grid.

**Harness note.** As in steps 9–11, no hook or `BUDGET_OK` is installed. The acceptance check is
`python -m src.step12.run --verify`, which must exit 0; its raw output goes into the SUMMARY.

## 1. Question

Steps 9 and 11 show that the generic weight-≤3 IQP completes orders 4–6 better than MaxEnt(3),
and far better than its decohered twin, **on `iqp4` targets, which are coherent IQPs**. That
favours the IQP by construction.

Step 12 asks whether the advantage survives on target families where the IQP is **not** native.

**Prior evidence (step 4, n = 12).** On a product-Bernoulli mixture, R ≈ 3–6, so there was no
advantage. Those mixtures were weakly peaked (D3 ≈ 0.04, the σ = 0.1 level), and no mixture of
that form reached σ = 0.2's peakedness. A FAIL here is therefore the expected outcome. This step
closes that gap by matching peakedness to step 9.

## 2. Design

- **Families** (new, `src/step12/targets.py`). Every numeric scale below is a **guess**, except β,
  which is calibrated.
  - `lcm`, a latent-class mixture: K = 4 classes, w ~ Dirichlet(1), and
    P(x_j = 1 | k) = sigmoid(β z_kj) with z ~ N(0, 1), all drawn from `default_rng(12000 + seed)`.
    - It is classical and natural (latent structure).
    - It is native to neither model.
  - `ising4`, a Boltzmann target: p(s) ∝ exp(β E(s)), with s = 1 − 2x and
    E = Σ_i h_i s_i + Σ_{i<j} J_ij s_i s_j + Σ_{T ∈ 𝒯} K_T s_T + Σ_{Q ∈ 𝒬} L_Q s_Q, where
    - h ~ N(0, 0.25);
    - J ~ N(0, 1/n) on all pairs;
    - 𝒯 is n random triples, with K ~ N(0, 1/n);
    - 𝒬 is 6 random quadruples, with L ~ N(0, 1);
    - everything is drawn from `default_rng(13000 + seed)`.

    It is native to MaxEnt(3) apart from 6 weight-4 terms. That mirrors `iqp4`, which is native
    to the IQP apart from 6 weight-4 generators.
- **Peakedness calibration** (frozen procedure, run before the grid):
  - For each (family, n), bisect log β in [0.01, 20] until the **median collision ratio over seeds
    0–4** equals the median for step 9's `iqp4` at that n: 479.1 at n = 14 and 319.1 at n = 16.
  - Stop when the ratio is within 1% of the reference.
  - Write the result to `results/step12/CALIBRATION.json`.
  - Seeds 0–4 are not test seeds, and the procedure looks at no fit result.
- **Test instances:** seeds 10–29, n ∈ {16, 14}, N = ∞, both families: 80 instances.
- **Fits** for each instance, with the same code and budget as step 9 (G) and step 11 (bitflip):
  - MaxEnt(3) with ridge 1e-8;
  - G, the generic IQP with all weight-≤3 generators, 3 restarts, via
    `src/step3/run.fit_restarts`;
  - the bitflip twin (`src/step11/bitflip.py`), 3 restarts with the same `replay_inits` vectors.

  Selection is by lowest training residual. R = G_iqp/G_maxent3, Q = G_iqp/G_bitflip and
  R_B = G_bitflip/G_maxent3. D3 = KL(p ‖ MaxEnt3) is computed from the same MaxEnt fit.
- **Threads:** 1 per worker, 16 workers. Jobs run as n = 16 first, then n = 14.
- `src/step1..11` are never edited.
- **Out of scope (stub only):** a fitted latent-class baseline. It would be well specified on
  `lcm`, so the real classical bar there is higher than MaxEnt(3). This is stated as a limit, not
  run.

## 3. Frozen hypotheses

Sign tests at ≥ 15/20 (one-sided p ≈ 0.021).

| ID | Statement | Kind |
|---|---|---|
| E1 | `lcm`, n = 16: R < 1 in ≥ 15/20 | **primary**: the advantage survives on neutral data |
| E2 | `lcm`, n = 16: Q < 1 in ≥ 15/20 | coherence still helps on neutral data |
| E3 | `ising4`, n = 16: R < 1 in ≥ 15/20 | the advantage holds even on MaxEnt-native data |
| E4 | `ising4`, n = 16: Q < 1 in ≥ 15/20 | coherence helps on MaxEnt-native data |
| E5–E8 | E1–E4 at n = 14 | secondary |

**Reading rules (n = 16), fixed now:**
- **E1 PASS:** the completion advantage is not specific to IQP-generated data. If E2 also passes,
  coherence is part of it.
- **E1 FAIL:** the advantage of steps 9–11 is specific to IQP-like targets. The main claim must
  be restricted to "the IQP completes IQP-like data better than MaxEnt(3)". This is consistent
  with step 4.
- **E3** is expected to FAIL. A PASS would be surprising: a sign that MaxEnt(3)'s weight-4 blind
  spot is worse than the IQP's misspecification.
- **E2 or E4 FAIL while E1 or E3 PASS:** a classical twin does as well. On that family the gain is
  structural, not coherent.

**Exploratory:** training residuals (the count above 1e-2), D3, the medians of R, Q and R_B, the
Spearman correlation of R and D3 within each family, and the residual-gated estimator (IQP if its
residual is ≤ 1e-2, else MaxEnt(3)) as a descriptive count only.

## 4. Artifacts and acceptance

- Results:
  - `results/step12/CALIBRATION.json`;
  - `results/step12/<family>/n_<n>/seed_<s>/metrics.json`;
  - `table.csv`, `verdicts.json` and `SUMMARY.md`;
  - `figures/step12/R_by_family` (png + pdf): R per seed for each family and n, with `iqp4` from
    step 9 alongside for reference, on a log scale with a line at 1.
- The SUMMARY opens with: "Step 12 was designed after step 11; the targets are not IQPs (`lcm` is
  a latent-class mixture, `ising4` a Boltzmann model with weight-4 terms), with peakedness
  calibrated to step 9 on seeds 0–4; G is the generic IQP (no oracle); n ≤ 16 proxies are not
  hardness evidence."
- `--verify` checks:
  - the spec is committed and unchanged;
  - `src/step1..11` are unchanged since the step-11 results commit 438fc80;
  - the calibration file exists, and each median is within 1% of the reference;
  - 80 metrics files exist, with the calibrated β, 3 G restarts and 3 bitflip restarts;
  - every target p ≥ 0 and sums to 1 within 1e-12;
  - the SUMMARY sentence and E1–E8 are marked;
  - the figure exists;
  - `tests/test_step12.py` passes.
- **Tests, written before the grid:**
  - `lcm` equals an explicit mixture sum at n = 6;
  - `ising4` equals explicit enumeration of exp(βE) at n = 6;
  - both are deterministic in the seed;
  - `ising4` has exactly 6 weight-4 terms and n triples.

## 5. Budget

- Per instance: G at n = 16 took about 35 min single-threaded in step 9 (3 restarts) and about
  40 min under contention. Bitflip at n = 16 is about 2 min per restart. MaxEnt is minutes.
- Projection: 40 n = 16 instances on 16 workers is about 2.5 rounds × 45 min, so about 2 h. The
  n = 14 half adds about 0.5 h.
- **Stop-loss: 4 h. Named lever:** drop the n = 14 half (E5–E8) and keep n = 16. Never cut seeds,
  restarts or a family.
