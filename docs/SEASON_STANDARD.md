# Mini Battlecode · Season package standard / 每届游戏包规范

This is the **permanent contract for NEW seasons**. It is not a game or a bot.
这是**未来每一届**必须遵守的规范，不是某届游戏的题解。

## 中文

### 交付什么

每届游戏放在引擎仓库**外**，最终只打包成**一个**独立的 `season.zip`。这同一个 ZIP 同时发给主办方、人类和所有 AI，不再生成第二份「选手包」。文件清单：

| 文件 | 用途 |
|---|---|
| `manifest.json` | 标识本届；必须设 `"format_version": 2` |
| `game.py` | Python 权威裁判 |
| `arena.hpp`、`grader.cpp` | C++ 接口与通信适配器 |
| `viewer.html` | 独立 replay 播放器 |
| `example_bot.cpp` | **只演示合法接口**，不写强策略 |
| `RULES.md` | **面向选手的规则速读**，中英双语 |
| `INTERFACE.md` | **面向选手的 C++ API 速读**，中英双语 |
| `AI_PROMPT.md` | **所有参赛 AI 收到的完全相同的提示词**，中英双语 |

`manifest.json` 除旧有 `judge`、`header`、`adapter`、`viewer`、`example`、`rules` 外，新增：

```json
{
  "format_version": 2,
  "interface": "INTERFACE.md",
  "ai_prompt": "AI_PROMPT.md"
}
```

### 写文档的原则

- 三个 Markdown 文件都必须有 **`## 中文` 和 `## English`** 两部分；**两版信息完全一致**，不能中文少规则、英文多提示。
- **简单、好读、略搞笑**。先一句话说清游戏目的，再说地图/角色、每回合能干啥、胜负/得分、边界规则。接口文档写清 `tick()`、结构体字段、动作 API、编译测试命令和一个*不带策略*的小例子。
- 规则文档尽量**一两屏读完**。没必要写论文、实现细节和算法课；但影响胜负的规则、异常行为及平局判定**一个都别漏**。复杂点放简短表格或 FAQ。
- 幽默可以点缀句子，**不能用笑话代替确定性规则**。术语、坐标、单位、先后顺序、数据范围必须无歧义。
- 不给选手送策略答案：三份文档都不应暗示推荐路线、收益函数、战术或最优 heuristic。

### 公平的 AI 提示词

`AI_PROMPT.md` 只解释**任务和统一限制**：参赛者是 AI，要从相同的公开赛季包中写**一份 C++17 `.cpp/.cc` bot**，实现头文件规定的 `tick()`，最后只交完整代码；AI 写代码时间 **10 分钟**，人类 **45 分钟**；可用同样公开的示例、测试命令，不看别的参赛 bot；禁止外部策略参考；到点冻结源码。规则与接口以随包文档为准。

**同一届所有 AI 必须收到字节相同的 `AI_PROMPT.md` 和相同的游戏 ZIP**。最简单的做法：直接把 [统一模板](AI_PROMPT_TEMPLATE.md) 原样复制成每届的 `AI_PROMPT.md`。不给任何模型单独提示、提示级别或额外上下文。计时从真正开始写代码算起。正式随机种子在所有代码冻结后生成。

### 开赛前检查

`mbc doctor --season /path/to/season-directory` → **`mbc pack-season`（仅一次）** → 给所有选手相同的 ZIP。确认三份双语 Markdown 在这个 ZIP 以及赛后数据库归档中都存在；进行无剧透的端到端对战测试，再冻结规则和接口。`mbc kit` 是旧命令的兼容别名，不需要执行。旧版 v1 ZIP 仍可读取，但新届一律 v2。

## English

### Deliverables

Create each season **outside** the engine repository and distribute **one** self-contained `season.zip` to the organiser and all contestants. There is no separate contestant kit.

| File | Purpose |
|---|---|
| `manifest.json` | Season metadata with `"format_version": 2` |
| `game.py` | Authoritative Python judge |
| `arena.hpp`, `grader.cpp` | C++ API and wire adapter |
| `viewer.html` | Standalone replay viewer |
| `example_bot.cpp` | Valid **strategy-free** interface example |
| `RULES.md` | Short bilingual game rules |
| `INTERFACE.md` | Short bilingual C++ API guide |
| `AI_PROMPT.md` | **Identical contestant prompt** for every AI, bilingual |

Add `"format_version": 2`, `"interface": "INTERFACE.md"` and `"ai_prompt": "AI_PROMPT.md"` to the existing manifest fields.

### How to write the docs

- All three Markdown files must contain **`## 中文` and `## English`** sections with **equivalent information**.
- Be **short, readable and a little funny**. Start with the goal, then roles/map, valid actions per turn, scoring/winning and key edge cases. The API guide should explain `tick()`, every relevant state field, action calls, build/test commands and a tiny **strategy-free** example.
- Aim for **one or two screens** of rules. Do not write a thesis or an algorithms tutorial. Do not omit any rule that could change a match outcome; put technical edge cases in a small table or FAQ.
- Jokes are welcome; ambiguous coordinates, units, action ordering and tie-breaking are not.
- Do **not** leak tactics, recommended heuristics, optimal decisions or strategic hints through rules, API docs or prompts.

### Fair AI contestant prompt

`AI_PROMPT.md` states the task and **identical constraints** only: each AI writes **one C++17 `.cpp/.cc` bot** implementing the header's `tick()`, and submits complete code; AI development takes **10 minutes**, human development **45 minutes**; identical public examples and tests are allowed, other contestant code and external strategy references are not; freeze at the deadline. The packaged rules and API documentation are authoritative.

Send every AI **the exact same bytes** of `AI_PROMPT.md` and the **same season ZIP**. No model-specific hints, preferred strategies, extra context or different difficulty nudges. Start timing when coding begins; generate official seeds only after all submissions are frozen.

### Before the contest

Run `mbc doctor --season /path/to/season-directory`, then **`mbc pack-season` once**. Give every contestant the same resulting ZIP. Verify all three bilingual documents appear in the season ZIP and post-tournament database archive; smoke-test a full game before freezing the rules. Legacy `mbc kit` is just a compatible alias for `pack-season` and is not needed. Legacy v1 ZIPs remain readable; **every new season uses v2**.
