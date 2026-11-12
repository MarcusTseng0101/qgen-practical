"""Theory check (explanatory, spent seeds): bias-variance decomposition of the completion error.

Both models are fitted to the same order-<=3 moments f_lo. Each defines a completion map
C: f_lo -> f_hi (orders 4-6). For an unbiased moment estimate with per-shot covariance S1,
    E G(N) ~= B + V / N,  B = G at N = inf,  V = tr(W C' S1 C'^T)
(delta method; W = the weights of G: 1 / (3 * #ops in that order)).
  MaxEnt:  C' = Cov_q(chi_hi, chi_lo) Cov_q(chi_lo, chi_lo)^-1      (exponential family)
  IQP:     C' = J_hi J_lo^+                                          (Gauss-Newton)
Prediction R(N) = (B_iqp + V_iqp/N) / (B_me + V_me/N), compared with step 14's measured R.
"""
import sys, json, time, numpy as np
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.bits import masks_up_to, popcount
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.walsh import parity_coefficients, fwht
from src.step4.targets import iqp4_target
from src.step14.run import SIGMA

n = 16; NN = 2**n
lo = masks_up_to(n, 3)
allm = np.arange(NN)
w = popcount(allm)
hi = allm[(w >= 4) & (w <= 6)]
W = np.array([1.0 / (3 * np.sum(w == k)) for k in popcount(hi)])


def cov_chi(f, A, B):
    """Cov(chi_A, chi_B) = f_{A xor B} - f_A f_B, for parity vector f over all masks."""
    return f[A[:, None] ^ B[None, :]] - f[A][:, None] * f[B][None, :]


def V_of(Cp, S1):
    return float(np.einsum("i,ij,jk,ik->", W, Cp, S1, Cp))


seed = int(sys.argv[1])
t = time.time()
p = iqp4_target(SIGMA, seed, n)[0]
fp = parity_coefficients(p)
S1 = cov_chi(fp, lo, lo)                               # per-shot covariance of the training moments
f_lo = fp[lo]

me = MaxEntModel(n, 3); q_me = me.prob(me.fit_moments(f_lo, lo).params)
fq = parity_coefficients(q_me)
Cme = cov_chi(fq, hi, lo) @ np.linalg.inv(cov_chi(fq, lo, lo))
B_me = M1.completion_gap(q_me, p, n)["G"]; V_me = V_of(Cme, S1)

m = IQPModel(n); fr = m.fit_moments(f_lo, lo, seed=seed, n_restarts=3)
th = fr.params
u = np.exp(1j * m.phase(th)); a = fwht(u) / NN
J = np.empty((NN, m.n_params))
for g in range(m.n_params):                            # forward mode, one column per generator
    da = fwht(1j * m.S[:, g] * u) / NN
    J[:, g] = fwht(2.0 * np.real(np.conj(a) * da))
Jlo, Jhi = J[lo], J[hi]
sv = np.linalg.svd(Jlo, compute_uv=False)
Ciqp = Jhi @ np.linalg.pinv(Jlo, rcond=1e-10)
B_iqp = M1.completion_gap(m.prob(th), p, n)["G"]; V_iqp = V_of(Ciqp, S1)
# amplification: V per unit of input noise, i.e. ||C'||^2 weighted
out = {"seed": seed, "B_iqp": B_iqp, "B_me": B_me, "V_iqp": V_iqp, "V_me": V_me,
       "resid_iqp": fr.train_residual, "cond_Jlo": float(sv[0] / sv[-1]), "smin_Jlo": float(sv[-1]),
       "R_inf": B_iqp / B_me, "secs": time.time() - t}
for N in (100_000, 10_000):
    out[f"Rpred_{N}"] = (B_iqp + V_iqp / N) / (B_me + V_me / N)
print(json.dumps(out), flush=True)
