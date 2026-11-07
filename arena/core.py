"""Game-independent bot process control, compilation and match execution.

WARNING: trusted local bot binaries only. This is NOT an OS security sandbox.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import select
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,60}$")
MAX_LINE_BYTES = 16384


class BotFault(RuntimeError):
    pass


class SeasonError(ValueError):
    pass


@dataclass(frozen=True)
class SeasonInfo:
    path: Path
    meta: dict
    judge: Path
    header: Path
    adapter: Path
    viewer: Path
    example: Path
    rules: Path

    @property
    def id(self) -> str:
        return self.meta["id"]


def resolve_season(value: str | Path) -> SeasonInfo:
    path = Path(value)
    if not path.is_dir():
        path = ROOT / "seasons" / str(value)
    path = path.resolve()
    manifest = path / "manifest.json"
    if not manifest.is_file():
        raise SeasonError(f"Season manifest not found: {manifest}")
    meta = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(meta, dict) or not SAFE_ID.fullmatch(str(meta.get("id", ""))):
        raise SeasonError("Season manifest needs a safe id")
    required = ("judge", "header", "adapter", "viewer", "example", "rules")
    files = {}
    for key in required:
        name = meta.get(key)
        if not isinstance(name, str) or Path(name).name != name:
            raise SeasonError(f"Invalid manifest path: {key}")
        candidate = path / name
        if not candidate.is_file():
            raise SeasonError(f"Missing season file {candidate}")
        files[key] = candidate
    return SeasonInfo(path, meta, **files)


def create_game(info: SeasonInfo, seed: int):
    # Isolated import name, allowing later seasons without a common game schema.
    module_name = f"_minibattlecode_{info.id}"
    spec = importlib.util.spec_from_file_location(module_name, info.judge)
    if not spec or not spec.loader:
        raise SeasonError(f"Cannot load season judge: {info.judge}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    game = module.create_game(seed)
    for attr in ("max_turns", "turn", "observe", "parse_action", "step", "snapshot", "outcome"):
        if not hasattr(game, attr):
            raise SeasonError(f"Season judge is missing {attr}")
    if not isinstance(game.max_turns, int) or not 1 <= game.max_turns <= 10000:
        raise SeasonError("max_turns must be an integer in 1..10000")
    return game


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def compile_cpp(source: str | Path, info: SeasonInfo, output: str | Path,
                *, compiler: str = "g++", timeout: float = 45.0) -> dict:
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_file() or source.suffix.lower() not in (".cpp", ".cc"):
        raise ValueError(f"Bot must be one existing .cpp/.cc file: {source}")
    if shutil.which(compiler) is None:
        raise RuntimeError(f"C++ compiler not found: {compiler}; use g++ inside WSL")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [compiler, "-std=c++17", "-O2", "-pipe", "-I", str(info.path),
               str(source), str(info.adapter), "-o", str(output)]
    try:
        cp = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Compilation took more than {timeout}s") from exc
    if cp.returncode:
        raise RuntimeError(f"Compilation failed for {source.name}:\n{cp.stderr[-6000:]}")
    return {"source": str(source), "binary": str(output),
            "source_sha256": sha256(source), "binary_sha256": sha256(output),
            "compiler": compiler, "compiler_args": command[1:-2]}


class BotProcess:
    """Persistent subprocess with bounded line reads, one request/response per tick."""
    def __init__(self, binary: str | Path, name: str):
        path = Path(binary).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Bot not built: {path}")
        self.name = name
        self.proc = subprocess.Popen([str(path)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     bufsize=0)
        self.buffer = bytearray()

    def query(self, observation: str, timeout: float) -> str:
        if not isinstance(observation, str) or not observation.endswith("\n") or "\n" in observation[:-1]:
            raise SeasonError("Observation must be exactly one newline-terminated line")
        if self.proc.poll() is not None:
            raise BotFault(f"{self.name}: exited with {self.proc.returncode}")
        try:
            self.proc.stdin.write(observation.encode("utf-8"))
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise BotFault(f"{self.name}: cannot receive observation") from exc
        deadline = time.monotonic() + timeout
        fd = self.proc.stdout.fileno()
        while True:
            end = self.buffer.find(b"\n")
            if end >= 0:
                if end > MAX_LINE_BYTES:
                    raise BotFault(f"{self.name}: output line too long")
                line = bytes(self.buffer[:end])
                del self.buffer[:end + 1]
                try:
                    return line.decode("utf-8", errors="strict")
                except UnicodeDecodeError as exc:
                    raise BotFault(f"{self.name}: invalid UTF-8 output") from exc
            if len(self.buffer) > MAX_LINE_BYTES:
                raise BotFault(f"{self.name}: output line too long")
            remain = deadline - time.monotonic()
            if remain <= 0:
                raise BotFault(f"{self.name}: response exceeded {timeout:.3f}s")
            readable, _, _ = select.select([fd], [], [], remain)
            if not readable:
                raise BotFault(f"{self.name}: response exceeded {timeout:.3f}s")
            chunk = os.read(fd, 4096)
            if not chunk:
                raise BotFault(f"{self.name}: EOF before action")
            self.buffer.extend(chunk)

    def close(self):
        if self.proc.poll() is None:
            try:
                self.proc.stdin.write(b"END\n")
                self.proc.stdin.flush()
                self.proc.wait(timeout=0.12)
            except (BrokenPipeError, OSError, subprocess.TimeoutExpired):
                if self.proc.poll() is None:
                    self.proc.terminate()
                try:
                    self.proc.wait(timeout=0.3)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait()
        for stream in (self.proc.stdin, self.proc.stdout):
            if stream:
                stream.close()


def run_match(info: SeasonInfo, players: list[dict], seed: int,
              *, timeout: float = 0.5, replay: str | Path | None = None) -> dict:
    """A fresh process for each player. No season-specific rules in here."""
    if len(players) != 2 or players[0]["id"] == players[1]["id"]:
        raise ValueError("Need exactly two distinct bots")
    game = create_game(info, seed)
    frames = [game.snapshot()] if replay else None
    errors = []
    bots = []
    start = time.monotonic()
    try:
        for player in players:
            bots.append(BotProcess(player["binary"], player["id"]))
        for expected_turn in range(game.max_turns):
            if game.turn != expected_turn:
                raise SeasonError("Judge turn counter drifted")
            # One immutable pre-turn state per side, applying neither action yet.
            observations = [game.observe(side) for side in range(2)]
            actions = []
            for side in range(2):
                try:
                    line = bots[side].query(observations[side], timeout)
                    actions.append(game.parse_action(side, line))
                except (BotFault, ValueError) as exc:
                    errors.append({"player": side, "turn": game.turn,
                                   "reason": str(exc)[:300]})
                    actions.append(None)
            if errors:
                break
            game.step(actions)
            if frames is not None:
                frame = game.snapshot()
                frame["actions"] = actions
                frames.append(frame)
    finally:
        for bot in bots:
            bot.close()
    outcome = game.outcome()
    winner = outcome["winner"]
    if errors:
        failed = {error["player"] for error in errors}
        winner = None if len(failed) == 2 else 1 - next(iter(failed))
    if winner is not None and winner not in (0, 1):
        raise SeasonError("Winner must be 0, 1 or null")
    result = {"season": info.id, "version": info.meta.get("version"),
              "seed": int(seed), "bot_ids": [player["id"] for player in players],
              "bot_names": [player.get("label", player["id"]) for player in players],
              "scores": list(outcome["scores"]), "winner": winner,
              "errors": errors, "turns_played": game.turn,
              "elapsed_seconds": round(time.monotonic() - start, 3)}
    if replay is not None:
        replay = Path(replay)
        replay.parent.mkdir(parents=True, exist_ok=True)
        replay.write_text(json.dumps({"game": info.meta["title"], "version": 1,
                                      "result": result, "frames": frames},
                                     separators=(",", ":")) + "\n", encoding="utf-8")
        result["replay"] = str(replay)
    return result
