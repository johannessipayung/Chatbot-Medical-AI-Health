import argparse
import json
import math
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Optional evaluation libs
try:
    from bert_score import score as bert_score
except Exception:
    bert_score = None
try:
    from rouge_score import rouge_scorer
except Exception:
    rouge_scorer = None

# Allow running as: `python app/eval.py` (without manual PYTHONPATH)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from app.data.retriever import MedicalRetriever
except ModuleNotFoundError as e:
    if getattr(e, "name", "") == "faiss":
        raise ModuleNotFoundError(
            "Missing dependency 'faiss'. Activate your venv and install requirements:\n"
            "  pip install -r requirements.txt\n"
            "Or specifically:\n"
            "  pip install faiss-cpu\n"
        ) from e
    raise


STRATEGIES = ["bm25", "dense", "hybrid"]



@dataclass
class Metrics:
    ndcg_at_k: float
    recall_at_k: float
    mrr: float


def _parse_citations(retrieved_docs: List[str]) -> List[Tuple[str, Optional[int]]]:
    import re

    out: List[Tuple[str, Optional[int]]] = []
    for d in retrieved_docs:
        m1 = re.search(r"^\s*SOURCE:\s*(.+)$", d, flags=re.MULTILINE)
        m2 = re.search(r"^\s*PAGE:\s*(\d+)", d, flags=re.MULTILINE)
        if not m1:
            continue
        src = m1.group(1).strip()
        page = int(m2.group(1)) if m2 else None
        out.append((src, page))
    return out


def _is_relevant(citation: Tuple[str, Optional[int]], gold: List[Dict[str, Any]]) -> bool:
    src, page = citation
    for g in gold:
        contains = (g.get("source_contains") or "").lower()
        gpage = g.get("page")
        # source must contain the gold identifier
        if contains and contains not in (src or "").lower():
            continue
        # If both gold and retrieved have page numbers, require equality.
        # If retrieved page is missing/unknown (None or 0), allow match based on source only.
        if gpage is not None and (page is not None and page != 0) and page != gpage:
            continue
        return True
    return False


def _dcg(rels: List[int]) -> float:
    s = 0.0
    for i, rel in enumerate(rels, start=1):
        if rel:
            s += 1.0 / math.log2(i + 1)
    return s


def compute_metrics(citations: List[Tuple[str, Optional[int]]], gold: List[Dict[str, Any]], k: int) -> Tuple[float, float, float]:
    rels = [1 if _is_relevant(c, gold) else 0 for c in citations[:k]]
    dcg = _dcg(rels)
    ideal = _dcg(sorted(rels, reverse=True)) or 1.0
    ndcg = dcg / ideal

    recall = 1.0 if any(rels) else 0.0

    rr = 0.0
    for i, r in enumerate(rels, start=1):
        if r:
            rr = 1.0 / i
            break

    return ndcg, recall, rr


def run_retrieval_eval(gold_path: str, k: int = 5) -> Dict[str, Metrics]:
    with open(gold_path, "r", encoding="utf-8") as f:
        gold = json.load(f)

    items = gold.get("retrieval", [])
    retriever = MedicalRetriever()

    results: Dict[str, Metrics] = {}

    for strat in STRATEGIES:
        ndcgs: List[float] = []
        recalls: List[float] = []
        rrs: List[float] = []

        print(f"\n=== STRATEGY: {strat.upper()} ===")

        for item in items:
            query = item["query"]
            relevant = item.get("relevant", [])

            if strat == "bm25":
                docs = retriever.search_bm25(query, top_n=k)
            elif strat == "dense":
                docs = retriever.search_dense(query, top_n=k)
            else:
                docs = retriever.search(query, top_n=k)

            citations = _parse_citations(docs)

            ndcg, recall, rr = compute_metrics(citations, relevant, k)
            ndcgs.append(ndcg)
            recalls.append(recall)
            rrs.append(rr)

            print(f"[{item.get('id')}] NDCG@{k}={ndcg:.3f} Recall@{k}={recall:.3f} RR={rr:.3f}")

        results[strat] = Metrics(
            ndcg_at_k=sum(ndcgs) / max(len(ndcgs), 1),
            recall_at_k=sum(recalls) / max(len(recalls), 1),
            mrr=sum(rrs) / max(len(rrs), 1),
        )

    return results


def _ece(confs: List[float], outcomes: List[int], n_bins: int = 10) -> Dict[str, Any]:
    # confs in [0,1]
    if not confs or not outcomes or len(confs) != len(outcomes):
        return {"ece": None, "bins": []}

    bins = []
    ece = 0.0
    for b in range(n_bins):
        lo = b / n_bins
        hi = (b + 1) / n_bins
        idx = [i for i, c in enumerate(confs) if (c >= lo and (c < hi or (b == n_bins - 1 and c <= hi)))]
        if not idx:
            continue
        acc = sum(outcomes[i] for i in idx) / len(idx)
        conf = sum(confs[i] for i in idx) / len(idx)
        w = len(idx) / len(confs)
        ece += w * abs(acc - conf)
        bins.append({"range": [lo, hi], "count": len(idx), "acc": acc, "conf": conf})

    return {"ece": ece, "bins": bins}


def run_generation_eval(gold_path: str, k: int = 5, use_judge: bool = False) -> Dict[str, Any]:
    from app.graph.graph_builder import build_medical_graph

    graph = build_medical_graph()

    with open(gold_path, "r", encoding="utf-8") as f:
        gold = json.load(f)

    items = gold.get("retrieval", [])

    judge_scores: List[float] = []
    citation_coverage = 0
    costs: List[float] = []
    bert_groundings: List[float] = []
    # reference-based metrics
    rouge_l_f1s: List[float] = []
    bert_ref_f1s: List[float] = []

    confs: List[float] = []
    outcomes: List[int] = []
    citation_precisions: List[float] = []

    judge = None
    if use_judge:
        from app.medical_judge import MedicalJudge

        judge = MedicalJudge

    for item in items:
        q = item["query"]
        out = graph.invoke(
            {
                "question": q,
                "triage_urgent": False,
                "blocked_by_guardrail": False,
                "needs_clarification": False,
                "retrieved_docs": [],
                "final_answer": "",
                "estimated_cost": 0.0,
            }
        )

        ans = out.get("final_answer", "") or ""
        has_cite = "Sumber yang digunakan" in ans
        citation_coverage += 1 if has_cite else 0

        cost = float(out.get("estimated_cost", 0.0) or 0.0)
        costs.append(cost)

        conf_score = out.get("confidence_score")
        if conf_score is not None:
            try:
                confs.append(float(conf_score) / 100.0)
            except Exception:
                pass

        if judge is not None:
            citations_text = "\n\n".join(out.get("retrieved_docs", []) or [])
            j = judge.judge(q, ans, citations_text=citations_text)
            overall = float(j.get("overall", 0))
            judge_scores.append(overall)

            verdict = str(j.get("verdict", "FAIL")).upper()
            outcomes.append(1 if verdict == "PASS" else 0)

            print(f"[GEN {item.get('id')}] overall={overall} verdict={verdict}")

            # Optional: compute BERTScore between answer and citations_text as grounding proxy
            if bert_score is not None and citations_text.strip():
                try:
                    P, R, F1 = bert_score([ans], [citations_text], lang="en", model_type="xlm-roberta-large", rescale_with_baseline=True)
                    f = float(F1.mean().item()) if hasattr(F1, 'mean') else float(F1[0])
                    bert_groundings.append(f)
                except Exception:
                    pass

            # If reference answers are provided in gold, compute ROUGE & BERTScore vs reference
            # Accept keys: "reference" (string) or "references" (list -> take first)
            ref = None
            if isinstance(item.get("reference"), str) and item.get("reference").strip():
                ref = item.get("reference").strip()
            elif isinstance(item.get("references"), list) and item.get("references"):
                # take first reference if multiple
                r0 = item.get("references")[0]
                if isinstance(r0, str) and r0.strip():
                    ref = r0.strip()

            if ref:
                # ROUGE-L
                if rouge_scorer is not None:
                    try:
                        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
                        sc = scorer.score(ref, ans)
                        rl_f = sc.get("rougeL").fmeasure if sc.get("rougeL") else 0.0
                        rouge_l_f1s.append(rl_f)
                    except Exception:
                        pass
                # BERTScore vs reference
                if bert_score is not None:
                    try:
                        # model_type chosen for multilingual support; may be slow on CPU
                        P, R, F1 = bert_score([ans], [ref], lang="en", model_type="xlm-roberta-large", rescale_with_baseline=True)
                        fref = float(F1.mean().item()) if hasattr(F1, 'mean') else float(F1[0])
                        bert_ref_f1s.append(fref)
                    except Exception:
                        pass
            # compute citation precision: fraction of retrieved docs that are relevant
            try:
                retrieved_docs = out.get("retrieved_docs", []) or []
                parsed = _parse_citations(retrieved_docs)
                if parsed:
                    rels = [1 if _is_relevant(c, item.get("relevant", [])) else 0 for c in parsed]
                    prec = sum(rels) / len(rels)
                else:
                    prec = 0.0
                citation_precisions.append(prec)
            except Exception:
                pass

    n = max(len(items), 1)
    avg_cost = sum(costs) / max(len(costs), 1)

    cal = _ece(confs, outcomes, n_bins=10) if (use_judge and confs and outcomes) else {"ece": None, "bins": []}

    bert_avg = sum(bert_groundings) / max(len(bert_groundings), 1) if bert_groundings else None
    citation_precision_avg = sum(citation_precisions) / max(len(citation_precisions), 1) if citation_precisions else None
    rouge_l_avg = sum(rouge_l_f1s) / max(len(rouge_l_f1s), 1) if rouge_l_f1s else None
    bert_ref_avg = sum(bert_ref_f1s) / max(len(bert_ref_f1s), 1) if bert_ref_f1s else None

    return {
        "citation_coverage": citation_coverage / n,
        "judge_overall_avg": (sum(judge_scores) / max(len(judge_scores), 1)) if judge_scores else None,
        "citation_precision": citation_precision_avg,
        "avg_cost": avg_cost,
        "cost_1000": avg_cost * 1000.0,
        "ece": cal.get("ece"),
        "reliability_bins": cal.get("bins"),
        "bert_grounding_f1_avg": bert_avg,
        "rouge_l_f1_avg": rouge_l_avg,
        "bert_ref_f1_avg": bert_ref_avg,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--with-judge", action="store_true")
    parser.add_argument("--with-generation", action="store_true")
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Run retrieval metrics only and skip generation eval.",
    )
    args = parser.parse_args()

    print("Running retrieval eval...")
    results = run_retrieval_eval("app/eval_goldset.json", k=args.k)

    print("\nRETRIEVAL SUMMARY")
    for strat, m in results.items():
        print(f"[{strat.upper()}] NDCG@{args.k}: {m.ndcg_at_k:.3f} | Recall@{args.k}: {m.recall_at_k:.3f} | MRR: {m.mrr:.3f}")

    run_generation = args.with_generation or not args.retrieval_only

    if run_generation:
        print("\nRunning generation eval...")
        gen = run_generation_eval("app/eval_goldset.json", k=args.k, use_judge=args.with_judge)
        print("\nGENERATION SUMMARY")
        print(f"Citation coverage: {gen['citation_coverage']:.3f}")
        if gen.get("citation_precision") is not None:
            print(f"Citation precision (avg): {gen['citation_precision']:.3f}")
        print(f"Avg cost/query: {gen['avg_cost']:.6f}")
        print(f"Estimated cost for 1000 queries: {gen['cost_1000']:.3f}")

        if gen.get("judge_overall_avg") is not None:
            print(f"Judge overall avg: {gen['judge_overall_avg']:.3f}")

        if gen.get("ece") is not None:
            print(f"ECE (calibration error): {gen['ece']:.3f}")
            for b in gen.get('reliability_bins', []):
                r0, r1 = b['range']
                print(f"  bin {r0:.1f}-{r1:.1f}: n={b['count']} acc={b['acc']:.2f} conf={b['conf']:.2f}")
        if gen.get('bert_grounding_f1_avg') is not None:
            print(f"BERT grounding F1 (avg): {gen['bert_grounding_f1_avg']:.3f}")
        if gen.get('rouge_l_f1_avg') is not None:
            print(f"ROUGE-L F1 (avg vs reference): {gen['rouge_l_f1_avg']:.3f}")
        if gen.get('bert_ref_f1_avg') is not None:
            print(f"BERTScore F1 (avg vs reference): {gen['bert_ref_f1_avg']:.3f}")

    print("\nNote: Retrieval goldset matches by source_contains. Add page numbers & more queries for stricter evaluation. Use --retrieval-only if you want retrieval metrics only.")
