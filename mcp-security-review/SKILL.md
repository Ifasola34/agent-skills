---
name: mcp-security-review
description: Audit an MCP server (or similar Python tool server) for the vulnerability classes that actually land in AI tool servers - command/code injection, unsafe deserialization, SSRF, path traversal, SSTI, SQL injection, and secret exposure. Runs a static scan and returns findings by severity with file:line and fixes, plus a manual review checklist. Use before shipping an MCP server or when reviewing one.
license: MIT
version: 0.1.0
---

# MCP Security Review

MCP servers expose tools that take model or user controlled input and often shell out, fetch URLs, read files, or deserialize data. That input-to-sink path is where the bugs are. This skill scans for those sinks and tells you which to triage first.

## When to use
Before publishing an MCP server, or when reviewing one. Also useful for any Python service that exposes tool or function endpoints to an agent.

## What it checks (the classes that pay)
- Command injection (subprocess / os.system with built arguments)
- Code execution (eval / exec / compile)
- Unsafe deserialization (pickle, marshal, dill, yaml.load)
- SQL injection (string-formatted queries)
- SSTI (templates rendered from strings)
- SSRF (outbound HTTP to input-derived URLs)
- Path traversal (file access with input-derived paths)
- Secret exposure (hardcoded or logged secrets)

## How to run
```
python3 mcp_scan.py path/to/mcp_server/
python3 mcp_scan.py server.py
python3 mcp_scan.py --self-test
```
Output groups findings by severity with file:line, the line itself, why it matters, and the fix. Files that define tool handlers are tagged as likely user-reachable so you triage those first.

## Reading it
Static analysis surfaces sinks; it does not prove exploitability. Confirm each HIGH by tracing whether tool input actually reaches the sink, then run the manual checks the scanner prints: is every tool handler authenticated and authorized, are tool arguments schema-validated, do file and URL inputs get containment or allowlist checks, do errors leak stack traces or secrets.

## Honest limits
This is a first-pass triage to focus a human review, not a guarantee of safety or a replacement for one. No data leaves your machine; the scanner only reads source text.

Dependencies: Python stdlib only.
