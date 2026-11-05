# Step 1: completion-gap pipeline on synthetic targets (qgen-practical)

## Project

Build the smallest pipeline that can measure a **completion gap**:
- fit an IQP model and an order-3 max-ent model to the **same** order-≤3 parity statistics;
- then measure which one predicts the order-4…6 parity structure of the target better.

Run it on three synthetic targets: one where a gap should exist, and two where it must not.

The deliverable is **a small, tested research module plus a 60-run result table and one
summary**. It is **not**:
- evidence of quantum advantage (n = 12 is trivially simulable; the targets are built to suit
  the IQP);
- a new trainer for real data;
- a repeat of qgen-iqp-A follow-up 5 (noisy Hamming), which is being done separately.

Architecture test: someone else must be able to add a third model, for example an
autoregressive one, by writing one file in `src/step1/models/`, without touching
`metrics.py` or `run.py`.

Background and why this matters: `notes/2026-11-05_iqp-from-limits.md`, sections 3 to 6.
Read it once. Do not re-derive it.

## Stack (do not substitute)

- Python 3.12 (the system `python`). Make a venv in `.venv`.
- `numpy`, `scipy`: `scipy.optimize.minimize(method="L-BFGS-B")` for every fit.
- `pytest`, `matplotlib`.
- **No jax, torch, pennylane or iqpopt.** n = 12 is enumerable, and the gradients below are
  hand-derived and tested. A framework would add an install risk and a second phase
  convention for no gain.

Pin versions in `requirements.txt`, and print the resolved versions into every
`metrics.json`.

## Repo layout

```
src/step1/
  bits.py          # all_bitstrings(n), s = 1-2x, fwht(v), subsets_by_order(n, kmax)
  walsh.py         # parity coefficients f_A = E_p[(-1)^{A.x}] of a probability vector, by order
  models/
    iqp.py         # IQPModel: generators of weight <= 3, prob(theta), fit_moments(...)
    maxent.py      # MaxEntModel(k): log-linear on parities of order <= k, fit_moments(...)
  targets.py       # make_target(kind, n, seed) -> exact probability vector + metadata
  metrics.py       # completion_gap(p_model, p_true, levels), tv, clifford_distance, collision_ratio
  run.py           # one config -> results/step1/<target>/<N>/seed_<s>/metrics.json; --all = grid
  figures.py       # figures from metrics.json files only
tests/test_core.py
prereg/step1.md    # predictions, ALREADY WRITTEN AND FROZEN. Do not edit.
```

**Hard architectural rule:** `src/step1/metrics.py` must not import anything from
`src/step1/models/`. It only sees probability vectors and angle arrays. If the metric knows
which model produced a distribution, it can be bent toward one model, and the comparison is
worthless. `scripts/check.sh` greps for this.

## Model specs: read carefully, this section contains the failure modes

**Convention.** This is the same convention as qgen-iqp-A `src/models/iqp.py::phase_np`;
read it, do not import it.
- Generators g ⊆ {0…n−1} with |g| ≤ 3.
- φ(s) = Σ_g θ_g Π_{j∈g} s_j, with s = 1 − 2x.
- Output distribution p(x) = |2^-n Σ_z (−1)^{x·z} e^{iφ(s(z))}|².

**IQP generator set (generic, not the target's).** All 1-, 2- and 3-subsets: at n = 12 that is
12 + 66 + 220 = **298 parameters**. MaxEnt(3) also has **298** (parities of order 1…3). The
two models are therefore matched in parameter count and in the statistics they are fitted to.
This is the fairness condition. Do not give the IQP the target's own sparse generator set:
that would make the comparison an oracle, not a test.

**Fit objective (both models).** L(θ) = Σ_{1≤|A|≤3} (f_A(model) − f̂_A(data))². The data is
either exact target moments (N = inf) or the moments of N samples.

### FAILURE MODE 1: wrong sign or factor in the IQP moments

The closed form is ⟨Z_a⟩ = E_s[cos(2 Σ_{g : |g∩a| odd} θ_g s_g)]. It is easy to get the factor
2 or the odd-overlap rule wrong, and the code then returns plausible but wrong numbers,
**silently**.

Fix: compute moments one way in production (FWHT, below). In `tests/test_core.py`, assert at
n = 6 with random θ that all three of the following agree to 1e-12:
1. FWHT moments;
2. the cos closed form;
3. a brute-force statevector, built from the matrix exp(iΦ) and explicit Hadamards.

### FAILURE MODE 2: an underfit model masquerading as a completion difference

The gap is only meaningful if **both** models fit the order-≤3 moments equally well.

- Symptom: the IQP's training residual is much larger than MaxEnt's. The IQP then "loses" or
  "wins" at high order for a reason that has nothing to do with completion.
- Mechanism: local minima, or flat gradients.

Fix:
- 10 restarts, keeping the lowest training residual;
- log both residuals in `metrics.json`;
- set `gap_valid = false` whenever `train_residual_iqp > max(10 * train_residual_maxent, tau)`,
  with tau = 1e-10 at N = inf and tau = 3 * (expected sampling residual, Σ_A (1 − f_A²)/N) at
  finite N. **Report invalid gaps as invalid; never average them in.**

### FAILURE MODE 3: random initialization (Herbst, arXiv 2512.24801)

A random-angle IQP anticoncentrates, its low-order moments concentrate near 0, and gradients
vanish.

Fix: initialize θ ~ N(0, 0.05²) (a guess; mark it as one in a code comment).
- **Do not** "fix" a stuck fit by switching to uniform-random angles.
- If the IQP still cannot fit the `biased` target at N = inf, stop and show me the residual
  trace.

### Load-bearing detail: compute via FWHT, never via the cos matrix

This matters a lot and is easy to miss. The cos closed form evaluated for all 298 moments is
a 4096 × 298 × 298 computation per loss call, so a grid would take hours. Production code
must do this instead:
1. u = e^{iφ(s)} (length 2^n);
2. amplitude = fwht(u) / 2^n;
3. p = |amplitude|²;
4. f = fwht(p), which gives every parity coefficient at once.

The gradient is the adjoint of these four steps:
- dL/df → dL/dp = fwht(dL/df);
- dL/dp → dL/du via the complex chain rule through |·|² and fwht;
- dL/dφ = Re(conj(i·u) · dL/du) up to the factor your convention gives;
- dL/dθ = S^T dL/dφ, where S is the 2^n × 298 matrix of products Π_{j∈g} s_j.

`test_core.py` must check this gradient against central finite differences: relative error
< 1e-6 at n = 6 and at n = 12. The cos form exists only in the test and in the stub below.

### MaxEnt(k)

- p(x) ∝ exp(Σ_{1≤|A|≤k} λ_A (−1)^{A·x}). Enumerate exactly.
- Minimise the convex dual: log Z(λ) − λ·f̂, plus 1e-8·|λ|² (a guess, purely for numerical
  safety at N = inf).
- Test: from the exact moments of a known Ising distribution, MaxEnt(2) recovers λ to 1e-6.

Leave a stub `iqp_moments_mc(theta, gens, ops, n_samples, rng)`: the Van den Nest Monte Carlo
estimator for n > 20. **Do not implement it beyond raising NotImplementedError**; it is the
hook for step 3.

## Targets (`targets.py`), n = 12 (a guess; chosen so everything is exact)

| kind | construction | role |
|---|---|---|
| `biased` | sparse degree-3 IQP: all 12 one-body terms, 18 random pairs, 8 random triples; θ ~ N(0, 0.4²) | a gap **should** exist (IQP-shaped high-order structure) |
| `ising` | p ∝ exp(Σ h_j s_j + Σ_{random 18 pairs} J s_j s_k), with h, J ~ N(0, 0.4²) | negative control. It lies inside MaxEnt(3), so the IQP **must not** win |
| `random` | the same generator layout as `biased`, but θ ~ Uniform[0, 2π) | Herbst control: anticoncentrated, so neither model should gain much |

Target seed s ∈ {0…4} selects the random layout and angles via `np.random.default_rng(100 + s)`.
Data samples use `default_rng(1000 + s)`. The 0.4 scales are guesses.

## Evaluation protocol: one definition, use it everywhere

- **Gap.** G(model) = mean over levels ℓ ∈ {4, 5, 6} of mean_{|A|=ℓ} (f_A(model) − f_A(true))².
  Compute it against the **exact** target, not test samples.
- **Primary statistic:** R = G(IQP) / G(MaxEnt3). R < 1 means the IQP completes better.
- Also report:
  - G(uniform), as a scale reference;
  - per-level errors;
  - TV to the target;
  - the training residuals and `gap_valid`;
  - `clifford_distance` of the trained IQP angles: distance to (π/4)Z, with max, mean and
    median;
  - the target's collision ratio 2^n Σ p²;
  - the Jacobian rank of the IQP moment map at the solution (via SVD, tolerance 1e-8 times
    the largest singular value).
- **Grid:** 3 targets × N ∈ {inf, 1000, 10000, 100000} × target seeds 0–4 = **60 runs**.
- **Win rule.** "R < 1 at (target, N)" means the 5-seed IQR of R lies entirely below 1, using
  valid gaps only, with at least 4 of 5 valid. Use the median and IQR, not the mean ± std.
- The predictions P1–P5 and the kill rules are in `prereg/step1.md`. It was written before
  any code and is frozen. **SUMMARY.md must mark every P as PASS or FAIL and quote the
  numbers.**

## Artifacts

All figures go to `figures/step1/` as PNG (150 dpi) and PDF, and must be readable without
color.
1. `ratio_vs_N`: median R with an IQR band against N (log x axis; N = inf drawn as a separate
   point), one line per target, and a reference line at R = 1. Prediction: `biased` below,
   `ising` above, `random` near 1.
2. `per_level_error`: for each target at N = 10000, the per-level error for IQP, MaxEnt3 and
   uniform.
3. `clifford_dist`: histogram of the trained-angle distances for `biased`. Prediction P5: the
   median is ≥ 0.02 rad.

Also produce `results/step1/SUMMARY.md` and `results/step1/table.csv` (one row per run).
SUMMARY must contain this sentence verbatim: "This is a pipeline sanity check on synthetic
IQP-shaped targets at n = 12 and is not evidence of advantage on real data."

## Performance and budget

- Time one full fit (both models, 10 restarts) at `biased`, N = 10000, seed 0.
- Write `results/step1/PROJECTION.json` as
  `{"projected_hours": h, "per_fit_seconds": t, "grid": 60}`.
- `run.py --all` must refuse to start unless `BUDGET_OK` exists. Only the user creates that
  file, after seeing the projection. Expected: well under 1 h.
- If the projection is over 1 h, cut in this order: (1) restarts 10 → 5, (2) drop
  N = 100000. Do not cut seeds, and do not cut the `ising` control. It is the test that the
  metric is not biased toward the IQP.

## References

| What to take from it | Reference |
|---|---|
| Why this design exists; requirements R1–R5; kill gates S1–S5 | `notes/2026-11-05_iqp-from-limits.md` |
| Phase convention and parameter layout only (read, do not import or edit) | `C:\Users\tseng\qgen-iqp-A\src\models\iqp.py` (`phase_np`) |
| `lattice_dist` / `clifford_distance` definition, to keep the numbers comparable | `C:\Users\tseng\qgen-iqp-A\src\eval\hardness.py` |
| Why random initialization is wrong; what concentrates | Herbst et al., arXiv 2512.24801 |
| Local statistics determining the parameters (the idea we are testing) | Huang et al., arXiv 2509.09033 |

**Warning about qgen-iqp-A:**
- That repo is running live jobs. **Never write to it, never run code from it, and never
  import from it.** Read the two files above only.
- Its IQP is 1+2-body and trained on exact NLL. Ours is ≤3-body and trained on moments. Take
  the convention, not the trainer.

## Build order (stop for my review at each checkpoint)

Work in a worktree on branch `step1-synthetic`. Commit at each checkpoint.

1. Scaffold, venv, `requirements.txt`; print the versions. **Checkpoint: `bash scripts/check.sh
   --stage 1` cannot pass yet; just commit.**
2. `bits.py`, `walsh.py`, `models/iqp.py`, `models/maxent.py`, and `tests/test_core.py`
   (Failure Mode 1, the gradient finite-difference check, MaxEnt recovery). **Do not proceed
   until these pass.** A wrong moment or gradient here silently invalidates all 60 runs.
   Checkpoint: `--stage 1` passes.
3. `targets.py`, `metrics.py`, `run.py`. Run N = inf, seed 0, for all three targets.
   - Look at `ising` first. If R < 1 there, the metric or the MaxEnt fit is wrong (P3 is a
     kill rule). Stop and tell me.
   - Then look at `biased`. If the IQP cannot reach a training residual of 1e-10, stop and
     show me the residual trace.
   - Checkpoint: `--stage 2` passes.
4. Timing → `PROJECTION.json` → **stop and wait for `BUDGET_OK`**.
5. The full grid, figures, `SUMMARY.md`, `table.csv`. Checkpoint: `--stage 3` passes.

## Working style

- Ask before installing anything outside `requirements.txt`.
- Commit at each checkpoint with a descriptive message. Never push.
- Mark every guessed hyperparameter as a guess in a code comment.
- If something does not converge, show me the diagnostic (residual trace) before changing
  hyperparameters. Change one thing at a time.
- "Done" means `bash scripts/check.sh --stage <current stage>` exits 0. The current stage is
  in `.harness/STAGE`, and only the user changes it.
- Do not edit `scripts/check.sh`, `.claude/`, `.harness/`, `prereg/` or `BUDGET_OK`. If a
  check is wrong, stop and tell me which one and why.
- If a hook or permission rule blocks you, report it. Do not rephrase the command to get
  around the matcher.
- Update `PROGRESS.md` at every checkpoint (done / in progress / next / open questions /
  guesses). Read it first after any context reset.
