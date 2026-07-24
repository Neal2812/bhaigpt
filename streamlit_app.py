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

/* Tweet action bar (cosmetic) */
.tw-actions{display:flex;justify-content:space-between;max-width:340px;
  margin-top:11px;color:var(--x-dim);}
.tw-act{display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer;
  transition:color .12s;}
.tw-act svg{width:18px;height:18px;stroke:currentColor;fill:none;
  stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round;}
.tw-reply:hover{color:var(--x-blue);}
.tw-rt:hover{color:#00ba7c;}
.tw-like{color:#f91880;}
.tw-like svg{fill:#f91880;stroke:#f91880;}
.tw-views:hover,.tw-share:hover{color:var(--x-blue);}
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


# --- Cosmetic tweet action bar (reply / repost / like / views / share) ------
_ICON = {
    "reply": '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 '
             '8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 '
             '8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8z"/>',
    "rt": '<polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/>'
          '<polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>',
    "like": '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 '
            '5.5 0 1 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z"/>',
    "views": '<line x1="4" y1="20" x2="4" y2="12"/><line x1="10" y1="20" x2="10" '
             'y2="4"/><line x1="16" y1="20" x2="16" y2="9"/><line x1="22" y1="20"'
             ' x2="22" y2="14"/>',
    "share": '<path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>'
             '<polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/>',
}


def _svg(name: str) -> str:
    return f'<svg viewBox="0 0 24 24">{_ICON[name]}</svg>'


def _count(seed: str, mod: int, base: int = 0) -> int:
    import hashlib
    return base + int(hashlib.md5(seed.encode()).hexdigest(), 16) % mod


def _fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n / 1_000:.1f}K".replace(".0K", "K")
    return str(n)


def _actions(text: str, bot: bool = True) -> str:
    s = text[:48]
    if bot:  # Bhai is a superstar — big numbers
        r, rt, lk, vw = (_count(s + "r", 900, 40), _count(s + "t", 6000, 300),
                         _count(s + "l", 90000, 3000), _count(s + "v", 2_000_000, 80000))
    else:
        r, rt, lk, vw = (_count(s + "r", 15), _count(s + "t", 8),
                         _count(s + "l", 70), _count(s + "v", 4000, 120))
    return (
        '<div class="tw-actions">'
        f'<span class="tw-act tw-reply">{_svg("reply")}{_fmt(r)}</span>'
        f'<span class="tw-act tw-rt">{_svg("rt")}{_fmt(rt)}</span>'
        f'<span class="tw-act tw-like">{_svg("like")}{_fmt(lk)}</span>'
        f'<span class="tw-act tw-views">{_svg("views")}{_fmt(vw)}</span>'
        f'<span class="tw-act tw-share">{_svg("share")}</span>'
        '</div>'
    )


for msg in st.session_state.messages:
    is_bot = msg["role"] == "assistant"
    with st.chat_message(msg["role"], avatar=BOT_AVATAR if is_bot else USER_AVATAR):
        st.markdown(
            _head("BhaiGPT", "@being_bhaigpt", tick=True) if is_bot
            else _head("You", "@you"),
            unsafe_allow_html=True,
        )
        st.markdown(msg["content"])
        st.markdown(_actions(msg["content"], bot=is_bot), unsafe_allow_html=True)

if prompt := st.chat_input("Post your reply to Bhai…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(_head("You", "@you"), unsafe_allow_html=True)
        st.markdown(prompt)
        st.markdown(_actions(prompt, bot=False), unsafe_allow_html=True)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        st.markdown(_head("BhaiGPT", "@being_bhaigpt", tick=True), unsafe_allow_html=True)
        with st.spinner("Bhai type kar raha hai…"):
            answer = reply(prompt, st.session_state.messages[:-1])
        st.markdown(answer)
        st.markdown(_actions(answer, bot=True), unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": answer})
