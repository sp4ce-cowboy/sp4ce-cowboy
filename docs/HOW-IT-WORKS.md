# How the profile README works

How each part of [README.md](../README.md) is made, where it comes from, and how to change it.
Kept up to date while the page is being built (last updated 2026-11-13).

## Files

| Path | What it is |
|---|---|
| `README.md` | The live profile page |
| `README-ORIGINAL.md` | The page as it was before Nov 2026 |
| `README-V2.md` | Version 2 (the project list) |
| `TECHSTACK-PREVIEW.md`, `TECHSTACK-PREVIEW-2.md` | Tech stack layouts under review (not shown on the profile) |
| `badges/` | Images and badge data the page loads, written by the scripts below |
| `.github/scripts/` | The scripts that write `badges/` |
| `.github/workflows/` | The schedules that run those scripts on GitHub |
| `.github/loc-repos.txt` | Which repos the lines-of-code count includes (edit freely) |

## Light and dark mode

Every image is wrapped in `<picture>`: a `<source media="(prefers-color-scheme: dark)">` for dark
mode and an `<img>` for light mode. GitHub shows the one that matches the viewer's theme.

## Sections, top to bottom

### whoami
Plain Markdown: a `sh` code block and a line of links. Edit it directly in `README.md`.

### tech stack
- **Badges:** [shields.io](https://shields.io) static badges, e.g.
  `https://img.shields.io/badge/Swift-black?logo=swift&logoColor=F05138`. Dark mode uses black
  badges; light mode uses `f6f8fa` badges with dark versions of white logos.
- **Logos:** [Simple Icons](https://simpleicons.org) names, passed as `logo=`.
- **Links:** each badge links to the code or write-up where the skill shows (a permalink or an
  `ARCHITECTURE.md` section). Badges with no link (C, Obj-C, SolidWorks, MATLAB, Logisim) are waiting
  for repos to point at.
- **Category labels:** shields.io `for-the-badge` badges (`white` in light mode, `21262d` in dark).
- Each category sits in a `<p>` so the badges flow on one line.

### coding
| Item | Source | Made by | Refreshed |
|---|---|---|---|
| Hours badges (all time, last 30 days, last 7 days) | WakaTime API | `wakatime_badges.py` writes `badges/wakatime-*.json`; shields.io's [endpoint badge](https://shields.io/badges/endpoint-badge) reads them | every 6 h |
| Lines-of-code badge | tokei over the repos in `loc-repos.txt` | `loc_card.py` writes `badges/loc.json` | daily |
| Coding time by language (left pie) | WakaTime all-time languages, excluding Markdown, data files and "Other" | `wakatime_cards.py` writes `badges/languages-{light,dark}.svg` | every 6 h |
| Lines of code by language (right pie) | tokei, as above | `loc_card.py` writes `badges/loc-{light,dark}.svg` | daily |
| Coding calendar | WakaTime daily totals, last 12 months | `wakatime_cards.py` writes `badges/calendar-{light,dark}.svg` | every 6 h |

**Lines of code, exactly:** each repo in `.github/loc-repos.txt` is cloned (latest commit only) and
[tokei](https://github.com/XAMPPRocky/tokei) counts **code lines**: no blank lines, no comments.
Left out: Markdown, JSON, YAML, XML, SVG, CSV, plain text, and the folders `node_modules`, `Pods`,
`build`, `dist`, `vendor`, `docs`, `javadocs`, `assets`, `weights` and two vendored Arduino libraries.
TSX counts as TypeScript and JSX as JavaScript. Team projects count in full.

**Drawing the pies:** `languages_card()` in `wakatime_cards.py` draws both (a donut plus a legend).
Language colours are in `LANG_COLORS`, light and dark palettes in `THEMES`; the card is 400 × 180.

### working with AI
`wakatime_cards.py` (`ai_card()`) sums, over the last 12 months of WakaTime summaries:
- **AI coding time:** the "AI Coding" category;
- **Agent sessions** and **prompts:** WakaTime's `ai_sessions` and `ai_prompt_events_total`;
- **Agents:** time in the editors Claude Code and Codex (from WakaTime's plugins for them);
- **Models:** the model names in `ai_model_breakdown`.

No line counts: most AI-written lines are Markdown notes, not code. Output:
`badges/ai-{light,dark}.svg`, every 6 h.

### GitHub stats and streak
- **Stats card with rank:** made by [github-readme-stats-action](https://github.com/stats-organization/github-readme-stats-action)
  (from [github-stats-extended](https://github.com/stats-organization/github-stats-extended)) in
  `stats.yml`, daily, into `badges/github-stats-{light,dark}.svg`. Self-hosted: no outside server.
  It uses the repo's own token, so it counts public activity only.
- **Streak card:** live from [streak-stats.demolab.com](https://streak-stats.demolab.com) (an outside service).

## Workflows and secrets

| Workflow | Runs | Needs |
|---|---|---|
| `wakatime.yml` | every 6 h, or by hand | secret `WAKATIME_API_KEY` (set) |
| `loc.yml` | daily, or by hand | secret `LOC_TOKEN`: a fine-grained token with read-only Contents and Metadata on all repos, so it can clone private ones (not set yet; the run skips without it and the last numbers stay) |
| `stats.yml` | daily, or by hand | nothing extra |

All three share one queue (`concurrency: profile-badges`) and rebase before pushing, so they
never overwrite each other. Run one by hand: `gh workflow run <name>.yml -R sp4ce-cowboy/sp4ce-cowboy`.

## Running the scripts locally
```sh
python3 .github/scripts/wakatime_badges.py   # reads ~/.wakatime-token
python3 .github/scripts/wakatime_cards.py
python3 .github/scripts/loc_card.py           # needs gh (logged in) and tokei
```
Then commit `badges/` and push.
