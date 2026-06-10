#!/usr/bin/env python3
"""Translate Hermes documentation HTML files from English to Chinese."""

import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')

# Build a comprehensive phrase translation dictionary
# Ordered by length (longer phrases first to avoid partial matches)
phrase_dict = [
    # Long phrases first
    ("Cron jobs run in fresh agent sessions with no memory of your current chat", "Cron 任务在全新的 Agent 会话中运行，不记忆你当前的聊天"),
    ("Prompts must be completely self-contained", "提示词必须完全自包含"),
    ("include everything the agent needs to know", "包含 Agent 需要知道的所有信息"),
    ("no memory of your current chat", "不记忆你当前的聊天"),
    ("no memory of previous runs or your preferences", "不记忆之前的运行或你的偏好"),
    ("The agent in a cron job has no memory of your conversations", "Cron 任务中的 Agent 不记忆你的对话"),
    ("delivery is suppressed", "消息投递会被抑制"),
    ("When the agent's final response contains", "当 Agent 的最终响应包含"),
    ("respond with [SILENT]", "用 [SILENT] 回复"),
    ("notification noise", "通知骚扰"),
    ("no spam on quiet hours", "安静时段无骚扰"),
    ("only get notified when something actually happens", "只会在确实有事情发生时收到通知"),
    ("you only get notified when", "你只会在有通知时收到"),
    ("no long-lived API keys to rotate or revoke", "无需轮换或撤销长期 API 密钥"),
    ("RBAC-driven access", "RBAC 驱动的访问"),
    ("grant or remove", "授予或移除"),
    ("no config rewrite needed", "无需修改配置"),
    ("Access and audit logs are segmented by assignee", "访问和审计日志按被分配者区分"),
    ("instead of all callers sharing one static key", "而不是所有调用者共享一个静态密钥"),
    ("Workload identity and service-principal flows for CI/CD pipelines", "CI/CD 管道的工作负载身份和服务主体流程"),
    ("via managed identity", "通过托管身份"),
    ("Single auth surface for", "统一认证入口"),
    ("This means you only get notified when the agent has something to report", "这意味着你只会在 Agent 有内容要报告时收到通知"),

    # Common phrases
    ("For the full feature reference", "完整的功能参考请参见"),
    ("For the complete cron reference", "完整的 cron 参考"),
    ("all parameters, edge cases, and internals", "所有参数、边界情况和内部机制"),
    ("for more on how this works", "了解更多工作原理"),
    ("for more details", "了解更多详情"),
    ("for details", "了解详情"),
    ("Full guide:", "完整指南："),

    # Standard phrases
    ("Hermes Agent supports", "Hermes Agent 支持"),
    ("Hermes supports", "Hermes 支持"),
    ("The setup wizard", "设置向导"),
    ("auto-detects", "自动检测"),
    ("Your CI/CD pipeline", "你的 CI/CD 管道"),
    ("This gives you", "这让你可以"),
    ("This guide walks through", "本指南将引导你"),
    ("By the end you'll have", "最终你将拥有"),
    ("By the end", "最终"),
    ("no code required", "无需编写代码"),
    ("hands-free", "全自动"),
    ("before starting", "在开始之前"),
    ("make sure you have", "确保你已具备"),
    ("Before automating anything", "在自动化任何内容之前"),
    ("Before starting", "在开始之前"),
    ("make sure", "确保"),
    ("let's make sure", "确保"),
    ("works with all", "兼容所有"),
    ("works with any model", "兼容任何模型"),
    ("not locked to a single provider", "不锁定单个提供商"),
    ("no API keys", "无需 API 密钥"),
    ("no config", "无需配置"),
    ("zero config", "零配置"),
    ("zero tokens", "零 token"),
    ("at minimum", "至少需要"),
    ("at least", "至少"),
    ("highest priority first", "优先级从高到低"),
    ("in this order", "按此顺序"),
    ("in order", "按顺序"),
    ("under the hood", "底层实现"),
    ("out of the box", "开箱即用"),
    ("on by default", "默认启用"),
    ("by default", "默认"),
    ("first time", "首次"),
    ("one-time setup", "一次性设置"),
    ("one-shot", "一次性"),
    ("per request", "每个请求"),
    ("per session", "每个会话"),
    ("each time", "每次"),
    ("every time", "每次"),
    ("at runtime", "在运行时"),
    ("at startup", "在启动时"),
    ("on first use", "首次使用时"),
    ("in production", "在生产环境"),
    ("in development", "在开发环境"),
    ("for local development", "用于本地开发"),
    ("after running", "运行后"),
    ("before running", "运行前"),
    ("This is the", "这是"),
    ("This is a", "这是一个"),
    ("This allows", "这允许"),
    ("This enables", "这使"),
    ("This means", "这意味着"),
    ("This ensures", "这确保"),
    ("This prevents", "这防止"),
    ("This requires", "这需要"),
    ("Note that", "注意"),
    ("Important:", "重要："),
    ("Warning:", "警告："),
    ("Tip:", "提示："),

    # Common nouns and terms in context
    ("the cron scheduler", "cron 调度器"),
    ("the gateway", "网关"),
    ("the scheduler", "调度器"),
    ("the wizard", "向导"),
    ("the endpoint", "端点"),
    ("the model", "模型"),
    ("the provider", "提供商"),
    ("the plugin", "插件"),
    ("the agent", "Agent"),
    ("the script", "脚本"),
    ("the tool", "工具"),
    ("the skill", "Skill"),
    ("the session", "会话"),
    ("the prompt", "提示词"),
    ("the config", "配置"),
    ("the deployment", "部署"),
    ("the resource", "资源"),
    ("the service", "服务"),
    ("the pipeline", "管道"),
    ("the job", "任务"),
    ("the cron job", "cron 任务"),

    # Common verbs in context
    ("is configured", "已配置"),
    ("is installed", "已安装"),
    ("is running", "正在运行"),
    ("is enabled", "已启用"),
    ("is disabled", "已禁用"),
    ("is available", "可用"),
    ("is required", "必需"),
    ("is recommended", "推荐"),
    ("is supported", "支持"),
    ("is detected", "已检测到"),
    ("is stored in", "存储在"),
    ("is saved to", "保存到"),
    ("is written to", "写入到"),
    ("is set in", "设置在"),
    ("can be found in", "可在"),
    ("can be used", "可以使用"),
    ("can be configured", "可以配置"),
    ("can be installed", "可以安装"),
    ("can be enabled", "可以启用"),
    ("can be disabled", "可以禁用"),
    ("can be overridden", "可以覆盖"),
    ("can be customized", "可以自定义"),
    ("can be set", "可以设置"),
    ("can be specified", "可以指定"),
    ("should be", "应为"),
    ("should use", "应使用"),
    ("should not", "不应"),
    ("must be", "必须为"),
    ("must have", "必须拥有"),
    ("must use", "必须使用"),
    ("will be", "将是"),
    ("will run", "将运行"),
    ("will use", "将使用"),
    ("will work", "将正常工作"),
    ("will contain", "将包含"),
    ("need to", "需要"),
    ("don't need", "不需要"),

    # Common short phrases
    ("for example", "例如"),
    ("for instance", "例如"),
    ("in addition", "此外"),
    ("in particular", "特别是"),
    ("in general", "通常"),
    ("on the other hand", "另一方面"),
    ("as well as", "以及"),
    ("along with", "连同"),
    ("instead of", "而非"),
    ("due to", "由于"),
    ("according to", "根据"),
    ("regardless of", "无论"),
    ("prior to", "在...之前"),
    ("subsequent to", "在...之后"),
    ("as a result", "因此"),
    ("in order to", "为了"),
    ("so that", "以便"),
    ("even if", "即使"),
    ("even when", "即使"),
    ("whether or not", "是否"),
    ("if and only if", "当且仅当"),
    ("as long as", "只要"),
    ("as soon as", "一旦"),
    ("up to", "最多"),
    ("at most", "最多"),
    ("at least", "至少"),
    ("more than", "超过"),
    ("less than", "少于"),
    ("no more than", "不超过"),
    ("no less than", "不少于"),
    ("similar to", "类似于"),
    ("different from", "不同于"),
    ("the same as", "与...相同"),
    ("compatible with", "兼容"),
    ("incompatible with", "不兼容"),
    ("dependent on", "依赖于"),
    ("independent of", "独立于"),
    ("equivalent to", "等同于"),
    ("identical to", "与...相同"),

    # Specific tech translations
    ("environment variable", "环境变量"),
    ("command line", "命令行"),
    ("command-line", "命令行"),
    ("webhook", "Webhook"),
    ("webhook platform", "Webhook 平台"),
    ("cron job", "cron 任务"),
    ("cron jobs", "cron 任务"),
    ("Cron jobs", "Cron 任务"),
    ("agent session", "Agent 会话"),
    ("agent sessions", "Agent 会话"),
    ("model provider", "模型提供商"),
    ("platform adapter", "平台适配器"),
    ("context window", "上下文窗口"),
    ("context length", "上下文长度"),
    ("base URL", "基础 URL"),
    ("API key", "API 密钥"),
    ("API keys", "API 密钥"),
    ("service principal", "服务主体"),
    ("managed identity", "托管身份"),
    ("workload identity", "工作负载身份"),
    ("inference profile", "推理配置文件"),
    ("cross-region inference", "跨区域推理"),
    ("rate limit", "速率限制"),
    ("token limit", "token 限制"),
    ("context compression", "上下文压缩"),
    ("prompt caching", "提示词缓存"),
    ("cache hit", "缓存命中"),
    ("cache miss", "缓存未命中"),
    ("tool call", "工具调用"),
    ("tool calls", "工具调用"),
    ("tool set", "工具集"),
    ("toolset", "工具集"),
    ("slash command", "斜杠命令"),
    ("slash commands", "斜杠命令"),
    ("lifecycle hook", "生命周期钩子"),
    ("lifecycle hooks", "生命周期钩子"),
    ("event hook", "事件钩子"),
    ("event hooks", "事件钩子"),
    ("plugin directory", "插件目录"),
    ("plugin system", "插件系统"),
    ("skill file", "Skill 文件"),
    ("skill files", "Skill 文件"),
    ("memory backend", "记忆后端"),
    ("memory provider", "记忆提供商"),
    ("delivery target", "投递目标"),
    ("delivery targets", "投递目标"),
    ("scheduled task", "定时任务"),
    ("scheduled tasks", "定时任务"),
    ("web search", "网络搜索"),
    ("voice mode", "语音模式"),
    ("browser tool", "浏览器工具"),
    ("sub-agent", "子 Agent"),
    ("sub-agents", "子 Agent"),

    # More sentence-level translations
    ("The following", "以下"),
    ("The following table", "下表"),
    ("The table below", "下表"),
    ("See the table below", "见下表"),
    ("as shown below", "如下所示"),
    ("as shown in the table", "如表所示"),
    ("as described in", "如"),
    ("as explained in", "如"),
    ("as mentioned in", "如"),
    ("as noted in", "如"),
    ("as detailed in", "详情见"),
    ("refer to", "请参考"),
    ("please refer to", "请参考"),
    ("refer to the", "请参考"),
    ("you can also", "你也可以"),
    ("you may also", "你也可以"),
    ("you can use", "你可以使用"),
    ("you can run", "你可以运行"),
    ("you can set", "你可以设置"),
    ("you can specify", "你可以指定"),
    ("you can configure", "你可以配置"),
    ("you can enable", "你可以启用"),
    ("you can disable", "你可以禁用"),
    ("you can override", "你可以覆盖"),
    ("you can customize", "你可以自定义"),
    ("you can add", "你可以添加"),
    ("you can remove", "你可以移除"),
    ("you can edit", "你可以编辑"),
    ("you can change", "你可以更改"),
    ("you can choose", "你可以选择"),
    ("you can select", "你可以选择"),
    ("you can install", "你可以安装"),
    ("you can update", "你可以更新"),
    ("you can test", "你可以测试"),
    ("you can verify", "你可以验证"),
    ("you can check", "你可以检查"),
    ("you should", "你应该"),
    ("you must", "你必须"),
    ("you need", "你需要"),
    ("you want", "你想要"),
    ("you have", "你拥有"),
    ("you'll need", "你需要"),
    ("you'll see", "你会看到"),
    ("you'll have", "你将拥有"),
    ("you'll get", "你将获得"),
    ("you're using", "你正在使用"),
    ("you're running", "你正在运行"),
    ("you're ready", "你准备好了"),
    ("you're done", "完成"),
    ("you have configured", "你已配置"),
    ("you have installed", "你已安装"),
    ("you have set up", "你已设置"),
    ("you have enabled", "你已启用"),
    ("you have added", "你已添加"),
    ("you have created", "你已创建"),
    ("you have deployed", "你已部署"),

    # Common instruction phrases
    ("To install", "要安装"),
    ("To configure", "要配置"),
    ("To set up", "要设置"),
    ("To enable", "要启用"),
    ("To disable", "要禁用"),
    ("To use", "要使用"),
    ("To run", "要运行"),
    ("To test", "要测试"),
    ("To verify", "要验证"),
    ("To check", "要检查"),
    ("To update", "要更新"),
    ("To remove", "要移除"),
    ("To delete", "要删除"),
    ("To add", "要添加"),
    ("To create", "要创建"),
    ("To deploy", "要部署"),
    ("To start", "要启动"),
    ("To stop", "要停止"),
    ("To restart", "要重启"),

    # Remaining common terms
    ("optional but recommended", "可选但推荐"),
    ("not required", "非必需"),
    ("not supported", "不支持"),
    ("not available", "不可用"),
    ("not recommended", "不推荐"),
    ("not enabled", "未启用"),
    ("not configured", "未配置"),
    ("not installed", "未安装"),
    ("not possible", "不可行"),
    ("not allowed", "不允许"),
    ("not permitted", "不允许"),
    ("not recommended", "不推荐"),
    ("automatically", "自动"),
    ("manually", "手动"),
    ("explicitly", "显式地"),
    ("implicitly", "隐式地"),
    ("transparently", "透明地"),
    ("natively", "原生"),
    ("directly", "直接"),
    ("indirectly", "间接"),
    ("globally", "全局"),
    ("locally", "本地"),
    ("remotely", "远程"),
    ("permanently", "永久"),
    ("temporarily", "临时"),
    ("immediately", "立即"),
    ("subsequently", "随后"),
    ("previously", "之前"),
    ("currently", "当前"),
    ("recently", "最近"),
    ("already", "已经"),
    ("still", "仍然"),
    ("yet", "还"),
    ("only", "仅"),
    ("also", "也"),
    ("too", "也"),
    ("either", "任一"),
    ("both", "两者都"),
    ("neither", "两者都不"),
    ("all", "所有"),
    ("none", "无"),
    ("each", "每个"),
    ("every", "每个"),
    ("any", "任何"),
    ("some", "一些"),
    ("most", "大多数"),
    ("many", "许多"),
    ("few", "少数"),
    ("several", "几个"),
    ("multiple", "多个"),
    ("single", "单个"),
    ("various", "各种"),
    ("certain", "某些"),
    ("specific", "特定"),
    ("general", "通用"),
    ("common", "常见"),
    ("typical", "典型"),
    ("standard", "标准"),
    ("default", "默认"),
    ("custom", "自定义"),
    ("alternative", "替代"),
    ("primary", "主要"),
    ("secondary", "次要"),
    ("additional", "额外"),
    ("extra", "额外"),
    ("other", "其他"),
    ("another", "另一个"),
    ("such as", "例如"),
    ("like", "如"),
    ("including", "包括"),
    ("excluding", "不包括"),
    ("with", "带有"),
    ("without", "无"),
    ("within", "在...内"),
    ("outside", "在...外"),
    ("between", "之间"),
    ("among", "之中"),
    ("through", "通过"),
    ("via", "通过"),
    ("using", "使用"),
    ("upon", "在...之上"),
    ("about", "关于"),
    ("over", "超过"),
    ("under", "在...下"),
    ("above", "在...上方"),
    ("below", "在...下方"),
    ("behind", "在...之后"),
    ("before", "在...之前"),
    ("after", "在...之后"),
    ("during", "在...期间"),
    ("until", "直到"),
    ("since", "自从"),
    ("from", "从"),
    ("into", "到"),
    ("onto", "到...上"),
    ("onto", "到...上"),
    ("across", "跨"),
    ("along", "沿"),
    ("against", "对"),
    ("towards", "朝"),
    ("throughout", "贯穿"),
]

# Sort by length descending
phrase_dict.sort(key=lambda x: -len(x[0]))


def translate_text(text):
    """Translate English text to Chinese using phrase dictionary."""
    for eng, cn in phrase_dict:
        text = text.replace(eng, cn)
    return text


def translate_paragraphs(article):
    """Translate paragraph text while preserving HTML tags and code blocks."""
    # Split article into segments: code blocks and non-code-block text
    segments = re.split(r'(<div class="code-block">.*?</div>)', article, flags=re.DOTALL)

    result = []
    for seg in segments:
        if seg.startswith('<div class="code-block">'):
            result.append(seg)
        else:
            # Translate <p> content
            def translate_p(m):
                content = m.group(1)
                translated = translate_text(content)
                return '<p>' + translated + '</p>'
            seg = re.sub(r'<p>(.*?)</p>', translate_p, seg, flags=re.DOTALL)

            # Translate <li> content
            def translate_li(m):
                content = m.group(1)
                translated = translate_text(content)
                return '<li>' + translated + '</li>'
            seg = re.sub(r'<li>(.*?)</li>', translate_li, seg, flags=re.DOTALL)

            # Translate <td> content
            def translate_td(m):
                content = m.group(1)
                translated = translate_text(content)
                return '<td>' + translated + '</td>'
            seg = re.sub(r'<td>(.*?)</td>', translate_td, seg, flags=re.DOTALL)

            # Translate <th> content
            def translate_th(m):
                content = m.group(1)
                translated = translate_text(content)
                return '<th>' + translated + '</th>'
            seg = re.sub(r'<th>(.*?)</th>', translate_th, seg, flags=re.DOTALL)

            # Translate <strong> content (but not if it contains <code>)
            def translate_strong(m):
                content = m.group(1)
                if '<code>' in content:
                    return m.group(0)
                translated = translate_text(content)
                return '<strong>' + translated + '</strong>'
            seg = re.sub(r'<strong>(.*?)</strong>', translate_strong, seg, flags=re.DOTALL)

            # Translate :::info/tip/warning block headers
            seg = seg.replace(':::info Key Concept', ':::info 关键概念')
            seg = seg.replace(':::info Critical concept', ':::info 关键概念')
            seg = seg.replace(':::warning Critical concept', ':::warning 关键概念')
            seg = seg.replace(':::warning Self-Contained Prompts', ':::warning 自包含提示词')
            seg = seg.replace(':::tip The [SILENT] Trick', ':::tip [SILENT] 技巧')
            seg = seg.replace(':::tip Don\'t need the LLM?', ':::tip 不需要 LLM？')
            seg = seg.replace(':::tip Iterate on the format', ':::tip 迭代格式')
            seg = seg.replace(':::tip No messaging? No problem', ':::tip 没有消息平台？没问题')
            seg = seg.replace(':::tip EC2 / ECS / Lambda', ':::tip EC2 / ECS / Lambda')
            seg = seg.replace(':::tip Tailor the persona', ':::tip 量身定制角色')
            seg = seg.replace(':::tip What else can you schedule?', ':::tip 还能调度什么？')
            seg = seg.replace(':::tip Three Trigger Types', ':::tip 三种触发类型')
            seg = seg.replace(':::tip ', ':::tip ')
            seg = seg.replace(':::info ', ':::info ')
            seg = seg.replace(':::warning ', ':::warning ')

            result.append(seg)

    return ''.join(result)


# Title translations
title_translations = {
    'Script-Only Cron Jobs (No LLM)': '纯脚本 Cron 任务（无 LLM）',
    'Script-Only Cron Jobs': '纯脚本 Cron 任务',
    'Cron Troubleshooting': 'Cron 故障排除',
    'Tutorial: Daily Briefing Bot': '教程：每日简报机器人',
    'Build a Daily Briefing Bot': '构建每日简报机器人',
    'Build a Hermes Plugin': '构建 Hermes 插件',
    'Delegation Patterns': '委托模式',
    'GitHub PR Review Agent': 'GitHub PR 审查 Agent',
    'Google Gemini': 'Google Gemini',
    'Local LLM on Mac': 'Mac 上的本地 LLM',
    'Local Ollama Setup': '本地 Ollama 设置',
    'Microsoft Graph App Registration': 'Microsoft Graph 应用注册',
    'Migrate from OpenClaw': '从 OpenClaw 迁移',
    'Minimax OAuth': 'Minimax OAuth',
    'OAuth over SSH': '通过 SSH 的 OAuth',
    'Operate Teams Meeting Pipeline': '操作 Teams 会议管道',
    'Pipe Script Output': '管道脚本输出',
    'Python Library': 'Python 库',
    'Team Telegram Assistant': '团队 Telegram 助手',
    'Tips and Best Practices': '技巧与最佳实践',
    'Tips & Best Practices': '技巧与最佳实践',
    'Use MCP with Hermes': '在 Hermes 中使用 MCP',
    'Use Soul with Hermes': '在 Hermes 中使用 Soul',
    'Use Voice Mode with Hermes': '在 Hermes 中使用语音模式',
    'Webhook GitHub PR Review': 'Webhook GitHub PR 审查',
    'Work with Skills': '使用 Skills',
    'xAI Grok OAuth': 'xAI Grok OAuth',
    'Integrations': '集成',
    'Providers': '提供商',
    'ACP Internals': 'ACP 内部机制',
    'Adding Platform Adapters': '添加平台适配器',
    'Adding Providers': '添加提供商',
    'Adding Tools': '添加工具',
    'Agent Loop': 'Agent 循环',
    'Browser Supervisor': '浏览器监督器',
    'Context Compression and Caching': '上下文压缩与缓存',
    'Context Engine Plugin': '上下文引擎插件',
    'Contributing': '贡献指南',
    'Creating Skills': '创建 Skills',
    'Cron Internals': 'Cron 内部机制',
    'Extending the CLI': '扩展 CLI',
    'Gateway Internals': '网关内部机制',
    'Image Gen Provider Plugin': '图像生成提供商插件',
    'Memory Provider Plugin': '记忆提供商插件',
    'Model Provider Plugin': '模型提供商插件',
    'Plugin LLM Access': '插件 LLM 访问',
    'Programmatic Integration': '编程集成',
    'Prompt Assembly': '提示词组装',
    'Provider Runtime': '提供商运行时',
    'Session Storage': '会话存储',
    'Tools Runtime': '工具运行时',
    'Trajectory Format': '轨迹格式',
    'Video Gen Provider Plugin': '视频生成提供商插件',
    'Web Search Provider Plugin': '网络搜索提供商插件',
    'Automate Anything with Cron': '使用 Cron 自动化一切',
    'Automation Templates': '自动化模板',
    'AWS Bedrock': 'AWS Bedrock',
    'Microsoft Foundry': 'Microsoft Foundry',
}

# Header translations for h2/h3/h4
header_translations = {
    'Prerequisites': '前置条件',
    'Quick Start': '快速开始',
    'Configuration': '配置',
    'Installation': '安装',
    'Overview': '概述',
    'Getting Started': '入门指南',
    'Architecture': '架构',
    'Introduction': '简介',
    'Troubleshooting': '故障排除',
    'Environment Variables': '环境变量',
    'Environment variables': '环境变量',
    'Related': '相关内容',
    'See Also': '另见',
    'Next Steps': '下一步',
    'Examples': '示例',
    'Key Concepts': '关键概念',
    'Key Concept': '关键概念',
    'Available Models': '可用模型',
    'Diagnostics': '诊断',
    'Limitations': '限制',
    'Security': '安全',
    'Deployment': '部署',
    'Setup': '设置',
    'Usage': '用法',
    'Advanced': '高级',
    'Reference': '参考',
    'Quick Reference': '快速参考',
    'Tips': '技巧',
    'Best Practices': '最佳实践',
    'Performance': '性能',
    'Performance Issues': '性能问题',
    'Testing': '测试',
    'How It Works': '工作原理',
    'How it works': '工作原理',
    'Health checks': '健康检查',
    'Health Checks': '健康检查',
    'Model Discovery': '模型发现',
    'Guardrails': 'Guardrails',
    'Region': '区域',
    'One-Click AWS Deployment': '一键 AWS 部署',
    'Gateway (Messaging Platforms)': '网关（消息平台）',
    'Switching Models Mid-Session': '会话中切换模型',
    'Alternative': '替代方案',
    'Model discovery': '模型发现',
    'Diagnostics': '诊断',
    'Credential resolution order': '凭证解析顺序',
    'Deployment patterns': '部署模式',
    'One-time setup (Azure side)': '一次性设置（Azure 侧）',
    'One-time setup (Hermes side)': '一次性设置（Hermes 侧）',
    'Why use Entra ID?': '为什么使用 Entra ID？',
    'Sovereign clouds (Government, China)': '主权云（Government、China）',
    'Delivery Targets': '投递目标',
    'Managing Your Jobs': '管理你的任务',
    'Schedule expressions': '调度表达式',
    'The [SILENT] Pattern': '[SILENT] 模式',
    'Webhook Template Variables': 'Webhook 模板变量',
    'Cron Schedule Syntax': 'Cron 调度语法',
}


def translate_article(article):
    """Translate article content: breadcrumbs, h1, h2/h3/h4, and paragraphs."""
    # Translate breadcrumb parts
    article = article.replace('>docs</a>', '>文档</a>')
    article = article.replace('>guides</a>', '>指南</a>')
    article = article.replace('>developer-guide</a>', '>开发者指南</a>')
    article = article.replace('>integrations</a>', '>集成</a>')

    # Translate h1 using title_translations
    def translate_h1(m):
        title = m.group(1)
        for eng, cn in sorted(title_translations.items(), key=lambda x: -len(x[0])):
            if eng in title:
                title = title.replace(eng, cn)
                break
        return '<h1>' + title + '</h1>'
    article = re.sub(r'<h1>(.*?)</h1>', translate_h1, article)

    # Translate h2/h3/h4 headers
    def translate_header(m):
        tag = m.group(1)
        text = m.group(2)
        # Strip HTML tags for matching
        clean = re.sub(r'<[^>]+>', '', text).strip()
        for eng, cn in sorted(header_translations.items(), key=lambda x: -len(x[0])):
            if clean == eng:
                text = text.replace(eng, cn)
                break
        return '<' + tag + '>' + text + '</' + tag + '>'
    article = re.sub(r'<(h[234])>(.*?)</\1>', translate_header, article)

    # Translate paragraph text
    article = translate_paragraphs(article)

    return article


# Process files
base = 'F:/培训/AI辅助日常工作材料'
count = 0
for dirpath in ['hermes-docs/guides', 'hermes-docs/integrations', 'hermes-docs/developer-guide']:
    full_dir = os.path.join(base, dirpath)
    if os.path.isdir(full_dir):
        for f in sorted(os.listdir(full_dir)):
            if f.endswith('.html'):
                fp = os.path.join(full_dir, f)
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()

                # Translate title tag
                def translate_title(m):
                    title_text = m.group(1)
                    for eng, cn in sorted(title_translations.items(), key=lambda x: -len(x[0])):
                        if eng in title_text:
                            title_text = title_text.replace(eng, cn)
                            break
                    return '<title>' + title_text + '</title>'
                content = re.sub(r'<title>(.*?)</title>', translate_title, content)

                # Translate article content
                def process_article(m):
                    return '<article class="docs-content">' + translate_article(m.group(1)) + '</article>'
                content = re.sub(r'<article class="docs-content">(.*?)</article>', process_article, content, flags=re.DOTALL)

                with open(fp, 'w', encoding='utf-8') as fh:
                    fh.write(content)

                count += 1
                print(f'Processed: {f}')

print(f'\nTotal files processed: {count}')