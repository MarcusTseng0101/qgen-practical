"""Gradient check + exactness check: with the target's own gens (1-body layer first) and eps on the 1-body layer only,
CohIQP must equal the true coherent circuit when the true circuit has RX only after the 1-body gates."""
import sys, time; sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
import numpy as np
from src.step1.bits import fwht
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step29 import noise as N29
from src.step30.cohiqp import CohIQP
from src.step26.flipiqp import _bits
p = N29.coherent_grid_iqp(980, 0.2, 0.02)
fhat, ops = training_moments(p, 10_000, 980, 16)
m = CohIQP(16, Gd.LOCAL_GENS); m._B = _bits(np.asarray(ops), 16)
rng = np.random.default_rng(1)
x = np.concatenate([rng.normal(0, .3, m.K), rng.normal(0, .3, m.E*16), rng.uniform(.7, 1, 16)])
t = time.time(); L, g = m.loss_and_grad(x, fhat, ops); print("eval s", time.time() - t)
worst = 0
for i in list(rng.choice(m.K, 4, replace=False)) + list(m.K + rng.choice(m.E*16, 6, replace=False)) + [len(x)-3]:
    h = 1e-6; e = np.zeros_like(x); e[i] = h
    num = (m.loss_and_grad(x+e, fhat, ops)[0] - m.loss_and_grad(x-e, fhat, ops)[0]) / (2*h)
    worst = max(worst, abs(g[i]-num)/max(1e-8, abs(num))); print(i, g[i], num)
print("worst rel", worst)
# exactness vs a brute-force circuit: singles, RX(e) on every qubit, then edges+plaqs
th = Gd.grid_iqp_theta(980); e = rng.normal(0, .2, 16)
mt = CohIQP(16, Gd.TARGET_GENS)
w = np.array([bin(int(g)).count("1") for g in Gd.TARGET_GENS])
order = np.concatenate([np.where(w == 1)[0], np.where(w == 2)[0], np.where(w >= 3)[0]])
xx = np.concatenate([th[order], e, np.zeros(16), np.ones(16)])
Z = np.arange(2**16); S = __import__("src.step1.bits", fromlist=["parity_matrix"]).parity_matrix(16, Gd.TARGET_GENS)
u = np.exp(1j * S[:, w == 1] @ th[w == 1])
for j in range(16): u = np.cos(e[j]/2) * u - 1j*np.sin(e[j]/2) * u[Z ^ (1 << j)]
u = u * np.exp(1j * S[:, w >= 2] @ th[w >= 2])
a = fwht(u) / 2**16; pb = np.abs(a)**2
print("exact diff", np.abs(mt.prob(xx) - pb / pb.sum()).max())
