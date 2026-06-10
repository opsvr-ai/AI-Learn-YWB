---
sidebar_position: 3
title: '学习路径'
description: '根据你的经验水平和目标，选择适合你的 Hermes Agent 文档学习路径。'
---

# 学习路径

Hermes Agent 能做很多事情 —— CLI 助手、Telegram/Discord 机器人、任务自动化、RL 训练等等。本页面帮助你根据自己的经验水平和目标，确定从哪里开始以及阅读什么内容。

:::tip 从这里开始
如果你还没有安装 Hermes Agent，请先从[安装指南](/docs/getting-started/installation)开始，然后完成[快速入门](/docs/getting-started/quickstart)。以下所有内容都假设你已经完成了安装。
:::

## 如何使用本页面

- **知道自己的水平？** 跳转到[经验水平对照表](#按经验水平)并按你的层级顺序阅读。
- **有明确的目标？** 跳转到[按使用场景](#按使用场景)找到匹配的场景。
- **只是随便看看？** 查看[核心功能一览](#核心功能一览)表，快速了解 Hermes Agent 的全部功能。

## 按经验水平

| 水平 | 目标 | 推荐阅读 | 预计时间 |
|---|---|---|---|
| **初学者** | 完成安装、进行基本对话、使用内置工具 | [安装指南](/docs/getting-started/installation) → [快速入门](/docs/getting-started/quickstart) → [CLI 使用](/docs/user-guide/cli) → [配置](/docs/user-guide/configuration) | 约 1 小时 |
| **中级** | 搭建消息机器人、使用高级功能如记忆、定时任务和 Skills | [会话](/docs/user-guide/sessions) → [消息](/docs/user-guide/messaging) → [工具](/docs/user-guide/features/tools) → [Skills](/docs/user-guide/features/skills) → [记忆](/docs/user-guide/features/memory) → [定时任务](/docs/user-guide/features/cron) | 约 2–3 小时 |
| **高级** | 构建自定义工具、创建 Skills、使用 RL 训练模型、参与项目贡献 | [架构](/docs/developer-guide/architecture) → [添加工具](/docs/developer-guide/adding-tools) → [创建 Skills](/docs/developer-guide/creating-skills) → [RL 训练](/docs/user-guide/features/rl-training) → [贡献指南](/docs/developer-guide/contributing) | 约 4–6 小时 |

## 按使用场景

选择与你想要实现的目标相匹配的场景。每个场景都按你应该阅读的顺序链接到相关文档。

### "我想要一个 CLI 编程助手"

将 Hermes Agent 用作交互式终端助手，用于编写、审查和运行代码。

1. [安装指南](/docs/getting-started/installation)
2. [快速入门](/docs/getting-started/quickstart)
3. [CLI 使用](/docs/user-guide/cli)
4. [代码执行](/docs/user-guide/features/code-execution)
5. [上下文文件](/docs/user-guide/features/context-files)
6. [技巧与窍门](/docs/guides/tips)

:::tip
通过上下文文件将文件直接传入对话中。Hermes Agent 可以读取、编辑和运行你项目中的代码。
:::

### "我想要一个 Telegram/Discord 机器人"

将 Hermes Agent 部署为你喜爱的消息平台上的机器人。

1. [安装指南](/docs/getting-started/installation)
2. [配置](/docs/user-guide/configuration)
3. [消息概述](/docs/user-guide/messaging)
4. [Telegram 设置](/docs/user-guide/messaging/telegram)
5. [Discord 设置](/docs/user-guide/messaging/discord)
6. [语音模式](/docs/user-guide/features/voice-mode)
7. [在 Hermes 中使用语音模式](/docs/guides/use-voice-mode-with-hermes)
8. [安全](/docs/user-guide/security)

完整项目示例请参见：
- [每日简报机器人](/docs/guides/daily-briefing-bot)
- [团队 Telegram 助手](/docs/guides/team-telegram-assistant)

### "我想要自动化任务"

安排周期性任务、运行批量作业或将 Agent 操作串联起来。

1. [快速入门](/docs/getting-started/quickstart)
2. [定时任务调度](/docs/user-guide/features/cron)
3. [批量处理](/docs/user-guide/features/batch-processing)
4. [委托](/docs/user-guide/features/delegation)
5. [钩子](/docs/user-guide/features/hooks)

:::tip
定时任务让 Hermes Agent 可以按计划运行任务——每日摘要、定期检查、自动生成报告——无需你在场。
:::

### "我想要构建自定义工具/Skills"

使用你自己的工具和可复用的 Skill 包来扩展 Hermes Agent。

1. [插件](/docs/user-guide/features/plugins)
2. [构建 Hermes 插件](/docs/guides/build-a-hermes-plugin)
3. [工具概述](/docs/user-guide/features/tools)
4. [Skills 概述](/docs/user-guide/features/skills)
5. [MCP（模型上下文协议）](/docs/user-guide/features/mcp)
6. [架构](/docs/developer-guide/architecture)
7. [添加工具](/docs/developer-guide/adding-tools)
8. [创建 Skills](/docs/developer-guide/creating-skills)

:::tip
对于大多数自定义工具的创建，请从插件开始。[添加工具](/docs/developer-guide/adding-tools)页面适用于 Hermes 内置核心开发，而非通常的用户/自定义工具路径。
:::

### "我想要训练模型"

使用强化学习，通过 Hermes Agent 内置的 RL 训练管线来微调模型行为。

1. [快速入门](/docs/getting-started/quickstart)
2. [配置](/docs/user-guide/configuration)
3. [RL 训练](/docs/user-guide/features/rl-training)
4. [提供商路由](/docs/user-guide/features/provider-routing)
5. [架构](/docs/developer-guide/architecture)

:::tip
当你已经了解 Hermes Agent 如何处理对话和工具调用的基础知识后，RL 训练效果最佳。如果你是新手，请先完成初学者路径。
:::

### "我想将其作为 Python 库使用"

以编程方式将 Hermes Agent 集成到你自己的 Python 应用程序中。

1. [安装指南](/docs/getting-started/installation)
2. [快速入门](/docs/getting-started/quickstart)
3. [Python 库指南](/docs/guides/python-library)
4. [架构](/docs/developer-guide/architecture)
5. [工具](/docs/user-guide/features/tools)
6. [会话](/docs/user-guide/sessions)

## 核心功能一览

不确定有哪些功能可用？以下是主要功能的快速目录：

| 功能 | 功能说明 | 链接 |
|---|---|---|
| **工具** | Agent 可调用的内置工具（文件 I/O、搜索、终端命令等） | [工具](/docs/user-guide/features/tools) |
| **Skills** | 可安装的插件包，用于添加新能力 | [Skills](/docs/user-guide/features/skills) |
| **记忆** | 跨会话的持久记忆 | [记忆](/docs/user-guide/features/memory) |
| **上下文文件** | 将文件和目录传入对话上下文 | [上下文文件](/docs/user-guide/features/context-files) |
| **MCP** | 通过模型上下文协议连接外部工具服务器 | [MCP](/docs/user-guide/features/mcp) |
| **定时任务** | 安排周期性 Agent 任务 | [定时任务](/docs/user-guide/features/cron) |
| **委托** | 生成子 Agent 进行并行工作 | [委托](/docs/user-guide/features/delegation) |
| **代码执行** | 运行以编程方式调用 Hermes 工具的 Python 脚本 | [代码执行](/docs/user-guide/features/code-execution) |
| **浏览器** | 网页浏览和抓取 | [浏览器](/docs/user-guide/features/browser) |
| **钩子** | 事件驱动的回调和中间件 | [钩子](/docs/user-guide/features/hooks) |
| **批量处理** | 批量处理多个输入 | [批量处理](/docs/user-guide/features/batch-processing) |
| **RL 训练** | 使用强化学习微调模型 | [RL 训练](/docs/user-guide/features/rl-training) |
| **提供商路由** | 跨多个 LLM 提供商路由请求 | [提供商路由](/docs/user-guide/features/provider-routing) |

## 下一步阅读什么

根据你目前所处的阶段：

- **刚完成安装？** → 前往[快速入门](/docs/getting-started/quickstart)运行你的第一次对话。
- **已完成快速入门？** → 阅读 [CLI 使用](/docs/user-guide/cli)和[配置](/docs/user-guide/configuration)来定制你的设置。
- **对基础知识已熟悉？** → 探索[工具](/docs/user-guide/features/tools)、[Skills](/docs/user-guide/features/skills)和[记忆](/docs/user-guide/features/memory)，解锁 Agent 的全部能力。
- **正在为团队搭建？** → 阅读[安全](/docs/user-guide/security)和[会话](/docs/user-guide/sessions)，了解访问控制和对话管理。
- **准备开始构建？** → 深入[开发者指南](/docs/developer-guide/architecture)，了解内部原理并开始贡献。
- **想要实践示例？** → 查看[指南](/docs/guides/tips)部分，获取真实项目示例和技巧。

:::tip
你不需要阅读所有内容。选择与你目标匹配的路径，按顺序点击链接，你就能快速提高效率。你随时可以回到本页面找到下一步该做什么。
:::
