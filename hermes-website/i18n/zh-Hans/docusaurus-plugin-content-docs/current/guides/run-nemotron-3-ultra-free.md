---
sidebar_position: 0
title: "在 Hermes Agent 中免费运行 Nemotron 3 Ultra"
description: "在 Nous Portal 上体验 NVIDIA Nemotron 3 Ultra — 6月4日至18日免费 — Hermes Agent 发布即支持"
---

# 在 Hermes Agent 中免费运行 Nemotron 3 Ultra

Nous Research 已加入由 **NVIDIA** 合作的领先 AI 实验室组成的 **Nemotron Coalition**，致力于推进开放前沿基础模型。为此，我们与 **Nebius** 合作，在 [Nous Portal](https://portal.nousresearch.com) 上提供 **Nemotron 3 Ultra** 为期两周的免费使用（**6月4日至6月18日**）。按照以下说明即可在你的 Hermes Agent 中体验该模型。

:::info 限时优惠
`nvidia/nemotron-3-ultra:free` 层级在 **6月4日至6月18日** 期间可用。`:free` 标签使其保持在免费计划中——请选择该精确变体。
:::

选择最适合你的安装方式。**桌面应用**最简单——无需终端。如果你习惯使用终端，命令行安装就在下方。

## 方案 A — 桌面应用（推荐）

最简便的方式：一键安装，附带引导式点击设置。无需终端。

### 1. 下载并安装

[下载 Hermes Desktop 安装程序](https://hermes-agent.nousresearch.com/desktop)（macOS 或 Windows），然后打开。首次启动时会完成自我设置（通常在一分钟以内）。

### 2. 连接 Nous Portal

应用打开后，你会看到一个"Let's get you set up"屏幕。点击 **Nous Portal**（标记为 **Recommended**）。你的浏览器打开——创建一个 [Nous Portal](https://portal.nousresearch.com) 账户（或登录），选择 **Free** 计划，并授权 Hermes。应用自动连接。

### 3. 选择免费 Nemotron 3 Ultra 模型

连接后，应用显示 **Default model** 卡片。点击 **Change**，搜索 **nemotron 3 ultra**，选择标记为 **Free tier** 的变体：

```
nvidia/nemotron-3-ultra:free
```

`:free` 标签使其保持在免费层级——请选择该变体。

### 4. 开始对话

点击 **Start chatting**。就这样——你正在免费与 Nemotron 3 Ultra 对话。

## 方案 B — 命令行

偏好终端？

### 1. 安装 Hermes Agent

macOS/Linux/WSL2/Android 上运行：

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Windows 上运行：

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

安装完成后，重新加载 shell：

```bash
source ~/.bashrc   # 或 source ~/.zshrc
```

### 2. 运行快速设置

```bash
hermes setup
```

选择 **Quick Setup**。Hermes 打开浏览器标签页，等待你完成后续步骤。

### 3. 创建 Nous Portal 账户

在浏览器中，创建一个 [Nous Portal](https://portal.nousresearch.com) 账户（或登录），选择 **Free** 计划。

### 4. 连接你的账户

当提示将你的账户连接到 Hermes Agent 时，点击 **Connect**。连接成功后你会看到确认提示。

### 5. 选择免费 Nemotron 3 Ultra 模型

返回终端。从模型列表中选择：

```
nvidia/nemotron-3-ultra:free
```

`:free` 标签使其保持在免费层级，因此请确保你选择了该变体。

### 6. 开始对话

完成剩余的快速设置提示，然后运行：

```bash
hermes
```

就这样——你正在免费与 Nemotron 3 Ultra 对话。

## 之后切换到此模型

已设置好其他模型？

- **桌面应用：** 打开模型选择器，搜索 **nemotron 3 ultra**，选择 **Free tier** 变体。
- **CLI / TUI：** 在会话中随时使用 `/model nvidia/nemotron-3-ultra:free` 切换，或运行 `/model` 打开选择器并从列表中选择。

## 故障排查

- **列表中看不到模型？** 确保你完成了 Nous Portal 连接，并且你使用的是 **Free** 计划。在 CLI 中，`hermes portal info` 可确认你已登录并通过 Nous 路由。
- **选错了变体？** 重新选择 `nvidia/nemotron-3-ultra:free`——`:free` 后缀是保持在免费层级的必要条件。
- **浏览器未打开 / 你在远程主机上（CLI）？** 参见 [SSH / 远程主机上的 OAuth](/guides/oauth-over-ssh) 了解端口转发和手动粘贴的解决方法。
