"""D2 (step 4 pre-amendment diagnostic): D3 of mix(s, delta) for delta in {0.9, 0.95, 0.99},
seeds 0-4, the same Dirichlet weights and u (src/step4/targets.mix_target). D3 only, computed
exactly as in results/step4/calibration.json (src/step2/sweep.d3); that file is read, not changed.
Writes only to this directory."""
import json
from pathlib import Path

import numpy as np

from src.step2.sweep import d3
from src.step4.targets import mix_target

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NEW = (0.9, 0.95, 0.99)

cal = json.loads((ROOT / "results" / "step4" / "calibration.json").read_text())
per = {f"{dl:g}": [d3(mix_target(s, dl))[0] for s in range(5)] for dl in NEW}
out = {"new_D3_per_seed": per, "new_D3_median": {k: float(np.median(v)) for k, v in per.items()},
       "existing_D3_by_delta": cal["D3_by_delta"], "existing_D3_per_seed": cal["D3_by_delta_per_seed"],
       "iqp_sigma_0.2_D3_median": cal["iqp_sigma_0.2_D3_median"]}
(HERE / "d2_mix_delta.json").write_text(json.dumps(out, indent=1))
allper = {**cal["D3_by_delta_per_seed"], **per}
for k in sorted(allper, key=float):
    v = allper[k]
    print(f"delta {k:>4}: median {np.median(v):.3e}  per seed " + " ".join(f"{x:.2e}" for x in v)
          + ("" if k in per else "   (calibration.json)"))
print(f"iqp sigma=0.2 median D3 = {cal['iqp_sigma_0.2_D3_median']:.3f}")
