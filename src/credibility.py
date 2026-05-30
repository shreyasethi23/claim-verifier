# Credibility tiers for source domains
HIGH_CREDIBILITY = [
    "nature.com", "science.org", "pubmed.ncbi.nlm.nih.gov", "scholar.google.com",
    "nasa.gov", "who.int", "cdc.gov", "nih.gov", "bbc.com", "reuters.com",
    "apnews.com", "theguardian.com", "nytimes.com", "washingtonpost.com",
    "economist.com", "scientificamerican.com", "newscientist.com",
    "ipcc.ch", "un.org", "gov.uk", "edu", "ac.uk"
]

MEDIUM_CREDIBILITY = [
    "wikipedia.org", "britannica.com", "investopedia.com", "healthline.com",
    "mayoclinic.org", "webmd.com", "techcrunch.com", "wired.com",
    "arstechnica.com", "theatlantic.com", "vox.com", "bloomberg.com"
]

LOW_CREDIBILITY = [
    "reddit.com", "quora.com", "medium.com", "substack.com",
    "wordpress.com", "blogspot.com", "tumblr.com"
]


def get_credibility(url: str) -> dict:
    """
    Given a URL, return a credibility dict with:
    - tier: "HIGH", "MEDIUM", "LOW", "UNKNOWN"
    - label: human readable label
    - color: emoji indicator
    """
    url_lower = url.lower()

    for domain in HIGH_CREDIBILITY:
        if domain in url_lower:
            return {"tier": "HIGH", "label": "High credibility", "color": "🟢"}

    for domain in MEDIUM_CREDIBILITY:
        if domain in url_lower:
            return {"tier": "MEDIUM", "label": "Medium credibility", "color": "🟡"}

    for domain in LOW_CREDIBILITY:
        if domain in url_lower:
            return {"tier": "LOW", "label": "Low credibility", "color": "🔴"}

    return {"tier": "UNKNOWN", "label": "Unknown credibility", "color": "⚪"}


def score_evidence(evidence: list) -> list:
    """
    Takes a list of evidence dicts and adds credibility info to each.
    Returns the same list with credibility added, sorted by tier.
    """
    tier_order = {"HIGH": 0, "MEDIUM": 1, "UNKNOWN": 2, "LOW": 3}

    for item in evidence:
        item["credibility"] = get_credibility(item.get("url", ""))

    return sorted(evidence, key=lambda x: tier_order[x["credibility"]["tier"]])
