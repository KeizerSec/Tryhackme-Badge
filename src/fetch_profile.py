#!/usr/bin/env python3
"""Fetch a TryHackMe public profile as JSON, using a browser-grade TLS fingerprint.

TryHackMe's API sits behind Vercel's bot mitigation, which serves a JavaScript
challenge (HTTP 429, `x-vercel-mitigated: challenge`) to any client whose TLS /
HTTP-2 fingerprint does not look like a real browser. A plain `fetch`/`curl`/Node
request is therefore blocked. curl_cffi reproduces Chrome's exact handshake, so
Vercel serves the JSON directly — no challenge to solve, no headless browser.

Note: Vercel also weighs IP reputation, so this only works from a normal
(residential) IP — a datacenter / CI runner IP is challenged regardless of TLS.
Run it from a machine on a residential connection.

Usage: fetch_profile.py <username>   (or set THM_USERNAME)
Prints the raw API JSON to stdout on success; diagnostics go to stderr.
Exit codes: 0 = JSON printed, 2 = bad usage, 3 = blocked/unreachable.
"""
import os
import sys

try:
    from curl_cffi import requests
except ImportError:
    sys.stderr.write("[thm-badge] curl_cffi is not installed. Run: pip install curl_cffi\n")
    sys.exit(3)

# Chrome/Safari handshakes that get served the JSON instead of the challenge.
IMPERSONATE_PROFILES = ["chrome", "chrome131", "safari", "chrome120"]
TIMEOUT = 25


def main() -> int:
    username = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("THM_USERNAME") or "").strip()
    if not username:
        sys.stderr.write("[thm-badge] usage: fetch_profile.py <username>\n")
        return 2

    url = "https://tryhackme.com/api/v2/public-profile"
    last = "no attempt"
    for profile in IMPERSONATE_PROFILES:
        try:
            resp = requests.get(
                url,
                params={"username": username},
                impersonate=profile,
                headers={"accept": "application/json"},
                timeout=TIMEOUT,
            )
        except Exception as exc:  # network error, TLS error, timeout…
            last = f"{profile}: {type(exc).__name__}: {exc}"
            continue

        if resp.status_code == 200 and "json" in (resp.headers.get("content-type") or ""):
            sys.stdout.write(resp.text)
            return 0

        mitigated = resp.headers.get("x-vercel-mitigated")
        last = f"{profile}: HTTP {resp.status_code}" + (f" (mitigated={mitigated})" if mitigated else "")

    sys.stderr.write(
        f"[thm-badge] could not fetch profile via browser-TLS; last attempt: {last}\n"
        "[thm-badge] (a datacenter/CI IP is always challenged — run from a residential connection)\n"
    )
    return 3


if __name__ == "__main__":
    sys.exit(main())
