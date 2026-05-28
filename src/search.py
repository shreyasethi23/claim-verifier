from ddgs import DDGS


def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search the web via DuckDuckGo and return normalized result dicts."""
    try:
        with DDGS() as ddgs:
            raw_results = ddgs.text(query, max_results=max_results)

        if not raw_results:
            return []

        return [
            {
                "title": result.get("title", ""),
                "url": result.get("href", ""),
                "snippet": result.get("body", ""),
            }
            for result in raw_results
        ]
    except Exception as e:
        print(f"Search failed: {e}")
        return []


if __name__ == "__main__":
    query = "transformer models outperform RNNs"
    print(f"Searching for: {query!r}\n")

    results = search_web(query)

    if not results:
        print("No results found.")
    else:
        for i, result in enumerate(results, start=1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   {result['snippet']}")
            print()
