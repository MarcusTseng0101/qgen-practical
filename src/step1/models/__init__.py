"""Model discovery: every module here that defines build(n) is a model."""
import importlib
import pkgutil


def discover(n: int) -> list:
    out = []
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        mod = importlib.import_module(f"{__name__}.{info.name}")
        if callable(getattr(mod, "build", None)):
            out.append(mod.build(n))
    return out
