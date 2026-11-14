"""Step 26: gate-level Pauli noise on the step 23 grid IQP circuit, by trajectory averaging.

Circuit: H^n |0>, then the diagonal gates exp(i theta_g Z_g) in TARGET_GENS order (16 singles, 24 edges,
9 plaquettes), then H^n, then measure. After every gate, each qubit it acts on suffers single-qubit depolarizing
noise with probability p_gate (X, Y, Z with p/3 each). Readout flips at eta are applied exactly afterwards.

In the Z basis between the two Hadamard layers the state is u(z) / sqrt(2^n) with |u| = 1 for the ideal circuit.
X_j:  u(z) -> u(z xor e_j);   Z_j:  u(z) -> (-1)^{z_j} u(z);   Y_j = i X_j Z_j (global phase dropped).
p(x) = |fwht(u)(x) / 2^n|^2, averaged over trajectories.

The target is DEFINED as the average over n_traj trajectories drawn from default_rng(seed_traj). With the default
n_traj it is a fixed, exactly computable mixture, so G is still scored exactly against it.
"""
from __future__ import annotations

import numpy as np

from src.step1.bits import fwht, parity_matrix
from src.step23 import grid as Gd
from src.step24 import conds as C24

NB = Gd.N_BITS
N_TRAJ = 4000                     # guess: Monte-Carlo size of the defined mixture (spec §2)
_Z = np.arange(2**NB, dtype=np.int64)
_S = None


def _gate_signs():
    global _S
    if _S is None:
        _S = parity_matrix(NB, Gd.TARGET_GENS)          # (2^n, 49), +-1
    return _S


def _qubits(mask: int):
    return [j for j in range(NB) if (mask >> j) & 1]


def noisy_grid_iqp(seed: int, p_gate: float, eta: float = 0.0, n_traj: int = N_TRAJ) -> np.ndarray:
    theta = Gd.grid_iqp_theta(seed)
    S = _gate_signs()
    gq = [_qubits(int(g)) for g in Gd.TARGET_GENS]
    rng = np.random.default_rng(30_000 + seed)
    N = 2**NB
    phases = np.exp(1j * S * theta[None, :])            # per-gate diagonal factor, (2^n, 49)
    ideal = np.prod(phases, axis=1)
    a = fwht(ideal) / N
    p_ideal = a.real**2 + a.imag**2
    acc = np.zeros(N)
    n_clean = 0
    for _ in range(n_traj):
        # draw the error pattern first; error-free trajectories reuse the ideal distribution
        events = []
        for k, qs in enumerate(gq):
            for j in qs:
                if rng.random() < p_gate:
                    events.append((k, j, int(rng.integers(3))))   # 0 = X, 1 = Y, 2 = Z
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
                bit = 1 << j
                if t in (1, 2):
                    u = u * (1.0 - 2.0 * ((_Z >> j) & 1))
                if t in (0, 1):
                    u = u[_Z ^ bit]
        a = fwht(u) / N
        acc += a.real**2 + a.imag**2
    p = (acc + n_clean * p_ideal) / n_traj
    p /= p.sum()
    return C24.readout_channel(p, eta) if eta else p
