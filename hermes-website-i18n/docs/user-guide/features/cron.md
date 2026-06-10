---
sidebar_position: 5
title: "定时任务 (Cron)"
description: "使用自然语言安排自动化任务，通过统一的 cron 工具进行管理，并可关联一个或多个技能"
---

# 定时任务 (Cron)

使用自然语言或 cron 表达式安排任务自动运行。Hermes 通过一个统一的 `cronjob` 工具来管理 cron，采用基于操作的调用方式，而非多个独立的 schedule/list/remove 工具。

## Cron 目前能做什么

Cron 任务可以：

- 安排一次性或重复性任务
- 暂停、恢复、编辑、触发和删除任务
- 为零个、一个或多个 skill 关联到任务
- 将结果投递回原始聊天、本地文件或已配置的平台目标
- 在带有常规静态工具列表的全新 agent 会话中运行
- 以 **无 agent 模式（no-agent mode）** 运行——按计划执行脚本，其 stdout 原样投递，完全不涉及 LLM（参见下方[无 agent 模式（仅脚本任务）](#无-agent-模式仅脚本任务)章节）

所有这些功能都通过 `cronjob` 工具对 Hermes 自身开放，因此你可以用自然语言创建、暂停、编辑和删除任务——无需使用 CLI。

:::warning
Cron 运行的会话不能递归地创建更多 cron 任务。Hermes 在 cron 执行期间会禁用 cron 管理工具，以防止失控的调度循环。
:::

## 创建定时任务

### 在聊天中使用 `/cron`

```bash
/cron add 30m "提醒我检查构建"
/cron add "every 2h" "检查服务器状态"
/cron add "every 1h" "总结新的订阅源内容" --skill blogwatcher
/cron add "every 1h" "使用两个技能并整合结果" --skill blogwatcher --skill maps
```

### 通过独立 CLI

```bash
hermes cron create "every 2h" "检查服务器状态"
hermes cron create "every 1h" "总结新的订阅源内容" --skill blogwatcher
hermes cron create "every 1h" "使用两个技能并整合结果" \
  --skill blogwatcher \
  --skill maps \
  --name "技能组合"
```

### 通过自然对话

像平常一样向 Hermes 提问：

```text
每天早上9点，查看 Hacker News 上的人工智能新闻，并通过 Telegram 发送摘要给我。
```

Hermes 会在内部使用统一的 `cronjob` 工具。

## 带 Skill 的 Cron 任务

一个 cron 任务可以在运行 prompt 之前加载一个或多个 skill。

### 单个 skill

```python
cronjob(
    action="create",
    skill="blogwatcher",
    prompt="检查已配置的订阅源并总结任何新内容。",
    schedule="0 9 * * *",
    name="晨间订阅",
)
```

### 多个 skill

Skill 按顺序加载。prompt 成为叠加在这些 skill 之上的任务指令。

```python
cronjob(
    action="create",
    skills=["blogwatcher", "maps"],
    prompt="查找新的本地活动和附近有趣的地点，然后将它们合并成一份简短的简报。",
    schedule="every 6h",
    name="本地简报",
)
```

当你希望定时 agent 继承可复用的工作流程，而不必将完整的 skill 文本填充到 cron prompt 本身中时，这非常有用。

## 在项目目录中运行任务

Cron 任务默认在脱离任何仓库的情况下运行——不会加载 `AGENTS.md`、`CLAUDE.md` 或 `.cursorrules`，并且 terminal / file / code-exec 工具从 gateway 启动时的工作目录运行。传递 `--workdir`（CLI）或 `workdir=`（工具调用）来更改：

```bash
# 独立 CLI（schedule 和 prompt 是位置参数）
hermes cron create "every 1d at 09:00" \
  "审计开放的 PR，总结 CI 健康状况，并发布到 #eng" \
  --workdir /home/me/projects/acme
```

```python
# 从聊天中，通过 cronjob 工具
cronjob(
    action="create",
    schedule="every 1d at 09:00",
    workdir="/home/me/projects/acme",
    prompt="审计开放的 PR，总结 CI 健康状况，并发布到 #eng",
)
```

当设置了 `workdir` 时：

- 该目录中的 `AGENTS.md`、`CLAUDE.md` 和 `.cursorrules` 会被注入到系统 prompt 中（发现顺序与交互式 CLI 相同）
- `terminal`、`read_file`、`write_file`、`patch`、`search_files` 和 `execute_code` 都使用该目录作为工作目录（通过 `TERMINAL_CWD`）
- 路径必须是存在的绝对目录——相对路径和不存在的目录在创建/更新时会被拒绝
- 编辑时传入 `--workdir ""`（或通过工具传入 `workdir=""`）可清除该设置并恢复原有行为

:::note 串行化
设置了 `workdir` 的任务在调度器计时触发时按顺序运行，不会进入并行池。这是有意为之——`TERMINAL_CWD` 是进程全局的，因此两个设置了 workdir 的任务同时运行会互相破坏对方的 cwd。未设置 workdir 的任务仍像之前一样并行运行。
:::

## 在特定 profile 中运行 cron 任务

默认情况下，cron 任务继承创建它的 gateway / CLI 所属的 Hermes profile。传递 `--profile <name>`（CLI）或 `profile=`（cronjob 工具）可将任务指向不同的 profile——调度器解析该 profile 的 `HERMES_HOME`，在运行期间临时切换到该目录，加载其 `.env` + `config.yaml`，并在那里执行任务：

```bash
# 将任务固定到 `night-ops` profile，无论它是在哪里调度的
hermes cron create "every 1d at 03:00" \
  "监控安全日志并标记异常" \
  --profile night-ops
```

```python
# 从聊天中，通过 cronjob 工具
cronjob(
    action="create",
    schedule="every 1d at 03:00",
    prompt="监控安全日志并标记异常",
    profile="night-ops",
)
```

使用 `--profile default` 可显式固定到根 Hermes profile。命名的 profile 必须已经存在；调度器拒绝动态创建 profile。要在 `cron edit` 期间清除 profile 绑定，传入空字符串（`--profile ""` 或 `profile=""`）——任务将恢复到在调度器自身所在的任何 profile 中运行。

如果绑定的 profile 后来被删除，调度器会记录警告并回退到在当前 profile 中运行任务，而不会崩溃——因此过期的 `profile` 引用永远不会让任务卡死。

:::note 串行化
设置了 `profile` 的任务也会按顺序运行，原因与设置了 `workdir` 的任务相同：切换 `HERMES_HOME` 是进程全局的变更，因此两个设置了 profile 的任务并行运行会相互竞争。未设置 profile 的任务仍在正常的并行池中运行。
:::

## 编辑任务

你不需要为了修改任务而删除并重新创建它们。

:::tip 任务引用
下面的 `<job_id>` 占位符（以及[生命周期操作](#生命周期操作)中的）也接受任务的名称（不区分大小写）——当你记得 `morning-digest` 但不记得十六进制 ID 时非常方便。精确的任务 ID 优先于名称匹配；如果引用不是 ID 且一个名称匹配多个任务，命令会拒绝执行并打印候选 ID，以便你消除歧义。
:::

### 聊天

```bash
/cron edit <job_id> --schedule "every 4h"
/cron edit <job_id> --prompt "使用修订后的任务"
/cron edit <job_id> --skill blogwatcher --skill maps
/cron edit <job_id> --remove-skill blogwatcher
/cron edit <job_id> --clear-skills
```

### 独立 CLI

```bash
hermes cron edit <job_id> --schedule "every 4h"
hermes cron edit <job_id> --prompt "使用修订后的任务"
hermes cron edit <job_id> --skill blogwatcher --skill maps
hermes cron edit <job_id> --add-skill maps
hermes cron edit <job_id> --remove-skill blogwatcher
hermes cron edit <job_id> --clear-skills
```

注意事项：

- 重复使用 `--skill` 会替换任务关联的 skill 列表
- `--add-skill` 追加到现有列表而不替换
- `--remove-skill` 删除特定的关联 skill
- `--clear-skills` 删除所有关联的 skill

## 生命周期操作

Cron 任务现在拥有比单纯的 create/remove 更完整的生命周期。

### 聊天

```bash
/cron list
/cron pause <job_id>
/cron resume <job_id>
/cron run <job_id>
/cron remove <job_id>
```

### 独立 CLI

```bash
hermes cron list
hermes cron pause <job_id>
hermes cron resume <job_id>
hermes cron run <job_id>
hermes cron remove <job_id>
hermes cron status
hermes cron tick
```

每个操作的作用：

- `pause` — 保留任务但停止调度
- `resume` — 重新启用任务并计算下一次未来运行时间
- `run` — 在下一次调度器计时触发时触发任务
- `remove` — 完全删除

## 工作原理

**Cron 执行由 gateway 守护进程处理。** Gateway 每 60 秒触发一次调度器，在隔离的 agent 会话中运行任何到期的任务。

```bash
hermes gateway install     # 作为用户服务安装
sudo hermes gateway install --system   # Linux：服务器上的系统级开机自启服务
hermes gateway             # 或在前台运行

hermes cron list
hermes cron status
```

### Gateway 调度器行为

每次触发时 Hermes 会：

1. 从 `~/.hermes/cron/jobs.json` 加载任务
2. 将 `next_run_at` 与当前时间对比
3. 为每个到期的任务启动一个新的 `AIAgent` 会话
4. 可选地将一个或多个关联的 skill 注入到该新会话中
5. 运行 prompt 直到完成
6. 投递最终响应
7. 更新运行元数据和下次调度时间

`~/.hermes/cron/.tick.lock` 处的文件锁可防止调度器触发重叠导致同一批任务重复运行。

## 投递选项

安排任务时，你可以指定输出发送到何处：

| 选项 | 描述 | 示例 |
|--------|-------------|---------|
| `"origin"` | 返回到创建任务的来源 | 消息平台上的默认行为 |
| `"local"` | 仅保存到本地文件（`~/.hermes/cron/output/`） | CLI 上的默认行为 |
| `"telegram"` | Telegram 主频道 | 使用 `TELEGRAM_HOME_CHANNEL` |
| `"telegram:123456"` | 按 ID 指定的 Telegram 聊天 | 直接投递 |
| `"telegram:-100123:17585"` | 特定的 Telegram 话题 | `chat_id:thread_id` 格式 |
| `"discord"` | Discord 主频道 | 使用 `DISCORD_HOME_CHANNEL` |
| `"discord:#engineering"` | 特定的 Discord 频道 | 按频道名称 |
| `"slack"` | Slack 主频道 | |
| `"whatsapp"` | WhatsApp 主页 | |
| `"signal"` | Signal | |
| `"matrix"` | Matrix 主房间 | |
| `"mattermost"` | Mattermost 主频道 | |
| `"email"` | 电子邮件 | |
| `"sms"` | 通过 Twilio 发送短信 | |
| `"homeassistant"` | Home Assistant | |
| `"dingtalk"` | 钉钉 | |
| `"feishu"` | 飞书/Lark | |
| `"wecom"` | 企业微信 | |
| `"weixin"` | 微信 | |
| `"bluebubbles"` | BlueBubbles (iMessage) | |
| `"qqbot"` | QQ 机器人 | |
| `"all"` | 扇出到所有已连接的主频道 | 在触发时解析 |
| `"telegram,discord"` | 扇出到一组特定的频道 | 逗号分隔列表 |
| `"origin,all"` | 投递到来源**以及**所有其他已连接频道 | 可组合任意令牌 |

Agent 的最终响应会自动投递。你不需要在 cron prompt 中调用 `send_message`。

### 路由意图 (`all`)

`all` 允许你将一个 cron 任务发送到你配置的所有消息频道，而无需逐一列举。它是**在触发时解析**的，因此一个在你配置 Telegram 之前创建的任务，会在你设置 `TELEGRAM_HOME_CHANNEL` 后的下一次触发时自动包含 Telegram。

语义：`all` 展开为每个配置了主频道的平台。零个是允许的；任务只是不产生任何投递目标，并在上游记录为投递失败。

`all` 可与显式目标组合。`origin,all` 投递到原始聊天*以及*所有其他已连接的主频道，并按 `(platform, chat_id, thread_id)` 去重。

### Telegram Cron 话题 (`TELEGRAM_CRON_THREAD_ID`)

当 Telegram 话题模式启用时，根私信被保留为系统大厅——发送到那里的回复会被大厅提醒拒绝，且 `reply_to_message_id` 会被丢弃，因此你无法回复落在主聊天中的 cron 消息。

将 cron 指向一个专用的论坛话题：

1. 在 Telegram 中，打开机器人私信并创建一个名为 e.g. `Cron` 的话题。长按话题标题 → **复制链接**；末尾的整数就是话题的 `message_thread_id`。
2. 在你的 `.env` 中设置 `TELEGRAM_CRON_THREAD_ID=<该id>`。

这仅适用于 cron 投递。`TELEGRAM_HOME_CHANNEL_THREAD_ID`（用于其他地方，如重启通知）保持不变。显式的 `deliver="telegram:chat_id:thread_id"` 目标仍然优先于环境变量。对 cron 消息的回复现在会到达已有的话题会话中，因此你可以直接处理它们。

### 响应包装

默认情况下，投递的 cron 输出会被包装上页眉和页脚，以便接收者知道它来自定时任务：

```
Cronjob Response: 晨间订阅
-------------

<agent 输出内容>

Note: The agent cannot see this message, and therefore cannot respond to it.
```

要投递原始 agent 输出而不带包装，将 `cron.wrap_response` 设置为 `false`：

```yaml
# ~/.hermes/config.yaml
cron:
  wrap_response: false
```

### 静默抑制

如果 agent 的最终响应以 `[SILENT]` 开头，投递将被完全抑制。输出仍会保存到本地以供审计（位于 `~/.hermes/cron/output/`），但不会向投递目标发送任何消息。

这对于仅在有异常时才需要报告的监控任务非常有用：

```text
检查 nginx 是否正在运行。如果一切正常，仅回复 [SILENT]。
否则，报告问题。
```

失败的任务始终会投递，无论 `[SILENT]` 标记如何——只有成功的运行才能被静默。

## 脚本超时

预运行脚本（通过 `script` 参数关联）的默认超时时间为 120 秒。如果你的脚本需要更长时间——例如，包含随机延迟以避免类似机器人的时序模式——你可以增加此时间：

```yaml
# ~/.hermes/config.yaml
cron:
  script_timeout_seconds: 300   # 5 分钟
```

或设置 `HERMES_CRON_SCRIPT_TIMEOUT` 环境变量。解析顺序为：环境变量 → config.yaml → 120s 默认值。

## 无 agent 模式（仅脚本任务）

对于不需要 LLM 推理的周期性任务——经典的看门狗、磁盘/内存告警、心跳检测、CI ping——在创建时传入 `no_agent=True`。调度器按计划运行你的脚本并直接投递其 stdout，完全跳过 agent：

```bash
hermes cron create "every 5m" \
  --no-agent \
  --script memory-watchdog.sh \
  --deliver telegram \
  --name "memory-watchdog"
```

语义：

- 脚本 stdout（去除首尾空白后）→ 作为消息原样投递。
- **空 stdout → 静默触发**，不投递。这是看门狗模式："只有在出错时才报告"。
- 非零退出码或超时 → 投递错误告警，因此损坏的看门狗不会静默失败。
- 最后一行为 `{"wakeAgent": false}` → 静默触发（与 LLM 任务使用相同的门控）。
- 无 token、无模型、无 provider 回退——任务完全不接触推理层。

`.sh` / `.bash` 文件在 `/bin/bash` 下运行；其他文件在当前 Python 解释器（`sys.executable`）下运行。脚本必须位于 `~/.hermes/scripts/`（与预运行脚本门控相同的沙箱规则）。

### Agent 会为你设置这些

`cronjob` 工具的 schema 直接向 Hermes 暴露 `no_agent`，因此你可以在聊天中描述一个看门狗，让 agent 来配置它：

```text
如果 RAM 超过 85%，每 5 分钟通过 Telegram ping 我一次。
```

Hermes 会通过 `write_file` 将检查脚本写入 `~/.hermes/scripts/`，然后调用：

```python
cronjob(action="create", schedule="every 5m",
        script="memory-watchdog.sh", no_agent=True,
        deliver="telegram", name="memory-watchdog")
```

当消息内容完全由脚本决定时（看门狗、阈值告警、心跳检测），它会自动选择 `no_agent=True`。同一个工具还允许 agent 暂停、恢复、编辑和删除任务——因此整个生命周期都由聊天驱动，无需任何人接触 CLI。

有关实际示例，请参阅[仅脚本 Cron 任务指南](/docs/guides/cron-script-only)。

## 使用 `context_from` 链接任务

Cron 任务在隔离的会话中运行，不记忆之前的运行。但有时一个任务的输出恰好是下一个任务所需的内容。`context_from` 参数会自动建立这种连接——任务 B 的 prompt 会在运行时自动获取到任务 A 最近一次输出作为前置上下文。

```python
# 任务 1：收集原始数据
cronjob(
    action="create",
    prompt="从 Hacker News 获取前 10 条 AI/ML 故事。将它们以 markdown 格式保存到 ~/.hermes/data/briefs/raw.md，包含标题、URL 和评分。",
    schedule="0 7 * * *",
    name="AI 新闻收集器",
)

# 任务 2：筛选——接收任务 1 的输出作为上下文
# 通过 cronjob(action="list") 获取任务 1 的 ID
cronjob(
    action="create",
    prompt="阅读 ~/.hermes/data/briefs/raw.md。为每个故事按参与潜力和新颖性评分 1-10。将前 5 名输出到 ~/.hermes/data/briefs/ranked.md。",
    schedule="30 7 * * *",
    context_from="<job1_id>",
    name="AI 新闻筛选",
)

# 任务 3：发布——接收任务 2 的输出作为上下文
cronjob(
    action="create",
    prompt="阅读 ~/.hermes/data/briefs/ranked.md。撰写 3 条推文草稿（钩子 + 正文 + 话题标签）。投递到 telegram:7976161601。",
    schedule="0 8 * * *",
    context_from="<job2_id>",
    name="AI 新闻简报",
)
```

**工作原理：**

- 当任务 2 触发时，Hermes 从 `~/.hermes/cron/output/{job1_id}/*.md` 读取任务 1 最近一次的输出
- 该输出会自动前置到任务 2 的 prompt 之前
- 任务 2 不需要硬编码"读取此文件"——它以上下文的形式接收内容
- 链可以是任意长度：任务 1 → 任务 2 → 任务 3 → ...

**`context_from` 接受的格式：**

| 格式 | 示例 |
|--------|---------|
| 单个任务 ID（字符串） | `context_from="a1b2c3d4"` |
| 多个任务 ID（列表） | `context_from=["job_a", "job_b"]` |

输出按列出顺序拼接。

**何时使用：**

- 多阶段流水线（收集 → 过滤 → 格式化 → 投递）
- 依赖任务，其中第 N 步的工作依赖于第 N-1 步的输出
- 扇出/扇入模式，其中一个任务聚合多个其他任务的结果

## Provider 恢复

Cron 任务继承你配置的回退 provider 和凭证池轮换。如果主 API 密钥被限流或 provider 返回错误，cron agent 可以：

- **回退到备用 provider**（如果你在 `config.yaml` 中配置了 `fallback_providers`（或旧版的 `fallback_model`））
- **轮换到同一 provider 的[凭证池](/docs/user-guide/configuration#credential-pool-strategies)中的下一个凭证**

这意味着在高频率或高峰时段运行的 cron 任务更加有弹性——单个被限流的密钥不会导致整个运行失败。

## 调度格式

Agent 的最终响应会自动投递——你**不**需要在 cron prompt 中为该相同目的地包含 `send_message`。如果 cron 运行调用了 `send_message` 发往调度器已经要投递的相同目标，Hermes 会跳过该重复发送并告诉模型改用最终响应放置面向用户的内容。仅对额外或不同的目标使用 `send_message`。

### 相对延迟（一次性）

```text
30m     → 30 分钟后运行一次
2h      → 2 小时后运行一次
1d      → 1 天后运行一次
```

### 间隔（重复性）

```text
every 30m    → 每 30 分钟
every 2h     → 每 2 小时
every 1d     → 每天
```

### Cron 表达式

```text
0 9 * * *       → 每天上午 9:00
0 9 * * 1-5     → 工作日上午 9:00
0 */6 * * *     → 每 6 小时
30 8 1 * *      → 每月第一天上午 8:30
0 0 * * 0       → 每周日午夜
```

### ISO 时间戳

```text
2026-03-15T09:00:00    → 2026年3月15日上午9:00 一次性运行
```

## 重复行为

| 调度类型 | 默认重复 | 行为 |
|--------------|----------------|----------|
| 一次性（`30m`、时间戳） | 1 | 运行一次 |
| 间隔（`every 2h`） | 永久 | 运行直到被删除 |
| Cron 表达式 | 永久 | 运行直到被删除 |

你可以覆盖它：

```python
cronjob(
    action="create",
    prompt="...",
    schedule="every 2h",
    repeat=5,
)
```

## 以编程方式管理任务

面向 agent 的 API 是一个统一的工具：

```python
cronjob(action="create", ...)
cronjob(action="list")
cronjob(action="update", job_id="...")
cronjob(action="pause", job_id="...")
cronjob(action="resume", job_id="...")
cronjob(action="run", job_id="...")
cronjob(action="remove", job_id="...")
```

对于 `update`，传入 `skills=[]` 可删除所有关联的 skill。

## Cron 任务可用的工具集

Cron 在每个全新的 agent 会话中运行任务，没有附加聊天平台。默认情况下，cron agent 获得的是**你在 `hermes tools` 中为 `cron` 平台配置的工具集**——不是 CLI 的默认值，也不是所有可用工具。

```bash
hermes tools
# → 在 curses 界面中选择 "cron" 平台
# → 像为 Telegram/Discord 等平台配置一样，切换工具集的开关
```

通过 `cronjob.create` 的 `enabled_toolsets` 字段（或通过 `cronjob.update` 在已有任务上）可以做到更精细的逐任务控制：

```text
cronjob(action="create", name="weekly-news-summary",
        schedule="every sunday 9am",
        enabled_toolsets=["web", "file"],      # 仅 web + file，不使用 terminal/browser 等
        prompt="总结本周的 AI 新闻：...")
```

当任务上设置了 `enabled_toolsets` 时，它优先；否则使用 `hermes tools` 中 cron 平台的配置；再否则 Hermes 回退到内置默认值。这对成本控制很重要：在每个微小的"获取新闻"类任务中携带 `moa`、`browser`、`delegation` 工具会膨胀每次 LLM 调用的工具 schema prompt。

### 完全跳过 agent：`wakeAgent`

如果你的 cron 任务关联了预检查脚本（通过 `script=`），该脚本可以在运行时决定 Hermes 是否应该调用 agent。在 stdout 最后一行输出以下形式的内容：

```text
{"wakeAgent": false}
```

...cron 会在本次触发时完全跳过 agent 运行。这对于频繁轮询（每 1-5 分钟）且仅在状态实际发生变化时才需要唤醒 LLM 的场景非常有用——否则你将反复为无内容的 agent 轮次付费。

```python
# 预检查脚本
import json, sys
latest = fetch_latest_issue_count()
prev = read_state("issue_count")
if latest == prev:
    print(json.dumps({"wakeAgent": False}))   # 跳过本次触发
    sys.exit(0)
write_state("issue_count", latest)
print(json.dumps({"wakeAgent": True, "context": {"new_issues": latest - prev}}))
```

当 `wakeAgent` 被省略时，默认为 `true`（照常唤醒 agent）。

#### 示例：低成本的预运行门控

`wakeAgent` 门控为你提供了一种 $0 成本的方式来决定定时任务是否应该消耗任何 LLM token。以下三种模式覆盖了大多数用例。

**文件变更门控** — 仅在被监视的文件自上次成功触发以来有新内容时才运行。调度器记录每个任务的 `last_run_at`；将其与文件的 mtime 进行比较。

```bash
#!/bin/bash
# ~/.hermes/scripts/feed-changed.sh
FEED="$HOME/data/feed.json"
STATE="$HOME/.hermes/scripts/.feed-changed.last"
test -f "$FEED" || { echo '{"wakeAgent": false}'; exit 0; }
mtime=$(stat -c %Y "$FEED")
last=$(cat "$STATE" 2>/dev/null || echo 0)
if [ "$mtime" -le "$last" ]; then
  echo '{"wakeAgent": false}'
else
  echo "$mtime" > "$STATE"
  echo '{"wakeAgent": true}'
fi
```

```text
cronjob(action="create", name="process-feed",
        schedule="every 30m",
        script="feed-changed.sh",
        prompt="一份新的 ~/data/feed.json 已到达。总结变更内容。")
```

**外部标记门控** — 仅在某个其他进程发出就绪信号时才运行（例如部署钩子放置一个文件，CI 任务在你的状态存储中设置一个值）。

```bash
#!/bin/bash
# ~/.hermes/scripts/flag-ready.sh
if test -f /tmp/new-data-ready; then
  rm -f /tmp/new-data-ready
  echo '{"wakeAgent": true}'
else
  echo '{"wakeAgent": false}'
fi
```

```text
cronjob(action="create", name="nightly-analysis",
        schedule="0 9 * * *",
        script="flag-ready.sh",
        prompt="对今天的数据批次运行夜间分析。")
```

**SQL 计数门控** — 仅在你自己的数据库中有新行需要处理时才运行。脚本还可以通过 `context` 将计数传递给 agent，以便 agent 无需重新查询就能知道要处理多少数据。

```python
#!/usr/bin/env python
# ~/.hermes/scripts/new-rows.py
import json, sqlite3
conn = sqlite3.connect("/home/me/data/app.db")
n = conn.execute(
    "SELECT COUNT(*) FROM messages WHERE ts > strftime('%s','now','-2 hours')"
).fetchone()[0]
if n < 1:
    print(json.dumps({"wakeAgent": False}))
else:
    print(json.dumps({"wakeAgent": True, "context": {"new_rows": n}}))
```

```text
cronjob(action="create", name="summarize-new-msgs",
        schedule="every 2h",
        script="new-rows.py",
        prompt="总结最近 2 小时的新消息。")
```

相同的模式适用于你可以从脚本中查询的任何数据源——Postgres、HTTP API、你自己的状态存储——而无需在 cron 子系统中内置 SQL 评估器。

:::tip
Hermes 自身的 `~/.hermes/state.db` 是一个内部 schema，会在不同版本之间变化。不要从预运行门控中查询它——请指向你自己的数据库或数据源。
:::

致谢：这组示例方案源自 @iankar8 在 [#2654](https://github.com/NousResearch/hermes-agent/pull/2654) 中的探索，该 PR 提出了将 sql/file/command 触发器作为并行机制。`script` + `wakeAgent` 门控已经以 $0 成本覆盖了所有三种情况，因此该工作最终以文档形式落地。

### 链接任务：`context_from`

一个 cron 任务可以通过在 `context_from` 中列出其他任务的名称（或 ID）来消费一个或多个其他任务最近一次成功运行的输出：

```text
cronjob(action="create", name="daily-digest",
        schedule="every day 7am",
        context_from=["ai-news-fetch", "github-prs-fetch"],
        prompt="使用上述输出撰写每日摘要。")
```

被引用的任务最近一次完成的输出会作为本次运行的上下文注入到 prompt 之前。每个上游条目必须是一个有效的任务 ID 或名称（参见 `cronjob action="list"`）。注意：链接读取的是*最近一次完成*的输出——它不会等待在同一触发周期中正在运行的上游任务。

## 任务存储

任务存储在 `~/.hermes/cron/jobs.json` 中。任务运行的输出保存到 `~/.hermes/cron/output/{job_id}/{timestamp}.md`。

任务可以将 `model` 和 `provider` 存储为 `null`。当这些字段被省略时，Hermes 在执行时从全局配置中解析它们。它们仅在设置了逐任务覆盖时才会出现在任务记录中。

存储使用原子文件写入，因此中断的写入不会留下部分写入的任务文件。

## 自包含的 Prompt 仍然重要

:::warning 重要
Cron 任务在完全全新的 agent 会话中运行。Prompt 必须包含 agent 所需的所有信息，这些信息不包括已由关联 skill 提供的内容。
:::

**不好的：** `"检查那个服务器问题"`

**好的：** `"以用户 'deploy' SSH 登录服务器 192.168.1.100，使用 'systemctl status nginx' 检查 nginx 是否正在运行，并验证 https://example.com 返回 HTTP 200。"`

## 安全性

定时任务的 prompt 在创建和更新时会进行 prompt 注入和凭证泄露模式扫描。包含不可见 Unicode 技巧、SSH 后门尝试或明显的密钥泄露载荷的 prompt 会被阻止。
