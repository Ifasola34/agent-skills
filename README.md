# Agent Skills

Focused, no-nonsense skills for coding agents (Claude Code and compatible). Each is a single folder with a `SKILL.md`, a small tested script, and a README. Each does one job well and tells you honestly what it cannot do.

## Skills

- **[backtest-validator](backtest-validator/)** - gives a trading strategy one honest verdict (PASS / FAIL / INCONCLUSIVE) by checking the four things most backtests skip: sample-size/power, realistic costs and break-even, luck (bootstrap), and multiple-testing. Stops you trusting overfit results.
- **[mcp-security-review](mcp-security-review/)** - audits an MCP server for the vulnerability classes that actually land in AI tool servers (command/code injection, unsafe deserialization, SSRF, path traversal, SSTI, SQL injection, secret exposure), grouped by severity with fixes and a manual checklist.
- **[verify-before-shipping](verify-before-shipping/)** - turns "it works" into proof: runs your real checks and captures the evidence (command, exit code, output), and gates on it. Stop shipping claims without receipts.

## Install
Copy a skill folder into your agent's skills directory (for Claude Code, `~/.claude/skills/<name>/`). Each skill's README has usage. Most run with `python3 <script>.py --self-test` to prove they work first.

## Design
Small over sprawling. A skill that says "run these checks, here is the verdict, here is what I cannot tell you" is worth more than a large one that hides its assumptions. Every script ships with a self-test so you can confirm it behaves before trusting it.

License: MIT.
