---
title: "功能概览"
sidebar_label: "概览"
sidebar_position: 1
---

# 功能概览

Hermes Agent 包含丰富的功能集，远不止基础的聊天对话。从持久化记忆和文件感知上下文，到浏览器自动化和语音对话，这些功能相互配合，使 Hermes 成为一款强大的自主助手。

## 核心功能

- **[工具与工具集](tools.md)** — 工具是扩展 Agent 能力的函数。它们被组织为逻辑工具集，可按平台启用或禁用，涵盖网络搜索、终端执行、文件编辑、记忆、委派等功能。
- **[Skills 系统](skills.md)** — 按需加载的知识文档，Agent 可在需要时读取。Skills 采用渐进式披露模式以最小化 token 消耗，并兼容 [agentskills.io](https://agentskills.io/specification) 开放标准。
- **[持久化记忆](memory.md)** — 跨会话持久化的限界精选记忆。Hermes 通过 `MEMORY.md` 和 `USER.md` 记住你的偏好、项目、环境以及学到的东西。
- **[上下文文件](context-files.md)** — Hermes 自动发现并加载项目上下文文件（`.hermes.md`、`AGENTS.md`、`CLAUDE.md`、`SOUL.md`、`.cursorrules`），这些文件会影响 Agent 在你的项目中的行为方式。
- **[上下文引用](context-references.md)** — 输入 `@` 后跟引用内容，即可将文件、文件夹、git diff 和 URL 直接注入到你的消息中。Hermes 会内联展开引用并自动追加内容。
- **[检查点](../checkpoints-and-rollback.md)** — Hermes 在进行文件更改前自动快照你的工作目录，出问题时可通过 `/rollback` 回滚，为你提供安全网。

## 自动化

- **[定时任务（Cron）](cron.md)** — 使用自然语言或 cron 表达式调度任务自动运行。任务可附加 Skills、将结果分发到任意平台，并支持暂停/恢复/编辑操作。
- **[子Agent委派](delegation.md)** — `delegate_task` 工具可以创建具有隔离上下文、受限工具集和独立终端会话的子 Agent 实例。默认支持 3 个并发子Agent（可配置），实现并行工作流。
- **[代码执行](code-execution.md)** — `execute_code` 工具允许 Agent 编写以编程方式调用 Hermes 工具的 Python 脚本，通过沙盒化的 RPC 执行将多步工作流整合为单次 LLM 轮次。
- **[事件钩子](hooks.md)** — 在关键生命周期节点运行自定义代码。Gateway 钩子处理日志记录、告警和 Webhook；Plugin 钩子处理工具拦截、指标监控和安全护栏。
- **[批量处理](batch-processing.md)** — 并行运行 Hermes Agent 处理成百上千条提示词，生成结构化的 ShareGPT 格式轨迹数据，用于训练数据生成或评估。

## 媒体与网页

- **[语音模式](voice-mode.md)** — 跨 CLI 和消息平台的完整语音交互。使用麦克风与 Agent 对话，收听语音回复，并在 Discord 语音频道中进行实时语音对话。
- **[浏览器自动化](browser.md)** — 支持多种后端的完整浏览器自动化：Browserbase 云端、Browser Use 云端、通过 CDP 连接本地 Chrome/Brave/Chromium/Edge，或本地 Chromium。可浏览网站、填写表单和提取信息。
- **[视觉与图片粘贴](vision.md)** — 多模态视觉支持。将剪贴板中的图片粘贴到 CLI 中，让 Agent 使用任意支持视觉功能的模型进行分析、描述或处理。
- **[图片生成](image-generation.md)** — 使用 FAL.ai 通过文本提示词生成图片。支持九种模型（FLUX 2 Klein/Pro、GPT-Image 1.5/2、Nano Banana Pro、Ideogram V3、Recraft V4 Pro、Qwen、Z-Image Turbo）；通过 `hermes tools` 选择模型。
- **[语音与 TTS](tts.md)** — 跨所有消息平台的文本转语音输出和语音消息转录，提供十种内置提供商选项：Edge TTS（免费）、ElevenLabs、OpenAI TTS、MiniMax、Mistral Voxtral、Google Gemini、xAI、NeuTTS、KittenTTS 和 Piper —— 外加自定义命令提供商，可对接任意本地 TTS CLI。

## 集成

- **[MCP 集成](mcp.md)** — 通过 stdio 或 HTTP 传输连接任意 MCP 服务器。无需编写原生 Hermes 工具即可访问来自 GitHub、数据库、文件系统和内部 API 的外部工具。支持按服务器的工具过滤和采样。
- **[提供商路由](provider-routing.md)** — 精细控制哪些 AI 提供商处理你的请求。通过排序、白名单、黑名单和优先级排序来优化成本、速度或质量。
- **[回退提供商](fallback-providers.md)** — 当主模型遇到错误时自动切换到备选 LLM 提供商，包括对视觉和压缩等辅助任务的独立回退。
- **[凭据池](credential-pools.md)** — 将 API 调用分发到同一提供商的多个密钥上。遇到速率限制或故障时自动轮换。
- **[Prompt 缓存](../configuration#prompt-caching)** — 内置跨会话 1 小时前缀缓存，适用于原生 Anthropic、OpenRouter 和 Nous Portal 上的 Claude。始终开启，无需配置。
- **[记忆提供商](memory-providers.md)** — 接入外部记忆后端（Honcho、OpenViking、Mem0、Hindsight、Holographic、RetainDB、ByteRover、Supermemory），在内置记忆系统之外实现跨会话用户建模和个性化。
- **[API 服务器](api-server.md)** — 将 Hermes 暴露为 OpenAI 兼容的 HTTP 端点。可连接任意支持 OpenAI 格式的前端 —— Open WebUI、LobeChat、LibreChat 等。
- **[IDE 集成（ACP）](acp.md)** — 在支持 ACP 的编辑器（如 VS Code、Zed 和 JetBrains）中使用 Hermes。聊天、工具活动、文件差异和终端命令都在你的编辑器内呈现。
- **[RL 训练](rl-training.md)** — 从 Agent 会话中生成轨迹数据，用于强化学习和模型微调。

## 自定义

- **[个性化与 SOUL.md](personality.md)** — 完全可自定义的 Agent 个性。`SOUL.md` 是主要的身份文件 —— 系统提示词中的第一项内容 —— 你可以为每个会话切换内置或自定义的 `/personality` 预设。
- **[皮肤与主题](skins.md)** — 自定义 CLI 的视觉呈现：横幅颜色、旋转动画的面孔和动词、响应框标签、品牌文本以及工具活动前缀。
- **[插件](plugins.md)** — 在不修改核心代码的情况下添加自定义工具、钩子和集成。三种插件类型：通用插件（工具/钩子）、记忆提供商（跨会话知识）和上下文引擎（替代上下文管理）。通过统一的 `hermes plugins` 交互界面进行管理。
