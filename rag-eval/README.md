# rag-eval

A Claude / agent skill that measures RAG retrieval quality (recall@k, precision@k, hit-rate, MRR, nDCG) from a labeled set and tells you whether retrieval, ranking, or generation is the bottleneck.

## Install
Drop this folder into your agent's skills directory (for Claude Code, `~/.claude/skills/rag-eval/`), or install from the marketplace listing.

## Use
```
python3 rag_eval.py cases.jsonl
```
Each object: `{"query": "...", "retrieved": ["d3","d1"], "relevant": ["d1"]}`. Run `python3 rag_eval.py --self-test` to see it score a good retriever above a bad one. See `SKILL.md` for the metrics and how to read the verdict.

## Why it exists
Teams burn days tuning prompts when the real problem is retrieval, or the reverse. This measures the retrieval layer directly so you fix the right thing. Pure stdlib; nothing leaves your machine.

License: MIT.
