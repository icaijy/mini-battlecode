# Prompt for an AI creating a new Mini Battlecode season

Design one new season plugin in `seasons/<season_id>/` for `icaijy/mini-battlecode`. Do not modify the shared competition engine.

Files required:

- `manifest.json`: season name, version and filenames.
- `game.py`: **authoritative Python judge**, with `create_game(seed)` returning an object exposing `max_turns`, `turn`, `observe(team)`, `parse_action(team,line)`, `step([a,b])`, `snapshot()` and `outcome()`.
- `arena.hpp`: intuitive C++17 state/action/tick interface; contestants implement **only one `.cpp` or `.cc` file**.
- `grader.cpp`: one-line, newline-terminated stdin observations to C++ `tick()` calls, one-line stdout actions. Terminate when input is `END`; keep debug output off stdout.
- `viewer.html`: self-contained replay visualiser for that game, with a local JSON file picker and per-tick playback.
- `RULES.md`: full, unambiguous bilingual Chinese/English rules.
- `example_bot.cpp`: minimal valid demonstration, no strategically useful opponent bot.

A suitable game is easy for an AI to implement a first bot in 10 minutes and a human in 45 minutes, yet offers strategic choices. The same seed must produce deterministic initial states and transitions. Prefer symmetric views for both players. Explain swap-side fairness.

The observation and action are each **one newline-terminated UTF-8 line**. Validate illegal actions with `ValueError` from `parse_action()`. `snapshot()` must be JSON serialisable, and `outcome()` must return `{ "scores": [number,number], "winner": 0|1|null }`. C++ adapter must not award points; the Python judge is authoritative.

Do not edit `arena/core.py`, `arena/tournament.py`, or `arena/publish.py`. Smoke test via `mbc doctor --season <season_id>` and `mbc duel --season <season_id> --blue ... --red ...`. Freeze rules before development starts; do not disclose tournament seeds in advance.
