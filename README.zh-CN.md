# Mini Battlecode · 通用引擎

[English](README.md) · [每届必须遵守的双语规范](docs/SEASON_STANDARD.md) · [新赛季设计任务](docs/SEASON_PROMPT_ZH.md) · [统一 AI 选手提示词](docs/AI_PROMPT_TEMPLATE.md)

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

## 每届完整流程：一个 ZIP 搞定

**以后每届只有一个游戏 ZIP，例如 `season_1.zip`。** 这份 ZIP 同时给主办方、你本人和所有参赛 AI；不再创建第二份「选手包」。人人看到相同的公开规则、接口和裁判代码。

1. 让负责设计游戏的 AI 在仓库**外**创建 `~/mbc-games/season_1/`，包含 `manifest.json`（`format_version: 2`）、`game.py`、`arena.hpp`、`grader.cpp`、`viewer.html`、`example_bot.cpp`。另外必须有三份简明、略搞笑、内容准确的**中英双语**文档：
   - `RULES.md`：游戏规则，别写论文。
   - `INTERFACE.md`：C++ 状态和动作 API，给我速查。
   - `AI_PROMPT.md`：所有 AI 使用**同一份原文**的中立比赛指令，建议复制 [统一模板](docs/AI_PROMPT_TEMPLATE.md)。

   文档都包含 `## 中文`、`## English`，不能有策略剧透。详细要求见 [赛季规范](docs/SEASON_STANDARD.md)。

2. 检查游戏，然后**只打一次包**：

```bash
mbc doctor --season ~/mbc-games/season_1
mbc pack-season --season ~/mbc-games/season_1 --out ~/mbc-games/season_1.zip
```

3. **把同一个 `season_1.zip` 发给每个 AI，也给自己用。** 每个 AI 收到相同的 `AI_PROMPT.md`。你可以解压它读取规则和示例，不需要额外的 kit：

```bash
mkdir -p ~/mbc-games/play
unzip ~/mbc-games/season_1.zip -d ~/mbc-games/play
```

   参赛者只写**一份 C++17 `.cpp` / `.cc`**；人类 45 分钟、AI 各 10 分钟。只准使用同一份公开资料，不查看其他参赛 bot。到时冻结源码，之后才生成决赛随机种子。

4. 你自己测试 bot 时，还是使用**同一份 ZIP**：

```bash
mbc duel --season ~/mbc-games/season_1.zip \
  --blue ~/mbc-games/bots/human.cpp \
  --red ~/mbc-games/play/example_bot.cpp \
  --seed 7 --replay ~/mbc-games/test.json
```

5. **正式决赛（默认方式）**：把参赛代码直接放进一个文件夹，例如 `~/mbc-games/bots/`：

```text
bots/
  human.cpp
  gpt.cpp
  claude.cpp
  gemini.cc
```

   一条命令自动找出这个目录**直接包含的所有 `.cpp/.cc` 文件**，全部编译并两两对战，最后按照**文件名**列出胜、平、负场次（终端不刷屏输出每一局）：

```bash
mbc finals --season ~/mbc-games/season_1.zip \
  --bots-dir ~/mbc-games/bots
```

   可选 `--seed-count 8` 指定每对选手的地图种子数（每个种子互换双方位置各打一场）。默认使用这一届游戏包里设置的种子数。正式冠军依完整双边循环赛积分决定；所有 replay 保存到结果目录，不自动挑精彩对局。**目录中不要放测试用的 `example_bot.cpp`，否则它也会参赛。**

   赛后输出每个人的文件名与胜/平/负场次，以及自动生成的 `database_import.zip`。这是存档数据文件，**不是第二份游戏 ZIP**。


6. 把 `database_import.zip` 传到网站服务器，在完成部署和迁移的 `icaijy.com` 项目目录运行：

```bash
python manage.py migrate
python manage.py import_battlecode /path/to/database_import.zip
```

   成绩、规则、选手源码和全部 replay 最终由网站数据库保存，在 `https://icaijy.com/battlecode/` 查看。注意第一次上线仍需要部署 Django 新代码，GitHub 更新本身不会自动部署。

**兼容提醒：** `mbc kit` 旧命令暂时保留，但它现在和 `mbc pack-season` 输出**相同的游戏包**。正常使用只需要 `pack-season`，别再生成两份。

## 文件放哪里？

| 内容 | 位置 |
|---|---|
| 编译、通讯、赛制、结果导出代码 | **本引擎仓库**，永不放赛季代码 |
| 每届独立的完整游戏包 | 你本地保存的 `season_1.zip` 等（仓库外） |
| 所有人使用的参赛包 | **就是上面同一份** `season_1.zip`，无需第二个文件 |
| 每个 bot | 单独 `.cpp` / `.cc`，仓库外 |
| 每届最终成绩、规则、源码快照、全部 replay | `icaijy.com` 的 **Django 数据库**，由 `database_import.zip` 导入 |

**技术边界**：新游戏必须有 `game.py`（Python 权威裁判）、`grader.cpp`（通信）、`arena.hpp`（C++ API）、`viewer.html`（可视化）；不是只需一个 grader。参赛者不用写 `main()`。新版 v2 赛季缺少必需文档或文档为空时 `mbc doctor` 和打包会拒绝通过；标题名称和排版不影响加载。双语内容由主办方审查，旧版 v1 ZIP 继续兼容。

**安全提醒**：游戏插件中的 `game.py` 及所有 C++ bot 都是会在你的电脑上实际运行的代码，**引擎不是安全沙箱**；只运行自己信任的代码或使用隔离容器。网站导入器只读取数据，不执行任何游戏代码。每届 viewer 会被沙箱化，必须支持 `postMessage` 接收 replay 数据。

## 验证

```bash
python3 -m unittest discover -s tests -v
mbc doctor
```

引擎测试使用临时生成的极简假游戏，**仓库完全不含任何真实赛季**。
