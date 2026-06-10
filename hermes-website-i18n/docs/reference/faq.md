---
sidebar_position: 3
title: "常见问题 FAQ"
description: "Hermes Agent 常见问题与排障指南"
---

# 常见问题 FAQ

## 一般问题

### Hermes 支持哪些 LLM 服务商？

支持所有兼容 OpenAI API 的服务商，包括：

- **OpenRouter** — 通过一个 API Key 访问数百个模型（推荐）
- **Nous Portal** — Nous Research 自有推理端点
- **OpenAI** — GPT 系列
- **Anthropic** — Claude 系列
- **Google** — Gemini 系列
- **本地模型** — Ollama、vLLM、llama.cpp 等

使用 `hermes model` 命令配置服务商。

### Hermes 是免费的吗？

是的，Hermes Agent 是开源软件。但使用 LLM 服务需要你自己提供 API Key，产生相应的 API 调用费用。

### Hermes 和 Claude Code / Cursor 有什么区别？

Hermes 是一个**自主智能体平台**，不仅限于代码编写。它能：
- 在 20+ 平台上运行（Telegram、Discord、Slack 等）
- 拥有持久化记忆和自学习技能
- 定时自动化任务
- 不依赖 IDE，可在服务器上独立运行

Claude Code 和 Cursor 是专注于代码编写的编程助手。

## 配置问题

### 如何切换模型？

```bash
hermes model
```

交互式选择菜单会引导你完成配置。

### 如何配置多个服务商？

编辑 `~/.hermes/.env`，添加多个 API Key。然后在配置文件中设置路由规则。

### 如何重置配置？

```bash
rm -rf ~/.hermes
hermes setup
```

## 使用问题

### 第一次对话应该说什么？

从具体任务开始：

```
帮我写一个 Python 脚本来批量重命名文件夹中的图片，按拍摄日期命名
```

### 如何让 Hermes 记住我的偏好？

在对话中直接告诉它，或编辑 `~/.hermes/SOUL.md` 设置默认行为。

### 技能不生效怎么办？

```bash
# 确认技能是否已安装
hermes skills list
# 重启 Hermes
exit 后再运行 hermes
```

## 排障

### Hermes 启动失败

检查：
1. API Key 是否正确配置：`cat ~/.hermes/.env`
2. 网络连接是否正常
3. 运行 `hermes doctor` 进行诊断

### 命令执行失败

确保：
1. 所需工具的依赖已安装（如 git、python 等）
2. 工作目录有足够的权限
3. 查看 `~/.hermes/logs/` 下的日志文件

### API 调用超时

- 检查网络连接
- 增加超时配置
- 尝试切换到更快的模型

## 安全

### Hermes 能访问我的所有文件吗？

默认情况下，Hermes 只能访问启动时所在的工作目录及其子目录。你可以通过配置限制或扩展访问范围。

### 如何保护敏感信息？

- 使用 `.hermes/.env` 存储 API Key，不要提交到 Git
- 启用命令审批模式
- 使用 Docker 后端进行文件隔离
- 定期审查 `hermes memory list` 清理敏感记忆
