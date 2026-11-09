# Step 11 spec: does the IQP's completion advantage need coherence? A decohered "bitflip" control (qgen-practical)

Status: **frozen** (user chose C on 2026-11-10, via `/spec-prompt c`). Written **after step 10**
(`notes/2026-11-10_step10_findings.md`) and the literature check
(`notes/2026-11-10_literature_positioning.md`). Once this file is committed, section 3 is frozen.
Any change needs a numbered amendment, written before the runs.

**Harness note.** As in steps 9 and 10, no hook or `BUDGET_OK` is installed: the run is small
(projected well under 1 h). The acceptance check is `python -m src.step11.run --verify`, which
must exit 0; its raw output goes into the SUMMARY. The guard hook and `scripts/check.sh` are not
edited.

## 1. Question

Step 9: at n = 16, level B, the generic weight-≤3 IQP G completes orders 4–6 better than MaxEnt(3)
on 16/20 fresh seeds. **Is that because the model is a coherent quantum circuit, or because of
its generator structure alone?**

The control is the **bitflip model** of Recio-Armengol et al. (arXiv 2503.02934): the same
circuit with every gate exp(iθ_g X_g) replaced by its fully dephased version, a random flip of the
bits in g with probability sin²θ_g. It is a classical, efficiently samplable model with:
- the **same generators** as G (every weight-≤3 mask: 469 at n = 14, 696 at n = 16);
- the **same parameters** θ, inits, optimizer, restarts and training moments;
- moments in closed form: ⟨Z_a⟩ = ∏_{g : |g ∧ a| odd} cos 2θ_g.

**Why it isolates coherence.** The coherent IQP has ⟨Z_a⟩ = E_s[cos(2 Σ_{g odd} θ_g s_g)], where
each s_g = ∏_{j∈g} s_j is a parity of the same n random signs s. The bitflip moment is the same
expression with the s_g **independent**. The two agree to second order in θ. They differ only
through the correlations among the parities s_g, which is exactly the interference in the
coherent circuit.

**What a result would not show.**
- The targets are themselves coherent IQPs (`iqp4`). A bitflip loss can partly reflect the model
  family matching the target. A pass on C1 therefore shows coherence matters **for IQP-generated
  targets**, not for real data.
- n ≤ 16 proxies are not hardness evidence.

## 2. Design

- **Instances:** step 9's, unchanged: `iqp4`, level B, N = ∞, seeds 10–29, at n = 16
  (σ = 0.251) and n = 14 (σ = 0.213). Targets come from `src/step5/targets.iqp4_target` and
  training moments from `src/step4/run.training_moments`, both imported unchanged.
  - **Target check:** each instance's collision ratio must equal step 9's stored value to a
    relative 1e-12, otherwise the seed is flagged.
- **Reused, not refit:** G_iqp (3 restarts) and G_maxent3 come from `results/step9`. At n = 14,
  the 10-restart G_iqp from `results/step10` is used only in the exploratory section.
- **Bitflip fit (new, `src/step11/bitflip.py`):**
  - generators `masks_up_to(n, 3)`;
  - loss Σ_a (f_a − f̂_a)² over the same order-≤3 ops;
  - the analytic gradient;
  - scipy L-BFGS-B with `LBFGS_OPTS` from `src/step1/models/iqp.py`;
  - 10 restarts with inits `replay_inits(n_params, seed, 10)`, which are the same vectors G used.
    The **primary** fit is the best of restarts 0–2, by lowest training residual. That matches
    G's 3-restart budget. Best of 10 is exploratory.
- **Completion metric:** the full bitflip distribution p = FWHT(f)/2^n, with f over all 2^n masks
  from the product formula. G is computed by `src/step1/metrics.completion_gap`, unchanged.
  - Definitions: R_B = G_bitflip / G_maxent3 and Q = G_iqp / G_bitflip. Q < 1 means coherence
    helps.
- **Threads:** 1 BLAS thread per worker, up to 12 workers (memory: the n = 16 parity matrix is
  about 365 MB).
- `src/step1..10` are never edited.

## 3. Frozen hypotheses

Sign tests at ≥ 15/20 (one-sided p ≈ 0.021), the same threshold as steps 9–10.

| ID | Statement | Kind |
|---|---|---|
| C1 | n = 16: G_iqp < G_bitflip (Q < 1) in at least 15 of 20 seeds | **primary**: coherence helps where the IQP wins |
| C2 | n = 16: G_bitflip < G_maxent3 (R_B < 1) in at least 15 of 20 seeds | the classical twin also beats MaxEnt(3) |
| C3 | n = 14: Q < 1 in at least 15 of 20 seeds | secondary |
| C4 | n = 14: R_B < 1 in at least 15 of 20 seeds | secondary |

**Reading rules (n = 16), fixed now:**
- **C1 PASS, C2 FAIL:** the advantage over MaxEnt(3) needs coherence. The decohered twin does not
  have it. This is the strongest outcome for the quantum reading.
- **C1 PASS, C2 PASS:** structure alone already beats MaxEnt(3), and coherence adds to it. Report
  both medians. The quantum share is the gap between them.
- **C1 FAIL, C2 PASS:** the advantage is reproduced by a classical, efficiently samplable model
  with the same generators. Steps 5–10 must then be read as "IQP-shaped inductive bias", not as a
  quantum effect. This is a negative result for the quantum claim and is reported as such.
- **C1 FAIL, C2 FAIL:** neither direction is supported. The control is uninformative here.

**Exploratory, reported but not tested:**
- Training residuals of the bitflip fit against G's, and the count above 1e-2.
- Q and R_B restricted to seeds where both fits have a residual ≤ 1e-2, to separate completion
  from training misfit.
- Best-of-10 bitflip, and at n = 14 against step 10's 10-restart G_iqp.
- Spearman correlation of R and R_B across seeds.

## 4. Artifacts and acceptance

- Results:
  - `results/step11/n_<n>/seed_<s>/metrics.json`, holding the bitflip restart residuals, G, nit
    and messages, the best-3 and best-10 indices, G_bitflip, R_B, Q, step 9's G_iqp,
    G_maxent3 and R, and `target_match`;
  - `results/step11/table.csv`, `verdicts.json` and `SUMMARY.md`;
  - `figures/step11/G_iqp_vs_bitflip` (png + pdf): log G_bitflip on x and log G_iqp on y, per
    n, with the diagonal. Prediction under C1: n = 16 points mostly below the diagonal.
- The SUMMARY opens with: "Step 11 was designed after step 10; the bitflip model is a classical,
  decohered twin of G with the same generators, inits and optimizer; the targets are coherent
  IQPs, so this tests coherence on IQP-generated data only; n ≤ 16 proxies are not hardness
  evidence."
- `--verify` checks:
  - the spec is committed and unchanged;
  - `src/step1..10` are unchanged since a7dbff9;
  - 40 metrics files exist, with exact σ, 10 restarts and `target_match` true;
  - every bitflip p has a minimum ≥ −1e-12 and sums to 1 within 1e-10;
  - the SUMMARY sentence and C1–C4 are marked;
  - the figure exists;
  - `tests/test_step11.py` passes.
- **Tests, written before the grid:**
  - (T1) at n = 6 with 8 random generators, the FWHT distribution equals explicit enumeration of
    all 2^8 flip patterns to 1e-12;
  - (T2) FWHT(p) equals the product formula on every mask at n = 8;
  - (T3) the analytic gradient matches central finite differences, relative error < 1e-6, at
    n = 8 with every weight-≤3 generator;
  - (T4) at θ = π/4, where cos 2θ = 0, the exclusive-product gradient is finite and matches finite
    differences;
  - (T5) with θ → θ/2, the bitflip–IQP moment difference shrinks by at least 12×. This checks
    that the two agree to second order.

## 5. Budget

The bitflip loss touches only the training ops, an ops × params matrix of about 700 × 700. One
restart should take seconds to a minute. The full distribution is built once per restart (one
65536 × 696 matmul at n = 16).
- **Timing gate:** one n = 16 seed is timed first and projected to 40 seeds on 12 workers.
- **Stop-loss:** 2 h. **Named lever if over:** drop the n = 14 half (C3 and C4) and keep n = 16
  (C1 and C2). Restarts and seeds are never cut.
