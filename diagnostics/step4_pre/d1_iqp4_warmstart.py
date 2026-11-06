"""D1 (step 4 pre-amendment diagnostic, BLIND): iqp4, sigma = 0.2, seeds 0-4.

Only training-side quantities: residuals on the exact order-<=3 moments and Jacobian minimum
singular values. No completion quantity (no G_iqp, G_maxent, R, no order-4..6 error) is computed.
Imports src/step1 and src/step4; changes nothing in src/. Writes only to this directory.

Per seed:
 (a) the truth's weight-<=3 angles (the 38 iqp generators, zeros elsewhere in the generic
     298-generator G) plugged into G's training residual, no optimization;
 (b) one L-BFGS-B run from (a), via the production fit_moments(n_restarts=1, theta0=...);
 (c) 10 restarts from the spec's init N(0, 0.05^2) (fit_moments' own draws: default_rng(seed),
     one vector per restart), each via fit_moments(n_restarts=1, theta0=init); final residual
     and the minimum singular value of the 298 x 298 moment Jacobian at each solution.
"""
import json
import time
from pathlib import Path

import numpy as np

from src.step1.models.iqp import INIT_STD, IQPModel
from src.step4.run import training_moments
from src.step4.targets import iqp4_target
from src.step2.sweep import sigma_target

SIGMA, N_RESTARTS, n = 0.2, 10, 12
HERE = Path(__file__).resolve().parent


def sv_min(model, theta, ops):
    return float(np.linalg.svd(model.moment_jacobian(theta, ops), compute_uv=False).min())


rows = []
for seed in range(5):
    t0 = time.time()
    p, masks, theta, _ = iqp4_target(SIGMA, seed, n)
    fhat, ops = training_moments(p, None, seed, n)
    model = IQPModel(n)
    pos = {int(m): i for i, m in enumerate(model.gens)}
    _, masks3, theta3, _, _ = sigma_target(SIGMA, seed, n)
    assert np.array_equal(masks[:len(masks3)], masks3)
    warm = np.zeros(model.n_params)
    for m, t in zip(masks3, theta3):
        warm[pos[int(m)]] = t
    res_a = float(model.loss_and_grad(warm, fhat, ops)[0])
    fb = model.fit_moments(fhat, ops, seed=seed, n_restarts=1, theta0=warm)
    res_b = float(fb.train_residual)
    sv_b = sv_min(model, fb.params, ops)
    rng = np.random.default_rng(seed)
    restarts = []
    for r in range(N_RESTARTS):
        init = rng.normal(0.0, INIT_STD, model.n_params)
        f = model.fit_moments(fhat, ops, seed=seed, n_restarts=1, theta0=init)
        restarts.append({"restart": r, "residual": float(f.train_residual), "nit": int(f.nit),
                         "message": f.message, "sv_min": sv_min(model, f.params, ops)})
    best = min(x["residual"] for x in restarts)
    row = {"seed": seed, "a_truth_w3_residual": res_a, "b_warm_residual": res_b,
           "b_warm_nit": int(fb.nit), "b_warm_message": fb.message, "b_warm_sv_min": sv_b,
           "c_restarts": restarts, "c_best_residual": best,
           "ratio_warm_over_best_random": res_b / best,
           "n_restarts_within_2x_warm": int(sum(x["residual"] <= 2 * res_b for x in restarts)),
           "seconds": time.time() - t0}
    rows.append(row)
    print(f"seed {seed}: (a) {res_a:.3e}  (b) {res_b:.3e} [sv_min {sv_b:.1e}]  (c) best {best:.3e}  "
          f"ratio b/c {res_b / best:.3g}  within 2x warm {row['n_restarts_within_2x_warm']}/10  "
          f"({row['seconds']:.0f} s)", flush=True)
    print("   restarts:", " ".join(f"{x['residual']:.2e}(sv {x['sv_min']:.1e})" for x in restarts), flush=True)

(HERE / "d1_iqp4_warmstart.json").write_text(json.dumps({"sigma": SIGMA, "seeds": rows}, indent=1))
