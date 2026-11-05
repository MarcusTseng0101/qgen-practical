"""Step 3 budget projection (spec, Budget): time the sigma = 0.4, seed 0 pair (iqp and
maxent_proj, each with O, G and MaxEnt(3)) and extrapolate to the 60-instance grid.

  python -m src.step3.projection        (reads results/step3/*/sigma_0.4/seed_0/metrics.json)

projected_hours = 60 x mean(total_seconds of the two sigma = 0.4 instances) / 3600.
Each instance's total_seconds includes building its pair (--all builds it once per pair, so
this is slightly conservative). Fit times depend on sigma; sigma = 0.05 is timed too and
reported, but per the spec only the sigma = 0.4 pair enters the projection.
"""
import json
from pathlib import Path

from src.step3.run import ROOT, SEEDS, SIGMAS, TARGETS, default_out

N_INSTANCES = len(SIGMAS) * len(SEEDS) * len(TARGETS)   # 60


def main():
    per = {}
    for sg in (0.05, 0.4):
        for t in TARGETS:
            f = default_out(t, sg, 0) / "metrics.json"
            if f.exists():
                d = json.loads(f.read_text())
                per[f"{t}/sigma_{sg:g}"] = {
                    "total_seconds": d["total_seconds"],
                    "O_fit_seconds": d.get("O_fit_seconds"),
                    "G_fit_seconds": d.get("G_fit_seconds"),
                    "other_seconds": d["total_seconds"] - d.get("O_fit_seconds", 0) - d.get("G_fit_seconds", 0)}
    basis = [per[f"{t}/sigma_0.4"] for t in TARGETS]
    mean = sum(b["total_seconds"] for b in basis) / len(basis)
    mean_g = sum(b["G_fit_seconds"] for b in basis) / len(basis)
    out = {"projected_hours": N_INSTANCES * mean / 3600.0, "instances": N_INSTANCES,
           "basis": "mean total_seconds of iqp and maxent_proj at sigma = 0.4, seed 0, x 60",
           "mean_instance_seconds": mean,
           "projected_hours_if_G_restarts_3_linear_guess": N_INSTANCES * (mean - mean_g * (1 - 3 / 10)) / 3600.0,
           "per_instance": per}
    # Not the spec's basis: sigma = 0.05 is measured several times slower, so also project with
    # the measured sigma = 0.05 time for its 10 instances and the sigma = 0.4 time for the other 50.
    if all(f"{t}/sigma_0.05" in per for t in TARGETS):
        m05 = sum(per[f"{t}/sigma_0.05"]["total_seconds"] for t in TARGETS) / len(TARGETS)
        n05 = len(SEEDS) * len(TARGETS)
        out["projected_hours_using_measured_sigma_0.05"] = (n05 * m05 + (N_INSTANCES - n05) * mean) / 3600.0
    path = ROOT / "results" / "step3" / "PROJECTION.json"
    path.write_text(json.dumps(out, indent=1))
    print(path)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
