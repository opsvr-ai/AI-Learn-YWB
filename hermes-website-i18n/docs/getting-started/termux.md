---
sidebar_position: 3
title: "Android / Termux"
description: "通过 Termux 在 Android 手机上直接运行 Hermes Agent"
---

# 在 Android 上通过 Termux 运行 Hermes

这是通过 [Termux](https://termux.dev/) 在 Android 手机上直接运行 Hermes Agent 的经验证路径。

它为你提供手机上的可用本地 CLI，以及目前已知可在 Android 上顺利安装的核心扩展功能。

## 经验证路径支持哪些功能？

经验证的 Termux 捆绑包安装内容包括：
- Hermes CLI
- cron 支持
- PTY/后台终端支持
- Telegram 网关支持（手动 / 尽力而为的后台运行）
- MCP 支持
- Honcho 记忆支持
- ACP 支持

具体来说，它对应以下命令：

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

## 哪些功能尚未纳入经验证路径？

部分功能仍需桌面/服务器端的依赖项，这些依赖项尚未针对 Android 发布，或尚未在手机上得到验证：

- `.[all]` 目前在 Android 上不受支持
- `voice` 扩展因 `faster-whisper -> ctranslate2` 而受阻，而 `ctranslate2` 不发布 Android wheel
- 自动浏览器 / Playwright 引导在 Termux 安装程序中被跳过
- 基于 Docker 的终端隔离在 Termux 内部不可用
- Android 可能仍会暂停 Termux 后台任务，因此网关的持久性属于尽力而为，而非常规的托管服务

这并不妨碍 Hermes 作为手机原生 CLI 智能体良好运行——只是说明推荐的移动端安装范围有意比桌面/服务器端安装更窄。

---

## 方案一：一行命令安装

Hermes 现在提供了适配 Termux 的安装路径：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

在 Termux 中，安装程序会自动：
- 使用 `pkg` 安装系统软件包
- 用 `python -m venv` 创建虚拟环境
- 先尝试范围更广的 `.[termux-all]` 扩展，若失败则回退到较小的 `.[termux]` 扩展（然后是基础安装）——curl 安装程序会自动按此顺序匹配
- 将 `hermes` 链接到 `$PREFIX/bin`，使其保持在你的 Termux PATH 中
- 跳过未经测试的浏览器 / WhatsApp 引导

如果你需要明确的命令，或需要调试安装失败的问题，请使用下方的手动安装路径。

---

## 方案二：手动安装（完全明确）

### 1. 更新 Termux 并安装系统软件包

```bash
pkg update
pkg install -y git python clang rust make pkg-config libffi openssl nodejs ripgrep ffmpeg
```

为什么需要这些软件包？
- `python` — 运行时 + venv 支持
- `git` — 克隆/更新仓库
- `clang`、`rust`、`make`、`pkg-config`、`libffi`、`openssl` — 在 Android 上构建部分 Python 依赖所需
- `nodejs` — 可选的 Node 运行时，用于经验证核心路径之外的实验
- `ripgrep` — 快速文件搜索
- `ffmpeg` — 媒体 / TTS 转换

### 2. 克隆 Hermes

```bash
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
```

如果你已经克隆但未包含子模块：

```bash
git submodule update --init --recursive
```

### 3. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install --upgrade pip setuptools wheel
```

`ANDROID_API_LEVEL` 对于基于 Rust / maturin 的软件包（如 `jiter`）非常重要。

### 4. 安装经验证的 Termux 捆绑包

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

如果你只需要最小核心智能体，也可以使用：

```bash
python -m pip install -e '.' -c constraints-termux.txt
```

### 5. 将 `hermes` 加入 Termux PATH

```bash
ln -sf "$PWD/venv/bin/hermes" "$PREFIX/bin/hermes"
```

`$PREFIX/bin` 已在 Termux 的 PATH 中，因此这样做可以让 `hermes` 命令在新 shell 中持久可用，无需每次都重新激活虚拟环境。

### 6. 验证安装

```bash
hermes version
hermes doctor
```

### 7. 启动 Hermes

```bash
hermes
```

---

## 推荐的后续设置

### 配置模型

```bash
hermes model
```

或直接在 `~/.hermes/.env` 中设置密钥。

### 稍后重新运行完整交互式设置向导

```bash
hermes setup
```

### 手动安装可选的 Node 依赖

经验证的 Termux 路径有意跳过了 Node/浏览器引导。如果你稍后想尝试浏览器工具：

```bash
pkg install nodejs-lts
npm install
```

浏览器工具会自动在其 PATH 搜索中包含 Termux 目录（`/data/data/com.termux/files/usr/bin`），因此无需额外配置 PATH 即可发现 `agent-browser` 和 `npx`。

在另有文档说明之前，请将 Android 上的浏览器 / WhatsApp 工具视为实验性功能。

---

## 故障排除

### 安装 `.[all]` 时出现 `No solution found`

请改用经验证的 Termux 捆绑包：

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

当前阻碍是 `voice` 扩展：
- `voice` 拉取 `faster-whisper`
- `faster-whisper` 依赖 `ctranslate2`
- `ctranslate2` 不发布 Android wheel

### `uv pip install` 在 Android 上失败

请改用 Termux 路径配合标准库 venv + `pip`：

```bash
python -m venv venv
source venv/bin/activate
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

### `jiter` / `maturin` 报错 `ANDROID_API_LEVEL`

在安装前显式设置 API 级别：

```bash
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

### `hermes doctor` 提示 ripgrep 或 Node 缺失

用 Termux 软件包安装它们：

```bash
pkg install ripgrep nodejs
```

### 安装 Python 软件包时构建失败

确保已安装构建工具链：

```bash
pkg install clang rust make pkg-config libffi openssl
```

然后重试：

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

---

## 手机上的已知限制

- Docker 后端不可用
- 经验证路径中无法使用通过 `faster-whisper` 进行的本地语音转录
- 安装程序有意跳过了浏览器自动化设置
- 部分可选扩展可能可以工作，但目前仅 `.[termux]` 和 `.[termux-all]` 被记录为经验证的 Android 捆绑包

如果你遇到新的 Android 特有问题，请提交 GitHub issue，并附上以下信息：
- 你的 Android 版本
- `termux-info`
- `python --version`
- `hermes doctor`
- 确切的安装命令及完整错误输出
