"""BhaiGPT — Gradio chat UI.

Run locally:   python app.py
Deploy free:   push this repo to a Hugging Face Space (SDK: gradio) and set
               GROQ_API_KEY (or GEMINI_API_KEY) as a Space secret.

This is an unofficial fan PARODY — not affiliated with Salman Khan.
"""
from __future__ import annotations

import gradio as gr

from bot.chat import reply

DISCLAIMER = (
    "⚠️ **Unofficial parody / fan project.** BhaiGPT is not affiliated with, "
    "endorsed by, or speaking for Salman Khan. Replies are AI-generated in a "
    "playful style and are not real statements."
)


def respond(message: str, history: list[dict]) -> str:
    # Gradio 'messages' format gives history as a list of {role, content} dicts.
    return reply(message, history)


demo = gr.ChatInterface(
    fn=respond,
    type="messages",
    title="🎬 BhaiGPT",
    description=(
        "Chat in the style of Bhai's tweets — short, warm, Hinglish. "
        + DISCLAIMER
    ),
    examples=[
        "Bhai, exam ka tension ho raha hai",
        "Success ka secret kya hai?",
        "Aaj mann udaas hai",
        "Gym jaana chahiye ya nahi?",
    ],
)


if __name__ == "__main__":
    demo.launch()
