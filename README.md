# Mini Battlecode — generic engine only

[中文文档](README.zh-CN.md) · [Season plugin contract (English)](docs/SEASON_PROMPT_EN.md)

**The repository contains no concrete seasons, game rules, participant bots, replays or tournament results.** External, self-contained game ZIPs supply all season-specific code. The final results ZIP is imported into the **`icaijy.com` Django database**, not published as static pages by this engine.

## Install (Linux / WSL)

Requires Python 3.10+, g++ with C++17, no pip dependencies.

```bash
sudo apt install -y git python3 g++
git clone https://github.com/icaijy/mini-battlecode.git
cd mini-battlecode
./install.sh
mbc doctor
```

The launcher is installed in `~/.local/bin/mbc`. Add this directory to PATH if necessary. Keep the clone in place; update with `git pull`.

## Per-season workflow

1. Ask a **game-designer AI** to create an external directory containing `manifest.json`, `game.py`, `arena.hpp`, `grader.cpp`, `viewer.html`, `RULES.md`, `example_bot.cpp`. See [the season contract](docs/SEASON_PROMPT_EN.md). Never commit these to this engine repository.
2. Validate and package the organiser-only game:

```bash
mbc doctor --season ~/games/s1
mbc pack-season --season ~/games/s1 --out ~/games/s1.zip
```

3. Generate an identical public contestant ZIP for each participant (excludes the private `game.py` judge):

```bash
mbc kit --season ~/games/s1.zip --out ~/games/s1_players.zip
```

4. Each contestant writes **one** C++17 `.cpp/.cc` bot; the human has 45 minutes, each AI 10 minutes. Freeze all sources before choosing official seeds. Test locally:

```bash
mbc duel --season ~/games/s1.zip --blue ~/bots/human.cpp --red ~/games/s1/example_bot.cpp --replay ~/games/test.json
```

5. Official paired round robin (same seeds, swapped sides; **all** replays preserved, manual video selection):

```bash
mbc finals --season ~/games/s1.zip \
  --bot human=~/bots/human.cpp --bot gpt=~/bots/gpt.cpp \
  --bot claude=~/bots/claude.cpp --human human --seed-count 8 \
  --out ~/games/results/s1
```

The engine writes `tournament.json`, `replays/*.json`, `sources/*.cpp` and **`database_import.zip`**. The ZIP contains season sources (including the Python judge), viewer and rules, participant source snapshots, standings and every replay. Import the ZIP on the site server:

```bash
python manage.py migrate
python manage.py import_battlecode /path/to/database_import.zip
```

The website stores records **in the database** and exposes them at `/battlecode/`. On first deployment, update the separate website repository and reload its Django process. This engine repo never modifies the website.

## Contract

- `--season` accepts an **external directory or ZIP** (ZIP is safely extracted into a temporary directory for each command).
- `mbc doctor` without `--season` checks the installation. With `--season`, also checks the game plugin.
- `mbc build`, `duel`, `match`, `tournament`, `finals`, `kit`, `pack-season`, `export` always use `--season`.
- Matches run in new native processes, one action line per tick. Invalid output and timeouts forfeit. Winner is determined by the game's Python `game.py` judge.
- Official standings: each pair plays every seed in both positions. Win 1 point / draw 0.5 / loss 0; ties use score difference then total score. For N bots and S seeds there are N(N−1)S games.
- Source files are snapshotted during the tournament; hashes, seeds, results and all replay JSONs go into the database import ZIP.
- The engine does **not** automatically highlight matches or write a static website. The organiser selects video clips manually from the website's complete match archive.
- This launcher is **not a security sandbox**. Only execute trusted C++ and Python code, or use an isolated VM/container.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Tests synthesise a disposable toy game in temporary storage. **No real season is bundled.**
