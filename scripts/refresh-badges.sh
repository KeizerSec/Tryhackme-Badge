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
#
# Resilient by design: when launchd fires just after the Mac wakes, the network may
# not be up yet — so it waits for connectivity and retries each repo a few times,
# and one repo failing never aborts the other. Exits 0 if there is simply no network
# (the next scheduled run will catch up).
set -uo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

ENGINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="${THM_BADGE_CACHE:-$HOME/.cache/thm-badge}"
USERNAME="${THM_USERNAME:-Keizer}"
COMMITTER_NAME="${THM_COMMITTER_NAME:-KeizerSec}"
COMMITTER_EMAIL="${THM_COMMITTER_EMAIL:-185857228+KeizerSec@users.noreply.github.com}"
mkdir -p "$CACHE"

log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

# Wait until github.com is reachable (the Mac may have just woken with no network).
wait_for_network() {
  local i
  for i in $(seq 1 12); do
    if curl -fsS -m 8 -o /dev/null https://github.com 2>/dev/null; then
      return 0
    fi
    log "network not ready (attempt $i/12), waiting 20s..."
    sleep 20
  done
  return 1
}

refresh() {
  local repo="$1" out="$2" theme="$3"
  local dir="$CACHE/$(basename "$repo")"
  log "── $repo → $out (theme: $theme)"
  local attempt rc
  for attempt in 1 2 3; do
    (
      set -e
      [ -d "$dir/.git" ] || git clone --quiet "https://github.com/$repo.git" "$dir"
      git -C "$dir" config credential.helper '!gh auth git-credential'  # gh token, non-interactive
      git -C "$dir" fetch --quiet origin main
      git -C "$dir" reset --quiet --hard origin/main
      THM_USERNAME="$USERNAME" OUTPUT_PATH="$dir/$out" THEME="$theme" node "$ENGINE/src/generate.js"
      git -C "$dir" add "$out"
      git -C "$dir" diff --staged --quiet && exit 10   # 10 = nothing changed
      git -C "$dir" -c user.name="$COMMITTER_NAME" -c user.email="$COMMITTER_EMAIL" \
        commit --quiet -m "chore: refresh TryHackMe badge"
      git -C "$dir" push --quiet origin HEAD:main
    )
    rc=$?
    case $rc in
      0)  log "   pushed ✓"; return 0 ;;
      10) log "   no change."; return 0 ;;
      *)  log "   attempt $attempt/3 failed (rc=$rc)"; sleep $((attempt * 15)) ;;
    esac
  done
  log "   FAILED after 3 attempts"
  return 1
}

if ! wait_for_network; then
  log "no network after waiting — skipping; the next scheduled run will catch up."
  exit 0
fi

status=0
# Profile badge (what people see on your GitHub profile) — most important.
refresh "KeizerSec/KeizerSec"       "assets/thm_badge.svg" "rotate" || status=1
# Project demo badge (shown in the Tryhackme-Badge README).
refresh "KeizerSec/Tryhackme-Badge" "assets/demo.svg"      "rotate" || status=1
log "done (status=$status)."
exit $status
