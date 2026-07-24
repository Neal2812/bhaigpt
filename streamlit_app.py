"""BhaiGPT — Streamlit chat UI, styled like X / Twitter.

Run locally:   streamlit run streamlit_app.py
Deploy free:   push to GitHub, then https://share.streamlit.io -> New app ->
               main file: streamlit_app.py -> set GROQ_API_KEY under Secrets.

Unofficial fan PARODY — not affiliated with Salman Khan.
"""
from __future__ import annotations

import os

import streamlit as st

# Bridge Streamlit secrets -> environment on every rerun, BEFORE importing the
# engine (which reads keys fresh from the environment).
for _key in ("GROQ_API_KEY", "GEMINI_API_KEY", "GROQ_MODEL", "GEMINI_MODEL"):
    try:
        val = st.secrets[_key]
    except Exception:  # noqa: BLE001
        val = None
    if val:
        os.environ[_key] = str(val)

from bot.chat import reply  # noqa: E402 - must follow the secrets bridge above

st.set_page_config(page_title="BhaiGPT", page_icon="🎬", layout="centered")

# --- X / Twitter styling ----------------------------------------------------
st.markdown(
    """
<style>
:root {
  --x-blue:#1d9bf0; --x-border:#2f3336; --x-dim:#71767b;
  --x-text:#e7e9ea; --x-card:#16181c;
}
/* Timeline-width column, no top gap */
.block-container, [data-testid="stMainBlockContainer"]{
  max-width:600px !important; padding-top:1rem !important;
}
#MainMenu, header, footer {visibility:hidden;}

/* Profile header */
.bhai-card{border:1px solid var(--x-border);border-radius:16px;
  background:var(--x-card);overflow:hidden;margin-bottom:14px;}
.bhai-banner{height:96px;background:linear-gradient(120deg,#1d9bf0 0%,#7856ff 100%);}
.bhai-body{padding:0 16px 16px;}
.bhai-avatar{width:74px;height:74px;border-radius:50%;background:#000;
  border:4px solid var(--x-card);margin-top:-38px;display:flex;
  align-items:center;justify-content:center;font-size:38px;}
.bhai-name{font-weight:800;font-size:20px;color:var(--x-text);
  display:flex;align-items:center;gap:5px;margin-top:8px;line-height:1.2;}
.bhai-badge{display:inline-flex;width:19px;height:19px;background:var(--x-blue);
  color:#fff;border-radius:50%;align-items:center;justify-content:center;
  font-size:12px;font-weight:900;}
.bhai-handle{color:var(--x-dim);font-size:15px;margin-top:1px;}
.bhai-bio{color:var(--x-text);font-size:15px;margin-top:10px;line-height:1.4;}
.bhai-meta{color:var(--x-dim);font-size:14px;margin-top:10px;
  display:flex;gap:18px;flex-wrap:wrap;}
.bhai-meta b{color:var(--x-text);}
.bhai-disc{color:var(--x-dim);font-size:12.5px;border:1px solid var(--x-border);
  border-radius:12px;padding:8px 12px;margin-bottom:6px;}

/* Tweet-style message rows */
[data-testid="stChatMessage"]{background:transparent !important;
  border-bottom:1px solid var(--x-border);border-radius:0;
  padding:12px 2px 10px;gap:11px;}
[data-testid="stChatMessage"] p{color:var(--x-text);font-size:15px;
  line-height:1.45;margin-bottom:0;}
[data-testid="stChatMessageAvatar"]{border-radius:50%;}
.tw-head{font-size:14.5px;margin-bottom:2px;line-height:1.2;}
.tw-name{font-weight:800;color:var(--x-text);}
.tw-tick{color:var(--x-blue);font-weight:900;}
.tw-handle{color:var(--x-dim);font-weight:400;}

/* Rounded 'post your reply' input */
[data-testid="stChatInput"]{border:1px solid var(--x-border) !important;
  border-radius:9999px !important;background:var(--x-card) !important;}
[data-testid="stChatInput"] textarea{color:var(--x-text) !important;}
</style>
""",
    unsafe_allow_html=True,
)

# --- Profile header ---------------------------------------------------------
st.markdown(
    """
<div class="bhai-card">
  <div class="bhai-banner"></div>
  <div class="bhai-body">
    <div class="bhai-avatar">🎬</div>
    <div class="bhai-name">BhaiGPT <span class="bhai-badge">✓</span></div>
    <div class="bhai-handle">@being_bhaigpt</div>
    <div class="bhai-bio">Mehnat karo, dil saaf rakho, love all n hate none.
      Talk to me like a dost. 💙 (parody bot)</div>
    <div class="bhai-meta"><span><b>∞</b> Fans</span>
      <span><b>1</b> Following (khud ko)</span>
      <span>📍 Galaxy Apartments, vibes</span></div>
  </div>
</div>
<div class="bhai-disc">⚠️ Unofficial parody / fan project. Not affiliated with,
  endorsed by, or speaking for Salman Khan. Replies are AI-generated and are not
  real statements.</div>
""",
    unsafe_allow_html=True,
)

# --- Key diagnostics (only when no usable key) ------------------------------
if not (os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")):
    try:
        _names = list(st.secrets.keys())
    except Exception:  # noqa: BLE001
        _names = []
    st.error(
        "No LLM key detected. Add a **Groq** key (console.groq.com, starts with "
        "`gsk_`) under **Manage app → Settings → Secrets** as "
        "`GROQ_API_KEY = \"gsk_...\"`.",
        icon="🔑",
    )
    with st.expander("🔍 Diagnostics — secrets the app can see"):
        st.write("**Names found:**", _names or "— none —")
        st.write("**Needs:** `GROQ_API_KEY` (note the Q) or `GEMINI_API_KEY`")

# --- Chat -------------------------------------------------------------------
BOT_AVATAR, USER_AVATAR = "🎬", "🧑"

if "messages" not in st.session_state:
    st.session_state.messages = []


def _head(name: str, handle: str, tick: bool = False) -> str:
    badge = ' <span class="tw-tick">✓</span>' if tick else ""
    return (f'<div class="tw-head"><span class="tw-name">{name}</span>{badge} '
            f'<span class="tw-handle">{handle} · now</span></div>')


for msg in st.session_state.messages:
    is_bot = msg["role"] == "assistant"
    with st.chat_message(msg["role"], avatar=BOT_AVATAR if is_bot else USER_AVATAR):
        st.markdown(
            _head("BhaiGPT", "@being_bhaigpt", tick=True) if is_bot
            else _head("You", "@you"),
            unsafe_allow_html=True,
        )
        st.markdown(msg["content"])

if prompt := st.chat_input("Post your reply to Bhai…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(_head("You", "@you"), unsafe_allow_html=True)
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        st.markdown(_head("BhaiGPT", "@being_bhaigpt", tick=True), unsafe_allow_html=True)
        with st.spinner("Bhai type kar raha hai…"):
            answer = reply(prompt, st.session_state.messages[:-1])
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
