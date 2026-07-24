"""BhaiGPT — Streamlit chat UI (for free deploy on Streamlit Community Cloud).

Run locally:   streamlit run streamlit_app.py
Deploy free:   push this repo to GitHub, then https://share.streamlit.io ->
               "New app" -> pick this repo -> main file: streamlit_app.py ->
               set GROQ_API_KEY (or GEMINI_API_KEY) under "Secrets".

Unofficial fan PARODY — not affiliated with Salman Khan.
"""
from __future__ import annotations

import os

import streamlit as st

# Bridge Streamlit secrets -> environment on every rerun, BEFORE importing the
# engine. The engine reads keys fresh from the environment, so a secret added
# after first launch propagates on the next rerun (no reboot strictly needed).
for _key in ("GROQ_API_KEY", "GEMINI_API_KEY", "GROQ_MODEL", "GEMINI_MODEL"):
    try:
        val = st.secrets[_key]  # may raise if no secrets file at all
    except Exception:  # noqa: BLE001
        val = None
    if val:
        os.environ[_key] = str(val)

from bot.chat import reply  # noqa: E402 - must follow the secrets bridge above

st.set_page_config(page_title="BhaiGPT", page_icon="🎬")

st.title("🎬 BhaiGPT")
st.caption("Chat in the style of Bhai's tweets — short, warm, Hinglish.")
st.warning(
    "**Unofficial parody / fan project.** Not affiliated with, endorsed by, or "
    "speaking for Salman Khan. Replies are AI-generated in a playful style and "
    "are not real statements.",
    icon="⚠️",
)

# --- Key diagnostics (shown only when no usable key is detected) -------------
# Reveals *names* of configured secrets (never values) so a misnamed secret —
# e.g. GROK_API_KEY instead of GROQ_API_KEY — is easy to spot.
_key_detected = bool(os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY"))
if not _key_detected:
    try:
        _secret_names = list(st.secrets.keys())
    except Exception:  # noqa: BLE001
        _secret_names = []
    st.error(
        "No LLM key detected. Set a **Groq** key (from console.groq.com, starts "
        "with `gsk_`) under **Manage app → Settings → Secrets**, exactly as:\n\n"
        "```toml\nGROQ_API_KEY = \"gsk_your_key\"\n```",
        icon="🔑",
    )
    with st.expander("🔍 Diagnostics — which secrets does the app see?"):
        st.write("**Secret names found:**", _secret_names or "— none —")
        st.write("**Names it needs:** `GROQ_API_KEY` (note the Q) or `GEMINI_API_KEY`")
        if any(n.upper() in ("GROK_API_KEY", "GROK", "XAI_API_KEY") for n in _secret_names):
            st.write("⚠️ Found a **GROK** secret — that's xAI's Grok, a different "
                     "service. Rename it to **GROQ_API_KEY** and use a key from "
                     "console.groq.com.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Bol bhai, kya haal hai?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Bhai soch raha hai..."):
            # Pass prior turns (everything before this new user message) as history.
            answer = reply(prompt, st.session_state.messages[:-1])
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
