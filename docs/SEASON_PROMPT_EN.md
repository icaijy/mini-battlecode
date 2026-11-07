# Mini Battlecode · Game-designer AI brief / 游戏设计任务

> This prompt is for the **game-designer AI**, not the competing bots. Competing AIs get each season's separate `AI_PROMPT.md`.

Create **one new, external season plugin** for Mini Battlecode. Follow the [permanent season standard](SEASON_STANDARD.md). Do **not** edit `arena/` or commit any game code to the generic engine repository.

Deliver every file below:

- `manifest.json` with `id`, `title`, `version`, `default_seeds`, `format_version: 2`, and `judge:"game.py"`, `header:"arena.hpp"`, `adapter:"grader.cpp"`, `viewer:"viewer.html"`, `example:"example_bot.cpp"`, `rules:"RULES.md"`, `interface:"INTERFACE.md"`, `ai_prompt:"AI_PROMPT.md"`.
- `game.py`: authoritative Python judge. `create_game(seed)` returns a game with `max_turns`, `turn`, `observe(team)`, `parse_action(team,line)`, `step([a,b])`, `snapshot()`, `outcome()`. Observations/actions are one newline-terminated UTF-8 line each turn. Reject invalid actions with `ValueError`, return JSON-serialisable snapshots and `{"scores":[x,y],"winner":0|1|null}` outcomes. Identical seeds must reproduce the game; apply both players' decisions simultaneously and aim for side fairness.
- `arena.hpp`: C++17 state/action API with the bot's `tick()` declaration. Each competitor writes exactly one `.cpp/.cc`.
- `grader.cpp`: read one observation line, call `tick()`, write one action line to stdout, stop on `END`. Python handles scoring; stderr is for diagnostics.
- `viewer.html`: completely self-contained (no CDN or fetch). Support a local replay JSON file picker, play/seek, and website sandboxed iframe `postMessage` with `{type:"mini-battlecode-replay",replay:{game,version,result,frames}}`.
- `example_bot.cpp`: minimal valid API example **without competitive strategy**.
- `RULES.md`: **中文 + English**, a clear, short game explanation: goal, turn order, actions, scoring/win conditions and relevant edge cases. Aim for one or two screens, with light humour but zero ambiguity.
- `INTERFACE.md`: **中文 + English**, short `tick()`/state/action API guide including field meanings and a tiny build/test example. Not an API dissertation.
- `AI_PROMPT.md`: **中文 + English**, one **identical neutral contestant prompt** for every AI. Prefer copying [the standard template](AI_PROMPT_TEMPLATE.md) verbatim. It should request one C++17 source file, permit identical public season ZIP/tests, set AI coding time to 10 minutes (human 45 minutes), forbid looking at other bots, and freeze code at the deadline. **No strategy hints, model-specific instructions or secret seeds.** All three Markdown files must contain `## 中文` and `## English` with equivalent content.

Design simple rules and meaningful heuristic trade-offs. A basic bot should be achievable in the contest's time limits without pre-existing niche knowledge. Keep all consequential rules precise and testable, and the prose approachable.

Run `mbc doctor --season <folder-or-zip>`, a smoke-test `mbc duel`, then run `mbc pack-season` **once**, send the **same resulting season ZIP** to every participant, and verify the three bilingual documents are present. **Freeze rules/interfaces before coding begins; create official seeds only after every submission is frozen.**
