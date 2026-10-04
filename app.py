import html

import streamlit as st

st.set_page_config(page_title="Claim Verifier", page_icon="🔍", layout="centered")

if "view" not in st.session_state:
    st.session_state.view = "landing"
if "claim" not in st.session_state:
    st.session_state.claim = ""
if "result" not in st.session_state:
    st.session_state.result = None

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;500&display=swap');
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.block-container { padding-top: 2rem; max-width: 750px; }
.cv-nav { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2.5rem; }
.cv-logo { display: flex; align-items: center; gap: 10px; }
.cv-logo-mark { width: 34px; height: 34px; background: #EEEDFE; border: 0.5px solid #AFA9EC; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; }
.cv-logo-text { font-family: 'DM Serif Display', serif; font-size: 20px; color: #1a1a1a; }
.cv-nav-badge { font-family: 'DM Mono', monospace; font-size: 11px; color: #534AB7; background: #EEEDFE; border: 0.5px solid #AFA9EC; padding: 4px 12px; border-radius: 20px; }
.cv-pill { display: inline-block; font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: 0.1em; color: #0F6E56; background: #E1F5EE; border: 0.5px solid #5DCAA5; padding: 5px 14px; border-radius: 20px; margin-bottom: 1.2rem; }
.cv-h1 { font-family: 'DM Serif Display', serif; font-size: 40px; line-height: 1.15; color: #1a1a1a; margin-bottom: 1rem; text-align: center; }
.cv-h1 em { font-style: italic; color: #534AB7; }
.cv-sub { font-family: 'Outfit', sans-serif; font-size: 16px; color: #666; line-height: 1.7; font-weight: 300; text-align: center; max-width: 480px; margin: 0 auto 2rem; }
.cv-ex-label { font-family: 'DM Mono', monospace; font-size: 11px; color: #aaa; letter-spacing: 0.08em; margin-bottom: 8px; }
.cv-how-title { font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 500; letter-spacing: 0.08em; color: #aaa; text-transform: uppercase; margin: 2rem 0 1rem; display: flex; align-items: center; gap: 10px; }
.cv-how-title::after { content: ''; flex: 1; height: 0.5px; background: #eee; }
.cv-step { background: white; border: 0.5px solid #eee; border-radius: 12px; padding: 1rem; }
.cv-step-num { font-family: 'DM Mono', monospace; font-size: 11px; color: #bbb; margin-bottom: 10px; }
.cv-step-icon { font-size: 22px; margin-bottom: 8px; }
.cv-step-title { font-family: 'Outfit', sans-serif; font-size: 14px; font-weight: 500; color: #1a1a1a; margin-bottom: 4px; }
.cv-step-desc { font-family: 'Outfit', sans-serif; font-size: 12px; color: #888; line-height: 1.6; }
.cv-verdict-supported { background: #EAF3DE; border: 0.5px solid #97C459; border-radius: 12px; padding: 1rem; }
.cv-verdict-refuted { background: #FCEBEB; border: 0.5px solid #F09595; border-radius: 12px; padding: 1rem; }
.cv-verdict-insufficient { background: #FAEEDA; border: 0.5px solid #EF9F27; border-radius: 12px; padding: 1rem; }
.cv-vtag-s { font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500; color: #27500A; letter-spacing: 0.08em; margin-bottom: 8px; display: block; }
.cv-vtag-r { font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500; color: #791F1F; letter-spacing: 0.08em; margin-bottom: 8px; display: block; }
.cv-vtag-i { font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500; color: #633806; letter-spacing: 0.08em; margin-bottom: 8px; display: block; }
.cv-vclaim-s { font-family: 'Outfit', sans-serif; font-size: 13px; color: #3B6D11; line-height: 1.5; margin-bottom: 8px; }
.cv-vclaim-r { font-family: 'Outfit', sans-serif; font-size: 13px; color: #A32D2D; line-height: 1.5; margin-bottom: 8px; }
.cv-vclaim-i { font-family: 'Outfit', sans-serif; font-size: 13px; color: #854F0B; line-height: 1.5; margin-bottom: 8px; }
.cv-vconf-s { font-family: 'DM Mono', monospace; font-size: 11px; color: #639922; }
.cv-vconf-r { font-family: 'DM Mono', monospace; font-size: 11px; color: #E24B4A; }
.cv-vconf-i { font-family: 'DM Mono', monospace; font-size: 11px; color: #BA7517; }
.cv-tech-card { background: #f9f9f9; border-radius: 10px; padding: 1rem; display: flex; align-items: center; gap: 12px; }
.cv-tech-icon { width: 36px; height: 36px; border-radius: 8px; background: white; border: 0.5px solid #eee; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.cv-tech-name { font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 500; color: #1a1a1a; }
.cv-tech-role { font-family: 'Outfit', sans-serif; font-size: 11px; color: #aaa; }
.cv-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 1.5rem; margin-top: 2rem; border-top: 0.5px solid #eee; }
.cv-footer-l { font-family: 'Outfit', sans-serif; font-size: 12px; color: #bbb; }
.cv-footer-r { font-family: 'DM Mono', monospace; font-size: 11px; color: #bbb; }
.stButton > button[kind="primary"] {
    background-color: #534AB7;
    border-color: #534AB7;
    color: white;
    font-family: 'Outfit', sans-serif;
    font-size: 15px;
    font-weight: 500;
    height: 48px;
    border-radius: 10px;
}
.stButton > button[kind="primary"]:hover {
    background-color: #3C3489;
    border-color: #3C3489;
}
</style>
""", unsafe_allow_html=True)

if st.session_state.view == "landing":

    st.markdown("""
    <div class="cv-nav">
        <div class="cv-logo">
            <div class="cv-logo-mark">⌕</div>
            <span class="cv-logo-text">Claim Verifier</span>
        </div>
        <span class="cv-nav-badge">MS CS · USC · 2026</span>
    </div>
    <div style="text-align:center; margin-bottom: 2rem;">
        <span class="cv-pill">Agentic fact-checking</span>
        <h1 class="cv-h1">Is it true, or is it<br><em>just a claim?</em></h1>
        <p class="cv-sub">A multi-agent system that decomposes any claim, researches it with a ReAct agent, stores evidence in a vector database, and returns a cited verdict.</p>
    </div>
    """, unsafe_allow_html=True)

    if "claim_input" not in st.session_state:
        st.session_state.claim_input = ""

    claim_input = st.text_area(
        "",
        value=st.session_state.claim_input,
        placeholder="e.g. climate change is fake news",
        height=80,
        label_visibility="collapsed",
        key=f"claim_text_area_{st.session_state.claim_input}"
    )
    st.session_state.claim_input = claim_input

    st.markdown('<p class="cv-ex-label">Try an example</p>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Vaccines cause autism", use_container_width=True):
            st.session_state.claim_input = "Vaccines cause autism"
            st.session_state.claim = "Vaccines cause autism"
            st.session_state.view = "results"
            st.session_state.result = None
            st.rerun()
    with col2:
        if st.button("Transformers outperform RNNs", use_container_width=True):
            st.session_state.claim_input = "Transformers outperform RNNs on all NLP tasks"
            st.session_state.claim = "Transformers outperform RNNs on all NLP tasks"
            st.session_state.view = "results"
            st.session_state.result = None
            st.rerun()
    with col3:
        if st.button("Climate change is fake news", use_container_width=True):
            st.session_state.claim_input = "Climate change is fake news"
            st.session_state.claim = "Climate change is fake news"
            st.session_state.view = "results"
            st.session_state.result = None
            st.rerun()
    with col4:
        if st.button("LLMs cannot reason", use_container_width=True):
            st.session_state.claim_input = "LLMs cannot reason"
            st.session_state.claim = "LLMs cannot reason"
            st.session_state.view = "results"
            st.session_state.result = None
            st.rerun()

    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

    if st.button("Verify Claim", type="primary", use_container_width=True):
        if st.session_state.claim_input.strip():
            st.session_state.claim = st.session_state.claim_input
            st.session_state.view = "results"
            st.session_state.result = None
            st.rerun()
        else:
            st.warning("Please enter a claim or pick an example above.")

    st.markdown("""
    <div class="cv-how-title">How it works</div>
    """, unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("""
        <div class="cv-step">
            <div class="cv-step-num">01</div>
            <div class="cv-step-icon">🔀</div>
            <div class="cv-step-title">Plan</div>
            <div class="cv-step-desc">Planner agent breaks your claim into 3–5 targeted sub-questions.</div>
        </div>""", unsafe_allow_html=True)
    with s2:
        st.markdown("""
        <div class="cv-step">
            <div class="cv-step-num">02</div>
            <div class="cv-step-icon">🌐</div>
            <div class="cv-step-title">Research</div>
            <div class="cv-step-desc">ReAct research agent searches, reads pages and stores evidence in ChromaDB.</div>
        </div>""", unsafe_allow_html=True)
    with s3:
        st.markdown("""
        <div class="cv-step">
            <div class="cv-step-num">03</div>
            <div class="cv-step-icon">⚖️</div>
            <div class="cv-step-title">Verdict</div>
            <div class="cv-step-desc">Verifier agent retrieves the best evidence and returns a cited verdict.</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="cv-how-title">Possible verdicts</div>', unsafe_allow_html=True)

    v1, v2, v3 = st.columns(3)
    with v1:
        st.markdown("""
        <div class="cv-verdict-supported">
            <span class="cv-vtag-s">SUPPORTED</span>
            <p class="cv-vclaim-s">"Exercise reduces risk of cardiovascular disease"</p>
            <span class="cv-vconf-s">HIGH confidence · 12 sources</span>
        </div>""", unsafe_allow_html=True)
    with v2:
        st.markdown("""
        <div class="cv-verdict-refuted">
            <span class="cv-vtag-r">REFUTED</span>
            <p class="cv-vclaim-r">"Climate change is fake news"</p>
            <span class="cv-vconf-r">HIGH confidence · 25 sources</span>
        </div>""", unsafe_allow_html=True)
    with v3:
        st.markdown("""
        <div class="cv-verdict-insufficient">
            <span class="cv-vtag-i">INSUFFICIENT</span>
            <p class="cv-vclaim-i">"AGI will be achieved by 2027"</p>
            <span class="cv-vconf-i">LOW confidence · 8 sources</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="cv-how-title">Built with</div>', unsafe_allow_html=True)

    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("""
        <div class="cv-tech-card">
            <div class="cv-tech-icon">⚡</div>
            <div><div class="cv-tech-name">Groq + Llama 3</div><div class="cv-tech-role">LLM inference</div></div>
        </div>""", unsafe_allow_html=True)
    with t2:
        st.markdown("""
        <div class="cv-tech-card">
            <div class="cv-tech-icon">🔍</div>
            <div><div class="cv-tech-name">DuckDuckGo</div><div class="cv-tech-role">Web search</div></div>
        </div>""", unsafe_allow_html=True)
    with t3:
        st.markdown("""
        <div class="cv-tech-card">
            <div class="cv-tech-icon">🧠</div>
            <div><div class="cv-tech-name">ChromaDB</div><div class="cv-tech-role">Evidence retrieval</div></div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="cv-footer">
        <span class="cv-footer-l">Shreya Sethi · MS Computer Science · USC 2026</span>
        <span class="cv-footer-r">claim-verifier v0.2</span>
    </div>""", unsafe_allow_html=True)

elif st.session_state.view == "results":

    if st.button("← New claim"):
        st.session_state.view = "landing"
        st.session_state.claim = ""
        st.session_state.result = None
        st.session_state.chat_history = []
        st.rerun()

    st.markdown(f"<h3 style='font-family: DM Serif Display, serif; margin-bottom: 1.5rem;'>Verifying: <em style='color:#534AB7'>{html.escape(st.session_state.claim)}</em></h3>", unsafe_allow_html=True)

    if st.session_state.result is None:
        from src.agent import run_pipeline

        progress_container = st.empty()
        with progress_container.container():
            st.markdown("#### Researching your claim...")
            s_plan = st.status("🧭 Planner agent: breaking the claim into sub-questions...", expanded=False)
            s_research = st.status("🔎 Research agent (ReAct): searching, reading, storing evidence...", expanded=True)
            s_verify = st.status("⚖️ Verifier agent: weighing cited evidence...", expanded=False)

        def on_stage(name):
            if name == "research":
                s_plan.update(label="🧭 Sub-questions ready", state="complete")
            elif name == "verify":
                s_research.update(label="🔎 Research complete", state="complete", expanded=False)

        def on_step(entry):
            arg = next(iter(entry["args"].values()), "") if entry["args"] else ""
            s_research.write(f"**Step {entry['step']}** · `{entry['action']}` {arg}")

        st.session_state.result = run_pipeline(st.session_state.claim, on_stage=on_stage, on_step=on_step)
        s_verify.update(label="⚖️ Verdict generated", state="complete")
        progress_container.empty()

    result = st.session_state.result
    verdict = result["verdict"]
    sources = result.get("sources", {})
    status = verdict.get("verdict", "ERROR")
    confidence = verdict.get("confidence", "")
    summary = verdict.get("summary", "")
    supporting = verdict.get("supporting_points", [])
    contradicting = verdict.get("contradicting_points", [])

    if status == "SUPPORTED":
        st.success(f"✅ SUPPORTED · {confidence} confidence")
    elif status == "REFUTED":
        st.error(f"❌ REFUTED · {confidence} confidence")
    elif status == "INSUFFICIENT EVIDENCE":
        st.warning(f"⚠️ INSUFFICIENT EVIDENCE · {confidence} confidence")
    else:
        st.error("Could not generate verdict.")

    st.info(summary)

    def render_point(p):
        links = " ".join(
            f"[{sid}]({sources[sid]['url']})" if sid in sources else sid for sid in p.get("sources", [])
        )
        st.markdown(f"- {p.get('point', '')} {links}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**✅ Supporting points**")
        for p in supporting:
            render_point(p)
    with c2:
        st.markdown("**❌ Contradicting points**")
        for p in contradicting:
            render_point(p)

    if verdict.get("citation_issues"):
        with st.expander("🛡️ Guardrail checks"):
            for issue in verdict["citation_issues"]:
                st.markdown(f"- {issue}")

    with st.expander("Sub-questions researched"):
        for i, q in enumerate(result["sub_questions"], 1):
            st.markdown(f"{i}. {q}")

    with st.expander("Agent trace (ReAct steps)"):
        for e in result.get("trace", []):
            st.markdown(f"**Step {e['step']} · {e['action']}** `{e['args']}`")
            if e.get("thought"):
                st.caption(f"Thought: {e['thought'][:300]}")
            if e.get("observation"):
                st.code(e["observation"][:400], language=None)

    with st.expander("Sources"):
        order = {"HIGH": 0, "MEDIUM": 1, "UNKNOWN": 2, "LOW": 3}
        for sid, s in sorted(sources.items(), key=lambda kv: order[kv[1]["credibility"]["tier"]]):
            cred = s["credibility"]
            st.markdown(f"{cred['color']} **{sid}** [{s['title'] or s['url']}]({s['url']}) — *{cred['label']}*")

    st.markdown("---")
    st.markdown("### 💬 Discuss this verdict")
    st.markdown("Ask follow-up questions, challenge the verdict, or dig deeper into the evidence.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if user_msg := st.chat_input("Ask something about this verdict..."):
        st.session_state.chat_history.append({"role": "user", "content": user_msg})

        with st.chat_message("user"):
            st.markdown(user_msg)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                from groq import Groq
                import os
                try:
                    import streamlit as st_inner
                    api_key = st_inner.secrets["GROQ_API_KEY"]
                except:
                    from dotenv import load_dotenv
                    load_dotenv()
                    api_key = os.getenv("GROQ_API_KEY")

                client = Groq(api_key=api_key)

                # Build context from the verdict
                verdict = st.session_state.result["verdict"]
                context = f"""
You are a fact-checking assistant. The user has just received this verdict 
on the claim: "{st.session_state.claim}"

Verdict: {verdict.get('verdict')}
Confidence: {verdict.get('confidence')}
Summary: {verdict.get('summary')}
Supporting points: {[p['point'] for p in verdict.get('supporting_points', [])]}
Contradicting points: {[p['point'] for p in verdict.get('contradicting_points', [])]}

The user wants to discuss, challenge, or explore this verdict further.
Be helpful, specific, and reference the evidence where possible.
If the user challenges the verdict, engage with their argument seriously.
Keep responses concise — 3-5 sentences max unless more detail is needed.
"""
                messages = [{"role": "system", "content": context}]
                for h in st.session_state.chat_history:
                    messages.append({"role": h["role"], "content": h["content"]})

                from src.llm import FAST_MODEL
                response = client.chat.completions.create(
                    model=FAST_MODEL,
                    messages=messages,
                    max_tokens=500
                )

                reply = response.choices[0].message.content
                st.markdown(reply)

        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    st.markdown("""
    <div class="cv-footer">
        <span class="cv-footer-l">Built with Groq · DuckDuckGo · ChromaDB · Streamlit</span>
        <span class="cv-footer-r">claim-verifier v0.2</span>
    </div>""", unsafe_allow_html=True)
