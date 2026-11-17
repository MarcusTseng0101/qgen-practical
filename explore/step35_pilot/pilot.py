"""Step 35 pilot: time step 29's xf02 run_job under the current CPU load (seeds 1168-1181, spent afterwards).

Run from the worktree root: python -m explore.step35_pilot.pilot SEED   (one job; launch 14 in parallel)
Only the 'secs' field is used, to size the step 35 stop-loss.
"""
import sys
from pathlib import Path

from src.step29 import run as R29

R29.RESULTS = Path("explore/step35_pilot/out")
R29.run_job("xf02", int(sys.argv[1]))
