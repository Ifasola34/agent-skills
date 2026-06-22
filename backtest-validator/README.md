# backtest-validator

A Claude / agent skill that gives a trading strategy one honest verdict: PASS, FAIL, or INCONCLUSIVE. It runs the four checks most backtests skip (sample size, costs, luck, multiple testing) so you stop trusting overfit results.

## Install
Drop this folder into your agent's skills directory (for Claude Code, `~/.claude/skills/backtest-validator/`), or install it from the marketplace listing.

## Use
```
python3 validate.py your_trades.csv --cost-bps 2 --tried 5
```
Input is a CSV with a per-trade fractional-return column (default `pct`). See `SKILL.md` for the full guide and how to read the verdict.

## Why it exists
A green backtest with 30 trades and no cost model is the most common way traders fool themselves. This encodes the validation a careful quant does by hand: walk-forward thinking, a real cost and break-even model, a 10k bootstrap for luck, and a multiple-testing penalty for the "best of N" trap. Run `python3 validate.py --self-test` to see it correctly pass a real edge and reject a fake one.

Dependencies: numpy, pandas.

License: MIT.
