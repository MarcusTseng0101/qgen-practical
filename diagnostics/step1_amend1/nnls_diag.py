import numpy as np, sys
sys.path.insert(0, ".")
from tests.test_core import _small_angle_target
from src.step1.models.iqp import select_sparse_generators
from src.step1.bits import masks_up_to, popcount
from src.step1.walsh import parity_coefficients
n = 12
for seed in (0, 1):
    masks, theta, p = _small_angle_target(n, seed)
    ops = masks_up_to(n, 3)
    fhat = parity_coefficients(p)[ops]
    sel = select_sparse_generators(fhat, ops)
    cand, t2 = sel["candidates"], sel["theta2_all"]
    true = set(int(m) for m in masks)
    is_true = np.array([int(c) in true for c in cand])
    order = np.argsort(-t2)
    print(f"seed {seed}: max theta2 {t2.max():.3e}, threshold {1e-3*t2.max():.3e}, nnls rnorm {sel['nnls_rnorm']:.2e}")
    print(f"  true theta2 range {np.min(theta**2):.2e}..{np.max(theta**2):.2e}")
    print(f"  true est range {t2[is_true].min():.3e}..{t2[is_true].max():.3e}; max |err| {np.max(np.abs(t2[is_true]-np.array([theta[list(masks).index(c)]**2 for c in cand[is_true]]))):.2e}")
    sp = t2[~is_true]
    print(f"  spurious: {np.sum(sp>0)} nonzero, {np.sum(sp>=1e-3*t2.max())} above threshold, max {sp.max():.3e}, weights {np.bincount(popcount(cand[~is_true][sp>=1e-3*t2.max()]), minlength=4)[1:]}")
    print(f"  rank of first non-true in sorted list: {np.argmax(~is_true[order])}  (38 true)")
    print(f"  sorted spurious above threshold: {np.sort(sp[sp>=1e-3*t2.max()])[::-1][:12]}")
    # how good is the 2nd-order model itself? residual of true theta2 in the linear system
    M = (popcount(ops[:,None] & cand[None,:]) % 2).astype(float)
    tt = np.zeros(len(cand)); 
    for m_, th in zip(masks, theta): tt[list(cand).index(m_)] = th**2
    m = (1-fhat)/2
    print(f"  |M t2_true - m| = {np.linalg.norm(M@tt-m):.2e}  vs nnls rnorm {sel['nnls_rnorm']:.2e}; |m| {np.linalg.norm(m):.2e}; rank M {np.linalg.matrix_rank(M)}")
