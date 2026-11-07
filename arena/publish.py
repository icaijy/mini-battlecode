"""Generate a static season microsite; NO Django integration or engine code."""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from .core import SeasonInfo


STYLE = """
:root{color-scheme:dark;font:15px/1.5 system-ui,Arial,sans-serif;background:#101720;color:#e5ebf4}
*{box-sizing:border-box}body{max-width:1100px;margin:auto;padding:28px 22px}
a{color:#9cd6ff}h1{font-size:clamp(28px,5vw,44px);margin:5px 0}
h2{font-size:22px;margin:30px 0 12px}.sub{color:#9aaac1}
.pill{background:#27374b;border:1px solid #455570;border-radius:50px;padding:4px 11px;font-size:12px}
.card{background:#1c2736;border:1px solid #34445a;border-radius:14px;padding:18px;margin-top:15px}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:9px 8px;border-bottom:1px solid #304055}
.badge{background:#2c405a;border-radius:8px;padding:3px 8px}small{color:#9aabc2}
.muted{background:#304969}.muted{color:#9aabc2}footer{margin-top:35px;color:#899aae;font-size:13px}
@media(max-width:600px){body{padding:15px 9px}table{font-size:12px}th,td{padding:6px 3px}}
"""


def publish(info: SeasonInfo, report_path: str | Path, dest: str | Path) -> Path:
    """Export the full standings and EVERY replay. Video selection is manual."""
    source = Path(report_path).resolve()
    base = source.parent
    report = json.loads(source.read_text(encoding="utf-8"))
    if report.get("season") != info.id:
        raise ValueError("Results and season mismatch")
    dest = Path(dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    replay_dest = dest / "replays"
    replay_dest.mkdir(exist_ok=True)
    shutil.copy2(info.viewer, dest / "viewer.html")
    shutil.copy2(info.rules, dest / "RULES.md")

    matches = report.get("matches", [])
    if not isinstance(matches, list):
        raise ValueError("Invalid match list")
    for match in matches:
        index = match.get("index")
        relative = match.get("replay")
        if type(index) is not int or index < 0 or relative != f"replays/match_{index:04d}.json":
            raise ValueError("Invalid replay reference in match report")
        origin = base / relative
        if not origin.is_file():
            raise FileNotFoundError(f"Replay missing: {origin}")
    # Avoid stale replays when replacing an earlier export of this season.
    for old in replay_dest.glob("match_*.json"):
        old.unlink()
    for match in matches:
        relative = match["replay"]
        shutil.copy2(base / relative, replay_dest / Path(relative).name)

    public = {k: report[k] for k in (
        "schema", "season", "title", "version", "created_at", "seed_list",
        "scoring", "matches_total", "bot_count", "leaderboard") if k in report}
    (dest / "results.json").write_text(json.dumps(public, indent=2, ensure_ascii=False) + "\n",
                                      encoding="utf-8")
    public_matches = [{key: value for key, value in match.items()
                       if key != "elapsed_seconds"} for match in matches]
    (dest / "matches.json").write_text(
        json.dumps(public_matches, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    esc = lambda x: html.escape(str(x), quote=True)
    rows = "\n".join(
        "<tr><td>" + esc(s["rank"]) + "</td><td>" + esc(s["label"]) + "</td><td>" +
        esc(s["match_points"]) + "</td><td>" +
        f'{s["wins"]}/{s["draws"]}/{s["losses"]}' + "</td><td>" +
        esc(s["score_diff"]) + "</td></tr>"
        for s in report["leaderboard"])
    match_rows = "\n".join(
        "<tr><td>" + esc(m["index"]) + "</td><td>" +
        esc(m["bot_names"][0]) + " vs " + esc(m["bot_names"][1]) + "</td><td>" +
        esc(m["scores"][0]) + " : " + esc(m["scores"][1]) + "</td><td>" +
        esc(m["seed"]) + "</td><td><a href=\"viewer.html?replay=" +
        esc(m["replay"]) + "\">Watch</a></td></tr>"
        for m in matches)
    content = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(report["title"])} · Results</title><style>{STYLE}</style></head><body>
<span class="pill">Mini Battlecode · Official standings</span><h1>{esc(report["title"])}</h1>
<p class="sub">{esc(report["matches_total"])} matches · {esc(report["bot_count"])} participants · paired seeds and swapped sides · {esc(report["version"])}</p>
<section class="card"><h2>Leaderboard</h2><table><thead><tr><th>#</th><th>Bot</th><th>Points</th><th>W/D/L</th><th>Diff</th></tr></thead>
<tbody>{rows}</tbody></table><p class="muted">Champion = best full round-robin result.</p></section>
<details class="card"><summary><strong>All matches &amp; replays ({len(matches)})</strong></summary>
<p class="muted">Every match is available. The organiser chooses which games to feature in videos.</p>
<table><thead><tr><th>#</th><th>Teams</th><th>Score</th><th>Seed</th><th>Replay</th></tr></thead>
<tbody>{match_rows}</tbody></table></details>
<footer><a href="matches.json">All match results (JSON)</a> · <a href="results.json">Leaderboard data (JSON)</a>.<br>
This is a static results export, not a live judge. Replays are not automatically ranked or selected.</footer>
</body></html>'''
    (dest / "index.html").write_text(content, encoding="utf-8")
    return dest


def publish_hub(root: str | Path) -> Path:
    """Build a season index from static exports, without knowing any game rules."""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    seasons = []
    for season_results in sorted(root.glob("*/results.json")):
        info = json.loads(season_results.read_text(encoding="utf-8"))
        if not (season_results.parent / "index.html").is_file():
            continue
        leaderboard = info.get("leaderboard") or []
        title = info.get("title")
        if not isinstance(title, str) or not leaderboard:
            continue
        seasons.append({"season": season_results.parent.name, "title": title,
                        "created_at": info.get("created_at", ""),
                        "participants": info.get("bot_count", len(leaderboard)),
                        "matches": info.get("matches_total", 0),
                        "champions": [p["label"] for p in leaderboard if p.get("rank") == 1]})
    seasons.sort(key=lambda x: x["created_at"], reverse=True)
    (root / "seasons.json").write_text(json.dumps({"schema": 1, "seasons": seasons},
                                                 indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    esc = lambda x: html.escape(str(x), quote=True)
    cards = "\n".join(
        f'<div class="card"><h2><a href="{esc(x["season"])}/index.html">{esc(x["title"])}</a></h2>'
        f'<div class="sub">{esc(x["matches"])} matches · {esc(x["participants"])} bots · {esc(x["created_at"][:10])}</div>'
        f'<p>Champion: <strong>{esc(", ".join(x["champions"]))}</strong></p></div>' for x in seasons)
    content = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mini Battlecode — Season Archive</title><style>{STYLE}</style></head><body>
<span class="pill">Human vs AI · Archives</span><h1>Mini Battlecode</h1>
<p class="sub">Season results and full replay archive. Matches run offline in a separate engine repository.</p>
{cards if cards else '<p>No completed seasons published yet.</p>'}
<footer>Official rankings are based on paired full round robins. Showcase matches do not affect the title.</footer>
</body></html>'''
    (root / "index.html").write_text(content, encoding="utf-8")
    return root
