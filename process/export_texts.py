"""Export the cleaned tweets to data/tweet_texts.json (the committable corpus).

Lightweight, no torch — this is all the HOSTED app needs to stay grounded in
real tweets (few-shot mode). Run build_index.py instead/additionally if you want
full query-relevant retrieval locally.

Usage:
    python -m process.export_texts
"""
from __future__ import annotations

import json
import sys

import config


def main() -> int:
    if not config.CLEAN_TWEETS.exists():
        print(f"ERROR: {config.CLEAN_TWEETS} not found. Run "
              "`python -m process.filter_tweets` first.", file=sys.stderr)
        return 1

    texts: list[str] = []
    with config.CLEAN_TWEETS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            t = (rec.get("clean_text") or rec.get("text") or "").strip()
            if t:
                texts.append(t)

    with config.EMBED_TEXTS.open("w", encoding="utf-8") as out:
        json.dump(texts, out, ensure_ascii=False, indent=0)

    print(f"Wrote {len(texts)} tweets -> {config.EMBED_TEXTS}")
    print("Commit it for hosting:  git add -f data/tweet_texts.json")
    return 0 if texts else 1


if __name__ == "__main__":
    raise SystemExit(main())
