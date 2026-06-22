# verify-before-shipping

A Claude / agent skill that turns "it works" into "here is the proof". Before a change is reported done, it runs your real checks and captures the evidence (command, exit code, output), and gates on it.

## Install
Drop this folder into your agent's skills directory (for Claude Code, `~/.claude/skills/verify-before-shipping/`), or install from the marketplace listing.

## Use
```
python3 proof.py "pytest -q" "ruff check ."
```
Paste the PASS/FAIL report into your done message. It exits non-zero if any check fails, so it also works as a pre-commit or CI gate. Run `python3 proof.py --self-test` to see it pass a passing command and fail a failing one.

## Why it exists
Agents and people routinely claim a fix works without running anything. This encodes the discipline of proof: show the command, the exit code, and the output, every time. No data leaves your machine.

License: MIT.
