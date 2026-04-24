# TryHackMe Badge

A GitHub Action that generates a beautiful, self-updating SVG badge with your live TryHackMe stats — rank, rooms, badges, level, league — straight from the official public profile API.

<p align="center">
  <img src="assets/demo.svg" alt="Live demo badge" width="640">
</p>

> Spiritual successor to the now-archived [`p4p1/tryhackme-badge-workflow`](https://github.com/p4p1/tryhackme-badge-workflow). Pure SVG. No Puppeteer. No Chrome on your runner. No HTML scraping.

## Features

- **Live data** — pulls from `tryhackme.com/api/v2/public-profile`, no auth required
- **5 themes** — `midnight`, `matrix`, `synthwave`, `inferno`, `frost`
- **Rotating themes** — defaults to `rotate`: deterministic per UTC day, so visitors see the same theme worldwide on a given day, but it changes overnight
- **Pure SVG** — no external fonts, no remote images, renders instantly through GitHub's image proxy
- **Customizable** — override the accent color, lock to one theme, change the output path, disable auto-commit
- **Lightweight** — composite action, zero npm dependencies, runs in under 10 seconds

## Quick start

Create `.github/workflows/thm-badge.yml` in your profile repository:

```yaml
name: Update TryHackMe Badge

on:
  schedule:
    - cron: '17 5 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: KeizerSec/Tryhackme-Badge@v1
        with:
          username: YourThmUsername
```

Then reference the badge in your README:

```markdown
![TryHackMe](https://raw.githubusercontent.com/<you>/<you>/main/assets/thm_badge.svg)
```

Trigger the workflow once manually (Actions → *Update TryHackMe Badge* → *Run workflow*). From then on it refreshes daily.

## Inputs

| Name | Required | Default | Description |
|---|:---:|---|---|
| `username` | yes | — | Your TryHackMe username. |
| `output_path` | no | `assets/thm_badge.svg` | Where the SVG is written, relative to the repo root. |
| `theme` | no | `rotate` | `rotate` (deterministic per UTC day), `random` (per-run), or one of: `midnight`, `matrix`, `synthwave`, `inferno`, `frost`. |
| `accent_color` | no | — | Hex color (e.g. `#00FF9D`) that overrides the theme accent and border. |
| `auto_commit` | no | `true` | Whether to commit and push the updated badge. Set to `false` to write the file only. |
| `commit_message` | no | `chore: refresh TryHackMe badge` | |
| `committer_name` | no | `github-actions[bot]` | |
| `committer_email` | no | `41898282+github-actions[bot]@users.noreply.github.com` | |

## Outputs

| Name | Description |
|---|---|
| `theme_used` | Name of the theme that was actually rendered. |
| `rank` | Current world rank value reported by the API. |

## Themes

Five themes ship out of the box. The default is `rotate`, which advances by one each UTC day so the badge feels alive without the chaos of per-run randomization.

| Name | Vibe |
|---|---|
| `midnight` | Balanced SOC analyst look, dark GitHub background, chartreuse accent |
| `matrix` | Pure black background, phosphor green, terminal-vintage |
| `synthwave` | Deep purple background, magenta and cyan accents, 80s retrowave |
| `inferno` | Charcoal background, ember orange and amber, red-team energy |
| `frost` | Light background with ice blue accents, for light-mode READMEs |

Lock to a single theme:

```yaml
- uses: KeizerSec/Tryhackme-Badge@v1
  with:
    username: YourName
    theme: matrix
```

Customize the accent color while keeping a theme:

```yaml
- uses: KeizerSec/Tryhackme-Badge@v1
  with:
    username: YourName
    theme: midnight
    accent_color: "#FF6B35"
```

## How it works

The action calls the TryHackMe public profile API:

```
GET https://tryhackme.com/api/v2/public-profile?username=<you>
```

It returns clean JSON with rank, rooms, badges, points, level, and league tier. The action renders a self-contained SVG using inline gradients and SVG primitives only — no `@font-face`, no remote images, no JavaScript inside the SVG — so GitHub's image proxy serves it without sandboxing issues. The output is committed back to the repository so the README can reference it via `raw.githubusercontent.com`.

## Why not p4p1's action?

The original [`p4p1/tryhackme-badge-workflow`](https://github.com/p4p1/tryhackme-badge-workflow) was archived on 2026-04-19. Its dynamic mode relied on `tryhackme.com/api/v2/badges/public-profile?userPublicId=...`, which currently returns *"There was an error while generating your badge"* for any input from outside TryHackMe's own infrastructure. Its static mode pulled from `tryhackme-badges.s3.amazonaws.com`, a bucket that has been frozen since 2024.

This action uses a different, working endpoint and renders the SVG itself, so it is independent of TryHackMe's own badge rendering pipeline.

## Permissions

The default `GITHUB_TOKEN` needs `contents: write` permission so the action can commit the refreshed badge. The example workflow above sets this at the job level. If you prefer to set it at the workflow level, add this near the top of your YAML:

```yaml
permissions:
  contents: write
```

## Local preview

You can render a badge locally without setting up a workflow:

```bash
git clone https://github.com/KeizerSec/Tryhackme-Badge.git
cd Tryhackme-Badge
THM_USERNAME=YourName THEME=synthwave OUTPUT_PATH=/tmp/badge.svg node src/generate.js
open /tmp/badge.svg
```

## License

MIT — see [LICENSE](LICENSE).
