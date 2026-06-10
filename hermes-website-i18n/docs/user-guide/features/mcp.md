---
sidebar_position: 4
title: "MCP（模型上下文协议）"
description: "通过 MCP 将 Hermes Agent 连接到外部工具服务器 — 并精确控制 Hermes 加载哪些 MCP 工具"
---

# MCP（模型上下文协议）

MCP 让 Hermes Agent 能够连接到外部工具服务器，使 Agent 可以使用 Hermes 本身之外的工具 — GitHub、数据库、文件系统、浏览器栈、内部 API 等等。

如果你曾经想让 Hermes 使用一个已经存在于其他地方的工具，MCP 通常是最简洁的实现方式。

## MCP 能带给你什么

- 无需先编写原生 Hermes 工具即可访问外部工具生态
- 在同一个配置中同时支持本地 stdio 服务器和远程 HTTP MCP 服务器
- 启动时自动发现并注册工具
- 当服务器支持时，提供 MCP 资源和提示的工具封装
- 逐服务器过滤，只暴露你希望 Hermes 看到的 MCP 工具

## 快速开始

1. 安装 MCP 支持（如果使用标准安装脚本，已默认包含）：

```bash
cd ~/.hermes/hermes-agent
uv pip install -e ".[mcp]"
```

2. 在 `~/.hermes/config.yaml` 中添加一个 MCP 服务器：

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

3. 启动 Hermes：

```bash
hermes chat
```

4. 让 Hermes 使用 MCP 支持的能力。

例如：

```text
列出 /home/user/projects 中的文件，并总结仓库结构。
```

Hermes 将发现 MCP 服务器的工具，并像使用其他工具一样使用它们。

## 两种 MCP 服务器

### Stdio 服务器

Stdio 服务器作为本地子进程运行，通过 stdin/stdout 通信。

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
```

在以下情况使用 stdio 服务器：
- 服务器已安装在本地
- 你想要低延迟访问本地资源
- 你正在按照 MCP 服务器文档操作，文档中展示了 `command`、`args` 和 `env`

### HTTP 服务器

HTTP MCP 服务器是 Hermes 直接连接的远程端点。

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer ***"
```

在以下情况使用 HTTP 服务器：
- MCP 服务器托管在其他地方
- 你的组织对外暴露了内部 MCP 端点
- 你不希望 Hermes 为该集成启动本地子进程

## 基本配置参考

Hermes 从 `~/.hermes/config.yaml` 的 `mcp_servers` 下读取 MCP 配置。

### 通用配置项

| 配置项 | 类型 | 含义 |
|---|---|---|
| `command` | string | stdio MCP 服务器的可执行文件 |
| `args` | list | stdio 服务器的参数列表 |
| `env` | mapping | 传递给 stdio 服务器的环境变量 |
| `url` | string | HTTP MCP 端点地址 |
| `headers` | mapping | 远程服务器的 HTTP 请求头 |
| `timeout` | number | 工具调用超时时间 |
| `connect_timeout` | number | 初始连接超时时间 |
| `enabled` | bool | 若为 `false`，Hermes 会完全跳过该服务器 |
| `supports_parallel_tool_calls` | bool | 若为 `true`，该服务器的工具可以并发执行 |
| `tools` | mapping | 逐服务器工具过滤和工具封装策略 |

### 最小化 stdio 示例

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
```

### 最小化 HTTP 示例

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.internal.example.com"
    headers:
      Authorization: "Bearer ***"
```

## 内置预设

对于知名的 MCP 服务器，`hermes mcp add` 接受一个 `--preset` 标志，自动填写传输细节，这样你就不需要自己去查找 command 和 args。预设只提供默认值 — 你在同一条命令中传入的其他任何配置（环境变量、请求头、过滤规则）仍然优先生效。

| 预设名称 | 配置内容 |
|---|---|
| `codex` | Codex CLI 的 MCP 服务器（通过 stdio 运行 `codex mcp-server`）。要求 PATH 中有 `codex` CLI。 |

```bash
# 一行命令将 Codex CLI 添加为 MCP 服务器
hermes mcp add codex --preset codex
```

这相当于写入了：

```yaml
mcp_servers:
  codex:
    command: "codex"
    args: ["mcp-server"]
```

你可以选择任意本地名称（`hermes mcp add my-codex --preset codex` 也可以）；预设只提供 `command`/`args` 的默认值。

## Hermes 如何注册 MCP 工具

Hermes 为 MCP 工具添加前缀，避免与内置名称冲突：

```text
mcp_<服务器名称>_<工具名称>
```

示例：

| 服务器 | MCP 工具 | 注册名称 |
|---|---|---|
| `filesystem` | `read_file` | `mcp_filesystem_read_file` |
| `github` | `create-issue` | `mcp_github_create_issue` |
| `my-api` | `query.data` | `mcp_my_api_query_data` |

在实际使用中，你通常不需要手动调用带前缀的名称 — Hermes 会看到该工具，并在正常推理过程中自行选择使用。

## MCP 工具封装

当服务器支持时，Hermes 还会注册围绕 MCP 资源和提示的工具封装：

- `list_resources`
- `read_resource`
- `list_prompts`
- `get_prompt`

这些封装按每个服务器注册，使用相同的前缀模式，例如：

- `mcp_github_list_resources`
- `mcp_github_get_prompt`

### 重要说明

这些工具封装现在是能力感知的：
- Hermes 仅在 MCP 会话确实支持资源操作时才注册资源相关封装
- Hermes 仅在 MCP 会话确实支持提示操作时才注册提示相关封装

因此，一个只暴露可调用工具但没有资源/提示功能的服务器，不会获得这些额外的封装工具。

## 逐服务器过滤

你可以控制每个 MCP 服务器向 Hermes 提供哪些工具，从而对工具命名空间进行精细化管理。

### 完全禁用某个服务器

```yaml
mcp_servers:
  legacy:
    url: "https://mcp.legacy.internal"
    enabled: false
```

当 `enabled: false` 时，Hermes 完全跳过该服务器，甚至不尝试连接。

### 白名单模式：仅包含指定的服务器工具

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [create_issue, list_issues]
```

只有这些 MCP 服务器工具会被注册。

### 黑名单模式：排除指定的服务器工具

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    tools:
      exclude: [delete_customer]
```

除了被排除的工具外，所有服务器工具都会被注册。

### 优先级规则

如果同时配置了两者：

```yaml
tools:
  include: [create_issue]
  exclude: [create_issue, delete_issue]
```

`include` 优先。

### 同时过滤工具封装

你也可以单独禁用 Hermes 添加的工具封装：

```yaml
mcp_servers:
  docs:
    url: "https://mcp.docs.example.com"
    tools:
      prompts: false
      resources: false
```

这意味着：
- `tools.resources: false` 禁用 `list_resources` 和 `read_resource`
- `tools.prompts: false` 禁用 `list_prompts` 和 `get_prompt`

### 完整示例

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [create_issue, list_issues, search_code]
      prompts: false

  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer]
      resources: false

  legacy:
    url: "https://mcp.legacy.internal"
    enabled: false
```

## 如果所有工具都被过滤掉了会怎样？

如果你的配置过滤掉了所有可调用工具，并禁用或省略了所有支持的工具封装，Hermes 不会为该服务器创建空的运行时 MCP 工具集。

这样能保持工具列表的整洁。

## 运行时行为

### 发现时机

Hermes 在启动时发现 MCP 服务器，并将其工具注册到常规工具注册表中。

### 动态工具发现

MCP 服务器可以通过发送 `notifications/tools/list_changed` 通知来告知 Hermes 其可用工具在运行时发生了变化。当 Hermes 收到此通知时，会自动重新获取该服务器的工具列表并更新注册表 — 无需手动执行 `/reload-mcp`。

这对于那些能力会动态变化的 MCP 服务器非常有用（例如，某个服务器在加载新的数据库模式时会添加工具，或在某个服务下线时会移除工具）。

刷新操作受锁保护，因此同一服务器发来的快速连续通知不会导致重叠刷新。提示和资源变更通知（`prompts/list_changed`、`resources/list_changed`）会被接收，但暂不响应。

### 重新加载

如果你修改了 MCP 配置，请使用：

```text
/reload-mcp
```

这会从配置文件重新加载 MCP 服务器并刷新可用工具列表。对于服务器自身推送的运行时工具变更，请参见上方的[动态工具发现](#动态工具发现)。

### 工具集

每个配置的 MCP 服务器在至少贡献一个已注册工具时，也会创建一个运行时工具集：

```text
mcp-<服务器名称>
```

这使得在工具集层面理解 MCP 服务器变得更加容易。

## 安全模型

### Stdio 环境变量过滤

对于 stdio 服务器，Hermes 不会盲目传递你完整的 shell 环境。

只会传递显式配置的 `env` 以及一个安全基线。这减少了意外的密钥泄露。

### 配置层面的暴露控制

新的过滤支持也是一种安全控制手段：
- 禁用你不想让模型看到的危险工具
- 对敏感服务器仅暴露最小化的白名单
- 当你不希望暴露该功能面时，禁用资源/提示封装

## 示例用例

### GitHub 服务器，只暴露最小化的 Issue 管理功能

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***"
    tools:
      include: [list_issues, create_issue, update_issue]
      prompts: false
      resources: false
```

像这样使用：

```text
显示所有标记为 bug 的未关闭 Issue，然后为 MCP 重连不稳定的问题起草一个新 Issue。
```

### Stripe 服务器，移除危险操作

```yaml
mcp_servers:
  stripe:
    url: "https://mcp.stripe.com"
    headers:
      Authorization: "Bearer ***"
    tools:
      exclude: [delete_customer, refund_payment]
```

像这样使用：

```text
查看最近 10 笔失败的付款，并总结常见的失败原因。
```

### 文件系统服务器，限定在单个项目根目录

```yaml
mcp_servers:
  project_fs:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/my-project"]
```

像这样使用：

```text
检查项目根目录，并说明目录布局。
```

## 故障排查

### MCP 服务器无法连接

检查：

```bash
# 验证 MCP 依赖已安装（标准安装中已默认包含）
cd ~/.hermes/hermes-agent && uv pip install -e ".[mcp]"

node --version
npx --version
```

然后验证你的配置并重启 Hermes。

### 工具未出现

可能的原因：
- 服务器连接失败
- 工具发现失败
- 你的过滤配置排除了这些工具
- 该服务器上不存在相应的工具封装能力
- 服务器被 `enabled: false` 禁用

如果你是有意过滤的，这是预期行为。

### 为什么资源或提示封装没有出现？

因为 Hermes 现在只在同时满足以下两个条件时才注册这些封装：
1. 你的配置允许它们
2. 服务器会话确实支持该能力

这是有意为之，能保持工具列表的真实性。

## 并行工具调用

默认情况下，MCP 工具按顺序执行 — 一次一个。如果你的 MCP 服务器暴露了可以安全并发执行的工具（例如只读查询、独立的 API 调用），你可以选择开启并行执行：

```yaml
mcp_servers:
  docs:
    command: "docs-server"
    supports_parallel_tool_calls: true
```

当 `supports_parallel_tool_calls` 为 `true` 时，Hermes 可以在单个工具调用批次中同时执行该服务器的多个工具，就像它对内置只读工具（web_search、read_file 等）的处理一样。

:::caution
仅在 MCP 服务器的工具可以安全地同时运行时才启用并行调用。如果工具涉及对共享状态、文件、数据库或外部资源的读写操作，在启用此设置之前，请仔细审查读写竞争条件。
:::

## MCP 采样支持

MCP 服务器可以通过 `sampling/createMessage` 协议请求 Hermes 进行 LLM 推理。这允许 MCP 服务器请求 Hermes 代为生成文本 — 适用于需要 LLM 能力但没有自己模型访问权限的服务器。

采样功能**默认启用**，适用于所有 MCP 服务器（当 MCP SDK 支持时）。通过 `sampling` 配置项按服务器进行配置：

```yaml
mcp_servers:
  my_server:
    command: "my-mcp-server"
    sampling:
      enabled: true            # 启用采样（默认：true）
      model: "openai/gpt-4o"  # 覆盖采样请求使用的模型（可选）
      max_tokens_cap: 4096     # 每次采样响应的最大 token 数（默认：4096）
      timeout: 30              # 每次请求的超时时间（秒）（默认：30）
      max_rpm: 10              # 速率限制：每分钟最大请求数（默认：10）
      max_tool_rounds: 5       # 采样循环中最大工具调用轮数（默认：5）
      allowed_models: []       # 服务器可请求的模型名称白名单（空 = 允许任意）
      log_level: "info"        # 审计日志级别：debug、info 或 warning（默认：info）
```

采样处理器包含滑动窗口速率限制器、逐请求超时和工具循环深度限制，以防止用量失控。每个服务器实例会跟踪指标（请求次数、错误次数、消耗的 token 数）。

为特定服务器禁用采样：

```yaml
mcp_servers:
  untrusted_server:
    url: "https://mcp.example.com"
    sampling:
      enabled: false
```

## 将 Hermes 作为 MCP 服务器运行

除了连接**到** MCP 服务器，Hermes 还可以**作为** MCP 服务器。这允许其他支持 MCP 的 Agent（Claude Code、Cursor、Codex 或任何 MCP 客户端）使用 Hermes 的消息传递能力 — 列出会话、读取消息历史记录，以及跨所有已连接平台发送消息。

### 适用场景

- 你希望 Claude Code、Cursor 或其他编程 Agent 通过 Hermes 发送和读取 Telegram/Discord/Slack 消息
- 你想要一个单一的 MCP 服务器，同时桥接 Hermes 所有已连接的消息平台
- 你已经有一个运行中的 Hermes 网关，且已连接了多个平台

### 快速开始

```bash
hermes mcp serve
```

这会启动一个 stdio MCP 服务器。由 MCP 客户端（而不是你）管理进程生命周期。

### MCP 客户端配置

将 Hermes 添加到你的 MCP 客户端配置中。例如，在 Claude Code 的 `~/.claude/claude_desktop_config.json` 中：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "hermes",
      "args": ["mcp", "serve"]
    }
  }
}
```

或者如果你将 Hermes 安装在特定位置：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "/home/user/.hermes/hermes-agent/venv/bin/hermes",
      "args": ["mcp", "serve"]
    }
  }
}
```

### 可用工具

MCP 服务器暴露了 10 个工具，对应 OpenClaw 的频道桥接功能以及一个 Hermes 专属的频道浏览器：

| 工具 | 描述 |
|------|------|
| `conversations_list` | 列出活跃的消息会话。可按平台过滤或按名称搜索。 |
| `conversation_get` | 通过会话键获取某个会话的详细信息。 |
| `messages_read` | 读取某个会话的最近消息历史记录。 |
| `attachments_fetch` | 从特定消息中提取非文本附件（图片、媒体）。 |
| `events_poll` | 从指定游标位置开始轮询新的会话事件。 |
| `events_wait` | 长轮询/阻塞直到下一个事件到达（近实时）。 |
| `messages_send` | 通过平台发送消息（例如 `telegram:123456`、`discord:#general`）。 |
| `channels_list` | 列出跨所有平台的可用消息发送目标。 |
| `permissions_list_open` | 列出本次桥接会话期间观察到的待处理审批请求。 |
| `permissions_respond` | 允许或拒绝某个待处理的审批请求。 |

### 事件系统

MCP 服务器包含一个实时事件桥接器，会轮询 Hermes 的会话数据库以获取新消息。这使 MCP 客户端能够近实时地感知传入的会话：

```
# 轮询新事件（非阻塞）
events_poll(after_cursor=0)

# 等待下一个事件（阻塞，最长达指定超时）
events_wait(after_cursor=42, timeout_ms=30000)
```

事件类型：`message`、`approval_requested`、`approval_resolved`

事件队列是内存中的，在桥接器连接时启动。更早的消息可以通过 `messages_read` 获取。

### 选项

```bash
hermes mcp serve              # 普通模式
hermes mcp serve --verbose    # 在 stderr 上输出调试日志
```

### 工作原理

MCP 服务器直接从 Hermes 的会话存储（`~/.hermes/sessions/sessions.json` 和 SQLite 数据库）中读取会话数据。一个后台线程轮询数据库以获取新消息，并维护一个内存中的事件队列。对于发送消息，它使用与 Hermes Agent 本身相同的 `send_message` 基础设施。

读取操作（列出会话、读取历史记录、轮询事件）不需要网关正在运行。发送操作则需要网关正在运行，因为平台适配器需要活跃的连接。

### 当前限制

- 内嵌的 `hermes mcp serve` 目前只暴露一个 **stdio-only** 的 MCP 服务器。如果你需要 HTTP MCP 服务器，请运行一个单独的适配器 — 或者，更常见的做法是使用 Hermes 的 MCP **客户端**端，它已经同时支持 stdio 和 HTTP（在 `mcp_servers.yaml` / `config.yaml` 中使用 `url` + `headers`；参见上方的 [HTTP 服务器](#http-服务器)）。
- 事件轮询间隔约 200ms，通过基于 mtime 优化的数据库轮询实现（文件未变化时跳过工作）
- 尚不支持 `claude/channel` 推送通知协议
- `messages_send` 仅支持纯文本发送（不支持发送媒体/附件）

## 相关文档

- [将 MCP 与 Hermes 结合使用](/docs/guides/use-mcp-with-hermes)
- [CLI 命令](/docs/reference/cli-commands)
- [斜杠命令](/docs/reference/slash-commands)
- [常见问题](/docs/reference/faq)
