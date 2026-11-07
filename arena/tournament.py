"""Reproducible, fully paired round robin; every game gets a replay."""
from __future__ import annotations

import itertools
import json
import random
import secrets
from datetime import datetime, timezone
from pathlib import Path

from .core import SAFE_ID, SeasonInfo, compile_cpp, run_match, sha256


def read_roster(path: str | Path, info: SeasonInfo):
    path = Path(path).resolve()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("season") != info.id:
        raise ValueError(f"Roster season mismatch: expected {info.id}")
    raw_bots = raw.get("bots")
    if not isinstance(raw_bots, list) or len(raw_bots) < 2:
        raise ValueError("Roster requires at least two bots")
    seen = set()
    bots = []
    for item in raw_bots:
        key = item.get("id", "")
        if not isinstance(key, str) or not SAFE_ID.fullmatch(key) or key in seen:
            raise ValueError(f"Unsafe or repeated bot id: {key}")
        seen.add(key)
        source = Path(item.get("source", ""))
        if not source.is_absolute():
            source = path.parent / source
        if source.suffix not in (".cpp", ".cc") or not source.is_file():
            raise ValueError(f"Bot source missing or not C++: {source}")
        bots.append({"id": key, "label": str(item.get("label", key))[:80],
                     "kind": str(item.get("kind", "participant"))[:25], "source": source.resolve()})
    seeds = raw.get("seeds")
    if seeds is None:
        count = int(raw.get("seed_count", info.meta.get("default_seeds", 10)))
        master = int(raw["seed_master"]) if "seed_master" in raw else secrets.randbits(64)
        if not 1 <= count <= 300:
            raise ValueError("seed_count must be in 1..300")
        seeds = random.Random(master).sample(range(1, 2**30), count)
    if not isinstance(seeds, list) or not seeds or len(seeds) > 300 or any(type(s) is not int for s in seeds):
        raise ValueError("seeds must be a nonempty list of <=300 integers")
    if len(set(seeds)) != len(seeds):
        raise ValueError("Duplicate seeds are not allowed")
    return bots, seeds


def build_roster(bots, info: SeasonInfo, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    players = []
    for b in bots:
        build = compile_cpp(b["source"], info, output / b["id"])
        players.append({**b, "source": str(b["source"]), "binary": build["binary"],
                        "source_sha256": build["source_sha256"],
                        "binary_sha256": build["binary_sha256"]})
    return players


def rank_players(players, matches):
    stats = {p["id"]: {"id": p["id"], "label": p["label"], "kind": p["kind"],
                        "wins": 0, "draws": 0, "losses": 0, "match_points": 0.0,
                        "score_for": 0, "score_against": 0, "games": 0}
             for p in players}
    for m in matches:
        for side, key in enumerate(m["bot_ids"]):
            s = stats[key]
            s["games"] += 1
            s["score_for"] += m["scores"][side]
            s["score_against"] += m["scores"][1 - side]
            if m["winner"] is None:
                s["draws"] += 1
                s["match_points"] += 0.5
            elif m["winner"] == side:
                s["wins"] += 1
                s["match_points"] += 1
            else:
                s["losses"] += 1
    leaderboard = list(stats.values())
    for s in leaderboard:
        s["score_diff"] = s["score_for"] - s["score_against"]
        s["win_rate"] = round(s["match_points"] / max(1, s["games"]), 5)
    # Primary: total match points. Score margin is SECONDARY (not part of wins).
    # Identical records retain the same standing rank.
    leaderboard.sort(key=lambda s: (-s["match_points"], -s["score_diff"],
                                    -s["score_for"], s["id"]))
    prev = None
    for ix, s in enumerate(leaderboard):
        key = (s["match_points"], s["score_diff"], s["score_for"])
        if key != prev:
            rank = ix + 1
        s["rank"] = rank
        prev = key
    return leaderboard


def run_tournament(info: SeasonInfo, roster_path: str | Path, output: str | Path,
                   *, timeout: float = 0.5, verbose=True):
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    bots, seeds = read_roster(roster_path, info)
    players = build_roster(bots, info, out / "build")
    matches = []
    pairings = list(itertools.combinations(range(len(players)), 2))
    for i, j in pairings:
        for seed in seeds:
            for blue, red in ((i, j), (j, i)):
                match_index = len(matches)
                replay = out / "replays" / f"match_{match_index:04d}.json"
                m = run_match(info, [players[blue], players[red]], seed,
                              timeout=timeout, replay=replay)
                m["index"] = match_index
                m["kinds"] = [players[blue]["kind"], players[red]["kind"]]
                m["replay"] = f"replays/match_{match_index:04d}.json"
                matches.append(m)
                if verbose:
                    print(f"[{match_index + 1}/{len(pairings)*len(seeds)*2}] "
                          f"{m['bot_ids'][0]} vs {m['bot_ids'][1]} "
                          f"{m['scores']} winner={m['winner']}", flush=True)
    leaderboard = rank_players(players, matches)
    metadata = [{k: v for k, v in player.items() if k not in ("binary", "source")}
                for player in players]
    report = {"schema": 1, "season": info.id, "title": info.meta["title"],
              "version": info.meta.get("version"), "created_at": datetime.now(timezone.utc).isoformat(),
              "seed_list": seeds, "scoring": "win=1 draw=0.5 loss=0; then score difference, total score",
              "matches_total": len(matches), "bot_count": len(players),
              "participants": metadata,
              "judge_sha256": sha256(info.judge), "adapter_sha256": sha256(info.adapter),
              "leaderboard": leaderboard, "matches": matches}
    (out / "tournament.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
    if verbose:
        print("\nOfficial standing (paired round robin):")
        for p in leaderboard:
            print(f" {p['rank']:2d}. {p['label'][:22]:22s} {p['match_points']:.1f}pt "
                  f"W{p['wins']}/D{p['draws']}/L{p['losses']}")
        print("Report:", out / "tournament.json")
    return report
