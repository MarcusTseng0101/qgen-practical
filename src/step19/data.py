"""Step 19 real data: Google surface-code detection events (Zenodo 6804040), reduced to 16 bits.

Source: google_qec3v5_experiment_data.zip, md5 a7fd8b481c3087090093106382dc217d, in
data/real/google_qec/ (git-ignored). The distance-3, 3-round experiments (d3_r03) have 24 detectors per
shot: 4 at t = 0, 8 at t = 1, 8 at t = 2 and 4 at t = 3 (stim DETECTOR time coordinates). The reduction,
fixed before any fit, keeps detectors 4..19: all 8 stabilizers at t = 1 and t = 2. That gives n = 16.

There are 8 runs: bases X and Z at 4 chip centres. Each has 50 000 shots.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "data" / "real" / "google_qec"
ZIP_MD5 = "a7fd8b481c3087090093106382dc217d"
RUNS = tuple(f"surface_code_b{b}_d3_r03_center_{c}" for c in ("3_5", "5_3", "5_7", "7_5") for b in ("X", "Z"))
N_DET, KEEP = 24, slice(4, 20)
SHOTS = 50_000
n = 16


def zip_md5() -> str:
    return hashlib.md5((DIR / "qec3v5.zip").read_bytes()).hexdigest()


def detectors(run: str) -> np.ndarray:
    """(50000, 24) 0/1 detection events; b8 format, little-endian bit order, byte-aligned per shot."""
    raw = np.fromfile(DIR / run / "detection_events.b8", dtype=np.uint8)
    nb = (N_DET + 7) // 8
    bits = np.unpackbits(raw.reshape(-1, nb), axis=1, bitorder="little")[:, :N_DET]
    assert bits.shape[0] == SHOTS
    return bits.astype(np.int64)


def bits(run: str) -> np.ndarray:
    return detectors(run)[:, KEEP]


def indices(b: np.ndarray) -> np.ndarray:
    return b @ (1 << np.arange(b.shape[1]))
