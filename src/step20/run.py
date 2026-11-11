"""Step 20: held-out order-4 validation gate on fresh instances (specs/step20_heldout_val_gate.md).

  python -m src.step20.run --qec RUN | --iqp4 SEED | --all | --report | --verify
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

from src.step19 import data as D19
from src.step20 import pilot as P

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "step20"
SPEC = "specs/step20_heldout_val_gate.md"
CLOSED_AT = "28509d8"
QEC = tuple(f"surface_code_b{b}_d3_r05_center_{c}" for c in ("3_5", "5_3", "5_7", "7_5") for b in ("X", "Z"))
IQP4 = tuple(range(310, 320))
STOP_LOSS_H = 2.5
SENT = ("Step 20 was designed after step 19 and a 12-instance development pilot; the 18 tested instances "
        "(8 QEC d3_r05 runs, iqp4 seeds 310–319) were never fit before; the validation rows never enter a fit.")


def path(name: str) -> Path:
    return RESULTS / name / "metrics.json"


def names():
    return list(QEC) + [f"iqp4_seed_{s}" for s in IQP4]


def compute() -> dict:
    ds = [json.loads(path(x).read_text()) for x in names() if path(x).exists()]
    if len(ds) < len(names()):
        return {"complete": False, "verdicts": {k: {"PASS": None} for k in ("W1", "W2", "W3")}}
    R = np.array([d["R"] for d in ds])
    new = np.array([d["picks_val4"] for d in ds])
    old = np.array([d["picks14"] for d in ds])
    win = R < 1
    l_new, l_old = int((new & ~win).sum()), int((old & ~win).sum())
    kept = int((new & win).sum())
    v = {"W1": {"losses": l_new, "picks": int(new.sum()), "PASS": bool(l_new <= 1),
                "statement": "new gate losses <= 1 of 18"},
         "W2": {"losses_new": l_new, "losses_step14": l_old, "PASS": bool(l_new < l_old),
                "statement": "new gate has fewer losses than the step 14 gate"},
         "W3": {"wins": int(win.sum()), "kept": kept, "PASS": (bool(kept >= 0.5 * win.sum()) if win.any() else None),
                "statement": "new gate keeps >= 50% of the R < 1 instances"}}
    rows = []
    for d in ds:
        dl = {l: d["val_iqp"][l] - d["val_maxent"][l] for l in ("4", "5", "6")}
        rows.append({"name": d.get("run", f"iqp4 {d['seed']}").replace("surface_code_", ""), "kind": d["kind"],
                     "R": d["R"], "R_raw": d.get("R_raw"), "picks14": d["picks14"], "picks_val4": d["picks_val4"],
                     "d4": dl["4"], "d5": dl["5"], "d6": dl["6"],
                     "pooled_pick": bool(d["picks14"] and np.mean(list(dl.values())) < 0), "excess": d["excess"]})
    fam = {k: {"n": sum(r["kind"] == k for r in rows), "wins": sum(r["kind"] == k and r["R"] < 1 for r in rows),
               "losses_step14": sum(r["kind"] == k and r["picks14"] and r["R"] >= 1 for r in rows),
               "losses_new": sum(r["kind"] == k and r["picks_val4"] and r["R"] >= 1 for r in rows),
               "kept": sum(r["kind"] == k and r["picks_val4"] and r["R"] < 1 for r in rows)} for k in ("qec", "iqp4")}
    pooled_disagree = sum(r["pooled_pick"] != r["picks_val4"] for r in rows)
    return {"complete": True, "verdicts": v, "rows": rows, "families": fam, "pooled_disagree": pooled_disagree}


def report() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    c = compute()
    (RESULTS / "verdicts.json").write_text(json.dumps(c, indent=2))
    mark = lambda x: "**PASS**" if x else ("**FAIL**" if x is False else "n/a")
    v = c["verdicts"]
    L = [SENT, "", f"Spec: `{SPEC}`.", "", "| ID | Statement | Counts | Verdict |", "|---|---|---|---|"]
    if not c["complete"]:
        L.append("incomplete")
    else:
        L += [f"| W1 | {v['W1']['statement']} | picks {v['W1']['picks']}, losses {v['W1']['losses']} | {mark(v['W1']['PASS'])} |",
              f"| W2 | {v['W2']['statement']} | new {v['W2']['losses_new']} vs step 14 {v['W2']['losses_step14']} | {mark(v['W2']['PASS'])} |",
              f"| W3 | {v['W3']['statement']} | kept {v['W3']['kept']} of {v['W3']['wins']} | {mark(v['W3']['PASS'])} |",
              "", "Per family (exploratory):", "", "| family | n | R < 1 | step 14 losses | new losses | wins kept |",
              "|---|---|---|---|---|---|"]
        for k, f in c["families"].items():
            L.append(f"| {k} | {f['n']} | {f['wins']} | {f['losses_step14']} | {f['losses_new']} | {f['kept']} |")
        L += ["", f"Pooled order-4–6 rule disagrees with the order-4 rule on {c['pooled_disagree']}/18.", "",
              "| instance | R | R_raw | step 14 picks | new picks | d4 | d5 | d6 | excess |", "|---|---|---|---|---|---|---|---|---|"]
        for r in c["rows"]:
            rr = f"{r['R_raw']:.3g}" if r["R_raw"] is not None else "—"
            L.append(f"| {r['name']} | {r['R']:.3g} | {rr} | {r['picks14']} | {r['picks_val4']} | {r['d4']:+.2e} | "
                     f"{r['d5']:+.2e} | {r['d6']:+.2e} | {r['excess']:.3g} |")
    txt = "\n".join(L) + "\n"
    (RESULTS / "SUMMARY.md").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


def verify() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    bad = []
    chk = lambda ok, name, msg: (print(("ok   " if ok else "FAIL ") + f"[{name}] {msg}"), ok or bad.append(name))
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    chk(git("ls-files", "--error-unmatch", SPEC).returncode == 0 and git("diff", "--quiet", "HEAD", "--", SPEC).returncode == 0,
        "spec", f"{SPEC} committed and unchanged")
    closed = [f"src/step{i}/" for i in range(1, 20)] + ["src/step20/core.py"]
    chk(git("diff", "--name-only", CLOSED_AT, "HEAD", "--", *closed).stdout.strip() == ""
        and git("diff", "--quiet", "HEAD", "--", *closed).returncode == 0, "closed",
        f"src/step1..19 and step20/core.py unchanged since {CLOSED_AT}")
    ok = True
    for x in names():
        if not path(x).exists():
            ok = False
            print(f"     missing {x}")
            continue
        d = json.loads(path(x).read_text())
        if d["kind"] == "qec":
            good = (d["run"] == x and d["seed"] == P.SPLIT_SEED and d["N_train"] == P.N_TRAIN and d["N_fit"] == 24_000
                    and d["N_val"] == 6_000 and d["N_test"] == 20_000 and d["zip_md5"] == D19.ZIP_MD5)
        else:
            good = d["N_total"] == P.N_IQP4 and d["N_fit"] == 100_000 and d["N_val"] == 25_000 and d["sigma"] == P.SIGMA
        if not (good and d["n_restarts"] == 3):
            ok = False
            print(f"     bad {x}")
    chk(ok, "grid", "18 instances with the frozen N, restarts, md5")
    S = RESULTS / "SUMMARY.md"
    txt = S.read_text(encoding="utf-8") if S.exists() else ""
    chk(txt.startswith(SENT), "summary", "SUMMARY opens with the required sentence")
    chk(all(re.search(rf"\| W{i} \|.*\| \*\*(PASS|FAIL)\*\* \|", txt) or (i == 3 and "| W3 |" in txt and "n/a" in txt)
            for i in (1, 2, 3)), "summary", "W1–W3 marked")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step20.py"], cwd=ROOT, capture_output=True, text=True)
    chk(t.returncode == 0, "tests", (t.stdout.strip().splitlines() or ["no output"])[-1])
    print("ALL CHECKS PASS (step 20)" if not bad else f"FAILED: {sorted(set(bad))}")
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--qec")
    ap.add_argument("--iqp4", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if a.qec:
        assert a.qec in QEC
        P.save(P.run_qec(a.qec), path(a.qec))
    elif a.iqp4 is not None:
        assert a.iqp4 in IQP4
        P.save(P.run_iqp4(a.iqp4), path(f"iqp4_seed_{a.iqp4}"))
    elif a.all:
        jobs = [("src.step20.run", ["--qec", r]) for r in QEC if not path(r).exists()]
        jobs += [("src.step20.run", ["--iqp4", str(s)]) for s in IQP4 if not path(f"iqp4_seed_{s}").exists()]
        return P.launch(jobs, STOP_LOSS_H)
    elif a.report:
        return report()
    elif a.verify:
        return verify()
    return 0


if __name__ == "__main__":
    sys.exit(main())
