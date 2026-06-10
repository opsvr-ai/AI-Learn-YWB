---
sidebar_position: 4
---

# 同时运行多个 Gateway

在同一台机器上作为托管服务运行多个[配置文件](./profiles.md)——每个配置有自己的机器人 Token、会话和记忆。本页涵盖运维相关事项：同时启动所有配置文件、跨配置文件查看日志、防止主机休眠，以及从常见的 launchd/systemd 异常中恢复。

如果你只运行一个 Hermes Agent，则不需要此页面——基础知识请参见[配置文件](./profiles.md)。

## 何时使用

当你需要两台或更多台 Hermes Agent 同时在线时适合使用此配置。常见原因：

- 一个 Telegram 机器人上运行个人助手，另一个上运行编程 Agent
- 每个家庭成员一个 Agent，或每个 Slack 工作区一个
- 同一配置的沙箱和生产实例
- 一个研究 Agent + 一个写作 Agent + 一个 Cron 驱动的机器人——各自拥有隔离的记忆和 Skills

每个配置文件已经有自己的每个平台 LaunchAgent（`ai.hermes.gateway-<name>.plist`）或 systemd 用户服务（`hermes-gateway-<name>.service`）。本指南补充了集体管理它们的模式。

## 快速开始

```bash
# 创建配置文件（一次）
hermes profile create coder
hermes profile create personal-bot
hermes profile create research

# 配置每个配置文件
coder setup
personal-bot setup
research setup

# 将每个 Gateway 安装为托管服务
coder gateway install
personal-bot gateway install
research gateway install

# 启动所有配置文件
coder gateway start
personal-bot gateway start
research gateway start
```

这样就完成了——三个独立的 Agent，各自运行在自己的进程上，崩溃或用户登录时自动重启。

## 同时启动、停止或重启所有 Gateway

CLI 提供了针对单个配置文件的生命周期命令。如需对所有配置文件执行操作，可以用 shell 循环包装它们。将以下代码片段放到 `~/.local/bin/hermes-gateways` 并 `chmod +x`：

```sh
#!/bin/sh
set -eu

# 在此添加或删除配置文件名称
profiles="default coder personal-bot research"

usage() {
  echo "用法: hermes-gateways {start|stop|restart|status|list}"
}

run_for_profile() {
  profile="$1"
  action="$2"
  if [ "$profile" = "default" ]; then
    hermes gateway "$action"
  else
    hermes -p "$profile" gateway "$action"
  fi
}

action="${1:-}"
case "$action" in
  start|stop|restart|status)
    for profile in $profiles; do
      echo "==> $action $profile"
      run_for_profile "$profile" "$action"
    done
    ;;
  list)
    hermes gateway list
    ;;
  *)
    usage
    exit 2
    ;;
esac
```

然后：

```bash
hermes-gateways start      # 启动每个已配置的配置文件
hermes-gateways stop       # 停止每个已配置的配置文件
hermes-gateways restart    # 重启所有
hermes-gateways status     # 所有配置文件的状态
hermes-gateways list       # 委托给 `hermes gateway list`
```

:::tip
`default` 配置文件通过 `hermes gateway <action>`（不带 `-p`）而非 `hermes -p default gateway <action>` 来操作。上面的包装器同时处理了两种形式。
:::

## 管理单个配置文件

每个配置文件安装的快捷命令：

```bash
coder gateway run        # 前台运行（Ctrl-C 停止）
coder gateway start      # 启动托管服务
coder gateway stop       # 停止托管服务
coder gateway restart    # 重启
coder gateway status     # 查看状态
coder gateway install    # 创建 LaunchAgent / systemd 单元
coder gateway uninstall  # 删除服务文件
```

这些等同于 `hermes -p coder gateway <action>`——当配置文件别名不在 `PATH` 中或需要从脚本动态指定时非常有用。

## 服务文件

每个配置文件安装自己唯一的服务，因此安装从不冲突：

| 平台 | 路径 |
| --- | --- |
| macOS | `~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist` |
| Linux | `~/.config/systemd/user/hermes-gateway-<profile>.service` |

默认配置文件保留历史名称：`ai.hermes.gateway.plist` / `hermes-gateway.service`。

## 查看日志

每个配置文件写入自己的日志文件：

```bash
# 默认配置文件
tail -f ~/.hermes/logs/gateway.log
tail -f ~/.hermes/logs/gateway.error.log

# 命名配置文件
tail -f ~/.hermes/profiles/<name>/logs/gateway.log
tail -f ~/.hermes/profiles/<name>/logs/gateway.error.log
```

同时流式查看每个配置文件的日志：

```bash
tail -f ~/.hermes/logs/gateway.log ~/.hermes/profiles/*/logs/gateway.log
```

CLI 还提供了一个结构化日志查看器：

```bash
hermes logs -f                  # 跟踪默认配置文件
hermes -p coder logs -f         # 跟踪单个配置文件
hermes logs --help              # 过滤器、级别、JSON 输出
```

## 确认当前运行状态

```bash
hermes profile list             # 配置文件 + 模型 + Gateway 状态
hermes-gateways status          # 所有配置文件的完整状态
launchctl list | grep hermes    # macOS — PID 和标签
systemctl --user list-units 'hermes-gateway-*'   # Linux — 单元
```

## 编辑配置

每个配置文件在其自己的目录中保存配置：

```
~/.hermes/profiles/<name>/
├── .env              # API Key、机器人 Token（chmod 600）
├── config.yaml       # 模型、提供商、工具集、Gateway 设置
└── SOUL.md           # 人格 / 系统提示
```

默认配置文件直接使用 `~/.hermes/` 中的相同三个文件。

使用任意编辑器或通过 CLI 编辑：

```bash
hermes config set model.model anthropic/claude-sonnet-4    # 默认配置文件
coder config set model.model openai/gpt-5                  # 命名配置文件
```

编辑 `.env` 或 `config.yaml` 后，重启受影响的 Gateway：

```bash
coder gateway restart
# 或重启所有：
hermes-gateways restart
```

## 保持主机不休眠

Gateway 进程可以全天运行，但操作系统仍会在空闲时尝试休眠。两种模式：

### macOS — `caffeinate`

`caffeinate` 内置于 macOS，运行时阻止睡眠。无需安装。

```bash
caffeinate -dis                    # 阻止显示器、空闲和系统睡眠
caffeinate -dis -t 28800           # 同上，8 小时后自动退出
caffeinate -i -w $(cat ~/.hermes/gateway.pid) &   # 默认 Gateway 运行时保持唤醒

# 持久：后台运行并遗忘
nohup caffeinate -dis >/dev/null 2>&1 &
disown

# 查看 / 停止
pmset -g assertions | grep -iE 'caffeinate|prevent|user is active'
pkill caffeinate
```

| 标志 | 效果 |
| --- | --- |
| `-d` | 阻止显示器睡眠 |
| `-i` | 阻止空闲系统睡眠（默认） |
| `-m` | 阻止磁盘睡眠 |
| `-s` | 阻止系统睡眠（仅限电源供电的 Mac） |
| `-u` | 模拟用户活动（防止屏幕锁定） |
| `-t N` | `N` 秒后自动退出 |
| `-w P` | 当 PID `P` 退出时退出 |

:::warning 合盖仍然会让 Mac 睡眠
`caffeinate` 无法覆盖 MacBook 上由硬件驱动的合盖睡眠。如需合盖运行，请更改节能/电池偏好设置或使用第三方工具。
:::

### Linux — `systemd-inhibit` 或 `loginctl`

```bash
# 在命令运行时阻止挂起
systemd-inhibit --what=idle:sleep --who=hermes --why="gateways running" \
  sleep infinity &

# 允许用户服务在注销后继续运行（推荐）
sudo loginctl enable-linger "$USER"
```

启用 lingering 后，你的 systemd 用户单元（包括 `hermes-gateway-<profile>.service`）在 SSH 断开和重启后继续运行。

## Token 冲突安全

每个配置文件必须为每个平台使用唯一的机器人 Token。如果两个配置文件共享 Telegram、Discord、Slack、WhatsApp 或 Signal 的 Token，第二个 Gateway 会拒绝启动并显示命名冲突配置文件的错误。

审计：

```bash
grep -H 'TELEGRAM_BOT_TOKEN\|DISCORD_BOT_TOKEN' \
     ~/.hermes/.env ~/.hermes/profiles/*/.env
```

## 更新代码

`hermes update` 拉取最新代码一次，并将新的内置 Skills 同步到每个配置文件：

```bash
hermes update
hermes-gateways restart
```

用户修改过的 Skills 永远不会被覆盖。

## 故障排查

### "Could not find service in domain for user gui: 501"

你在 `hermes gateway stop` 之后运行了 `hermes gateway start`。CLI 的 `stop` 执行完整的 `launchctl unload`，这会从 launchd 注册表中移除服务。CLI 在 `start` 时会捕获此特定错误并自动重新加载 plist。服务正常启动。无需修复。

### 崩溃后 PID 残留

如果某个配置文件的 Gateway 显示 `not running` 但进程仍然存活：

```bash
ps -ef | grep "hermes_cli.*-p <profile>"
cat ~/.hermes/profiles/<profile>/gateway.pid
kill -TERM <pid>          # 优雅停止
kill -KILL <pid>          # 如果几秒后仍未停止
<profile> gateway start
```

### 强制硬重置某个服务

```bash
# macOS
launchctl unload ~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist
launchctl load   ~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist

# Linux
systemctl --user restart hermes-gateway-<profile>.service
```

### 健康检查

```bash
hermes doctor                  # 默认配置文件
hermes -p <profile> doctor     # 单个配置文件
```
