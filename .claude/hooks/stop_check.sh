#!/usr/bin/env bash
# Block "done" until scripts/check.sh passes for the current stage (.harness/STAGE, set by the user).
input=$(cat)
echo "$input" | grep -q '"stop_hook_active": *true' && exit 0
cd "${CLAUDE_PROJECT_DIR:-.}"
stage=$(cat .harness/STAGE 2>/dev/null || echo 0)
out=$(bash scripts/check.sh --stage "$stage" 2>&1) && exit 0
echo "Not done: scripts/check.sh --stage $stage fails:" >&2
echo "$out" | tail -20 >&2
echo "Fix the cause, or stop and tell the user which check is wrong. Do not edit the check." >&2
exit 2
