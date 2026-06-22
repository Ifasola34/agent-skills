#!/usr/bin/env python3
"""
validate.py - rigorous strategy validation harness.

Answers ONE question per strategy: is there a REAL, cost-surviving edge, or is it
noise / overfitting? Tackles the four things that make backtests lie:
  1. Sample size / power     - is n big enough to conclude anything at all?
  2. Costs                   - does the edge survive fees + slippage?
  3. Luck                    - bootstrap: could this happen by chance?
  4. Multiple testing        - you tried N strategies; the best looks good by
                               luck alone (Sidak correction + PSR).

Input: a trades CSV with a per-trade FRACTIONAL-return column (default 'pct',
e.g. 0.0019 = +0.19%). Matches the ~/Desktop/Stats/*.csv format.

Usage:
  python3 validate.py ~/Desktop/Stats/*.csv --cost-bps 2 --tried 8
  python3 validate.py --self-test
Deps: numpy, pandas (no scipy).
"""
import sys, glob, math, argparse
import numpy as np
import pandas as pd

def ncdf(x):                       # standard normal CDF via erf (no scipy)
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def basic(r):
    r = np.asarray(r, float); n = len(r)
    mean = float(r.mean()); sd = float(r.std(ddof=1)) if n > 1 else float('nan')
    win = float((r > 0).mean())
    wins = r[r > 0].sum(); losses = -r[r < 0].sum()
    pf = float(wins / losses) if losses > 0 else float('inf')
    eq = np.cumsum(r); peak = np.maximum.accumulate(eq); dd = float((eq - peak).min())
    return dict(n=n, mean=mean, sd=sd, win=win, pf=pf, total=float(r.sum()), maxdd=dd)

def psr0(r):                       # Probabilistic Sharpe Ratio vs 0 (skew/kurt + n aware)
    r = np.asarray(r, float); n = len(r)
    if n < 3: return float('nan')
    m = r.mean(); s = r.std(ddof=1)
    if s == 0: return float('nan')
    sr = m / s
    sk = float(((r - m) ** 3).mean() / s ** 3)
    ku = float(((r - m) ** 4).mean() / s ** 4)        # Pearson (normal = 3)
    denom = math.sqrt(max(1e-12, 1 - sk * sr + ((ku - 1) / 4.0) * sr ** 2))
    return ncdf(sr * math.sqrt(n - 1) / denom)

def bootstrap(r, nboot, rng):
    r = np.asarray(r, float); n = len(r)
    idx = rng.integers(0, n, size=(nboot, n))
    samp = r[idx]
    means = samp.mean(axis=1); totals = samp.sum(axis=1)
    p_le0 = float((means <= 0).mean())                 # one-sided: P(mean <= 0)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return p_le0, float(lo), float(hi), float((totals > 0).mean())

def analyze(name, r, cost, tried, nboot, rng):
    g = basic(r); net = np.asarray(r, float) - cost; ns = basic(net)
    p_le0, lo, hi, p_profit = bootstrap(net, nboot, rng)
    p_mt = 1 - (1 - p_le0) ** max(1, tried)            # Sidak multiple-testing
    psr = psr0(net)
    be_bps = g['mean'] * 1e4                            # break-even cost = gross mean
    sharpe = ns['mean'] / ns['sd'] if ns['sd'] and not math.isnan(ns['sd']) else float('nan')
    n = g['n']
    power = "SEVERELY UNDERPOWERED" if n < 30 else ("underpowered" if n < 100 else "ok")
    if ns['mean'] <= 0:        v = "FAIL - no edge after costs"
    elif p_le0 > 0.05:         v = "INCONCLUSIVE - edge not distinguishable from luck"
    elif p_mt > 0.05:          v = "INCONCLUSIVE - fails multiple-testing (best-of-N luck)"
    elif n < 100:              v = "WEAK - positive but sample too small to trust"
    else:                      v = "PASS - survives costs, luck & multiple-testing"
    return dict(name=name, g=g, ns=ns, p_le0=p_le0, ci=(lo, hi), p_profit=p_profit,
                p_mt=p_mt, psr=psr, be_bps=be_bps, sharpe=sharpe, power=power, verdict=v)

def fmt(a, cost, tried):
    g, ns = a['g'], a['ns']; lo, hi = a['ci']
    return ("\n=== %s ===\n"
            "  trades=%d  (%s)   win%%=%.1f\n"
            "  GROSS: mean=%+.2f bps/trade  total=%+.2f%%  PF=%.2f  maxDD=%.2f%%\n"
            "  NET (cost %.1f bps/trade): mean=%+.2f bps  total=%+.2f%%  Sharpe/trade=%.3f\n"
            "  break-even cost = %+.2f bps/trade  (edge dies above this)\n"
            "  bootstrap: P(mean<=0)=%.3f   95%% CI mean=[%+.2f, %+.2f] bps   P(period profitable)=%.2f\n"
            "  multiple-testing (tried %d): Sidak p=%.3f    PSR(>0)=%.3f\n"
            "  -> %s") % (
        a['name'], g['n'], a['power'], g['win'] * 100,
        g['mean'] * 1e4, g['total'] * 100, g['pf'], g['maxdd'] * 100,
        cost * 1e4, ns['mean'] * 1e4, ns['total'] * 100, a['sharpe'],
        a['be_bps'], a['p_le0'], lo * 1e4, hi * 1e4, a['p_profit'],
        tried, a['p_mt'], a['psr'], a['verdict'])

def self_test():
    rng = np.random.default_rng(0)
    print("SELF-TEST (expect: no-edge->FAIL/INCONCLUSIVE, big-edge n=500->PASS, "
          "edge n=20->UNDERPOWERED, tiny-edge->dies on cost)")
    cases = {
        "no-edge n=500":               rng.normal(0.0000, 0.01, 500),
        "real-edge n=500 (+20bps)":    rng.normal(0.0020, 0.01, 500),
        "edge-but-n=20 (+20bps)":      rng.normal(0.0020, 0.01, 20),
        "tiny-edge +1bp dies on cost": rng.normal(0.0001, 0.01, 500),
    }
    for k, v in cases.items():
        print(fmt(analyze(k, v, 0.0002, 1, 5000, rng), 0.0002, 1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--col", default="pct")
    ap.add_argument("--cost-bps", type=float, default=2.0, help="round-trip cost per trade, bps")
    ap.add_argument("--tried", type=int, default=0, help="# strategies tried (multiple-testing); default=#files")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test: self_test(); return

    files = []
    for f in args.files: files += glob.glob(f)
    files = sorted(set(files))
    if not files: print("no files matched"); return
    tried = args.tried or len(files); cost = args.cost_bps / 1e4
    rng = np.random.default_rng(42); results = []
    for f in files:
        try:
            df = pd.read_csv(f)
            if args.col not in df.columns:
                print("\n=== %s ===\n  no '%s' column, skipped" % (f.split('/')[-1], args.col)); continue
            r = df[args.col].dropna().to_numpy(float)
            if len(r) < 2:
                print("\n=== %s ===\n  only %d trades - cannot analyze" % (f.split('/')[-1], len(r))); continue
            a = analyze(f.split('/')[-1], r, cost, tried, args.boot, rng)
            results.append(a); print(fmt(a, cost, tried))
        except Exception as e:
            print("  %s: error %s" % (f, e))
    if results:
        npass = sum('PASS' in a['verdict'] for a in results)
        nfail = sum('FAIL' in a['verdict'] for a in results)
        ninc = len(results) - npass - nfail
        tot = sum(a['g']['n'] for a in results)
        print("\n" + "=" * 56)
        print("AGGREGATE: %d strategies, %d total trades, multiple-testing N=%d" % (len(results), tot, tried))
        print("  PASS=%d   FAIL=%d   INCONCLUSIVE/WEAK=%d" % (npass, nfail, ninc))
        print("  cost assumed %.1f bps/trade round-trip (change with --cost-bps)" % args.cost_bps)

if __name__ == "__main__":
    main()
