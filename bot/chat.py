"""BhaiGPT chat engine: RAG prompt assembly + free-tier LLM call.

Primary backend is Groq (fast, free tier); falls back to Google Gemini (free
tier) if Groq has no key or errors. Both keys come from the environment. If no
key is configured at all, we return a clear message instead of failing silently.
"""
from __future__ import annotations

from bot import persona
from bot.retriever import TweetRetriever
import config

# Lazily-initialized singletons.
_retriever: TweetRetriever | None = None
_groq_client = None
_gemini_model = None


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


def _try_groq(messages: list[dict]) -> str | None:
    if not config.GROQ_API_KEY:
        return None
    global _groq_client
    try:
        if _groq_client is None:
            from groq import Groq
            _groq_client = Groq(api_key=config.GROQ_API_KEY)
        resp = _groq_client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            max_tokens=config.MAX_REPLY_TOKENS,
            temperature=0.9,
            top_p=0.95,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:  # noqa: BLE001 - fall back to Gemini
        print(f"[groq] error, falling back to Gemini: {exc}")
        return None


def _try_gemini(messages: list[dict]) -> str | None:
    if not config.GEMINI_API_KEY:
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
            genai.configure(api_key=config.GEMINI_API_KEY)
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
        print(f"[gemini] error: {exc}")
        return None


def _postprocess(text: str) -> str:
    text = text.strip().strip('"')
    # Keep it tweet-short: cap at ~4 lines.
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) > 4:
        text = "\n".join(lines[:4])
    return text.strip()


def reply(user_msg: str, history: list[dict] | None = None) -> str:
    """Generate one in-persona reply. Never raises to the UI."""
    if not user_msg or not user_msg.strip():
        return "Bol bhai, kya baat hai? 😎"

    if not config.GROQ_API_KEY and not config.GEMINI_API_KEY:
        return (
            "⚠️ Koi LLM key set nahi hai. Add GROQ_API_KEY or GEMINI_API_KEY to "
            "your .env (both have free tiers) and restart. — BhaiGPT"
        )

    messages = _build_messages(user_msg, history)

    out = _try_groq(messages) or _try_gemini(messages)
    if not out:
        return (
            "⚠️ Dono LLM backends abhi jawab nahi de paaye (key galat ya rate "
            "limit?). Thodi der baad try kar, bhai."
        )
    return _postprocess(out)


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
