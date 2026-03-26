import requests
from datetime import datetime
import os

WEBHOOK_URL = "https://discord.com/api/webhooks/1486796669365522624/y_Xo6Kp9HPKlVyaMiQoTJlDn24qtPzlwcYz-8sPiy31Hs4MdHV4_n9nIlhr3yRREBFi_"

today = datetime.now().strftime("%Y-%m-%d")

LEAGUES = {
    "🇬🇧 Premier League": "4328",
    "🇪🇸 La Liga": "4335",
    "🇮🇹 Serie A": "4332",
    "🇩🇪 Bundesliga": "4331",
    "🇬🇷 Super League": "4334",
    "🇪🇺 Champions League": "4480",
    "🇪🇺 Europa League": "4481",
    "🌍 World Cup": "4429",
    "🇪🇺 Euro": "4482",
    "🏆 Nations League": "4483"
}

def is_big_team(team):
    BIG_TEAMS = [
        "real madrid", "barcelona", "atletico",
        "manchester united", "manchester city", "liverpool",
        "arsenal", "chelsea",
        "bayern",
        "juventus", "inter", "milan",
        "psg",
        "olympiacos"
    ]
    return any(t in team.lower() for t in BIG_TEAMS)

def is_super_big(home, away):
    SUPER_MATCHES = [
        ("real madrid", "barcelona"),
        ("arsenal", "chelsea"),
        ("liverpool", "manchester united"),
        ("inter", "milan"),
        ("olympiacos", "panathinaikos")
    ]
    home = home.lower()
    away = away.lower()

    for t1, t2 in SUPER_MATCHES:
        if (t1 in home and t2 in away) or (t2 in home and t1 in away):
            return True
    return False

def is_greece_match(home, away):
    return "greece" in home.lower() or "greece" in away.lower()

all_matches = []
thumbnail = None  # 🔥 for logo

for league_name, league_id in LEAGUES.items():
    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={today}&l={league_id}"
    
    response = requests.get(url)
    data = response.json()

    if data.get("events"):
        for match in data["events"]:
            home = match["strHomeTeam"]
            away = match["strAwayTeam"]
            time = match["strTime"][:5] if match["strTime"] else "TBD"

            score_home = match.get("intHomeScore")
            score_away = match.get("intAwayScore")

            score = f"{score_home} - {score_away}" if score_home is not None else "vs"

            is_greece = is_greece_match(home, away)

            # 🖼️ Try to get a logo (first big match)
            if not thumbnail and (is_greece or is_super_big(home, away)):
                thumbnail = match.get("strThumb")

            all_matches.append({
                "league": league_name,
                "time": time,
                "home": home,
                "away": away,
                "score": score,
                "big": is_big_team(home) or is_big_team(away) or is_greece,
                "super": is_super_big(home, away),
                "greece": is_greece,
                "live": score_home is not None
            })

# ❌ No matches
if not all_matches:
    new_state = f"NO_MATCHES_{today}"
else:
    all_matches.sort(key=lambda x: x["time"])
    new_state = "".join([
        f"{m['league']}{m['time']}{m['home']}{m['away']}{m['score']}"
        for m in all_matches
    ])

# 📁 Load last state
last_state = ""
if os.path.exists("last_state.txt"):
    with open("last_state.txt", "r") as f:
        last_state = f.read()

if new_state == last_state:
    exit()

with open("last_state.txt", "w") as f:
    f.write(new_state)

# 🔴 LIVE + normal
live_matches = [m for m in all_matches if m["live"]]
other_matches = [m for m in all_matches if not m["live"]]

fields = []

# 🔴 LIVE
if live_matches:
    text = ""
    for m in live_matches:
        prefix = "🇬🇷🔥 " if m["greece"] else "⭐🔥 " if m["super"] else "🔥 "
        text += f"{prefix}**{m['home']} {m['score']} {m['away']}**\n"

    fields.append({"name": "🔴 LIVE NOW", "value": text, "inline": False})

# 🏆 normal
current = ""
text = ""

for m in other_matches:
    if m["league"] != current:
        if text:
            fields.append({"name": current, "value": text, "inline": False})
        current = m["league"]
        text = ""

    prefix = "🇬🇷🔥 " if m["greece"] else "⭐🔥 " if m["super"] else "🔥 " if m["big"] else ""
    text += f"{prefix}{m['time']} - {m['home']} vs {m['away']}\n"

if text:
    fields.append({"name": current, "value": text, "inline": False})

# 🚀 SEND
embed = {
    "title": "⚽ Daily Fixtures & Live Scores",
    "description": "🇬🇷 Athens time | 🔴 Live updates",
    "color": 3066993,
    "fields": fields
}

# 🖼️ add thumbnail if exists
if thumbnail:
    embed["thumbnail"] = {"url": thumbnail}

requests.post(WEBHOOK_URL, json={"embeds": [embed]})
