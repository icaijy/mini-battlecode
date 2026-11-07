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

## Per-season workflow — **one ZIP, everyone uses it**

**Each game has exactly one `season.zip`**. Send the **same file** to the organiser, every competing AI and the human. It contains all public game files, the Python judge, C++ API, viewer, rules, and neutral AI prompt. There is no organiser/contestant package distinction.

1. Ask a game-designer AI to create an external season directory (never commit game-specific files to the engine repository). New games use `format_version: 2` and ship `game.py`, `arena.hpp`, `grader.cpp`, `viewer.html`, `example_bot.cpp`, plus three **short, bilingual, accessible** docs: `RULES.md`, `INTERFACE.md`, `AI_PROMPT.md`. Include `## 中文` and `## English` in all three. Keep the wording clear and a little funny, but avoid strategy hints. Follow [the season standard](docs/SEASON_STANDARD.md).

2. Validate and **package once**:

```bash
mbc doctor --season ~/games/s1
mbc pack-season --season ~/games/s1 --out ~/games/s1.zip
```

3. **Share that exact `s1.zip` with everyone.** Give each AI the identical `AI_PROMPT.md` text (preferably [the standard template](docs/AI_PROMPT_TEMPLATE.md)). For local editing, extract the same ZIP:

```bash
mkdir -p ~/games/play
unzip ~/games/s1.zip -d ~/games/play
```

Each participant writes **one** C++17 `.cpp/.cc` bot. Human time limit: 45 minutes; AI time limit: 10 minutes. Everyone has the same public materials and tests. Freeze source files before drawing official tournament seeds.

4. Test using the **same `s1.zip`**:

```bash
mbc duel --season ~/games/s1.zip --blue ~/bots/human.cpp \
  --red ~/games/play/example_bot.cpp --replay ~/games/test.json
```

5. **Run the finals (recommended):** put every participant's single `.cpp` or `.cc` file directly inside one folder:

```text
bots/
  human.cpp
  gpt.cpp
  claude.cpp
  gemini.cc
```

Run one command from any directory:

```bash
mbc finals --season ~/games/s1.zip --bots-dir ~/games/bots
```

The engine finds **every `.cpp/.cc` in that folder (non-recursive)**, compiles all of them, runs every pair on seeded maps with swapped sides, and prints a **compact wins/draws/losses table keyed by filename**. Full match details and every replay are still archived; there is no automatic video selection. Do not place the example/test bot in this folder unless you want it to compete. Optionally pass `--seed-count 8` to override the season's default number of seeds, or `--out ~/games/results/s1` to specify a result directory.

Legacy explicit `--bot id=path` and `--roster file.json` alternatives remain supported.

After the finals, the engine produces `database_import.zip`. **This is a results archive generated after the competition, not a second game ZIP**. Transfer it to the separately deployed `icaijy.com` Django server and import:

```bash
python manage.py migrate
python manage.py import_battlecode /path/to/database_import.zip
```

The website stores the results, rules, source snapshots and every replay in its database and exposes them at `/battlecode/`. First deployment requires updating the separate website repository and reloading Django; this engine never modifies the website.

**Backward compatibility:** `mbc kit` is retained as an alias for `mbc pack-season` and creates an **identical** ZIP. Use only `pack-season` in normal workflows.

## Contract

- `--season` accepts an **external directory or ZIP** (ZIP is safely extracted into a temporary directory for each command).
- `mbc doctor` without `--season` checks the installation. With `--season`, also checks the game plugin.
- `mbc build`, `duel`, `match`, `tournament`, `finals`, `pack-season`, `export` always use `--season`; legacy `kit` is a synonym for `pack-season`.
- Matches run in new native processes, one action line per tick. Invalid output and timeouts forfeit. Winner is determined by the game's Python `game.py` judge.
- Official standings: each pair plays every seed in both positions. Win 1 point / draw 0.5 / loss 0; ties use score difference then total score. For N bots and S seeds there are N(N−1)S games.
- Source files are snapshotted during the tournament; hashes, seeds, results and all replay JSONs go into the database import ZIP.
- The engine does **not** automatically highlight matches or write a static website. The organiser selects video clips manually from the website's complete match archive.
- New season `format_version: 2` packages require three bilingual documents; they are in the **single shared season ZIP** and the post-tournament database ZIP. Legacy v1 packages remain playable.
- This launcher is **not a security sandbox**. Only execute trusted C++ and Python code, or use an isolated VM/container.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Tests synthesise a disposable toy game in temporary storage. **No real season is bundled.**
