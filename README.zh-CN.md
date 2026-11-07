# Mini Battlecode · 通用引擎

[English](README.md) · [新赛季交给 AI 的制作规范](docs/SEASON_PROMPT_ZH.md)

**此仓库只有引擎，没有任何一届的游戏规则、赛季代码、bot 或战绩。** 每届游戏独立为一个 ZIP；全部历史数据最终通过导入 ZIP 保存在 `icaijy.com` 的数据库里。

## 安装（Linux / WSL）

需要 Python ≥3.10、g++（支持 C++17），不需要 pip 包：

```bash
sudo apt install -y git python3 g++
git clone https://github.com/icaijy/mini-battlecode.git
cd mini-battlecode
./install.sh
mbc doctor
```

`mbc` 安装到 `~/.local/bin`。若提示找不到命令，执行 `export PATH="$HOME/.local/bin:$PATH"`，并加到 `~/.bashrc`。保留克隆的仓库目录，更新用 `git pull`。

## 每届完整流程（只需要几个命令）

1. 创建一个**仓库外**的 `~/mbc-games/season_1/`，把 [AI 新赛季制作规范](docs/SEASON_PROMPT_ZH.md) 给负责设计游戏的 AI。它会写 `manifest.json`、`game.py`、`arena.hpp`、`grader.cpp`、`viewer.html`、`RULES.md` 和无策略示例 `example_bot.cpp`。**你只负责写自己的一个 `.cpp` 文件**，不改引擎。
2. 检查游戏并打包**完整赛事 ZIP**（主办方使用）：

```bash
mbc doctor --season ~/mbc-games/season_1
mbc pack-season --season ~/mbc-games/season_1 --out ~/mbc-games/season_1.zip
```

3. 单独打包发给各参赛 AI 的**公开参赛包**（包含公开规则和裁判，方便所有参赛者本地测试），所有选手收到同一份：

```bash
mbc kit --season ~/mbc-games/season_1.zip --out ~/mbc-games/season_1_players.zip
```

4. 所有 bot 开始编写。人类限时 45 分钟、AI 各 10 分钟；每人仅交 `.cpp` 或 `.cc`，策略代码冻结后再生成比赛随机种子。测试自己的 bot：

```bash
mbc duel --season ~/mbc-games/season_1.zip \
  --blue ~/mbc-games/bots/human.cpp --red ~/mbc-games/season_1/example_bot.cpp \
  --seed 7 --replay ~/mbc-games/test.json
```

5. 正式大决战，双边循环赛，**所有对局回放都保存**；没有自动选精彩对局：

```bash
mbc finals --season ~/mbc-games/season_1.zip \
  --bot human=~/mbc-games/bots/human.cpp \
  --bot gpt=~/mbc-games/bots/gpt.cpp \
  --bot claude=~/mbc-games/bots/claude.cpp \
  --bot gemini=~/mbc-games/bots/gemini.cpp \
  --human human --seed-count 8 \
  --out ~/mbc-games/results/season_1
```

输出：`~/mbc-games/results/season_1/tournament.json`、`replays/`、`sources/` 和 **`database_import.zip`**。

6. 把结果 ZIP 上传到自己的网站服务器（比如 SCP），在 `icaijy.com` 项目目录执行：

```bash
python manage.py migrate
python manage.py import_battlecode /path/to/database_import.zip
```

以后在 **`https://icaijy.com/battlecode/`** 浏览历届赛季、排行榜和全部回放。首次网站部署仍需要拉取网站仓库、迁移数据库、重新加载 Django；GitHub 提交不会自行部署线上网站。

## 文件放哪里？

| 内容 | 位置 |
|---|---|
| 编译、通讯、赛制、结果导出代码 | **本引擎仓库**，永不放赛季代码 |
| 每届独立的完整游戏包 | 你本地保存的 `season_1.zip` 等（仓库外） |
| 给人类、AI 的参赛包 | 你本地保存的 `season_1_players.zip` |
| 每个 bot | 单独 `.cpp` / `.cc`，仓库外 |
| 每届最终成绩、规则、源码快照、全部 replay | `icaijy.com` 的 **Django 数据库**，由 `database_import.zip` 导入 |

**技术边界**：新游戏必须有 `game.py`（Python 权威裁判）、`grader.cpp`（通信）、`arena.hpp`（C++ API）、`viewer.html`（可视化）；不是只需一个 grader。参赛者不用写 `main()`。

**安全提醒**：游戏插件中的 `game.py` 及所有 C++ bot 都是会在你的电脑上实际运行的代码，**引擎不是安全沙箱**；只运行自己信任的代码或使用隔离容器。网站导入器只读取数据，不执行任何游戏代码。每届 viewer 会被沙箱化，必须支持 `postMessage` 接收 replay 数据。

## 验证

```bash
python3 -m unittest discover -s tests -v
mbc doctor
```

引擎测试使用临时生成的极简假游戏，**仓库完全不含任何真实赛季**。
