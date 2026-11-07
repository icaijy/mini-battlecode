# Mini Battlecode — reusable Human vs AI tournament engine

A small **standalone** competition engine. This repository is intentionally **not part of `icaijy.com`**. Any website integration should only consume a **static publication export**.

## The boundary

| Layer | Reused between seasons? | Responsibility |
|---|---|---|
| `arena/core.py` | Yes | Compile a single C++ source, launch subprocesses, enforce response timeouts, run the game, save replays |
| `arena/tournament.py` | Yes | Frozen seeded paired round robin, official ranking, shortlist of interesting matches |
| `arena/publish.py` | Yes | Export leaderboards and selected replays to a static microsite |
| `seasons/SEASON/game.py` | **No** | Actual rules / state / observations / valid actions / scoring, authoritative Python judge |
| `seasons/SEASON/arena.hpp` | **No** | Season-specific C++ API for bots |
| `seasons/SEASON/grader.cpp` | **No** | Season-specific C++ wire adapter; not responsible for scoring |
| `seasons/SEASON/viewer.html` | **No** | Season-specific visualiser (local file picker and hosted replay links) |
| `seasons/SEASON/RULES.md` | **No** | Public rules |
| `bots/*.cpp` or `.cc` | Every participant | **ONE C++ source file per bot**; no additional libraries beyond standard C++ |

**Important:** New gameplay requires a new Python judge **and** an associated C++ grader/header. Only replacing `grader.cpp` cannot change game rules: the Python judge is what executes turns and awards points. The *generic runner*, tournament format and publication format stay unchanged.

## Get started — Linux / WSL / macOS

Requirements: Python 3.10+, `g++` with C++17, standard libraries only. No pip installs.

```bash
# Test engine and Courier Clash plugin
python3 -m unittest discover -s tests -v

# Build one bot file (your file includes season's arena.hpp)
python3 -m arena build --season courier_s1 --source seasons/courier_s1/example_bot.cpp --out .build/example

# Run a match, and open the replay using seasons/courier_s1/viewer.html
python3 -m arena match --season courier_s1 --blue .build/example --red .build/example --seed 7 --replay results/demo.json

# Full paired round-robin tournament with source files from roster.json
python3 -m arena tournament --season courier_s1 --roster bots/roster.example.json --out results/demo --features 8

# Generate static results webpage; it does not deploy anywhere
python3 -m arena publish --season courier_s1 --results results/demo/tournament.json --out published/courier_s1
python3 -m arena publish-hub --root published

# Generate identical, small per-season contestant kit
python3 -m arena kit --season courier_s1 --out kits/courier_s1.zip
```

Open `published/index.html` for the multi-season archive and `published/courier_s1/index.html` for the standings; select a replay manually if opened as `file://`, or run `python3 -m http.server 8000 --directory published/courier_s1` to use featured replay links at `http://localhost:8000/`.

## How a tournament works

Every pair of bots competes on **the same seeded maps in both player positions**. Official result = entire round robin; points: win 1, draw 0.5, loss 0. Ties sorted by score difference, then total score; identical results get the same rank. Each match starts a fresh bot process. Compile artefacts and SHA-256 hashes of source, binary, judge and adapter are retained in `results/.../tournament.json`.

For `N` bots and `S` seeds per pair, **number of matches = N(N−1)S** (each unordered pair has two games per seed). Example: 6 bots × 12 seeds = 360 games. Do not choose seeds or change the rules after seeing opponents. `roster.json` can specify `seeds` explicitly, or choose `seed_count`. If no explicit `seed_master` is given, a fresh cryptographically random master is chosen at tournament launch, **after the bots have been submitted**, and the exact generated seed list is saved in `tournament.json` for reproducibility. Please freeze your own and AI bot source at the development deadline. The time limit refers to development, not to the total tournament runtime.

**Video format:** `arena/tournament.py` selects representative matches *after* the competition — close games, surprise results, high combined scores, leaders head-to-head and some human matches. These labels affect **only the video selection**, never the champion. A top-four knockout can be a *showmatch*, not the official championship. This avoids the unfairness of a single-elimination bracket while retaining exciting footage.

## Static website publishing

`arena publish` outputs:

```text
published/
  index.html      # automatically generated archive across every season
  seasons.json    # machine-readable season index
  courier_s1/
  index.html      # official final leaderboard, shareable landing page
  results.json    # machine-readable ranking and featured-match metadata
  matches.json    # full match-level score/winner audit log
  viewer.html     # season-specific viewer, never a generic viewer
  replays/        # only selected featured replays
  RULES.md
```

Copy these **static files only** to a website or GitHub Pages; never copy the Python engine, bot executables or development tooling into the website. `icaijy.com` can later host or link to this output, but **this repository never writes to `icaijy.com`**.

The full `results/demo/replays/` folder contains **all matches** for auditing and further video edits. It can be large; published microsites only include selected matches. For video, record the full event, display standings, show 2–5 annotated featured replays, then explain representative algorithmic decisions. Avoid presenting showmatch wins as the official title.

## Fairness and security

- Identical documentation / engine / start kit for all participants; fixed model versions and prompts are recommended.
- Human gets 45 minutes to write the bot, each AI 10 minutes, measured from implementation start. No access to other bots before submission. Freeze sources / hashes before choosing seeds.
- A bot only needs to implement the season-specific `tick()` defined in `arena.hpp`. `grader.cpp` implements stdin/stdout. `stderr` debug output is ignored by the runner.
- Invalid output, EOF and per-turn timeout produce a **forfeit**. If both players forfeit on the same turn, it is a draw. The engine preserves the offending tick and reason.
- **Trust boundary:** This runner launches native compiled code and is **not a secure sandbox**. Run only your own or trusted AI-generated binaries in a disposable container/VM if they might be untrusted. `timeout` and output-size limits are not filesystem/network isolation.
- Ensure your public replay doesn't contain prompt secrets, tokens or personal account data.

## Adding Season 2

1. Copy `seasons/courier_s1/` to `seasons/new_name/` and change the manifest ID.
2. Replace `game.py` with the new rules and implement `create_game(seed)` returning an object with `max_turns`, `turn`, `observe(team)`, `parse_action(team,line)`, `step([a,b])`, `snapshot()`, and `outcome()` with `{scores:[x,y],winner:0|1|None}`.
3. Replace `arena.hpp`, `grader.cpp`, `viewer.html` and `RULES.md`. Keep `grader.cpp` communicating in single newline-terminated text lines and accepting `END` on shutdown.
4. Add engine-level tests for deterministic seeds, both-side fairness, valid actions and end conditions. **No edits to `arena/*.py` should be necessary.**
5. Use the same commands with `--season new_name`. Export `published/new_name` as a separate season microsite.

The first prototype is Courier Clash S1; no strategy-specific bot code is included.
