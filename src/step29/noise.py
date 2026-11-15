"""Step 29: COHERENT (non-Pauli) gate errors on the step 23 grid IQP circuit.

After every gate, each qubit it acts on gets a small unwanted rotation RX(eps_j) = exp(-i eps_j X_j / 2), where
eps_j is a fixed per-qubit miscalibration (the same every time that qubit is touched). Deterministic: one state
vector, no trajectories.

In the Z basis between the two H layers (state u(z) / sqrt(2^n)):
    X_j: u(z) -> u(z xor e_j),  so  RX(eps): u -> cos(eps/2) u - i sin(eps/2) u[z xor e_j].
Readout flips at eta are applied exactly afterwards.

eps_j ~ N(0, eps_std^2) from default_rng(50_000 + seed): sign and size vary by qubit, as calibration errors do.
"""
from __future__ import annotations

import numpy as np

from src.step1.bits import fwht
from src.step23 import grid as Gd
from src.step24 import conds as C24
from src.step26 import noise as N26

NB = Gd.N_BITS
_Z = N26._Z


def eps_of(seed: int, eps_std: float) -> np.ndarray:
    return np.random.default_rng(50_000 + seed).normal(0.0, eps_std, NB)


def coherent_grid_iqp(seed: int, eps_std: float, eta: float = 0.0) -> np.ndarray:
    theta = Gd.grid_iqp_theta(seed)
    S = N26._gate_signs()
    gq = [N26._qubits(int(g)) for g in Gd.TARGET_GENS]
    eps = eps_of(seed, eps_std)
    c, s = np.cos(eps / 2), np.sin(eps / 2)
    N = 2**NB
    u = np.ones(N, dtype=np.complex128)
    for k, qs in enumerate(gq):
        u = u * np.exp(1j * S[:, k] * theta[k])
        for j in qs:
            u = c[j] * u - 1j * s[j] * u[_Z ^ (1 << j)]
    a = fwht(u) / N
    p = a.real**2 + a.imag**2
    p /= p.sum()
    return C24.readout_channel(p, eta) if eta else p
