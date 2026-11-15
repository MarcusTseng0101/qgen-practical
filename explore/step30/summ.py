import json, glob, sys
import numpy as np
pat = sys.argv[1] if len(sys.argv) > 1 else "xf02_given"
rows = [json.load(open(f)) for f in sorted(glob.glob(rf"C:\Users\tseng\qgen-practical-step1\explore\step30\out\{pat}_*.json"))]
for d in rows:
    print(d["seed"], "Rcoh", d["R_coh"], "ratio", d["ratio_coh"], "| R_given29", d["R_given29"], "ratio29", d["ratio_given29"], "R_flow29", d["R_flow29"], "R_enl29", d["R_enl29"], "lam", d["lam_min"], d["secs"])
if rows:
    R = np.array([d["R_coh"] for d in rows]); print("n", len(R), "wins", (R < 1).sum(), "median R", np.median(R),
      "| given29 wins", sum(d["R_given29"] < 1 for d in rows), "median", np.median([d["R_given29"] for d in rows]),
      "| coh beats given29", sum(d["R_coh"] < d["R_given29"] for d in rows), "max ratio", max(d["ratio_coh"] for d in rows))
