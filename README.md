# 🎬 BhaiGPT

A **$0, no-paid-API** chatbot that talks in the style of Salman Khan ("Bhai")
by learning from [@BeingSalmanKhan](https://twitter.com/BeingSalmanKhan)'s
tweets — short, warm, blunt-but-positive Hinglish one-liners.

> ⚠️ **Unofficial parody / fan project.** BhaiGPT is **not** affiliated with,
> endorsed by, or speaking for Salman Khan. All replies are AI-generated in a
> playful style and are **not** real statements by any person.

## How it works

```
scrape tweets ─▶ filter out ads/promo ─▶ embed his voice (local) ─▶ RAG + free LLM ─▶ web chat
  twscrape         filter_tweets.py        sentence-transformers      Groq/Gemini       Streamlit
```

- **Scraping** — [`twscrape`](https://github.com/vladkens/twscrape) with a
  throwaway X account (X killed its free API, so this is the reliable free path).
- **Filtering** — heuristic removal of retweets, replies, and ad/promo tweets
  (Being Human, ticket bookings, sponsorships, contests, campaign hashtags…) so
  the bot sounds like *him*, not a billboard. Produces an auditable report.
- **Brain** — local [`sentence-transformers`](https://www.sbert.net/) embeddings
  (free, no key) retrieve his real tweets; a **free-tier LLM** (Groq, with Gemini
  fallback) generates the reply grounded in that style.
- **UI** — [Streamlit](https://streamlit.io/) chat (`streamlit_app.py`), free to
  host on Streamlit Community Cloud. A [Gradio](https://www.gradio.app/) UI
  (`app.py`) is also included for local use.

### Three modes, picked automatically by what data is present

| Data present | Mode | Needs torch? | Where it's used |
|---|---|---|---|
| Embeddings index | **Full RAG** — query-relevant real tweets | yes | local (full pipeline) |
| `tweet_texts.json` only | **Few-shot** — random real tweets as style anchors | no | hosted with data |
| None | **Persona-only** — the style prompt alone | no | deploy-before-you-scrape |

This means **you can deploy a working link before scraping anything** — it runs
in persona-only mode and gets richer as you add data.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements-local.txt               # full pipeline (scrape + embed + UIs)
cp .env.example .env                                # then edit .env
```

> `requirements.txt` is the **lean, torch-free set the hosted app uses**.
> `requirements-local.txt` adds scraping, embeddings, and Gradio for local work.

Fill in `.env`:

- **A burner X account** (`X_USERNAME` / `X_PASSWORD` / `X_EMAIL` /
  `X_EMAIL_PASSWORD`, or paste `X_COOKIES`) — for scraping only. Use a throwaway,
  not your real account.
- **At least one free LLM key** — get a **Groq** key at
  <https://console.groq.com/keys> or a **Gemini** key at
  <https://aistudio.google.com/app/apikey>. Both have free tiers; no card needed.

## Run the pipeline (in order)

```bash
python -m scrape.setup_account     # 1. register the burner account (once)
python -m scrape.scrape_tweets     # 2. -> data/raw_tweets.jsonl   (resumable)
python -m process.filter_tweets    # 3. -> data/clean_tweets.jsonl + filter_report.json
python -m process.build_index      # 4. -> local embedding index
streamlit run streamlit_app.py     # 5. launch the BhaiGPT web chat (or: python app.py for Gradio)
```

Inspect `data/filter_report.json` after step 3 to see what got dropped and why —
tune the keyword lists / thresholds in `process/filter_tweets.py` and `config.py`
if needed. For a quick terminal test without the UI: `python -m bot.chat`.

## Deploy free — Streamlit Community Cloud

> ⚠️ **Not Hugging Face Spaces.** As of 2026, HF requires a paid **PRO** plan to
> create Gradio/Docker Spaces; only Static Spaces are free. Streamlit Community
> Cloud is a genuinely free, permanent, public host.

1. Push this repo to **GitHub** (public repo).
2. **(Optional but recommended)** commit your tweet text list so the hosted bot
   stays grounded in real tweets — it's the one data file allowed past
   `.gitignore`:
   ```bash
   git add -f data/tweet_texts.json && git commit -m "Add tweet corpus for hosting"
   ```
   Skip this and the app still runs in **persona-only** mode. Do **not** commit
   the raw dump, the embeddings (`.npy`), or your `.env`.
3. Go to <https://share.streamlit.io> → **New app** → pick your repo →
   **Main file path:** `streamlit_app.py`.
4. Under **Advanced settings → Secrets**, add your key in TOML form:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
   *(or `GEMINI_API_KEY = "..."`)*
5. **Deploy.** You get a permanent public link like
   `https://<your-app>.streamlit.app` to share.

> Do the scraping **locally**, never on the host — keep X credentials off any
> deployed environment.

## Project layout

| Path | Purpose |
|------|---------|
| `config.py` | Paths, model names, target handle, thresholds |
| `scrape/setup_account.py` | Register burner X account into twscrape |
| `scrape/scrape_tweets.py` | Pull tweets → `data/raw_tweets.jsonl` |
| `process/filter_tweets.py` | Remove ads/promo → `clean_tweets.jsonl` + report |
| `process/build_index.py` | Embed clean tweets → local vector index |
| `bot/persona.py` | Persona system prompt + style-block builder |
| `bot/retriever.py` | Retrieval + few-shot; degrades gracefully by data present |
| `bot/chat.py` | RAG prompt + Groq/Gemini call |
| `streamlit_app.py` | Streamlit chat UI (free-hostable on Streamlit Cloud) |
| `app.py` | Gradio chat UI (local alternative) |
| `requirements.txt` / `requirements-local.txt` | Lean hosted deps / full local deps |

## Notes on responsible use

- Scraping public tweets may conflict with X's Terms of Service — keep volume
  low and use this for **personal/educational** purposes.
- Secrets (`.env`), the raw tweet dump, and the embeddings are gitignored. The
  only data file you may optionally commit is `data/tweet_texts.json` (public
  tweet text), so the hosted app stays grounded — your call.
- The persona is a light caricature with guardrails: it won't push products or
  fabricate real quotes/news attributed to a real person.
