"""Offline tests: no API key or internet needed (LLM, search and page fetches are mocked).

    python -m pytest tests -q
"""
import json
import os
import sys
import zlib
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("GROQ_API_KEY", "test-key")

import evidence_store  # noqa: E402
import researcher  # noqa: E402
import verdict  # noqa: E402
import agent  # noqa: E402
from chromadb import Documents, EmbeddingFunction, Embeddings  # noqa: E402


class BagOfWordsEmbedding(EmbeddingFunction):
    """Tiny deterministic embedding so tests don't download a model."""
    def __init__(self):
        pass

    def __call__(self, input: Documents) -> Embeddings:
        out = []
        for doc in input:
            v = np.zeros(64)
            for w in doc.lower().split():
                v[zlib.crc32(w.strip(".,").encode()) % 64] += 1   # stable across runs (hash() is randomized)
            out.append(v / (np.linalg.norm(v) or 1))
        return out


def make_store():
    return evidence_store.EvidenceStore(embedding_function=BagOfWordsEmbedding())


def tool_call(name, args, i):
    return SimpleNamespace(id=f"call_{i}", function=SimpleNamespace(name=name, arguments=json.dumps(args)))


# ---------- chunking ----------
def test_chunking_overlaps_and_skips_tiny():
    text = " ".join(f"w{i}" for i in range(300))
    chunks = evidence_store.chunk_text(text, size=120, overlap=30)
    assert len(chunks) == 3
    assert chunks[0].split()[-30:] == chunks[1].split()[:30]     # overlap preserved
    assert evidence_store.chunk_text("too short") == []


# ---------- ChromaDB store ----------
def test_store_retrieves_relevant_chunk_and_boosts_credibility(monkeypatch):
    store = make_store()
    store.add_snippet("https://www.who.int/vaccines", "WHO", "large studies find no link between vaccines and autism in children")
    store.add_snippet("https://reddit.com/r/x", "Reddit", "my cousin says vaccines and autism are linked somehow")
    store.add_snippet("https://example.com/cake", "Cake", "how to bake a chocolate cake with butter and sugar")
    hits = store.search("vaccines autism link", k=2)
    assert {h["source_id"] for h in hits} == {"S1", "S2"}
    assert hits[0]["source_id"] == "S1"                            # HIGH credibility ranks first
    assert store.sources["S1"]["credibility"]["tier"] == "HIGH"


def test_add_page_chunks_into_chroma(monkeypatch):
    monkeypatch.setattr(evidence_store, "fetch_page_text",
                        lambda url: " ".join(["measles vaccine safety study cohort"] * 60))
    store = make_store()
    sid, n = store.add_page("https://nih.gov/study", "NIH study")
    assert sid == "S1" and n >= 2
    assert store.collection.count() == n


# ---------- ReAct researcher ----------
def test_react_loop_calls_tools_dedupes_and_stops(monkeypatch):
    monkeypatch.setattr(researcher, "search_web", lambda q, max_results=5: [
        {"title": "WHO on vaccines", "url": "https://www.who.int/v", "snippet": "no link between vaccines and autism was found"},
        {"title": "Blog", "url": "https://blogspot.com/b", "snippet": "vaccines are dangerous says a blog post here"},
    ])
    monkeypatch.setattr(evidence_store, "fetch_page_text",
                        lambda url: " ".join(["a cohort of 650000 children found no autism link"] * 30))

    script = [  # what the fake LLM "decides" at each step
        SimpleNamespace(content="Thought: search first.", tool_calls=[tool_call("web_search", {"query": "vaccines autism"}, 1)]),
        SimpleNamespace(content="Thought: read the WHO page.", tool_calls=[tool_call("read_page", {"url": "https://www.who.int/v"}, 2)]),
        SimpleNamespace(content="Thought: repeat (should be blocked).", tool_calls=[tool_call("web_search", {"query": "vaccines autism"}, 3)]),
        SimpleNamespace(content="Thought: a made-up tool.", tool_calls=[tool_call("delete_everything", {}, 4)]),
        SimpleNamespace(content="Enough evidence: no link found.", tool_calls=None),
    ]
    calls = []

    def fake_llm(messages, model=None, tools=None):
        calls.append(messages)
        return script[len(calls) - 1]

    store = make_store()
    agent_ = researcher.ResearchAgent(store, llm=fake_llm)
    summary = agent_.run("Vaccines cause autism", ["Is there a link?"])

    actions = [t["action"] for t in agent_.trace]
    assert actions == ["web_search", "read_page", "web_search", "delete_everything", "finish"]
    assert "already made this exact call" in agent_.trace[2]["observation"]
    assert "Unknown tool" in agent_.trace[3]["observation"]
    assert summary.startswith("Enough evidence")
    assert store.collection.count() > 2                      # snippets + page chunks stored
    assert any(m["role"] == "tool" for m in calls[-1])       # observations fed back to the model


def test_react_loop_respects_max_steps(monkeypatch):
    monkeypatch.setattr(researcher, "search_web", lambda q, max_results=5: [])
    n = {"i": 0}

    def looping_llm(messages, model=None, tools=None):
        n["i"] += 1
        return SimpleNamespace(content="", tool_calls=[tool_call("web_search", {"query": f"q{n['i']}"}, n["i"])])

    agent_ = researcher.ResearchAgent(make_store(), llm=looping_llm)
    assert agent_.run("c", ["q"]) == "Stopped at step limit."
    assert n["i"] == researcher.MAX_STEPS


def test_read_page_only_allows_urls_from_search():
    agent_ = researcher.ResearchAgent(make_store(), llm=None)
    assert "Only read URLs returned by web_search" in agent_._read_page("https://evil.example/inject")


# ---------- verifier guardrails ----------
EVIDENCE = [{"source_id": "S1", "url": "u1", "title": "t", "text": "x", "credibility": "HIGH", "score": 0.9},
            {"source_id": "S2", "url": "u2", "title": "t", "text": "y", "credibility": "LOW", "score": 0.5}]


def test_verifier_drops_fake_citations_and_downgrades():
    fake = lambda messages, model=None: {  # noqa: E731
        "verdict": "SUPPORTED", "confidence": "HIGH", "summary": "s",
        "supporting_points": [{"point": "made up", "sources": ["S9"]}], "contradicting_points": []}
    out = verdict.generate_verdict("c", EVIDENCE, llm=fake)
    assert out["verdict"] == "INSUFFICIENT EVIDENCE" and out["confidence"] == "LOW"
    assert any("S9" in i for i in out["citation_issues"])


def test_verifier_keeps_valid_citations():
    fake = lambda messages, model=None: {  # noqa: E731
        "verdict": "REFUTED", "confidence": "HIGH", "summary": "s",
        "supporting_points": [], "contradicting_points": [{"point": "large study, no link", "sources": ["S1"]}]}
    out = verdict.generate_verdict("c", EVIDENCE, llm=fake)
    assert out["verdict"] == "REFUTED" and out["contradicting_points"][0]["sources"] == ["S1"]
    assert out["citation_issues"] == []


def test_verifier_handles_invalid_labels_and_llm_failure():
    fake = lambda messages, model=None: {"verdict": "TRUE!!", "confidence": "VERY",  # noqa: E731
                                         "summary": "s", "supporting_points": [], "contradicting_points": []}
    out = verdict.generate_verdict("c", EVIDENCE, llm=fake)
    assert out["verdict"] == "INSUFFICIENT EVIDENCE" and out["confidence"] == "LOW"

    def boom(messages, model=None):
        raise ValueError("bad json")
    assert verdict.generate_verdict("c", EVIDENCE, llm=boom)["verdict"] == "ERROR"
    assert verdict.generate_verdict("c", [])["verdict"] == "INSUFFICIENT EVIDENCE"


def test_gather_evidence_covers_each_subquestion_and_dedupes():
    store = make_store()
    store.add_snippet("https://nasa.gov/a", "A", "the great wall is not visible from low earth orbit with naked eye")
    store.add_snippet("https://bbc.com/b", "B", "astronauts report cities lights visible from space at night clearly")
    ev = verdict.gather_evidence(store, "great wall visible from space", ["can astronauts see cities"])
    ids = [e["source_id"] for e in ev]
    assert set(ids) == {"S1", "S2"} and len(ids) == len(set((e["source_id"], e["text"][:80]) for e in ev))


# ---------- planner ----------
def test_planner_parses_and_falls_back():
    ok = lambda messages, model=None: {"sub_questions": ["a", " ", "b", "c", "d", "e", "f"]}  # noqa: E731
    assert agent.decompose_claim("claim", llm=ok) == ["a", "b", "c", "d", "e"]

    def boom(messages, model=None):
        raise ValueError("not json")
    assert agent.decompose_claim("claim", llm=boom) == ["claim"]


# ---------- error handling ----------
import llm  # noqa: E402


class FakeAPIError(Exception):
    def __init__(self, status_code):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


def test_permanent_errors_fail_fast_but_rate_limits_retry(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    calls = {"n": 0}

    def fake_create(status):
        def create(**kw):
            calls["n"] += 1
            raise FakeAPIError(status)
        return create

    for status, expected_calls in [(404, 1), (401, 1), (429, 3), (503, 3)]:
        calls["n"] = 0
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create(status))))
        monkeypatch.setattr(llm, "get_client", lambda c=client: c)
        try:
            llm.chat([{"role": "user", "content": "hi"}])
        except RuntimeError:
            pass
        assert calls["n"] == expected_calls, (status, calls["n"])


def test_research_agent_stops_gracefully_on_llm_failure():
    def broken_llm(messages, model=None, tools=None):
        raise RuntimeError("model not found")
    agent_ = researcher.ResearchAgent(make_store(), llm=broken_llm)
    out = agent_.run("claim", ["q"])
    assert out.startswith("Research stopped early")
    assert agent_.trace[-1]["action"] == "error"
