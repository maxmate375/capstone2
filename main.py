import os
from uuid import uuid4

import requests
import streamlit as st
import truststore

truststore.inject_into_ssl()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="Yojana Saathi | Government Schemes",
    page_icon="🇮🇳",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Manrope:wght@600;700;800&display=swap');

    /* ── Base reset ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: #f0f4f8;
    }

    /* ── Main content width ── */
    [data-testid="stMainBlockContainer"] {
        max-width: 960px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] h2 {
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
        color: #1a3c2e;
        font-size: 1.2rem;
        margin-bottom: 0.25rem;
    }

    /* ── Hero banner ── */
    .hero {
        border-radius: 20px;
        padding: 2.5rem 2.5rem 2.2rem 2.5rem;
        margin-bottom: 1.2rem;
        background: linear-gradient(135deg, #0d3b2e 0%, #1a6b50 55%, #2a9272 100%);
        box-shadow: 0 8px 32px rgba(13, 59, 46, 0.25);
        overflow: hidden;
        position: relative;
    }
    .hero::after {
        content: "भारत";
        position: absolute;
        right: 2rem;
        top: 1rem;
        font-family: 'Manrope', sans-serif;
        font-size: 5rem;
        font-weight: 800;
        color: rgba(255,255,255,0.07);
        letter-spacing: -0.05em;
        pointer-events: none;
    }
    .hero-eyebrow {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #a7f3d0;
        margin-bottom: 0.6rem;
    }
    .hero h1 {
        font-family: 'Manrope', sans-serif;
        font-size: clamp(1.8rem, 3.5vw, 2.6rem);
        font-weight: 800;
        line-height: 1.15;
        color: #ffffff;
        margin: 0 0 0.85rem 0;
        letter-spacing: -0.03em;
    }
    .hero p {
        font-size: 0.97rem;
        line-height: 1.7;
        color: #d1fae5;
        max-width: 620px;
        margin: 0 0 1.2rem 0;
    }
    .trust-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .trust-pill {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.22);
        border-radius: 999px;
        padding: 0.38rem 0.85rem;
        font-size: 0.78rem;
        font-weight: 600;
        color: #ecfdf5;
    }

    /* ── Disclaimer ── */
    .disclaimer {
        border-left: 4px solid #f59e0b;
        background: #fffbeb;
        border-radius: 8px;
        padding: 0.85rem 1.1rem;
        color: #78350f;
        font-size: 0.85rem;
        line-height: 1.55;
        margin-bottom: 1.4rem;
    }

    /* ── Section headings ── */
    .section-title {
        font-family: 'Manrope', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: #1a3c2e;
        margin: 0 0 0.2rem 0;
    }
    .section-sub {
        font-size: 0.88rem;
        color: #64748b;
        margin-bottom: 1rem;
    }

    /* ── Chat messages ── */
    [data-testid="stChatMessage"] {
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        background: #ffffff;
        margin-bottom: 0.6rem;
    }

    /* ── Suggestion / action buttons ── */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 0.55rem 0.9rem;
        border: 1.5px solid #d1fae5;
        background: #ffffff;
        color: #1a6b50;
        transition: all 0.18s ease;
        white-space: normal;
        text-align: left;
        line-height: 1.35;
        height: auto;
    }
    .stButton > button:hover {
        border-color: #1a6b50;
        background: #f0fdf4;
        color: #0d3b2e;
        box-shadow: 0 2px 8px rgba(26, 107, 80, 0.12);
    }
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button {
        background: #1a6b50 !important;
        border-color: #1a6b50 !important;
        color: #ffffff !important;
        font-weight: 700;
    }
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button:hover {
        background: #0d3b2e !important;
        border-color: #0d3b2e !important;
        box-shadow: 0 4px 12px rgba(13, 59, 46, 0.25) !important;
    }

    /* ── Chat input ── */
    [data-testid="stChatInput"] textarea {
        border-radius: 12px;
        border: 1.5px solid #d1d5db;
        background: #ffffff;
        font-size: 0.95rem;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #1a6b50;
        box-shadow: 0 0 0 3px rgba(26, 107, 80, 0.12);
    }

    /* ── Scheme match card ── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        background: #fff;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        background: #ffffff;
    }

    /* ── Form inputs ── */
    [data-testid="stSelectbox"] > div,
    [data-testid="stNumberInput"] > div {
        border-radius: 8px;
    }

    /* ── Spinner text ── */
    [data-testid="stSpinner"] p {
        color: #1a6b50;
        font-weight: 500;
    }

    /* ── Toast ── */
    [data-testid="stToast"] {
        background: #1a6b50;
        color: #fff;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state ──────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
      <div class="hero-eyebrow">🇮🇳 INDIA · CENTRAL GOVERNMENT SCHEMES</div>
      <h1>Find the support<br>you may be eligible for.</h1>
      <p>Ask in everyday language. Get scheme information grounded in MyScheme records, with clear eligibility details and official links.</p>
      <div class="trust-row">
        <span class="trust-pill">📚 526 central scheme records</span>
        <span class="trust-pill">🔗 Source-linked answers</span>
        <span class="trust-pill">🔒 Profile stays in your session</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="disclaimer">⚠️ Eligibility suggestions are <strong>preliminary</strong>, not an official decision. Scheme rules can change — confirm current requirements on the linked MyScheme or ministry page.</div>',
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Your profile")
    st.caption(
        "Optional details help compare your situation with scheme criteria. "
        "Leave unknown fields blank. Details stay in this browser session and are not saved to feedback."
    )
    with st.form("profile_form"):
        age_value = st.number_input("Age", min_value=0, max_value=120, value=0,
                                    help="Leave 0 if you prefer not to share.")
        gender_value = st.selectbox("Gender", ["Not specified", "Woman", "Man", "Other"])
        state_value = st.selectbox(
            "State / Union Territory",
            [
                "Not specified", "Andhra Pradesh", "Arunachal Pradesh", "Assam",
                "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana",
                "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
                "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
                "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
                "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
                "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands",
                "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
                "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
            ],
        )
        income_value = st.number_input(
            "Annual household income (₹)",
            min_value=0, max_value=10_000_000_000, value=0, step=10_000,
            help="Leave 0 if unknown or you prefer not to share.",
        )
        occupation_value = st.text_input("Occupation (optional)", max_chars=120)
        category_value = st.selectbox(
            "Social category",
            ["Not specified", "General", "SC", "ST", "OBC", "Other"],
        )
        farmer_value   = st.checkbox("I am a farmer")
        student_value  = st.checkbox("I am a student")
        disability_value = st.checkbox("I have a disability")
        bpl_value      = st.checkbox("My household has a BPL card")
        submitted = st.form_submit_button("Use this profile", type="primary", use_container_width=True)

    if submitted:
        profile = {
            "age": age_value or None,
            "gender": None if gender_value == "Not specified" else gender_value,
            "state": None if state_value == "Not specified" else state_value,
            "annual_household_income": income_value or None,
            "occupation": occupation_value.strip() or None,
            "social_category": None if category_value == "Not specified" else category_value,
            "is_farmer": farmer_value,
            "is_student": student_value,
            "disability_status": disability_value,
            "bpl_household": bpl_value,
        }
        st.session_state.user_profile = {k: v for k, v in profile.items() if v is not None}
        st.toast("✅ Profile saved for this chat.")

    if st.session_state.user_profile:
        st.success("Profile details ready")
        if st.button("Clear profile", use_container_width=True):
            st.session_state.user_profile = {}
            st.rerun()

    st.divider()
    if st.button("＋  New conversation", use_container_width=True):
        st.session_state.session_id = str(uuid4())
        st.session_state.messages = []
        st.rerun()
    st.caption("💡 Try asking about eligibility, benefits, required documents, or how to apply.")

# ── Scheme assistant ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Scheme assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Ask a question or choose a suggested starting point.</div>',
    unsafe_allow_html=True,
)

suggestions = [
    "I am a farmer. What central schemes could support me?",
    "What are the eligibility rules for PM-KISAN?",
    "Find scholarships for students from low-income families",
]
cols = st.columns(len(suggestions))
for col, suggestion in zip(cols, suggestions):
    if col.button(suggestion, use_container_width=True, help="Ask this question"):
        st.session_state.pending_prompt = suggestion


def render_result(result: dict, index: int, query_text: str) -> None:
    matches = result.get("eligibility_matches", [])
    if matches:
        st.markdown("**Possible scheme matches**")
        for match in matches:
            badge = {
                "potential_match":        "🟢 Potential match",
                "needs_more_information": "🟡 More info needed",
                "may_not_match":          "⚪ May not match",
            }.get(match["status"], "Scheme assessment")
            with st.container(border=True):
                st.markdown(f"**{match['scheme_name']}** · {badge}")
                st.write(match["rationale"])
                if match.get("criteria_matched"):
                    st.caption("✅ Profile details that match: " + "; ".join(match["criteria_matched"]))
                if match.get("missing_information"):
                    st.caption("❓ Still needed: " + "; ".join(match["missing_information"]))

    sources = result.get("sources", [])
    if sources:
        with st.expander(f"📎 Official scheme sources · {len(sources)} records"):
            for source in sources:
                st.markdown(f"**[{source['title']}]({source['url']})**")
                if source.get("ministry"):
                    st.caption(source["ministry"])
                if source.get("official_url") and source["official_url"] != source["url"]:
                    st.markdown(f"[Official application / ministry page]({source['official_url']})")

    with st.expander("🔍 How this answer was produced"):
        st.caption(
            "Agent trace: " + " → ".join(result.get("agents_invoked", []))
            + f"  |  Grounding confidence: {result.get('confidence', 0):.0%}"
        )
        st.caption(
            "Knowledge source: a public MyScheme dataset snapshot; use the links above "
            "to verify the latest official rules."
        )
        for context in result.get("retrieved_context", []):
            st.write(context)

    with st.form(f"feedback_form_{index}"):
        rating = st.radio(
            "Was this answer helpful?",
            ["👍 Helpful", "👎 Not helpful"],
            index=None,
            horizontal=True,
            label_visibility="collapsed",
            key=f"feedback-{index}",
        )
        correction = st.text_input(
            "What could be improved? (optional)",
            key=f"correction-{index}",
            max_chars=1000,
        )
        submitted = st.form_submit_button("Send feedback")
    if submitted:
        if rating is None:
            st.info("Choose a thumbs-up or thumbs-down rating first.")
        else:
            try:
                requests.post(
                    f"{API_BASE_URL}/feedback",
                    json={
                        "session_id": st.session_state.session_id,
                        "query": query_text,
                        "rating": 1 if rating == "👍 Helpful" else -1,
                        "correction": correction.strip() or None,
                    },
                    timeout=15,
                ).raise_for_status()
                st.success("Thanks — your feedback was recorded.")
            except requests.RequestException as error:
                st.error(f"Could not save feedback: {error}")


# ── Chat history ───────────────────────────────────────────────────────────────
for message_index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("result"):
            render_result(message["result"], message_index, message["query"])

# ── Chat input ─────────────────────────────────────────────────────────────────
prompt = st.chat_input("Ask about eligibility, scheme benefits or applications")
if not prompt:
    prompt = st.session_state.pop("pending_prompt", None)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching scheme records and verifying sources..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/query",
                    json={
                        "query": prompt,
                        "session_id": st.session_state.session_id,
                        "profile": st.session_state.user_profile or None,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()
            except requests.RequestException as error:
                detail = error.response.text if error.response is not None else str(error)
                st.error(f"The scheme assistant could not answer: {detail}")
                st.stop()

        st.markdown(result["answer"])
        render_result(result, len(st.session_state.messages), prompt)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "result": result,
            "query": prompt,
        }
    )
