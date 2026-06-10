---
sidebar_position: 8
title: "安全"
description: "安全模型、危险命令审批、用户授权、容器隔离和生产部署最佳实践"
---

# 安全

Hermes Agent 采用纵深防御安全模型设计。本页涵盖每个安全边界——从命令审批到容器隔离，再到消息平台上的用户授权。

## 概述

安全模型共有七层：

1. **用户授权**——谁可以与代理对话（允许名单、DM配对）
2. **危险命令审批**——对破坏性操作进行人工介入审批
3. **容器隔离**——采用加固设置的 Docker/Singularity/Modal 沙箱
4. **MCP 凭据过滤**——MCP 子进程的环境变量隔离
5. **上下文文件扫描**——项目文件中的提示注入检测
6. **跨会话隔离**——会话之间无法访问彼此的数据或状态；定时任务存储路径已加固以防止路径穿越攻击
7. **输入清洗**——终端工具后端中的工作目录参数经过允许名单验证，防止 shell 注入

## 危险命令审批

在执行任何命令之前，Hermes 会将其与精心策划的危险模式列表进行比对。如果发现匹配，用户必须明确批准。

### 审批模式

审批系统支持三种模式，通过 `~/.hermes/config.yaml` 中的 `approvals.mode` 进行配置：

```yaml
approvals:
  mode: manual    # manual | smart | off
  timeout: 60     # 等待用户响应的秒数（默认：60）
```

| 模式 | 行为 |
|------|----------|
| **manual**（默认） | 始终在危险命令上提示用户审批 |
| **smart** | 使用辅助 LLM 评估风险。低风险命令（例如 `python -c "print('hello')"`）自动批准。真正危险的命令自动拒绝。不确定的情况升级为手动提示。 |
| **off** | 禁用所有审批检查——相当于以 `--yolo` 模式运行。所有命令无提示执行。 |

:::warning
将 `approvals.mode` 设置为 `off` 会禁用所有安全提示。仅在可信环境中使用（CI/CD、容器等）。
:::

### YOLO 模式

YOLO 模式绕过当前会话中**所有**危险命令审批提示。它可以通过三种方式激活：

1. **CLI 标志**：使用 `hermes --yolo` 或 `hermes chat --yolo` 启动会话
2. **斜杠命令**：在会话中输入 `/yolo` 来切换开关
3. **环境变量**：设置 `HERMES_YOLO_MODE=1`

`/yolo` 命令是一个**切换开关**——每次使用都会翻转模式的开启或关闭：

```
> /yolo
  ⚡ YOLO 模式开启 — 所有命令自动批准。请谨慎使用。

> /yolo
  ⚠ YOLO 模式关闭 — 危险命令将需要审批。
```

YOLO 模式在 CLI 和网关会话中均可用。在内部，它设置 `HERMES_YOLO_MODE` 环境变量，该变量在每次命令执行前被检查。

当 YOLO 激活时，Hermes 会显示两个持久的视觉提醒，使得很难忘记审批提示已被绕过：

- 当 YOLO 已激活时，会话开始处显示红色横幅：`⚠ YOLO 模式 — 所有审批提示已绕过`。当 YOLO 关闭时隐藏，以保持默认横幅简洁。
- 在所有宽度层级的状态栏中显示 `⚠ YOLO` 片段，随 YOLO 的开启或关闭实时更新（富文本渲染和纯文本回退均支持）。

:::danger
YOLO 模式会禁用会话中**所有**危险命令安全检查——**除了**硬性阻止列表（见下文）。仅当你完全信任正在生成的命令时才使用（例如，在可丢弃环境中经过充分测试的自动化脚本）。
:::

对于破坏性会话斜杠命令（`/clear`、`/new` / `/reset`、`/undo`、`/exit --delete`），CLI 在运行之前也会提示确认。请参阅[斜杠命令 — 破坏性命令的确认提示](../reference/slash-commands.md#confirmation-prompts-for-destructive-commands)。

### 硬性阻止列表（始终生效的底线）

有些命令灾难性极大——不可逆的文件系统擦除、fork 炸弹、直接块设备写入——Hermes **无论**以下情况如何，都拒绝运行它们：

- `--yolo` / `/yolo` 已切换开启
- `approvals.mode: off`
- 定时任务在无头 `approve` 模式下运行
- 用户明确点击"始终允许"

阻止列表是 `--yolo` 之下的底线。它在审批层甚至看到命令之前就触发，并且没有覆盖标志。当前覆盖的模式（非详尽列表；与 `tools/approval.py::UNRECOVERABLE_BLOCKLIST` 保持同步）：

| 模式 | 为何是硬性阻止 |
|---|---|
| `rm -rf /` 及明显变体 | 擦除文件系统根目录 |
| `rm -rf --no-preserve-root /` | 明确的"是的，我就是要删根目录"变体 |
| `:(){ :\|:& };:`（bash fork 炸弹） | 耗尽主机资源直到重启 |
| 在已挂载的根设备上执行 `mkfs.*` | 格式化正在运行的系统 |
| `dd if=/dev/zero of=/dev/sd*` | 将物理磁盘清零 |
| 在根文件系统顶层将不受信任的 URL 管道传输到 `sh` | 远程代码执行攻击面过大，无法批准 |

如果触发了阻止列表，工具调用会向代理返回解释性错误，并且不会执行任何操作。如果某个合法工作流需要这些命令之一（例如，你是擦除并重新安装流水线的操作员），请在代理外部运行它。

### 审批超时

当危险命令提示出现时，用户有可配置的时间来响应。如果在超时时间内未给出响应，命令默认被**拒绝**（故障关闭）。

在 `~/.hermes/config.yaml` 中配置超时时间：

```yaml
approvals:
  timeout: 60  # 秒（默认：60）
```

### 什么会触发审批

以下模式会触发审批提示（在 `tools/approval.py` 中定义）：

| 模式 | 描述 |
|---------|-------------|
| `rm -r` / `rm --recursive` | 递归删除 |
| `rm ... /` | 在根路径中删除 |
| `chmod 777/666` / `o+w` / `a+w` | 全局/其他用户可写权限 |
| `chmod --recursive` 且使用不安全权限 | 递归设置全局/其他用户可写（长标志） |
| `chown -R root` / `chown --recursive root` | 递归将所有者改为 root |
| `mkfs` | 格式化文件系统 |
| `dd if=` | 磁盘复制 |
| `> /dev/sd` | 写入块设备 |
| `DROP TABLE/DATABASE` | SQL DROP |
| `DELETE FROM`（不带 WHERE） | 不带 WHERE 的 SQL DELETE |
| `TRUNCATE TABLE` | SQL TRUNCATE |
| `> /etc/` | 覆盖系统配置 |
| `systemctl stop/restart/disable/mask` | 停止/重启/禁用系统服务 |
| `kill -9 -1` | 终止所有进程 |
| `pkill -9` | 强制终止进程 |
| fork 炸弹模式 | Fork 炸弹 |
| `bash -c` / `sh -c` / `zsh -c` / `ksh -c` | 通过 `-c` 标志执行 shell 命令（包括组合标志如 `-lc`） |
| `python -e` / `perl -e` / `ruby -e` / `node -c` | 通过 `-e`/`-c` 标志执行脚本 |
| `curl ... \| sh` / `wget ... \| sh` | 将远程内容管道传输到 shell |
| `bash <(curl ...)` / `sh <(wget ...)` | 通过进程替换执行远程脚本 |
| 通过 tee 写入 `/etc/`、`~/.ssh/`、`~/.hermes/.env` | 通过 tee 覆盖敏感文件 |
| 通过 `>` / `>>` 写入 `/etc/`、`~/.ssh/`、`~/.hermes/.env` | 通过重定向覆盖敏感文件 |
| `xargs rm` | 使用 xargs 执行 rm |
| `find -exec rm` / `find -delete` | 使用破坏性操作执行 find |
| 将文件 `cp`/`mv`/`install` 到 `/etc/` | 将文件复制/移动到系统配置目录 |
| 对 `/etc/` 执行 `sed -i` / `sed --in-place` | 原地编辑系统配置 |
| `pkill`/`killall` hermes/gateway | 防止自终止 |
| 使用 `&`/`disown`/`nohup`/`setsid` 执行 `gateway run` | 防止在服务管理器之外启动网关 |

:::info
**容器绕过**：在 `docker`、`singularity`、`modal`、`daytona` 或 `vercel_sandbox` 后端中运行时，危险命令检查会被**跳过**，因为容器本身就是安全边界。容器内的破坏性命令无法损害宿主机。
:::

### 审批流程（CLI）

在交互式 CLI 中，危险命令会显示内联审批提示：

```
  ⚠️  危险命令：递归删除
      rm -rf /tmp/old-project

      [o]nce  |  [s]ession  |  [a]lways  |  [d]eny

      选择 [o/s/a/D]：
```

四个选项：

- **once**（一次）——允许此次单次执行
- **session**（会话）——在本次会话剩余时间内允许此模式
- **always**（始终）——添加到永久允许名单（保存到 `config.yaml`）
- **deny**（拒绝，默认）——阻止该命令

### 审批流程（网关/消息平台）

在消息平台上，代理将危险命令详情发送到聊天中，并等待用户回复：

- 回复 **yes**、**y**、**approve**、**ok** 或 **go** 以批准
- 回复 **no**、**n**、**deny** 或 **cancel** 以拒绝

运行网关时会自动设置 `HERMES_EXEC_ASK=1` 环境变量。

### 永久允许名单

标记为"always"批准的命令会保存到 `~/.hermes/config.yaml`：

```yaml
# 永久允许的危险命令模式
command_allowlist:
  - rm
  - systemctl
```

这些模式在启动时加载，并在所有未来会话中静默批准。

:::tip
使用 `hermes config edit` 来查看或从永久允许名单中移除模式。
:::

## 用户授权（网关）

在运行消息网关时，Hermes 通过分层授权系统控制谁可以与机器人交互。

### 授权检查顺序

`_is_user_authorized()` 方法按以下顺序检查：

1. **按平台允许所有标志**（例如 `DISCORD_ALLOW_ALL_USERS=true`）
2. **DM 配对批准列表**（通过配对码批准的用户）
3. **平台特定允许名单**（例如 `TELEGRAM_ALLOWED_USERS=12345,67890`）
4. **全局允许名单**（`GATEWAY_ALLOWED_USERS=12345,67890`）
5. **全局允许所有**（`GATEWAY_ALLOW_ALL_USERS=true`）
6. **默认：拒绝**

### 平台允许名单

在 `~/.hermes/.env` 中将允许的用户 ID 设置为逗号分隔的值：

```bash
# 平台特定允许名单
TELEGRAM_ALLOWED_USERS=123456789,987654321
DISCORD_ALLOWED_USERS=111222333444555666
WHATSAPP_ALLOWED_USERS=15551234567
SLACK_ALLOWED_USERS=U01ABC123

# 跨平台允许名单（对所有平台进行检查）
GATEWAY_ALLOWED_USERS=123456789

# 按平台允许所有（请谨慎使用）
DISCORD_ALLOW_ALL_USERS=true

# 全局允许所有（请极度谨慎使用）
GATEWAY_ALLOW_ALL_USERS=true
```

:::warning
如果**未配置任何允许名单**且未设置 `GATEWAY_ALLOW_ALL_USERS`，则**所有用户都被拒绝**。网关在启动时记录一条警告：

```
未配置用户允许名单。所有未经授权的用户将被拒绝。
在 ~/.hermes/.env 中设置 GATEWAY_ALLOW_ALL_USERS=true 以允许开放访问，
或配置平台允许名单（例如 TELEGRAM_ALLOWED_USERS=your_id）。
```
:::

### DM 配对系统

为了更灵活的授权，Hermes 包含一个基于代码的配对系统。无需预先提供用户 ID，未知用户会收到一个一次性配对码，机器人所有者通过 CLI 批准该码。

**工作原理：**

1. 未知用户向机器人发送私信
2. 机器人回复一个 8 字符的配对码
3. 机器人所有者在 CLI 上运行 `hermes pairing approve <platform> <code>`
4. 该用户在该平台上被永久批准

在 `~/.hermes/config.yaml` 中控制如何处理未经授权的直接消息：

```yaml
unauthorized_dm_behavior: pair

whatsapp:
  unauthorized_dm_behavior: ignore
```

- `pair` 是默认值。未经授权的私信会收到配对码回复。
- `ignore` 静默丢弃未经授权的私信。
- 平台部分会覆盖全局默认值，因此你可以在 Telegram 上保持配对的同时让 WhatsApp 保持静默。

**安全特性**（基于 OWASP + NIST SP 800-63-4 指南）：

| 特性 | 详情 |
|---------|---------|
| 代码格式 | 从 32 字符无歧义字母表（不含 0/O/1/I）生成的 8 字符 |
| 随机性 | 密码学随机（`secrets.choice()`） |
| 代码 TTL | 1 小时过期 |
| 速率限制 | 每用户每 10 分钟 1 次请求 |
| 待处理限制 | 每个平台最多 3 个待处理代码 |
| 锁定 | 5 次失败的批准尝试 → 1 小时锁定 |
| 文件安全 | 对所有配对数据文件设置 `chmod 0600` |
| 日志记录 | 代码永远不会记录到 stdout |

**配对 CLI 命令：**

```bash
# 列出待处理和已批准的用户
hermes pairing list

# 批准一个配对码
hermes pairing approve telegram ABC12DEF

# 撤销用户的访问权限
hermes pairing revoke telegram 123456789

# 清除所有待处理代码
hermes pairing clear-pending
```

**存储：** 配对数据存储在 `~/.hermes/pairing/` 中，使用按平台的 JSON 文件：
- `{platform}-pending.json` — 待处理的配对请求
- `{platform}-approved.json` — 已批准的用户
- `_rate_limits.json` — 速率限制和锁定跟踪

## 容器隔离

当使用 `docker` 终端后端时，Hermes 对每个容器应用严格的安全加固。

### Docker 安全标志

每个容器都使用以下标志运行（在 `tools/environments/docker.py` 中定义）：

```python
_SECURITY_ARGS = [
    "--cap-drop", "ALL",                          # 移除所有 Linux 能力
    "--cap-add", "DAC_OVERRIDE",                  # root 可以写入绑定挂载的目录
    "--cap-add", "CHOWN",                         # 包管理器需要文件所有权
    "--cap-add", "FOWNER",                        # 包管理器需要文件所有权
    "--security-opt", "no-new-privileges",         # 阻止权限提升
    "--pids-limit", "256",                         # 限制进程数量
    "--tmpfs", "/tmp:rw,nosuid,size=512m",         # 大小限制的 /tmp
    "--tmpfs", "/var/tmp:rw,noexec,nosuid,size=256m",  # 禁止执行的 /var/tmp
    "--tmpfs", "/run:rw,noexec,nosuid,size=64m",   # 禁止执行的 /run
]
```

### 资源限制

容器资源可在 `~/.hermes/config.yaml` 中配置：

```yaml
terminal:
  backend: docker
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  docker_forward_env: []  # 仅显式允许名单；空列表可防止密钥进入容器
  container_cpu: 1        # CPU 核心数
  container_memory: 5120  # MB（默认 5GB）
  container_disk: 51200   # MB（默认 50GB，需要 overlay2 在 XFS 上）
  container_persistent: true  # 跨会话持久化文件系统
```

### 文件系统持久化

- **持久化模式**（`container_persistent: true`）：从 `~/.hermes/sandboxes/docker/<task_id>/` 绑定挂载 `/workspace` 和 `/root`
- **临时模式**（`container_persistent: false`）：对工作区使用 tmpfs——清理时所有内容都会丢失

:::tip
对于生产网关部署，使用 `docker`、`modal`、`daytona` 或 `vercel_sandbox` 后端来将代理命令与宿主机系统隔离。这完全消除了对危险命令审批的需求。
:::

:::warning
如果你向 `terminal.docker_forward_env` 添加名称，这些变量会被有意注入到容器中以供终端命令使用。这对于任务特定的凭据（如 `GITHUB_TOKEN`）很有用，但这也意味着在容器中运行的代码可以读取和窃取它们。
:::

## 终端后端安全对比

| 后端 | 隔离级别 | 危险命令检查 | 最适合 |
|---------|-----------|-------------------|----------|
| **local** | 无——在宿主机上运行 | ✅ 是 | 开发、可信用户 |
| **ssh** | 远程机器 | ✅ 是 | 在独立服务器上运行 |
| **docker** | 容器 | ❌ 跳过（容器即边界） | 生产网关 |
| **singularity** | 容器 | ❌ 跳过 | HPC 环境 |
| **modal** | 云沙箱 | ❌ 跳过 | 可扩展的云隔离 |
| **daytona** | 云沙箱 | ❌ 跳过 | 持久化云工作区 |
| **vercel_sandbox** | 云 microVM | ❌ 跳过 | 带快照持久化的云执行 |

## 环境变量透传 {#environment-variable-passthrough}

`execute_code` 和 `terminal` 都会从子进程中剥离敏感环境变量，以防止 LLM 生成的代码窃取凭据。然而，声明了 `required_environment_variables` 的技能合法地需要访问这些变量。

### 工作原理

两种机制允许特定变量通过沙箱过滤器：

**1. 技能范围透传（自动）**

当加载技能时（通过 `skill_view` 或 `/skill` 命令）且技能声明了 `required_environment_variables`，这些变量中实际在环境中设置的任何变量都会自动注册为透传。缺失的变量（仍处于待设置状态）**不会**被注册。

```yaml
# 在技能的 SKILL.md 前言中
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: 从 https://developers.google.com/tenor 获取密钥
```

加载此技能后，`TENOR_API_KEY` 会透传到 `execute_code`、`terminal`（本地）**和远程后端（Docker、Modal）**——无需手动配置。

:::info Docker & Modal
在 v0.5.1 之前，Docker 的 `forward_env` 是与技能透传分开的系统。它们现在已合并——技能声明的环境变量会自动转发到 Docker 容器和 Modal 沙箱中，无需手动将它们添加到 `docker_forward_env`。
:::

**2. 基于配置的透传（手动）**

对于任何技能未声明的环境变量，将它们添加到 `config.yaml` 中的 `terminal.env_passthrough`：

```yaml
terminal:
  env_passthrough:
    - MY_CUSTOM_KEY
    - ANOTHER_TOKEN
```

### 凭据文件透传（OAuth 令牌等） {#credential-file-passthrough}

某些技能需要沙箱中的**文件**（而不仅仅是环境变量）——例如，Google Workspace 将 OAuth 令牌存储为活动配置文件 `HERMES_HOME` 下的 `google_token.json`。技能在前言中声明这些：

```yaml
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 令牌（由设置脚本创建）
  - path: google_client_secret.json
    description: Google OAuth2 客户端凭据
```

加载时，Hermes 检查这些文件是否存在于活动配置文件的 `HERMES_HOME` 中，并注册它们以进行挂载：

- **Docker**：只读绑定挂载（`-v host:container:ro`）
- **Modal**：在沙箱创建时挂载 + 每次命令前同步（处理会话中的 OAuth 设置）
- **Local**：无需操作（文件已可访问）

你也可以在 `config.yaml` 中手动列出凭据文件：

```yaml
terminal:
  credential_files:
    - google_token.json
    - my_custom_oauth_token.json
```

路径相对于 `~/.hermes/`。文件在容器内挂载到 `/root/.hermes/`。

### 各沙箱的过滤规则

| 沙箱 | 默认过滤 | 透传覆盖 |
|---------|---------------|---------------------|
| **execute_code** | 阻止名称中包含 `KEY`、`TOKEN`、`SECRET`、`PASSWORD`、`CREDENTIAL`、`PASSWD`、`AUTH` 的变量；仅允许安全前缀变量通过 | ✅ 透传变量绕过两项检查 |
| **terminal**（本地） | 阻止显式的 Hermes 基础设施变量（提供商密钥、网关令牌、工具 API 密钥） | ✅ 透传变量绕过阻止列表 |
| **terminal**（Docker） | 默认无宿主机环境变量 | ✅ 透传变量 + `docker_forward_env` 通过 `-e` 转发 |
| **terminal**（Modal） | 默认无宿主机环境变量/文件 | ✅ 凭据文件挂载；环境变量通过同步透传 |
| **MCP** | 阻止除安全系统变量 + 显式配置的 `env` 之外的所有内容 | ❌ 不受透传影响（请改用 MCP `env` 配置） |

### 安全考量

- 透传仅影响你或你的技能显式声明的变量——对于任意 LLM 生成的代码，默认安全态势不变
- 凭据文件以**只读**方式挂载到 Docker 容器中
- Skills Guard 在安装前扫描技能内容中可疑的环境访问模式
- 缺失/未设置的变量永远不会被注册（不存在的东西无法泄露）
- Hermes 基础设施密钥（提供商 API 密钥、网关令牌）不应添加到 `env_passthrough`——它们有专用机制

## MCP 凭据处理

MCP（Model Context Protocol）服务器子进程接收**经过过滤的环境**，以防止意外凭据泄露。

### 安全环境变量

只有以下变量从宿主机传递到 MCP stdio 子进程：

```
PATH, HOME, USER, LANG, LC_ALL, TERM, SHELL, TMPDIR
```

以及任何 `XDG_*` 变量。所有其他环境变量（API 密钥、令牌、密钥）均被**剥离**。

在 MCP 服务器的 `env` 配置中显式定义的变量会透传：

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."  # 只有此项被传递
```

### 凭据脱敏

MCP 工具的错误消息在返回给 LLM 之前会被清理。以下模式被替换为 `[REDACTED]`：

- GitHub PAT（`ghp_...`）
- OpenAI 风格的密钥（`sk-...`）
- Bearer 令牌
- `token=`、`key=`、`API_KEY=`、`password=`、`secret=` 参数

### 网站访问策略

你可以限制代理通过其 Web 和浏览器工具可以访问哪些网站。这对于防止代理访问内部服务、管理面板或其他敏感 URL 非常有用。

```yaml
# 在 ~/.hermes/config.yaml 中
security:
  website_blocklist:
    enabled: true
    domains:
      - "*.internal.company.com"
      - "admin.example.com"
    shared_files:
      - "/etc/hermes/blocked-sites.txt"
```

当请求被阻止的 URL 时，工具会返回一个错误，说明该域名被策略阻止。阻止列表在 `web_search`、`web_extract`、`browser_navigate` 和所有支持 URL 的工具中强制执行。

完整详情请参阅配置指南中的[网站阻止列表](/docs/user-guide/configuration#website-blocklist)。

### SSRF 防护

所有支持 URL 的工具（web 搜索、web 提取、视觉、浏览器）在获取 URL 之前都会验证它们，以防止服务端请求伪造（SSRF）攻击。被阻止的地址包括：

- **私有网络**（RFC 1918）：`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`
- **环回地址**：`127.0.0.0/8`、`::1`
- **链路本地地址**：`169.254.0.0/16`（包括 `169.254.169.254` 的云元数据）
- **CGNAT / 共享地址空间**（RFC 6598）：`100.64.0.0/10`（Tailscale、WireGuard VPN）
- **云元数据主机名**：`metadata.google.internal`、`metadata.goog`
- **保留地址、多播地址和未指定地址**

SSRF 防护对于面向互联网的使用始终处于活动状态，DNS 失败被视为已阻止（故障关闭）。重定向链的每一跳都会重新验证，以防止基于重定向的绕过。

#### 有意允许私有 URL

某些设置确实需要访问私有/内部 URL——解析 `home.arpa` 到 RFC 1918 地址空间的家庭网络、仅限 LAN 的 Ollama/llama.cpp 端点、内部 wiki、云元数据调试等。对于这些情况，有一个全局退出选项：

```yaml
security:
  allow_private_urls: true   # 默认：false
```

开启后，Web 工具、浏览器、视觉 URL 获取和网关媒体下载不再拒绝 RFC 1918 / 环回 / 链路本地 / CGNAT / 云元数据目标地址。**这是一个有意的信任边界**——仅在代理运行任意提示注入 URL 对本地网络造成风险是可接受风险的机器上启用它。面向公众的网关应保持关闭状态。

无论此设置如何，主机子字符串防护（即使底层 IP 是公共的也阻止外观相似的 Unicode 域名欺骗）将始终保持开启。

### Tirith 执行前安全扫描

Hermes 集成了 [tirith](https://github.com/sheeki03/tirith)，用于在执行前进行内容级命令扫描。Tirith 检测模式匹配单独无法发现的威胁：

- 同形异义 URL 欺骗（国际化域名攻击）
- 管道到解释器模式（`curl | bash`、`wget | sh`）
- 终端注入攻击

Tirith 在首次使用时从 GitHub releases 自动安装，并进行 SHA-256 校验和验证（如果 cosign 可用，还会进行 cosign 出处验证）。

```yaml
# 在 ~/.hermes/config.yaml 中
security:
  tirith_enabled: true       # 启用/禁用 tirith 扫描（默认：true）
  tirith_path: "tirith"      # tirith 二进制文件的路径（默认：PATH 查找）
  tirith_timeout: 5          # 子进程超时秒数
  tirith_fail_open: true     # 当 tirith 不可用时允许执行（默认：true）
```

当 `tirith_fail_open` 为 `true`（默认）时，如果 tirith 未安装或超时，命令将继续执行。在高安全环境中设置为 `false` 以在 tirith 不可用时阻止命令。

Tirith 为 Linux（x86_64 / aarch64）和 macOS（x86_64 / arm64）提供预编译二进制文件。在没有预编译二进制文件的平台（Windows 等）上，tirith 会被静默跳过——模式匹配防护仍然运行，CLI 不会显示"不可用"横幅。要在 Windows 上使用 tirith，请在 WSL 下运行 Hermes。

Tirith 的裁决与审批流程集成：安全命令直接通过，而可疑和被阻止的命令都会触发用户审批，并附带完整的 tirith 发现（严重性、标题、描述、更安全的替代方案）。用户可以批准或拒绝——默认选择是拒绝，以保持无人值守场景的安全。

### 上下文文件注入防护

上下文文件（AGENTS.md、.cursorrules、SOUL.md）在被包含到系统提示之前会扫描提示注入。扫描器检查：

- 忽略/无视先前指令的指令
- 包含可疑关键字的隐藏 HTML 注释
- 尝试读取密钥（`.env`、`credentials`、`.netrc`）
- 通过 `curl` 窃取凭据
- 不可见的 Unicode 字符（零宽度空格、双向覆盖）

被阻止的文件显示警告：

```
[BLOCKED: AGENTS.md 包含潜在的提示注入（prompt_injection）。内容未加载。]
```

## 生产部署最佳实践

### 网关部署检查清单

1. **设置显式允许名单**——切勿在生产环境中使用 `GATEWAY_ALLOW_ALL_USERS=true`
2. **使用容器后端**——在 config.yaml 中设置 `terminal.backend: docker`
3. **限制资源限制**——设置适当的 CPU、内存和磁盘限制
4. **安全存储密钥**——将 API 密钥保存在 `~/.hermes/.env` 中，并设置适当的文件权限
5. **启用 DM 配对**——尽可能使用配对码而不是硬编码用户 ID
6. **审查命令允许名单**——定期审计 config.yaml 中的 `command_allowlist`
7. **设置 `MESSAGING_CWD`**——不要让代理从敏感目录操作
8. **以非 root 用户运行**——切勿以 root 身份运行网关
9. **监控日志**——检查 `~/.hermes/logs/` 中是否有未经授权的访问尝试
10. **保持更新**——定期运行 `hermes update` 以获取安全补丁

### 保护 API 密钥

```bash
# 设置 .env 文件的适当权限
chmod 600 ~/.hermes/.env

# 为不同服务使用不同的密钥
# 切勿将 .env 文件提交到版本控制
```

### 网络隔离

为了最大程度的安全性，请在单独的机器或虚拟机上运行网关。在 `config.yaml` 中设置 `terminal.backend: ssh`，然后通过 `~/.hermes/.env` 中的环境变量提供主机详情：

```yaml
# ~/.hermes/config.yaml
terminal:
  backend: ssh
```

```bash
# ~/.hermes/.env
TERMINAL_SSH_HOST=agent-worker.local
TERMINAL_SSH_USER=hermes
TERMINAL_SSH_KEY=~/.ssh/hermes_agent_key
```

SSH 连接详情存放在 `.env`（而非 `config.yaml`）中，这样它们就不会被签入或通过配置文件导出共享。这使网关的消息连接与代理的命令执行保持分离。

## 供应链安全公告检查

Hermes 内置了一个公告扫描器，会标记活动 venv 中与已知被入侵版本精选目录匹配的 Python 包（供应链蠕虫，例如 2026 年 5 月的 `mistralai 2.4.6` 投毒事件）。实现在 `hermes_cli/security_advisories.py` 中。

运行方式：

- **CLI 启动横幅。** 如果匹配到任何公告，会打印一行警告，并指向运行 `hermes doctor` 获取完整修复方案。
- **`hermes doctor`。** 显示每个活动公告的版本详情和 2-4 步修复说明。
- **网关启动。** 记录到 `gateway.log`；第一条交互消息会显示简短的操作员横幅。

每个公告都有一个稳定的 id。阅读并处理后，你可以永久忽略它：

```bash
hermes doctor --ack <advisory-id>
```

确认操作会持久化到 `config.security.acked_advisories` 并在重启后保留。旧公告**不会**从目录中删除——保留它们可以让新安装对可能仍缓存在私有镜像中的历史投毒版本保持警惕。

检查本身仅使用标准库，每次公告只需一次 `importlib.metadata.version()` 查找，因此在每次启动时运行是安全的。

### 可选依赖的惰性安装

许多功能（Mistral TTS、ElevenLabs、Honcho memory、Bedrock、Slack、Matrix……）依赖于并非每个用户都需要的 Python 包。Hermes 在首次使用时**惰性安装**这些依赖，而不是在 `hermes-agent[all]` 下预先安装。实现在 `tools/lazy_deps.py` 中。

这解决了以下权衡：

- **脆弱性。** 当一个额外依赖的传递依赖在 PyPI 上不可用时（因恶意软件被隔离、被撤回、上传损坏），整个 `[all]` 解析会失败，新安装会静默降级到精简层级——一次丢失 10 多个不相关的额外依赖。惰性安装隔离了每个后端，因此一个被投毒的依赖不会破坏不相关的功能。
- **臃肿。** 只使用一个提供商的用户不再需要拉取数百个永远不会导入的包。

工作原理：

1. 后端模块在其首次导入路径的顶部调用 `ensure("feature.name")`。
2. 如果缺少依赖，`ensure` 检查 `config.yaml` 中的 `security.allow_lazy_installs`（默认 `true`），并为允许列表中的规范运行 venv 范围内的 `pip install`。
3. 如果安装失败或用户禁用了惰性安装，调用会抛出 `FeatureUnavailable`，附带实际的 pip stderr 输出和指向 `hermes tools` 的提示。

`tools/lazy_deps.py` 强制执行的安全保证：

| 保证 | 含义 |
|---|---|
| 仅限 venv 范围 | 安装目标为活动 venv 中的 `sys.executable`——绝不使用系统 Python |
| 仅按名称从 PyPI 安装 | 规范接受 `"package>=1.0,<2"` 语法。不允许 `--index-url`、`git+https://` 或 file: 路径——恶意的 `config.yaml` 无法重定向安装 |
| 允许名单 | 只有出现在树内 `LAZY_DEPS` 映射中的规范才能通过此路径安装。功能名称中的拼写错误不会获得"安装任何东西"的语义 |
| 退出选项 | 设置 `security.allow_lazy_installs: false` 以完全禁用运行时安装。适用于受限网络或严格的安全态势 |
| 无静默重试 | 失败会显示为 `FeatureUnavailable`——不缓存错误状态，不产生重试风暴 |

禁用运行时安装：

```yaml
# ~/.hermes/config.yaml
security:
  allow_lazy_installs: false
```

禁用后，需要可选依赖的后端会告诉用户手动运行安装（`pip install …`）或通过 `hermes tools` 选择其他后端。
