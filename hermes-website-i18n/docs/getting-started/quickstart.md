---
sidebar_position: 1
title: "快速入门"
description: "从零开始使用 Hermes Agent — 5 分钟内完成安装到首次对话"
---

# 快速入门

本指南带你从零开始，在 5 分钟内完成 Hermes 的安装和首次对话。

## 适用人群

- 首次接触 Hermes，需要最快上手指南
- 切换服务商，不想在配置上浪费时间
- 为团队或机器人设置 Hermes
- 安装成功但不知道怎么用

## 最快路径

| 目标 | 第一步 | 第二步 |
|---|---|---|
| 只想让 Hermes 跑起来 | `hermes setup` | 进行一次对话验证功能 |
| 已知道要用哪个服务商 | `hermes model` | 保存配置后开始对话 |
| 想设置机器人 | CLI 验证通过后 `hermes gateway setup` | 对接 Telegram、Discord 等平台 |
| 想用本地模型 | `hermes model` → 自定义端点 | 验证端点、模型名称和上下文长度 |
| 想要多服务商容错 | 先 `hermes model` | 基本对话正常后再添加路由和 fallback |

**铁律：** 如果 Hermes 连一次正常对话都无法完成，不要添加更多功能。先确保一次干净的对话成功，再逐步增加网关、定时任务、技能、语音、路由。

---

## 1. 安装 Hermes Agent

```bash
# Linux / macOS / WSL2
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Windows (PowerShell, 管理员)
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

验证安装：

```bash
hermes --version
```

## 2. 选择一个服务商

Hermes 支持所有兼容 OpenAI 接口的服务商。推荐以下方式：

- **OpenRouter** — 通过一个 API Key 访问数百个模型（推荐灵活使用）
- **Nous Portal** — Nous Research 自有推理端点
- **OpenAI** — GPT 系列模型
- **Anthropic** — Claude 系列模型
- **本地模型** — 通过 Ollama、vLLM 等

使用 `hermes model` 配置服务商。

## 3. 你的第一次对话

配置完成后，运行 `hermes` 启动对话：

```bash
hermes
```

试试这些开场：
- "帮我写一个 Python 脚本来整理下载文件夹"
- "解释一下这段代码做了什么"
- "给我推荐 5 个学习 AI 的资源"

## 4. 配置记忆系统

Hermes 默认启用记忆。每次对话结束后，它会自动总结关键信息并存储。你也可以手动要求：

```
记住：我们的项目使用 Python 3.11，部署在 AWS us-east-1
```

## 5. 探索 Skills

Skills 是 Hermes 的技能系统。安装技能包后，Hermes 获得特定领域能力。

```bash
# 查看可用技能
hermes skills list
```

## 下一步

- 配置 **[消息网关](/docs/user-guide/messaging)** 从 Telegram/Discord 访问 Hermes
- 了解 **[Skills 系统](/docs/user-guide/features/skills)** 创建自定义技能
- 设置 **[定时任务](/docs/user-guide/features/cron)** 实现自动化
- 查看 **[提示技巧](/docs/guides/tips)** 优化使用效果
