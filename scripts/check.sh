#!/usr/bin/env bash
# Definition of done for step 1 (specs/step1_synthetic_completion_gap.md + specs/step1_amendment1.md).
# Usage: bash scripts/check.sh --stage N   (stages are cumulative; N in 0..3)
# Exit 0 = every criterion up to stage N holds. Do not edit to make it pass;
# if a check is wrong, stop and tell the user which one and why.
# v2 (2026-11-06, amendment 1): sparse IQP (n_params_iqp <= n_params_maxent), maxent_proj control,
# amendment frozen once committed, import-only arch grep, .py-only isolation grep.
set -u
cd "$(dirname "$0")/.."
stage=0
[ "${1:-}" = "--stage" ] && stage="${2:-0}"
fail=0
die() { echo "CHECK FAILED [$1]: $2" >&2; fail=1; }
PY=python; [ -x .venv/Scripts/python ] && PY=.venv/Scripts/python; [ -x .venv/bin/python ] && PY=.venv/bin/python
TARGETS="biased maxent_proj random"

# ---- stage 0: harness and frozen predictions in place
for f in specs/step1_synthetic_completion_gap.md specs/step1_amendment1.md prereg/step1.md \
         .claude/settings.json .claude/hooks/guard.py .claude/hooks/stop_check.sh PROGRESS.md; do
  [ -f "$f" ] || die "harness" "missing $f"
done

if [ "$stage" -ge 1 ]; then
  for f in prereg/step1.md specs/step1_amendment1.md; do
    git ls-files --error-unmatch "$f" >/dev/null 2>&1 || die "prereg" "$f is not committed"
    git diff --quiet HEAD -- "$f" 2>/dev/null || die "prereg" "$f modified after commit (predictions are frozen)"
  done
  [ -f requirements.txt ] || die "stack" "missing requirements.txt"
  grep -qiE "^(jax|torch|pennylane|iqpopt)" requirements.txt 2>/dev/null && die "stack" "forbidden framework in requirements.txt"
  [ -f src/step1/metrics.py ] || die "layout" "missing src/step1/metrics.py"
  # hard architectural rule: real import statements only (not docstrings)
  grep -qE "^[[:space:]]*(from|import)[[:space:]].*models" src/step1/metrics.py 2>/dev/null && die "arch-rule" "metrics.py imports from src/step1/models"
  # isolation: no code path into qgen-iqp-A (imports, sys.path, file opens); .py files only
  grep -rqE --include='*.py' "(^[[:space:]]*(from|import)[[:space:]].*qgen.?iqp|sys\.path.*qgen.?iqp|open\(.*qgen.?iqp)" src/ 2>/dev/null \
    && die "isolation" "src/ has a code path into the qgen-iqp-A repo"
  "$PY" -m pytest -q tests/test_core.py >/tmp/step1_pytest.txt 2>&1 || { die "core-tests" "tests/test_core.py fails"; tail -5 /tmp/step1_pytest.txt >&2; }
  for t in fwht cos statevector finite maxent; do
    grep -qi "$t" tests/test_core.py 2>/dev/null || die "core-tests" "tests/test_core.py has no '$t' test (FM1 / gradient / maxent)"
  done
  grep -qiE "nnls|selector" tests/test_core.py 2>/dev/null || die "core-tests" "no sparse-selector test (amendment 1, build step 2)"
fi

need_keys='R G_iqp G_maxent G_uniform per_level train_residual_iqp train_residual_maxent gap_valid tv_iqp tv_maxent clifford_dist_median collision_ratio_target jacobian_rank n_params_iqp n_params_maxent versions'
check_json() {  # $1 = metrics.json, $2 = 1 if amended (sparse) run
  "$PY" - "$1" "$2" $need_keys <<'EOF' || die "metrics" "$1 lacks required keys, or n_params_iqp > n_params_maxent, or no support info"
import json, sys
d = json.load(open(sys.argv[1])); amended = sys.argv[2] == "1"
miss = [k for k in sys.argv[3:] if k not in d]
if miss: print("missing:", miss, file=sys.stderr); sys.exit(1)
if d["n_params_iqp"] > d["n_params_maxent"]: sys.exit(1)
if amended and not all(k in d for k in ("gens_mode", "support_recall", "support_precision")): sys.exit(1)
if amended and d["gens_mode"] != "sparse": sys.exit(1)
EOF
}

if [ "$stage" -ge 2 ]; then
  for t in $TARGETS; do
    f=results/step1/$t/Ninf/seed_0/metrics.json
    if [ -f "$f" ]; then check_json "$f" 1; else die "ninf-runs" "missing $f"; fi
  done
  tmp=$(mktemp -d)
  "$PY" -m src.step1.run --target maxent_proj --N inf --seed 0 --out "$tmp/a" >/dev/null 2>&1
  "$PY" -m src.step1.run --target maxent_proj --N inf --seed 0 --out "$tmp/b" >/dev/null 2>&1
  "$PY" - "$tmp/a/metrics.json" "$tmp/b/metrics.json" <<'EOF' || die "repro" "same seed gives different metrics (ignoring timing fields)"
import json, sys
a, b = (json.load(open(p)) for p in sys.argv[1:])
drop = lambda d: {k: v for k, v in d.items() if "time" not in k and "second" not in k}
sys.exit(0 if drop(a) == drop(b) else 1)
EOF
fi

if [ "$stage" -ge 3 ]; then
  [ -f results/step1/PROJECTION.json ] || die "budget" "missing results/step1/PROJECTION.json"
  n=0
  for t in $TARGETS; do for N in Ninf N1000 N10000 N100000; do for s in 0 1 2 3 4; do
    f=results/step1/$t/$N/seed_$s/metrics.json
    if [ -f "$f" ]; then n=$((n+1)); check_json "$f" 1; fi
  done; done; done
  [ "$n" -ge 60 ] || echo "note: $n/60 runs (fewer is allowed only if PROGRESS.md names the budget cut)" >&2
  [ "$n" -ge 40 ] || die "grid" "only $n/60 runs"
  for fig in ratio_vs_N per_level_error clifford_dist; do
    [ -f figures/step1/$fig.png ] && [ -f figures/step1/$fig.pdf ] || die "figures" "missing figures/step1/$fig.{png,pdf}"
  done
  S=results/step1/SUMMARY.md
  [ -f results/step1/table.csv ] || die "artifacts" "missing results/step1/table.csv"
  if [ -f $S ]; then
    grep -qF "This is a pipeline sanity check on synthetic IQP-shaped targets at n = 12 and is not evidence of advantage on real data." $S || die "summary" "SUMMARY lacks the required not-evidence sentence"
    grep -qiF "amendment 1 (post-hoc" $S || die "summary" "SUMMARY does not label the amended pipeline as post-hoc"
    for p in "P1′" "P2′" "P3′" "P4′" "P5′" "P6′"; do
      grep -qE "$p.*(PASS|FAIL)" $S || die "summary" "SUMMARY does not mark $p PASS/FAIL"
    done
    for p in P1 P2 P3 P4 P5; do
      grep -qE "(^|[^′])$p[^′].*(PASS|FAIL|NOT EVALUABLE)" $S || die "summary" "SUMMARY does not report original $p (PASS/FAIL/NOT EVALUABLE)"
    done
  else die "summary" "missing $S"; fi
fi

[ $fail -eq 0 ] && echo "ALL CHECKS PASS (stage $stage)"
exit $fail
