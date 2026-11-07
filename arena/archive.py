"""Produce the portable result ZIP consumed by icaijy.com's database importer."""
from __future__ import annotations

import json
import hashlib
import zipfile
from pathlib import Path

from .core import SeasonInfo, sha256

PLUGIN_FILES = ("judge", "header", "adapter", "viewer", "example", "rules")


def export_archive(info: SeasonInfo, report_path: str | Path,
                   out: str | Path) -> Path:
    source = Path(report_path).resolve()
    report = json.loads(source.read_text(encoding="utf-8"))
    if report.get("season") != info.id or report.get("schema") != 1:
        raise ValueError("Tournament report does not match the season")
    matches = report.get("matches")
    if not isinstance(matches, list) or report.get("matches_total") != len(matches):
        raise ValueError("Tournament match count mismatch")
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite an archive: {out}")
    with zipfile.ZipFile(out, "x", zipfile.ZIP_DEFLATED, compresslevel=7) as z:
        z.write(source, "tournament.json")
        z.write(info.path / "manifest.json", "season/manifest.json")
        for field in PLUGIN_FILES:
            src = getattr(info, field)
            z.write(src, "season/" + src.name)
        seen = set()
        for match in matches:
            ix = match.get("index")
            rel = match.get("replay")
            if type(ix) is not int or ix in seen or rel != f"replays/match_{ix:04d}.json":
                raise ValueError("Invalid replay reference")
            seen.add(ix)
            replay = source.parent / rel
            if not replay.is_file() or replay.stat().st_size > 5 * 1024 * 1024:
                raise ValueError(f"Missing or oversized replay: {rel}")
            z.write(replay, rel)
        for bot in report.get("participants", []):
            # Optional source preservation after the submission deadline.
            key = bot["id"]
            src = source.parent / "sources" / (key + ".cpp")
            if src.exists() and src.is_file() and src.stat().st_size < 500_000:
                z.write(src, "sources/" + key + ".cpp")
    return out


def season_package(info: SeasonInfo, out: str | Path) -> Path:
    """A reusable full game plugin ZIP; do not commit it to engine repository."""
    output = Path(out).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as z:
        z.write(info.path / "manifest.json", "manifest.json")
        for field in PLUGIN_FILES:
            src = getattr(info, field)
            z.write(src, src.name)
    return output


def contestant_kit(info: SeasonInfo, out: str | Path) -> Path:
    """Identical public contest ZIP, including rules and judge for local testing."""
    output = Path(out).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as z:
        z.write(info.path / "manifest.json", "manifest.json")
        for field in PLUGIN_FILES:
            src = getattr(info, field)
            z.write(src, src.name)
        z.writestr("HOW_TO_BUILD.txt", "Write ONE .cpp/.cc file; implement tick() in arena.hpp.\n"
                   "Compile: g++ -std=c++17 -O2 bot.cpp grader.cpp -o bot\n"
                   "Build/test under the organiser's full season ZIP.\n")
    return output
