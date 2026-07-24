"""Register a burner X (Twitter) account with twscrape.

Run this ONCE before scraping. It reads credentials from your .env (never
committed) and stores an authenticated session in a local twscrape SQLite DB.
Use a throwaway account — scraping can get accounts rate-limited or locked.

Usage:
    python -m scrape.setup_account

If you already have a cookies string (X_COOKIES in .env), it is used directly
and no password login is attempted.
"""
from __future__ import annotations

import asyncio
import sys

from twscrape import API

import config


async def main() -> int:
    if not config.X_USERNAME:
        print(
            "ERROR: X_USERNAME is not set. Copy .env.example to .env and fill in\n"
            "a burner X account (username/password/email) or X_COOKIES.",
            file=sys.stderr,
        )
        return 1

    api = API(str(config.TWSCRAPE_DB))

    if config.X_COOKIES:
        print(f"Adding account '{config.X_USERNAME}' via cookies...")
        await api.pool.add_account(
            config.X_USERNAME,
            config.X_PASSWORD or "x",
            config.X_EMAIL or "",
            config.X_EMAIL_PASSWORD or "",
            cookies=config.X_COOKIES,
        )
    else:
        print(f"Adding account '{config.X_USERNAME}' and logging in...")
        await api.pool.add_account(
            config.X_USERNAME,
            config.X_PASSWORD,
            config.X_EMAIL,
            config.X_EMAIL_PASSWORD,
        )
        await api.pool.login_all()

    accounts = await api.pool.accounts_info()
    active = [a for a in accounts if a.get("active")]
    print(f"\nAccounts in pool: {len(accounts)} | active: {len(active)}")
    for a in accounts:
        print(f"  - {a.get('username')}: active={a.get('active')}")

    if not active:
        print(
            "\nWARNING: No active account. Login may have failed (bad creds, "
            "captcha, or account flagged). Try X_COOKIES instead, or a different "
            "burner account.",
            file=sys.stderr,
        )
        return 1

    print("\nReady. Next: python -m scrape.scrape_tweets")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
