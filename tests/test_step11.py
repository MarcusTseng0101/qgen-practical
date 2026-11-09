"""Step 11 tests (specs/step11_bitflip_control.md), written before the grid."""
import itertools

import numpy as np

from src.step1.bits import fwht, masks_up_to
from src.step1.models.iqp import IQPModel
from src.step11.bitflip import BitflipModel


def test_T1_explicit_enumeration():
    rng = np.random.default_rng(1)
    n = 6
    gens = rng.choice(masks_up_to(n, 3), 8, replace=False)
    th = rng.normal(0, 0.6, 8)
    q = np.sin(th) ** 2
    p = np.zeros(2**n)
    for b in itertools.product((0, 1), repeat=8):
        x = 0
        w = 1.0
        for bi, g, qi in zip(b, gens, q):
            x ^= int(g) if bi else 0
            w *= qi if bi else 1 - qi
        p[x] += w
    assert np.max(np.abs(BitflipModel(n, gens).prob(th) - p)) < 1e-12


def test_T2_product_formula_all_masks():
    rng = np.random.default_rng(2)
    m = BitflipModel(8)
    th = rng.normal(0, 0.4, m.n_params)
    p = m.prob(th)
    ops = np.arange(2**8)
    assert np.max(np.abs(fwht(p) - m.moments(th, ops))) < 1e-12
    assert p.min() > -1e-12 and abs(p.sum() - 1) < 1e-12


def _fd_check(m, th, fhat, ops, h=1e-6):
    L, g = m.loss_and_grad(th, fhat, ops)
    fd = np.array([(m.loss_and_grad(th + h * e, fhat, ops)[0] - m.loss_and_grad(th - h * e, fhat, ops)[0]) / (2 * h)
                   for e in np.eye(len(th))])
    return np.linalg.norm(g - fd) / np.linalg.norm(fd)


def test_T3_gradient_fd():
    rng = np.random.default_rng(3)
    m = BitflipModel(8)
    ops = masks_up_to(8, 3)
    th = rng.normal(0, 0.3, m.n_params)
    fhat = rng.uniform(-0.5, 0.9, len(ops))
    assert _fd_check(m, th, fhat, ops) < 1e-6


def test_T4_gradient_at_zero_cos():
    rng = np.random.default_rng(4)
    m = BitflipModel(6)
    ops = masks_up_to(6, 3)
    th = rng.normal(0, 0.3, m.n_params)
    th[[0, 7]] = np.pi / 4
    fhat = rng.uniform(-0.5, 0.9, len(ops))
    L, g = m.loss_and_grad(th, fhat, ops)
    assert np.all(np.isfinite(g))
    assert _fd_check(m, th, fhat, ops) < 1e-6


def test_T5_second_order_agreement_with_iqp():
    rng = np.random.default_rng(5)
    n = 6
    b, q = BitflipModel(n), IQPModel(n)
    ops = np.arange(1, 2**n)
    th = rng.normal(0, 1.0, b.n_params)
    d = [np.max(np.abs(b.moments(t * th, ops) - q.moments(t * th, ops))) for t in (0.04, 0.02)]
    assert d[0] / d[1] >= 12
