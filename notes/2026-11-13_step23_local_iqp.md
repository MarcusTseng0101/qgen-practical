# Step 23 result: a device-connectivity prior makes the IQP win (A1, H1–H4 all PASS 14/14)

Spec: `specs/step23_local_iqp.md` (3cbd3b7, frozen before the run). Code: branch `step18-adversarial` a507a1e. Results:
`results/step23/` (0112bab). `python -m src.step23.run --verify` → ALL PASS (exit 0). The run took 1.5 h of the 5 h
stop-loss, with no errors and no missing jobs.

## Verdicts (fresh seeds 920–933)

| ID | Statement | Wins | Need | Verdict |
|---|---|---|---|---|
| H1 (primary) | local IQP beats MaxEnt(3) at N = 1e4 | 14/14 | 11 | PASS |
| H2 (fairness) | local IQP beats MaxEnt-on-graph at N = 1e4 | 14/14 | 13 | PASS |
| H3 | local IQP beats MaxEnt(3) at N = 1e5 | 14/14 | 11 | PASS |
| H4 (contrast) | local IQP beats the generic 696-gen IQP at N = 1e4 | 14/14 | 11 | PASS |

Sign test p = 6e-5 for each 14/14.

## Reported numbers (no verdict)

| Set | N | median R vs me3 | range | median R vs me_local |
|---|---|---|---|---|
| grid_iqp | 1e4 | 0.35 | 0.23–0.72 | 0.068 |
| grid_iqp | 1e5 | 0.19 | 0.03–0.85 | 0.023 |
| grid_iqp | ∞ | 0.17 | 0.002–0.76 | 0.021 |
| grid_ising (safety) | 1e4 | 7.9 (0/14 wins) | 5.1–17 | 56 (0/14 wins) |

- Generic IQP vs MaxEnt(3) at 1e4: median R 1.17, 2/14 wins. This reproduces the earlier finding that the unrestricted
  IQP does not win at finite N.
- iqp_local training residual / noise floor: median 0.49 at 1e4 and 0.79 at 1e5. The fit reaches the noise floor.
- R improves from 1e4 to 1e5 (0.35 → 0.19). The advantage does not shrink with more data, as expected when the
  IQP family is right and MaxEnt(3) is misspecified (B > 0).

## Reading: A1

- The generic IQP's finite-N loss is a non-identifiability problem. A known device graph removes it: 85 candidates,
  of which 36 (the triples) are inactive and not told to the model.
- MaxEnt given the same graph does far worse (R vs me_local ≈ 0.07). Interference makes log p non-local, so the
  classical model cannot use the graph prior.
- The safety set behaves correctly. On classical grid-Ising data, the local IQP loses to both MaxEnt arms by 8× and 56×.
  The prior helps only when the data are coherent. It does not win by being a generally better fitter.

## Limits (state these in the paper)

1. **Well-specified synthetic target.** The data are produced by an IQP inside the iqp_local family. This shows that
   the right inductive bias wins. It is not evidence about real data. The QEC data (steps 17–22) remain a negative.
2. **No computational advantage.** n = 16; IQP moments are classically estimable at any n. The claim is statistical
   (sample-efficiency for completing orders 4–6), not complexity-theoretic.
3. **One graph, one σ.** 4×4 grid, σ = 0.251. Other topologies, sizes, and couplings are untested.
4. **Init std 0.3 and 20 restarts were chosen on dev seeds 900–903.** They are guesses, though they generalised to 14/14.
5. **Fewer parameters.** iqp_local has 85 params against me3's 696 and me_local's 76. The H2 comparison (76 vs 85) is
   the near-equal-size one.

## Next

Paper positioning: non-identifiability explains why the generic IQP loses. A hardware-native connectivity prior fixes
it and gives a statistical advantage that the classical model cannot copy. There is no computational advantage for
moment tasks, and the QEC result is negative. A natural follow-up is a real-hardware dataset with a known coupling map,
or a misspecified-graph robustness test.
