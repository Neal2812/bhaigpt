"""Semantic retrieval over Bhai's tweets, plus few-shot sampling.

Loads the local embedding index built by process/build_index.py and, for a given
user message, returns the most similar real tweets as "style anchors". Also
provides a stable curated few-shot sample of his voice for the persona prompt.

Everything runs locally and free (no API key).
"""
from __future__ import annotations

import json
import random

import numpy as np

import config


class TweetRetriever:
    def __init__(self) -> None:
        if not config.EMBEDDINGS.exists() or not config.EMBED_TEXTS.exists():
            raise FileNotFoundError(
                "Embedding index not found. Run `python -m process.build_index` "
                "after scraping and filtering tweets."
            )
        self.embeddings: np.ndarray = np.load(config.EMBEDDINGS)
        with config.EMBED_TEXTS.open(encoding="utf-8") as fh:
            self.texts: list[str] = json.load(fh)
        self._model = None  # lazy-loaded SentenceTransformer

        # A fixed few-shot sample (seeded) so the persona prompt is stable.
        rng = random.Random(42)
        n = min(config.FEWSHOT_N, len(self.texts))
        self.fewshot: list[str] = rng.sample(self.texts, n) if n else []

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(config.EMBED_MODEL)
        return self._model

    def anchors(self, query: str, k: int | None = None) -> list[str]:
        """Return up to k tweets most similar to `query` (cosine similarity)."""
        k = k or config.TOP_K
        if not query.strip() or len(self.texts) == 0:
            return []
        q = self._get_model().encode(
            [query], normalize_embeddings=True
        ).astype("float32")[0]
        # Embeddings are L2-normalized, so dot product == cosine similarity.
        scores = self.embeddings @ q
        top = np.argsort(-scores)[:k]
        return [self.texts[i] for i in top]
