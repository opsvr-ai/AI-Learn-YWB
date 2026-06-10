---
sidebar_position: 10
title: "语音模式"
description: "与 Hermes Agent 进行实时语音对话 — 支持 CLI、Telegram、Discord（私信、文字频道和语音频道）"
---

# 语音模式

Hermes Agent 支持在 CLI 和消息平台上进行完整的语音交互。你可以使用麦克风与 Agent 对话，收听语音回复，并在 Discord 语音频道中进行实时语音对话。

如果你想要一份包含推荐配置和实际使用模式的实操设置指南，请参阅 [使用 Hermes 语音模式](/docs/guides/use-voice-mode-with-hermes)。

## 前置条件

在使用语音功能之前，请确保你已具备：

1. **已安装 Hermes Agent** — `pip install hermes-agent`（参见 [安装指南](/docs/getting-started/installation)）
2. **已配置 LLM 提供商** — 运行 `hermes model` 或在 `~/.hermes/.env` 中设置你偏好的提供商凭据
3. **基础设置可正常工作** — 运行 `hermes` 验证 Agent 能响应文字消息后再启用语音

:::tip
`~/.hermes/` 目录和默认的 `config.yaml` 会在你首次运行 `hermes` 时自动创建。你只需手动创建 `~/.hermes/.env` 来配置 API 密钥。
:::

## 概述

| 功能 | 平台 | 描述 |
|---------|----------|-------------|
| **交互式语音** | CLI | 按 Ctrl+B 开始录音，Agent 自动检测静音并回复 |
| **自动语音回复** | Telegram、Discord | Agent 在发送文字回复的同时发送语音音频 |
| **语音频道** | Discord | Bot 加入语音频道，监听用户发言并语音回复 |

## 环境要求

### Python 包

```bash
# CLI 语音模式（麦克风 + 音频播放）
pip install "hermes-agent[voice]"

# Discord + Telegram 消息（包含用于语音频道支持的 discord.py[voice]）
pip install "hermes-agent[messaging]"

# 高级 TTS（ElevenLabs）
pip install "hermes-agent[tts-premium]"

# 本地 TTS（NeuTTS，可选）
python -m pip install -U neutts[all]

# 一次性安装全部
pip install "hermes-agent[all]"
```

| Extra | 包含的包 | 用于 |
|-------|----------|-------------|
| `voice` | `sounddevice`、`numpy` | CLI 语音模式 |
| `messaging` | `discord.py[voice]`、`python-telegram-bot`、`aiohttp` | Discord 和 Telegram Bot |
| `tts-premium` | `elevenlabs` | ElevenLabs TTS 提供商 |

可选的本地 TTS 提供商：通过 `python -m pip install -U neutts[all]` 单独安装 `neutts`。首次使用时它会自动下载模型。

:::info
`discord.py[voice]` 会自动安装 **PyNaCl**（用于语音加密）和 **opus 绑定**。这是 Discord 语音频道支持所必需的。
:::

### 系统依赖

```bash
# macOS
brew install portaudio ffmpeg opus
brew install espeak-ng   # NeuTTS 需要

# Ubuntu/Debian
sudo apt install portaudio19-dev ffmpeg libopus0
sudo apt install espeak-ng   # NeuTTS 需要
```

| 依赖 | 用途 | 用于 |
|-----------|---------|-------------|
| **PortAudio** | 麦克风输入和音频播放 | CLI 语音模式 |
| **ffmpeg** | 音频格式转换（MP3 → Opus、PCM → WAV） | 所有平台 |
| **Opus** | Discord 语音编解码器 | Discord 语音频道 |
| **espeak-ng** | 音素化后端 | 本地 NeuTTS 提供商 |

### API 密钥

添加到 `~/.hermes/.env`：

```bash
# 语音转文字 — 本地提供商无需任何密钥
# pip install faster-whisper          # 免费，本地运行，推荐
GROQ_API_KEY=your-key                 # Groq Whisper — 快速，免费额度（云端）
VOICE_TOOLS_OPENAI_KEY=your-key       # OpenAI Whisper — 付费（云端）

# 文字转语音（可选 — Edge TTS 和 NeuTTS 无需任何密钥即可使用）
ELEVENLABS_API_KEY=***           # ElevenLabs — 高级品质
# 上面的 VOICE_TOOLS_OPENAI_KEY 也可启用 OpenAI TTS
```

:::tip
如果安装了 `faster-whisper`，语音模式进行 STT 时**零 API 密钥**即可工作。模型（`base` 版本约 150 MB）会在首次使用时自动下载。
:::

---

## CLI 语音模式

语音模式在 **经典 CLI**（`hermes chat`）和 **TUI**（`hermes --tui`）中均可使用。两者的行为完全一致 — 相同的斜杠命令、相同的 VAD 静音检测、相同的流式 TTS、相同的幻觉过滤。TUI 会额外将崩溃取证日志转发到 `~/.hermes/logs/`，这样在非主流音频后端上发生的按键通话故障可以被带有完整堆栈跟踪地报告，而不是静默消失。

### 快速开始

启动 CLI 并启用语音模式：

```bash
hermes                # 启动交互式 CLI
```

然后在 CLI 中使用以下命令：

```
/voice          切换语音模式 开/关
/voice on       启用语音模式
/voice off      禁用语音模式
/voice tts      切换 TTS 输出
/voice status   显示当前状态
```

### 工作流程

1. 用 `hermes` 启动 CLI，用 `/voice on` 启用语音模式
2. **按下 Ctrl+B** — 播放一声提示音（880Hz），开始录音
3. **说话** — 实时音频电平条显示你的输入：`● [▁▂▃▅▇▇▅▂] ❯`
4. **停止说话** — 静音 3 秒后，录音自动停止
5. **播放两声提示音**（660Hz）确认录音结束
6. 音频通过 Whisper 转写并发送给 Agent
7. 如果 TTS 已启用，Agent 的回复会被朗读出来
8. 录音**自动重新开始** — 无需按任何键即可继续说话

这个循环会持续进行，直到你在录音期间按下 **Ctrl+B**（退出连续模式），或者连续 3 次录音都未检测到语音。

:::tip
录音键可通过 `~/.hermes/config.yaml` 中的 `voice.record_key` 配置（默认：`ctrl+b`）。
:::

### 静音检测

两阶段算法检测你是否已说完话：

1. **语音确认** — 等待音频 RMS 值超过阈值（200）持续至少 0.3 秒，容忍音节间的短暂下降
2. **结束检测** — 一旦确认有语音，在连续静音 3.0 秒后触发结束

如果超过 15 秒完全未检测到任何语音，录音会自动停止。

`sound_threshold` 和 `silence_duration` 均可在 `config.yaml` 中配置。你也可以通过 `voice.beep_enabled: false` 禁用录音开始/停止的提示音。

### 流式 TTS

启用 TTS 后，Agent 会在生成文字的过程中**逐句**朗读回复 — 你无需等待完整响应：

1. 将文字增量缓冲为完整句子（最少 20 个字符）
2. 去除 markdown 格式和 ` thinking` 块
3. 实时对每个句子生成并播放音频

### 幻觉过滤

Whisper 有时会从静音或背景噪音中生成虚假文字（"感谢观看"、"订阅"等）。Agent 使用一组涵盖多语言的 26 个已知幻觉短语，以及一个能捕获重复变体的正则表达式模式来过滤这些内容。

---

## Gateway 语音回复（Telegram 和 Discord）

如果你还没有设置消息 Bot，请参阅各平台专属指南：
- [Telegram 设置指南](../messaging/telegram.md)
- [Discord 设置指南](../messaging/discord.md)

启动 Gateway 以连接你的消息平台：

```bash
hermes gateway        # 启动 Gateway（连接到已配置的平台）
hermes gateway setup  # 交互式设置向导，用于首次配置
```

### Discord：频道 vs 私信

Bot 在 Discord 上支持两种交互模式：

| 模式 | 如何对话 | 需要提及 | 设置 |
|------|------------|-----------------|-------|
| **私信（DM）** | 打开 Bot 的个人资料 → "发消息" | 否 | 立即可用 |
| **服务器频道** | 在 Bot 所在的文字频道中输入 | 是（`@bot名字`） | Bot 必须被邀请到服务器 |

**私信（推荐个人使用）：** 只需打开与 Bot 的私信并输入 — 无需 @提及。语音回复和所有命令与在频道中一样工作。

**服务器频道：** Bot 仅在你 @提及 它时才会响应（例如 `@hermesbyt4 你好`）。请确保你从提及弹出窗口中选择的是 **Bot 用户**，而非同名的角色。

:::tip
要在服务器频道中禁用提及要求，在 `~/.hermes/.env` 中添加：
```bash
DISCORD_REQUIRE_MENTION=false
```
或者将特定频道设置为自由回复（无需提及）：
```bash
DISCORD_FREE_RESPONSE_CHANNELS=123456789,987654321
```
:::

### 命令

以下命令在 Telegram 和 Discord（私信和文字频道）中均可使用：

```
/voice          切换语音模式 开/关
/voice on       仅在你发送语音消息时进行语音回复
/voice tts      对所有消息进行语音回复
/voice off      禁用语音回复
/voice status   显示当前设置
```

### 模式

| 模式 | 命令 | 行为 |
|------|---------|----------|
| `off` | `/voice off` | 仅文字（默认） |
| `voice_only` | `/voice on` | 仅在你发送语音消息时朗读回复 |
| `all` | `/voice tts` | 对每条消息都朗读回复 |

语音模式设置在 Gateway 重启后会持续保留。

### 各平台发送方式

| 平台 | 格式 | 备注 |
|----------|--------|-------|
| **Telegram** | 语音气泡（Opus/OGG） | 在聊天中内联播放。ffmpeg 按需将 MP3 转换为 Opus |
| **Discord** | 原生语音气泡（Opus/OGG） | 像用户语音消息一样内联播放。如果语音气泡 API 失败则降级为文件附件 |

---

## Discord 语音频道

最具沉浸感的语音功能：Bot 加入 Discord 语音频道，监听用户发言，转写语音内容，通过 Agent 处理，然后在语音频道中朗读回复。

### 设置

#### 1. Discord Bot 权限

如果你已经为文字功能设置了 Discord Bot（参见 [Discord 设置指南](../messaging/discord.md)），你需要添加语音权限。

前往 [Discord 开发者门户](https://discord.com/developers/applications) → 你的应用 → **Installation** → **Default Install Settings** → **Guild Install**：

**在现有文字权限基础上添加以下权限：**

| 权限 | 用途 | 是否必需 |
|-----------|---------|----------|
| **Connect** | 加入语音频道 | 是 |
| **Speak** | 在语音频道中播放 TTS 音频 | 是 |
| **Use Voice Activity** | 检测用户是否在说话 | 推荐 |

**更新后的权限整数：**

| 级别 | 整数 | 包含内容 |
|-------|---------|----------------|
| 仅文字 | `274878286912` | 查看频道、发送消息、读取历史、嵌入、附件、帖子、反应 |
| 文字 + 语音 | `274881432640` | 上述全部 + Connect、Speak |

**使用更新后的权限 URL 重新邀请 Bot：**

```
https://discord.com/oauth2/authorize?client_id=YOUR_APP_ID&scope=bot+applications.commands&permissions=274881432640
```

将 `YOUR_APP_ID` 替换为你在开发者门户中的 Application ID。

:::warning
重新邀请 Bot 到它已在的服务器会更新其权限而不会移除它。你不会有任何数据或配置丢失。
:::

#### 2. 特权 Gateway Intents

在 [开发者门户](https://discord.com/developers/applications) → 你的应用 → **Bot** → **Privileged Gateway Intents** 中，启用所有三个：

| Intent | 用途 |
|--------|---------|
| **Presence Intent** | 检测用户在线/离线状态 |
| **Server Members Intent** | 将 `DISCORD_ALLOWED_USERS` 中的用户名解析为数字 ID（有条件的） |
| **Message Content Intent** | 读取频道中的文字消息内容 |

**Message Content Intent** 是必需的。**Server Members Intent** 仅在你的 `DISCORD_ALLOWED_USERS` 列表使用用户名时才需要 — 如果你使用数字用户 ID，可以保持关闭。语音频道 SSRC → user_id 的映射来自 Discord 语音 websocket 的 SPEAKING 操作码，**不**需要 Server Members Intent。

#### 3. Opus 编解码器

Opus 编解码器库必须安装在运行 Gateway 的机器上：

```bash
# macOS（Homebrew）
brew install opus

# Ubuntu/Debian
sudo apt install libopus0
```

Bot 会自动从以下位置加载编解码器：
- **macOS：** `/opt/homebrew/lib/libopus.dylib`
- **Linux：** `libopus.so.0`

#### 4. 环境变量

```bash
# ~/.hermes/.env

# Discord Bot（已为文字功能配置）
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_ALLOWED_USERS=your-user-id

# STT — 本地提供商无需密钥（pip install faster-whisper）
# GROQ_API_KEY=your-key            # 替代方案：云端，快速，免费额度

# TTS — 可选。Edge TTS 和 NeuTTS 无需密钥。
# ELEVENLABS_API_KEY=***      # 高级品质
# VOICE_TOOLS_OPENAI_KEY=***  # OpenAI TTS / Whisper
```

### 启动 Gateway

```bash
hermes gateway        # 使用现有配置启动
```

Bot 应在几秒内上线 Discord。

### 命令

在 Bot 所在的 Discord 文字频道中使用以下命令：

```
/voice join      让 Bot 加入你当前所在的语音频道
/voice channel   /voice join 的别名
/voice leave     让 Bot 断开语音频道连接
/voice status    显示语音模式和已连接的频道
```

:::info
你必须先进入一个语音频道才能运行 `/voice join`。Bot 会加入你所在的同一个语音频道。
:::

### 工作流程

当 Bot 加入语音频道后，它会：

1. **监听** 每个用户的独立音频流
2. **检测静音** — 至少 0.5 秒语音后出现 1.5 秒静音时触发处理
3. **转写** 音频通过 Whisper STT（本地、Groq 或 OpenAI）
4. **处理** 通过完整的 Agent 流水线（会话、工具、记忆）
5. **朗读** 通过 TTS 在语音频道中回复

### 文字频道集成

当 Bot 在语音频道中时：

- 转写内容会显示在文字频道中：`[Voice] @用户：你说了什么`
- Agent 的回复会以文字形式发送到频道中，同时也在语音频道中朗读
- 文字频道是执行 `/voice join` 命令的那个频道

### 回声防止

Bot 在播放 TTS 回复时会自动暂停音频监听，防止它听到并重新处理自己的输出。

### 访问控制

只有列在 `DISCORD_ALLOWED_USERS` 中的用户才能通过语音进行交互。其他用户的音频会被静默忽略。

```bash
# ~/.hermes/.env
DISCORD_ALLOWED_USERS=284102345871466496
```

---

## 配置参考

### config.yaml

```yaml
# 语音录制（CLI）
voice:
  record_key: "ctrl+b"            # 开始/停止录音的按键
  max_recording_seconds: 120       # 最长录音时长
  auto_tts: false                  # 启动语音模式时自动启用 TTS
  beep_enabled: true               # 播放录音开始/停止提示音
  silence_threshold: 200           # RMS 值（0-32767），低于此值视为静音
  silence_duration: 3.0            # 自动停止前的静音秒数

# 语音转文字
stt:
  enabled: true                     # 设为 false 以跳过自动转写 —
                                    # Gateway 仍会缓存音频文件并将其路径
                                    # 作为入站消息的一部分传递给 Agent，
                                    # 适用于自定义流水线
                                    #（说话人分离、对齐、归档等）
  provider: "local"                  # "local"（免费）| "groq" | "openai"
  local:
    model: "base"                    # tiny、base、small、medium、large-v3
  # model: "whisper-1"              # 旧版：在未设置 provider 时使用

# 文字转语音
tts:
  provider: "edge"                 # "edge"（免费）| "elevenlabs" | "openai" | "neutts" | "minimax"
  edge:
    voice: "en-US-AriaNeural"      # 322 种声音，74 种语言
  elevenlabs:
    voice_id: "pNInz6obpgDQGcFmaJgB"    # Adam
    model_id: "eleven_multilingual_v2"
  openai:
    model: "gpt-4o-mini-tts"
    voice: "alloy"                 # alloy、echo、fable、onyx、nova、shimmer
    base_url: "https://api.openai.com/v1"  # 可选：覆盖为自托管或兼容 OpenAI 的端点
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```

### 环境变量

```bash
# 语音转文字提供商（本地无需密钥）
# pip install faster-whisper        # 免费本地 STT — 无需 API 密钥
GROQ_API_KEY=...                    # Groq Whisper（快速，免费额度）
VOICE_TOOLS_OPENAI_KEY=...         # OpenAI Whisper（付费）

# STT 高级覆盖选项（可选）
STT_GROQ_MODEL=whisper-large-v3-turbo    # 覆盖默认的 Groq STT 模型
STT_OPENAI_MODEL=whisper-1               # 覆盖默认的 OpenAI STT 模型
GROQ_BASE_URL=https://api.groq.com/openai/v1     # 自定义 Groq 端点
STT_OPENAI_BASE_URL=https://api.openai.com/v1    # 自定义 OpenAI STT 端点

# 文字转语音提供商（Edge TTS 和 NeuTTS 无需密钥）
ELEVENLABS_API_KEY=***             # ElevenLabs（高级品质）
# 上面的 VOICE_TOOLS_OPENAI_KEY 也可启用 OpenAI TTS

# Discord 语音频道
DISCORD_BOT_TOKEN=...
DISCORD_ALLOWED_USERS=...
```

### STT 提供商对比

| 提供商 | 模型 | 速度 | 质量 | 费用 | API 密钥 |
|----------|-------|-------|---------|------|---------|
| **本地** | `base` | 快（取决于 CPU/GPU） | 良好 | 免费 | 否 |
| **本地** | `small` | 中等 | 更好 | 免费 | 否 |
| **本地** | `large-v3` | 慢 | 最佳 | 免费 | 否 |
| **Groq** | `whisper-large-v3-turbo` | 非常快（~0.5s） | 良好 | 免费额度 | 是 |
| **Groq** | `whisper-large-v3` | 快（~1s） | 更好 | 免费额度 | 是 |
| **OpenAI** | `whisper-1` | 快（~1s） | 良好 | 付费 | 是 |
| **OpenAI** | `gpt-4o-transcribe` | 中等（~2s） | 最佳 | 付费 | 是 |

提供商优先级（自动降级）：**本地** > **groq** > **openai**

### TTS 提供商对比

| 提供商 | 质量 | 费用 | 延迟 | 是否需要密钥 |
|----------|---------|------|---------|-------------|
| **Edge TTS** | 良好 | 免费 | ~1s | 否 |
| **ElevenLabs** | 优秀 | 付费 | ~2s | 是 |
| **OpenAI TTS** | 良好 | 付费 | ~1.5s | 是 |
| **NeuTTS** | 良好 | 免费 | 取决于 CPU/GPU | 否 |

NeuTTS 使用上面的 `tts.neutts` 配置块。

---

## 故障排查

### "未找到音频设备"（CLI）

PortAudio 未安装：

```bash
brew install portaudio    # macOS
sudo apt install portaudio19-dev  # Ubuntu
```

### Bot 在 Discord 服务器频道中不响应

Bot 在服务器频道中默认需要 @提及。请确保你：

1. 输入 `@` 并选择 **Bot 用户**（带有 #区分号），而不是同名的**角色**
2. 或者改用私信 — 无需提及
3. 或者在 `~/.hermes/.env` 中设置 `DISCORD_REQUIRE_MENTION=false`

### Bot 加入了语音频道但听不到我说话

- 检查你的 Discord 用户 ID 是否在 `DISCORD_ALLOWED_USERS` 中
- 确保你在 Discord 中没有被静音
- Bot 需要从 Discord 收到 SPEAKING 事件后才能映射你的音频 — 请在加入后的几秒内开始说话

### Bot 能听到我但不回复

- 验证 STT 是否可用：安装 `faster-whisper`（无需密钥）或设置 `GROQ_API_KEY` / `VOICE_TOOLS_OPENAI_KEY`
- 检查 LLM 模型是否已配置且可访问
- 查看 Gateway 日志：`tail -f ~/.hermes/logs/gateway.log`

### Bot 以文字回复但不在语音频道中回复

- TTS 提供商可能失败 — 检查 API 密钥和配额
- Edge TTS（免费，无需密钥）是默认降级方案
- 检查日志中的 TTS 错误

### Whisper 返回乱码文字

幻觉过滤器在大多数情况下会自动处理。如果仍然出现虚假转写：

- 在更安静的环境中使用
- 调整配置中的 `silence_threshold`（值越高 = 越不敏感）
- 尝试不同的 STT 模型
