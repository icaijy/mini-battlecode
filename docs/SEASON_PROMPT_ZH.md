# Mini Battlecode · 给「游戏设计 AI」的任务 / Game designer prompt

> 本文件是设计新游戏用的。参赛 AI 收到的是每届自己独立的 `AI_PROMPT.md`，别搞混。

请为通用 Mini Battlecode 引擎创建**一届全新的游戏**。遵守 [每届规范 / Season standard](SEASON_STANDARD.md)。**不修改 `arena/`，不把游戏代码提交到引擎仓库**。全部文件输出在我指定的外部目录。

交付以下全部文件：

- `manifest.json`，包含 `id`、`title`、`version`、`default_seeds`、`format_version: 2`，以及文件字段 `judge:"game.py"`、`header:"arena.hpp"`、`adapter:"grader.cpp"`、`viewer:"viewer.html"`、`example:"example_bot.cpp"`、`rules:"RULES.md"`、`interface:"INTERFACE.md"`、`ai_prompt:"AI_PROMPT.md"`。
- `game.py`：Python 权威裁判。提供 `create_game(seed)`，返回具备 `max_turns`、`turn`、`observe(team)`、`parse_action(team,line)`、`step([a,b])`、`snapshot()`、`outcome()` 的对象。输入输出每回合各一行 UTF-8（以 `\n` 结尾），非法行动抛 `ValueError`；快照可 JSON 序列化，结局为 `{"scores":[x,y],"winner":0|1|null}`。相同 seed 确定性重现；双方同时行动并尽量公平对称。
- `arena.hpp`：C++17 状态、行动 API 与 `tick()` 声明，选手仅需写一份 `.cpp/.cc`。
- `grader.cpp`：解析一行观察，调用 `tick()`，向 stdout 输出一行行动，读到 `END` 退出。不要在 grader 偷偷算分；调试写 stderr。
- `viewer.html`：自包含 CSS/JS、无 CDN/HTTP fetch，支持本地 replay JSON 文件选择和播放/定位；在网站受限 iframe 中监听 `postMessage`：`{type:"mini-battlecode-replay",replay:{game,version,result,frames}}` 并播放。
- `example_bot.cpp`：只演示合法接口，**不能给出有竞争力的策略**。
- `RULES.md`：**中文 + English**，简短易懂。写清目的、回合、合法行动、胜负、边界；尽量一两屏读完，可以小幽默，不能遗漏影响比赛结果的规则。
- `INTERFACE.md`：**中文 + English**，只写需要的 API、`tick()`、重要结构体字段、动作、最小编译/测试示例；不要把游戏接口说明写成论文。
- `AI_PROMPT.md`：**中文 + English**，**所有参赛 AI 直接使用的统一中立提示词**。说明交一份 C++17 代码、限时 10 分钟（人类 45 分钟）、同一份参赛包及本地测试、截止冻结、不可参考其他 bot；**不能添加任何策略建议、模型专属说明或作弊暗示**。不替任何具体模型调教提示词。三份文档每个都要包含 `## 中文` 与 `## English`，两版信息一致。

游戏应满足 **10 分钟 AI / 45 分钟人类**能够实现基础 bot，但又有一些真正的 heuristic 空间；不要默认玩家懂复杂算法。所有规则必须确定、可测试，文档语气轻松一点，但严谨优先。

执行 `mbc doctor --season <目录或ZIP>`、一次 `mbc duel` 并用 `mbc pack-season`、`mbc kit` 检查三份双语文档包含在 ZIP 中。**比赛开始前冻结规则和接口；正式 seeds 在所有人交卷后才生成。**
