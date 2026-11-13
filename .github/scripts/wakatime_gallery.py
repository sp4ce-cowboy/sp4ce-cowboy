"""Draw candidate WakaTime charts (light and dark) for WAKATIME-PREVIEW.md, into badges/gallery-*.svg.

  editors     all-time hours per editor (horizontal bars)
  monthly     hours per month since tracking began (vertical bars)
  weekday     share of coding time per weekday (vertical bars)
  cumulative  total hours over time since tracking began (area chart)
"""
import datetime as dt, sys, pathlib, urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from wakatime_cards import THEMES, OUT, api, svg, esc, hours  # noqa: E402

ACCENT = ["#3b8ad9", "#F05138", "#3572A5", "#B07219", "#89E051", "#F1E05A", "#663399", "#8b949e"]

def hbars(title, rows, t, w=400):
    peak = max(v for _, v in rows) or 1
    parts = [f'<text x="16" y="22" font-size="13" font-weight="600" fill="{t["fg"]}">{esc(title)}</text>'] if title else []
    y = 44 if title else 20
    for i, (name, v) in enumerate(rows):
        bw = (w - 190) * v / peak
        parts.append(f'<text x="16" y="{y + 10}" font-size="12" fill="{t["fg"]}">{esc(name)}</text>')
        parts.append(f'<rect x="120" y="{y}" width="{max(bw, 2):.1f}" height="13" rx="3" fill="{ACCENT[0]}"/>')
        parts.append(f'<text x="{126 + bw:.1f}" y="{y + 10}" font-size="11" fill="{t["muted"]}">{hours(v)}</text>')
        y += 21
    return svg(w, y + 8, "".join(parts))

def vbars(rows, t, w=820, h=170, label_every=1, fmt=hours, values=False):
    peak = max(v for _, v in rows) or 1
    n = len(rows); gap = 4; bw = (w - 40 - gap * n) / n
    parts = []
    for i, (name, v) in enumerate(rows):
        bh = (h - 50) * v / peak
        x = 30 + i * (bw + gap)
        parts.append(f'<rect x="{x:.1f}" y="{h - 30 - bh:.1f}" width="{bw:.1f}" height="{max(bh, 1):.1f}" rx="2" fill="{ACCENT[0]}"><title>{esc(name)}: {fmt(v)}</title></rect>')
        if values or v == peak:
            parts.append(f'<text x="{x + bw / 2:.1f}" y="{h - 34 - bh:.1f}" font-size="10" text-anchor="middle" fill="{t["fg"]}">{fmt(v)}</text>')
        if i % label_every == 0:
            parts.append(f'<text x="{x + bw / 2:.1f}" y="{h - 14}" font-size="10" text-anchor="middle" fill="{t["muted"]}">{esc(name)}</text>')
    parts.append(f'<line x1="26" y1="{h - 30}" x2="{w - 8}" y2="{h - 30}" stroke="{t["line"]}"/>')
    return svg(w, h, "".join(parts))

def cumulative(days, t, w=820, h=170):
    dates = sorted(days); total, pts = 0, []
    x0, x1, y0, y1 = 30, w - 60, h - 30, 16
    span = (dates[-1] - dates[0]).days or 1
    run = []
    for d in dates:
        total += days[d]; run.append((d, total))
    peak = total or 1
    for d, v in run:
        pts.append(f"{x0 + (x1 - x0) * (d - dates[0]).days / span:.1f},{y0 - (y0 - y1) * v / peak:.1f}")
    parts = [f'<polygon points="{x0},{y0} {" ".join(pts)} {x1},{y0}" fill="{ACCENT[0]}" fill-opacity="0.25"/>',
             f'<polyline points="{" ".join(pts)}" fill="none" stroke="{ACCENT[0]}" stroke-width="2"/>',
             f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{t["line"]}"/>',
             f'<text x="{x1 + 6}" y="{y1 + 4}" font-size="12" font-weight="600" fill="{t["fg"]}">{hours(total)}</text>']
    for year in range(dates[0].year + 1, dates[-1].year + 1):
        x = x0 + (x1 - x0) * (dt.date(year, 1, 1) - dates[0]).days / span
        parts.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y0 + 4}" stroke="{t["line"]}"/>')
        parts.append(f'<text x="{x:.1f}" y="{y0 + 16}" font-size="10" text-anchor="middle" fill="{t["muted"]}">{year}</text>')
    return svg(w, h, "".join(parts))

def main():
    a = api("/stats/all_time")["data"]
    merged = {}
    for e in a["editors"]:
        name = "Codex" if e["name"].startswith("Codex") else e["name"]
        merged[name] = merged.get(name, 0) + e["total_seconds"]
    editors = sorted(((n, v) for n, v in merged.items() if v > 3600), key=lambda r: -r[1])[:7]
    start = dt.date.fromisoformat(a["start"][:10]); end = dt.date.today()
    days, s = {}, start
    while s <= end:
        e = min(s + dt.timedelta(days=89), end)
        for d in api("/summaries?" + urllib.parse.urlencode({"start": s.isoformat(), "end": e.isoformat()}))["data"]:
            days[dt.date.fromisoformat(d["range"]["date"])] = d["grand_total"]["total_seconds"]
        s = e + dt.timedelta(days=1)
    months = {}
    for d, v in days.items():
        months[(d.year, d.month)] = months.get((d.year, d.month), 0) + v
    mrows = [(dt.date(y, m, 1).strftime("%b %y"), months[(y, m)]) for (y, m) in sorted(months)]
    wk = [0] * 7
    for d, v in days.items():
        wk[d.weekday()] += v
    total = sum(wk) or 1
    wrows = [(n, 100 * v / total) for n, v in zip(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], wk)]
    for name, t in THEMES.items():
        (OUT / f"gallery-editors-{name}.svg").write_text(hbars("", editors, t))
        (OUT / f"gallery-monthly-{name}.svg").write_text(vbars(mrows, t, label_every=3))
        (OUT / f"gallery-weekday-{name}.svg").write_text(vbars(wrows, t, w=400, fmt=lambda v: f"{v:.0f}%", values=True))
        (OUT / f"gallery-cumulative-{name}.svg").write_text(cumulative(days, t))

if __name__ == "__main__":
    main()
