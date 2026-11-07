# Courier Clash — Season 1 (v1.0)

A tiny two-player Battlecode-style tournament for **C++17** bots. Two teams of four delivery robots compete to transport resource packets from wells back to their own base. Rules and interfaces are intentionally small; finding a winning heuristic is the challenge.

**Competition rule:** Everyone receives the *same* ZIP. The organiser freezes this version before development begins. The sample bot illustrates the API only: it contains **no reference strategy**. AI bots get 10 minutes of actual implementation time; the human bot gets 45 minutes. No outside strategies or existing code snippets during the timer (standard library, game documentation and permitted compiler/debug tools are fine). All bot code and executable hashes should be frozen at the deadline. Use fresh processes for each match, and use paired seeds with swapped sides for fair comparison.


## Rules

- **Board:** 13×13, coordinates `(x,y)` from `(0,0)` at the bottom-left to `(12,12)` at the top-right. No walls. Team Blue's base is `(0,0)` and Team Red's is `(12,12)`.
- **Drones:** 4 per team, IDs 0..3. All start at their team's base. Multiple friendly drones may occupy the same cell. Both teams submit all 4 actions *simultaneously* every tick.
- **Moves:** `STAY`, `UP`, `RIGHT`, `DOWN`, `LEFT` (one tile, or stay). Moving off the board keeps the drone inside the boundary. A head-on swap (crossing each other along an edge) is **not** a collision.
- **Collision:** After all movement, if *at least one* robot from each team ends on the same tile, **every** robot of both teams on that tile crashes. They instantly return to their own base and lose any unbanked cargo. Crashed drones do not harvest or deposit on that tick.
- **Harvest:** There are **seven stationary resource wells**. Each well has `value` (points per packet), `period` (ticks between replenishments), `stock` (available packets), and `phase` (public recharge offset). After collision and deposit resolution, a drone standing on a well automatically collects **one** packet if it has room and the well has stock. Every drone carries at most **5 packets**, but the packets may have different point values. At most **one packet is collected from each well per tick**; if several friendly drones share that well, the lowest drone ID collects it. (Opposing drones would have crashed.)
- **Deposit:** After collisions and before harvest, a surviving robot ending on **its own base** delivers all its packets automatically, adding their combined `cargo_value` to the team score. It then carries zero.
- **Regeneration:** Each well generates one packet every `period` ticks, up to stock 5. Replenishment happens **after** harvesting each tick. Initial stock and recharge phase vary by seed, but the map is always 180° rotationally symmetric. All well data, including the regeneration phase, is public. After tick `t` finishes (tick numbers start at 0), replenishment occurs if `(t + 1 + phase) % period == 0`.
- **Finish:** 140 ticks. Highest *banked* score wins. Undelivered cargo gives no points. Equal banked scores = draw. A bot that crashes, exits unexpectedly, produces invalid output or exceeds 0.5 s on a tick **forfeits**.

The 7 wells are symmetrical; their world-coordinate `(x,y,value,period)` entries are:

| x | y | value | period |
|---:|---:|---:|---:|
| 2 | 3 | 1 | 1 |
| 3 | 2 | 1 | 1 |
| 10 | 9 | 1 | 1 |
| 9 | 10 | 1 | 1 |
| 4 | 8 | 3 | 3 |
| 8 | 4 | 3 | 3 |
| 6 | 6 | 5 | 5 |

There are **no hidden rules** and no random events during the match after the seed's initial stocks/phases are determined.

## C++ Bot Interface

You receive an identical kit consisting of `arena.hpp`, `grader.cpp`, `example_bot.cpp`, `game.py`, `viewer.html`, and these rules. `example_bot.cpp` only demonstrates the API, **not a strategy**.

```cpp
#include "arena.hpp"
using namespace courier;
void courier::tick(const State& s) {
    for (int i = 0; i < DRONES; ++i) move(i, STAY);
}
```

- Use **one C++17 `.cpp/.cc` source file** for your bot. Include `arena.hpp`.
- The `State` argument exposes own/enemy robot positions and cargo, scores, and all resource wells.
- Both players always see their own base at `(0,0)` thanks to 180° perspective rotation. Input wells appear sorted by local coordinates.
- Each bot sends one action per robot: `STAY`, `UP`, `RIGHT`, `DOWN`, `LEFT`. Unset actions default to `STAY`.
- Bot processes persist across ticks, allowing ordinary in-memory state, and restart for each match.
- Print debugging data to `stderr`, not `stdout` (the adapter owns stdout).

Build using:

```bash
g++ -std=c++17 -O2 your_bot.cpp grader.cpp -o your_bot
```

The organiser supplies the generic Mini Battlecode runner. It runs both executables, enforces a response deadline, and writes JSON replays. `viewer.html` can load a local replay JSON. `game.py` is the authoritative rules implementation; do not modify any of the supplied kit files.

## Fair play

Human 45 minutes vs AI 10 minutes is a **game format**, not a scientifically fair comparison of capabilities. Everyone receives the same rules and interfaces; no accessing other submissions during implementation. After source submission deadlines the organiser freezes each file, chooses tournament seeds and runs a paired round robin (every pair plays both sides on identical seeds). Official ranking is based on the full round robin. Featured games are for video only.

---

## 中文规则 / Chinese rules

**Courier Clash 第一届**：每队 4 个运输机器人，在 13×13 地图上采集资源并运回自己的基地。每局 140 tick，以**已运回基地的总积分**决定胜负；未运回的货物不计分。

- **地图与视角**：坐标为 `(0,0)` 到 `(12,12)`，没有墙。蓝队基地 `(0,0)`，红队基地 `(12,12)`；红队看到的坐标会旋转 180 度，所以**每个 bot 都认为自己在 `(0,0)`**。
- **机器人**：每队 4 个，编号 0–3。同队可以叠在同一格；每回合同时提交全部 4 个动作。
- **移动**：`STAY/UP/RIGHT/DOWN/LEFT`，每回合移动一格或不动；越界会停在边界。两队在一条边上迎面交换位置**不算碰撞**。
- **撞车**：双方至少各一个机器人走到同一格时，该格所有双方机器人都立即回到各自基地，并丢失全部**未存入基地**的货物。本回合撞车机器人不能采集或存货。
- **采集**：共 7 个固定资源井。每个资源井的每包积分为 `value`，补货周期 `period`，当前库存 `stock`，周期偏移 `phase`。机器人站在资源井上时自动采集一包。每个机器人最多携带 5 包，不同包可以具有不同积分；每口井每回合最多被采走 1 包，同队多个机器人同格时 ID 最小者先采。双方在同井会先撞车。
- **存货**：碰撞结算后、采集前，活着的机器人回到自己的基地就自动把全部货物存入积分并清空货物。
- **补货**：采集之后，每口井按自己的周期补 1 包，库存上限 5。种子决定初始库存和相位，保证 180 度旋转对称；所有信息均公开。结束第 `t` 回合（从 0 开始）时，若 `(t+1+phase)%period==0` 则补货。
- **胜负**：140 回合后比较存入基地的积分，相等平局。bot 崩溃、非法输出、超时或提前退出，直接判负（双方同时违规为平局）。

七口井的固定 `(x,y,value,period)` 在上方英文表格完整列出。初始随机值完全由 seed 决定，比赛开始后没有额外隐藏随机事件。Python `game.py` 是权威判定，C++ `grader.cpp` 只负责通信。

**选手提交规则**：只交一份 C++17 `.cpp/.cc`，包含 `arena.hpp` 并实现 `void courier::tick(const State&)`，通过 `move(drone_id,direction)` 设置 4 个机器人的行动；不调用 `move` 默认 `STAY`。所有日志写 `stderr`，不能直接写 `stdout`。选手不得更改游戏 SDK 或裁判。每个 AI 10 分钟，人类 45 分钟，参赛期间互不参考已有策略，交卷后冻结代码；完整双边循环赛才决定正式冠军，精选视频不影响战绩。
