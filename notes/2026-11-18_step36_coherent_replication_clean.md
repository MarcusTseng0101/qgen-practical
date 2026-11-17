# Step 36: clean rerun of the coherent replication (2026-11-18)

Spec: `specs/step36_coherent_replication_clean.md` (3c6d189). Code and timing pilot: worktree bb18c02.
Results: worktree 5ebabc9. `--verify` → ALL PASS.

## Verdict

**D1 PASS: 26/28 (need 19), p = 1.5e-6.** All 28 jobs finished, none was killed.

## Reported (no verdict)

- **Median R** (G_flow / G_me3): **0.62**, bootstrap 95% CI [0.57, 0.64].
  - Given-graph fit: 0.62. Enlarged fit: 0.65.
- **Alarms:** 3 of 28.
- **Pooled, descriptive only:**

  | Source | Wins |
  |---|---|
  | step 29 | 10/14 |
  | step 33 | 13/14 |
  | step 34 | 15/20 finished |
  | step 36 | 26/28 |
  | **Total** | **64/76**, sign-test p = 5e-10 |

## Run log

- **Timing pilot:** 14 parallel jobs on spent seeds 1168–1181, under a foreign load of about 25. Each took
  98–176 min, which set the 12 h stop-loss.
- **First launch** at 01:19. The user stopped it at 01:33 to download a game. No job had finished, and all worker
  trees were killed. This is recorded in `INTERRUPTED.txt`.
- **Resumed** at 01:36, with the stop-loss counted from the resume. All jobs finished at 06:29.

## Reading (spec §6, D1 PASS)

Coherent over-rotations at ε = 0.2 do not remove the advantage on the correct graph. The paper's "limit" becomes "the
hardest case". There are three tests on separate fresh sets:

| Test | Result | Cause |
|---|---|---|
| step 29 | FAIL 10/14 | on the merits |
| step 34 | FAIL 15/28 | compute: 8 jobs killed |
| step 36 | PASS 26/28 | — |

The margin is smaller than in the other noise settings: median R 0.62, against about 0.35–0.5 elsewhere. The outcome
also varies between sets of 14.

## Paper changes

- §V is retitled "The hardest case: coherent over-rotations". It gives the three tests and the pooled 64/76.
- The abstract now reads "the hardest case: the advantage shrinks, and it passed only one of three tests…".
- The intro says "the noise class where it is weakest".
- The discussion and the open questions are updated.
- §VI now notes that step 33's 13/14 agrees with the passing test.
- The PDF builds cleanly with 6 pages. Prose: 17.1 words per sentence on average.
