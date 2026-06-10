---
slug: /
sidebar_position: 0
title: "Hermes Agent 文档"
description: "由 Nous Research 打造的自我进化 AI 智能体。内置学习循环，能从经验中创建技能，在使用中不断改进，跨会话持续记忆。"
hide_table_of_contents: true
displayed_sidebar: docs
---

# Hermes Agent

由 [Nous Research](https://nousresearch.com) 打造的自我进化 AI 智能体。唯一内置学习循环的智能体 — 它能从经验中创建技能，在使用过程中自我改进，主动提示自己持续积累知识，并逐步构建对你的深度理解。

<div style={{display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap'}}>
  <a href="/docs/getting-started/installation" style={{display: 'inline-block', padding: '0.6rem 1.2rem', backgroundColor: '#FFD700', color: '#07070d', borderRadius: '8px', fontWeight: 600, textDecoration: 'none'}}>快速开始 →</a>
  <a href="https://github.com/NousResearch/hermes-agent" style={{display: 'inline-block', padding: '0.6rem 1.2rem', border: '1px solid rgba(255,215,0,0.2)', borderRadius: '8px', textDecoration: 'none'}}>GitHub 仓库</a>
</div>

## 安装

**Linux / macOS / WSL2**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

**Windows（原生 PowerShell）** — *早期测试版，[详情 →](/docs/user-guide/windows-native)*

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

**Android（Termux）** — 与 Linux 使用相同的 curl 命令；安装器会自动检测 Termux 环境。

详见完整的 **[安装指南](/docs/getting-started/installation)**，了解安装器的工作方式、用户级与系统级安装的区别，以及 Windows 特定说明。

## 什么是 Hermes Agent？

它不是绑定在 IDE 上的编程助手，也不是单一 API 的聊天包装器。它是一个**自主智能体**，运行越久越强大。可以部署在任何地方 — 从 5 美元的 VPS 到 GPU 集群再到无服务器基础设施（Daytona、Modal），空闲时几乎零成本。你可以通过 Telegram 与它对话，而它在云端 VM 上自主工作，你甚至无需 SSH 登录。

## 快速导航

| | |
|---|---|
| 启动 | **[安装指南](/docs/getting-started/installation)** | 60 秒内在 Linux、macOS、WSL2 或 Windows 上完成安装 |
| 从零开始教程 | **[快速入门](/docs/getting-started/quickstart)** | 首次对话及核心功能体验 |
| 学习路线 | **[学习路径](/docs/getting-started/learning-path)** | 根据经验水平找到合适的文档 |
| 配置文件 | **[配置说明](/docs/user-guide/configuration)** | 配置文件、服务商、模型及选项设置 |
| 消息网关 | **[消息集成](/docs/user-guide/messaging)** | 对接 Telegram、Discord、Slack、WhatsApp、Teams 等 |
| 工具系统 | **[工具 & 工具集](/docs/user-guide/features/tools)** | 70+ 内置工具及其配置方式 |
| 记忆系统 | **[记忆系统](/docs/user-guide/features/memory)** | 跨会话持续增长的持久化记忆 |
| 技能系统 | **[Skills 系统](/docs/user-guide/features/skills)** | 智能体自动创建并复用的程序性记忆 |
| MCP 集成 | **[MCP 集成](/docs/user-guide/features/mcp)** | 连接 MCP 服务器，过滤工具，安全扩展 Hermes |
| MCP 实战 | **[使用 MCP 与 Hermes](/docs/guides/use-mcp-with-hermes)** | 实用的 MCP 配置模式、示例和教程 |
| 语音交互 | **[语音模式](/docs/user-guide/features/voice-mode)** | CLI、Telegram、Discord 等平台的实时语音交互 |
| 个性系统 | **[Personality & SOUL.md](/docs/user-guide/features/personality)** | 用全局 SOUL.md 定义 Hermes 的默认对话风格 |
| 项目上下文 | **[上下文文件](/docs/user-guide/features/context-files)** | 影响每次对话的项目上下文文件 |
| 安全机制 | **[安全说明](/docs/user-guide/security)** | 命令审批、授权管理、容器隔离
| 实用技巧 | **[提示与最佳实践](/docs/guides/tips)** | 最大化发挥 Hermes 效能的技巧 |
| 架构说明 | **[架构文档](/docs/developer-guide/architecture)** | 深入理解 Hermes 的工作原理 |
| 常见问题 | **[FAQ 常见问题](/docs/reference/faq)** | 常见问题与解决方案 |

## 核心特性

- **闭环学习系统** — 智能体自主管理记忆，定期提示回顾，自主创建技能，使用中自我改进，FTS5 跨会话检索配合 LLM 摘要，以及 [Honcho](https://github.com/plastic-labs/honcho) 辩证用户建模
- **到处运行，不止于笔记本** — 6 种终端后端：本地、Docker、SSH、Daytona、Singularity、Modal。Daytona 和 Modal 提供无服务器持久化 — 环境空闲时自动休眠，几乎零成本
- **生活在你所在的地方** — CLI、Telegram、Discord、Slack、WhatsApp、Signal、Matrix、Mattermost、Email、SMS、钉钉、飞书、企业微信、微信、QQ Bot、元宝、BlueBubbles、Home Assistant、Microsoft Teams、Google Chat 等 — 20+ 平台统一接入
- **由模型训练者打造** — [Nous Research](https://nousresearch.com) 出品，Hermes、Nomos、Psyche 模型的创造者。支持 [Nous Portal](https://portal.nousresearch.com)、[OpenRouter](https://openrouter.ai)、OpenAI 或任意兼容端点
- **定时自动化** — 内置 cron 定时任务，支持向任意平台推送
- **委托与并行** — 为子智能体派生独立工作流并行处理。通过 `execute_code` 实现编程式工具调用，将多步流程压缩为单次推理调用
- **开放标准技能** — 兼容 [agentskills.io](https://agentskills.io)。技能可移植、可共享，由 Skills Hub 社区贡献
- **完整 Web 控制** — 搜索、提取、浏览、视觉识别、图片生成、文字转语音
- **MCP 支持** — 连接任意 MCP 服务器扩展工具能力
- **研究就绪** — 批量处理、轨迹导出、RL 训练（Atropos）。由 [Nous Research](https://nousresearch.com) 打造 — Hermes、Nomos、Psyche 模型的实验室

## 面向LLM和编码助手

本文档的机器可读入口：

- **[`/llms.txt`](/llms.txt)** — 每个文档页面的精选索引及简短描述。约 17 KB，适合加载到 LLM 上下文中。
- **[`/llms-full.txt`](/llms-full.txt)** — 所有文档页连接为单个 markdown 文件，适合一次性导入。约 1.8 MB。

两个文件也可通过 `/docs/llms.txt` 和 `/docs/llms-full.txt` 访问。每次部署时自动生成。
