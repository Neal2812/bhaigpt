"""Filter raw tweets down to authentic-voice tweets for BhaiGPT.

Removes retweets/replies and ad/promo/campaign noise so the chatbot learns how
Salman Khan actually *talks*, not how his PR team advertises. Emits:
  - data/clean_tweets.jsonl  (kept tweets)
  - data/filter_report.json  (counts + samples of what was dropped, per reason)

The filtering is heuristic and auditable — inspect the report and tune the
keyword lists / thresholds in this file or config.py as needed.

Usage:
    python -m process.filter_tweets
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter

import config

# --- Promo / ad signals -----------------------------------------------------
# Case-insensitive substring/keyword hits that mark a tweet as promotional.
PROMO_KEYWORDS = [
    "being human",
    "beinghumanclothing",
    "in cinemas",
    "in theatres",
    "in theaters",
    "book your tickets",
    "book now",
    "advance booking",
    "tickets now",
    "out now",
    "trailer out",
    "teaser out",
    "song out",
    "first look",
    "releasing on",
    "hits the screens",
    "presented by",
    "in association with",
    "powered by",
    "sponsored",
    "brand ambassador",
    "use code",
    "download the app",
    "click the link",
    "link in bio",
    "giveaway",
    "contest",
    "lucky winner",
    "stand a chance",
    "pre-order",
    "now streaming",
    "watch now",
    "coming soon on",
]

# Regex signals (hashtag campaigns, #ad disclosures, ticketing domains).
PROMO_PATTERNS = [
    re.compile(r"#ad\b", re.I),
    re.compile(r"#sponsored\b", re.I),
    re.compile(r"#paidpartnership", re.I),
    re.compile(r"\b(bookmyshow|paytm|ticketnew|pvrcinemas|inox)\b", re.I),
    re.compile(r"\bcinemas?\b.*\b(feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|eid|diwali)\b", re.I),
]

URL_RE = re.compile(r"https?://\S+")
HASHTAG_RE = re.compile(r"#\w+")
MENTION_RE = re.compile(r"@\w+")


def _promo_reason(rec: dict) -> str | None:
    """Return a reason string if the tweet looks promotional, else None."""
    text = rec.get("text", "") or ""
    low = text.lower()

    for kw in PROMO_KEYWORDS:
        if kw in low:
            return f"keyword:{kw}"
    for pat in PROMO_PATTERNS:
        if pat.search(text):
            return f"pattern:{pat.pattern}"

    # Mostly-URL tweets (links dominate the content).
    url_chars = sum(len(m) for m in URL_RE.findall(text))
    if text and url_chars / len(text) > config.MAX_URL_RATIO:
        return "mostly_url"

    # Mostly-hashtag tweets (campaign spam).
    tokens = text.split()
    if tokens:
        hashtag_ratio = sum(1 for t in tokens if t.startswith("#")) / len(tokens)
        if hashtag_ratio > config.MAX_HASHTAG_RATIO:
            return "mostly_hashtags"

    return None


def _clean_text(text: str) -> str:
    """Light normalization for the kept tweets (used as style corpus)."""
    text = URL_RE.sub("", text)          # drop links; they add no voice
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main() -> int:
    if not config.RAW_TWEETS.exists():
        print(
            f"ERROR: {config.RAW_TWEETS} not found. Run "
            "`python -m scrape.scrape_tweets` first.",
            file=sys.stderr,
        )
        return 1

    reasons = Counter()
    dropped_samples: dict[str, list[str]] = {}
    kept: list[dict] = []
    seen_norm: set[str] = set()
    total = 0

    with config.RAW_TWEETS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total += 1
            rec = json.loads(line)
            text = rec.get("text", "") or ""

            reason = None
            if rec.get("is_retweet"):
                reason = "retweet"
            elif rec.get("is_reply"):
                reason = "reply"
            elif len(_clean_text(text)) < config.MIN_TWEET_CHARS:
                reason = "too_short"
            else:
                reason = _promo_reason(rec)

            if reason is None:
                cleaned = _clean_text(text)
                norm = cleaned.lower()
                if norm in seen_norm:
                    reason = "duplicate"
                else:
                    seen_norm.add(norm)
                    rec["clean_text"] = cleaned
                    kept.append(rec)
                    continue

            reasons[reason] += 1
            bucket = dropped_samples.setdefault(reason, [])
            if len(bucket) < 5:
                bucket.append(text[:200])

    with config.CLEAN_TWEETS.open("w", encoding="utf-8") as out:
        for rec in kept:
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")

    report = {
        "total_raw": total,
        "kept": len(kept),
        "dropped": total - len(kept),
        "dropped_by_reason": dict(reasons.most_common()),
        "dropped_samples": dropped_samples,
    }
    with config.FILTER_REPORT.open("w", encoding="utf-8") as out:
        json.dump(report, out, ensure_ascii=False, indent=2)

    print(f"Raw: {total} | kept: {len(kept)} | dropped: {total - len(kept)}")
    print("Dropped by reason:")
    for reason, n in reasons.most_common():
        print(f"  {reason:16s} {n}")
    print(f"\nClean tweets -> {config.CLEAN_TWEETS}")
    print(f"Filter report -> {config.FILTER_REPORT}")
    if not kept:
        print("WARNING: nothing survived filtering — loosen thresholds/keywords.",
              file=sys.stderr)
        return 1
    print("Next: python -m process.build_index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
