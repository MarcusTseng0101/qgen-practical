"""Step 28: CORRELATED gate noise on the step 23 grid IQP circuit (compare step 26's independent noise).

After every gate acting on k qubits, with probability q_k a uniformly random NON-IDENTITY k-qubit Pauli string is
applied to those qubits. q_k is chosen so that each qubit's marginal error rate equals p_gate, as in step 26:
the marginal of a uniform non-identity k-qubit Pauli on one qubit is 3 * 4^(k-1) / (4^k - 1), so
q_k = p_gate * (4^k - 1) / (3 * 4^(k-1)). The only difference from step 26 is correlation between the qubits of a gate.

Conventions as in src.step26.noise: X_j: u(z) -> u(z xor e_j); Z_j: sign (-1)^{z_j}; Y = both (global phase dropped).
The target is DEFINED as the average over n_traj trajectories from default_rng(40_000 + seed).
"""
from __future__ import annotations

import numpy as np

from src.step1.bits import fwht
from src.step23 import grid as Gd
from src.step24 import conds as C24
from src.step26 import noise as N26

NB = Gd.N_BITS
N_TRAJ = 4000                     # guess, as in step 26
_Z = N26._Z


def q_of_k(p_gate: float, k: int) -> float:
    return p_gate * (4**k - 1) / (3 * 4 ** (k - 1))


def correlated_grid_iqp(seed: int, p_gate: float, eta: float = 0.0, n_traj: int = N_TRAJ) -> np.ndarray:
    theta = Gd.grid_iqp_theta(seed)
    S = N26._gate_signs()
    gq = [N26._qubits(int(g)) for g in Gd.TARGET_GENS]
    rng = np.random.default_rng(40_000 + seed)
    N = 2**NB
    phases = np.exp(1j * S * theta[None, :])
    a = fwht(np.prod(phases, axis=1)) / N
    p_ideal = a.real**2 + a.imag**2
    acc = np.zeros(N)
    n_clean = 0
    for _ in range(n_traj):
        events = []
        for k, qs in enumerate(gq):
            if rng.random() < q_of_k(p_gate, len(qs)):
                code = int(rng.integers(1, 4 ** len(qs)))          # uniform non-identity Pauli string
                for i, j in enumerate(qs):
                    t = (code >> (2 * i)) & 3                      # 0 = I, 1 = X, 2 = Y, 3 = Z
                    if t:
                        events.append((k, j, t - 1))               # step 26 code: 0 = X, 1 = Y, 2 = Z
        if not events:
            n_clean += 1
            continue
        u = np.ones(N, dtype=np.complex128)
        ev = {}
        for k, j, t in events:
            ev.setdefault(k, []).append((j, t))
        for k in range(len(gq)):
            u *= phases[:, k]
            for j, t in ev.get(k, []):
                if t in (1, 2):
                    u = u * (1.0 - 2.0 * ((_Z >> j) & 1))
                if t in (0, 1):
                    u = u[_Z ^ (1 << j)]
        a = fwht(u) / N
        acc += a.real**2 + a.imag**2
    p = (acc + n_clean * p_ideal) / n_traj
    p /= p.sum()
    return C24.readout_channel(p, eta) if eta else p
