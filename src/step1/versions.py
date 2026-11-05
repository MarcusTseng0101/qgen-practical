"""Resolved library versions, printed into every metrics.json (spec: Stack)."""
import platform

import matplotlib
import numpy
import scipy


def versions() -> dict:
    return {"python": platform.python_version(), "numpy": numpy.__version__,
            "scipy": scipy.__version__, "matplotlib": matplotlib.__version__}


if __name__ == "__main__":
    print(versions())
