# Mid-term report: completing order-4–6 moments with a generic IQP versus MaxEnt(3) (steps 1–14)

Research note, 2026-11-11. It draws on the findings notes for steps 1–14, the step-8 diagnostic,
the literature note of 2026-11-10 and the README table. Specs were read only to check what a
hypothesis said. No new number is computed here. Every number is quoted from a note.

## Abstract

We fit a generic weight-≤3 IQP circuit model to the order-≤3 parity moments of a target
distribution over n bits. We ask whether it completes the order-4–6 moments better than
MaxEnt(3), the maximum-entropy model with the same constraints. After fourteen pre-registered
steps, the claim reads: "At n = 16, with N = 1e5 samples, a training-only residual gate picks the
generic IQP over MaxEnt(3) on IQP-like data and wins 11 of 14 decided seeds (p = 0.03). It never
picks the IQP on non-IQP data (0/40). At N = 1e4 the advantage is gone." Without a gate, the
advantage exists only on IQP-like targets, and it needs coherence. On two non-IQP families the
IQP loses to MaxEnt(3) on every seed. All targets are synthetic, and n ≤ 16. The n ≤ 16 proxies
are not hardness evidence.

## Update after steps 15–16 (added 2026-11-11)

This box supersedes the claim wording in the Abstract and section 3. It also supersedes the
split-sample and shot-threshold bullets of section 4, and the recommendation of section 6. The
rest of the report is unchanged.

- **Step 15 (pilot only, development seeds; `notes/2026-11-11_step15_split_pilot.md`).** The
  split-sample gate is unbiased, but it has no power at τ = 1e-2. It does not rank R within
  `iqp4`, and its families overlap at N = 1e4. It was dropped. At N = 1e4 the bottleneck is the
  advantage itself, not the gate.
- **Step 16 (frozen, fresh seeds 70–89; `notes/2026-11-11_step16_threshold_findings.md`).** The
  step 14 gate, unchanged, was run at N = 3e4.
  - T1 PASS: 19 picked, 17 wins, 2 losses, p = 3.6e-4.
  - T2 PASS: 0/40 picked out of family.
  - The pooled geometric mean R_gate is 0.895, against an oracle 0.893.
  - Caveat: the always-IQP R is not monotone in N across seed sets, nor on the same pilot seeds.
    The threshold is a soft transition.

**Updated claim:**

> At n = 16, a training-only noise-corrected residual gate picks the generic IQP over MaxEnt(3) on
> IQP-like data and wins at N = 3e4 (17/2, p = 4e-4) and N = 1e5 (11/3, p = 0.03). It never picks
> the IQP on non-IQP data: 0/120 across N ∈ {1e4, 3e4, 1e5}. At N = 1e4 the advantage itself is
> gone (12/8, not significant).

**Updated recommendation: rank 1, the real-data probe.** The shot budget is now known: about
N ≥ 3e4 at n = 16. The gate works at that N. That removes the blocker that made rank 2 the
recommendation. A real binary dataset with n ≤ 16 features and ≥ 3e4 rows can now be read through
the frozen gate.

## Update after steps 17–21 (added 2026-11-11)

This box supersedes the claim wording of the steps 15–16 box. That box's "never picks the IQP on non-IQP
data" holds only for the synthetic families and for MNIST. Every number below is quoted from the step
notes.

- **Step 17 (frozen; MNIST-16; `notes/2026-11-11_step17_mnist16_findings.md`).** U1 and U2 PASS.
  - The IQP cannot fit the order-≤3 moments and loses about 4×.
  - The gate falls back to MaxEnt(3) on 20/20 splits.
  - The gate is safe here because the misfit is visible at low order.
- **Step 18 (identifiability demo; `notes/2026-11-11_step18_identifiability.md`).**
  - q_λ = λp + (1−λ)MaxEnt3(p) has the same order-≤3 moments for every λ.
  - The gate picks G at every λ, but G loses below λ* = 0.60–0.74.
  - So no order-≤3 gate can be safe in general.
- **Step 19 (frozen; Google surface-code detection events, 7 hardware runs;
  `notes/2026-11-11_step19_qec_findings.md`).**
  - V1 FAIL: the gate picked the IQP on 7/7 runs and lost on 5 (median R 2.87).
  - V2 FAIL.
  - An order-4 check on the training rows flagged 0/7.
- **Step 20 (frozen; held-out order-4 validation gate, 18 fresh instances;
  `notes/2026-11-11_step20_val_gate_findings.md`).**
  - W1 FAIL: 2 losses, both on QEC.
  - W2 PASS: 2 losses against 7 for the step 14 gate.
  - W3 PASS: kept 6/9 wins.
  - On iqp4 the new gate had 0 losses on 14 instances (test plus pilot). On QEC its decisions matched the
    outcome at chance (4/8).
- **Step 21 (diagnostic; bootstrap CIs, 16 QEC runs × 2 splits;
  `notes/2026-11-11_step21_qec_resolvability.md`).**
  - 9/16 runs are unresolved, and the sign agreed across splits on only 8/16.
  - IQP wins: 0/32 resolved.
  - Losses: 12/32 resolved, and 3 runs lose in both splits.
  - The validation CI excludes 0 in 1/32 cells.

**Updated claim:**

> At n = 16, on IQP-like synthetic data, the generic IQP completes order-4–6 moments better than MaxEnt(3)
> at N ≥ 3e4. A training-only gate picks it there (17/2 at 3e4; 11/3 at 1e5). Adding a held-out order-4
> validation check removed every loss on 14 IQP-family instances while keeping most wins. The order-≤3
> gate alone is **not** safe in general (step 18). On real data it is safe only when the IQP visibly
> misfits at low order (MNIST, 0/20 picks). On real parity-structured data (QEC syndromes, 5e4 shots) it
> picks the IQP every time. There, the IQP shows no resolved advantage (0/32) and loses reproducibly on
> 3 of 16 runs.

**Reporting rule.** Real-data outcomes are reported as resolved / unresolved counts with bootstrap CIs over
at least two splits. Win/loss counts of a single point R are not used.

**Updated recommendation.**
1. Write up. The synthetic advantage, the identifiability limit and the QEC negative result form a
   complete, honest story.
2. Optional: a larger real parity-structured dataset, ≥ 5e5 shots per run, so that validation and test
   can resolve differences of about 3e-5.

## 1. Question and setup

### 1.1 The question

Take a target p over n bits. Give two models the same order-≤3 parity moments, exact (N = ∞) or
estimated from N samples. Which one predicts the order-4–6 parity moments better?

### 1.2 Models

| Model | What it is | Notes |
|---|---|---|
| G, the generic IQP | A weight-≤3 IQP with one angle per generator: 298 generators at n = 12, 469 at n = 14, 696 at n = 16 | No oracle layout. 3 restarts, lowest training residual selected (10 restarts in step 10). |
| O, the oracle IQP | An IQP on the target's true layout | Steps 2–3 only. |
| MaxEnt(3) | The maximum-entropy model with the same order-≤3 constraints | Ridge 1e-8. It always matches the order-≤3 moments it is given. |
| Bitflip twin | A decohered, classical twin of G: same generators, inits and optimizer; ⟨Z_a⟩ = ∏ cos 2θ_g | Steps 11–12. Taken from Xanadu's control (literature note). |
| Residual gate | Use G if its training residual is ≤ τ = 1e-2, otherwise MaxEnt(3) | Steps 13–14. At finite N the residual is noise-corrected: r_N − Σ(1 − f̂²)/N ≤ τ. |

### 1.3 Target families

| Family | Definition | Role |
|---|---|---|
| `iqp` | Sparse IQP: n one-body, 18 pairs, 8 triples (38 generators at n = 12); θ = σ·z, z ~ N(0, 1) | Well specified: inside G's family |
| `iqp4` | `iqp` plus 6 weight-4 generators, all angles ∝ σ | Misspecified but IQP-like; the main target from step 4 on |
| `iqp4f` | `iqp4` with the weight-4 angles fixed at τ = 0.2 | Step 5 control |
| `mix` | Product-Bernoulli mixture, K = 48, δ = 0.99 | Step 4 non-IQP target |
| `maxent_proj` | MaxEnt3 of the target | Paired kill control (steps 3–4) |
| `lcm` | Latent-class mixture, K = 4 | Step 12–14 non-IQP target |
| `ising4` | Boltzmann model with weight-4 terms | Step 12–14 non-IQP target |

From step 7 on, σ is set by peakedness level. Level B matches n = 12's collision ratio at
σ = 0.175 (about 284). At level B, n = 14 uses σ = 0.213 and n = 16 uses σ = 0.251.

### 1.4 Metrics

- **G_model:** the mean squared parity error at orders 4–6, against the exact target.
- **R = G_iqp / G_maxent3.** R < 1 means the IQP completes better. Q = G_iqp / G_bitflip and
  R_B = G_bitflip / G_maxent3 are the bitflip analogues.
- **D3 = KL(p ‖ MaxEnt3(p)):** the completion room, that is, how much MaxEnt(3) has to miss.
- **Collision ratio:** the target's collision probability relative to uniform. It measures
  peakedness.
- **Training residual:** G's misfit to the order-≤3 training moments. It needs no target
  information.

### 1.5 Pre-registration practice

- Each step has a spec in `specs/`, with hypotheses frozen at a commit before the grid runs. The
  notes for steps 3–10 label each spec as designed after the previous step's results.
- Amendments in steps 4, 5 and 9 were committed before the grid ran (step 4: before any
  completion quantity was computed).
- Fresh seeds: 10–29 from step 9, 30–49 in step 13, 50–69 in step 14. Seeds 0–4 were used for
  development and calibration.
- Acceptance is a command that must exit 0: `check.sh --stage …` for steps 4–7, and
  `python -m src.stepK.run --verify` from step 9 on.
- Exceptions are recorded, not hidden:
  - Step 7 ran with the harness hooks removed, at the user's request. `check.sh` was run after.
  - Steps 9 and 10 had no `BUDGET_OK` gate.
  - Step 9's `--verify` exits 1, on its reproduction item only. It was not loosened.
- Statistics changed once. Steps 4–7 used "the whole IQR over 5 seeds lies below 1". From step 9
  on, the primary test is a seed count over 20 seeds with a sign test.

## 2. The path of evidence

Verdicts are the frozen ones. "Expl." marks exploratory results that were not frozen.

### 2.1 Arc (a): existence at n = 12 (steps 1–5)

| Step | Question | Frozen verdicts | What it changed |
|---|---|---|---|
| 1 | Can G (298 generators) recover a σ = 0.4 IQP from exact order-≤3 moments? | P1 FAIL (0/50 restarts reach the truth). Amendment 1: P1′, P6′ FAIL (0/5 seeds) | Exact recovery is the wrong criterion. Generic generator sets are not identifiable from order-≤3 moments. |
| 2 | With the oracle layout at σ = 0.05, does the fit reach 1e-10? | H1 FAIL (0/5; best residual 1e-6 to 9e-6) | Wrong-sign basins (7–8 of 18 pair signs). Expl.: the completion survives them; the best wrong-sign fit gives R = 0.1–0.6 on 4/5 seeds. |
| 3 | How does R vary with σ (N = ∞, `iqp`)? | K1, K2 PASS but vacuous; C1 PASS; M1, M2, M3 FAIL | Expl.: R_G = 0.15–0.18 at σ = 0.05–0.2, about 5× in the IQP's favour. G fails to train at σ ≥ 0.3 (R 1.41–2.2). |
| 4 | Does R_G < 1 survive misspecification and finite N? | K, R1, P1, P2, F1, F2: all six PASS | `iqp4` at σ = 0.2: R = 0.577 (N = ∞), 0.546 (N = 1e5). `mix`: R = 5.02. Finite N needs about N ≥ 1e4 at n = 12. Expl.: `iqp4` at σ = 0.1 reverses (R = 7.93). |
| 5 | Where does the `iqp4` advantage reverse in σ? | Q0, Q1, Q2, Q4 PASS; Q3, Q5 FAIL | σ\* = 0.160, as predicted. The window is narrow: R < 1 only at σ = 0.175–0.2. Q3: σ = 0.25 undecided (0.891). Q5: the finite-N shift went the wrong way, by less than the grid step. |

Points to carry forward:
- Steps 1 and 2 both ended by their kill rules. Steps 3 and later are designed after seeing those
  diagnostics.
- Step 3's paired control was vacuous at N = ∞: on `maxent_proj` the truth is MaxEnt(3). It
  became a real kill test only at finite N in step 4 (R ≥ 1 in all 6 cells, 1.22 to 78).
- Step 4's `mix` comparison was made at the σ = 0.1 room level (D3 = 0.0385), with no fitted
  mixture baseline.
- Step 5's mechanism: G_iqp stays within 2.3× across σ, while G_maxent3 grows 22× from σ = 0.1
  to 0.2. The two cross near σ\* = 0.16. Above 0.2, G_maxent3 levels off and R climbs back.

### 2.2 Arc (b): scaling and peakedness (steps 6–10)

| Step | Question | Frozen verdicts | What it changed |
|---|---|---|---|
| 6 | Does the n = 12 window survive n = 14, 16 at fixed σ and fixed layout counts? | S1, S2, S3 FAIL; S4 PASS | At σ = 0.2: R = 0.889 (n = 14), 1.38 (n = 16). n = 16 has no window at σ ≤ 0.2; σ = 0.25 was cut. The collision ratio grows 3.5–3.7× per +2 bits. |
| 7 | At matched peakedness (collision ratio), does R < 1 return? | C1, C2, C3 FAIL; C4 PASS | n = 14: R < 1 at all three levels. n = 16: medians 0.65–0.83 but undecided; seeds 1 and 2 lose at every level. Most of step 6's collapse was peakedness. |
| 8 | Why do seeds 1 and 2 lose at n = 16? | None (exploratory, no new fits) | Two-mechanism story: seed 1 has a strong weight-4 part (r4 = 0.415); seed 2 has the least room (lowest D3). log R ~ D3 + r4 gives R² = 0.83 at n = 16. Advice: use more seeds. |
| 9 | On 20 fresh seeds (10–29) at level B, does the IQP usually win? | H1, H5, H6 PASS; H2, H3, H4, H7 FAIL | n = 16: 16/20 wins (p ≈ 0.006), median R = 0.637 [0.543, 0.889]. n = 14: 10/20. Step 8's model fails out of sample (ρ = 0.35). |
| 10 | Do 10 restarts rescue the n = 14 losers? | K1, K2, K3 FAIL; K4 PASS | 11/20 win; 1/10 losers rescued. The high residuals are a floor: 10 restarts land within 1.18–1.57× of the lowest. Expl.: residual ≤ 1e-2 → 10 of 13 win; > 1e-2 → 1 of 7. |

Points to carry forward:
- Step 7's frozen reading rule said "the advantage shrinks with n even at matched peakedness".
  The note itself flagged that this overstates the failure: every n = 16 median was below 1, and
  the cells failed as undecided, not as R ≥ 1.
- Step 7's C3 also shows that the crossing is not fixed in collision coordinates. At matched
  collision ratio, D3 grows with n (0.216, 0.247, 0.304 at level B for n = 12, 14, 16).
- Step 8's explanation did not survive. In step 9, H3 fails (b(D3) = −2.49 [−4.43, +0.007],
  c(r4) = 1.49 [−0.33, 4.14]), H4 fails, and H7 fails (ρ = 0.35 against ≥ 0.5). Only the D3
  direction survives, marginally.[^1]
- Step 7's "undecided at n = 16" was a 5-seed artifact, by step 9's frozen reading.[^2]
- Step 9 found that per-instance R reproduces only to about 1–10% across BLAS thread counts.
  At n = 16 the reproduction instance differed from step 7 by 6.0e-3 in R. 16/20 seeds still have
  R < 1 − 0.006, and 15/20 have R < 0.9, so H1 holds under that drift.
- Step 9's fresh n = 14 seeds missed the intended peakedness: median collision ratio 479 against
  the 284 target, median D3 0.24. The fresh n = 16 seeds were near target (319, D3 0.33).
- Step 9 called the n = 14 losses "under-training". Step 10 showed they are moment misfits on a
  floor, not a search failure.[^3] The oracle restart choice also gives only 11/20, so restart
  selection cannot help at n = 14.

### 2.3 Arc (c): what the advantage needs (steps 11–12)

| Step | Question | Frozen verdicts | What it changed |
|---|---|---|---|
| 11 | Does a decohered twin with the same generators also beat MaxEnt(3)? (step 9 targets) | C1, C3 PASS; C2, C4 FAIL | IQP beats bitflip 20/20 at both n (median Q = 0.39 at n = 16, 0.32 at n = 14). Bitflip beats MaxEnt(3) on 3/20 and 2/20. Frozen reading: the advantage needs coherence. |
| 12 | On non-IQP targets (`lcm`, `ising4`), does the IQP still win? | E1, E3, E5, E7 FAIL (0/20 each); E2, E4, E6, E8 PASS | Median R = 25 (lcm, 16), 2.05 (ising4, 16), 160 (lcm, 14), 16.5 (ising4, 14). The claim is restricted to IQP-like data. |

Points to carry forward:
- Step 11's coherence result is a statement about **fitting**, not completion at matched fit.
  The bitflip model's training residual is above 1e-2 in 40/40 seeds (median about 0.1). No seed
  has both residuals ≤ 1e-2. The targets are coherent IQPs, so family match favours the coherent
  model by construction.
- Step 12 has the same mechanism. The IQP misfits the order-≤3 training moments on every seed
  (median residuals 0.20 to 1.57). R there mostly measures the failure to represent the low-order
  data.
- Expl. in step 12: the residual gate at τ = 1e-2 falls back to MaxEnt(3) on all 80 instances,
  0 wins and 0 losses. This was not frozen there; it became F2 and F4 in step 13.
- Step 12 caveat: `ising4` at n = 16 came out less peaked on the test seeds (median collision
  ratio 42) than on the calibration seeds (319). That cell is not peakedness-matched in practice.

### 2.4 Arc (d): a deployable estimator (steps 13–14)

| Step | Question | Frozen verdicts | What it changed |
|---|---|---|---|
| 13 | Does the residual gate (τ = 1e-2, exact moments) win in family and stay safe out of family, on fresh seeds 30–49? | F1, F2, F4 PASS; F3 FAIL | n = 16 `iqp4`: picks IQP 15/20, 14 wins, 1 loss, 5 ties, p = 0.0005. Out of family: 0/40 picked at each n. n = 14: 9 wins, 2 losses, below the ≥ 10 floor. |
| 14 | Does the gate survive finite N (noise-corrected, n = 16, fresh seeds 50–69)? | S1, S2, S4 PASS; S3 FAIL | N = 1e5: 14 picked, 11 wins, 3 losses, p = 0.029. N = 1e4: 20 picked, 12 wins, 8 losses, p = 0.25. Out of family: 0/80 picked. |

Points to carry forward:
- Step 13 pooled 60 instances per n (expl.). Geometric mean R_gate is 0.867 at n = 16, against
  an oracle min(R, 1) of 0.854 and always-IQP 3.43. At n = 14 the figures are 0.93, 0.904 and
  18.1.
- Step 13's residual separation is wide. `iqp4` residual medians are 0.0057 (n = 16) and 0.0060
  (n = 14). `lcm` and `ising4` never go below about 0.19.
- Step 13's τ sensitivity at n = 16: τ = 3e-3 gives 6/6 wins; τ = 3e-2 gives 14 wins and
  3 losses.
- Step 14: noise erodes the underlying advantage before any gating. The always-IQP median R on
  `iqp4` is 0.66 at N = ∞ (step 13 seeds), 0.93 at N = 1e5 and 0.99 at N = 1e4.
- Step 14 at N = 1e4: the noise floor (0.066) is 3–4× G's raw residual (0.015). The excess is
  negative on every `iqp4` seed, so the gate picks all 20. G fits the noise (r_true ≈ 0.058). The
  uncorrected gate is no better (6 picked, 4 wins, 2 losses).
- Step 14 safety margin: at τ = 3e-2 a single `lcm` instance would be picked at N = 1e4, and it
  loses.

### 2.5 Verdict tally by step

| Step | PASS | FAIL | Comment |
|---|---|---|---|
| 1–2 | 0 | P1, P1′, P6′, H1 | Ended by kill rules |
| 3 | K1, K2 (vacuous), C1 | M1, M2, M3 | Main result exploratory |
| 4 | K, R1, P1, P2, F1, F2 | none | |
| 5 | Q0, Q1, Q2, Q4 | Q3, Q5 | Q4 low confidence |
| 6 | S4 | S1, S2, S3 | Confounded by peakedness |
| 7 | C4 | C1, C2, C3 | Frozen reading overstated, per the note |
| 8 | n/a | n/a | Exploratory; refuted in step 9 |
| 9 | H1, H5, H6 | H2, H3, H4, H7 | `--verify` exits 1 on reproduction |
| 10 | K4 | K1, K2, K3 | |
| 11 | C1, C3 | C2, C4 | |
| 12 | E2, E4, E6, E8 | E1, E3, E5, E7 | E1 was the primary |
| 13 | F1, F2, F4 | F3 | F3 FAIL expected by its spec |
| 14 | S1, S2, S4 | S3 | |

## 3. The current claim and its exact support

The claim, as step 14's note section 4 words it:

> At n = 16, with N = 1e5 samples, a training-only residual gate picks the generic IQP over
> MaxEnt(3) on IQP-like data and wins 11 of 14 decided seeds (p = 0.03). It never picks the IQP on
> non-IQP data (0/40). At N = 1e4 the advantage is gone.

The pre-registered PASSes it rests on:

| Support | Step, ID | Seeds | Count | Frozen threshold |
|---|---|---|---|---|
| Finite-N gain | 14, S1 (primary) | 50–69 | `iqp4`, N = 1e5: 14 picked, 11 wins, 3 losses, p = 0.029 | wins ≥ 10/20 and p ≤ 0.05 |
| Finite-N safety | 14, S2 (primary) | 50–69 | `lcm` + `ising4`, N = 1e5: 0/40 picked | losses ≤ 2/40 |
| Finite-N safety, lower N | 14, S4 | 50–69 | N = 1e4: 0/40 picked | losses ≤ 2/40 |
| Exact-moment gain | 13, F1 (primary) | 30–49 | `iqp4`, n = 16: 15 picked, 14 wins, 1 loss, p = 0.0005 | wins ≥ 10/20 and p ≤ 0.05 |
| Exact-moment safety | 13, F2 (primary) | 30–49 | n = 16: 0/40 picked | losses ≤ 2/40 |
| Exact-moment safety, n = 14 | 13, F4 | 30–49 | 0/40 picked | losses ≤ 2/40 |
| Ungated IQP advantage at n = 16 | 9, H1 | 10–29 | 16/20 R < 1, p ≈ 0.006 | ≥ 15/20 |
| Same, IQR rule | 9, H5 | 10–29 | median R = 0.637 [0.543, 0.889] | whole IQR < 1 |
| Not under-training | 9, H6 | 10–29 | median residual 2.7e-3; 14/16 well-trained seeds win | median ≤ 1e-2, H1 unchanged |
| Coherence needed (on IQP targets) | 11, C1 and C3 | 10–29 | Q < 1 in 20/20 at n = 16 and at n = 14 | ≥ 15/20 |
| IQP beats bitflip on non-IQP families too | 12, E2, E4, E6, E8 | 10–29 | Q < 1 in 20/20, 20/20, 20/20, 19/20 | ≥ 15/20 |

The FAILs that bound it:
- **S3** (N = 1e4): 12 wins, 8 losses, p = 0.25. This is the "advantage is gone" clause.
- **F3** (n = 14, exact): 9 wins, 2 losses. The claim is stated at n = 16 only.
- **E1, E3, E5, E7**: 0/20 in every non-IQP cell. This is why the claim says "IQP-like data".
- **C2, C4**: the bitflip twin does not beat MaxEnt(3). This is why coherence enters the
  reading.

## 4. What is NOT shown

- **Hardness.** Every result is at n ≤ 16, simulated classically. The proxies (collision ratio,
  distance from Clifford angles) are not hardness evidence. The winning regime is strongly
  peaked: at n = 12 the window sits at collision ratio about 130–1800 × uniform. Step 3 calls this
  the Herbst trade-off (trainability versus anticoncentration), measured on the completion task.
  Where targets approach anticoncentration (σ ≥ 0.4 in step 3, ratio about 2), G does not train.
- **Real data.** All targets are synthetic. Whether any real dataset is IQP-like at orders 4–6 is
  the open practical question since step 4. Real data was deferred as "a deep pit" (step 10).
- **n > 16.** Only n = 12, 14, 16 were run. Two sizes per arc are not a trend (step 13). The gain
  does not grow cleanly with n: n = 14 is weaker than n = 16 in steps 9, 10 and 13. Step 14
  notes that the noise floor scales as about n³/(6N), so the shot requirement grows roughly as n³.
- **The fitted latent-class baseline.** MaxEnt(3) is the information-matched baseline, not the
  strongest classical one. A fitted latent-class model would be well specified on `mix` and `lcm`.
  It exists only as a stub (`fit_mixture_moments`). It would make the non-IQP losses more
  decisive. It could also raise the in-family bar, which is untested.
- **The split-sample gate.** At N = 1e4, G's 696 parameters equal the number of moments, so G
  absorbs noise and the noise-corrected gate goes blind. A split-sample gate would avoid this. It
  is a stub and was not run.
- **The shot threshold.** Only N = 1e4 and 1e5 were run at n = 16. The threshold lies between
  them and is not located. At n = 12, step 4 put the requirement at about N ≥ 1e4 for ungated R.
- **Only two non-IQP families.** `lcm` and `ising4` (plus step 4's `mix` at n = 12). The safety
  result (0/40, 0/80) would break on a target the IQP fits at low order but completes badly. No
  such case appeared in 80 + 80 instances (steps 12–13), but none was constructed either.
  Parity-structured data, which might favour the IQP, is also untested.
- **Coherence at matched fit.** Step 11 shows coherence is needed to fit IQP targets. It does not
  separately show that coherence improves completion when both models fit.
- **Per-instance R.** It is reproducible only to about 1–10% across BLAS thread counts (step 9).
  Single values near 1 should not be read as signs. The claim rests on counts over seeds.
- **Robustness in σ.** At n = 12 the misspecified window is narrow (σ = 0.175–0.2). From step 7 on,
  σ is set per n by peakedness level, and the gated claim is tested at level B only.

## 5. Positioning against the literature

Source: the literature note of 2026-11-10 only. Its scrapes were truncated before the papers'
discussion sections.

| Paper | Relation to this project |
|---|---|
| Baumann et al., arXiv 2605.10258 | **Closest.** A weight-2 ring IQP fitted to parity moments, against a "MaxEnt-parity" model on the same moments. Their gap is large (mean KL 0.385 against 1.804; lowest in 190/200). Their MaxEnt has 512 parameters, no order cutoff, and is fitted to 200-sample moments. No restarts, residuals, misspecified targets or held-out completion are reported. |
| Recio-Armengol, Ahmed, Bowles, arXiv 2503.02934 | IQP trained with MMD, which is a bandwidth-weighted moment-matching loss. No baseline gets the same moments. They concede their classical baselines are under-tuned. Source of the bitflip control used in steps 11–12. |
| Shen, Pielawa, Dunjko, Wang, arXiv 2602.11042 | Small-variance Gaussian init gives polynomial gradient variance. We use small N(0, σ²) inits, so barren plateaus do not explain step 10's floor. |
| Lerch et al., arXiv 2603.14576 | Data-dependent init gives provable gradients. A possible check of whether step 10's floor is expressivity. |

What the note concludes:
- **The niche is not taken.** No work found combines an IQP fitted to exact order-≤k moments, the
  information-matched MaxEnt(k) baseline, held-out order-k+1… completion, misspecified targets,
  and reported residuals, restarts and per-instance statistics.
- **"Information-matched baseline" is the main methodological point.** Both the Xanadu and the
  LMU groups say their baselines are not that.
- **Our margin is far smaller than Baumann et al.'s** (at n = 16: 16/20 wins, median R ≈ 0.64,
  against their about 4.7× in KL). Our untested hypothesis: much of their gap is finite-sample
  overfitting by an uncut 512-parameter MaxEnt.
- **The residual gate appears new.** No prior work proposing it was found.[^4]

## 6. Open questions and candidate next steps

Ranked by how much the outcome would change the claim. Costs are not ranked here.

| Rank | Step | What it would decide | How the claim could change |
|---|---|---|---|
| 1 | **Real-data probe**: D3 and an order-4–6 completion check on one small real binary dataset | Whether real data ever sit in the IQP-like regime | From "synthetic only" to "practical", or to "the regime is not reached by real data" |
| 2 | **Split-sample gate, and N between 1e4 and 1e5** at n = 16 | Whether the gate can work below 1e5 shots, and where the threshold is | Moves the "N = 1e5" and "gone at 1e4" clauses; sets the shot budget any real-data test needs |
| 3 | **An adversarial non-IQP family**: one the IQP fits at low order but completes badly (or parity-structured data) | Whether the safety half (0/40) is general | Could break the "never picks the IQP on non-IQP data" clause |
| 4 | **n > 16** at level B, with per-seed σ matching | Whether the gated gain holds, grows or shrinks with n | Could lift or bound the "n = 16" clause; tests the n³ shot scaling |
| 5 | **Baumann et al. reproduction** with an order-cut or regularised MaxEnt(k) | Whether their large gap is MaxEnt overfitting | Changes positioning, not our claim |
| 6 | **Fitted latent-class baseline** on `lcm`, `mix` and `iqp4` | The real classical bar | Non-IQP losses already decide the out-of-family half; matters in family only if it beats MaxEnt(3) on `iqp4` |
| 7 | **Data-dependent init** (Lerch et al. style) on the n = 14 floor seeds | Whether the step-10 floor is expressivity | Explains F3; does not change the n = 16 claim |

**Recommended: rank 2, the split-sample gate between N = 1e4 and 1e5.** Any real dataset arrives
at finite N, and step 14 shows the current gate goes blind at 1e4 shots, so the real-data probe
(rank 1) cannot be read until the gate works at realistic N. The stub exists, and step 14 names it
as the natural fix.

## Footnotes

[^1]: Step 8 (2026-11-09) proposed a two-mechanism model (strong weight-4 part, low D3) with
R² = 0.83 at n = 16. Step 9 (later) refuted it out of sample (H3, H4, H7 FAIL). This report uses
step 9.

[^2]: Step 7 read its n = 16 cells as "the advantage shrinks with n even at matched peakedness".
Step 9 (later), on 20 fresh seeds, calls step 7's "undecided" a 5-seed artifact (H1 PASS, 16/20).
This report uses step 9.

[^3]: Step 9 labelled the n = 14 high-residual losers "under-training". Step 10 (later) showed that
10 restarts converge within 1.18–1.57× of the same residual, and called them moment misfits. This
report uses step 10.

[^4]: The literature note (2026-11-10) lists the bitflip control as "a cheap control we lack" and
the residual gate as "still exploratory". Steps 11 and 13 (later) ran both as frozen tests. This
report uses the later status.
