"""Draw WakaTime cards as SVG, each in a light and a dark version, into badges/.

  languages-{light,dark}.svg  all-time coding time by language (donut)
  calendar-{light,dark}.svg   daily coding time over the last 12 months

Reads the API key from WAKATIME_API_KEY (GitHub Actions secret) or ~/.wakatime-token.
"""
import base64, datetime as dt, html, json, math, os, pathlib, urllib.parse, urllib.request

OUT = pathlib.Path(__file__).resolve().parents[2] / "badges"

def api(path):
    key = os.environ.get("WAKATIME_API_KEY") or pathlib.Path.home().joinpath(".wakatime-token").read_text().strip()
    auth = {"Authorization": "Basic " + base64.b64encode(key.encode()).decode()}
    req = urllib.request.Request("https://wakatime.com/api/v1/users/current" + path, headers=auth)
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
def languages_card(langs, t, title=None, fmt=None, centre="all time"):
    fmt = fmt or hours
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
    parts.append(f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" font-size="17" font-weight="600" fill="{t["fg"]}">{fmt(total)}</text>')
    parts.append(f'<text x="{cx}" y="{cy + 15}" text-anchor="middle" font-size="11" fill="{t["muted"]}">{esc(centre)}</text>')
    y = 38
    for name, s in langs:
        color = LANG_COLORS.get(name, "#8b949e")
        parts.append(f'<rect x="190" y="{y - 9}" width="10" height="10" rx="2" fill="{color}"/>')
        parts.append(f'<text x="208" y="{y}" font-size="12.5" fill="{t["fg"]}">{esc(name)}</text>')
        parts.append(f'<text x="330" y="{y}" font-size="12.5" text-anchor="end" fill="{t["muted"]}">{fmt(s)}</text>')
        parts.append(f'<text x="385" y="{y}" font-size="12.5" text-anchor="end" fill="{t["muted"]}">{100 * s / total:.0f}%</text>')
        y += 19
    if not title:                                          # graph only: shift everything up
        return svg(400, 180, f'<g transform="translate(0,-14)">{"".join(parts)}</g>')
    title = f'<text x="16" y="22" font-size="14" font-weight="600" fill="{t["fg"]}">{esc(title)}</text>'
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
    ly = top + 7 * (cell + gap) + 12
    legend = f'<text x="{width - 150}" y="{ly + 9}" font-size="10" fill="{t["muted"]}">Less</text>'
    for i in range(5):
        legend += f'<rect x="{width - 122 + i * (cell + gap)}" y="{ly}" width="{cell}" height="{cell}" rx="2" fill="{t["scale"][i]}"/>'
    legend += f'<text x="{width - 48}" y="{ly + 9}" font-size="10" fill="{t["muted"]}">More</text>'
    return svg(width, ly + 18 - 22, f'<g transform="translate(0,-22)">{"".join(parts)}{legend}</g>')

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
    days = {}
    for day in data:
        days[dt.date.fromisoformat(day["range"]["date"])] = day["grand_total"]["total_seconds"]

    for name, t in THEMES.items():
        (OUT / f"languages-{name}.svg").write_text(languages_card(langs, t))
        (OUT / f"calendar-{name}.svg").write_text(calendar_card(days, t))
    print("languages:", [(n, round(s / 3600)) for n, s in langs])
    print("calendar days:", len(days))

if __name__ == "__main__":
    main()
