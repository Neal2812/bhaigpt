"""BhaiGPT chat engine: RAG prompt assembly + free-tier LLM call.

Primary backend is Groq (fast, free tier); falls back to Google Gemini (free
tier) if Groq has no key or errors. Both keys come from the environment. If no
key is configured at all, we return a clear message instead of failing silently.
"""
from __future__ import annotations

import os
import re

from bot import persona
from bot.retriever import TweetRetriever
import config

# Emoji / pictographic ranges + variation selectors and ZWJ. Bhai's tweets are
# text-only, and the user wants no emojis in replies.
_EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"  # regional indicators (flags)
    "\U0001F300-\U0001FAFF"  # symbols, pictographs, emoji
    "\U00002600-\U000027BF"  # misc symbols + dingbats
    "\U00002B00-\U00002BFF"  # misc symbols/arrows
    "\U0001F000-\U0001F0FF"  # mahjong/dominoes/cards
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U0000200D"              # zero-width joiner
    "\U00002700-\U000027BF"
    "]",
    flags=re.UNICODE,
)

# Lazily-initialized singletons.
_retriever: TweetRetriever | None = None
_groq_client = None
_groq_model_ok: str | None = None   # first Groq model that worked this session
_gemini_model = None
_last_error: str = ""               # short reason the last LLM attempt failed


def _short(exc: object, limit: int = 200) -> str:
    return " ".join(str(exc).split())[:limit]


def _model_related(exc: object) -> bool:
    """Heuristic: does this error look like a bad/retired model (vs. auth)?"""
    msg = str(exc).lower()
    return any(k in msg for k in
               ("model", "not found", "does not exist", "decommission", "deprecat"))


# Read keys FRESH from the environment on every call, not once at import. On
# hosts like Streamlit Cloud the process can start before secrets are injected;
# a cached import-time snapshot would stay empty until a full reboot.
def _groq_key() -> str:
    return (os.getenv("GROQ_API_KEY") or config.GROQ_API_KEY or "").strip()


def _gemini_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or config.GEMINI_API_KEY or "").strip()


def _get_retriever() -> TweetRetriever:
    global _retriever
    if _retriever is None:
        _retriever = TweetRetriever()
    return _retriever


def _build_messages(user_msg: str, history: list[dict] | None) -> list[dict]:
    r = _get_retriever()
    anchors = r.anchors(user_msg)

    messages: list[dict] = [
        {"role": "system", "content": persona.SYSTEM_PROMPT},
    ]
    # Only add the tweet-reference block if we actually have tweets; otherwise
    # the persona prompt alone carries the style (persona-only mode).
    if r.fewshot or anchors:
        messages.append(
            {"role": "system", "content": persona.build_style_block(r.fewshot, anchors)}
        )
    for turn in (history or [])[-6:]:  # keep context small & tweet-like
        role = turn.get("role")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_msg})
    return messages


def _groq_discover_models() -> list[str]:
    """Ask Groq which chat models this key can use, ordered by preference."""
    try:
        data = _groq_client.models.list().data
    except Exception as exc:  # noqa: BLE001
        print(f"[groq] models.list() failed: {exc}")
        return []
    ids = [getattr(m, "id", "") for m in data]
    usable = [m for m in ids
              if m and not any(s in m.lower() for s in config.GROQ_MODEL_SKIP)]

    def rank(model: str) -> int:
        low = model.lower()
        for i, pref in enumerate(config.GROQ_MODEL_PREFER):
            if pref in low:
                return i
        return len(config.GROQ_MODEL_PREFER)

    return sorted(usable, key=rank)


def _try_groq(messages: list[dict]) -> str | None:
    key = _groq_key()
    if not key:
        return None
    global _groq_client, _groq_model_ok, _last_error
    try:
        if _groq_client is None:
            from groq import Groq
            _groq_client = Groq(api_key=key)
    except Exception as exc:  # noqa: BLE001 - lib/init problem
        _last_error = f"groq: {_short(exc)}"
        print(f"[groq] init error: {exc}")
        return None

    def _call(model: str) -> str:
        resp = _groq_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=config.MAX_REPLY_TOKENS,
            temperature=0.9,
            top_p=0.95,
        )
        return (resp.choices[0].message.content or "").strip()

    # Known-good model first, then configured + hardcoded fallbacks.
    candidates: list[str] = []
    for m in [_groq_model_ok, config.GROQ_MODEL, *config.GROQ_MODEL_FALLBACKS]:
        if m and m not in candidates:
            candidates.append(m)

    last_exc: Exception | None = None
    for model in candidates:
        try:
            out = _call(model)
            _groq_model_ok = model  # remember what worked
            return out
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            print(f"[groq] model '{model}' failed: {exc}")
            # Auth / rate-limit errors won't be fixed by another model — stop.
            if not _model_related(exc):
                _last_error = f"groq: {_short(exc)}"
                return None

    # Every hardcoded guess was rejected as a bad model — ask the API what's
    # actually available on this key and try those. Removes reliance on IDs
    # I guessed; survives Groq renaming models.
    for model in _groq_discover_models():
        if model in candidates:
            continue
        try:
            out = _call(model)
            _groq_model_ok = model
            print(f"[groq] auto-selected available model: {model}")
            return out
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if not _model_related(exc):
                _last_error = f"groq: {_short(exc)}"
                return None

    if last_exc is not None:
        _last_error = f"groq: {_short(last_exc)}"
    return None


def _try_gemini(messages: list[dict]) -> str | None:
    key = _gemini_key()
    if not key:
        return None
    global _gemini_model
    try:
        import google.generativeai as genai

        # Gemini has no dedicated system role — fold system messages into the
        # model's system_instruction and pass the conversation as contents.
        system = "\n\n".join(
            m["content"] for m in messages if m["role"] == "system"
        )
        if _gemini_model is None:
            genai.configure(api_key=key)
            _gemini_model = genai.GenerativeModel(
                config.GEMINI_MODEL, system_instruction=system
            )
        contents = [
            {"role": "user" if m["role"] == "user" else "model",
             "parts": [m["content"]]}
            for m in messages if m["role"] in ("user", "assistant")
        ]
        resp = _gemini_model.generate_content(
            contents,
            generation_config={
                "max_output_tokens": config.MAX_REPLY_TOKENS,
                "temperature": 0.9,
                "top_p": 0.95,
            },
        )
        return (resp.text or "").strip()
    except Exception as exc:  # noqa: BLE001
        global _last_error
        _last_error = f"gemini: {_short(exc)}"
        print(f"[gemini] error: {exc}")
        return None


def _postprocess(text: str) -> str:
    text = text.strip()
    # Strip reasoning-model output: complete <think>...</think> blocks, and any
    # trailing unclosed <think> (truncated reasoning that never reached an answer).
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = text.strip().strip('"')
    text = _EMOJI_RE.sub("", text)              # user wants no emojis
    text = re.sub(r"\s+([,.!?…])", r"\1", text)  # no space before punctuation
    text = re.sub(r"[ \t]{2,}", " ", text)       # tidy gaps left by removed emojis
    # Keep it tweet-short: cap at ~4 lines.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) > 4:
        lines = lines[:4]
    return "\n".join(lines).strip()


def reply(user_msg: str, history: list[dict] | None = None) -> str:
    """Generate one in-persona reply. Never raises to the UI."""
    if not user_msg or not user_msg.strip():
        return "Bol bhai, kya baat hai? 😎"

    if not _groq_key() and not _gemini_key():
        return (
            "⚠️ Koi LLM key set nahi hai. Set GROQ_API_KEY (or GEMINI_API_KEY) — "
            "in Streamlit: Manage app → Settings → Secrets, then Reboot; locally: "
            "in your .env. Both have free tiers. — BhaiGPT"
        )

    global _last_error
    _last_error = ""
    messages = _build_messages(user_msg, history)

    out = _try_groq(messages) or _try_gemini(messages)
    if not out:
        detail = f"\n\n_debug: {_last_error}_" if _last_error else ""
        return (
            "⚠️ Bhai abhi jawab nahi de paaya (key galat, model retire, ya rate "
            "limit?). Thodi der baad try kar." + detail
        )
    final = _postprocess(out)
    return final or "Haan bhai bol, kya chah raha hai?"


if __name__ == "__main__":
    # Quick terminal smoke test.
    print("BhaiGPT (Ctrl-C to exit)")
    hist: list[dict] = []
    try:
        while True:
            msg = input("you: ").strip()
            if not msg:
                continue
            ans = reply(msg, hist)
            print(f"bhai: {ans}\n")
            hist.append({"role": "user", "content": msg})
            hist.append({"role": "assistant", "content": ans})
    except (KeyboardInterrupt, EOFError):
        print("\nChalo, milte hain! 👋")
