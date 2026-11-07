#!/usr/bin/env bash
# Definition of done for step 1 (specs/step1_synthetic_completion_gap.md + specs/step1_amendment1.md).
# Usage: bash scripts/check.sh --stage N   (step 1: N in 0..3, cumulative; step 2: N in 4..6; step 3: N in 7..9; step 4: N in 10..12; step 5: N in 13..15; step 6: N in 16..18)
# Exit 0 = every criterion up to stage N holds. Do not edit to make it pass;
# if a check is wrong, stop and tell the user which one and why.
# v7 (2026-11-07): stages 16..18 = step 6 track (specs/step6_iqp4_scaling_n.md); step-5 checks only at 13..15.
# v6 (2026-11-07): stages 13..15 = step 5 track (specs/step5_iqp4_sigma_scan.md); step-4 checks only at 10..12.
# v5 (2026-11-06): stages 10..12 = step 4 track (specs/step4_misspec_finite_n.md); step-3 checks only at 7..9.
# v4 (2026-11-06): stages 7..9 = step 3 track (specs/step3_completion_vs_sigma.md).
# v3 (2026-11-06): stages 4..6 = step 2 track (specs/step2_sigma_boundary.md).
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
for f in specs/step1_synthetic_completion_gap.md specs/step1_amendment1.md specs/step2_sigma_boundary.md specs/step3_completion_vs_sigma.md specs/step4_misspec_finite_n.md specs/step5_iqp4_sigma_scan.md specs/step6_iqp4_scaling_n.md prereg/step1.md \
         .claude/settings.json .claude/hooks/guard.py .claude/hooks/stop_check.sh PROGRESS.md; do
  [ -f "$f" ] || die "harness" "missing $f"
done

s1=$stage; [ "$stage" -ge 4 ] && s1=0
if [ "$s1" -ge 1 ]; then
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

if [ "$s1" -ge 2 ]; then
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

if [ "$s1" -ge 3 ]; then
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


# ==== step 2 track (stages 4..6): specs/step2_sigma_boundary.md. Stage-0 checks above still apply;
# step-1 stages 1..3 are NOT required (step 1 ended by its kill rule).
step2_checks() {
  local st=$1
  f=specs/step2_sigma_boundary.md
  git ls-files --error-unmatch "$f" >/dev/null 2>&1 || die "s2-spec" "$f is not committed"
  git diff --quiet HEAD -- "$f" 2>/dev/null || die "s2-spec" "$f modified after commit (hypotheses are frozen)"
  [ -f src/step2/sweep.py ] || die "s2-layout" "missing src/step2/sweep.py"
  git diff --quiet HEAD -- src/step1/ 2>/dev/null || die "s2-closed" "src/step1/ has uncommitted edits (step 1 is a closed record)"
  [ -z "$(git diff --name-only e7480cc HEAD -- src/step1/ 2>/dev/null)" ] || die "s2-closed" "src/step1/ changed after step 1 closed (e7480cc)"
  "$PY" -m pytest -q tests/test_step2.py >/tmp/step2_pytest.txt 2>&1 || { die "s2-tests" "tests/test_step2.py fails"; tail -5 /tmp/step2_pytest.txt >&2; }
  grep -q "NotImplementedError" src/step2/sweep.py || die "s2-stub" "pauli_path_tv stub missing"
  s2_json() {  # $1 metrics.json
    "$PY" - "$1" <<'EOF' || die "s2-metrics" "$1 lacks required step-2 keys"
import json, sys
d = json.load(open(sys.argv[1]))
need = ["D3", "hi_order_frac", "collision_ratio_target", "clifford_dist_median_target", "versions"]
for m in ("O", "G"):
    need += [f"{m}_best_residual", f"{m}_n_success_restarts", f"{m}_success"]
miss = [k for k in need if k not in d]
if miss: print("missing:", miss, file=sys.stderr); sys.exit(1)
EOF
  }
  if [ "$st" -ge 5 ]; then
    for sg in 0.05 0.4; do
      p=results/step2/sigma_$sg/seed_0/metrics.json
      if [ -f "$p" ]; then s2_json "$p"; else die "s2-first" "missing $p"; fi
    done
    [ -f results/step2/PROJECTION.json ] || die "s2-budget" "missing results/step2/PROJECTION.json"
  fi
  if [ "$st" -ge 6 ]; then
    n=0
    for sg in 0.05 0.1 0.15 0.2 0.3 0.4 0.6; do for s in 0 1 2 3 4; do
      p=results/step2/sigma_$sg/seed_$s/metrics.json
      if [ -f "$p" ]; then n=$((n+1)); s2_json "$p"; fi
    done; done
    [ "$n" -ge 30 ] || die "s2-grid" "only $n/35 runs (30 allowed only with the named sigma=0.15 cut)"
    for fig in boundary proxies; do
      [ -f figures/step2/$fig.png ] && [ -f figures/step2/$fig.pdf ] || die "s2-figures" "missing figures/step2/$fig.{png,pdf}"
    done
    [ -f results/step2/table.csv ] || die "s2-artifacts" "missing results/step2/table.csv"
    S=results/step2/SUMMARY.md
    if [ -f $S ]; then
      grep -qF "Oracle-support fits are a diagnostic of the landscape, not a practical method; n = 12 proxies are not hardness evidence." $S \
        || die "s2-summary" "SUMMARY lacks the required oracle/proxy sentence"
      for h in H1 H2 H3 H4 H5; do grep -qE "$h.*(PASS|FAIL)" $S || die "s2-summary" "SUMMARY does not mark $h PASS/FAIL"; done
    else die "s2-summary" "missing $S"; fi
  fi
}


# ==== step 3 track (stages 7..9): specs/step3_completion_vs_sigma.md. Stage-0 checks still apply;
# step-1 and step-2 stages are NOT required (both ended by their kill rules).
step3_checks() {
  local st=$1
  f=specs/step3_completion_vs_sigma.md
  git ls-files --error-unmatch "$f" >/dev/null 2>&1 || die "s3-spec" "$f is not committed"
  git diff --quiet HEAD -- "$f" 2>/dev/null || die "s3-spec" "$f modified after commit (hypotheses are frozen)"
  [ -f src/step3/run.py ] || die "s3-layout" "missing src/step3/run.py"
  git diff --quiet HEAD -- src/step1/ src/step2/ 2>/dev/null || die "s3-closed" "src/step1 or src/step2 has uncommitted edits (closed records)"
  [ -z "$(git diff --name-only 163fe19 HEAD -- src/step1/ src/step2/ 2>/dev/null)" ] || die "s3-closed" "src/step1 or src/step2 changed after step 2 closed (163fe19)"
  "$PY" -m pytest -q tests/test_step3.py >/tmp/step3_pytest.txt 2>&1 || { die "s3-tests" "tests/test_step3.py fails"; tail -5 /tmp/step3_pytest.txt >&2; }
  s3_json() {  # $1 metrics.json
    "$PY" - "$1" <<'EOF' || die "s3-metrics" "$1 lacks required step-3 keys"
import json, sys
d = json.load(open(sys.argv[1]))
need = ["G_maxent", "G_uniform", "D3", "hi_order_frac", "collision_ratio_target", "clifford_dist_median_target", "versions"]
for m in ("O", "G"):
    need += [f"{m}_G", f"{m}_R", f"{m}_train_residual", f"{m}_restart_residuals", f"{m}_restart_G"]
miss = [k for k in need if k not in d]
if miss: print("missing:", miss, file=sys.stderr); sys.exit(1)
EOF
  }
  if [ "$st" -ge 8 ]; then
    for t in iqp maxent_proj; do for sg in 0.05 0.4; do
      p=results/step3/$t/sigma_$sg/seed_0/metrics.json
      if [ -f "$p" ]; then s3_json "$p"; else die "s3-first" "missing $p"; fi
    done; done
    [ -f results/step3/PROJECTION.json ] || die "s3-budget" "missing results/step3/PROJECTION.json"
  fi
  if [ "$st" -ge 9 ]; then
    n=0; nproj=0
    for t in iqp maxent_proj; do for sg in 0.05 0.1 0.2 0.3 0.4 0.6; do for s in 0 1 2 3 4; do
      p=results/step3/$t/sigma_$sg/seed_$s/metrics.json
      if [ -f "$p" ]; then n=$((n+1)); [ "$t" = maxent_proj ] && nproj=$((nproj+1)); s3_json "$p"; fi
    done; done; done
    [ "$n" -ge 50 ] || die "s3-grid" "only $n/60 instances (50 allowed only with the named sigma=0.6 cut)"
    [ "$nproj" -ge 25 ] || die "s3-grid" "only $nproj maxent_proj instances; the paired control is never cut"
    for fig in ratio_vs_sigma room_and_proxies residual_vs_G; do
      [ -f figures/step3/$fig.png ] && [ -f figures/step3/$fig.pdf ] || die "s3-figures" "missing figures/step3/$fig.{png,pdf}"
    done
    [ -f results/step3/table.csv ] || die "s3-artifacts" "missing results/step3/table.csv"
    S=results/step3/SUMMARY.md
    if [ -f $S ]; then
      grep -qF "Step 3 was designed after the step 1–2 diagnostics; C1 replicates data already seen; oracle-support fits are a landscape diagnostic; n = 12 proxies are not hardness evidence." $S \
        || die "s3-summary" "SUMMARY lacks the required designed-after sentence"
      for h in K1 K2 C1 M1 M2 M3; do grep -qE "$h.*(PASS|FAIL)" $S || die "s3-summary" "SUMMARY does not mark $h PASS/FAIL"; done
    else die "s3-summary" "missing $S"; fi
  fi
}

[ "$stage" -ge 4 ] && [ "$stage" -le 6 ] && step2_checks "$stage"

# ==== step 4 track (stages 10..12): specs/step4_misspec_finite_n.md. Stage-0 checks still apply;
# steps 1-3 are closed records (step 3 closed at 372ad38).
S4_SENT="Step 4 was designed after step 3; R1 replicates data already seen; G is the generic IQP (no oracle); n = 12 proxies are not hardness evidence."
step4_checks() {
  local st=$1
  f=specs/step4_misspec_finite_n.md
  git ls-files --error-unmatch "$f" >/dev/null 2>&1 || die "s4-spec" "$f is not committed"
  git diff --quiet HEAD -- "$f" 2>/dev/null || die "s4-spec" "$f modified after commit (hypotheses are frozen)"
  for p in src/step4/run.py src/step4/targets.py tests/test_step4.py; do [ -f $p ] || die "s4-layout" "missing $p"; done
  git diff --quiet HEAD -- src/step1/ src/step2/ src/step3/ 2>/dev/null || die "s4-closed" "src/step1..3 has uncommitted edits (closed records)"
  git cat-file -e 372ad38 2>/dev/null || die "s4-closed" "commit 372ad38 (step 3 close) not in history; branch step4 from step3-ratio"
  [ -z "$(git diff --name-only 372ad38 HEAD -- src/step1/ src/step2/ src/step3/ 2>/dev/null)" ] || die "s4-closed" "src/step1..3 changed after step 3 closed (372ad38)"
  "$PY" -m pytest -q tests/test_step4.py >/tmp/step4_pytest.txt 2>&1 || { die "s4-tests" "tests/test_step4.py fails"; tail -5 /tmp/step4_pytest.txt >&2; }
  C=results/step4/calibration.json
  if [ -f $C ]; then
    "$PY" - $C <<'EOF' || die "s4-calib" "$C must record D3 for every delta in {0.2,0.4,0.6,0.8} and chosen_delta"
import json, sys
d = json.load(open(sys.argv[1]))
assert d.get("chosen_delta") in (0.2, 0.4, 0.6, 0.8), "chosen_delta"
c = {float(k): v for k, v in d["D3_by_delta"].items()}
assert set(c) == {0.2, 0.4, 0.6, 0.8}, "D3_by_delta keys"
assert not any(k.startswith("R") or "G_" in k for k in d), "calibration must not compute R or G"
EOF
  else die "s4-calib" "missing $C"; fi
  s4_json() {  # $1 metrics.json
    "$PY" - "$1" <<'EOF' || die "s4-metrics" "$1 lacks required step-4 keys"
import json, sys
d = json.load(open(sys.argv[1]))
need = ["G_iqp", "G_maxent", "G_uniform", "R", "G_train_residual", "G_restart_residuals", "G_restart_G",
        "maxent_train_residual", "D3", "noise_floor", "hi_order_frac", "collision_ratio_target",
        "versions", "total_seconds"]
miss = [k for k in need if k not in d]
if miss: print("missing:", miss, file=sys.stderr); sys.exit(1)
if len(d["G_restart_residuals"]) < 3: print("fewer than 3 G restarts (never cut)", file=sys.stderr); sys.exit(1)
EOF
  }
  cell() { [ "$1" = mix ] && echo "results/step4/mix/none/N_$2" || echo "results/step4/$1/sigma_$3/N_$2"; }
  if [ "$st" -ge 11 ]; then
    for p in results/step4/iqp4/sigma_0.2/N_10000/seed_0/metrics.json results/step4/mix/none/N_10000/seed_0/metrics.json; do
      if [ -f "$p" ]; then s4_json "$p"; else die "s4-first" "missing $p"; fi
    done
    [ -f results/step4/PROJECTION.json ] || die "s4-budget" "missing results/step4/PROJECTION.json"
  fi
  if [ "$st" -ge 12 ]; then
    n=0
    for t in iqp iqp4 maxent_proj mix; do for N in inf 1000 10000 100000; do for sg in 0.1 0.2; do
      [ $t = mix ] && [ $sg = 0.1 ] && continue
      c=$(cell $t $N $sg); k=0
      for s in 0 1 2 3 4; do p=$c/seed_$s/metrics.json; [ -f $p ] && { k=$((k+1)); s4_json $p; }; done
      n=$((n+k))
      [ $k -eq 0 ] || [ $k -eq 5 ] || die "s4-grid" "$c has $k/5 seeds (seeds are never cut)"
    done; done; done
    [ "$n" -ge 60 ] || die "s4-grid" "only $n/140 instances (fewer than the two named cuts allow)"
    for N in 10000 100000; do for s in 0 1 2 3 4; do
      [ -f results/step4/maxent_proj/sigma_0.2/N_$N/seed_$s/metrics.json ] || die "s4-grid" "maxent_proj sigma=0.2 N=$N seed $s missing (K is never cut)"
    done; done
    for N in inf 100000; do for s in 0 1 2 3 4; do
      [ -f results/step4/iqp4/sigma_0.2/N_$N/seed_$s/metrics.json ] || die "s4-grid" "iqp4 sigma=0.2 N=$N seed $s missing (P1/F2 are never cut)"
    done; done
    for fig in ratio_vs_N ratio_at_inf noise_floor; do
      [ -f figures/step4/$fig.png ] && [ -f figures/step4/$fig.pdf ] || die "s4-figures" "missing figures/step4/$fig.{png,pdf}"
    done
    [ -f results/step4/table.csv ] || die "s4-artifacts" "missing results/step4/table.csv"
    S=results/step4/SUMMARY.md
    if [ -f $S ]; then
      grep -qF "$S4_SENT" $S || die "s4-summary" "SUMMARY lacks the required designed-after sentence"
      for h in K R1 P1 P2 F1 F2; do grep -qE "(^|[^A-Za-z0-9])$h([^A-Za-z0-9]).*(PASS|FAIL)" $S || die "s4-summary" "SUMMARY does not mark $h PASS/FAIL"; done
    else die "s4-summary" "missing $S"; fi
  fi
}

[ "$stage" -ge 7 ] && [ "$stage" -le 9 ] && step3_checks "$stage"

# ==== step 5 track (stages 13..15): specs/step5_iqp4_sigma_scan.md. Steps 1-4 are closed (step 4 closed at 1c6921e).
S5_SENT="Step 5 was designed after step 4; Q0 replicates data already seen; G is the generic IQP (no oracle); n = 12 proxies are not hardness evidence."
step5_checks() {
  local st=$1
  f=specs/step5_iqp4_sigma_scan.md
  git ls-files --error-unmatch "$f" >/dev/null 2>&1 || die "s5-spec" "$f is not committed"
  git diff --quiet HEAD -- "$f" 2>/dev/null || die "s5-spec" "$f modified after commit (hypotheses are frozen)"
  for p in src/step5/run.py src/step5/targets.py tests/test_step5.py; do [ -f $p ] || die "s5-layout" "missing $p"; done
  git cat-file -e 1c6921e 2>/dev/null || die "s5-closed" "commit 1c6921e (step 4 close) not in history; branch step5 from step4-misspec"
  git diff --quiet HEAD -- src/step1/ src/step2/ src/step3/ src/step4/ 2>/dev/null || die "s5-closed" "src/step1..4 has uncommitted edits (closed records)"
  [ -z "$(git diff --name-only 1c6921e HEAD -- src/step1/ src/step2/ src/step3/ src/step4/ 2>/dev/null)" ] || die "s5-closed" "src/step1..4 changed after step 4 closed (1c6921e)"
  "$PY" -m pytest -q tests/test_step5.py >/tmp/step5_pytest.txt 2>&1 || { die "s5-tests" "tests/test_step5.py fails"; tail -5 /tmp/step5_pytest.txt >&2; }
  s5_json() {  # $1 metrics.json, $2 target
    "$PY" - "$1" "$2" <<'EOF' || die "s5-metrics" "$1 lacks required step-5 keys"
import json, sys
d = json.load(open(sys.argv[1]))
need = ["target", "sigma", "N", "seed", "G_iqp", "G_maxent", "R", "G_train_residual", "G_restart_residuals",
        "G_restart_G", "maxent_train_residual", "D3", "noise_floor", "collision_ratio_target", "versions", "total_seconds"]
if sys.argv[2] == "iqp4f": need.append("tau")
miss = [k for k in need if k not in d]
if miss: print("missing:", miss, file=sys.stderr); sys.exit(1)
if len(d["G_restart_residuals"]) < 3: print("fewer than 3 G restarts (never cut)", file=sys.stderr); sys.exit(1)
if sys.argv[2] == "iqp4f" and d["tau"] != 0.2: print("tau must be 0.2", file=sys.stderr); sys.exit(1)
EOF
  }
  if [ "$st" -ge 14 ]; then
    for t in iqp4 iqp4f; do p=results/step5/$t/sigma_0.25/N_10000/seed_0/metrics.json
      if [ -f "$p" ]; then s5_json "$p" $t; else die "s5-first" "missing $p (timing instance)"; fi
    done
    [ -f results/step5/PROJECTION.json ] || die "s5-budget" "missing results/step5/PROJECTION.json"
    "$PY" - <<'EOF' || die "s5-repro" "iqp4 sigma=0.2 N=inf seed 0 does not reproduce step 4 (R rel. diff > 1e-6)"
import json, os
a = "results/step5/iqp4/sigma_0.2/N_inf/seed_0/metrics.json"; b = "results/step4/iqp4/sigma_0.2/N_inf/seed_0/metrics.json"
assert os.path.exists(a) and os.path.exists(b), "missing " + (a if not os.path.exists(a) else b)
ra, rb = json.load(open(a))["R"], json.load(open(b))["R"]
assert abs(ra - rb) <= 1e-6 * abs(rb), (ra, rb)
EOF
  fi
  if [ "$st" -ge 15 ]; then
    n=0
    for t in iqp4 iqp4f; do for N in inf 10000; do for sg in 0.1 0.125 0.15 0.175 0.2 0.25; do
      c=results/step5/$t/sigma_$sg/N_$N; k=0
      for s in 0 1 2 3 4; do p=$c/seed_$s/metrics.json; [ -f $p ] && { k=$((k+1)); s5_json $p $t; }; done
      n=$((n+k))
      [ $k -eq 0 ] || [ $k -eq 5 ] || die "s5-grid" "$c has $k/5 seeds (seeds are never cut)"
      [ $N = inf ] && [ $k -ne 5 ] && die "s5-grid" "$c incomplete (N = inf cells are never cut)"
    done; done; done
    [ "$n" -ge 60 ] || die "s5-grid" "only $n/120 instances"
    "$PY" - <<'EOF' || die "s5-repro" "iqp4 at sigma 0.1/0.2, N=inf does not reproduce step 4"
import json
for sg in ("0.1", "0.2"):
    for s in range(5):
        a = json.load(open(f"results/step5/iqp4/sigma_{sg}/N_inf/seed_{s}/metrics.json"))["R"]
        b = json.load(open(f"results/step4/iqp4/sigma_{sg}/N_inf/seed_{s}/metrics.json"))["R"]
        assert abs(a - b) <= 1e-6 * abs(b), (sg, s, a, b)
EOF
    for fig in R_vs_sigma G_vs_sigma; do
      [ -f figures/step5/$fig.png ] && [ -f figures/step5/$fig.pdf ] || die "s5-figures" "missing figures/step5/$fig.{png,pdf}"
    done
    for a in table.csv verdicts.json; do [ -f results/step5/$a ] || die "s5-artifacts" "missing results/step5/$a"; done
    S=results/step5/SUMMARY.md
    if [ -f $S ]; then
      grep -qF "$S5_SENT" $S || die "s5-summary" "SUMMARY lacks the required designed-after sentence"
      for h in Q0 Q1 Q2 Q3 Q4 Q5; do grep -qE "(^|[^A-Za-z0-9])$h([^A-Za-z0-9]).*(PASS|FAIL)" $S || die "s5-summary" "SUMMARY does not mark $h PASS/FAIL"; done
    else die "s5-summary" "missing $S"; fi
  fi
}

[ "$stage" -ge 10 ] && [ "$stage" -le 12 ] && step4_checks "$stage"

# ==== step 6 track (stages 16..18): specs/step6_iqp4_scaling_n.md. Steps 1-5 are closed (step 5 closed at bdc4cea).
S6_SENT="Step 6 was designed after step 5; the n = 12 reference is data already seen; G is the generic IQP (no oracle); n ≤ 16 proxies are not hardness evidence."
step6_checks() {
  local st=$1
  f=specs/step6_iqp4_scaling_n.md
  git ls-files --error-unmatch "$f" >/dev/null 2>&1 || die "s6-spec" "$f is not committed"
  git diff --quiet HEAD -- "$f" 2>/dev/null || die "s6-spec" "$f modified after commit (hypotheses are frozen)"
  for p in src/step6/run.py tests/test_step6.py; do [ -f $p ] || die "s6-layout" "missing $p"; done
  git cat-file -e bdc4cea 2>/dev/null || die "s6-closed" "commit bdc4cea (step 5 close) not in history; branch step6 from step5-sigma"
  git diff --quiet HEAD -- src/step1/ src/step2/ src/step3/ src/step4/ src/step5/ 2>/dev/null || die "s6-closed" "src/step1..5 has uncommitted edits (closed records)"
  [ -z "$(git diff --name-only bdc4cea HEAD -- src/step1/ src/step2/ src/step3/ src/step4/ src/step5/ 2>/dev/null)" ] || die "s6-closed" "src/step1..5 changed after step 5 closed (bdc4cea)"
  "$PY" -m pytest -q tests/test_step6.py >/tmp/step6_pytest.txt 2>&1 || { die "s6-tests" "tests/test_step6.py fails"; tail -5 /tmp/step6_pytest.txt >&2; }
  s6_json() {  # $1 metrics.json, $2 n
    "$PY" - "$1" "$2" <<'EOF' || die "s6-metrics" "$1 lacks required step-6 keys"
import json, sys
d = json.load(open(sys.argv[1]))
need = ["n", "sigma", "seed", "G_iqp", "G_maxent", "R", "G_train_residual", "G_restart_residuals", "G_restart_G",
        "G_restart_nit", "G_n_params", "maxent_train_residual", "D3", "collision_ratio_target", "versions", "total_seconds"]
miss = [k for k in need if k not in d]
if miss: print("missing:", miss, file=sys.stderr); sys.exit(1)
if len(d["G_restart_residuals"]) < 3: print("fewer than 3 G restarts (never cut)", file=sys.stderr); sys.exit(1)
n = int(sys.argv[2])
if d["n"] != n: print("n mismatch", file=sys.stderr); sys.exit(1)
want = n + n * (n - 1) // 2 + n * (n - 1) * (n - 2) // 6
if d["G_n_params"] != want: print(f"G_n_params {d['G_n_params']} != {want}", file=sys.stderr); sys.exit(1)
EOF
  }
  if [ "$st" -ge 17 ]; then
    for n in 14 16; do p=results/step6/n_$n/sigma_0.2/seed_0/metrics.json
      if [ -f "$p" ]; then s6_json "$p" $n; else die "s6-first" "missing $p (timing instance)"; fi
    done
    [ -f results/step6/PROJECTION.json ] || die "s6-budget" "missing results/step6/PROJECTION.json"
  fi
  if [ "$st" -ge 18 ]; then
    tot=0
    for n in 14 16; do for sg in 0.125 0.15 0.175 0.2 0.25; do
      c=results/step6/n_$n/sigma_$sg; k=0
      for s in 0 1 2 3 4; do p=$c/seed_$s/metrics.json; [ -f $p ] && { k=$((k+1)); s6_json $p $n; }; done
      tot=$((tot+k))
      [ $k -eq 0 ] || [ $k -eq 5 ] || die "s6-grid" "$c has $k/5 seeds (seeds are never cut)"
      if [ $n = 14 ] || [ $sg = 0.15 ] || [ $sg = 0.175 ] || [ $sg = 0.2 ]; then
        [ $k -eq 5 ] || die "s6-grid" "$c incomplete (never cut: all n = 14 cells and n = 16 at sigma 0.15/0.175/0.2)"
      fi
    done; done
    [ "$tot" -ge 40 ] || die "s6-grid" "only $tot/50 instances"
    for fig in R_vs_sigma_by_n G_vs_sigma_by_n collision_vs_n; do
      [ -f figures/step6/$fig.png ] && [ -f figures/step6/$fig.pdf ] || die "s6-figures" "missing figures/step6/$fig.{png,pdf}"
    done
    for a in table.csv verdicts.json; do [ -f results/step6/$a ] || die "s6-artifacts" "missing results/step6/$a"; done
    S=results/step6/SUMMARY.md
    if [ -f $S ]; then
      grep -qF "$S6_SENT" $S || die "s6-summary" "SUMMARY lacks the required designed-after sentence"
      for h in S1 S2 S3 S4; do grep -qE "(^|[^A-Za-z0-9])$h([^A-Za-z0-9]).*(PASS|FAIL)" $S || die "s6-summary" "SUMMARY does not mark $h PASS/FAIL"; done
    else die "s6-summary" "missing $S"; fi
  fi
}

[ "$stage" -ge 13 ] && [ "$stage" -le 15 ] && step5_checks "$stage"
[ "$stage" -ge 16 ] && step6_checks "$stage"

[ $fail -eq 0 ] && echo "ALL CHECKS PASS (stage $stage)"
exit $fail
