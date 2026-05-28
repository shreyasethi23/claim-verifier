import re

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "out", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all",
    "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "and",
    "but", "or", "if", "while", "that", "this", "these", "those", "it", "its",
}


def _extract_keywords(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if len(word) > 2 and word not in STOP_WORDS}


class ClaimMemory:
    """In-memory store for previously verified claims."""

    def __init__(self) -> None:
        self._claims: list[dict] = []

    def add_claim(self, claim: str, verdict_dict: dict) -> None:
        self._claims.append({"claim": claim, "verdict": verdict_dict})

    def get_past_claims(self) -> list[dict]:
        return list(self._claims)

    def find_similar(self, claim: str) -> dict | None:
        claim_keywords = _extract_keywords(claim)
        if not claim_keywords:
            return None

        for entry in self._claims:
            past_keywords = _extract_keywords(entry["claim"])
            if not past_keywords:
                continue

            overlap = claim_keywords & past_keywords
            if len(overlap) >= 2 or (
                len(overlap) >= 1 and len(overlap) / len(claim_keywords) >= 0.5
            ):
                return entry

        return None
