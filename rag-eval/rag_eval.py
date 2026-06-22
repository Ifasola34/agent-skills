#!/usr/bin/env python3
"""
rag_eval.py - evaluate RAG retrieval quality from a labeled set.

Given queries with the doc ids your retriever returned (ranked) and the ids that are
actually relevant, it computes recall@k, precision@k, hit-rate@k, MRR, and nDCG@k, then
tells you whether retrieval is the bottleneck (versus ranking, or generation). Pure stdlib.

Input: JSON array or JSONL, one case per object:
  {"query": "...", "retrieved": ["d3","d1","d9"], "relevant": ["d1","d7"]}

Usage:
  python3 rag_eval.py cases.jsonl
  python3 rag_eval.py cases.json --k 1,3,5,10
  python3 rag_eval.py --self-test
Deps: Python stdlib only.
"""
import sys, json, argparse, math

def load(path):
    txt = open(path, encoding="utf-8").read().strip()
    return json.loads(txt) if txt.startswith("[") else [json.loads(l) for l in txt.splitlines() if l.strip()]

def dcg(rels):
    return sum(r / math.log2(i + 2) for i, r in enumerate(rels))

def eval_case(retrieved, relevant, ks):
    rel = set(relevant); out = {}
    for k in ks:
        topk = retrieved[:k]
        hits = sum(1 for d in topk if d in rel)
        out[f"recall@{k}"] = hits / len(rel) if rel else 0.0
        out[f"precision@{k}"] = hits / k if k else 0.0
        out[f"hit@{k}"] = 1.0 if hits else 0.0
        gains = [1.0 if d in rel else 0.0 for d in topk]
        ideal = [1.0] * min(len(rel), k) + [0.0] * max(0, k - len(rel))
        idcg = dcg(ideal)
        out[f"ndcg@{k}"] = (dcg(gains) / idcg) if idcg else 0.0
    rr = 0.0
    for i, d in enumerate(retrieved, 1):
        if d in rel:
            rr = 1.0 / i; break
    out["rr"] = rr
    return out

def aggregate(cases, ks):
    keys = [f"{m}@{k}" for k in ks for m in ("recall", "precision", "hit", "ndcg")] + ["rr"]
    sums = {key: 0.0 for key in keys}
    for c in cases:
        r = eval_case(c.get("retrieved", []), c.get("relevant", []), ks)
        for key in keys:
            sums[key] += r.get(key, 0.0)
    n = len(cases) or 1
    return {key: sums[key] / n for key in keys}

def report(agg, ks, n):
    print(f"=== RAG retrieval eval · {n} queries ===")
    print(f"{'k':>4} | {'recall':>7} | {'prec':>6} | {'hit-rate':>8} | {'nDCG':>6}")
    for k in ks:
        print(f"{k:>4} | {agg[f'recall@{k}']:>7.3f} | {agg[f'precision@{k}']:>6.3f} | {agg[f'hit@{k}']:>8.3f} | {agg[f'ndcg@{k}']:>6.3f}")
    print(f"MRR: {agg['rr']:.3f}")
    kmax = max(ks); r = agg[f"recall@{kmax}"]
    if r < 0.5:
        print(f"\nVERDICT: retrieval is the bottleneck (recall@{kmax}={r:.2f}). Fix chunking / embeddings / index before touching the prompt or generation.")
    elif agg[f"ndcg@{kmax}"] < 0.6:
        print(f"\nVERDICT: relevant docs are found but ranked low (nDCG@{kmax}={agg[f'ndcg@{kmax}']:.2f}). Add a reranker.")
    else:
        print(f"\nVERDICT: retrieval is healthy (recall@{kmax}={r:.2f}). If answers are still wrong, the problem is generation / prompt, not retrieval.")

def self_test():
    good = [{"retrieved": ["d1", "d2", "d3"], "relevant": ["d1"]},
            {"retrieved": ["d5", "d4"], "relevant": ["d5"]}]
    bad = [{"retrieved": ["d9", "d8", "d7"], "relevant": ["d1"]},
           {"retrieved": ["d6", "d3"], "relevant": ["d5"]}]
    ks = [1, 3]
    ga, ba = aggregate(good, ks), aggregate(bad, ks)
    print(f"good recall@3={ga['recall@3']:.2f}  bad recall@3={ba['recall@3']:.2f}")
    print("PASS" if ga["recall@3"] == 1.0 and ba["recall@3"] == 0.0 else "FAIL")
    report(ga, ks, len(good))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--k", default="1,3,5,10")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test(); return
    if not a.file:
        ap.print_help(); return
    ks = [int(x) for x in a.k.split(",")]
    cases = load(a.file)
    report(aggregate(cases, ks), ks, len(cases))

if __name__ == "__main__":
    main()
