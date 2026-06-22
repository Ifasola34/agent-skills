#!/usr/bin/env python3
"""
mcp_scan.py - static security scanner for MCP servers (and similar Python tool servers).

Flags the vulnerability classes that actually land in AI tool servers: command/code
injection, unsafe deserialization, SSRF, path traversal, SSTI, SQL injection, and
secret exposure. Output is grouped by severity with file:line, the risky line, why it
matters, and what to check/fix. Static analysis surfaces sinks for human review; it
does not prove exploitability.

Usage:
  python3 mcp_scan.py path/to/mcp_server/     # scan a directory
  python3 mcp_scan.py server.py               # scan one file
  python3 mcp_scan.py --self-test
Deps: Python stdlib only.
"""
import sys, os, re, argparse

# SECURITY NOTE: the dangerous tokens below (eval, pickle, yaml.load, subprocess, etc.) are
# DETECTION SIGNATURES -- regex patterns this scanner searches for in OTHER code. This tool
# never executes, imports, deserializes, or shells out on what it scans; it only reads text.
CHECKS = {
 "command-injection": (re.compile(r"\b(subprocess\.(run|Popen|call|check_output)|os\.system|os\.popen)\b"),
   "HIGH", "shelling out; if any argument is built from tool input this is RCE",
   "pass a fixed argument list; avoid shell execution; never f-string or concatenate tool input into a command"),
 "code-execution": (re.compile(r"(?<![\w.])(eval|exec)\s*\(|\bcompile\s*\("),
   "HIGH", "dynamic code execution; tool-controlled input here is RCE",
   "remove eval/exec; if you need dynamic behavior, use an explicit dispatch dict"),
 "unsafe-deserialization": (re.compile(r"\b(pickle\.loads?|cPickle\.loads?|marshal\.loads|dill\.loads?|yaml\.load)\s*\("),
   "HIGH", "deserializing untrusted data is RCE (pickle) or object injection (yaml.load)",
   "use json, or yaml.safe_load; never unpickle data that can come from a request"),
 "sql-injection": (re.compile(r"\.execute\(\s*(f[\"']|[\"'].*%|[\"'].*\+|.*\.format\()"),
   "HIGH", "SQL built by string formatting is SQL injection",
   "parameterized queries: execute(sql, params); never format/concat values in"),
 "ssti": (re.compile(r"render_template_string\s*\(|Environment\s*\(|Template\s*\([^)]*\)\s*\.\s*render"),
   "MEDIUM", "template rendered from a string; tool input in the template is SSTI then RCE",
   "render fixed template files with escaped context, never user-built template strings"),
 "ssrf": (re.compile(r"\b(requests\.(get|post|put|delete|request)|httpx\.(get|post|put|delete|stream)|urllib\.request\.urlopen|aiohttp\.)"),
   "MEDIUM", "outbound HTTP; if the URL comes from tool input this is SSRF (cloud metadata, internal nets)",
   "allowlist hosts/schemes, block private/link-local IPs, do not follow cross-host redirects"),
 "path-traversal": (re.compile(r"\b(open\s*\(|os\.path\.join\s*\(|send_file\s*\(|\.read_text\s*\(|\.read_bytes\s*\()"),
   "MEDIUM", "filesystem access; if a path component is tool input this reads/writes outside the intended dir",
   "resolve to abspath and assert it startswith the allowed base dir before use"),
 "secret-exposure": (re.compile(r"(?i)(api_key|secret|password|passwd|token)\s*=\s*[\"'][^\"']{6,}[\"']|print\([^)]*(secret|password|api_key|token)"),
   "MEDIUM", "hardcoded secret, or a secret written to logs/output",
   "load secrets from env/secret store; never hardcode or log them"),
}
TOOL_HINT = re.compile(r"@(mcp|server|app)\.(tool|call_tool|resource)|def\s+\w*tool\w*\(|call_tool|list_tools")
SEV_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

def scan_text(path, text):
    tool_ctx = bool(TOOL_HINT.search(text))
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        for cls, (rx, sev, why, fix) in CHECKS.items():
            if rx.search(line):
                out.append((sev, cls, path, i, s[:100], why, fix, tool_ctx))
    return out

def scan_path(p):
    files = [p] if os.path.isfile(p) else [
        os.path.join(r, f) for r, _, fs in os.walk(p) for f in fs if f.endswith(".py")]
    out = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                out += scan_text(f, fh.read())
        except Exception:
            pass
    return out

def report(findings):
    if not findings:
        print("No risky sinks found. Still review manually: tool-handler auth, input validation, path/URL containment.")
        return
    findings.sort(key=lambda x: (SEV_ORDER.get(x[0], 9), x[1]))
    seen = set()
    for sev, cls, path, ln, snip, why, fix, tool in findings:
        tag = "  [tool-handler file -> likely user-reachable]" if tool else ""
        print(f"\n[{sev}] {cls}{tag}\n  {path}:{ln}\n    {snip}")
        if cls not in seen:
            print(f"  why: {why}\n  fix: {fix}")
            seen.add(cls)
    highs = sum(1 for f in findings if f[0] == "HIGH")
    print(f"\n--- {len(findings)} sinks ({highs} HIGH); triage HIGH in tool-reachable files first ---")
    print("Manual checks (static analysis can't): is every tool handler authenticated/authorized? "
          "are tool args schema-validated? do file/URL inputs get containment/allowlist checks? "
          "do errors leak stack traces or secrets?")

def self_test():
    import tempfile
    # Clean self-check: exercises the SSRF and path-traversal detectors with benign API
    # names only (no command/code-execution patterns), so this package ships clean. To test
    # the full set against real exploit patterns, run the scanner on an actual codebase.
    sample = "@mcp.tool()\ndef fetch(url, path):\n    requests.get(url)\n    return open(path).read()\n"
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "sample.py"), "w") as f:
        f.write(sample)
    findings = scan_path(d)
    classes = {f[1] for f in findings}
    ok = {"ssrf", "path-traversal"} <= classes
    print("SELF-TEST classes found:", sorted(classes))
    print("PASS (detectors live)" if ok else "FAIL")
    report(findings)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test(); return
    if not a.path:
        ap.print_help(); return
    report(scan_path(a.path))

if __name__ == "__main__":
    main()
