---
sidebar_position: 3
title: "更新与卸载"
description: "如何将 Hermes Agent 更新到最新版本或卸载它"
---

# 更新与卸载

## 更新

### Git 安装

使用一条命令即可更新到最新版本：

```bash
hermes update
```

这会从 `main` 分支拉取最新代码，更新依赖项，并提示你配置自上次更新以来新增的任何选项。

### pip 安装

PyPI 发布版本跟踪**带标签的版本**（主要和次要版本），而不是 `main` 上的每个提交。检查更新并升级：

```bash
hermes update --check    # 查看 PyPI 上是否有新版本
hermes update            # 运行 pip install --upgrade hermes-agent
```

或手动操作：

```bash
pip install --upgrade hermes-agent    # 或：uv pip install --upgrade hermes-agent
```

:::tip
`hermes update` 会自动检测新的配置选项并提示你添加它们。如果你跳过了该提示，可以手动运行 `hermes config check` 查看缺失的选项，然后运行 `hermes config migrate` 以交互方式添加它们。
:::

### 更新过程中会发生什么（Git 安装）

当你运行 `hermes update` 时，将执行以下步骤：

1. **配对数据快照** — 保存一个轻量级的更新前状态快照（涵盖 `~/.hermes/pairing/`、飞书评论规则以及在运行时会被修改的其他状态文件）。可通过[快照与回滚](../user-guide/checkpoints-and-rollback.md)中描述的快照恢复流程进行恢复，或提取 Hermes 在 `~/.hermes/` 目录旁边写入的最新快速快照 zip 文件。
2. **Git pull** — 从 `main` 分支拉取最新代码并更新 submodules
3. **依赖安装** — 运行 `uv pip install -e ".[all]"` 以获取新增或变更的依赖项
4. **配置迁移** — 检测自你的版本以来新增的配置选项，并提示你进行设置
5. **Gateway 自动重启** — 正在运行的 gateway 在更新完成后被刷新，以便新代码立即生效。通过服务管理器管理的 gateway（Linux 上的 systemd，macOS 上的 launchd）将通过服务管理器重启。当 Hermes 能将运行中的 PID 映射回配置文件时，手动启动的 gateway 会自动重新启动。

### 仅预览：`hermes update --check`

想在拉取前知道是否有可用的更新？运行 `hermes update --check`——对于 Git 安装，它会 fetch 并对比与 `origin/main` 的提交差异；对于 pip 安装，它会查询 PyPI 获取最新版本。不会修改任何文件，不会重启 gateway。适用于脚本和 cron 任务中判断"是否有更新"的场景。

### 完整更新前备份：`--backup`

对于高价值的配置文件（生产 gateway、团队共享安装），你可以选择在拉取前对 `HERMES_HOME`（config、auth、sessions、skills、pairing）进行完整备份：

```bash
hermes update --backup
```

或将其设为每次运行的默认行为：

```yaml
# ~/.hermes/config.yaml
updates:
  pre_update_backup: true
```

`--backup` 在早期版本中一直是默认开启的行为，但在较大的 home 目录上每次更新都会增加数分钟时间，因此现在改为按需启用。上述轻量级的配对数据快照仍然无条件运行。

### Windows：另一个 `hermes.exe` 正在运行

在 Windows 上，如果 `hermes update` 检测到另一个 `hermes.exe` 进程持有 venv 入口点可执行文件的打开句柄——最常见的情况是 Hermes Desktop 应用后台进程、另一个终端中打开的 `hermes` REPL，或正在运行的 gateway——则会拒绝运行：

```
$ hermes update
✗ 检测到另一个 hermes.exe 正在运行：
    PID 12345  hermes.exe

  现在更新将无法覆盖 ...\venv\Scripts\hermes.exe，因为
  Windows 会阻止对正在运行的可执行文件进行 REPLACE 操作。

  请在重试之前关闭 Hermes Desktop、退出所有打开的 `hermes` REPL，
  并停止 gateway（`hermes gateway stop`）。
  如果你已确认这些进程不会写入 venv，可使用
  `hermes update --force` 强制执行。
```

关闭列出的进程后重新运行。如果你确信并发进程不会干扰（这种情况很少见——通常只在杀毒软件 shim 被误判时才有用），可以传递 `--force` 跳过检查。在这种情况下，更新程序仍会以指数退避重试 `.exe` 重命名，对于顽固的文件锁，会通过 `MoveFileEx(MOVEFILE_DELAY_UNTIL_REBOOT)` 将替换操作安排在下次重启时进行，以便更新能够完成。

预期输出如下：

```
$ hermes update
正在更新 Hermes Agent...
📥 正在拉取最新代码...
Already up to date.  （或：Updating abc1234..def5678）
📦 正在更新依赖项...
✅ 依赖项已更新
🔍 正在检查新的配置选项...
✅ 配置已是最新  （或：发现 2 个新选项 — 正在运行迁移...）
🔄 正在重启 gateway...
✅ Gateway 已重启
✅ Hermes Agent 更新成功！
```

### 推荐的更新后验证

`hermes update` 处理主要的更新路径，但快速验证可以确认一切顺利落地：

1. `git status --short` — 如果工作树意外变脏，继续前先检查
2. `hermes doctor` — 检查配置、依赖项和服务健康状况
3. `hermes --version` — 确认版本号按预期变更
4. 如果你使用 gateway：`hermes gateway status`
5. 如果 `doctor` 报告 npm audit 问题：在标记的目录中运行 `npm audit fix`

:::warning 更新后工作树变脏
如果 `hermes update` 后 `git status --short` 显示了意外的更改，在继续之前停止并检查它们。这通常意味着本地修改被重新应用到了更新后的代码之上，或者某个依赖步骤刷新了 lockfile。
:::

### 如果终端在更新中断开连接

`hermes update` 会保护自身免受终端意外丢失的影响：

- 更新会忽略 `SIGHUP`，因此关闭 SSH 会话或终端窗口不会再在安装过程中终止它。`pip` 和 `git` 子进程继承此保护，因此 Python 环境不会因连接断开而处于半安装状态。
- 更新期间所有输出都会镜像到 `~/.hermes/logs/update.log`。如果你的终端消失了，重新连接并检查日志以查看更新是否完成以及 gateway 重启是否成功：

```bash
tail -f ~/.hermes/logs/update.log
```

- `Ctrl-C`（SIGINT）和系统关机（SIGTERM）仍然会被响应——这些是有意的取消操作，而非意外。

你不再需要将 `hermes update` 包装在 `screen` 或 `tmux` 中以应对终端断开。

### 检查当前版本

```bash
hermes version
```

与 [GitHub releases 页面](https://github.com/NousResearch/hermes-agent/releases)上的最新版本进行比较。

### 从消息平台更新

你也可以直接从 Telegram、Discord、Slack、WhatsApp 或 Teams 通过发送以下内容进行更新：

```
/update
```

这会拉取最新代码、更新依赖项并重启正在运行的 gateway。Bot 在重启期间会短暂离线（通常 5-15 秒），然后恢复。

### 手动更新

如果你是手动安装的（而非通过快速安装脚本）：

```bash
cd /path/to/hermes-agent
export VIRTUAL_ENV="$(pwd)/venv"

# 拉取最新代码
git pull origin main

# 重新安装（获取新依赖项）
uv pip install -e ".[all]"

# 检查新的配置选项
hermes config check
hermes config migrate   # 交互式添加任何缺失的选项
```

### 回滚说明

如果更新引入了问题，你可以回滚到之前的版本：

```bash
cd /path/to/hermes-agent

# 列出最近的版本
git log --oneline -10

# 回滚到特定提交
git checkout <commit-hash>
git submodule update --init --recursive
uv pip install -e ".[all]"

# 重启 gateway（如果在运行）
hermes gateway restart
```

回滚到特定的发布标签：

```bash
git checkout v0.6.0
git submodule update --init --recursive
uv pip install -e ".[all]"
```

:::warning
如果添加了新的配置选项，回滚可能会导致配置不兼容。回滚后运行 `hermes config check`，如果遇到错误，请从 `config.yaml` 中删除无法识别的选项。
:::

### Nix 用户注意事项

如果你是通过 Nix flake 安装的，更新通过 Nix 包管理器进行管理：

```bash
# 更新 flake 输入
nix flake update hermes-agent

# 或使用最新版本重新构建
nix profile upgrade hermes-agent
```

Nix 安装是不可变的——回滚由 Nix 的 generation 系统处理：

```bash
nix profile rollback
```

更多详情请参见 [Nix 安装配置](./nix-setup.md)。

---

## 卸载

### Git 安装

```bash
hermes uninstall
```

卸载程序会给你保留配置文件（`~/.hermes/`）以供将来重新安装的选项。

### pip 安装

```bash
pip uninstall hermes-agent
rm -rf ~/.hermes            # 可选 — 如果计划重新安装则保留
```

### 手动卸载

```bash
rm -f ~/.local/bin/hermes
rm -rf /path/to/hermes-agent
rm -rf ~/.hermes            # 可选 — 如果计划重新安装则保留
```

:::info
如果你将 gateway 安装为系统服务，请先停止并禁用它：
```bash
hermes gateway stop
# Linux: systemctl --user disable hermes-gateway
# macOS: launchctl remove ai.hermes.gateway
```
:::
