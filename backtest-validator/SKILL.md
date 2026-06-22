---
name: backtest-validator
description: Validate whether a trading strategy or backtest has a real, tradeable edge or is overfit noise. Runs four checks most backtests skip (sample-size/power, realistic costs, luck via bootstrap, multiple-testing) and returns a PASS / FAIL / INCONCLUSIVE verdict plus the break-even cost. Use when reviewing a strategy, backtest output, or trade log before trusting or deploying it.
license: MIT
version: 0.1.0
---

# Backtest Validator

Most backtests lie for one of four reasons. This skill runs all four checks and returns a single honest verdict instead of a win rate that fools you.

## When to use
Use whenever someone presents a strategy, backtest result, or trade log and the real question is "does this have an edge that survives reality". Especially when results look flat, bounce around as data is added, or a "best" variant was cherry-picked from many.

## What it catches
1. Sample size / power. With around 30 trades the confidence interval on the average trade swamps the signal, so results look random and flip as you add data. The skill flags underpowered samples instead of pretending they mean something.
2. Costs. It applies a per-trade cost (fees, spread, slippage) and reports the break-even cost: the level at which the edge hits zero. If that sits below your real cost, the strategy loses live.
3. Luck. A 10,000-sample bootstrap gives the probability the mean is genuinely positive plus a confidence interval, so a lucky run does not get mistaken for an edge.
4. Multiple testing. If many variants were tried, the best one looks good by chance alone. A Sidak correction and the Probabilistic Sharpe Ratio penalize that and kill the "best of N" illusion.

## How to run
Input is a CSV with one row per closed trade and a fractional-return column (default `pct`, where 0.0019 means +0.19%).

```
python3 validate.py trades.csv --cost-bps 2 --tried 8
python3 validate.py *.csv --col return_pct --cost-bps 1
python3 validate.py --self-test
```

- `--cost-bps`: round-trip cost per trade in basis points
- `--tried`: how many strategy variants you tested (drives the multiple-testing penalty)
- `--col`: the return column name

## Reading the verdict
- PASS: positive after costs, distinguishable from luck, survives multiple-testing, n at least 100
- WEAK: positive and significant but n under 100, do not trust yet
- INCONCLUSIVE: cannot separate signal from noise, usually too few trades
- FAIL: no edge after costs

The single most useful number is the break-even cost. Compare it to your real trading cost; if real cost is higher, the strategy is not tradeable no matter how clean the win rate looks.

## Honest limits
This tests whether the historical edge is real and survives costs, which is the necessary first gate, not a promise about the future. It needs the trade list and does not re-run your strategy logic.

Dependencies: numpy, pandas. No scipy.
