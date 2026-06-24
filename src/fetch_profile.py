#!/usr/bin/env python3
"""Fetch a TryHackMe public profile as JSON, defeating Vercel's bot mitigation.

TryHackMe's API sits behind Vercel's bot challenge. Two layers matter:

1. TLS/HTTP-2 fingerprint — a plain Node/`curl` request is challenged outright.
   curl_cffi reproduces Chrome's handshake, so from a normal (residential) IP the
   JSON is served directly, no challenge.
2. IP reputation — from a datacenter IP (e.g. a CI runner) Vercel still issues the
   JS challenge even to a browser-grade client. In that case we solve it: fetch
   Vercel's own challenge worker + WASM and run them offline (src/solve_wasm.js) to
   compute the proof-of-work, then submit it over the same browser-TLS session to
   obtain the `_vcrcs` cookie.

No headless browser involved. Usage: fetch_profile.py <username>  (or THM_USERNAME).
Prints the API JSON to stdout. Exit: 0 ok, 2 usage, 3 blocked/unreachable.
"""
import os
import subprocess
import sys
import tempfile

try:
    from curl_cffi import requests
except ImportError:
    sys.stderr.write("[thm-badge] curl_cffi is not installed. Run: pip install curl_cffi\n")
    sys.exit(3)

ORIGIN = "https://tryhackme.com"
PROFILE_URL = f"{ORIGIN}/api/v2/public-profile"
WORKER_URL = f"{ORIGIN}/.well-known/vercel/security/static/challenge.v2.min.js"
WASM_URL = f"{ORIGIN}/.well-known/vercel/security/static/challenge.v2.wasm"
SUBMIT_URL = f"{ORIGIN}/.well-known/vercel/security/request-challenge"
IMPERSONATE = "chrome"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
HERE = os.path.dirname(os.path.abspath(__file__))


def log(msg):
    sys.stderr.write(f"[thm-badge] {msg}\n")


def get_profile(session, username):
    return session.get(PROFILE_URL, params={"username": username}, headers={"accept": "application/json"}, timeout=25)


def is_json_ok(resp):
    return resp.status_code == 200 and "json" in (resp.headers.get("content-type") or "")


def solve_challenge(session, token):
    """Compute the PoW with Vercel's own worker+WASM and submit it (browser-TLS)."""
    worker_src = session.get(WORKER_URL, timeout=25).text
    wasm_bytes = session.get(WASM_URL, timeout=25).content
    with tempfile.TemporaryDirectory() as tmp:
        wjs = os.path.join(tmp, "worker.js")
        wasm = os.path.join(tmp, "challenge.wasm")
        with open(wjs, "w") as f:
            f.write(worker_src)
        with open(wasm, "wb") as f:
            f.write(wasm_bytes)
        proc = subprocess.run(
            ["node", os.path.join(HERE, "solve_wasm.js")],
            env={**os.environ, "THM_TOKEN": token, "WORKER_JS_PATH": wjs, "WASM_PATH": wasm, "UA": UA},
            capture_output=True, text=True, timeout=40,
        )
    if proc.returncode != 0 or not proc.stdout.strip():
        log(f"WASM solver failed (rc={proc.returncode}): {proc.stderr.strip()[:200]}")
        return False
    solution = proc.stdout.strip()
    resp = session.post(SUBMIT_URL, headers={
        "x-vercel-challenge-solution": solution,
        "x-vercel-challenge-token": token,
        "x-vercel-challenge-version": "2",
        "accept": "*/*", "origin": ORIGIN, "referer": f"{PROFILE_URL}",
    }, timeout=25)
    log(f"challenge submit -> HTTP {resp.status_code}; cookie set: {'_vcrcs' in session.cookies}")
    return resp.status_code in (200, 204) or "_vcrcs" in session.cookies


def main() -> int:
    username = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("THM_USERNAME") or "").strip()
    if not username:
        log("usage: fetch_profile.py <username>")
        return 2

    session = requests.Session(impersonate=IMPERSONATE)

    # Layer 1: browser-TLS direct (works from a normal IP).
    resp = get_profile(session, username)
    if is_json_ok(resp):
        sys.stdout.write(resp.text)
        return 0

    # Layer 2: challenged (e.g. datacenter IP) — solve it, then retry.
    token = resp.headers.get("x-vercel-challenge-token")
    if resp.status_code == 429 and resp.headers.get("x-vercel-mitigated") == "challenge" and token:
        log("challenged; solving Vercel proof-of-work over browser-TLS...")
        for attempt in range(1, 4):
            if solve_challenge(session, token):
                resp = get_profile(session, username)
                if is_json_ok(resp):
                    log(f"solved on attempt {attempt}")
                    sys.stdout.write(resp.text)
                    return 0
            token = resp.headers.get("x-vercel-challenge-token") or token
            resp = get_profile(session, username)
            if is_json_ok(resp):
                sys.stdout.write(resp.text)
                return 0
            token = resp.headers.get("x-vercel-challenge-token") or token

    log(f"could not fetch profile; last status {resp.status_code} (mitigated={resp.headers.get('x-vercel-mitigated')})")
    return 3


if __name__ == "__main__":
    sys.exit(main())
