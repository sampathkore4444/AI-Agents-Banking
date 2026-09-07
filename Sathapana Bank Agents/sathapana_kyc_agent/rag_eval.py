"""
RAG evaluation: golden-question set with expected answers/collections.

`python main.py eval-rag` runs every golden question through the pipeline and
reports recall (is the question's expected collection retrieved and the golden
answer text present in the top-k context?), plus latency. Used to catch
regressions when the knowledge base, embeddings or retrieval settings change.
"""

from __future__ import annotations

from dataclasses import dataclass

from tools import get_rag

GOLDEN_SET = [
    {
        "question": "What are the required documents for individual KYC in Cambodia?",
        "collection": "nbc_regulations",
        "must_contain": ["national id", "photo"],
    },
    {
        "question": "Under what conditions is enhanced due diligence required (EDD)?",
        "collection": "risk_typologies",
        "must_contain": ["enhanced due diligence"],
    },
    {
        "question": "What is the FATF-aligned UBO threshold for beneficial ownership?",
        "collection": "nbc_regulations",
        "must_contain": ["25%", "beneficial"],
    },
    {
        "question": "How should a casino customer be risk-classified?",
        "collection": "risk_typologies",
        "must_contain": ["casino"],
    },
    {
        "question": "List the documents required for a business registration KYC file",
        "collection": "document_schemas",
        "must_contain": ["business", "registration"],
    },
    {
        "question": "What triggers a Suspicious Transaction Report (STR)?",
        "collection": "risk_typologies",
        "must_contain": ["suspicious"],
    },
    {
        "question": "What are the account opening policies for SME customers?",
        "collection": "product_policies",
        "must_contain": ["sme"],
    },
    {
        "question": "How were past high-risk gaming customers handled?",
        "collection": "past_kyc_decisions",
        "must_contain": ["gaming", "declined"],
    },
    {
        "question": "What PEP categories exist under the law and what is required?",
        "collection": "nbc_regulations",
        "must_contain": ["politically exposed"],
    },
    {
        "question": "What cash reporting thresholds apply for cash-intensive businesses?",
        "collection": "nbc_regulations",
        "must_contain": ["cash", "report"],
    },
]


@dataclass
class EvalItem:
    question: str
    expected_collection: str
    hit: bool
    recall: float
    latency_ms: float
    retrieved_collections: list[str]
    found_terms: list[str]
    missing_terms: list[str]


def run_rag_eval(top_k: int = 5) -> dict:
    rag = get_rag()
    items: list[EvalItem] = []
    for golden in GOLDEN_SET:
        import time

        t0 = time.time()
        result = rag.query(golden["question"], top_k=top_k)
        latency_ms = round((time.time() - t0) * 1000, 1)

        texts = " ".join(c.text.lower() for c in result.chunks)
        collections_hit = {c.collection for c in result.chunks}
        found = [term for term in golden["must_contain"] if term.lower() in texts]
        missing = [term for term in golden["must_contain"] if term.lower() not in texts]
        hit = golden["collection"] in collections_hit and not missing
        recall = len(found) / len(golden["must_contain"])
        items.append(
            EvalItem(
                question=golden["question"],
                expected_collection=golden["collection"],
                hit=hit,
                recall=recall,
                latency_ms=latency_ms,
                retrieved_collections=sorted(collections_hit),
                found_terms=found,
                missing_terms=missing,
            )
        )

    hits = sum(1 for i in items if i.hit)
    avg_recall = sum(i.recall for i in items) / len(items)
    avg_latency = sum(i.latency_ms for i in items) / len(items)
    return {
        "items": items,
        "hit_rate": hits / len(items),
        "avg_recall": round(avg_recall, 3),
        "avg_latency_ms": round(avg_latency, 1),
        "questions": len(items),
        "top_k": top_k,
    }


def print_rag_eval() -> None:
    report = run_rag_eval()
    sep = "=" * 78
    print(sep)
    print(f"RAG EVALUATION ({report['questions']} golden questions, top_k={report['top_k']})")
    print(sep)
    for item in report["items"]:
        mark = "PASS" if item.hit else "FAIL"
        status = "ok" if item.hit else "miss"
        extra = f" found={item.found_terms} missing={item.missing_terms}" if status == "miss" else ""
        print(
            f"  [{mark}] {item.question[:66]:66s} recall={item.recall:.2f} ({item.latency_ms}ms)"
            f" -> {','.join(item.retrieved_collections)}{extra}"
        )
    print(sep)
    print(f"  hit_rate={report['hit_rate']:.2f}  avg_recall={report['avg_recall']:.2f}  avg_latency_ms={report['avg_latency_ms']}")
    print(sep)