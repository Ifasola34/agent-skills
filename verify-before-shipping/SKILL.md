---
name: verify-before-shipping
description: Stop claiming a change works; prove it. Before reporting a fix or feature as done, run the relevant checks and attach real evidence (the command, its exit code, its output). Bundles proof.py to capture that evidence and gate on it. Use whenever you are about to say "done", "fixed", or "it works".
license: MIT
version: 0.1.0
---

# Verify Before Shipping

The most common failure mode in agent coding is claiming success without proof. This skill makes "done" mean "here is the evidence", not "I believe so".

## The rule
Before you report a change as fixed, working, or done, show:
1. the exact command(s) you ran
2. their exit codes
3. their real output

If you cannot produce passing evidence, you are not done. A green claim with no receipts is a guess.

## How to use proof.py
Run your real checks through it, then paste the report into your "done" message.
```
python3 proof.py "pytest -q" "ruff check ."
python3 proof.py --shell "curl -s localhost:8000/health | grep ok"
python3 proof.py --self-test
```
It prints a PASS/FAIL block per command with exit code and output, a summary line, and exits non-zero if any check fails, so it also works as a pre-commit or CI gate.

## What counts as evidence
- Tests: the run and its summary, not "tests should pass"
- A bug fix: the failing case reproduced first, then the same case passing after
- An endpoint or UI: the actual request and response, or the exact URL and what to look for
- A refactor: the suite green plus a behavior check, not just "it compiles"

Mocks prove wiring, not behavior. Where it matters, exercise the real path.

## What this is not
It does not decide whether your checks are the right ones; you still choose meaningful checks. It captures and gates on the evidence so a claim cannot ship without receipts.

Deps: Python stdlib only.
