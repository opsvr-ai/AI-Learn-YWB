---
sidebar_position: 7
title: "会话"
description: "会话持久化、恢复、搜索、管理以及各平台的会话追踪"
---

# 会话

Hermes Agent 会自动将每次对话保存为一个会话。会话支持对话恢复、跨会话搜索和完整的对话历史管理。

## 会话工作原理

每次对话——无论是来自 CLI、Telegram、Discord、Slack、WhatsApp、Signal、Matrix、Teams 还是任何其他消息平台——都会被存储为一个包含完整消息历史的会话。会话追踪通过以下方式实现：

1. **SQLite 数据库**（`~/.hermes/state.db`）——结构化的会话元数据，带 FTS5 全文搜索，以及完整的消息历史

SQLite 数据库存储：
- 会话 ID、来源平台、用户 ID
- **会话标题**（唯一、人类可读的名称）
- 模型名称和配置
- 系统提示快照
- 完整消息历史（角色、内容、工具调用、工具结果）
- Token 计数（输入/输出）
- 时间戳（开始时间、结束时间）
- 父会话 ID（用于压缩触发的会话分割）

### 什么会占用上下文

Hermes 存储会话历史以便恢复对话，但它不会一直重复发送它处理过的每一个字节。在每一轮中，模型看到的是选定的系统提示、当前对话窗口以及 Hermes 为该轮显式注入的任何内容。

媒体附件作为轮次范围内的输入处理：

- 图片可以原生附加到下一次模型调用中，或者当活跃模型不支持原生视觉时，预先分析为文本描述。
- 音频在配置了语音转文本时转录为文本。
- 文本文档的提取文本可以包含在内；其他文档类型通常以保存的本地路径和简短说明表示。
- 附件路径和提取/派生文本可以出现在转录中，但原始图片、音频或二进制文件字节不会反复复制到后续提示中。

例如，如果用户发送一张图片并要求 Hermes 用它制作一个表情包，Hermes 可能会用视觉功能检查该图片一次并运行一个图片处理脚本。后续轮次不会自动将原始 JPEG 带入上下文。它们只携带写入对话中的内容，如用户的请求、简短的图片描述、本地缓存路径或最终的助手回复。

上下文增长的最常见原因不是媒体文件本身，而是冗长的文本：粘贴的转录稿、完整日志、大量工具输出、长 diff、重复的状态报告和详细的证明输出。建议使用摘要、文件路径、聚焦的摘录和基于工具的查找，而不是将大量内容复制到聊天中。

:::tip
当会话变长时使用 `/compress`，使用 `/new` 开启新线程，只有在想从存储中删除旧的已结束会话时才使用 `hermes sessions prune`。压缩会减少活跃上下文；它不是隐私删除。为 `/new` 传递名称（例如 `/new payments-refactor`）可以提前设置新会话的初始标题——便于稍后使用 `/resume <name>` 或在 `/sessions` 选择器中找到它。
:::

### 会话来源

每个会话都会标记其来源平台：

| 来源 | 说明 |
|--------|-------------|
| `cli` | 交互式 CLI（`hermes` 或 `hermes chat`） |
| `telegram` | Telegram 消息应用 |
| `discord` | Discord 服务器/私信 |
| `slack` | Slack 工作区 |
| `whatsapp` | WhatsApp 消息应用 |
| `signal` | Signal 消息应用 |
| `matrix` | Matrix 房间和私信 |
| `mattermost` | Mattermost 频道 |
| `email` | 电子邮件（IMAP/SMTP） |
| `sms` | 通过 Twilio 的 SMS |
| `dingtalk` | 钉钉消息应用 |
| `feishu` | 飞书/Lark 消息应用 |
| `wecom` | 企业微信 |
| `weixin` | 微信（个人微信） |
| `bluebubbles` | 通过 BlueBubbles macOS 服务器的 Apple iMessage |
| `qqbot` | QQ 机器人（腾讯 QQ），通过官方 API v2 |
| `homeassistant` | Home Assistant 对话 |
| `webhook` | 入站 webhooks |
| `api-server` | API 服务器请求 |
| `acp` | ACP 编辑器集成 |
| `cron` | 定时 cron 作业 |
| `batch` | 批量处理运行 |

## CLI 会话恢复

使用 `--continue` 或 `--resume` 从 CLI 恢复之前的对话：

### 继续上次会话

```bash
# 恢复最近的 CLI 会话
hermes --continue
hermes -c

# 或使用 chat 子命令
hermes chat --continue
hermes chat -c
```

这会从 SQLite 数据库中查找最近的 `cli` 会话并加载其完整对话历史。

### 按名称恢复

如果您已为会话设置了标题（参见下方的[会话命名](#session-naming)），可以按名称恢复：

```bash
# 恢复已命名的会话
hermes -c "my project"

# 如果存在谱系变体（my project、my project #2、my project #3），
# 这会自动恢复最新的一个
hermes -c "my project"   # → 恢复 "my project #3"
```

### 恢复特定会话

```bash
# 通过 ID 恢复特定会话
hermes --resume 20250305_091523_a1b2c3d4
hermes -r 20250305_091523_a1b2c3d4

# 通过标题恢复
hermes --resume "refactoring auth"

# 或使用 chat 子命令
hermes chat --resume 20250305_091523_a1b2c3d4
```

会话 ID 会在退出 CLI 会话时显示，也可以通过 `hermes sessions list` 找到。

### 恢复时的对话摘要

当您恢复会话时，Hermes 会在输入提示符之前以样式化面板显示先前对话的简洁摘要：

<img className="docs-terminal-figure" src="/img/docs/session-recap.svg" alt="Stylized preview of the Previous Conversation recap panel shown when resuming a Hermes session." />
<p className="docs-figure-caption">恢复模式显示一个简洁的摘要面板，包含最近的用户和助手轮次，然后将您带回实时提示符。</p>

摘要：
- 显示**用户消息**（金色 `●`）和**助手回复**（绿色 `◆`）
- **截断**长消息（用户 300 字符，助手 200 字符 / 3 行）
- **折叠**工具调用为计数和工具名称（如 `[3 tool calls: terminal, web_search]`）
- **隐藏**系统消息、工具结果和内部推理
- **上限**为最近 10 次交流，带有"... N earlier messages ..."指示符
- 使用**暗淡样式**与活跃对话区分开来

要禁用摘要并保持简洁的单行行为，在 `~/.hermes/config.yaml` 中设置：

```yaml
display:
  resume_display: minimal   # 默认: full
```

:::tip
会话 ID 遵循格式 `YYYYMMDD_HHMMSS_<hex>`——CLI/TUI 会话使用 6 个字符的十六进制后缀（如 `20250305_091523_a1b2c3`），网关会话使用 8 个字符的后缀（如 `20250305_091523_a1b2c3d4`）。您可以通过 ID（完整或唯一前缀）或标题恢复——两者都支持 `-c` 和 `-r`。
:::

## 跨平台交接

在 CLI 会话中使用 `/handoff <platform>` 将当前对话转移到消息平台的主频道。agent 会从 CLI 离开的地方精确接续——相同的会话 ID、完整的角色感知转录、包括所有工具调用。

```bash
# 在 CLI 会话中
/handoff telegram
```

发生的过程：

1. CLI 验证 `<platform>` 已启用并设置了主频道（在目标聊天中运行一次 `/sethome` 来配置）。
2. CLI 将会话标记为待处理并**阻塞轮询网关**。如果 agent 正在执行中，它会拒绝——请等待当前回复完成。
3. 网关观察器认领交接并请求目标适配器创建新讨论串：
   - **Telegram**——打开新的论坛话题（如果在聊天中启用了 Bot API 9.4+ Topics 模式则为私信话题，或论坛超级群组话题）。
   - **Discord**——在主文本频道下创建一个 1440 分钟自动归档的讨论串。
   - **Slack**——发布一条种子消息并使用其 `ts` 作为讨论串锚点。
   - **WhatsApp / Signal / Matrix / SMS**——不支持原生讨论串，直接回退到主频道。
4. 网关将目标键重新绑定到您现有的 CLI 会话 ID，然后生成一条合成的用户轮次，要求 agent 确认并摘要。回复会出现在新讨论串中。
5. 网关确认成功后，CLI 打印 `/resume` 提示并干净退出：

   ```
   ↻ Handoff complete. The session is now active on telegram.
     Resume it on this CLI later with: /resume my-session-title
   ```

6. 从那时起，对话在平台上进行。在新讨论串中回复——该频道中的任何授权用户共享同一个会话，并且由于讨论串会话键不含 `user_id`，任何后续的真实用户消息都会无缝加入。

**恢复到 CLI：** 当您想回到桌面时，只需运行 `/resume <title>`（或从 shell 运行 `hermes -r "<title>"`）即可从平台离开的地方继续。

**失败模式：**
- 未配置主频道 → CLI 拒绝并提供 `/sethome` 提示。
- 平台未启用 / 网关未运行 → CLI 在 60 秒后超时并显示明确消息，您的 CLI 会话保持完好。
- 讨论串创建失败（权限、topics 模式关闭）→ 直接回退到主频道并仍然完成；没有讨论串隔离，但交接本身有效。
- `adapter.send` 失败（速率限制、临时 API 错误）→ 交接标记为失败并显示原因；该记录被清除以便您重试。

**需要注意的限制：** 对于没有讨论串功能的多用户群组主频道平台，合成的轮次以私信风格会话键存储。这对于自用私信主频道（典型设置）有效，但对于真正的共享群聊并不理想。讨论串功能覆盖了 Telegram / Discord / Slack——绝大多数情况——所以大多数设置不会遇到此问题。

## 会话命名

为会话设置人类可读的标题，以便轻松查找和恢复。

### 自动生成标题

Hermes 在首次交流后会自动为每个会话生成一个简短的描述性标题（3–7 个单词）。这在后台线程中使用快速的辅助模型运行，不会增加延迟。使用 `hermes sessions list` 或 `hermes sessions browse` 浏览会话时，您会看到自动生成的标题。

自动标题每个会话只触发一次，如果您已手动设置标题则会跳过。

### 手动设置标题

在任何聊天会话（CLI 或网关）中使用 `/title` 斜杠命令：

```
/title my research project
```

标题会立即应用。如果会话尚未在数据库中创建（例如，您在发送第一条消息之前运行了 `/title`），它会被排队并在会话开始时应用。

您也可以从命令行重命名现有会话：

```bash
hermes sessions rename 20250305_091523_a1b2c3d4 "refactoring auth module"
```

### 标题规则

- **唯一**——没有两个会话可以共享相同的标题
- **最多 100 个字符**——保持列表输出整洁
- **已清理**——控制字符、零宽字符和 RTL 覆盖符会被自动剥离
- **普通 Unicode 正常**——emoji、中日韩文字、带重音字符均可用

### 压缩时自动谱系

当会话上下文被压缩时（手动通过 `/compress` 或自动），Hermes 会创建一个新的延续会话。如果原始会话有标题，新会话会自动获得一个编号标题：

```
"my project" → "my project #2" → "my project #3"
```

当您按名称恢复时（`hermes -c "my project"`），它会自动选择谱系中最新的会话。

### 消息平台中的 /title

`/title` 命令在所有网关平台（Telegram、Discord、Slack、WhatsApp）中均可用：

- `/title My Research`——设置会话标题
- `/title`——显示当前标题

## 会话管理命令

Hermes 通过 `hermes sessions` 提供完整的会话管理命令集：

### 列出会话

```bash
# 列出最近的会话（默认：最近 20 个）
hermes sessions list

# 按平台过滤
hermes sessions list --source telegram

# 显示更多会话
hermes sessions list --limit 50
```

当会话有标题时，输出显示标题、预览和相对时间戳：

```
Title                  Preview                                  Last Active   ID
────────────────────────────────────────────────────────────────────────────────────────────────
refactoring auth       Help me refactor the auth module please   2h ago        20250305_091523_a
my project #3          Can you check the test failures?          yesterday     20250304_143022_e
—                      What's the weather in Las Vegas?          3d ago        20250303_101500_f
```

当没有会话有标题时，使用更简单的格式：

```
Preview                                            Last Active   Src    ID
──────────────────────────────────────────────────────────────────────────────────────
Help me refactor the auth module please             2h ago        cli    20250305_091523_a
What's the weather in Las Vegas?                    3d ago        tele   20250303_101500_f
```

### 导出会话

```bash
# 将所有会话导出到 JSONL 文件
hermes sessions export backup.jsonl

# 从特定平台导出会话
hermes sessions export telegram-history.jsonl --source telegram

# 导出单个会话
hermes sessions export session.jsonl --session-id 20250305_091523_a1b2c3d4
```

导出的文件每行包含一个 JSON 对象，包含完整的会话元数据和所有消息。

### 删除会话

```bash
# 删除特定会话（需确认）
hermes sessions delete 20250305_091523_a1b2c3d4

# 无需确认直接删除
hermes sessions delete 20250305_091523_a1b2c3d4 --yes
```

### 重命名会话

```bash
# 设置或更改会话标题
hermes sessions rename 20250305_091523_a1b2c3d4 "debugging auth flow"

# 多词标题在 CLI 中不需要引号
hermes sessions rename 20250305_091523_a1b2c3d4 debugging auth flow
```

如果标题已被其他会话使用，会显示错误。

### 清理旧会话

```bash
# 删除超过 90 天的已结束会话（默认）
hermes sessions prune

# 自定义时间阈值
hermes sessions prune --older-than 30

# 仅清理特定平台的会话
hermes sessions prune --source telegram --older-than 60

# 跳过确认
hermes sessions prune --older-than 30 --yes
```

:::info
清理只会删除**已结束**的会话（已明确结束或自动重置的会话）。活跃会话永远不会被清理。
:::

### 会话统计

```bash
hermes sessions stats
```

输出：

```
Total sessions: 142
Total messages: 3847
  cli: 89 sessions
  telegram: 38 sessions
  discord: 15 sessions
Database size: 12.4 MB
```

如需更深入的分析——token 使用量、费用估算、工具分解和活动模式——使用 [`hermes insights`](/docs/reference/cli-commands#hermes-insights)。

## 会话搜索工具

agent 有一个内置的 `session_search` 工具，使用 SQLite 的 FTS5 引擎对所有过去的对话进行全文搜索——并让 agent 滚动浏览找到的任何会话。不调用 LLM，不进行摘要，不截断。每个返回形式都从数据库中返回实际消息。

### 三种调用形式

工具根据您设置的参数推断您想要什么。没有 `mode` 参数。

**1. 发现——传递 `query`：**

```python
session_search(query="auth refactor", limit=3)
```

运行 FTS5，按会话谱系去重，返回前 N 个会话。每个结果包含：

- `session_id`、`title`、`when`、`source`
- `snippet`——FTS5 高亮的匹配摘录
- `bookend_start`——会话的前 3 条 user+assistant 消息（目标/启动）
- `messages`——FTS5 匹配前后的 ±5 条消息，锚点消息被标记（上下文中的命中）
- `bookend_end`——会话的最后 3 条 user+assistant 消息（结论/决策）
- `match_message_id`、`messages_before`、`messages_after`

Bookends + 窗口一起重构目标 → 匹配 → 结论，而无需为整个转录付费。在真实会话数据库上的典型耗时：15–50ms。

**2. 滚动——传递 `session_id` + `around_message_id`：**

```python
session_search(session_id="20260510_174648_805cc2", around_message_id=590803, window=10)
```

返回以锚点为中心的 ±`window` 消息窗口。不使用 FTS5，没有 bookends——就是切片。在发现调用后需要比默认 ±5 窗口更多上下文时使用。

- 要**向前**滚动：将 `messages[-1].id` 作为 `around_message_id` 传回
- 要**向后**滚动：将 `messages[0].id` 作为 `around_message_id` 传回
- 边界消息会出现在两个窗口中作为方向标记
- 当 `messages_before` 或 `messages_after` 小于 `window` 时，您已到达会话的开头或结尾

每次滚动调用的典型耗时：1–2ms。

**3. 浏览——无参数：**

```python
session_search()
```

按时间顺序返回最近的会话（标题、预览、时间戳）。当用户问"我之前在做什么"而没有指定话题时很有用。

### FTS5 查询语法

关键词模式支持标准 FTS5 查询语法：

- 简单关键词：`docker deployment`（FTS5 默认为 AND）
- 短语：`"exact phrase"`
- 布尔：`docker OR kubernetes`、`python NOT java`
- 前缀：`deploy*`

### 可选参数

- `sort`——`newest` 或 `oldest`，在 FTS5 排名之上。省略则仅按相关性排序（默认；适用于探索性召回）。对于"我们在哪里停止了 X"之类的问题使用 `newest`，对于"X 是怎么开始的"之类的问题使用 `oldest`。
- `role_filter`——逗号分隔的要包含的角色。发现默认为 `user,assistant`（工具输出通常是噪音）。传递 `user,assistant,tool` 以包含工具输出（调试工具行为），或仅传递 `tool` 仅搜索工具输出。

### 何时使用

agent 被提示自动使用会话搜索：

> *"当用户引用过去对话中的某些内容，或者您怀疑存在相关的先前上下文时，请使用 session_search 来召回它，然后再要求他们重复。"*

典型触发词："we did this before"、"remember when"、"last time"、"as I mentioned"，或对不在当前窗口中的项目/人员/概念的任何引用。

## 各平台会话追踪

### 网关会话

在消息平台上，会话通过从消息来源构建的确定性会话键来标识：

| 聊天类型 | 默认键格式 | 行为 |
|-----------|--------------------|----------|
| Telegram 私信 | `agent:main:telegram:dm:<chat_id>` | 每个私信聊天一个会话 |
| Discord 私信 | `agent:main:discord:dm:<chat_id>` | 每个私信聊天一个会话 |
| WhatsApp 私信 | `agent:main:whatsapp:dm:<canonical_identifier>` | 每个私信用户一个会话（当映射存在时，LID/电话号码别名合并为一个身份） |
| 群聊 | `agent:main:<platform>:group:<chat_id>:<user_id>` | 当平台暴露用户 ID 时，群组内每个用户独立会话 |
| 群组讨论串/话题 | `agent:main:<platform>:group:<chat_id>:<thread_id>` | 所有讨论串参与者共享会话（默认）。使用 `thread_sessions_per_user: true` 切换为每个用户独立。 |
| 频道 | `agent:main:<platform>:channel:<chat_id>:<user_id>` | 当平台暴露用户 ID 时，频道内每个用户独立会话 |

当 Hermes 无法获取共享聊天的参与者标识符时，会回退到该房间的一个共享会话。

### 共享 vs 隔离的群组会话

默认情况下，Hermes 在 `config.yaml` 中使用 `group_sessions_per_user: true`。这意味着：

- Alice 和 Bob 可以在同一个 Discord 频道中与 Hermes 对话，而不会共享转录历史
- 一个用户的工具密集型长任务不会污染另一个用户的上下文窗口
- 打断处理也保持按用户独立，因为运行中 agent 的键与隔离的会话键匹配

如果您想要一个共享的"房间大脑"，请设置：

```yaml
group_sessions_per_user: false
```

这会将群组/频道恢复为每个房间一个共享会话，保留了共享的对话上下文，但也共享了 token 成本、打断状态和上下文增长。

### 会话重置策略

网关会话基于可配置的策略自动重置：

- **idle**——在 N 分钟不活动后重置
- **daily**——在每天的特定时间重置
- **both**——以先到者为准（空闲或每日）重置
- **none**——从不自动重置

在会话自动重置之前，agent 会获得一轮机会来保存对话中的重要记忆或 skills。

具有**活跃后台进程**的会话永远不会自动重置，无论策略如何。

## 存储位置

| 内容 | 路径 | 说明 |
|------|------|-------------|
| SQLite 数据库 | `~/.hermes/state.db` | 所有会话元数据 + 消息，带 FTS5 |
| 网关消息    | `~/.hermes/state.db`   | SQLite——所有会话消息的规范存储 |
| 网关路由索引 | `~/.hermes/sessions/sessions.json` | 将会话键映射到活跃会话 ID（来源元数据、过期标志） |

SQLite 数据库使用 WAL 模式以支持并发读取和单一写入者，这非常适合网关的多平台架构。

:::note 旧版 JSONL 转录文件
在 state.db 成为规范存储之前创建的会话可能在 `~/.hermes/sessions/` 中留有 `*.jsonl` 文件。Hermes 不再写入或读取它们。验证对应会话在 state.db 中存在后即可安全删除。
:::

### 数据库模式

`state.db` 中的关键表：

- **sessions**——会话元数据（id、source、user_id、model、title、时间戳、token 计数）。标题有唯一索引（允许 NULL 标题，只有非 NULL 值必须唯一）。
- **messages**——完整消息历史（role、content、tool_calls、tool_name、token_count）
- **messages_fts**——用于跨消息内容全文搜索的 FTS5 虚拟表

## 会话过期和清理

### 自动清理

- 网关会话基于配置的重置策略自动重置
- 重置前，agent 会保存即将过期会话中的记忆和 skills
- 选择性自动清理：当 `sessions.auto_prune` 为 `true` 时，在 CLI/网关启动时清理超过 `sessions.retention_days`（默认 90）天的已结束会话
- 实际删除了记录的清理之后，`state.db` 会执行 `VACUUM` 以回收磁盘空间（SQLite 不会在普通 DELETE 后缩小文件）
- 清理最多每 `sessions.min_interval_hours`（默认 24）小时运行一次；上次运行时间戳存储在 `state.db` 内部，因此它在同一 `HERMES_HOME` 中的所有 Hermes 进程间共享

默认为**关闭**——会话历史对 `session_search` 召回很有价值，静默删除可能会让用户感到意外。在 `~/.hermes/config.yaml` 中启用：

```yaml
sessions:
  auto_prune: true          # 主动选择——默认为 false
  retention_days: 90        # 将已结束会话保留这么多天
  vacuum_after_prune: true  # 清理后回收磁盘空间
  min_interval_hours: 24    # 清理间隔不低于此时间
```

活跃会话永远不会被自动清理，无论其存在多长时间。

### 手动清理

```bash
# 清理超过 90 天的会话
hermes sessions prune

# 删除特定会话
hermes sessions delete <session_id>

# 清理前导出（备份）
hermes sessions export backup.jsonl
hermes sessions prune --older-than 30 --yes
```

:::tip
数据库增长缓慢（典型：数百个会话 10-15 MB），会话历史支持跨过去对话的 `session_search` 召回，因此自动清理默认关闭。如果您运行的是重负载网关/cron 工作负载，且 `state.db` 对性能有明显影响（观察到的故障模式：384 MB 的 state.db 约 1000 个会话，导致 FTS5 插入和 `/resume` 列表变慢），请启用它。使用 `hermes sessions prune` 进行一次性清理，而无需开启自动清理。
:::
