# Game designer contract for Mini Battlecode

Build **one external season plugin**. Do not edit the reusable `arena/` implementation and do not commit game-specific code to the engine repository. Produce an external directory containing `manifest.json`, `game.py`, `arena.hpp`, `grader.cpp`, `viewer.html`, `RULES.md` (English/Chinese) and a strategy-free `example_bot.cpp`.

Manifest fields: `id`, `title`, `version`, `judge`, `header`, `adapter`, `viewer`, `example`, `rules`, `default_seeds`. The source filenames should be the exact names above.

`game.py` must expose `create_game(seed)` returning an object with `max_turns`, `turn`, `observe(team)`, `parse_action(team,line)`, `step([a,b])`, `snapshot()`, `outcome()`. Observation and action are newline-terminated single-line UTF-8 messages. Invalid actions must throw `ValueError`. Snapshots are JSON-serialisable dictionaries. Outcome is `{"scores":[x,y],"winner":0|1|null}`. Gameplay must be deterministic for a fixed seed and should strive for side symmetry. The Python judge is authoritative.

A competitor writes **exactly one C++17 `.cpp` / `.cc` file**, implementing the `tick()` function declared in `arena.hpp`. The season-specific `grader.cpp` implements `main()`, streams observations to `tick()` and prints the move to stdout; it exits on `END` and reserves stderr for debugging.

**Viewer contract (mandatory for database-backed website):** the website embeds this standalone HTML in a sandboxed iframe and sends the replay with `postMessage`. Listen for:

```javascript
window.addEventListener('message', (event) => {
  if (event.data?.type === 'mini-battlecode-replay') {
    loadReplay(event.data.replay);
  }
});
```

The viewer must support a local JSON file picker, be fully self-contained (no CDN/HTTP fetch), and allow playback/seek. Replays have `{game, version, result, frames}`.

Aim for very simple rules but non-trivial heuristic strategy (AI development 10 minutes, human 45 minutes). Include a minimal valid bot only, not a tuned strategy. Do not preselect final seeds. Verify with `mbc doctor --season <path-or-zip>` and a smoke-test duel. Ship this plugin externally, not inside the generic engine repository.
