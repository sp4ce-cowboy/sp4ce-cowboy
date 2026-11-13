"""Draw WakaTime cards as SVG, each in a light and a dark version, into badges/.

  languages-{light,dark}.svg  all-time coding time by language (donut)
  calendar-{light,dark}.svg   daily coding time over the last 12 months
  ai-{light,dark}.svg         AI-assisted engineering over the last 12 months

Reads the API key from WAKATIME_API_KEY (GitHub Actions secret) or ~/.wakatime-token.
"""
import base64, datetime as dt, html, json, math, os, pathlib, urllib.parse, urllib.request

key = os.environ.get("WAKATIME_API_KEY") or pathlib.Path.home().joinpath(".wakatime-token").read_text().strip()
AUTH = {"Authorization": "Basic " + base64.b64encode(key.encode()).decode()}
OUT = pathlib.Path(__file__).resolve().parents[2] / "badges"

def api(path):
    req = urllib.request.Request("https://wakatime.com/api/v1/users/current" + path, headers=AUTH)
    return json.load(urllib.request.urlopen(req, timeout=60))

THEMES = {
    "light": dict(fg="#1f2328", muted="#59636e", line="#d1d9e0",
                  scale=["#ebedf0", "#c6dbef", "#6baed6", "#3182bd", "#08519c"]),
    "dark": dict(fg="#f0f6fc", muted="#9198a1", line="#3d444d",
                 scale=["#151b23", "#0e2a47", "#1f5a91", "#3b8ad9", "#79b8ff"]),
}
LANG_COLORS = {"Swift": "#F05138", "Python": "#3572A5", "Java": "#B07219", "TypeScript": "#3178C6",
               "JavaScript": "#F1E05A", "TeX": "#3D6117", "Bash": "#89E051", "Shell": "#89E051",
               "CSS": "#663399", "C++": "#F34B7D", "C": "#555555", "HTML": "#E34C26", "Cocoa": "#438EFF",
               "Objective-C": "#438EFF", "Kotlin": "#A97BFF", "Go": "#00ADD8", "Rust": "#DEA584", "SQL": "#E38C00"}
NOT_CODE = {"Markdown", "Other", "Text", "JSON", "YAML", "XML", "INI", "TOML", "Git Config", "Image (png)", "CSV"}
FONT = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<style>text{{{FONT}}}</style>{body}</svg>\n')

def esc(s): return html.escape(str(s))

def hours(seconds):
    h = seconds / 3600
    return f"{h:,.0f} h" if h >= 10 else f"{h:.1f} h"

# --- languages donut ------------------------------------------------------------------------
def languages_card(langs, t):
    total = sum(s for _, s in langs)
    r, cx, cy, sw = 62, 95, 100, 26
    circ = 2 * math.pi * r
    parts, offset = [], 0.0
    for name, s in langs:
        seg = circ * s / total
        color = LANG_COLORS.get(name, "#8b949e")
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{sw}" '
                     f'stroke-dasharray="{seg:.2f} {circ - seg:.2f}" stroke-dashoffset="{-offset:.2f}" '
                     f'transform="rotate(-90 {cx} {cy})"/>')
        offset += seg
    parts.append(f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" font-size="17" font-weight="600" fill="{t["fg"]}">{hours(total)}</text>')
    parts.append(f'<text x="{cx}" y="{cy + 15}" text-anchor="middle" font-size="11" fill="{t["muted"]}">all time</text>')
    y = 38
    for name, s in langs:
        color = LANG_COLORS.get(name, "#8b949e")
        parts.append(f'<rect x="190" y="{y - 9}" width="10" height="10" rx="2" fill="{color}"/>')
        parts.append(f'<text x="208" y="{y}" font-size="12.5" fill="{t["fg"]}">{esc(name)}</text>')
        parts.append(f'<text x="330" y="{y}" font-size="12.5" text-anchor="end" fill="{t["muted"]}">{hours(s)}</text>')
        parts.append(f'<text x="385" y="{y}" font-size="12.5" text-anchor="end" fill="{t["muted"]}">{100 * s / total:.0f}%</text>')
        y += 19
    title = f'<text x="16" y="22" font-size="14" font-weight="600" fill="{t["fg"]}">Coding time by language</text>'
    return svg(400, 200, title + "".join(parts))

# --- calendar heatmap -----------------------------------------------------------------------
def calendar_card(days, t):
    end = max(days); start = end - dt.timedelta(days=364)
    start -= dt.timedelta(days=start.weekday())            # weeks start on Monday
    peak = max(days.values()) or 1
    def level(s):
        if s <= 0: return 0
        f = s / peak
        return 1 if f < 0.15 else 2 if f < 0.35 else 3 if f < 0.65 else 4
    cell, gap, left, top = 11, 3, 34, 34
    parts, d, col, last_month = [], start, 0, None
    while d <= end:
        if d.weekday() == 0 and d.month != last_month and col < 52:
            parts.append(f'<text x="{left + col * (cell + gap)}" y="{top - 8}" font-size="10" fill="{t["muted"]}">{d:%b}</text>')
            last_month = d.month
        s = days.get(d, 0)
        tip = f"{d:%a %d %b %Y}: {hours(s)}" if s else f"{d:%a %d %b %Y}: no coding"
        parts.append(f'<rect x="{left + col * (cell + gap)}" y="{top + d.weekday() * (cell + gap)}" width="{cell}" height="{cell}" '
                     f'rx="2" fill="{t["scale"][level(s)]}"><title>{tip}</title></rect>')
        if d.weekday() == 6: col += 1
        d += dt.timedelta(days=1)
    for i, name in ((0, "Mon"), (2, "Wed"), (4, "Fri")):
        parts.append(f'<text x="2" y="{top + i * (cell + gap) + 9}" font-size="10" fill="{t["muted"]}">{name}</text>')
    width = left + (col + 1) * (cell + gap) + 10
    total = sum(days.values()); active = sum(1 for s in days.values() if s > 0)
    title = (f'<text x="2" y="14" font-size="14" font-weight="600" fill="{t["fg"]}">Coding activity, last 12 months</text>'
             f'<text x="{width - 10}" y="14" font-size="11.5" text-anchor="end" fill="{t["muted"]}">{hours(total)} over {active} days</text>')
    ly = top + 7 * (cell + gap) + 12
    legend = f'<text x="{width - 150}" y="{ly + 9}" font-size="10" fill="{t["muted"]}">Less</text>'
    for i in range(5):
        legend += f'<rect x="{width - 122 + i * (cell + gap)}" y="{ly}" width="{cell}" height="{cell}" rx="2" fill="{t["scale"][i]}"/>'
    legend += f'<text x="{width - 48}" y="{ly + 9}" font-size="10" fill="{t["muted"]}">More</text>'
    return svg(width, ly + 18, title + "".join(parts) + legend)

# --- AI card --------------------------------------------------------------------------------
def ai_card(ai, t):
    w = 440
    rows = [("AI coding time", hours(ai["ai_seconds"])),
            ("Agent sessions", f'{ai["sessions"]:,}'),
            ("Prompts", f'{ai["prompts"]:,}'),
            ("Lines written by AI", f'{ai["ai_lines"]:,}')]
    parts = [f'<text x="16" y="22" font-size="14" font-weight="600" fill="{t["fg"]}">AI-assisted engineering</text>',
             f'<text x="{w - 16}" y="22" font-size="11" text-anchor="end" fill="{t["muted"]}">last 12 months</text>']
    y = 50
    for label, value in rows:
        parts.append(f'<text x="16" y="{y}" font-size="12.5" fill="{t["muted"]}">{esc(label)}</text>')
        parts.append(f'<text x="{w - 16}" y="{y}" font-size="12.5" font-weight="600" text-anchor="end" fill="{t["fg"]}">{esc(value)}</text>')
        y += 20
    # share of added lines: by hand vs AI
    total = ai["ai_lines"] + ai["human_lines"] or 1
    share = ai["ai_lines"] / total
    bw = w - 32
    parts.append(f'<text x="16" y="{y + 8}" font-size="11.5" fill="{t["muted"]}">Lines added: {100 * (1 - share):.0f}% by hand, {100 * share:.0f}% with AI</text>')
    parts.append(f'<rect x="16" y="{y + 15}" width="{bw}" height="8" rx="4" fill="{t["scale"][2]}"/>')
    parts.append(f'<rect x="16" y="{y + 15}" width="{max(bw * share, 4):.1f}" height="8" rx="4" fill="#D97757"/>')
    y += 44
    models = ", ".join(f'{m["name"]} ({m["lines"]:,} lines)' for m in ai["models"] if m["lines"]) or "n/a"
    agents = ", ".join(f"{n} ({hours(s)})" for n, s in ai["agents"]) or "n/a"
    parts.append(f'<text x="16" y="{y}" font-size="11.5" fill="{t["muted"]}">Models: <tspan fill="{t["fg"]}">{esc(models)}</tspan></text>')
    parts.append(f'<text x="16" y="{y + 18}" font-size="11.5" fill="{t["muted"]}">Agents: <tspan fill="{t["fg"]}">{esc(agents)}</tspan></text>')
    return svg(w, y + 30, "".join(parts))

def main():
    OUT.mkdir(exist_ok=True)
    langs_all = api("/stats/all_time")["data"]["languages"]
    langs = [(l["name"], l["total_seconds"]) for l in langs_all if l["name"] not in NOT_CODE][:8]

    end = dt.date.today(); start = end - dt.timedelta(days=371)
    data, s = [], start
    while s <= end:                                         # the API takes ranges up to ~3 months
        e = min(s + dt.timedelta(days=89), end)
        data += api("/summaries?" + urllib.parse.urlencode({"start": s.isoformat(), "end": e.isoformat()}))["data"]
        s = e + dt.timedelta(days=1)
    days, ai = {}, dict(ai_seconds=0, sessions=0, prompts=0, ai_lines=0, human_lines=0)
    models, agents = {}, {}
    for day in data:
        d = dt.date.fromisoformat(day["range"]["date"])
        days[d] = day["grand_total"]["total_seconds"]
        g = day["grand_total"]
        ai["sessions"] += g.get("ai_sessions") or 0
        ai["prompts"] += g.get("ai_prompt_events_total") or 0
        ai["ai_lines"] += g.get("ai_additions") or 0
        ai["human_lines"] += g.get("human_additions") or 0
        for m in g.get("ai_model_breakdown") or []:
            models[m["name"]] = models.get(m["name"], 0) + (m.get("lines") or 0)
        for c in day.get("categories", []):
            if c["name"] == "AI Coding": ai["ai_seconds"] += c["total_seconds"]
        for e in day.get("editors", []):
            name = "Codex" if e["name"].startswith("Codex") else e["name"]
            if name in ("Claude Code", "Codex", "Cursor", "Copilot", "Windsurf", "Gemini CLI"):
                agents[name] = agents.get(name, 0) + e["total_seconds"]
    ai["models"] = sorted(({"name": k, "lines": v} for k, v in models.items() if "codex" not in k.lower()),
                          key=lambda m: -m["lines"])[:3]
    ai["agents"] = sorted(agents.items(), key=lambda x: -x[1])

    for name, t in THEMES.items():
        (OUT / f"languages-{name}.svg").write_text(languages_card(langs, t))
        (OUT / f"calendar-{name}.svg").write_text(calendar_card(days, t))
        (OUT / f"ai-{name}.svg").write_text(ai_card(ai, t))
    print("languages:", [(n, round(s / 3600)) for n, s in langs])
    print("calendar days:", len(days), "AI:", {k: v for k, v in ai.items() if k not in ("models",)}, ai["models"])

if __name__ == "__main__":
    main()
