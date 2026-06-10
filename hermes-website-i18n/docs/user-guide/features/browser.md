---
title: 浏览器自动化
description: 通过多种后端提供商控制浏览器——本地 Chromium 系列浏览器（通过 CDP）或云端浏览器，实现网页交互、表单填写、数据抓取等功能。
sidebar_label: Browser
sidebar_position: 5
---

# 浏览器自动化

Hermes Agent 提供了完整的浏览器自动化工具集，支持多种后端选项：

- **Browserbase 云端模式** — 通过 [Browserbase](https://browserbase.com) 使用托管的云端浏览器和反机器人工具
- **Browser Use 云端模式** — 通过 [Browser Use](https://browser-use.com) 作为替代的云端浏览器提供商
- **Firecrawl 云端模式** — 通过 [Firecrawl](https://firecrawl.dev) 使用内置抓取功能的云端浏览器
- **Camofox 本地模式** — 通过 [Camofox](https://github.com/jo-inc/camofox-browser) 进行本地反检测浏览（基于 Firefox 的指纹伪装）
- **本地 Chromium 系列 CDP** — 使用 `/browser connect` 将浏览器工具连接到您自己的 Chrome、Brave、Chromium 或 Edge 实例
- **本地浏览器模式** — 通过 `agent-browser` CLI 和本地 Chromium 安装

在所有模式下，Agent 都可以导航网站、与页面元素交互、填写表单和提取信息。

## 概述

页面以**无障碍树**（基于文本的快照）的形式呈现，非常适合 LLM Agent 使用。可交互元素会获得引用 ID（如 `@e1`、`@e2`），Agent 使用这些 ID 进行点击和输入。

核心能力：

- **多提供商云端执行** — Browserbase、Browser Use 或 Firecrawl，无需本地浏览器
- **本地 Chromium 系列集成** — 通过 CDP 连接到您正在运行的 Chrome、Brave、Chromium 或 Edge 浏览器进行实操浏览
- **内置隐匿** — 随机指纹、验证码解决、住宅代理（Browserbase）
- **会话隔离** — 每个任务拥有独立的浏览器会话
- **自动清理** — 不活跃的会话将在超时后关闭
- **视觉分析** — 截图 + AI 分析实现视觉理解

## 设置

:::tip Nous 订阅用户
如果您有付费的 [Nous Portal](https://portal.nousresearch.com) 订阅，可以通过 **[Tool Gateway](tool-gateway.md)** 使用浏览器自动化，无需单独的 API Key。运行 `hermes model` 或 `hermes tools` 来启用。
:::

### Browserbase 云端模式

要使用 Browserbase 托管的云端浏览器，添加以下配置：

```bash
# 添加到 ~/.hermes/.env
BROWSERBASE_API_KEY=***
BROWSERBASE_PROJECT_ID=your-project-id-here
```

在 [browserbase.com](https://browserbase.com) 获取您的凭证。

### Browser Use 云端模式

要使用 Browser Use 作为云端浏览器提供商，添加以下配置：

```bash
# 添加到 ~/.hermes/.env
BROWSER_USE_API_KEY=***
```

在 [browser-use.com](https://browser-use.com) 获取您的 API Key。Browser Use 通过其 REST API 提供云端浏览器。如果同时设置了 Browserbase 和 Browser Use 的凭证，Browserbase 将优先使用。

### Firecrawl 云端模式

要使用 Firecrawl 作为云端浏览器提供商，添加以下配置：

```bash
# 添加到 ~/.hermes/.env
FIRECRAWL_API_KEY=fc-***
```

在 [firecrawl.dev](https://firecrawl.dev) 获取您的 API Key。然后选择 Firecrawl 作为浏览器提供商：

```bash
hermes setup tools
# → Browser Automation → Firecrawl
```

可选设置：

```bash
# 自托管的 Firecrawl 实例（默认：https://api.firecrawl.dev）
FIRECRAWL_API_URL=http://localhost:3002

# 会话 TTL（秒）（默认：300）
FIRECRAWL_BROWSER_TTL=600
```

### 混合路由：公共 URL 走云端，LAN/localhost 走本地

当配置了云端提供商时，对于解析为私有/回环/LAN 地址的 URL（`localhost`、`127.0.0.1`、`192.168.x.x`、`10.x.x.x`、`172.16-31.x.x`、`*.local`、`*.lan`、`*.internal`、IPv6 回环地址 `::1`、链路本地地址 `169.254.x.x`），Hermes 会自动启动一个**本地 Chromium sidecar**。公共 URL 则继续在同一对话中使用云端提供商。

这解决了常见的"我在本地开发，但使用的是 Browserbase"的工作流场景——Agent 可以对 `http://localhost:3000` 上的仪表盘截图，同时抓取 `https://github.com`，无需切换提供商或禁用 SSRF 防护。云端提供商永远不会看到私有 URL。

此功能**默认开启**。要禁用它（所有 URL 都走配置的云端提供商，如之前的行为）：

```yaml
# ~/.hermes/config.yaml
browser:
  cloud_provider: browserbase
  auto_local_for_private_urls: false
```

禁用自动路由后，私有 URL 将被拒绝，并提示 `"Blocked: URL targets a private or internal address"`，除非您同时设置 `browser.allow_private_urls: true`（允许云端提供商尝试访问——但通常不会成功，因为 Browserbase 等无法访问您的 LAN）。

要求：本地 sidecar 使用与纯本地模式相同的 `agent-browser` CLI，因此您需要安装它（`hermes setup tools → Browser Automation` 会自动安装）。从公共 URL 导航后重定向到私有地址的情况仍然会被阻止（您不能利用重定向到内部的技巧通过公共路径访问您的 LAN）。

### Camofox 本地模式

[Camofox](https://github.com/jo-inc/camofox-browser) 是一个自托管的 Node.js 服务器，封装了 Camoufox（一个带有 C++ 指纹伪装功能的 Firefox 分支）。它提供本地反检测浏览，不依赖云端服务。

```bash
# 首先克隆 Camofox 浏览器服务器
git clone https://github.com/jo-inc/camofox-browser
cd camofox-browser

# 使用 Docker 构建并启动，采用默认容器设置
# （自动检测架构：M1/M2 上为 aarch64，Intel 上为 x86_64）
make up

# 停止并移除默认容器
make down

# 强制完全重建（例如，在升级 VERSION/RELEASE 之后）
make reset

# 仅下载二进制文件而不构建
make fetch

# 显式覆盖架构或版本
make up ARCH=x86_64
make up VERSION=135.0.1 RELEASE=beta.24
```

`make up` 会立即启动默认容器。如果您需要自定义运行时设置（如更大的 Node 堆内存、VNC 或持久化配置文件目录），请先构建镜像然后自行运行：

```bash
# 构建镜像而不启动默认容器
make build

# 启动时启用持久化、VNC 实时查看和更大的 Node 堆内存
mkdir -p ~/.camofox-docker
docker run -d \
  --name camofox-browser \
  --restart unless-stopped \
  -p 9377:9377 \
  -p 6080:6080 \
  -p 5901:5900 \
  -e CAMOFOX_PORT=9377 \
  -e ENABLE_VNC=1 \
  -e VNC_BIND=0.0.0.0 \
  -e VNC_RESOLUTION=1920x1080 \
  -e MAX_OLD_SPACE_SIZE=2048 \
  -v ~/.camofox-docker:/root/.camofox \
  camofox-browser:135.0.1-aarch64
```

启用 VNC 后，浏览器以有头模式运行，您可以在浏览器中通过 `http://localhost:6080`（noVNC）实时观看。您也可以使用原生 VNC 客户端连接到 `localhost:5901`。

如果您已经运行了 `make up`，在启动自定义容器之前先停止并移除默认容器：

```bash
make down
# 然后运行上述自定义 docker run 命令
```

然后在 `~/.hermes/.env` 中设置：

```bash
CAMOFOX_URL=http://localhost:9377
```

或者通过 `hermes tools` → Browser Automation → Camofox 进行配置。

当设置了 `CAMOFOX_URL` 时，所有浏览器工具将自动路由到 Camofox，而不是 Browserbase 或 agent-browser。

#### 持久化浏览器会话

默认情况下，每个 Camofox 会话都会获得一个随机身份——cookies 和登录状态不会在 Agent 重启后保留。要启用持久化浏览器会话，在 `~/.hermes/config.yaml` 中添加以下内容：

```yaml
browser:
  camofox:
    managed_persistence: true
```

然后完全重启 Hermes 使新配置生效。

:::warning 嵌套路径很重要
Hermes 读取的是 `browser.camofox.managed_persistence`，**而不是**顶级 `managed_persistence`。一个常见的错误是写：

```yaml
# ❌ 错误 — Hermes 会忽略此配置
managed_persistence: true
```

如果标志放在错误的路径，Hermes 会静默地回退到随机临时 `userId`，每次会话您的登录状态将会丢失。
:::

##### Hermes 会做什么
- 向 Camofox 发送一个确定性的、按配置文件范围划分的 `userId`，使服务器可以在不同会话之间重用同一个 Firefox 配置文件。
- 在清理时跳过服务器端的上下文销毁，这样 cookies 和登录状态可以在 Agent 任务之间保留。
- 将 `userId` 的范围限定为活跃的 Hermes 配置文件，因此不同的 Hermes 配置文件会获得不同的浏览器配置文件（配置文件隔离）。

##### Hermes 不会做什么
- 它不会强制 Camofox 服务器端的持久化。Hermes 仅发送一个稳定的 `userId`；服务器必须通过将该 `userId` 映射到持久化的 Firefox 配置文件目录来实现持久化。
- 如果您的 Camofox 服务器构建将每个请求都视为临时的（例如，总是调用 `browser.newContext()` 而不加载已存储的配置文件），Hermes 无法使这些会话持久化。请确保您运行的 Camofox 构建版本支持基于 userId 的配置文件持久化。

##### 验证是否生效

1. 启动 Hermes 和您的 Camofox 服务器。
2. 在浏览器任务中打开 Google（或任何登录站点）并手动登录。
3. 正常结束浏览器任务。
4. 启动一个新的浏览器任务。
5. 再次打开同一站点——您应该仍然是登录状态。

如果第 5 步您被登出了，说明 Camofox 服务器没有遵守稳定的 `userId`。请仔细检查您的配置路径，确认在编辑 `config.yaml` 后完全重启了 Hermes，并验证您的 Camofox 服务器版本是否支持按用户持久化配置文件。

##### 状态存储位置

Hermes 从按配置文件范围的目录 `~/.hermes/browser_auth/camofox/`（或非默认配置文件对应的 `$HERMES_HOME` 下的等效目录）派生出稳定的 `userId`。实际的浏览器配置文件数据存储在 Camofox 服务器端，以该 `userId` 为键。要完全重置持久化配置文件，请清除 Camofox 服务器上的数据并删除相应 Hermes 配置文件的状态目录。

#### 外部管理的 Camofox 会话

当另一个应用程序驱动可见的 Camofox 浏览器（桌面助手、自定义集成、另一个 Agent）时，可以将 Hermes 配置为在同一身份中操作，而不是生成自己隔离的配置文件。

有三个开关控制此行为：

| 设置 | 环境变量 | 效果 |
|---------|---------|--------|
| `browser.camofox.user_id` | `CAMOFOX_USER_ID` | Hermes 在创建标签页时使用的 Camofox `userId`。设置此项会使会话进入"外部管理"模式。 |
| `browser.camofox.session_key` | `CAMOFOX_SESSION_KEY` | 创建标签页时发送的 `sessionKey`（也称为 `listItemId`）。用于在采用时匹配现有标签页。如果未设置，默认为每个任务的值。 |
| `browser.camofox.adopt_existing_tab` | `CAMOFOX_ADOPT_EXISTING_TAB` | 当为 true 时，Hermes 在首次使用时调用 `GET /tabs?userId=<user_id>` 并优先复用现有标签页，而不是创建新的。 |

环境变量优先于 `config.yaml`。两种形式均可：

```yaml
browser:
  camofox:
    user_id: shared-camofox
    session_key: visible-tab
    adopt_existing_tab: true
```

```bash
CAMOFOX_USER_ID=shared-camofox
CAMOFOX_SESSION_KEY=visible-tab
CAMOFOX_ADOPT_EXISTING_TAB=true
```

**设置 `user_id` 后的变化：**

- Hermes 在任务结束时跳过破坏性清理（与 `managed_persistence: true` 相同）。其他应用的标签页/cookies/配置文件将得以保留。
- Hermes **不会**调用 `DELETE /sessions/<user_id>`——该端点会清除所有用户数据，如果执行它将摧毁外部应用的会话。

**标签页采用的工作方式（当 `adopt_existing_tab: true` 时）：**

1. 在进程启动后的首次浏览器工具调用时，Hermes 发送 `GET /tabs?userId=<user_id>`（5 秒超时）。
2. 如果响应中任何标签页的 `listItemId == session_key`，Hermes 采用该组中最近创建的那一个。
3. 否则，Hermes 采用该用户最近创建的标签页（任意 `listItemId`）。
4. 如果不存在标签页或请求失败，Hermes 回退到在下一次操作时创建新标签页。

采用仅在会话的 `tab_id` 被填充之前触发。如果外部应用在运行中途关闭了被采用的标签页，下一次浏览器工具调用将显示 Camofox 错误——Hermes 不会在每次调用时重新轮询新标签页。

**选择 `session_key`：** 如果您希望 Hermes 可靠地附加到*特定*的现有标签页，请将 `session_key` 设置为外部应用在创建该标签页时使用的 `listItemId`。如果您不设置 `session_key` 而只设置 `user_id`，Hermes 会生成一个按任务分配的 `session_key`（`task_<id>`）——Hermes 将与外部应用共享 cookies 和配置文件，但会打开自己的标签页与其并存，而不是复用一个。

**并发注意事项：** 外部应用和 Hermes 可以同时驱动同一个 Camofox `userId`，但 Camofox 不会在客户端之间协调每个标签页的焦点。请在应用层面协调所有权（例如，在 Hermes 运行时外部应用暂停）。

#### VNC 实时查看

当 Camofox 以有头模式运行（带有可见的浏览器窗口）时，它会在健康检查响应中暴露一个 VNC 端口。Hermes 会自动发现此端口，并在导航响应中包含 VNC URL，这样 Agent 可以分享一个链接供您实时观看浏览器操作。

### 通过 CDP 连接到本地 Chromium 系列浏览器（`/browser connect`）

除了云端提供商，您还可以通过 Chrome DevTools Protocol (CDP) 将 Hermes 的浏览器工具附加到您自己正在运行的 Chrome、Brave、Chromium 或 Edge 实例。当您想要实时查看 Agent 的操作、与需要您自己的 cookies/会话的页面交互，或避免云端浏览器费用时，这非常有用。

:::note
`/browser connect` 是一个**交互式 CLI 斜杠命令**——它不会通过网关分发。如果您尝试在 WebUI、Telegram、Discord 或其他网关聊天中运行它，消息将以纯文本形式发送给 Agent，命令不会执行。请从终端启动 Hermes（`hermes` 或 `hermes chat`）并在那里执行 `/browser connect`。
:::

在 CLI 中，使用：

```
/browser connect                 # 自动启动/连接到 http://127.0.0.1:9222 上的本地 Chromium 系列浏览器
/browser connect ws://host:port  # 连接到特定的 CDP 端点
/browser status                  # 检查当前连接状态
/browser disconnect              # 断开连接并返回云端/本地模式
```

如果浏览器尚未以远程调试模式运行，Hermes 会尝试自动启动一个受支持的 Chromium 系列浏览器，并添加 `--remote-debugging-port=9222`。检测范围包括 Brave、Google Chrome、Chromium 和 Microsoft Edge，以及常见的 Linux 安装路径，如 `/opt/brave-bin/brave` 和 `/snap/bin/brave`。

:::tip
要手动启动一个启用 CDP 的 Chromium 系列浏览器，请使用专用的 user-data-dir，这样即使已有浏览器以您的正常配置文件运行，调试端口也能实际启动：

```bash
# Linux — Brave
brave-browser \
  --remote-debugging-port=9222 \
  --user-data-dir=$HOME/.hermes/chrome-debug \
  --no-first-run \
  --no-default-browser-check &

# Linux — Google Chrome
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=$HOME/.hermes/chrome-debug \
  --no-first-run \
  --no-default-browser-check &

# macOS — Brave
"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.hermes/chrome-debug" \
  --no-first-run \
  --no-default-browser-check &

# macOS — Google Chrome
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.hermes/chrome-debug" \
  --no-first-run \
  --no-default-browser-check &
```

然后启动 Hermes CLI 并运行 `/browser connect`。

**为什么需要 `--user-data-dir`？** 如果不使用它，在已有常规实例运行时启动 Chromium 系列浏览器通常会在现有进程上打开一个新窗口——而该现有进程并非以 `--remote-debugging-port` 启动，因此端口 9222 永远不会打开。专用的 user-data-dir 会强制启动一个全新的浏览器进程，使调试端口实际监听。`--no-first-run --no-default-browser-check` 为新的配置文件跳过首次启动向导。
:::

通过 CDP 连接后，所有浏览器工具（`browser_navigate`、`browser_click` 等）都将在您的实时浏览器实例上操作，而不是启动云端会话。

### WSL2 + Windows Chrome：优先使用 MCP 而非 `/browser connect`

如果 Hermes 在 WSL2 内部运行，而您想要控制的 Chrome 窗口在 Windows 主机上运行，`/browser connect` 通常不是最佳方案。

原因：

- `/browser connect` 期望 Hermes 自身能够访问可用的 CDP 端点
- 现代 Chrome 的实时调试会话通常暴露一个主机本地的端点，不像经典 `9222` 端口那样可以直接从 WSL 访问
- 即使 Windows Chrome 可调试，最简洁的集成方式通常是让 Windows 端的 browser MCP 服务器附加到 Chrome，并让 Hermes 与该 MCP 服务器通信

对于这种设置，推荐通过 Hermes MCP 支持使用 `chrome-devtools-mcp`。

请参阅 MCP 指南了解实际设置：

- [在 Hermes 中使用 MCP](../../guides/use-mcp-with-hermes.md#wsl2-bridge-hermes-in-wsl-to-windows-chrome)

### 本地浏览器模式

如果您**没有**设置任何云端凭证，也没有使用 `/browser connect`，Hermes 仍然可以通过由 `agent-browser` 驱动的本地 Chromium 安装来使用浏览器工具。

### 可选环境变量

```bash
# 用于更好验证码解决的住宅代理（默认："true"）
BROWSERBASE_PROXIES=true

# 使用自定义 Chromium 的高级隐匿——需要 Scale 计划（默认："false"）
BROWSERBASE_ADVANCED_STEALTH=false

# 断开连接后会话重连——需要付费计划（默认："true"）
BROWSERBASE_KEEP_ALIVE=true

# 自定义会话超时（毫秒）（默认：项目默认值）
# 示例：600000（10分钟）、1800000（30分钟）
BROWSERBASE_SESSION_TIMEOUT=600000

# 自动清理前的不活跃超时（秒）（默认：120）
BROWSER_INACTIVITY_TIMEOUT=120

# 额外的 Chromium 启动标志（以逗号或换行分隔）。Hermes 在检测到
# root 或受 AppArmor 限制的非特权用户命名空间（Ubuntu 23.10+、
# DGX Spark、许多容器镜像）时会自动注入
# `--no-sandbox,--disable-dev-shm-usage`，因此大多数用户无需设置此项。
# 仅在您需要 Hermes 不会自动添加的标志时手动设置；设置此项会禁用自动注入。
AGENT_BROWSER_ARGS=--no-sandbox
```

### 安装 agent-browser CLI

```bash
npm install -g agent-browser
# 或在仓库中本地安装：
npm install
```

:::info
`browser` 工具集必须包含在您配置的 `toolsets` 列表中，或通过 `hermes config set toolsets '["hermes-cli", "browser"]'` 启用。
:::

## 可用工具

### `browser_navigate`

导航到指定 URL。必须在任何其他浏览器工具之前调用。初始化 Browserbase 会话。

```
导航到 https://github.com/NousResearch
```

:::tip
对于简单的信息检索，优先使用 `web_search` 或 `web_extract`——它们更快更便宜。当您需要**与页面交互**（点击按钮、填写表单、处理动态内容）时才使用浏览器工具。
:::

### `browser_snapshot`

获取当前页面无障碍树的文本快照。返回带有引用 ID（如 `@e1`、`@e2`）的可交互元素，供 `browser_click` 和 `browser_type` 使用。

- **`full=false`**（默认）：紧凑视图，仅显示可交互元素
- **`full=true`**：完整页面内容

超过 8000 字符的快照将由 LLM 自动摘要。

### `browser_click`

点击快照中由其引用 ID 标识的元素。

```
点击 @e5 以按下"Sign In"按钮
```

### `browser_type`

在输入字段中输入文本。先清除字段内容，然后输入新文本。

```
在搜索字段 @e3 中输入"hermes agent"
```

### `browser_scroll`

向上或向下滚动页面以显示更多内容。

```
向下滚动以查看更多结果
```

### `browser_press`

按下键盘按键。适用于提交表单或导航。

```
按 Enter 提交表单
```

支持的按键：`Enter`、`Tab`、`Escape`、`ArrowDown`、`ArrowUp` 等。

### `browser_back`

导航回浏览器历史记录中的上一页。

### `browser_get_images`

列出当前页面上所有图片的 URL 和 alt 文本。适用于查找需要分析的图片。

### `browser_vision`

截取屏幕截图并通过视觉 AI 进行分析。当文本快照无法捕获重要的视觉信息时使用——特别适用于验证码、复杂布局或视觉验证挑战。

截图会被持久保存，文件路径与 AI 分析结果一起返回。在消息平台（Telegram、Discord、Slack、WhatsApp）上，您可以让 Agent 分享截图——它将通过 `MEDIA:` 机制作为原生图片附件发送。

```
这个页面上的图表显示什么？
```

截图存储在 `~/.hermes/cache/screenshots/` 中，24 小时后自动清理。

### `browser_console`

获取当前页面的浏览器控制台输出（log/warn/error 消息）和未捕获的 JavaScript 异常。对于检测无障碍树中不显示的静默 JS 错误至关重要。

```
检查浏览器控制台中是否有 JavaScript 错误
```

使用 `clear=True` 在读取后清除控制台，使后续调用只显示新消息。

当使用 `expression` 参数调用时，`browser_console` 还可以执行 JavaScript——与 DevTools 控制台形状相同，结果以解析后的形式返回（JSON 可序列化的对象变为 dict；原始值保持原始类型）。

```
browser_console(expression="document.querySelector('h1').textContent")
browser_console(expression="JSON.stringify(performance.timing)")
```

当 CDP supervisor 对当前会话处于活跃状态时（通常适用于对支持 CDP 的后端运行了 `browser_navigate` 的任何会话），表达式通过 supervisor 的持久 WebSocket 执行——没有子进程启动开销。否则回退到标准的 agent-browser CLI 路径。行为完全相同；只有延迟不同。

### `browser_cdp`

原始 Chrome DevTools Protocol 透传——当其他工具无法覆盖浏览器操作时的万能后备方案。用于原生对话框处理、iframe 范围内的表达式求值、cookie/网络控制，或 Agent 需要的任何 CDP 命令。

**仅在会话启动时可访问 CDP 端点时可用**——即 `/browser connect` 已附加到正在运行的 Chrome、Brave、Chromium 或 Edge 浏览器，或在 `config.yaml` 中设置了 `browser.cdp_url`。默认的本地 agent-browser 模式、Camofox 和云端提供商（Browserbase、Browser Use、Firecrawl）目前不向此工具暴露 CDP——云端提供商有每个会话的 CDP URL，但实时会话路由是后续工作。

**CDP 方法参考：** https://chromedevtools.github.io/devtools-protocol/ —— Agent 可以通过 `web_extract` 提取特定方法页面来查找参数和返回格式。

常见用法：

```
# 列出标签页（浏览器级别，不需要 target_id）
browser_cdp(method="Target.getTargets")

# 处理标签页上的原生 JS 对话框
browser_cdp(method="Page.handleJavaScriptDialog",
            params={"accept": true, "promptText": ""},
            target_id="<tabId>")

# 在特定标签页中执行 JS
browser_cdp(method="Runtime.evaluate",
            params={"expression": "document.title", "returnByValue": true},
            target_id="<tabId>")

# 获取所有 cookies
browser_cdp(method="Network.getAllCookies")
```

浏览器级别的方法（`Target.*`、`Browser.*`、`Storage.*`）省略 `target_id`。页面级别的方法（`Page.*`、`Runtime.*`、`DOM.*`、`Emulation.*`）需要通过 `Target.getTargets` 获取 `target_id`。每次无状态调用是独立的——调用之间不会持久化会话。

**跨域 iframe：** 传入 `frame_id`（来自 `browser_snapshot.frame_tree.children[]` 中 `is_oopif=true` 的项），通过 supervisor 的实时会话将 CDP 调用路由到该 iframe。这是在 Browserbase 上对跨域 iframe 内部执行 `Runtime.evaluate` 的方式，因为无状态 CDP 连接会遇到签名 URL 过期问题。示例：

```
browser_cdp(
  method="Runtime.evaluate",
  params={"expression": "document.title", "returnByValue": True},
  frame_id="<frame_id from browser_snapshot>",
)
```

同源 iframe 不需要 `frame_id`——可以直接从顶级 `Runtime.evaluate` 使用 `document.querySelector('iframe').contentDocument`。

### `browser_dialog`

响应原生 JS 对话框（`alert` / `confirm` / `prompt` / `beforeunload`）。在此工具出现之前，对话框会静默地阻塞页面的 JavaScript 线程，后续的 `browser_*` 调用会挂起或抛出异常；现在 Agent 可以在 `browser_snapshot` 输出中看到待处理的对话框并显式响应。

**工作流程：**
1. 调用 `browser_snapshot`。如果有对话框阻塞页面，它将显示为 `pending_dialogs: [{"id": "d-1", "type": "alert", "message": "..."}]`。
2. 调用 `browser_dialog(action="accept")` 或 `browser_dialog(action="dismiss")`。对于 `prompt()` 对话框，传入 `prompt_text="..."` 来提供响应。
3. 重新快照——`pending_dialogs` 为空；页面的 JS 线程已恢复。

**检测是自动进行的**，通过持久 CDP supervisor 实现——每个任务一个 WebSocket，订阅 Page/Runtime/Target 事件。supervisor 还会在快照中填充 `frame_tree` 字段，以便 Agent 查看当前页面的 iframe 结构，包括跨域（OOPIF）iframe。

**可用性矩阵：**

| 后端 | 通过 `pending_dialogs` 检测 | 响应（`browser_dialog` 工具） |
|---|---|---|
| 本地 Chrome 通过 `/browser connect` 或 `browser.cdp_url` | ✓ | ✓ 完整工作流 |
| Browserbase | ✓ | ✓ 完整工作流（通过注入的 XHR bridge） |
| Camofox / 默认本地 agent-browser | ✗ | ✗（无 CDP 端点） |

**在 Browserbase 上的工作方式。** Browserbase 的 CDP 代理会在服务器端约 10ms 内自动关闭真正的原生对话框，因此我们无法使用 `Page.handleJavaScriptDialog`。supervisor 通过 `Page.addScriptToEvaluateOnNewDocument` 注入一个小脚本，使用同步 XHR 覆盖 `window.alert`/`confirm`/`prompt`。我们通过 `Fetch.enable` 拦截这些 XHR——页面的 JS 线程在 XHR 上保持阻塞，直到我们调用 `Fetch.fulfillRequest` 并返回 Agent 的响应。`prompt()` 的返回值原样回传到页面 JS 中。

**对话框策略** 在 `config.yaml` 的 `browser.dialog_policy` 下配置：

| 策略 | 行为 |
|--------|----------|
| `must_respond`（默认） | 捕获、在快照中显示、等待显式的 `browser_dialog()` 调用。在 `browser.dialog_timeout_s`（默认 300 秒）后安全自动关闭，以防止有问题的 Agent 永久停滞。 |
| `auto_dismiss` | 捕获、立即关闭。Agent 仍可在 `browser_state` 历史中看到对话框，但无需采取行动。 |
| `auto_accept` | 捕获、立即接受。用于浏览带有激进 `beforeunload` 提示的页面时非常有用。 |

**Frame tree** 在 `browser_snapshot.frame_tree` 中限制为 30 个 frame 和 OOPIF 深度 2，以在广告密集的页面上保持负载可控。当达到限制时，会显示 `truncated: true` 标志；需要完整树的 Agent 可以使用 `browser_cdp` 配合 `Page.getFrameTree`。

## 实际示例

### 填写网页表单

```
用户：在 example.com 上用我的邮箱 john@example.com 注册账户

Agent 工作流程：
1. browser_navigate("https://example.com/signup")
2. browser_snapshot()  → 看到带有引用的表单字段
3. browser_type(ref="@e3", text="john@example.com")
4. browser_type(ref="@e5", text="SecurePass123")
5. browser_click(ref="@e8")  → 点击"Create Account"
6. browser_snapshot()  → 确认成功
```

### 研究动态内容

```
用户：GitHub 上现在热门的仓库有哪些？

Agent 工作流程：
1. browser_navigate("https://github.com/trending")
2. browser_snapshot(full=true)  → 读取热门仓库列表
3. 返回格式化结果
```

## 会话录制

自动将浏览器会话录制为 WebM 视频文件：

```yaml
browser:
  record_sessions: true  # 默认：false
```

启用后，录制将在首次 `browser_navigate` 时自动开始，并在会话关闭时保存到 `~/.hermes/browser_recordings/`。在本地和云端（Browserbase）模式均可使用。超过 72 小时的录制文件会自动清理。

## 隐匿特性

Browserbase 提供自动隐匿能力：

| 特性 | 默认值 | 说明 |
|---------|---------|-------|
| 基础隐匿 | 始终开启 | 随机指纹、视口随机化、验证码解决 |
| 住宅代理 | 开启 | 通过住宅 IP 路由以获得更好的访问能力 |
| 高级隐匿 | 关闭 | 自定义 Chromium 构建，需要 Scale 计划 |
| Keep Alive | 开启 | 网络波动后的会话重连 |

:::note
如果付费功能在您的计划中不可用，Hermes 会自动回退——首先禁用 `keepAlive`，然后是代理——因此在免费计划上浏览仍然可以正常工作。
:::

## 会话管理

- 每个任务通过 Browserbase 获得隔离的浏览器会话
- 会话在不活跃后自动清理（默认：2 分钟）
- 后台线程每 30 秒检查一次过时会话
- 进程退出时执行紧急清理以防止孤立会话
- 会话通过 Browserbase API 释放（`REQUEST_RELEASE` 状态）

## 限制

- **基于文本的交互** — 依赖无障碍树而非像素坐标
- **快照大小** — 大页面可能在 8000 字符处截断或由 LLM 摘要
- **会话超时** — 云端会话根据您的提供商计划设置过期
- **成本** — 云端会话会消耗提供商额度；对话结束或不活跃后会话会自动清理。使用 `/browser connect` 进行免费的本地浏览。
- **不支持文件下载** — 无法从浏览器下载文件
