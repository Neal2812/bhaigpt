"""Scrape @BeingSalmanKhan's tweets into data/raw_tweets.jsonl via twscrape.

Requires an authenticated account in the pool (see setup_account.py). Writes one
JSON object per line. Re-running resumes: already-saved tweet IDs are skipped, so
you can top up the archive over time without duplicates.

Usage:
    python -m scrape.scrape_tweets [--limit N]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from twscrape import API

import config


def _load_seen_ids() -> set[str]:
    seen: set[str] = set()
    if config.RAW_TWEETS.exists():
        with config.RAW_TWEETS.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    seen.add(str(json.loads(line)["id"]))
                except (json.JSONDecodeError, KeyError):
                    continue
    return seen


def _tweet_to_record(tw) -> dict:
    """Flatten a twscrape Tweet into a compact, serializable record."""
    urls = [u.expandedUrl or u.url for u in (tw.links or [])]
    hashtags = list(tw.hashtags or [])
    has_media = bool(getattr(tw, "media", None) and (
        tw.media.photos or tw.media.videos or tw.media.animated
    ))
    return {
        "id": str(tw.id),
        "text": tw.rawContent or "",
        "date": tw.date.isoformat() if tw.date else None,
        "likes": tw.likeCount or 0,
        "retweets": tw.retweetCount or 0,
        "replies": tw.replyCount or 0,
        "is_retweet": tw.retweetedTweet is not None,
        "is_reply": tw.inReplyToTweetId is not None,
        "is_quote": tw.quotedTweet is not None,
        "has_media": has_media,
        "urls": urls,
        "hashtags": hashtags,
        "lang": tw.lang,
    }


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=config.MAX_TWEETS)
    args = parser.parse_args()

    api = API(str(config.TWSCRAPE_DB))
    accounts = await api.pool.accounts_info()
    if not any(a.get("active") for a in accounts):
        print(
            "ERROR: No active account in the pool. Run "
            "`python -m scrape.setup_account` first.",
            file=sys.stderr,
        )
        return 1

    seen = _load_seen_ids()
    print(f"Resuming: {len(seen)} tweets already saved. Target handle: "
          f"@{config.TARGET_HANDLE}")

    user = await api.user_by_login(config.TARGET_HANDLE)
    if user is None:
        print(f"ERROR: Could not resolve @{config.TARGET_HANDLE}.", file=sys.stderr)
        return 1

    written = 0
    with config.RAW_TWEETS.open("a", encoding="utf-8") as out:
        async for tw in api.user_tweets(user.id, limit=args.limit):
            if str(tw.id) in seen:
                continue
            rec = _tweet_to_record(tw)
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            seen.add(rec["id"])
            written += 1
            if written % 50 == 0:
                print(f"  ...saved {written} new tweets")

    total = len(seen)
    print(f"\nDone. New: {written} | total on disk: {total} -> {config.RAW_TWEETS}")
    if total == 0:
        print(
            "No tweets saved. The account may be rate-limited or the timeline "
            "empty/protected. Try again later or use a different burner account.",
            file=sys.stderr,
        )
        return 1
    print("Next: python -m process.filter_tweets")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
