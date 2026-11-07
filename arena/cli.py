"""Season-agnostic Linux CLI. Game contents always arrive as external ZIP/folder."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .core import SAFE_ID, compile_cpp, create_game, open_season, run_match
from .archive import contestant_kit, export_archive, season_package
from .tournament import run_tournament


def doctor(info=None):
    from sys import version_info
    print(f"Python {version_info.major}.{version_info.minor}, g++: {shutil.which('g++')}")
    if version_info < (3, 10) or not shutil.which('g++'):
        raise RuntimeError("Install Python >= 3.10 and g++ (sudo apt install python3 g++)")
    if info:
        game = create_game(info, 1)
        for team in (0, 1):
            obs = game.observe(team)
            if not isinstance(obs, str) or not obs.endswith('\n') or '\n' in obs[:-1]:
                raise RuntimeError("Season observation must be a single terminated line")
        json.dumps(game.snapshot())
        json.dumps(game.outcome())
        print(f"Season {info.id}: {game.max_turns} ticks; OK")
    print("Ready.")


def finals(info, args):
    if args.timeout <= 0:
        raise ValueError("Timeout must be positive")
    if bool(args.roster) == bool(args.bot):
        raise ValueError("Provide exactly one of --roster or repeated --bot id=path")
    if args.roster and (args.seed_count is not None or args.seed_master is not None or args.human):
        raise ValueError("When using --roster put seeds and kinds in roster JSON")
    tag = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    out = Path(args.out or f"results/{info.id}/{tag}").resolve()
    if (out / 'tournament.json').exists():
        raise FileExistsError("Tournament output already exists")
    with tempfile.TemporaryDirectory(prefix="mbc-roster-") as temp:
        if args.roster:
            roster = Path(args.roster).resolve()
        else:
            if len(args.bot) < 2:
                raise ValueError("At least two --bot arguments required")
            roster_bots, seen = [], set()
            for spec in args.bot:
                key, sep, filename = spec.partition('=')
                src = Path(filename).resolve()
                if (not sep or not SAFE_ID.fullmatch(key) or key in seen or
                    not src.is_file() or src.suffix not in ('.cpp', '.cc')):
                    raise ValueError(f"Bad or duplicate bot: {spec}")
                seen.add(key)
                roster_bots.append({"id": key, "source": str(src),
                                    "kind": "human" if key == args.human else "ai"})
            if args.human and args.human not in seen:
                raise ValueError("Unknown human bot id")
            payload = {"season": info.id, "bots": roster_bots,
                       "seed_count": args.seed_count or info.meta.get('default_seeds', 8)}
            if args.seed_master is not None:
                payload['seed_master'] = args.seed_master
            roster = Path(temp) / 'roster.json'
            roster.write_text(json.dumps(payload), encoding='utf-8')
        result = run_tournament(info, roster, out, timeout=args.timeout)
    archive = Path(args.archive).resolve() if args.archive else out / 'database_import.zip'
    export_archive(info, out / 'tournament.json', archive)
    print('Database import ZIP:', archive)
    print('Import on icaijy.com using: python manage.py import_battlecode', archive)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(prog='mbc', description='Mini Battlecode generic engine (no bundled seasons)')
    sp = ap.add_subparsers(dest='command', required=True)
    d = sp.add_parser('doctor', help='check installation, optionally validate a season ZIP')
    d.add_argument('--season')
    for cmd, helptext in (
        ('build', 'compile a single bot source'),
        ('duel', 'compile and play two sources'),
        ('match', 'run two pre-compiled executables'),
        ('finals', 'paired round robin and DB import ZIP'),
        ('tournament', 'run a roster file tournament'),
        ('kit', 'produce public contestant kit ZIP'),
        ('pack-season', 'produce full independent game ZIP'),
        ('export', 'export a completed tournament to DB ZIP'),
    ):
        q = sp.add_parser(cmd, help=helptext)
        q.add_argument('--season', required=True, help='external plugin directory or full ZIP')
        if cmd == 'build':
            q.add_argument('--source', required=True)
            q.add_argument('--out', required=True)
        elif cmd in ('duel', 'match'):
            q.add_argument('--blue', required=True)
            q.add_argument('--red', required=True)
            q.add_argument('--seed', type=int, default=7)
            q.add_argument('--timeout', type=float, default=0.5)
            q.add_argument('--replay')
        elif cmd == 'finals':
            q.add_argument('--bot', action='append', metavar='ID=FILE')
            q.add_argument('--roster')
            q.add_argument('--human')
            q.add_argument('--seed-count', type=int)
            q.add_argument('--seed-master', type=int)
            q.add_argument('--out')
            q.add_argument('--archive')
            q.add_argument('--timeout', type=float, default=0.5)
        elif cmd == 'tournament':
            q.add_argument('--roster', required=True)
            q.add_argument('--out', required=True)
            q.add_argument('--timeout', type=float, default=0.5)
        elif cmd in ('kit', 'pack-season'):
            q.add_argument('--out', required=True)
        elif cmd == 'export':
            q.add_argument('--results', required=True)
            q.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    try:
        if args.command == 'doctor' and not args.season:
            doctor()
            return
        with open_season(args.season) as info:
            if args.command == 'doctor':
                doctor(info)
            elif args.command == 'build':
                print(json.dumps(compile_cpp(args.source, info, args.out), indent=2))
            elif args.command in ('duel', 'match'):
                if args.timeout <= 0:
                    raise ValueError("Timeout must be positive")
                with tempfile.TemporaryDirectory(prefix='mbc-duel-') as temp:
                    if args.command == 'duel':
                        blue = compile_cpp(args.blue, info, Path(temp) / 'blue')['binary']
                        red = compile_cpp(args.red, info, Path(temp) / 'red')['binary']
                    else:
                        blue, red = args.blue, args.red
                    players = [{"id": "blue", "label": Path(args.blue).stem, "binary": blue},
                               {"id": "red", "label": Path(args.red).stem, "binary": red}]
                    replay = args.replay or f"results/{info.id}/duel.json"
                    result = run_match(info, players, args.seed, timeout=args.timeout, replay=replay)
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    print('Replay:', Path(replay).resolve())
            elif args.command == 'finals':
                finals(info, args)
            elif args.command == 'tournament':
                run_tournament(info, args.roster, args.out, timeout=args.timeout)
            elif args.command == 'kit':
                print('Contestant ZIP:', contestant_kit(info, args.out))
            elif args.command == 'pack-season':
                print('Full game ZIP:', season_package(info, args.out))
            elif args.command == 'export':
                print('Database import ZIP:', export_archive(info, args.results, args.out))
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError) as exc:
        ap.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
