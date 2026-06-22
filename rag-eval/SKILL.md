---
name: rag-eval
description: Evaluate RAG retrieval quality from a labeled set. Computes recall@k, precision@k, hit-rate@k, MRR, and nDCG@k from your queries, the doc ids your retriever returned, and the ids that are actually relevant, then tells you whether retrieval, ranking, or generation is the bottleneck. Use when a RAG system gives wrong or weak answers and you need to know where the problem is.
license: MIT
version: 0.1.0
---

# RAG Eval

When a RAG system answers badly, the question is always whether it is retrieval, ranking, or generation. Guessing wastes days. This measures retrieval directly so you fix the right layer.

## When to use
When RAG answers are wrong, thin, or inconsistent, before you start tuning prompts or swapping models. Also as a regression check whenever you change chunking, embeddings, or the index.

## Input
A JSON array or JSONL file, one case per object:
```
{"query": "how do I reset my key", "retrieved": ["d3","d1","d9"], "relevant": ["d1","d7"]}
```
`retrieved` is your retriever's output in rank order; `relevant` is the ground-truth set from labels or a golden set.

## Run
```
python3 rag_eval.py cases.jsonl
python3 rag_eval.py cases.json --k 1,3,5,10
python3 rag_eval.py --self-test
```

## What you get
- recall@k (did the right docs make the top k), precision@k, hit-rate@k
- MRR (how high the first relevant doc ranks)
- nDCG@k (ranking quality)
- a verdict that points at the actual bottleneck: low recall means fix chunking / embeddings / index; good recall but low nDCG means add a reranker; healthy retrieval means the problem is generation or prompt, not retrieval

## Honest limits
It measures retrieval against the labels you give it, so the eval is only as good as your relevance labels. It does not score answer quality; that is a separate generation eval.

Deps: Python stdlib only.
