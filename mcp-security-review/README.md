# mcp-security-review

A Claude / agent skill that audits an MCP server for the vulnerability classes common in AI tool servers: command and code injection, unsafe deserialization, SSRF, path traversal, SSTI, SQL injection, and secret exposure. Static scan, grouped by severity, with file:line and fixes, plus a manual checklist.

## Install
Drop this folder into your agent's skills directory (for Claude Code, `~/.claude/skills/mcp-security-review/`), or install from the marketplace listing.

## Use
```
python3 mcp_scan.py path/to/mcp_server/
```
Run `python3 mcp_scan.py --self-test` to see it flag a deliberately vulnerable sample. See `SKILL.md` for the full guide.

## Why it exists
MCP tools take agent-controlled input and frequently shell out, fetch URLs, read files, or deserialize data. That input-to-sink path is where real MCP bugs live. This encodes a first-pass review so the obvious ones get caught before shipping. The scanner reads source text only; nothing leaves your machine.

License: MIT.
