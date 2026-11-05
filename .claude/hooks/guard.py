"""PreToolUse guard for qgen-practical: keep the harness and prereg intact, gate the grid.

Paths are matched relative to the project root, so files outside the repo (for example
~/.claude/projects/.../memory/) are never blocked. qgen-iqp-A's guard matched any '.claude/'
substring and blocked memory writes; that was a false positive and is fixed here.

Shell commands are checked per segment (split on && || ; | and newlines), after heredoc
bodies are removed. Read-only or index-only git segments (add, commit, status, diff, log,
show) are exempt from the harness-write rule: they do not change file contents, and their
commit messages (e.g. "<noreply@...>") used to trip the '>' redirect pattern.
"""
import json, os, re, sys

call = json.load(sys.stdin)
tool, args = call.get("tool_name", ""), call.get("tool_input", {}) or {}
root = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))


def block(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


PROTECTED = ("scripts/check.sh", ".claude/settings.json", ".claude/hooks/", ".harness/", "prereg/", "BUDGET_OK")
REDIR = r"(?<![0-9&])>(?!&)"  # real redirects; not 2>&1 or 2>/dev/null
WRITES = re.compile(REDIR + r"|(sed -i|\brm |\bmv |\bcp |touch |\btee |New-Item|Set-Content|Out-File|Remove-Item|"
                    r"git (checkout|restore|rm|mv|reset|stash|apply)\b)")
GIT_SAFE = re.compile(r"^\s*git\s+(add|commit|status|diff|log|show)\b")


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


def strip_heredocs(cmd):
    return re.sub(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\s*\1\s*(\n|$)", "\n", cmd, flags=re.S)


if tool in ("Edit", "Write", "NotebookEdit"):
    r = rel_in_repo(str(args.get("file_path", "")))
    if r and any(r == p.rstrip("/") or r.startswith(p) for p in PROTECTED):
        block(f"{r} is part of the harness / frozen prereg (or the user-only BUDGET_OK). "
              "If a check is wrong, stop and tell the user which one and why.")

if tool in ("Bash", "PowerShell"):
    cmd = strip_heredocs(str(args.get("command", "")))
    segments = [s for s in re.split(r"&&|\|\||;|\||\n", cmd) if s.strip()]
    for seg in segments:
        if re.search(r"^\s*git\s+push\b", seg):
            block("git push is not allowed in this project. Commit locally and report.")
        if "qgen-iqp-A" in cmd and re.search(REDIR + r"|sed -i|\brm |\bmv |\bcp |touch |git |python|pytest", seg) \
                and not re.search(r"^\s*(cat|head|tail|grep|sed -n|ls|cd)\b", seg):
            block("qgen-iqp-A is read-only for this task (live jobs). Read its files; do not write to or run code from it.")
        if GIT_SAFE.search(seg):
            continue
        if any(p in seg for p in PROTECTED) and WRITES.search(seg):
            block("Shell write into the harness, prereg/ or BUDGET_OK. If a check is wrong, stop and report it.")
    if re.search(r"step2[./\\]sweep(\.py)?\b.*--all", cmd) and not os.path.exists(os.path.join(root, "BUDGET_OK")):
        block("Step-2 sweep blocked: no BUDGET_OK. Write results/step2/PROJECTION.json, report it, and wait for the user.")
    if re.search(r"step1[./\\]run(\.py)?\b.*--all", cmd) and not os.path.exists(os.path.join(root, "BUDGET_OK")):
        block("Full grid blocked: no BUDGET_OK. Write PROJECTION.json, report it in PROGRESS.md, and wait for the user.")

sys.exit(0)
