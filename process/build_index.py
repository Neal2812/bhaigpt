"""Embed the clean tweets into a local vector index for retrieval.

Uses sentence-transformers (all-MiniLM-L6-v2) which runs locally and free — no
API key. Saves:
  - data/tweet_embeddings.npy  (float32 matrix, L2-normalized)
  - data/tweet_texts.json      (parallel list of tweet texts)

Usage:
    python -m process.build_index
"""
from __future__ import annotations

import json
import sys

import numpy as np

import config


def load_clean_texts() -> list[str]:
    texts: list[str] = []
    with config.CLEAN_TWEETS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            t = rec.get("clean_text") or rec.get("text") or ""
            if t.strip():
                texts.append(t.strip())
    return texts


def main() -> int:
    if not config.CLEAN_TWEETS.exists():
        print(
            f"ERROR: {config.CLEAN_TWEETS} not found. Run "
            "`python -m process.filter_tweets` first.",
            file=sys.stderr,
        )
        return 1

    texts = load_clean_texts()
    if not texts:
        print("ERROR: no clean tweets to embed.", file=sys.stderr)
        return 1

    print(f"Embedding {len(texts)} tweets with {config.EMBED_MODEL} (first run "
          "downloads the model)...")
    # Imported here so the rest of the pipeline doesn't require torch installed.
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(config.EMBED_MODEL)
    emb = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,  # enables cosine sim via dot product
    ).astype("float32")

    np.save(config.EMBEDDINGS, emb)
    with config.EMBED_TEXTS.open("w", encoding="utf-8") as out:
        json.dump(texts, out, ensure_ascii=False)

    print(f"\nSaved embeddings {emb.shape} -> {config.EMBEDDINGS}")
    print(f"Saved texts -> {config.EMBED_TEXTS}")
    print("Next: python app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
