"""Central configuration for BhaiGPT.

All tunables live here so scripts stay thin. Paths are resolved relative to the
repo root, and secrets are pulled from the environment (.env), never hardcoded.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

RAW_TWEETS = DATA_DIR / "raw_tweets.jsonl"
CLEAN_TWEETS = DATA_DIR / "clean_tweets.jsonl"
FILTER_REPORT = DATA_DIR / "filter_report.json"
EMBEDDINGS = DATA_DIR / "tweet_embeddings.npy"
EMBED_TEXTS = DATA_DIR / "tweet_texts.json"
TWSCRAPE_DB = DATA_DIR / "twscrape_accounts.db"

# --- Scrape target ----------------------------------------------------------
TARGET_HANDLE = "BeingSalmanKhan"
MAX_TWEETS = int(os.getenv("MAX_TWEETS", "3000"))

# --- Filtering thresholds ---------------------------------------------------
MIN_TWEET_CHARS = 15          # drop one-word / near-empty tweets
MAX_URL_RATIO = 0.35          # drop tweets that are mostly links
MAX_HASHTAG_RATIO = 0.40      # drop tweets that are mostly hashtags

# --- Embeddings / retrieval -------------------------------------------------
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # local, free
TOP_K = 6                     # style anchors retrieved per query
FEWSHOT_N = 8                 # curated example tweets in the persona prompt

# --- LLM --------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
# Groq retires models periodically (e.g. llama-3.3-70b-versatile was
# decommissioned 2026-06-17). We try the configured model first, then these
# fallbacks in order, so a single deprecation can't take the app down.
# Default to gpt-oss (clean, non-reasoning, casual enough with our style rules).
# Auto-discovery (bot/chat.py) covers any ID that's wrong or retired, so this
# list just sets preference/order.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_MODEL_FALLBACKS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "gemma2-9b-it",
    "llama-3.3-70b-versatile",  # legacy; kept last in case it lingers
]
# When auto-discovering, prefer these substrings (in order). Skip non-chat
# models AND reasoning models that emit verbose <think> output (e.g. qwen3,
# qwq, deepseek-r1) — unsuitable for short tweet replies and they burn the
# token budget on reasoning.
GROQ_MODEL_PREFER = ("gpt-oss", "gemma", "llama")
GROQ_MODEL_SKIP = ("whisper", "tts", "guard", "embed", "moderation", "vision",
                   "qwen3", "qwq", "deepseek", "-r1", "reasoning", "think")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MAX_REPLY_TOKENS = 160        # keep replies short & tweet-like

# --- X credentials (scraping only) ------------------------------------------
X_USERNAME = os.getenv("X_USERNAME", "").strip()
X_PASSWORD = os.getenv("X_PASSWORD", "").strip()
X_EMAIL = os.getenv("X_EMAIL", "").strip()
X_EMAIL_PASSWORD = os.getenv("X_EMAIL_PASSWORD", "").strip()
X_COOKIES = os.getenv("X_COOKIES", "").strip()
