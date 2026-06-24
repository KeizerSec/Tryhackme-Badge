#!/usr/bin/env bash
# Refresh the TryHackMe badge SVGs from a residential IP.
#
# Why local: TryHackMe's API is behind Vercel bot mitigation that challenges every
# datacenter IP (all GitHub-hosted runners / VPS), so the badge cannot be refreshed
# from the cloud. From a residential connection a browser-TLS request (curl_cffi)
# is served the JSON directly. This script is run daily by a launchd agent.
#
# It uses this repo's src/ as the rendering engine and writes/commits the badges in
# throwaway clones under $THM_BADGE_CACHE, so it never touches your working copy.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

ENGINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="${THM_BADGE_CACHE:-$HOME/.cache/thm-badge}"
USERNAME="${THM_USERNAME:-Keizer}"
COMMITTER_NAME="${THM_COMMITTER_NAME:-KeizerSec}"
COMMITTER_EMAIL="${THM_COMMITTER_EMAIL:-185857228+KeizerSec@users.noreply.github.com}"
mkdir -p "$CACHE"

log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

refresh() {
  local repo="$1" out="$2" theme="$3"
  local dir="$CACHE/$(basename "$repo")"
  log "── $repo → $out (theme: $theme)"
  if [ ! -d "$dir/.git" ]; then
    git clone --quiet "https://github.com/$repo.git" "$dir"
  fi
  # Push over HTTPS using the gh token (works non-interactively under launchd).
  git -C "$dir" config credential.helper '!gh auth git-credential'
  git -C "$dir" fetch --quiet origin main
  git -C "$dir" reset --quiet --hard origin/main

  THM_USERNAME="$USERNAME" OUTPUT_PATH="$dir/$out" THEME="$theme" node "$ENGINE/src/generate.js"

  git -C "$dir" add "$out"
  if git -C "$dir" diff --staged --quiet; then
    log "   no change."
    return 0
  fi
  git -C "$dir" -c user.name="$COMMITTER_NAME" -c user.email="$COMMITTER_EMAIL" \
    commit --quiet -m "chore: refresh TryHackMe badge"
  git -C "$dir" push --quiet origin HEAD:main
  log "   pushed ✓"
}

# Profile badge (what people see on your GitHub profile) — most important.
refresh "KeizerSec/KeizerSec"       "assets/thm_badge.svg" "rotate"
# Project demo badge (shown in the Tryhackme-Badge README).
refresh "KeizerSec/Tryhackme-Badge" "assets/demo.svg"      "rotate"
log "done."
