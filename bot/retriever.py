"""Retrieval + few-shot sampling over Bhai's tweets — with graceful degradation.

Three modes, picked automatically by what data is present:
  1. Full RAG      — embeddings index present -> query-relevant "style anchors"
                     (needs sentence-transformers/torch).
  2. Few-shot only — tweet texts present but no embeddings -> a random sample of
                     his real tweets grounds the style (lightweight, no torch).
  3. Persona only  — no tweet data at all -> the caller falls back to the persona
                     prompt alone. Nothing here raises.

This lets the hosted (Streamlit) app run even before any scraping has happened,
and stay lightweight when only the tweet text list is committed.
"""
from __future__ import annotations

import json
import random

import numpy as np

import config


class TweetRetriever:
    def __init__(self) -> None:
        self.texts: list[str] = self._load_texts()
        self.embeddings: np.ndarray | None = self._load_embeddings()
        self._model = None  # lazy-loaded SentenceTransformer

        # A fixed few-shot sample (seeded) so the persona prompt is stable.
        rng = random.Random(42)
        n = min(config.FEWSHOT_N, len(self.texts))
        self.fewshot: list[str] = rng.sample(self.texts, n) if n else []

    # --- data loading (never raises) ----------------------------------------
    def _load_texts(self) -> list[str]:
        """Prefer the embedding text list, else the cleaned tweets, else none."""
        if config.EMBED_TEXTS.exists():
            try:
                with config.EMBED_TEXTS.open(encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    return [t for t in data if isinstance(t, str) and t.strip()]
            except (json.JSONDecodeError, OSError):
                pass
        texts: list[str] = []
        if config.CLEAN_TWEETS.exists():
            with config.CLEAN_TWEETS.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    t = (rec.get("clean_text") or rec.get("text") or "").strip()
                    if t:
                        texts.append(t)
        return texts

    def _load_embeddings(self) -> np.ndarray | None:
        if not (config.EMBEDDINGS.exists() and self.texts):
            return None
        try:
            emb = np.load(config.EMBEDDINGS)
        except (OSError, ValueError):
            return None
        # Only usable if it lines up with the loaded texts.
        return emb if emb.shape[0] == len(self.texts) else None

    @property
    def has_tweets(self) -> bool:
        return bool(self.texts)

    # --- retrieval ----------------------------------------------------------
    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(config.EMBED_MODEL)
        return self._model

    def anchors(self, query: str, k: int | None = None) -> list[str]:
        """Query-relevant tweets via cosine similarity. Empty if no embeddings."""
        k = k or config.TOP_K
        if self.embeddings is None or not query.strip() or not self.texts:
            return []
        try:
            q = self._get_model().encode(
                [query], normalize_embeddings=True
            ).astype("float32")[0]
        except Exception:  # noqa: BLE001 - torch/model missing -> degrade to few-shot
            return []
        # Embeddings are L2-normalized, so dot product == cosine similarity.
        scores = self.embeddings @ q
        top = np.argsort(-scores)[:k]
        return [self.texts[i] for i in top]
