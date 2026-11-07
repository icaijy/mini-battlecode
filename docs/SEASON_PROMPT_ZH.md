# Mini Battlecode：交给 AI 的新赛季制作任务（直接复制）

请为通用 Mini Battlecode 引擎创作**一个独立赛季插件**。不要修改 `mini-battlecode/arena/`，不要把任何赛季代码提交到引擎仓库。所有文件输出到我指定的外部目录，例如 `~/mbc-games/s2/`，完成后由我执行 `mbc pack-season` 生成可复用 ZIP。

交付 7 个文件：`manifest.json`、`game.py`、`arena.hpp`、`grader.cpp`、`viewer.html`、`RULES.md`（中英双语）与 `example_bot.cpp`（只演示 API，不包含有效竞赛策略）。

`manifest.json` 必须包含 `id`, `title`, `version`, `judge:"game.py"`, `header:"arena.hpp"`, `adapter:"grader.cpp"`, `viewer:"viewer.html"`, `example:"example_bot.cpp"`, `rules:"RULES.md"`, `default_seeds`。

Python `game.py` 提供 `create_game(seed)`，返回具备 `max_turns`, `turn`, `observe(team)`, `parse_action(team, line)`, `step([action0,action1])`, `snapshot()`, `outcome()` 的实例。`observe` 产生一行带 `\n` 的 UTF-8 文本；`parse_action` 验证并拒绝非法行动；`snapshot` 产生 JSON 可序列化的字典；`outcome()` 产生 `{ "scores": [x,y], "winner": 0|1|null }`。同 seed 可复现，双方同时下指令后结算，且应尽可能公平对称。

C++17 的 `arena.hpp` 只暴露可供编写一个 `.cpp` / `.cc` bot 的 `tick()`、状态和行动函数。`grader.cpp` 负责每 tick 从 stdin 读入一行 observation、调用 `tick()`、往 stdout 输出一行 action，收到 `END` 退出。选手不写 `main()`。

**可视化协议（强制）**：网站会把 `viewer.html` 放到受限沙箱 iframe，不能用 fetch 读取服务器上的回放。Viewer 应监听：

```javascript
window.addEventListener('message', (event) => {
  if (event.data?.type === 'mini-battlecode-replay') {
    const replay = event.data.replay; // {game, version, result, frames}
    loadReplay(replay);               // 自行实现绘制、进度条和播放
  }
});
```

也应能通过本地文件选择器直接加载 `.json`，方便离线审查比赛。所有 CSS/JS 写在该 HTML 内，不依赖外部网络 CDN。

设计规则要少而有策略深度，适合人类 45 分钟和 AI 10 分钟写 bot。必要时增加插件自己的测试；不要包含现成的高级 bot 策略或正式比赛 seeds。使用 `mbc doctor --season /path/to/game.zip` 和 `mbc duel` 验证。游戏包与参赛包由主办方打包，结果导入 `icaijy.com` 数据库。
