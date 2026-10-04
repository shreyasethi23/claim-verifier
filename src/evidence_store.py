"""Evidence store: fetch web pages, chunk them, embed into ChromaDB, retrieve by similarity."""
import re
import uuid

import chromadb
import requests
from bs4 import BeautifulSoup

try:
    from .credibility import get_credibility
except ImportError:
    from credibility import get_credibility

CHUNK_WORDS = 120      # ~1 paragraph per chunk
OVERLAP_WORDS = 30     # overlap so a fact split across a boundary isn't lost
MAX_PAGE_WORDS = 3000  # don't embed giant pages
HEADERS = {"User-Agent": "Mozilla/5.0 (claim-verifier research bot)"}


def fetch_page_text(url: str, timeout: int = 8) -> str:
    """Download a page and return its readable text ('' on failure)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        if "text/html" not in resp.headers.get("Content-Type", "text/html"):
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            tag.decompose()
        text = " ".join(soup.get_text(" ").split())
        return " ".join(text.split()[:MAX_PAGE_WORDS])
    except Exception:
        return ""


def chunk_text(text: str, size: int = CHUNK_WORDS, overlap: int = OVERLAP_WORDS) -> list[str]:
    """Split text into overlapping word windows."""
    words = text.split()
    if not words:
        return []
    chunks, step = [], size - overlap
    for start in range(0, len(words), step):
        piece = words[start:start + size]
        if len(piece) >= 20:              # skip tiny fragments
            chunks.append(" ".join(piece))
        if start + size >= len(words):
            break
    return chunks


class EvidenceStore:
    """One ChromaDB collection per claim run, so different claims never mix evidence."""

    def __init__(self, embedding_function=None):
        self.client = chromadb.EphemeralClient()
        kwargs = {"metadata": {"hnsw:space": "cosine"}}
        if embedding_function is not None:
            kwargs["embedding_function"] = embedding_function
        self.collection = self.client.create_collection(f"claim_{uuid.uuid4().hex[:12]}", **kwargs)
        self.sources = {}          # source_id -> {title, url, credibility}
        self._url_to_id = {}

    def _source_id(self, url: str, title: str) -> str:
        if url not in self._url_to_id:
            sid = f"S{len(self._url_to_id) + 1}"
            self._url_to_id[url] = sid
            self.sources[sid] = {"title": title, "url": url, "credibility": get_credibility(url)}
        return self._url_to_id[url]

    def add_snippet(self, url: str, title: str, snippet: str) -> str:
        """Store a search-result snippet (cheap, always available)."""
        sid = self._source_id(url, title)
        if snippet and len(snippet.split()) >= 5:
            self.collection.upsert(
                ids=[f"{sid}-snippet"],
                documents=[snippet],
                metadatas=[{"source_id": sid, "url": url, "title": title, "kind": "snippet"}],
            )
        return sid

    def add_page(self, url: str, title: str = "") -> tuple[str, int]:
        """Fetch a full page, chunk it and embed the chunks. Returns (source_id, n_chunks)."""
        sid = self._source_id(url, title or url)
        chunks = chunk_text(fetch_page_text(url))
        if chunks:
            self.collection.upsert(
                ids=[f"{sid}-c{i}" for i in range(len(chunks))],
                documents=chunks,
                metadatas=[{"source_id": sid, "url": url, "title": title, "kind": "page"} for _ in chunks],
            )
        return sid, len(chunks)

    def search(self, query: str, k: int = 5) -> list[dict]:
        """Semantic search; re-rank by similarity + a small credibility boost."""
        if self.collection.count() == 0:
            return []
        res = self.collection.query(query_texts=[query], n_results=min(k * 2, self.collection.count()))
        boost = {"HIGH": 0.10, "MEDIUM": 0.05, "UNKNOWN": 0.0, "LOW": -0.10}
        hits = []
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            sid = meta["source_id"]
            tier = self.sources[sid]["credibility"]["tier"]
            hits.append({
                "source_id": sid,
                "url": meta["url"],
                "title": meta.get("title", ""),
                "text": doc,
                "credibility": tier,
                "score": round((1 - dist) + boost[tier], 4),
            })
        hits.sort(key=lambda h: h["score"], reverse=True)
        return hits[:k]


def clean(text: str, limit: int = 600) -> str:
    """Collapse whitespace and cap length before putting web text into a prompt."""
    return re.sub(r"\s+", " ", text or "").strip()[:limit]
