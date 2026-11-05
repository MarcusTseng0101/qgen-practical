"""Model discovery: every module here that defines build(n, **options) is a model.
build must accept (and may ignore) run options it does not use, e.g. gens="sparse"."""
import importlib
import pkgutil


def discover(n: int, **options) -> list:
    out = []
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        mod = importlib.import_module(f"{__name__}.{info.name}")
        if callable(getattr(mod, "build", None)):
            out.append(mod.build(n, **options))
    return out
