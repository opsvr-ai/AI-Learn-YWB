---
sidebar_position: 1
title: "工具与工具集"
description: "Hermes Agent 工具概览——可用工具、工具集工作机制以及终端后端"
---

# 工具与工具集

工具是扩展 Agent 能力的函数。它们被组织成逻辑上的**工具集（Toolsets）**，可以按平台启用或禁用。

## 可用工具

Hermes 内置了广泛的内建工具注册表，涵盖网页搜索、浏览器自动化、终端执行、文件编辑、记忆、委托、强化学习训练、消息投递、Home Assistant 等。

:::note
**Honcho 跨会话记忆**作为记忆提供者插件（`plugins/memory/honcho/`）提供，而非内建工具集。请参阅[插件](./plugins.md)了解安装方式。
:::

高级分类如下：

| 类别 | 示例 | 描述 |
|----------|----------|-------------|
| **网页** | `web_search`、`web_extract` | 搜索网页并提取页面内容。 |
| **X 搜索** | `x_search` | 通过 xAI 内置的 `x_search` Responses 工具搜索 X（Twitter）帖子和话题——需 xAI 凭据（SuperGrok OAuth 或 `XAI_API_KEY`）；默认关闭，通过 `hermes tools` → 🐦 X (Twitter) 搜索 选择加入。 |
| **终端与文件** | `terminal`、`process`、`read_file`、`patch` | 执行命令并操作文件。 |
| **浏览器** | `browser_navigate`、`browser_snapshot`、`browser_vision` | 支持文本和视觉的交互式浏览器自动化。 |
| **媒体** | `vision_analyze`、`image_generate`、`video_generate`、`video_analyze`、`text_to_speech` | 多模态分析与生成。`video_generate` 和 `video_analyze` 需选择加入（通过 `hermes tools` 或 `--toolsets` 添加 `video_gen` / `video` 工具集）。 |
| **Agent 编排** | `todo`、`clarify`、`execute_code`、`delegate_task` | 规划、澄清、代码执行和子 Agent 委托。 |
| **记忆与回溯** | `memory`、`session_search` | 持久化记忆和会话搜索。 |
| **自动化与投递** | `cronjob`、`send_message` | 支持 create/list/update/pause/resume/run/remove 操作的定时任务，以及外发消息投递。 |
| **集成** | `ha_*`、MCP 服务器工具、`rl_*` | Home Assistant、MCP、强化学习训练及其他集成。 |

权威的代码生成注册表，请参阅[内建工具参考](/docs/reference/tools-reference)和[工具集参考](/docs/reference/toolsets-reference)。

:::tip Nous 工具网关
付费 [Nous Portal](https://portal.nousresearch.com) 订阅用户可以通过**[工具网关](tool-gateway.md)**使用网页搜索、图像生成、TTS 和浏览器自动化——无需单独的 API 密钥。运行 `hermes model` 启用，或通过 `hermes tools` 配置各个工具。
:::

## 使用工具集

```bash
# 使用指定的工具集
hermes chat --toolsets "web,terminal"

# 查看所有可用工具
hermes tools

# 按平台交互式配置工具
hermes tools
```

常用工具集包括 `web`、`search`、`terminal`、`file`、`browser`、`vision`、`image_gen`、`moa`、`skills`、`tts`、`todo`、`memory`、`session_search`、`cronjob`、`code_execution`、`delegation`、`clarify`、`homeassistant`、`messaging`、`spotify`、`discord`、`discord_admin`、`debugging`、`safe` 和 `rl`。

请参阅[工具集参考](/docs/reference/toolsets-reference)了解完整集合，包括平台预设（如 `hermes-cli`、`hermes-telegram`）和动态 MCP 工具集（如 `mcp-<server>`）。

## 终端后端

终端工具可以在不同环境中执行命令：

| 后端 | 描述 | 使用场景 |
|---------|-------------|----------|
| `local` | 在本地机器运行（默认） | 开发、受信任的任务 |
| `docker` | 隔离容器 | 安全性、可复现性 |
| `ssh` | 远程服务器 | 沙箱隔离，使 Agent 远离自身代码 |
| `singularity` | HPC 容器 | 集群计算，无 root 权限 |
| `modal` | 云端执行 | 无服务器、弹性伸缩 |
| `daytona` | 云端沙箱工作区 | 持久化远程开发环境 |
| `vercel_sandbox` | Vercel Sandbox 云端微虚拟机 | 云端执行，支持基于快照的文件系统持久化 |

### 配置

```yaml
# 在 ~/.hermes/config.yaml 中
terminal:
  backend: local    # 或: docker, ssh, singularity, modal, daytona, vercel_sandbox
  cwd: "."          # 工作目录
  timeout: 180      # 命令超时时间（秒）
```

### Docker 后端

```yaml
terminal:
  backend: docker
  docker_image: python:3.11-slim
```

**一个持久化容器，在整个进程中共享。** Hermes 在首次使用时启动一个长期存活的容器（`docker run -d ... sleep 2h`），并将每次终端、文件和 `execute_code` 调用通过 `docker exec` 路由到该同一容器。工作目录更改、安装的软件包、环境调整以及写入 `/workspace` 的文件都会在工具调用之间持续保留，跨 `/new`、`/reset` 和 `delegate_task` 子 Agent，在 Hermes 进程的整个生命周期内有效。容器在关闭时停止并移除。

这意味着 Docker 后端的行为类似于持久化沙箱虚拟机，而非每次命令都新建容器。如果你执行了一次 `pip install foo`，它在会话的剩余时间里一直可用。如果你执行了 `cd /workspace/project`，后续的 `ls` 调用会看到该目录。请参阅[配置 → Docker 后端](../configuration.md#docker-backend)了解完整的生命周期细节，以及控制 `/workspace` 和 `/root` 是否跨 Hermes 重启保留的 `container_persistent` 标志。

### SSH 后端

推荐用于安全性——Agent 无法修改自身代码：

```yaml
terminal:
  backend: ssh
```
```bash
# 在 ~/.hermes/.env 中设置凭据
TERMINAL_SSH_HOST=my-server.example.com
TERMINAL_SSH_USER=myuser
TERMINAL_SSH_KEY=~/.ssh/id_rsa
```

### Singularity/Apptainer

```bash
# 为并行工作节点预构建 SIF
apptainer build ~/python.sif docker://python:3.11-slim

# 配置
hermes config set terminal.backend singularity
hermes config set terminal.singularity_image ~/python.sif
```

### Modal（无服务器云端）

```bash
uv pip install modal
modal setup
hermes config set terminal.backend modal
```

### Vercel Sandbox

```bash
pip install 'hermes-agent[vercel]'
hermes config set terminal.backend vercel_sandbox
hermes config set terminal.vercel_runtime node24
```

需要同时设置 `VERCEL_TOKEN`、`VERCEL_PROJECT_ID` 和 `VERCEL_TEAM_ID` 三个环境变量进行认证。此访问令牌设置方式是 Render、Railway、Docker 及类似托管环境上部署和正常运行长期 Hermes 进程的推荐路径。支持的运行时包括 `node24`、`node22` 和 `python3.13`；Hermes 默认以 `/vercel/sandbox` 作为远程工作区根目录。

对于一次性本地开发，Hermes 也接受短期 Vercel OIDC 令牌：

```bash
VERCEL_OIDC_TOKEN="$(vc project token <project-name>)" hermes chat
```

从已关联的 Vercel 项目目录：

```bash
VERCEL_OIDC_TOKEN="$(vc project token)" hermes chat
```

当设置 `container_persistent: true` 时，Hermes 使用 Vercel 快照在同一任务的沙箱重建时保留文件系统状态。这可以包括沙箱内 Hermes 同步的凭据、Skills 和缓存文件。快照不保留活动进程、PID 空间或同一活动沙箱身份。

后台终端命令使用 Hermes 的通用非本地进程流程：启动、轮询、等待、日志和终止在沙箱存活期间通过常规进程工具工作，但 Hermes 在清理或重启后不提供原生的 Vercel 分离进程恢复。

保持 `container_disk` 不设置或使用共享默认值 `51200`；Vercel Sandbox 不支持自定义磁盘大小，否则将导致诊断/后端创建失败。

### 容器资源

为所有容器后端配置 CPU、内存、磁盘和持久化：

```yaml
terminal:
  backend: docker  # 或 singularity, modal, daytona, vercel_sandbox
  container_cpu: 1              # CPU 核心数（默认: 1）
  container_memory: 5120        # 内存（MB）（默认: 5GB）
  container_disk: 51200         # 磁盘（MB）（默认: 50GB）
  container_persistent: true    # 跨会话保留文件系统（默认: true）
```

当 `container_persistent: true` 时，安装的软件包、文件和配置将在会话之间保留。

### 容器安全

所有容器后端均运行安全加固：

- 只读根文件系统（Docker）
- 丢弃所有 Linux capability
- 禁止权限提升
- PID 限制（256 个进程）
- 完整命名空间隔离
- 通过卷实现持久化工作区，而非可写根层

Docker 可通过 `terminal.docker_forward_env` 选择性地接收显式环境变量允许列表，但转发的变量对容器内命令可见，应视为对该会话暴露。

## 后台进程管理

启动后台进程并进行管理：

```python
terminal(command="pytest -v tests/", background=true)
# 返回: {"session_id": "proc_abc123", "pid": 12345}

# 然后使用 process 工具管理:
process(action="list")       # 显示所有运行中的进程
process(action="poll", session_id="proc_abc123")   # 检查状态
process(action="wait", session_id="proc_abc123")   # 阻塞直到完成
process(action="log", session_id="proc_abc123")    # 完整输出
process(action="kill", session_id="proc_abc123")   # 终止
process(action="write", session_id="proc_abc123", data="y")  # 发送输入
```

PTY 模式（`pty=true`）可启用交互式 CLI 工具，如 Codex 和 Claude Code。

## Sudo 支持

如果命令需要 sudo，系统会提示你输入密码（在会话期间缓存）。或者在 `~/.hermes/.env` 中设置 `SUDO_PASSWORD`。

:::warning
在消息平台上，如果 sudo 失败，输出会提示将 `SUDO_PASSWORD` 添加到 `~/.hermes/.env`。
:::
