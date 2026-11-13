"""Write WakaTime coding-time badges (shields.io endpoint JSON) into badges/.

Reads the API key from WAKATIME_API_KEY (GitHub Actions secret) or ~/.wakatime-token (local run).
"""
import base64, json, os, pathlib, urllib.request

key = os.environ.get("WAKATIME_API_KEY") or pathlib.Path.home().joinpath(".wakatime-token").read_text().strip()
auth = {"Authorization": "Basic " + base64.b64encode(key.encode()).decode()}

def get(path):
    req = urllib.request.Request("https://wakatime.com/api/v1/users/current" + path, headers=auth)
    return json.load(urllib.request.urlopen(req))["data"]

def short(text):
    return (text or "0 mins").replace(" hrs", " h").replace(" hr", " h").replace(" mins", " min").replace(" min", " min")

def summary(rng):
    req = urllib.request.Request("https://wakatime.com/api/v1/users/current/summaries?range=" + rng.replace(" ", "%20"), headers=auth)
    return json.load(urllib.request.urlopen(req))

week, month = summary("Last 7 Days"), summary("Last 30 Days")
badges = {
    "last 7 days": short(week["cumulative_total"]["text"]),
    "last 30 days": short(month["cumulative_total"]["text"]),
    "all time": short(get("/all_time_since_today")["text"]),
}
out = pathlib.Path(__file__).resolve().parents[2] / "badges"
out.mkdir(exist_ok=True)
for label, value in badges.items():
    name = "wakatime-" + label.replace(" ", "-") + ".json"
    (out / name).write_text(json.dumps({"schemaVersion": 1, "label": label, "message": value,
                                        "color": "007ec6", "labelColor": "555", "namedLogo": "wakatime", "logoColor": "white"}) + "\n")
    print(label, "→", value)
