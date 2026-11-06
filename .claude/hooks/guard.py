"""PreToolUse guard for qgen-practical: keep the harness and prereg intact, gate the grids.

Paths are matched relative to the project root, so files outside the repo (for example
~/.claude/projects/.../memory/) are never blocked.

Shell commands are checked per segment (split on && || ; | and newlines), after heredoc
bodies are removed. Read-only or index-only git segments (add, commit, status, diff, log,
show) are exempt from the harness-write rule.

v5 (2026-11-06), two false positives fixed:
- A redirect only counts as a harness write when its *target* is protected (`printf 8 >
  .harness/STAGE`), not when a protected name merely appears in the same segment (`grep -v
  BUDGET_OK > list.txt`, or a `<target>` placeholder in prompt text). The other write verbs
  (rm, mv, cp, touch, tee, sed -i, git checkout/restore/...) still block on any protected
  name in the segment.
- `herdr agent prompt` segments are text sent to another agent (whose own guard applies), so
  they are not scanned for writes.
- Grid gates (`--all` without BUDGET_OK) apply per segment, after the git-safe and prompt-text
  exemptions, so commit messages and prompt text that mention the flag are no longer blocked.
- Step-4 grid gate added.

v6 (2026-11-07): step-5 grid gate added.
"""
import json, os, re, sys

call = json.load(sys.stdin)
tool, args = call.get("tool_name", ""), call.get("tool_input", {}) or {}
root = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))


def block(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


PROTECTED = ("scripts/check.sh", ".claude/settings.json", ".claude/hooks/", ".harness/", "prereg/", "BUDGET_OK")
VERBS = re.compile(r"(sed -i|\brm |\bmv |\bcp |touch |\btee |New-Item|Set-Content|Out-File|Remove-Item|"
                   r"git (checkout|restore|rm|mv|reset|stash|apply)\b)")
REDIR_TARGET = re.compile(r"(?<![0-9&<>-])>{1,2}\|?\s*['\"]?([^\s'\";|&<>]+)")
GIT_SAFE = re.compile(r"^\s*git\s+(add|commit|status|diff|log|show)\b")
PROMPT_TEXT = re.compile(r"^\s*herdr\s+agent\s+prompt\b")
GATES = [
    (r"step5[./\\]run(\.py)?\b.*--all", "Step-5 grid blocked: no BUDGET_OK. Write results/step5/PROJECTION.json, report it, and wait for the user."),
    (r"step4[./\\]run(\.py)?\b.*--all", "Step-4 grid blocked: no BUDGET_OK. Write results/step4/PROJECTION.json, report it, and wait for the user."),
    (r"step3[./\\]run(\.py)?\b.*--all", "Step-3 grid blocked: no BUDGET_OK. Write results/step3/PROJECTION.json, report it, and wait for the user."),
    (r"step2[./\\]sweep(\.py)?\b.*--all", "Step-2 sweep blocked: no BUDGET_OK. Write results/step2/PROJECTION.json, report it, and wait for the user."),
    (r"step1[./\\]run(\.py)?\b.*--all", "Full grid blocked: no BUDGET_OK. Write PROJECTION.json, report it in PROGRESS.md, and wait for the user."),
]


def rel_in_repo(p):
    if not p:
        return None
    ap = os.path.realpath(p if os.path.isabs(p) else os.path.join(root, p))
    try:
        if os.path.commonpath([ap.lower(), root.lower()]) != root.lower():
            return None  # outside the repo: not ours to guard
    except ValueError:  # different drives on Windows
        return None
    return os.path.relpath(ap, root).replace("\\", "/")


def is_protected(rel):
    return bool(rel) and any(rel == p.rstrip("/") or rel.startswith(p) for p in PROTECTED)


def strip_heredocs(cmd):
    return re.sub(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\s*\1\s*(\n|$)", "\n", cmd, flags=re.S)


if tool in ("Edit", "Write", "NotebookEdit"):
    r = rel_in_repo(str(args.get("file_path", "")))
    if is_protected(r):
        block(f"{r} is part of the harness / frozen prereg (or the user-only BUDGET_OK). "
              "If a check is wrong, stop and tell the user which one and why.")

if tool in ("Bash", "PowerShell"):
    cmd = strip_heredocs(str(args.get("command", "")))
    segments = [s for s in re.split(r"&&|\|\||;|\||\n", cmd) if s.strip()]
    for seg in segments:
        if re.search(r"^\s*git\s+push\b", seg):
            block("git push is not allowed in this project. Commit locally and report.")
        if PROMPT_TEXT.search(seg):
            continue
        if "qgen-iqp-A" in cmd and re.search(r"(?<![0-9&])>(?!&)|sed -i|\brm |\bmv |\bcp |touch |git |python|pytest", seg) \
                and not re.search(r"^\s*(cat|head|tail|grep|sed -n|ls|cd)\b", seg):
            block("qgen-iqp-A is read-only for this task (live jobs). Read its files; do not write to or run code from it.")
        if GIT_SAFE.search(seg):
            continue
        for t in REDIR_TARGET.findall(seg):
            if t.startswith("/dev/") or t.startswith("&"):
                continue
            # any protected name in the target counts, even outside this root (another checkout)
            if is_protected(rel_in_repo(t)) or any(p in t.replace("\\", "/") for p in PROTECTED):
                block("Shell write into the harness, prereg/ or BUDGET_OK. If a check is wrong, stop and report it.")
        if any(p in seg for p in PROTECTED) and VERBS.search(seg):
            block("Shell write into the harness, prereg/ or BUDGET_OK. If a check is wrong, stop and report it.")
        if "python" in seg and not os.path.exists(os.path.join(root, "BUDGET_OK")):
            for pat, msg in GATES:
                if re.search(pat, seg):
                    block(msg)

sys.exit(0)
