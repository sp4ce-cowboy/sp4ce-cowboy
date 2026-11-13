"""Count lines of code across my repos with tokei and draw a donut card (light and dark).

Clones every repo listed in .github/loc-repos.txt (shallow), runs tokei, and writes badges/loc-{light,dark}.svg
and badges/loc.json (a shields.io endpoint badge). Needs `gh`, `git` and `tokei` on PATH.
Team repositories are included, so the total is code in my project repos, not only lines I wrote.
"""
import json, pathlib, subprocess, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from wakatime_cards import THEMES, languages_card, OUT  # noqa: E402

NOT_CODE = {"Markdown", "JSON", "YAML", "XML", "SVG", "CSV", "Plain Text", "Text", "TOML", "INI", "Autoconf",
            "ReStructuredText", "AsciiDoc", "Org", "Jupyter Notebooks", "License", "Batch"}
EXCLUDE = ["node_modules", "Pods", "build", "dist", ".build", "vendor", "docs", "javadocs", "assets",
           "Grove_LCD_RGB_Backlight-master", "Time-master", "weights", "*.min.js", "package-lock.json"]

def lines(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)

def main():
    listing = pathlib.Path(__file__).resolve().parents[1] / "loc-repos.txt"
    names = [l.strip() for l in listing.read_text().splitlines() if l.strip() and not l.startswith("#")]
    work = pathlib.Path(tempfile.mkdtemp())
    for n in names:   # gh uses GH_TOKEN in CI (a read-only token that can see private repos), else the local login
        r = subprocess.run(["gh", "repo", "clone", f"sp4ce-cowboy/{n}", str(work / n), "--", "-q", "--depth", "1"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"could not clone {n}; keeping the last published numbers", file=sys.stderr)
            return
    args = ["tokei", "--output", "json"] + [x for e in EXCLUDE for x in ("--exclude", e)] + [str(work)]
    data = json.loads(subprocess.run(args, capture_output=True, text=True, check=True).stdout)
    merge = {"TSX": "TypeScript", "JSX": "JavaScript", "C Header": "C", "C++ Header": "C++", "Objective-C++": "Objective-C"}
    langs = {}
    for k, v in data.items():
        if k == "Total" or k in NOT_CODE or not v.get("code"):
            continue
        langs[merge.get(k, k)] = langs.get(merge.get(k, k), 0) + v["code"]
    top = sorted(langs.items(), key=lambda kv: -kv[1])
    shown = top[:7]
    rest = sum(v for _, v in top[7:])
    if rest:
        shown.append(("Other", rest))
    total = sum(langs.values())
    for name, t in THEMES.items():
        (OUT / f"loc-{name}.svg").write_text(languages_card(shown, t, title="Lines of code across my repos",
                                                            fmt=lines, centre=f"{len(names)} repos"))
    (OUT / "loc.json").write_text(json.dumps({"schemaVersion": 1, "label": "lines of code", "message": lines(total),
                                              "color": "555"}) + "\n")
    print(f"{total:,} lines of code in {len(names)} repos:", [(k, v) for k, v in shown])

if __name__ == "__main__":
    main()
