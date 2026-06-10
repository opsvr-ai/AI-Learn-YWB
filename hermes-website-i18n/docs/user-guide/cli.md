---
sidebar_position: 1
title: "CLI 界面"
description: "掌握 Hermes Agent 终端界面——命令、快捷键、人格模式等"
---

# CLI 界面

Hermes Agent 的 CLI 是一个完整的终端用户界面（TUI）——不是 Web UI。它具有多行编辑、斜杠命令自动补全、对话历史、打断并重定向以及流式工具输出等功能。为习惯在终端中工作的人而打造。

:::tip
Hermes 还附带一个现代化的 TUI，支持模态浮层、鼠标选择和异步输入。使用 `hermes --tui` 启动——参见 [TUI](tui.md) 指南。
:::

## 运行 CLI

```bash
# 启动交互式会话（默认）
hermes

# 单次查询模式（非交互式）
hermes chat -q "Hello"

# 指定模型
hermes chat --model "anthropic/claude-sonnet-4"

# 指定提供商
hermes chat --provider nous        # 使用 Nous Portal
hermes chat --provider openrouter  # 强制使用 OpenRouter

# 指定工具集
hermes chat --toolsets "web,terminal,skills"

# 启动时预加载一个或多个 skills
hermes -s hermes-agent-dev,github-auth
hermes chat -s github-pr-workflow -q "open a draft PR"

# 恢复之前的会话
hermes --continue             # 恢复最近的 CLI 会话 (-c)
hermes --resume <session_id>  # 通过 ID 恢复特定会话 (-r)

# 详细模式（调试输出）
hermes chat --verbose

# 隔离的 git worktree（用于并行运行多个 agent）
hermes -w                         # worktree 中的交互模式
hermes -w -q "Fix issue #123"     # worktree 中的单次查询
```

## 界面布局

<img className="docs-terminal-figure" src="/img/docs/cli-layout.svg" alt="Stylized preview of the Hermes CLI layout showing the banner, conversation area, and fixed input prompt." />
<p className="docs-figure-caption">Hermes CLI 横幅、对话流和固定输入提示符，以稳定的文档图形呈现，而非脆弱的文本艺术。</p>

欢迎横幅会一目了然地显示您的模型、终端后端、工作目录、可用工具和已安装的 skills。

### 状态栏

输入区域上方有一个持久的状态栏，实时更新：

```
 ⚕ claude-sonnet-4-20250514 │ 12.4K/200K │ [██████░░░░] 6% │ $0.06 │ 15m
```

| 元素 | 说明 |
|---------|-------------|
| 模型名称 | 当前模型（超过 26 个字符时截断显示） |
| Token 计数 | 已使用的上下文 token 数 / 最大上下文窗口 |
| 上下文进度条 | 带颜色编码阈值的可视化填充指示器 |
| 费用 | 预估会话费用（未知/零价格模型显示 `n/a`） |
| 🗜️ N | **上下文压缩计数**——当前运行中的会话已被自动压缩的次数。首次压缩触发后显示。 |
| ▶ N | **活跃后台任务**——当前会话中仍在运行的 `/background` 提示数量。只要有至少一个任务在执行就显示。 |
| 持续时间 | 已过会话时间 |
| ⚠ YOLO | **YOLO 模式警告**——当 `HERMES_YOLO_MODE` 开启时显示（启动时 `hermes --yolo` 或会话中 `/yolo` 切换）。与横幅行警告呼应，让您不会忘记正处于自动批准模式。 |

状态栏会根据终端宽度自适应——完整布局在 ≥ 76 列时显示，紧凑模式在 52–75 列，最小模式（模型 + 持续时间，以及 YOLO 激活时的 YOLO 标记）在低于 52 列时显示。

**上下文颜色编码：**

| 颜色 | 阈值 | 含义 |
|-------|-----------|---------|
| 绿色 | < 50% | 空间充裕 |
| 黄色 | 50–80% | 逐渐变满 |
| 橙色 | 80–95% | 接近上限 |
| 红色 | ≥ 95% | 即将溢出——建议 `/compress` |

使用 `/usage` 查看详细分类，包括各类别的费用（输入 vs 输出 token）。

### 会话恢复显示

恢复之前的会话时（`hermes -c` 或 `hermes --resume <id>`），横幅和输入提示符之间会显示一个"先前对话"面板，展示对话历史的简洁摘要。详见[会话——恢复时的对话摘要](sessions.md#conversation-recap-on-resume)，了解详情和配置方式。

## 快捷键

| 按键 | 操作 |
|-----|--------|
| `Enter` | 发送消息 |
| `Alt+Enter`、`Ctrl+J` 或 `Shift+Enter` | 换行（多行输入）。`Shift+Enter` 需要终端能将其与 `Enter` 区分开来——见下文。在 Windows Terminal 上，`Alt+Enter` 被终端捕获（全屏切换）；请改用 `Ctrl+Enter` 或 `Ctrl+J`。 |
| `Alt+V` | 当终端支持时，从剪贴板粘贴图片 |
| `Ctrl+V` | 粘贴文本并机会性地附加剪贴板中的图片 |
| `Ctrl+B` | 当语音模式启用时，开始/停止录音（`voice.record_key`，默认：`ctrl+b`） |
| `Ctrl+G` | 在 `$EDITOR`（vim/nvim/nano/VS Code 等）中打开当前输入缓冲区。保存并退出后将编辑后的文本作为下一条提示发送——适合编写长篇、多段落的提示。 |
| `Ctrl+X Ctrl+E` | Emacs 风格的外部编辑器替代快捷键（与 `Ctrl+G` 行为相同）。 |
| `Ctrl+C` | 打断 agent（2 秒内双击强制退出） |
| `Ctrl+D` | 退出 |
| `Ctrl+Z` | 将 Hermes 挂起到后台（仅限 Unix）。在 shell 中运行 `fg` 恢复。 |
| `Tab` | 接受自动建议（幽灵文本）或自动补全斜杠命令 |

**多行粘贴预览。** 当您粘贴多行文本块时，CLI 会显示一个简洁的单行预览（`[pasted: 47 lines, 1,842 chars — press Enter to send]`），而不是将整个载荷倾泻到回滚缓冲区中。实际发送的仍然是完整内容；这只是显示上的优化。

**最终回复中的 Markdown 剥离。** CLI 会从*最终* agent 回复中剥离最冗长的 markdown 栅栏和 `**粗体**` / `*斜体*` 包装，使其呈现为可读的终端文本，而非原始源码。代码块和列表会保留。这不影响网关平台或工具结果——它们保留 markdown 以供原生渲染。

## 斜杠命令

输入 `/` 查看自动补全下拉菜单。Hermes 支持大量 CLI 斜杠命令、动态 skill 命令和用户自定义快速命令。

常用示例：

| 命令 | 说明 |
|---------|-------------|
| `/help` | 显示命令帮助 |
| `/model` | 显示或更改当前模型 |
| `/tools` | 列出当前可用工具 |
| `/skills browse` | 浏览 skills 中心和官方可选 skills |
| `/background <prompt>` | 在独立的后台会话中运行提示 |
| `/skin` | 显示或切换活跃的 CLI 皮肤 |
| `/voice on` | 启用 CLI 语音模式（按 `Ctrl+B` 录音） |
| `/voice tts` | 切换 Hermes 回复的语音播报 |
| `/reasoning high` | 提高推理强度 |
| `/title My Session` | 为当前会话命名 |
| `/status` | 显示会话信息——模型/配置文件/token/持续时间——随后显示一个本地的**会话摘要**块（最近的轮次数、使用最多的工具、涉及的文件、最新用户提示 + 助手回复）。纯本地计算；不调用 LLM。 |
| `/sessions` | 在经典 CLI 中打开交互式会话选择器（与 TUI 使用的界面相同）。输入过滤、方向键导航、Enter 恢复。 |

完整的 CLI 和消息平台内置命令列表，参见[斜杠命令参考](../reference/slash-commands.md)。

关于设置、提供商、静音调节和消息平台/Discord 语音使用，参见[语音模式](features/voice-mode.md)。

:::tip
命令不区分大小写——`/HELP` 与 `/help` 效果相同。已安装的 skills 也会自动成为斜杠命令。
:::

## 快速命令

您可以定义自定义命令，直接运行 shell 命令而无需调用 LLM。这些命令在 CLI 和消息平台（Telegram、Discord 等）中均可使用。

```yaml
# ~/.hermes/config.yaml
quick_commands:
  status:
    type: exec
    command: systemctl status hermes-agent
  gpu:
    type: exec
    command: nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
  restart:
    type: alias
    target: /gateway restart
```

然后在任何聊天中输入 `/status`、`/gpu` 或 `/restart`。更多示例参见[配置指南](/docs/user-guide/configuration#quick-commands)。

## 启动时预加载 Skills

如果您已经知道要为会话激活哪些 skills，可以在启动时指定：

```bash
hermes -s hermes-agent-dev,github-auth
hermes chat -s github-pr-workflow -s github-auth
```

Hermes 会在第一轮对话之前将每个命名的 skill 加载到会话提示中。该标志在交互模式和单次查询模式下均有效。

## Skill 斜杠命令

`~/.hermes/skills/` 中的每个已安装 skill 都会自动注册为一个斜杠命令。skill 名称即为命令：

```
/gif-search funny cats
/axolotl help me fine-tune Llama 3 on my dataset
/github-pr-workflow create a PR for the auth refactor

# 仅输入 skill 名称会加载它，让 agent 询问您需要什么：
/excalidraw
```

## 人格模式

设置预定义的人格来改变 agent 的语气：

```
/personality pirate
/personality kawaii
/personality concise
```

内置人格包括：`helpful`、`concise`、`technical`、`creative`、`teacher`、`kawaii`、`catgirl`、`pirate`、`shakespeare`、`surfer`、`noir`、`uwu`、`philosopher`、`hype`。

您也可以在 `~/.hermes/config.yaml` 中定义自定义人格：

```yaml
personalities:
  helpful: "You are a helpful, friendly AI assistant."
  kawaii: "You are a kawaii assistant! Use cute expressions..."
  pirate: "Arrr! Ye be talkin' to Captain Hermes..."
  # 添加您自己的！
```

## 多行输入

有两种方式输入多行消息：

1. **`Alt+Enter`、`Ctrl+J` 或 `Shift+Enter`**——插入换行
2. **反斜杠续行**——以 `\` 结尾进行续行：

```
❯ Write a function that:\
  1. Takes a list of numbers\
  2. Returns the sum
```

:::info
支持粘贴多行文本——使用上述任意换行键，或直接粘贴内容。
:::

### Shift+Enter 兼容性

大多数终端默认发送相同的字节序列来代表 `Enter` 和 `Shift+Enter`，因此应用程序无法区分它们。只有当终端通过 [Kitty keyboard protocol](https://sw.kovidgoyal.net/kitty/keyboard-protocol/) 或 xterm 的 `modifyOtherKeys` 模式发送不同的序列时，Hermes 才能识别 `Shift+Enter`。

| 终端 | 状态 |
|---|---|
| Kitty、foot、WezTerm、Ghostty | 默认启用独立的 `Shift+Enter` |
| iTerm2（较新版本）、Alacritty、VS Code 终端、Warp | 在设置中启用 Kitty protocol 后支持 |
| Windows Terminal Preview 1.25+ | 在设置中启用 Kitty protocol 后支持 |
| macOS Terminal.app、Windows Terminal（稳定版） | 不支持——`Shift+Enter` 与 `Enter` 无法区分 |

在终端无法区分它们的地方，`Alt+Enter` 和 `Ctrl+J` 在各处都能继续使用。**特别提醒：在 Windows Terminal 上，`Alt+Enter` 被终端捕获（切换全屏），永远不会到达 Hermes——请使用 `Ctrl+Enter`（传递为 `Ctrl+J`）或直接使用 `Ctrl+J` 来换行。**

## 打断 Agent

您可以随时打断 agent：

- **输入新消息 + Enter**——当 agent 正在工作时，它会打断并处理您的新指令
- **`Ctrl+C`**——打断当前操作（2 秒内双击强制退出）
- 正在进行的终端命令会立即被终止（SIGTERM，然后 1 秒后 SIGKILL）
- 打断期间输入的多个消息会合并为一条提示

### 忙碌输入模式

`display.busy_input_mode` 配置键控制当 agent 正在工作时按 Enter 键的行为：

| 模式 | 行为 |
|------|----------|
| `"interrupt"`（默认） | 您的消息打断当前操作并立即被处理 |
| `"queue"` | 您的消息被静默排队，在 agent 完成后作为下一轮对话发送 |
| `"steer"` | 您的消息通过 `/steer` 注入当前运行，在下一个工具调用后到达 agent——不打断，不产生新轮次 |

```yaml
# ~/.hermes/config.yaml
display:
  busy_input_mode: "steer"   # 或 "queue" 或 "interrupt"（默认）
```

`"queue"` 模式在您想准备后续消息而不想意外取消进行中的工作时很有用。`"steer"` 模式在您想在不打断的情况下中途重定向 agent 时很有用——例如，当 agent 还在编辑代码时，输入"actually, also check the tests"。未知值会回退到 `"interrupt"`。

`"steer"` 有两个自动回退：如果 agent 尚未启动，或附加了图片，消息会回退到 `"queue"` 行为，确保不丢失任何内容。

您也可以在 CLI 中更改它：

```text
/busy queue
/busy steer
/busy interrupt
/busy status
```

:::tip 首次提示
您在 Hermes 工作时第一次按 Enter 时，Hermes 会打印一行提示来解释 `/busy` 选项（`"(tip) Your message interrupted the current run…"`）。该提示每次安装仅触发一次——`config.yaml` 中 `onboarding.seen.busy_input_prompt` 下的标志会锁定它。删除该键可以再次看到提示。
:::

### 挂起到后台

在 Unix 系统上，按 **`Ctrl+Z`** 将 Hermes 挂起到后台——就像任何终端进程一样。Shell 会打印确认信息：

```
Hermes Agent has been suspended. Run `fg` to bring Hermes Agent back.
```

在 shell 中输入 `fg` 即可从离开的位置恢复会话。Windows 不支持此功能。

## 工具进度显示

CLI 在 agent 工作时显示动画反馈：

**思考动画**（API 调用期间）：
```
  ◜ (｡•́︿•̀｡) 思考中... (1.2s)
  ◠ (⊙_⊙) 思索中... (2.4s)
  ✧٩(ˊᗜˋ*)و✧ 有思路了！ (3.1s)
```

**工具执行信息流：**
```
  ┊ 💻 terminal `ls -la` (0.3s)
  ┊ 🔍 web_search (1.2s)
  ┊ 📄 web_extract (2.1s)
```

使用 `/verbose` 循环切换显示模式：`off → new → all → verbose`。此命令也可在消息平台中启用——参见[配置](/docs/user-guide/configuration#display-settings)。

### 工具预览长度

`display.tool_preview_length` 配置键控制工具调用预览行中显示的最大字符数（如文件路径、终端命令）。默认为 `0`，表示无限制——显示完整路径和命令。

```yaml
# ~/.hermes/config.yaml
display:
  tool_preview_length: 80   # 将工具预览截断为 80 个字符（0 = 无限制）
```

这在狭窄终端或工具参数包含很长的文件路径时很有用。

## 会话管理

### 恢复会话

退出 CLI 会话时，会打印一条恢复命令：

```
Resume this session with:
  hermes --resume 20260225_143052_a1b2c3

Session:        20260225_143052_a1b2c3
Duration:       12m 34s
Messages:       28 (5 user, 18 tool calls)
```

恢复选项：

```bash
hermes --continue                          # 恢复最近的 CLI 会话
hermes -c                                  # 简短形式
hermes -c "my project"                     # 恢复已命名的会话（谱系中最新的）
hermes --resume 20260225_143052_a1b2c3     # 通过 ID 恢复特定会话
hermes --resume "refactoring auth"         # 通过标题恢复
hermes -r 20260225_143052_a1b2c3           # 简短形式
```

恢复会从 SQLite 加载完整的对话历史。agent 会看到所有之前的消息、工具调用和回复——就像您从未离开一样。

在聊天中使用 `/title My Session Name` 为当前会话命名，或从命令行使用 `hermes sessions rename <id> <title>`。使用 `hermes sessions list` 浏览过去的会话。

### 会话存储

CLI 会话存储在 Hermes 的 SQLite 状态数据库中，位于 `~/.hermes/state.db`。数据库保存着：

- 会话元数据（ID、标题、时间戳、token 计数器）
- 消息历史
- 跨压缩/恢复会话的谱系
- `session_search` 使用的全文搜索索引

一些消息适配器还会在数据库旁边保留每个平台的转录文件，但 CLI 本身从 SQLite 会话存储中恢复。

### 上下文压缩

长对话在接近上下文限制时会自动摘要：

```yaml
# 在 ~/.hermes/config.yaml 中
compression:
  enabled: true
  threshold: 0.50    # 默认在上下文限制的 50% 时压缩

# 摘要模型配置在 auxiliary 下：
auxiliary:
  compression:
    model: ""  # 留空使用主聊天模型（默认）。或指定便宜快速的模型，如 "google/gemini-3-flash-preview"。
```

压缩触发时，中间的轮次会被摘要，而前 3 轮和后 20 轮始终保留。

## 后台会话

在独立的后台会话中运行提示，同时继续使用 CLI 进行其他工作：

```
/background Analyze the logs in /var/log and summarize any errors from today
```

Hermes 会立即确认任务并将提示返回给您：

```
🔄 Background task #1 started: "Analyze the logs in /var/log and summarize..."
   Task ID: bg_143022_a1b2c3
```

### 工作原理

每个 `/background` 提示会在守护线程中生成一个**完全独立的 agent 会话**：

- **隔离的对话**——后台 agent 不了解您当前会话的历史。它只接收您提供的提示。
- **相同配置**——后台 agent 继承当前会话的模型、提供商、工具集、推理设置和回退模型。
- **非阻塞**——您的前台会话保持完全交互。您可以聊天、运行命令，甚至启动更多后台任务。
- **多任务**——您可以同时运行多个后台任务。每个任务都会获得一个编号 ID。

### 结果

后台任务完成后，结果会作为面板显示在您的终端中：

```
╭─ ⚕ Hermes (background #1) ──────────────────────────────────╮
│ Found 3 errors in syslog from today:                         │
│ 1. OOM killer invoked at 03:22 — killed process nginx        │
│ 2. Disk I/O error on /dev/sda1 at 07:15                      │
│ 3. Failed SSH login attempts from 192.168.1.50 at 14:30      │
╰──────────────────────────────────────────────────────────────╯
```

如果任务失败，您将看到错误通知。如果配置中启用了 `display.bell_on_complete`，终端会在任务完成时响铃。

### 使用场景

- **长时间研究**——"/background research the latest developments in quantum error correction"，同时您在处理代码
- **文件处理**——"/background analyze all Python files in this repo and list any security issues"，同时您在进行其他对话
- **并行调查**——启动多个后台任务同时探索不同角度

:::info
后台会话不会出现在您的主对话历史中。它们是独立的会话，拥有自己的任务 ID（如 `bg_143022_a1b2c3`）。
:::

## 安静模式

默认情况下，CLI 以安静模式运行，该模式下：
- 抑制工具的详细日志
- 启用 kawaii 风格的动画反馈
- 保持输出简洁且用户友好

如需调试输出：
```bash
hermes chat --verbose
```
