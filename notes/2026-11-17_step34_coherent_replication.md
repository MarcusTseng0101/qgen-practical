# Step 34: replication of the coherent limit (2026-11-17)

Spec: `specs/step34_coherent_replication.md` (7adfbc7). Code: worktree 8429234. Results: worktree 4c0eba2.
`--verify` → ALL PASS. The stop-loss is recorded in `run_log.txt`.

## Verdict

**C1 FAIL: 15/28 (need 19), p = 0.43.**

- Only 20 of 28 jobs finished inside the 10 h stop-loss.
- The recipe won 15 of those 20.
- The 8 killed jobs (seeds 1155, 1159, 1161–1163, 1165–1167) count as failures, as the spec requires.

## Reported (no verdict)

- **Median R** (G_flow / G_me3) on the 20 finished jobs: **0.68**, bootstrap 95% CI [0.52, 0.91].
  - Given-graph fit alone: 0.77. Enlarged fit: 0.76.
- **Alarms:** 6 of 20.
- **Pooled, descriptive only:**
  - step 29: 10/14;
  - step 33: 13/14;
  - step 34: 15/20 finished;
  - total 38/48, sign-test p = 3e-5. This pool includes seen seeds and finished-only jobs, so it is not a test.

## Why the jobs were killed

- The CPU was heavily shared. The load average was about 60–73 on an i9-13900HX (24 physical cores, 32 threads,
  laptop power limit). About 45 other Python jobs, from another session, were running until about 18:00.
- First-wave jobs took 3.8–4.3 h each, against a 45 min median in step 29.
- The user stopped the other jobs at about 18:00. That was too late for the last 8 second-wave jobs.

## Reading (spec §5, C1 FAIL)

- The paper's limit stands as written: the recipe failed two pre-registered coherent tests.
- The honest content is narrower than "the advantage is gone":
  - on finished instances the recipe wins about 3 in 4, and the median R is 0.68 with an upper CI bound below 1;
  - coherent errors shrink the margin and make the per-instance outcome unreliable.
- This FAIL is partly a compute failure. If the 8 killed jobs had won at the observed rate, the count would have been
  about 21/28. That is a guess and is not used anywhere.

## Paper changes

- §V gained a paragraph on the replication: it failed, 20 of 28 finished, 15 wins, median R 0.68 [0.52, 0.91].
  The paragraph ends: "shrink the advantage and make it unreliable, although the recipe still wins on most
  instances".
- In §VI, the step 33 count of 13/14 is now framed as variation between instance sets.
- The abstract is unchanged: the limit still stands.

## Lesson for the next long run

Check the load average before launch. With more than about 20 foreign Python processes, either ask the user to pause
them or size the stop-loss on a timed first job. Do not size it on earlier wall-clock times.
