# 🎬 BhaiGPT

A **$0, no-paid-API** chatbot that talks in the style of Salman Khan ("Bhai")
by learning from [@BeingSalmanKhan](https://twitter.com/BeingSalmanKhan)'s
tweets — short, warm, blunt-but-positive Hinglish one-liners.

> ⚠️ **Unofficial parody / fan project.** BhaiGPT is **not** affiliated with,
> endorsed by, or speaking for Salman Khan. All replies are AI-generated in a
> playful style and are **not** real statements by any person.

## How it works

```
scrape tweets ─▶ filter out ads/promo ─▶ embed his voice (local) ─▶ RAG + free LLM ─▶ Gradio chat
  twscrape         filter_tweets.py        sentence-transformers      Groq/Gemini       app.py
```

- **Scraping** — [`twscrape`](https://github.com/vladkens/twscrape) with a
  throwaway X account (X killed its free API, so this is the reliable free path).
- **Filtering** — heuristic removal of retweets, replies, and ad/promo tweets
  (Being Human, ticket bookings, sponsorships, contests, campaign hashtags…) so
  the bot sounds like *him*, not a billboard. Produces an auditable report.
- **Brain** — local [`sentence-transformers`](https://www.sbert.net/) embeddings
  (free, no key) retrieve his real tweets; a **free-tier LLM** (Groq, with Gemini
  fallback) generates the reply grounded in that style.
- **UI** — [Gradio](https://www.gradio.app/) chat, free to host on Hugging Face
  Spaces.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
cp .env.example .env                                # then edit .env
```

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
python app.py                      # 5. launch the BhaiGPT web chat
```

Inspect `data/filter_report.json` after step 3 to see what got dropped and why —
tune the keyword lists / thresholds in `process/filter_tweets.py` and `config.py`
if needed. For a quick terminal test without the UI: `python -m bot.chat`.

## Deploy free on Hugging Face Spaces

1. Create a new **Space** → SDK: **Gradio**.
2. Push this repo to it (or upload the files). `app.py` is the entrypoint.
3. In **Settings → Secrets**, add `GROQ_API_KEY` (and/or `GEMINI_API_KEY`).
4. Commit the generated embedding index (`data/tweet_embeddings.npy` and
   `data/tweet_texts.json`) **only if** you're comfortable including that derived
   data — by default `data/` is gitignored. The Space needs the index to run, so
   either commit those two files or rebuild them in the Space.

> Do the scraping **locally**, not on the Space — never put X credentials in a
> hosted environment.

## Project layout

| Path | Purpose |
|------|---------|
| `config.py` | Paths, model names, target handle, thresholds |
| `scrape/setup_account.py` | Register burner X account into twscrape |
| `scrape/scrape_tweets.py` | Pull tweets → `data/raw_tweets.jsonl` |
| `process/filter_tweets.py` | Remove ads/promo → `clean_tweets.jsonl` + report |
| `process/build_index.py` | Embed clean tweets → local vector index |
| `bot/persona.py` | Persona system prompt + style-block builder |
| `bot/retriever.py` | Semantic retrieval + few-shot sampling |
| `bot/chat.py` | RAG prompt + Groq/Gemini call |
| `app.py` | Gradio chat UI |

## Notes on responsible use

- Scraping public tweets may conflict with X's Terms of Service — keep volume
  low and use this for **personal/educational** purposes.
- Secrets (`.env`) and scraped data (`data/`) are gitignored and must never be
  committed.
- The persona is a light caricature with guardrails: it won't push products or
  fabricate real quotes/news attributed to a real person.
