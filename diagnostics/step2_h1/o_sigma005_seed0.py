"""Step 2 build item 2: why the oracle-support (O) fit misses 1e-10 at sigma = 0.05, seed 0.
Diagnostic only; imports src/step1 and src/step2, changes nothing."""
import json
from pathlib import Path

import numpy as np

from src.step1.bits import masks_up_to, popcount
from src.step1.models.iqp import IQPModel
from src.step1.walsh import parity_coefficients
from src.step2.sweep import fit_iqp, sigma_target

n = 12
p, masks, theta, z, layout = sigma_target(0.05, 0, n)
ops = masks_up_to(n, 3)
fhat = parity_coefficients(p)[ops]
m = IQPModel(n, gens=masks)
r = fit_iqp(m, fhat, ops, seed=0)
out = {"restarts": r["restarts"], "best_trace": r["trace"]}
th_all = []
for k, x in enumerate(r["restarts"]):
    pass
# best restart's params; align signs with theta* over the gauge group
# theta_g -> (-1)^{|g & B|} theta_g (bit flips of the input, p unchanged) and theta -> -theta
th = r["fit"].params
best = None
for B in range(2**n):
    sgn = 1.0 - 2.0 * (popcount(masks & B) % 2)
    for gsign in (1.0, -1.0):
        mism = np.sign(gsign * sgn * th) != np.sign(theta)
        c = int(mism.sum())
        if best is None or c < best[0]:
            best = (c, B, gsign, mism)
c, B, gsign, mism = best
aligned = gsign * (1.0 - 2.0 * (popcount(masks & B) % 2)) * th
print(f"best restart residual {r['best_residual']:.3e}")
print(f"after gauge alignment (B={B:#05x}, global {gsign:+.0f}): {c}/38 sign mismatches")
print("mismatched generators (layout, theta*, fitted aligned):")
for i in np.flatnonzero(mism):
    print(f"   {layout[i]}  {theta[i]:+.4f}  {aligned[i]:+.4f}")
print(f"max |aligned - theta*| over matching signs: {np.max(np.abs(aligned[~mism] - theta[~mism])):.2e}")
J = m.moment_jacobian(th, ops); sv = np.linalg.svd(J, compute_uv=False)
J0 = m.moment_jacobian(theta, ops); sv0 = np.linalg.svd(J0, compute_uv=False)
print(f"Jacobian at fit: rank {int((sv > 1e-8*sv[0]).sum())}/38, sv min/max {sv[-1]:.2e}/{sv[0]:.2e}")
print(f"Jacobian at truth: sv min/max {sv0[-1]:.2e}/{sv0[0]:.2e}; residual at truth "
      f"{m.loss_and_grad(theta, fhat, ops)[0]:.1e}; |grad| at fit {np.linalg.norm(m.loss_and_grad(th, fhat, ops)[1]):.2e}")
out.update({"gauge_B": B, "global_sign": gsign, "n_sign_mismatch": c,
            "mismatched": [[list(layout[i]), float(theta[i]), float(aligned[i])] for i in np.flatnonzero(mism)],
            "sv_min_fit": float(sv[-1]), "sv_min_truth": float(sv0[-1])})
Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=1))
