import ast
import os

from groq import Groq

try:
    from .search import search_web
    from .verdict import generate_verdict
except ImportError:
    from search import search_web
    from verdict import generate_verdict

try:
    import streamlit as st
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL = "llama-3.1-8b-instant"
SYSTEM_PROMPT = (
    "You are a fact-checking assistant. Given a claim, break it down into "
    "3-5 specific search queries that would help verify or refute it. "
    'Return ONLY a Python list of strings, nothing else. '
    'Example: ["query 1", "query 2", "query 3"]'
)

client = Groq(api_key=GROQ_API_KEY)


def _parse_query_list(text: str) -> list[str]:
    """Parse a Python list of strings from the model response."""
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

    parsed = ast.literal_eval(cleaned)
    if not isinstance(parsed, list):
        raise ValueError("Response is not a list")

    queries = [str(item).strip() for item in parsed if str(item).strip()]
    if not queries:
        raise ValueError("Response list is empty")

    return queries


def decompose_claim(claim: str) -> list[str]:
    """Break a claim into search queries using Groq."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": claim},
            ],
        )
        content = response.choices[0].message.content or ""
        return _parse_query_list(content)
    except (SyntaxError, ValueError) as e:
        print(f"Failed to parse response: {e}")
        return [claim]
    except Exception as e:
        print(f"API request failed: {e}")
        return [claim]


def run_pipeline(claim: str) -> dict:
    """Run the full claim verification pipeline."""
    sub_questions = decompose_claim(claim)

    all_evidence = []
    for question in sub_questions:
        all_evidence.extend(search_web(question))

    return {
        "claim": claim,
        "sub_questions": sub_questions,
        "evidence": all_evidence,
        "verdict": generate_verdict(claim, all_evidence[:10]),
    }


if __name__ == "__main__":
    claim = "climate change is fake news"
    print(f"Running pipeline for: {claim!r}\n")

    result = run_pipeline(claim)

    print("Sub-questions:")
    for i, question in enumerate(result["sub_questions"], start=1):
        print(f"  {i}. {question}")

    print(f"\nEvidence ({len(result['evidence'])} results):")
    for i, item in enumerate(result["evidence"], start=1):
        print(f"  {i}. {item['title']}")
        print(f"     {item['url']}")

    verdict = result["verdict"]
    print("\nVerdict:")
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
