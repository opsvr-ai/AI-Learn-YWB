---
sidebar_position: 10
title: "使用技巧与最佳实践"
description: "快速发挥 Hermes Agent 最大效能的使用技巧"
---

# 使用技巧与最佳实践

## 写好提示词

好的提示词 = 清晰的上下文 + 具体的任务 + 期望的输出格式。

**示例：**

```
你是一个资深 DevOps 工程师。
我们的服务部署在 AWS ECS 上，使用 Terraform 管理。
请帮我审查以下 Terraform 配置的安全性和最佳实践问题。
以列表形式输出，每条包含：严重程度、问题描述、修复建议。
```

## 利用记忆系统

### 手动记录

```bash
# 在对话中直接告知 Hermes 需要记住的信息
请记住：我们的项目代号是 "Phoenix"，后端用 Go，前端用 React
```

### 查看记忆

```bash
hermes memory list
```

## Skills 使用技巧

### 安装社区技能

```bash
hermes skills install github-pr-review
```

### 在对话中调用技能

```
用 PR Review 技能审查我最近一次提交的改动
```

## 定时自动化

### 每日站会摘要

```bash
hermes cron add "每天早上 9 点，查看我的 GitHub issues 和 PR，生成一份摘要发到 Telegram"
```

### 监控提醒

```bash
hermes cron add "每小时检查我们的生产服务状态页面，如有异常立即通知我"
```

## 多平台接入

Hermes 支持 20+ 平台。推荐从 Telegram 开始，配置最简单：

```bash
hermes gateway setup telegram
```

按提示输入 Bot Token 即可。

## 安全建议

- **命令审批**：启用命令审批模式，执行危险操作前需确认
- **隔离运行**：使用 Docker 后端隔离文件操作
- **密钥管理**：将 API Key 等敏感信息配置在 `~/.hermes/.env` 中，不要提交到 Git
- **定期审查**：定期用 `hermes memory list` 和 `hermes sessions list` 审查活动和记忆

## 常见模式

### 代码审查工作流

```
请审查这个 PR 的改动，重点关注：
1. 安全问题
2. 性能影响
3. 边界情况处理
4. 代码可读性
```

### 文档生成

```
根据这个代码文件，生成 API 文档，包括：
- 接口描述
- 请求/响应示例
- 参数说明
```

### 问题排查

```
我的服务出现了以下错误日志：[粘贴日志]
请帮我分析可能的原因和排查步骤。
```
