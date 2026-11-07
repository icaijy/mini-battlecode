# Mini Battlecode — 极简人机大战引擎

[English README](README.md) · [给 AI 的新赛季制作提示词](docs/SEASON_PROMPT_ZH.md)

目的很简单：**Linux / WSL 安装一次，以后每届只换游戏插件和可视化，选手各交一份 `.cpp` / `.cc`，一条命令打完决赛。**

本仓库和 `icaijy.com` **完全独立**。网站只接收静态战绩页面和回放，不运行裁判，也不存你日常训练网站的代码。

## 1. 安装：以后就用 `mbc` 命令

需要 Python 3.10+、`g++`（C++17）。不需要 pip、Node.js 或数据库。

```bash
sudo apt update && sudo apt install -y git python3 g++
git clone https://github.com/icaijy/mini-battlecode.git
cd mini-battlecode
./install.sh
```

这会在 `~/.local/bin/mbc` 建立命令。终端提示 `mbc: command not found` 时，把这行加到 `~/.bashrc`，重新打开终端：

```bash
export PATH="$HOME/.local/bin:$PATH"
```

之后即使不在仓库目录，也能执行：

```bash
mbc doctor
```

安装后**不要删掉或搬走这个仓库目录**，因为 `mbc` 指向这里的源代码。更新直接在仓库执行 `git pull`。

## 2. 每天想玩的时候

### (1) 测试自己的 Bot

把自己的一份 C++ 代码放在 `bots/my_bot.cpp`。参赛 bot 只写一份 `.cpp/.cc`，不改 `grader.cpp`。以下命令建议在仓库根目录运行：

```bash
mbc duel --season courier_s1 \
  --blue bots/my_bot.cpp \
  --red seasons/courier_s1/example_bot.cpp \
  --seed 7 --replay results/test.json
```

它会自动编译两边代码、对战，并保存回放。第一届的可视化在 `seasons/courier_s1/viewer.html`，可直接加载生成的 replay JSON。

### (2) 正式大决战：一个命令

```bash
mbc finals --season courier_s1 \
  --bot human=bots/my_bot.cpp \
  --bot gpt=bots/gpt.cpp \
  --bot claude=bots/claude.cpp \
  --bot gemini=bots/gemini.cpp \
  --human human --seed-count 8
```

所有 bot 都只是一份 C++ 文件，不需要写额外的配置。引擎自动：编译 → 新生成比赛随机种子 → 每两人相互打、交换蓝红双方 → 保存全部 replay → 排名 → 生成可公开展示的静态网页。**程序不自动选择精彩对局，录视频时你自己挑。**

网页在 `published/index.html` 和 `published/courier_s1/index.html`。用下面命令在浏览器打开：

```bash
python3 -m http.server 8000 --directory published
```

打开 `http://localhost:8000`。想指定更多参数可以看 `mbc finals --help`。也可以通过 `--roster bots/roster.example.json` 让 JSON 配置所有选手；和 `--bot` 二选一。

**冠军只由完整双边循环赛决定，不让剪辑或一轮随机淘汰决定冠军。** `n` 个选手、每对 `s` 个种子，一共 `n(n−1)s` 场；例如 5 个 bot、6 个 seed = 120 场。视频内容由你自己挑回放，全部 replay 和比赛数据都会保留。

### (3) 给人类和各 AI 发完全相同的参赛包

```bash
mbc kit --season courier_s1 --out kits/courier_s1.zip
```

里面包括公开规则、`arena.hpp`、`grader.cpp`、专用 viewer、极简示例 bot 等，不包含任何高级策略。这样人类 45 分钟对 AI 10 分钟的挑战才有统一起跑线。计时从开始实际开发算起，交卷后冻结代码再生成决赛种子。

## 3. 第二届之后怎么搞？

```bash
mbc new-season season_2
```

它会复制第一届作为 **草稿**。然后把 [AI 新赛季制作提示词](docs/SEASON_PROMPT_ZH.md) 发给负责写游戏的 AI，请它为 `seasons/season_2/` 写好下面的文件：

| 新赛季需要改变的内容 | 说明 |
|---|---|
| `game.py` | **真正的游戏裁判**，Python 实现规则、回合、得分、胜负 |
| `arena.hpp` | 提供选手使用的 C++ 接口 |
| `grader.cpp` | 把引擎观察数据送给 bot 的 `tick()`，把动作送回去 |
| `viewer.html` | 每届自己的浏览器回放可视化 |
| `RULES.md` | 中英双语、无歧义的游戏规则 |
| `manifest.json` | 赛季名称、版本和文件列表 |

**有个必要的技术事实：新游戏不能只靠 `grader.cpp` 和 `viewer.html` 实现。** 因为判分与规则在 Python `game.py` 中执行；AI 需要把它也一起生成。但**通用引擎的 `arena/*.py` 无需修改**，正式比赛命令永远一样。

开始参赛之前先执行 `mbc doctor --season season_2`，并跑一局 `mbc duel` 验证能正常结束。然后冻结规则再让每个选手开工，不能边打边改裁判。

## 4. 结果怎么放到网站？

`mbc finals` 自动生成 `published/`：

- `published/index.html`：历届总目录。
- `published/<赛季>/index.html`：本届排行榜。
- `published/<赛季>/matches.json`：全部对局结果。
- `published/<赛季>/results.json`：正式排名、种子等元数据。
- `published/<赛季>/viewer.html`：专属回放播放器。
- `published/<赛季>/replays/`：**全部对局的回放**，网站的「All matches & replays」表格可以逐场打开，你自己挑要剪进视频的对局。

这些**静态文件**以后可以复制到 `icaijy.com` 的一个目录或单独部署 GitHub Pages；不需要在个人网站安装 Python 引擎和编译器。目前不会自动修改网站部署。

## 5. 比赛规则与安全边界

- 双方同时行动。每 tick 引擎把一行观察发送给 bot，bot 回一行动作；Python 裁判先收集双方动作再结算。
- 默认每次响应超时 0.5 秒判负；非法输出、崩溃或提前 EOF 同样判负。
- 每场比赛重新启动 bot 进程，避免把上一场记忆带进下一场。
- 每对选手对相同随机种子交换双方位置，全部双边循环赛计正式排名：胜 1，平 0.5，负 0，之后看净得分等平局细则。
- bot **直接编译运行本地原生 C++**，不是安全沙箱。不要执行来源不可信的恶意代码；需要时放到隔离虚拟机或容器里。

完整程序入口 `arena/cli.py`、通用裁判 `arena/core.py`、赛制 `arena/tournament.py`、网页导出 `arena/publish.py`；这些文件日后**基本不动**。改新赛季，优先只动 `seasons/<id>/`。

跑回归测试：

```bash
python3 -m unittest discover -s tests -v
```

这套系统是用来**打人机大战**的，不是为了让你每天继续造训练工具。满足前一天 OI 训练验收后开玩，别变成没有 OI 的 Battlecode 专业户。💀
