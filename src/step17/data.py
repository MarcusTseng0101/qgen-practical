"""Step 17 real data: MNIST (70 000 images) reduced to 16 bits.

Reduction (fixed before any fit): crop the centre 20x20, average-pool 5x5 blocks to 4x4, then
threshold each of the 16 block means at its median over all 70 000 images, so every bit is
roughly balanced. Bit j (row-major block j) is bit j of the state index.

Raw files are downloaded once with urllib into data/real/mnist/ (git-ignored) and checked by
SHA-256, so the dataset is pinned without committing it.
"""
from __future__ import annotations

import gzip
import hashlib
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "data" / "real" / "mnist"
URL = "https://storage.googleapis.com/cvdf-datasets/mnist/"
FILES = ("train-images-idx3-ubyte.gz", "t10k-images-idx3-ubyte.gz")
n = 16


def fetch() -> dict:
    DIR.mkdir(parents=True, exist_ok=True)
    sha = {}
    for f in FILES:
        p = DIR / f
        if not p.exists():
            urllib.request.urlretrieve(URL + f, p)
        sha[f] = hashlib.sha256(p.read_bytes()).hexdigest()
    return sha


def images() -> np.ndarray:
    fetch()
    out = []
    for f in FILES:
        raw = gzip.decompress((DIR / f).read_bytes())
        k = int.from_bytes(raw[4:8], "big")
        out.append(np.frombuffer(raw, np.uint8, offset=16).reshape(k, 28, 28))
    return np.concatenate(out).astype(np.float64) / 255.0


def bits() -> np.ndarray:
    """(70000, 16) array of 0/1."""
    x = images()[:, 4:24, 4:24].reshape(-1, 4, 5, 4, 5).mean(axis=(2, 4)).reshape(-1, 16)
    return (x > np.median(x, axis=0)).astype(np.int64)


def indices(b: np.ndarray) -> np.ndarray:
    return b @ (1 << np.arange(b.shape[1]))
