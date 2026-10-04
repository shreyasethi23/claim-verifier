"""Orchestrator: Planner agent -> Researcher agent (ReAct + ChromaDB) -> Verifier agent.

The ORDER of the three agents is a fixed workflow (predictable, cheap);
the Researcher is the only part where the LLM chooses its own next step.
"""
try:
    from .evidence_store import EvidenceStore
    from .llm import FAST_MODEL, chat_json
    from .researcher import ResearchAgent
    from .verdict import gather_evidence, generate_verdict
except ImportError:
    from evidence_store import EvidenceStore
    from llm import FAST_MODEL, chat_json
    from researcher import ResearchAgent
    from verdict import gather_evidence, generate_verdict

PLANNER_PROMPT = (
    "You are a fact-checking planner. Break the claim into 3-5 specific, independently searchable "
    "sub-questions that together would verify or refute it. Include at least one question that looks "
    "for counter-evidence. Return JSON: {\"sub_questions\": [\"...\", \"...\"]}"
)


def decompose_claim(claim: str, llm=chat_json) -> list[str]:
    """Planner agent (small fast model: an easy task -> model routing)."""
    try:
        data = llm([{"role": "system", "content": PLANNER_PROMPT},
                    {"role": "user", "content": claim}], model=FAST_MODEL)
        qs = [str(q).strip() for q in data.get("sub_questions", []) if str(q).strip()]
        return qs[:5] or [claim]
    except Exception as e:
        print(f"Planner failed, falling back to the raw claim: {e}")
        return [claim]


def run_pipeline(claim: str, on_stage=None, on_step=None, embedding_function=None) -> dict:
    """Run all three agents. on_stage(name) / on_step(trace_entry) let the UI show live progress."""
    def stage(name):
        if on_stage:
            on_stage(name)

    stage("plan")
    sub_questions = decompose_claim(claim)

    stage("research")
    store = EvidenceStore(embedding_function=embedding_function)
    researcher = ResearchAgent(store)
    research_summary = researcher.run(claim, sub_questions, on_step=on_step)

    stage("verify")
    evidence = gather_evidence(store, claim, sub_questions)
    verdict = generate_verdict(claim, evidence)

    return {
        "claim": claim,
        "sub_questions": sub_questions,
        "research_summary": research_summary,
        "trace": researcher.trace,
        "evidence": evidence,
        "sources": store.sources,
        "verdict": verdict,
    }


if __name__ == "__main__":
    import sys
    claim = " ".join(sys.argv[1:]) or "Transformers outperform RNNs on all NLP tasks"
    result = run_pipeline(claim, on_stage=lambda s: print(f"\n== {s.upper()} =="),
                          on_step=lambda e: print(f"  step {e['step']}: {e['action']} {e['args']}"))
    v = result["verdict"]
    print(f"\nVerdict: {v['verdict']} ({v['confidence']})\n{v['summary']}")
    for p in v["supporting_points"]:
        print("  +", p["point"], p["sources"])
    for p in v["contradicting_points"]:
        print("  -", p["point"], p["sources"])
    if v.get("citation_issues"):
        print("Citation issues:", v["citation_issues"])

    # ChromaDB's ONNX runtime can abort while shutting down on macOS; exit cleanly after printing.
    import os
    sys.stdout.flush()
    os._exit(0)
