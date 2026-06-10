---
title: "Desktop App"
description: "Hermes 原生桌面应用 — 流畅的聊天体验，支持流式工具输出、并排预览、文件浏览器、语音、Cron、配置文件、Skills 和设置。支持 macOS、Windows 和 Linux。"
---

# Desktop App

Hermes Desktop 是一款围绕**同一个** Agent 构建的原生桌面应用——使用与 CLI 和 Gateway 相同的配置、API Key、会话、Skills 和记忆系统。它不是一个独立产品或简化克隆；它使用相同的 Hermes Agent 核心和设置，通过现代且精心设计的 UI 驱动。如果你已经在终端中使用过 `hermes`，你在那里配置的一切在这里立即可用，在这里做的任何操作也会同步到终端。

支持 **macOS、Windows 和 Linux**。

:::tip 各个界面的区别
Hermes 有多个前端界面，都连接同一个 Agent：

- **Desktop App**（本页）—— 原生桌面应用，提供专为聊天、配置和管理设计的 UI。
- **CLI**（`hermes`）和 **[TUI](./tui.md)**（`hermes --tui`）—— 终端界面。
- **[Web Dashboard](./features/web-dashboard.md)**（`hermes dashboard`）—— 浏览器管理面板；其可选的**聊天**选项卡通过伪终端嵌入 TUI。

根据场景选择即可。它们共享状态，因此可以在一个界面开始会话，在另一个界面继续。
:::

## 安装

请参考 [Hermes Desktop 安装指南](../getting-started/installation.md)。

如果你已经安装了 Hermes，直接运行：

```bash
hermes desktop
```

这会使用你当前的配置、Key、会话和 Skills。

## 应用功能

桌面应用采用聊天优先的窗口布局，左侧为导航栏。支持管理多个并发的 Agent 对话、配置消息提供商、创建制品、浏览项目文件夹结构，以及在多个项目间切换。

### 聊天

应用的核心功能，提供：

- **流式响应**，实时显示工具活动状态和结构化工具调用摘要。
- **完整的对话历史**，与所有其他 Hermes 界面共享——在桌面端开始的会话可在 CLI/TUI 中继续，反之亦然。
- **拖放文件**到聊天区域，附加到你的下一条消息中。
- **右侧预览栏**——可并排渲染网页、文件和工具输出，同时继续聊天。
- **历史记录与队列编辑**——在空白输入框中按上下方向键可回顾并复用之前的提示，已排队等待发送的消息也可编辑。

#### 状态栏

聊天窗口底部的状态栏显示实时会话状态，无需打开设置即可快速操作：

- **内联模型选择器**——直接从状态栏切换当前会话的模型。
- **会话级 YOLO 开关**——仅针对当前会话开启或关闭 YOLO（与 TUI 一致）。YOLO 会跳过危险命令的审批提示，请确保你了解其作用——参见[安全 → YOLO 模式](./security.md#yolo-mode)。

### 文件浏览器

无需离开应用即可浏览和预览工作目录——方便随时查看 Agent 读写和编辑文件的过程。使用 `hermes desktop --cwd <path>`（或 `HERMES_DESKTOP_CWD` 环境变量）设置初始项目目录。

### 语音

与 Hermes 对话并收听回复，与[语音模式](./features/voice-mode.md)功能相同。macOS 上系统会提示一次麦克风权限。

### 设置与首次引导

通过真实的 UI 界面管理提供商、模型、工具和凭据，无需编辑 YAML。首次运行的引导流程可在数秒内让你发出第一条消息。设置面板涵盖提供商/Key、模型选择、工具集配置、MCP 服务器、Gateway 和会话管理。

- **提供商设置面板**——管理推理提供商的专属界面，提供账户/API-Key 的 UX，用于登录和存储每个提供商的凭据。
- **所有提供商和模型均可见**——GUI 显示完整的提供商列表和 `hermes model` 能够识别的所有模型，与 CLI 看到的是同一目录，而非精选子集。
- **xAI Grok OAuth**——Grok 是启动器中一等公民的 OAuth 提供商；通过浏览器流程登录，与其他 OAuth 提供商一致。
- **从 GUI 安装工具后端**——直接在应用内运行工具后端的安装步骤，无需切换到终端。
- **辅助模型警告**——如果将主模型切换到新提供商，而辅助任务（标题、摘要等）仍绑定到其他提供商时，应用会发出警告，避免无意中跨两个提供商分割工作。

### 管理面板

应用还提供了更广泛的 Hermes 管理功能，无需切换到终端：

- **Skills**——浏览、安装和管理 [Skills](./features/skills.md)。
- **Cron**——查看和管理[定时任务](../reference/cli-commands.md#hermes-cron)。
- **Profiles**——切换 [Hermes 配置文件](./profiles.md)（隔离的配置/Skills/会话）。
- **Messaging**——设置 Gateway 通道。
- **Agents 和 Command Center**——多 Agent 工作流的管理界面。

### 快捷键与导航

- **命令面板**——按 **Cmd+K**（Windows/Linux 为 Ctrl+K）快速跳转到操作和导航。
- **可自定义快捷键**——设置中的快捷键面板允许你重新映射应用的所有键盘快捷键。
- **自定义缩放**——以半档步长缩放界面，更精细地控制文字大小。
- **UI 语言切换**——在应用内切换界面语言，包括简体中文。

### 会话与配置文件

- **会话列表改进**——重新设计的会话列表，支持归档和会话维护，保持列表整洁。
- **按 ID 搜索会话**——直接通过 ID 查找特定会话。
- **多配置文件并行会话**——同时运行多个[配置文件](./profiles.md)下的会话，通过跨配置文件的 `@session` 链接引用其他配置文件中的会话。

## 更新

应用会在后台检查更新，有可用更新时提供一键更新。

手动[更新流程](https://hermes-agent.nousresearch.com/docs/getting-started/updating) 同样适用于 GUI。

## 卸载

打开 **设置 → 关于 → 危险区域**，选择卸载范围：

- **仅卸载聊天 GUI**——删除桌面应用及其数据；Hermes Agent、你的配置和聊天记录保留。（等同于 `hermes uninstall --gui`）
- **卸载 GUI + Agent，保留数据**——删除应用和 Agent，但保留配置、聊天记录和密钥，便于将来重新安装。（等同于 `hermes uninstall`）
- **卸载全部**——删除应用、Agent 和所有用户数据。（等同于 `hermes uninstall --full`）

应用会自动关闭以完成清理（清理在退出后执行，以便删除正在运行的应用包本身及其 venv）。当本地未安装 Agent 时（例如仅 GUI 的"精简版"客户端连接到远程后端），删除 Agent 的选项会自动隐藏。

你也可以从终端执行相同操作：`hermes uninstall --gui` 仅删除 GUI，或 `hermes uninstall` / `hermes uninstall --full` 同时删除 Agent。

## CLI 参考：`hermes desktop`

通过 CLI 启动只需运行 `hermes desktop`。默认会安装工作区 Node 依赖，构建当前操作系统的解包版 Electron 应用，然后启动构建好的制品。

| 参数 | 说明 |
|------|------|
| `--skip-build` | 跳过 npm install/package，直接从 `apps/desktop/release` 启动已有的解包应用 |
| `--force-build` | 即使内容戳匹配也强制完整重建 |
| `--build-only` | 构建桌面应用但不启动（用于 `hermes update`） |
| `--source` | 通过 `electron .` 从 `apps/desktop/dist` 启动而非打包版应用 |
| `--cwd PATH` | 桌面聊天会话的初始项目目录（设置 `HERMES_DESKTOP_CWD`） |
| `--hermes-root PATH` | 覆盖应用使用的 Hermes 源码根目录（设置 `HERMES_DESKTOP_HERMES_ROOT`） |
| `--ignore-existing` | 强制应用在后台解析期间忽略已在 `PATH` 上的 `hermes` CLI |
| `--fake-boot` | 启用确定性启动延迟，用于验证启动 UI |

## 工作原理

打包的应用仅包含 Electron 外壳。首次启动时，它将 Hermes Agent 运行时安装到 `HERMES_HOME`（`~/.hermes`，Windows 上为 `%LOCALAPPDATA%\hermes`）——**与 CLI 安装使用相同的目录结构**，这也是两者可互换的原因。React 渲染器通过标准 Gateway API 与 `hermes dashboard` 后端通信，复用 Agent 而非重新实现。安装、后端解析和自更新逻辑位于 Electron 主进程中。

## 连接到远程后端

默认情况下，应用启动并管理自己的**本地**后端。你也可以将其指向运行在其他机器上的 Hermes 后端——例如 VPS、家庭服务器或 Tailscale 后的 Mini。

远程后端是一个运行的 `hermes dashboard` 进程。桌面应用需要连接到这个服务器。

### 在后端（远程机器）上

设置用户名和密码，然后在可达地址上启动 Dashboard：

```bash
# 1. 设置 Dashboard 登录凭据
cat >> ~/.hermes/.env <<'EOF'
HERMES_DASHBOARD_BASIC_AUTH_USERNAME=admin
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=choose-a-strong-password
HERMES_DASHBOARD_BASIC_AUTH_SECRET=$(openssl rand -base64 32)
EOF
chmod 600 ~/.hermes/.env

# 2. 启动 Dashboard 绑定到可达地址
hermes dashboard --no-open --host 0.0.0.0 --port 9119
```

### 在应用中

**设置 → Gateway → Remote gateway：**

1. **Remote URL**——`http://<backend-host>:9119`
2. **Sign in**——应用自动检测后端使用的认证方式并显示对应的登录按钮
3. **Save and reconnect**——切换到远程后端

详见完整的[远程后端连接文档](./features/web-dashboard.md#connecting-hermes-desktop-to-a-remote-backend)。

## 故障排查

启动日志位于 `HERMES_HOME/logs/desktop.log`（包含后端输出和 Python 回溯），应用启动失败时请先检查这里。你也可以从 CLI 实时查看：

```bash
hermes logs gui -f
```

常见重置操作：

```bash
# 强制重新首次启动设置（macOS/Linux）
rm "$HOME/.hermes/hermes-agent/.hermes-bootstrap-complete"

# 重建损坏的 Python venv（macOS/Linux）
rm -rf "$HOME/.hermes/hermes-agent/venv"

# 重置卡住的 macOS 麦克风权限
tccutil reset Microphone com.nousresearch.hermes
```

## 从源码构建

如果想在应用本身上进行开发，从仓库根目录安装工作区依赖，然后在 `apps/desktop` 中启动开发服务器：

```bash
npm install          # 从仓库根目录
cd apps/desktop
npm run dev          # Vite renderer + Electron
```

构建安装包：

```bash
npm run dist:mac     # DMG + zip
npm run dist:win     # NSIS + MSI
npm run dist:linux   # AppImage + deb + rpm
npm run pack         # release/ 下的解包应用（无需安装程序）
```

## 参见

- [CLI 指南](./cli.md) —— 终端界面
- [TUI](./tui.md) —— 现代终端 UI
- [Web Dashboard](./features/web-dashboard.md) —— 浏览器管理面板
- [配置](./configuration.md) —— 桌面应用读写配置
- [Windows（原生）](./windows-native.md) —— Windows 原生安装路径
