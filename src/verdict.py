import json
import os

from groq import Groq

try:
    import streamlit as st
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL = "llama-3.1-8b-instant"

client = Groq(api_key=GROQ_API_KEY)

DEFAULT_ERROR_VERDICT = {
    "verdict": "ERROR",
    "confidence": "LOW",
    "summary": "Unable to generate a verdict.",
    "supporting_points": [],
    "contradicting_points": [],
}


def _format_evidence(evidence: list) -> str:
    """Format evidence dicts into a readable string for the model."""
    if not evidence:
        return "No evidence provided."

    sections = []
    for i, item in enumerate(evidence, start=1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        snippet = item.get("snippet", "")
        sections.append(
            f"Evidence {i}:\n"
            f"Title: {title}\n"
            f"URL: {url}\n"
            f"Snippet: {snippet}"
        )

    return "\n\n".join(sections)


def _parse_verdict_json(text: str) -> dict:
    """Parse a JSON verdict from the model response."""
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Model may return Python-style single-quoted JSON from the prompt example.
        return json.loads(cleaned.replace("'", '"'))


def generate_verdict(claim: str, evidence: list) -> dict:
    """Analyze evidence and return a structured verdict for a claim."""
    system_prompt = (
        "You are a fact-checking assistant. Analyze the claim and evidence provided.\n"
        "You MUST respond with ONLY a valid JSON object, no other text, no markdown, "
        "no code fences. Use double quotes throughout.\n"
        "\n"
        "Rules:\n"
        "- supporting_points and contradicting_points must be specific factual "
        "statements drawn from the evidence. Never say 'Evidence 1 mentions' or "
        "reference evidence by number. Write actual facts.\n"
        "- Be precise about the verdict. If a claim says 'always' or 'all' or 'never',\n"
        "  check carefully — sweeping absolutes are usually REFUTED or "
        "INSUFFICIENT EVIDENCE.\n"
        "- contradicting_points should never be empty if the claim uses absolute "
        "language like 'all', 'always', 'never', 'every'.\n"
        "\n"
        "Return this exact format:\n"
        "{\n"
        '  "verdict": "SUPPORTED" or "REFUTED" or "INSUFFICIENT EVIDENCE",\n'
        '  "confidence": "HIGH" or "MEDIUM" or "LOW",\n'
        '  "summary": "2-3 sentence explanation of the verdict",\n'
        '  "supporting_points": ["specific fact 1", "specific fact 2"],\n'
        '  "contradicting_points": ["specific fact 1", "specific fact 2"]\n'
        "}"
    )

    user_message = (
        f"Claim: {claim}\n\n"
        f"Evidence:\n{_format_evidence(evidence)}"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        content = response.choices[0].message.content or ""
        return _parse_verdict_json(content)
    except json.JSONDecodeError as e:
        print(f"Failed to parse response: {e}")
        return DEFAULT_ERROR_VERDICT.copy()
    except Exception as e:
        print(f"API request failed: {e}")
        return DEFAULT_ERROR_VERDICT.copy()


if __name__ == "__main__":
    claim = "transformer models outperform RNNs on all NLP tasks"
    evidence = [
        {
            "title": "Transformers vs RNNs: A Comparative Study on NLP Benchmarks",
            "url": "https://example.com/transformers-vs-rnns",
            "snippet": (
                "Across GLUE and SuperGLUE benchmarks, transformer models consistently "
                "achieve higher accuracy than LSTM-based RNNs on classification and "
                "inference tasks."
            ),
        },
        {
            "title": "When RNNs Still Win: Low-Resource and Streaming NLP",
            "url": "https://example.com/rnn-low-resource",
            "snippet": (
                "On small datasets and streaming speech tasks, RNNs can match or exceed "
                "transformer performance due to lower data requirements and latency."
            ),
        },
        {
            "title": "Survey of Neural Architectures for NLP",
            "url": "https://example.com/nlp-architecture-survey",
            "snippet": (
                "Transformers dominate most modern NLP leaderboards, but the claim that "
                "they outperform RNNs on all NLP tasks is too broad and task-dependent."
            ),
        },
    ]

    print(f"Claim: {claim}\n")
    print("Evidence used:")
    for i, item in enumerate(evidence, start=1):
        print(f"  {i}. {item['title']}")
    print()

    verdict = generate_verdict(claim, evidence)

    print("Verdict:")
    print(f"  Status: {verdict.get('verdict', 'UNKNOWN')}")
    print(f"  Confidence: {verdict.get('confidence', 'UNKNOWN')}")
    print(f"  Summary: {verdict.get('summary', '')}")

    supporting = verdict.get("supporting_points", [])
    if supporting:
        print("\n  Supporting points:")
        for point in supporting:
            print(f"    - {point}")

    contradicting = verdict.get("contradicting_points", [])
    if contradicting:
        print("\n  Contradicting points:")
        for point in contradicting:
            print(f"    - {point}")
