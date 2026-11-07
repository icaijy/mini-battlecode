# 让 AI 为 Mini Battlecode 创建新一届游戏（可直接复制给 AI）

你负责设计与实现一个新赛季插件，不修改通用引擎。仓库是 `icaijy/mini-battlecode`。

新的赛季目录 `seasons/<season_id>/` 必须包含：

- `manifest.json`：赛事标识、描述、指向其他文件。
- `game.py`：**Python 权威裁判**，包含游戏规则、初始状态、每步行动、胜负判定；实现 `create_game(seed)` 返回对象，包含 `max_turns`, `turn`, `observe(team)`, `parse_action(team,line)`, `step([a,b])`, `snapshot()`, `outcome()`。
- `arena.hpp`：C++17 的状态、行动和 `tick()` 接口，**选手只写一份 `.cpp`/`.cc`**。
- `grader.cpp`：将裁判输入输出转为 `tick()` 调用的适配器；每回合收一行文本，返回一行行动；收到 `END` 退出；标准输出不得包含日志。
- `viewer.html`：该届独立的 HTML 回放可视化，能打开 JSON replay 并逐 tick 播放。
- `RULES.md`：中英双语规则（完整、无歧义）。
- `example_bot.cpp`：最简单的合法示例 bot，**不包含比赛策略**。

目标是容易在 10 分钟（AI）/45 分钟（人类）编写 bot 的简单游戏；有明显策略空间，但不存在强制的复杂算法模板。尽量让双方视角统一，并解释随机种子如何保证交换先后手公平。相同 seed 必须确定性产生相同初态和过程。

严格遵守通信规则：观察是 **一行以 `\\n` 结尾的 UTF-8 文本**；行动也必须是一行；`parse_action()` 验证不合法行动并抛出 `ValueError`；`snapshot()` 返回 JSON 可序列化 dict；`outcome()` 返回 `{"scores":[number,number],"winner":0|1|null}`。Python 游戏部分拥有最终解释权，不要在 C++ grader 中偷偷判分。

不要动 `arena/core.py`, `arena/tournament.py`, `arena/publish.py`。完成后用 `mbc doctor --season <season_id>`, `mbc duel --season <season_id> --blue ... --red ...` 测通，并在必要时增加赛季专用测试。

禁止生成私有参赛 bot 策略；不要预设正式决战的随机 seed。游戏规则在参赛开始前冻结。
