"""Reusable command-line interface; independent of individual games."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .core import (ROOT, SAFE_ID, compile_cpp, create_game, resolve_season,
                   run_match)
from .publish import publish, publish_hub
from .tournament import run_tournament


def _doctor(name: str):
    from sys import version_info
    print(f"Python: {version_info.major}.{version_info.minor} (needs >= 3.10)")
    compiler = shutil.which("g++")
    if version_info < (3, 10) or not compiler:
        raise RuntimeError("Need Python >= 3.10 and g++; on Ubuntu use: sudo apt install python3 g++")
    print(f"C++ compiler: {compiler}")
    info = resolve_season(name)
    game = create_game(info, 1)
    for team in (0, 1):
        obs = game.observe(team)
        if not isinstance(obs, str) or not obs.endswith("\n") or "\n" in obs[:-1]:
            raise RuntimeError("Season judge must produce one newline-terminated observation")
    json.dumps(game.snapshot())
    json.dumps(game.outcome())
    print(f"Season plugin: {info.id} OK ({game.max_turns} turns)")
    print("Ready. Try: mbc duel --season " + info.id +
          " --blue seasons/" + info.id + "/example_bot.cpp" +
          " --red seasons/" + info.id + "/example_bot.cpp")


def _init_season(name, source):
    if not SAFE_ID.fullmatch(name):
        raise ValueError("Season ID must contain only letters, numbers, underscore or hyphen")
    src = resolve_season(source)
    target = ROOT / "seasons" / name
    if target.exists():
        raise FileExistsError(f"Season already exists: {target}")
    shutil.copytree(src.path, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    manifest_path = target / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data.update(id=name, title=name.replace("_", " ").title() + " (DRAFT)", version="0.1.0")
    manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Created draft {target}")
    print("IMPORTANT: replace game.py, arena.hpp, grader.cpp, viewer.html, RULES.md")
    print("Then run: mbc doctor --season " + name)


def _duel(args):
    season = resolve_season(args.season)
    if args.timeout <= 0:
        raise ValueError("--timeout must be positive")
    with tempfile.TemporaryDirectory(prefix="mbc-duel-") as temp:
        blue = compile_cpp(args.blue, season, Path(temp) / "blue")
        red = compile_cpp(args.red, season, Path(temp) / "red")
        players = [{"id": "blue", "label": Path(args.blue).stem, "binary": blue["binary"]},
                   {"id": "red", "label": Path(args.red).stem, "binary": red["binary"]}]
        replay = args.replay or f"results/{season.id}/duel.json"
        report = run_match(season, players, args.seed, timeout=args.timeout, replay=replay)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print("Replay:", Path(replay).resolve())


def _finals(args):
    season = resolve_season(args.season)
    if args.timeout <= 0:
        raise ValueError("Timeout must be positive")
    if bool(args.roster) == bool(args.bot):
        raise ValueError("Provide exactly one of --roster or at least two --bot id=path options")
    if args.roster and (args.seed_count is not None or args.seed_master is not None or args.human):
        raise ValueError("For --roster mode specify seed_count, seed_master and kind in roster JSON")
    tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = Path(args.out or f"results/{season.id}/{tag}").resolve()
    site_root = Path(args.site_root or "published").resolve()
    if (out / "tournament.json").exists():
        raise FileExistsError(f"Tournament results already exist at {out}; choose another --out")
    with tempfile.TemporaryDirectory(prefix="mbc-roster-") as tmp:
        if args.roster:
            roster_path = Path(args.roster).resolve()
        else:
            if len(args.bot) < 2:
                raise ValueError("Provide at least two --bot id=path options")
            bots = []
            seen = set()
            for entry in args.bot:
                key, sep, filename = entry.partition("=")
                if not sep or not SAFE_ID.fullmatch(key) or key in seen or not filename:
                    raise ValueError(f"Bad or duplicated --bot id=path: {entry}")
                seen.add(key)
                source = Path(filename).resolve()
                if source.suffix not in (".cpp", ".cc") or not source.is_file():
                    raise FileNotFoundError(f"Bot source not found: {source}")
                bots.append({"id": key, "source": str(source),
                             "kind": "human" if key == args.human else "ai"})
            if args.human and args.human not in seen:
                raise ValueError("--human must equal one of the bot IDs")
            roster = {"season": season.id,
                      "seed_count": args.seed_count or int(season.meta.get("default_seeds", 8)),
                      "bots": bots}
            if args.seed_master is not None:
                roster["seed_master"] = args.seed_master
            roster_path = Path(tmp) / "roster.json"
            roster_path.write_text(json.dumps(roster), encoding="utf-8")
        report = run_tournament(season, roster_path, out, timeout=args.timeout)
    if not args.no_publish:
        site = publish(season, out / "tournament.json", site_root / season.id)
        publish_hub(site_root)
        print("Published:", site / "index.html")
        print("Season archive:", site_root / "index.html")
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mbc", description="Mini Battlecode: reusable Human vs AI tournament engine")
    sp = ap.add_subparsers(dest="command", required=True)
    check = sp.add_parser("doctor", help="check Linux installation and season plugin")
    check.add_argument("--season", default="courier_s1")
    new = sp.add_parser("new-season", help="copy a draft season so an AI can replace its rules and interface")
    new.add_argument("id")
    new.add_argument("--from-season", default="courier_s1")
    b = sp.add_parser("build", help="compile a single .cpp/.cc bot")
    b.add_argument("--season", required=True)
    b.add_argument("--source", required=True)
    b.add_argument("--out", required=True)
    d = sp.add_parser("duel", help="compile two .cpp files and play a test match")
    d.add_argument("--season", required=True)
    d.add_argument("--blue", required=True, help="source .cpp/.cc")
    d.add_argument("--red", required=True, help="source .cpp/.cc")
    d.add_argument("--seed", type=int, default=7)
    d.add_argument("--replay")
    d.add_argument("--timeout", type=float, default=0.5)
    m = sp.add_parser("match", help="run one match of two already compiled executables")
    m.add_argument("--season", required=True)
    m.add_argument("--blue", required=True)
    m.add_argument("--red", required=True)
    m.add_argument("--seed", type=int, default=7)
    m.add_argument("--replay")
    m.add_argument("--timeout", type=float, default=0.5)
    t = sp.add_parser("tournament", help="run a full, fair paired round robin using a roster JSON")
    t.add_argument("--season", required=True)
    t.add_argument("--roster", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--timeout", type=float, default=0.5)
    f = sp.add_parser("finals", help="one-command tournament, ranking, replays and static website")
    f.add_argument("--season", required=True)
    f.add_argument("--bot", action="append", metavar="ID=FILE", help="repeat for each .cpp/.cc bot")
    f.add_argument("--roster", help="alternative roster.json (cannot combine with --bot)")
    f.add_argument("--human", help="bot ID belonging to the human player")
    f.add_argument("--seed-count", type=int)
    f.add_argument("--seed-master", type=int)
    f.add_argument("--out", help="tournament output folder (defaults to timestamped results)")
    f.add_argument("--site-root", default="published")
    f.add_argument("--timeout", type=float, default=0.5)
    f.add_argument("--no-publish", action="store_true")
    p = sp.add_parser("publish", help="export static results and all replays")
    p.add_argument("--season", required=True)
    p.add_argument("--results", required=True)
    p.add_argument("--out", required=True)
    hub = sp.add_parser("publish-hub", help="build a standalone index for every published season")
    hub.add_argument("--root", required=True)
    k = sp.add_parser("kit", help="package a single season for contestants")
    k.add_argument("--season", required=True)
    k.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    try:
        if args.command == "doctor":
            _doctor(args.season)
        elif args.command == "new-season":
            _init_season(args.id, args.from_season)
        elif args.command == "publish-hub":
            print("Season archive:", publish_hub(args.root))
        elif args.command == "duel":
            _duel(args)
        elif args.command == "finals":
            _finals(args)
        else:
            season = resolve_season(args.season)
            if args.command == "build":
                print(json.dumps(compile_cpp(args.source, season, args.out), indent=2))
            elif args.command == "match":
                if args.timeout <= 0:
                    raise ValueError("--timeout must be positive")
                players = [{"id": "blue", "label": Path(args.blue).stem, "binary": args.blue},
                           {"id": "red", "label": Path(args.red).stem, "binary": args.red}]
                print(json.dumps(run_match(season, players, args.seed, timeout=args.timeout,
                                           replay=args.replay), indent=2, ensure_ascii=False))
            elif args.command == "tournament":
                if args.timeout <= 0:
                    raise ValueError("--timeout must be positive")
                run_tournament(season, args.roster, args.out, timeout=args.timeout)
            elif args.command == "publish":
                print("Published:", publish(season, args.results, args.out))
            elif args.command == "kit":
                output = Path(args.out)
                output.parent.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
                    for field in ("header", "adapter", "viewer", "example", "rules", "judge"):
                        file = getattr(season, field)
                        z.write(file, file.name)
                    z.writestr("HOW_TO_BUILD.txt",
                               "Write a single .cpp/.cc file including arena.hpp.\n"
                               "Build: g++ -std=c++17 -O2 your_bot.cpp grader.cpp -o your_bot\n"
                               "Use the organiser's generic runner for local games.\n")
                print("Contestant kit:", output)
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError) as exc:
        ap.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
