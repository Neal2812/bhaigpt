"""Ingest an Apify "Tweet Scraper" CSV export into data/raw_tweets.jsonl.

A free alternative to live scraping: run the Apify Tweet Scraper actor (it has a
free tier), download the CSV, and feed it here. The output matches the schema
produced by scrape/scrape_tweets.py, so the rest of the pipeline
(filter_tweets -> export_texts / build_index) is unchanged.

Usage:
    python -m process.ingest_csv path/to/apify_export.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys

import config

URL_RE = re.compile(r"https?://\S+")
HASHTAG_RE = re.compile(r"#(\w+)")


def _truthy(v: str | None) -> bool:
    return str(v).strip().lower() in ("true", "1", "yes")


def _row_to_record(row: dict) -> dict | None:
    text = (row.get("fullText") or row.get("text") or "").strip()
    if not text:
        return None
    tid = row.get("id") or row.get("url") or row.get("twitterUrl") or ""
    has_media = any(
        row.get(k) for k in row
        if k.startswith("entities/media/") and k.endswith("/media_url_https")
    ) or bool(row.get("entities/media/0/display_url"))
    return {
        "id": str(tid),
        "text": text,
        "date": row.get("createdAt"),
        "likes": int(row.get("likeCount") or 0) if str(row.get("likeCount") or "").isdigit() else 0,
        "retweets": int(row.get("retweetCount") or 0) if str(row.get("retweetCount") or "").isdigit() else 0,
        "replies": int(row.get("replyCount") or 0) if str(row.get("replyCount") or "").isdigit() else 0,
        "is_retweet": _truthy(row.get("isRetweet")),
        "is_reply": _truthy(row.get("isReply")),
        "is_quote": _truthy(row.get("isQuote")),
        "has_media": bool(has_media),
        "urls": URL_RE.findall(text),
        "hashtags": HASHTAG_RE.findall(text),
        "lang": row.get("lang"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", help="Path to the Apify Tweet Scraper CSV export")
    parser.add_argument("--handle", default=config.TARGET_HANDLE,
                        help="Only keep tweets authored by this username")
    args = parser.parse_args()

    seen: set[str] = set()
    if config.RAW_TWEETS.exists():
        with config.RAW_TWEETS.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        seen.add(str(json.loads(line)["id"]))
                    except (json.JSONDecodeError, KeyError):
                        pass

    # utf-8-sig strips the BOM some exports include.
    with open(args.csv_path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    written = skipped_author = skipped_dup = 0
    with config.RAW_TWEETS.open("a", encoding="utf-8") as out:
        for row in rows:
            author = (row.get("author/userName") or "").lstrip("@")
            if args.handle and author.lower() != args.handle.lower():
                skipped_author += 1
                continue
            rec = _row_to_record(row)
            if rec is None:
                continue
            if rec["id"] and rec["id"] in seen:
                skipped_dup += 1
                continue
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            seen.add(rec["id"])
            written += 1

    print(f"CSV rows: {len(rows)} | ingested: {written} | "
          f"skipped (other author): {skipped_author} | skipped (dup): {skipped_dup}")
    print(f"-> {config.RAW_TWEETS}")
    if written == 0 and skipped_author:
        print(f"NOTE: no rows matched handle '{args.handle}'. "
              "Pass --handle to match your export, or --handle '' to keep all.",
              file=sys.stderr)
    print("Next: python -m process.filter_tweets")
    return 0 if written else 1


if __name__ == "__main__":
    raise SystemExit(main())
