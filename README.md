# Mini Battlecode — generic engine only

[中文文档](README.zh-CN.md) · [Bilingual season standard](docs/SEASON_STANDARD.md) · [Game designer brief](docs/SEASON_PROMPT_EN.md) · [Identical AI contestant prompt](docs/AI_PROMPT_TEMPLATE.md)

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

1. Ask a **game-designer AI** to create an external season (never in this engine repo). The new `manifest.json` uses **`format_version: 2`**. Alongside `game.py`, `arena.hpp`, `grader.cpp`, `viewer.html` and `example_bot.cpp`, it **must** contain three short Markdown documents: bilingual `RULES.md` (game rules), `INTERFACE.md` (C++ API quick-start), and `AI_PROMPT.md` (same neutral instructions for every competing AI). Both languages use the headings `## 中文` and `## English` and convey equivalent information. Aim for readable, slightly funny wording—not a dissertation. See [the permanent standard](docs/SEASON_STANDARD.md) and [the game-designer brief](docs/SEASON_PROMPT_EN.md).
2. Validate and package the organiser-only game:

```bash
mbc doctor --season ~/games/s1
mbc pack-season --season ~/games/s1 --out ~/games/s1.zip
```

3. Generate an identical public contestant ZIP for each participant (including the same publicly inspectable `game.py` judge and all three bilingual docs). **Send every AI the exact same ZIP and `AI_PROMPT.md`, preferably copied verbatim from [the standard template](docs/AI_PROMPT_TEMPLATE.md)**; no model-specific strategy hints:

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
- New season `format_version: 2` packages require the three bilingual documents and include them in the full ZIP, contestant ZIP and final database ZIP. Legacy v1 packages remain playable.
- This launcher is **not a security sandbox**. Only execute trusted C++ and Python code, or use an isolated VM/container.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Tests synthesise a disposable toy game in temporary storage. **No real season is bundled.**
