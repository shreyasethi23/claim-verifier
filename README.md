# Claim Verifier

A multi-agent fact-checking system: a **planner** agent decomposes a claim, a **ReAct research agent**
searches the web, reads pages and stores evidence in **ChromaDB**, and a **verifier** agent retrieves the
best evidence and returns a **cited** verdict — with code-level guardrails on every step.

## Architecture

```
Claim
  │
  ▼
① Planner agent (GPT-OSS 20B, JSON mode)          src/agent.py
   claim → 3–5 sub-questions (incl. one looking for counter-evidence)
  │
  ▼
② Research agent — ReAct loop with tool calling    src/researcher.py
   Thought → Action → Observation, up to MAX_STEPS
   tools:  web_search(query)    DuckDuckGo → snippets stored in ChromaDB
           read_page(url)       fetch → clean → chunk (120 words, 30 overlap) → embed into ChromaDB
           search_evidence(q)   semantic search over everything gathered so far
  │                                                 src/evidence_store.py
  ▼
③ Verifier agent (GPT-OSS 120B, JSON mode)        src/verdict.py
   retrieve top chunks for the claim AND each sub-question (credibility-boosted, deduped)
   → verdict + confidence + supporting/contradicting points, each citing source ids [S1]
   → code validates every citation; uncited/fake citations dropped; unbacked verdicts downgraded
  │
  ▼
Streamlit UI: verdict, cited points, live agent trace, sources by credibility, follow-up chat
```

## Design choices

| Choice | Why |
|---|---|
| Fixed order of agents, ReAct only inside research | The overall steps are always the same (cheap, predictable); only research needs the LLM to decide what to do next |
| Model routing | Small 20B model for planning, 120B for tool use + judgment (set `FAST_MODEL` / `SMART_MODEL` in `.env` to change) |
| `temperature=0`, JSON mode | Consistent, parseable outputs |
| ChromaDB per claim run | Retrieve the most relevant passages instead of stuffing every snippet into the prompt; runs never mix evidence |
| Credibility boost in retrieval | High-credibility domains (gov/edu/journals/major news) rank above blogs and forums |
| Citation validation in code | The model can't invent sources: points must cite real source ids or they're dropped |

## Guardrails

- `MAX_STEPS = 8` and `MAX_PAGES = 4` cap cost and stop infinite loops
- Repeated identical tool calls are blocked; unknown (hallucinated) tools return an error to the model
- `read_page` only accepts URLs that came from `web_search`
- Web text is treated as untrusted data (prompt-injection defense); all tools are read-only
- Retries with exponential backoff + jitter on rate limits / server errors; permanent errors (bad key, unknown model) fail fast
- If the research agent's LLM call fails, it stops gracefully and the verifier still runs on gathered evidence
- Invalid labels → `INSUFFICIENT EVIDENCE`; LLM failure → `ERROR` verdict, app never crashes
- User input is HTML-escaped in the UI

## Run

```bash
pip install -r requirements.txt
echo "GROQ_API_KEY=your_key" > .env
streamlit run app.py                        # UI
python src/agent.py "Vaccines cause autism" # CLI with step-by-step trace
```

## Test & evaluate

```bash
python -m pytest tests -q          # offline unit tests (LLM, search and fetch are mocked)
python evals/run_eval.py           # labeled claims → accuracy per verdict class + confusion matrix
python evals/run_eval.py --limit 3 # quick smoke test
```

Run the eval on every prompt or model change to catch regressions.
