# How the profile README works

How each part of [README.md](../README.md) is made and how to change it.

## Files

| Path | What it is |
|---|---|
| `README.md` | The live profile page |
| `README-ORIGINAL.md`, `README-V2.md`, `README-V3.md` | Earlier versions, kept for reference |
| `TECHSTACK-PREVIEW.md`, `TECHSTACK-PREVIEW-2.md` | Tech stack layouts that were considered |
| `WAKATIME-PREVIEW.md` | WakaTime chart options being considered (drawn by `wakatime_gallery.py`, not refreshed by the workflow) |
| `.github/scripts/` | Scripts that draw the badges and cards |
| `.github/workflows/profile-cards.yml` | The schedule that runs them |
| `.github/loc-repos.txt` | Which repos the lines-of-code chart counts |
| `output` branch | The generated badges and cards the page loads |

## Light and dark mode

Every image sits in a `<picture>`: a `<source media="(prefers-color-scheme: dark)">` for dark mode
and an `<img>` for light mode, so GitHub shows the one that matches the viewer's theme.

## Sections

### whoami
Plain Markdown: a `sh` code block. Edit it directly in `README.md`.

### tech stack
One line per category of plain Markdown links. Each skill links to the code or write-up where it
is used (a permalink or an `ARCHITECTURE.md` section in one of my repos). Edit the lines directly.

### coding stats
| Item | Source | Made by | Refreshed |
|---|---|---|---|
| Hours badges (all time, last 30 days, last 7 days, daily average over 30 days) | WakaTime API | `wakatime_badges.py` writes `wakatime-*.json`; shields.io's [endpoint badge](https://shields.io/badges/endpoint-badge) draws them in WakaTime's colours | every 6 h |
| Coding time by language (left) | WakaTime all-time languages | `wakatime_cards.py` → `languages-{light,dark}.svg` | every 6 h |
| Lines of code by language (right) | tokei over the repos in `loc-repos.txt` | `loc_card.py` → `loc-{light,dark}.svg` | daily |
| Coding calendar | WakaTime daily totals, last 12 months | `wakatime_cards.py` → `calendar-{light,dark}.svg` | every 6 h |
| GitHub stats with rank | GitHub API | [github-readme-stats-action](https://github.com/stats-organization/github-readme-stats-action) → `github-stats-{light,dark}.svg` | daily |
| Streak | [streak-stats.demolab.com](https://streak-stats.demolab.com) | live | live |

**Lines of code:** each repo in `.github/loc-repos.txt` is cloned (latest commit) and
[tokei](https://github.com/XAMPPRocky/tokei) counts code lines, leaving out blank lines, comments,
documentation and data files (Markdown, JSON, YAML, XML, SVG, CSV, text) and dependency or generated
folders (`node_modules`, `Pods`, `build`, `dist`, `vendor`, `docs`, `assets`). TSX counts as
TypeScript and JSX as JavaScript.

**The charts:** `languages_card()` in `wakatime_cards.py` draws both pies (a donut plus a legend).
Language colours are in `LANG_COLORS`, the light and dark palettes in `THEMES`. `calendar_card()`
draws the calendar.

**Caching:** GitHub serves README images through its own cache. After changing how a card looks,
add or bump a `?v=` on its URL in `README.md` so the new version shows straight away.

## The workflow

`profile-cards.yml` runs every 6 hours (WakaTime) and once a day (lines of code and the GitHub stats
card), or by hand: `gh workflow run profile-cards.yml -R sp4ce-cowboy/sp4ce-cowboy`.

It starts from the files already on the `output` branch, updates them, and force-pushes the result
to `output` as a single commit. `main` never receives automated commits.

| Secret | Used for |
|---|---|
| `WAKATIME_API_KEY` | WakaTime badges and cards |
| `LOC_TOKEN` | A fine-grained token with read-only Contents and Metadata on all my repos, so the lines-of-code count can clone private ones. Without it, that step is skipped and the last numbers stay |

## Running the scripts locally
```sh
python3 .github/scripts/wakatime_badges.py   # reads ~/.wakatime-token
python3 .github/scripts/wakatime_cards.py
python3 .github/scripts/loc_card.py           # needs gh (logged in) and tokei
python3 .github/scripts/wakatime_gallery.py   # the charts in WAKATIME-PREVIEW.md
```
They write to `badges/` (ignored on `main`). To publish by hand, push that folder to the `output`
branch the way the workflow's last step does.
