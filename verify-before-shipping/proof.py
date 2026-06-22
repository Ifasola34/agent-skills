#!/usr/bin/env python3
"""
proof.py - capture real evidence that a change works, instead of claiming it does.

Runs one or more verification commands, captures exit code + output + duration, and
prints a PASS/FAIL evidence report you attach to your "done" claim. Exits non-zero if
any check fails, so it doubles as a CI or pre-commit gate.

This intentionally runs the commands YOU pass it (your own tests/checks) to capture
their output; it does not execute anything from untrusted input. Default is no shell
(arguments are split safely with shlex); pass --shell only when you need pipes or &&.

Usage:
  python3 proof.py "pytest -q" "ruff check ."
  python3 proof.py --shell "grep -rc TODO src | sort"
  python3 proof.py --self-test
Deps: Python stdlib only.
"""
import sys, subprocess, shlex, time, argparse

def run_one(cmd, shell, timeout):
    start = time.time()
    try:
        # Runs the developer's own verification command to capture its real output.
        proc = subprocess.run(cmd if shell else shlex.split(cmd), shell=shell,
                              capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr, time.time() - start, None
    except subprocess.TimeoutExpired:
        return None, "", "", time.time() - start, f"timed out after {timeout}s"
    except Exception as e:
        return None, "", "", time.time() - start, str(e)

def tail(s, n=1200):
    s = s or ""
    return s if len(s) <= n else "...(truncated)...\n" + s[-n:]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("commands", nargs="*")
    ap.add_argument("--shell", action="store_true")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    cmds = ['python3 -c "print(123)"', 'python3 -c "import sys; sys.exit(1)"'] if a.self_test else a.commands
    if not cmds:
        ap.print_help(); return
    print(f"=== PROOF OF WORK · {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    passed = 0
    for cmd in cmds:
        code, out, err, dur, errmsg = run_one(cmd, a.shell, a.timeout)
        ok = code == 0
        passed += ok
        print(f"\n[{'PASS' if ok else 'FAIL'}] $ {cmd}")
        print(f"  exit={code if code is not None else 'n/a'}  time={dur:.2f}s" + (f"  ({errmsg})" if errmsg else ""))
        body = (out or "") + (("\n[stderr]\n" + err) if (err or "").strip() else "")
        for line in tail(body).splitlines():
            print("  | " + line)
    total = len(cmds)
    print(f"\n=== {passed}/{total} checks passed ===")
    if a.self_test:
        print("SELF-TEST PASS" if passed == 1 else "SELF-TEST FAIL")
        return
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
