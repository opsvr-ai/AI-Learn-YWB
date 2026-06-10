#!/usr/bin/env python3
"""
Phase 2: Comprehensive content translation for Hermes docs skill HTML files.
Translates the full article body text from English to Chinese.
"""
import os, re

BASE = r'F:\培训\AI辅助日常工作材料\hermes-docs\user-guide\skills'

def find_all_html_files():
    files = []
    for root, dirs, fnames in os.walk(BASE):
        for fname in fnames:
            if fname.endswith('.html'):
                files.append(os.path.join(root, fname))
    files.sort()
    return files

def translate_article_content(article):
    """Apply comprehensive translations to article content."""

    # Very long list of phrase-level translations
    # Ordered: longer/more specific phrases first to avoid partial matches
    translations = [
        # ---- Auto-generated notice and info box ----
        ("This page is auto-generated from the skill's SKILL.md",
         "本页面由技能的 SKILL.md 自动生成"),

        # ---- Skill metadata table ----
        ("<td>Source</td>", "<td>来源</td>"),
        ("<td>Path</td>", "<td>路径</td>"),
        ("<td>Version</td>", "<td>版本</td>"),
        ("<td>Author</td>", "<td>作者</td>"),
        ("<td>License</td>", "<td>许可证</td>"),
        ("<td>Platforms</td>", "<td>平台</td>"),
        ("<td>Tags</td>", "<td>标签</td>"),
        ("<td>Related skills</td>", "<td>相关技能</td>"),
        ("Bundled (installed by default)", "内置（默认安装）"),
        ("Optional (install with /skill install)", "可选（通过 /skill install 安装）"),

        # ---- Section headers ----
        ("Skill metadata", "技能元数据"),
        ("Reference: full SKILL.md", "参考：完整 SKILL.md"),
        ("Prerequisites", "前提条件"),
        ("When to Use", "何时使用"),
        ("When NOT to Use", "何时不使用"),
        ("Quick Reference", "快速参考"),
        ("Limitations", "限制"),
        ("Rules", "规则"),
        ("Setup", "设置"),
        ("Configuration", "配置"),
        ("Installation", "安装"),
        ("Usage", "用法"),
        ("Examples", "示例"),
        ("Troubleshooting", "故障排除"),
        ("Notes", "备注"),
        ("Tips", "技巧"),
        ("Warning", "警告"),
        ("Overview", "概述"),
        ("Features", "功能"),
        ("Options", "选项"),
        ("Arguments", "参数"),
        ("Security", "安全"),
        ("Best Practices", "最佳实践"),
        ("Environment Variables", "环境变量"),
        ("Getting Started", "入门"),
        ("Advanced Usage", "高级用法"),
        ("Common Operations", "常用操作"),
        ("Workflow", "工作流"),
        ("Workflows", "工作流"),
        ("Key Concepts", "关键概念"),

        # ---- Common descriptive text ----
        ("The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.",
         "以下是 Hermes 在此技能被触发时加载的完整技能定义。这是技能激活时代理所看到的指令。"),

        ("macOS with Notes.app", "macOS 并安装 Notes.app"),
        ("macOS with Reminders.app", "macOS 并安装 Reminders.app"),
        ("macOS with Messages.app signed in", "macOS 并已登录 Messages.app"),
        ("macOS with Find My app and iCloud signed in", "macOS 并已登录"查找"应用和 iCloud"),
        ("Grant Automation access to Notes.app when prompted", "在提示时授予 Notes.app 的自动化访问权限"),
        ("Grant Reminders permission when prompted", "在提示时授予 Reminders 权限"),
        ("Grant Full Disk Access for terminal", "为终端授予完全磁盘访问权限"),
        ("Grant Automation permission for Messages.app when prompted", "在提示时授予 Messages.app 的自动化权限"),
        ("Screen Recording permission for terminal", "为终端授予屏幕录制权限"),
        ("System Settings", "系统设置"),

        # ---- When to Use descriptions ----
        ("User asks to create, view, or search Apple Notes", "用户要求创建、查看或搜索 Apple Notes"),
        ("Saving information to Notes.app for cross-device access", "将信息保存到 Notes.app 以实现跨设备访问"),
        ("Organizing notes into folders", "将笔记整理到文件夹中"),
        ("Exporting notes to Markdown/HTML", "将笔记导出为 Markdown/HTML"),
        ("User mentions \"reminder\" or \"Reminders app\"", "用户提到「提醒」或「提醒事项应用」"),
        ("Creating personal to-dos with due dates that sync to iOS", "创建带有截止日期的个人待办事项，同步到 iOS"),
        ("Managing Apple Reminders lists", "管理 Apple Reminders 列表"),
        ("User wants tasks to appear on their iPhone/iPad", "用户希望任务出现在他们的 iPhone/iPad 上"),
        ("User asks \"where is my", "用户问「我的"),
        ("Tracking AirTag locations", "追踪 AirTag 位置"),
        ("Checking device locations", "检查设备位置"),
        ("Monitoring pet or item movement over time", "监控宠物或物品随时间的移动"),
        ("User asks to send an iMessage or text message", "用户要求发送 iMessage 或短信"),
        ("Reading iMessage conversation history", "阅读 iMessage 对话历史"),
        ("Checking recent Messages.app chats", "查看最近的 Messages.app 聊天"),
        ("Sending to phone numbers or Apple IDs", "发送到电话号码或 Apple ID"),

        # ---- When NOT to Use ----
        ("Obsidian vault management", "Obsidian 库管理"),
        ("use the <code>obsidian</code> skill", "使用 <code>obsidian</code> 技能"),
        ("use the <code>memory</code> tool instead", "改用 <code>memory</code> 工具"),
        ("Quick agent-only notes", "仅代理使用的快速笔记"),
        ("Bear Notes", "Bear Notes"),
        ("separate app (not supported here)", "独立应用（此处不支持）"),
        ("Scheduling agent alerts", "安排代理警报"),
        ("use the cronjob tool instead", "改用定时任务工具"),
        ("Calendar events", "日历事件"),
        ("use Apple Calendar or Google Calendar", "使用 Apple 日历或 Google 日历"),
        ("Project task management", "项目任务管理"),
        ("use GitHub Issues, Notion, etc.", "使用 GitHub Issues、Notion 等"),
        ("Telegram/Discord/Slack/WhatsApp messages", "Telegram/Discord/Slack/WhatsApp 消息"),
        ("use the appropriate gateway channel", "使用相应的网关通道"),
        ("Group chat management", "群聊管理"),
        ("not supported", "不支持"),
        ("Bulk/mass messaging", "批量/群发消息"),
        ("always confirm with user first", "始终先与用户确认"),

        # ---- Common limitations ----
        ("Cannot edit notes containing images or attachments", "无法编辑包含图片或附件的笔记"),
        ("Interactive prompts require terminal access", "交互式提示需要终端访问"),
        ("macOS only", "仅限 macOS"),
        ("Linux only", "仅限 Linux"),
        ("Windows only", "仅限 Windows"),

        # ---- Common rules ----
        ("Prefer Apple Notes when user wants cross-device sync", "当用户需要跨设备同步时，优先使用 Apple Notes"),
        ("Use the <code>memory</code> tool for agent-internal notes that don't need to sync", "使用 <code>memory</code> 工具处理不需要同步的代理内部笔记"),
        ("Use the <code>obsidian</code> skill for Markdown-native knowledge management", "使用 <code>obsidian</code> 技能进行 Markdown 原生的知识管理"),
        ("Always confirm recipient and message content", "始终确认收件人和消息内容"),
        ("Never send to unknown numbers", "切勿发送到未知号码"),
        ("without explicit user approval", "未经用户明确批准"),
        ("Verify file paths exist before attaching", "附加前验证文件路径是否存在"),
        ("Don't spam", "不要发送垃圾信息"),
        ("rate-limit yourself", "自行限速"),

        # ---- Common instructional phrases ----
        ("Install:", "安装："),
        ("Check:", "检查："),
        ("Request:", "请求："),
        ("Or:", "或："),
        ("Note:", "注意："),
        ("Important:", "重要："),
        ("Optional but recommended", "可选但推荐"),
        ("For example:", "例如："),
        ("Default:", "默认："),
        ("Required:", "必需："),

        # ---- Date format related ----
        ("Accepted by", "接受的格式"),
        ("and date filters:", "和日期过滤器："),
        ("Date Formats", "日期格式"),

        # ---- Table header translations ----
        ("<th>---</th><th>---</th>", "<th>项目</th><th>值</th>"),

        # ---- Common action verbs ----
        ("View Notes", "查看笔记"),
        ("Create Notes", "创建笔记"),
        ("Edit Notes", "编辑笔记"),
        ("Delete Notes", "删除笔记"),
        ("Move Notes", "移动笔记"),
        ("Export Notes", "导出笔记"),
        ("View Reminders", "查看提醒事项"),
        ("Manage Lists", "管理列表"),
        ("Create Reminders", "创建提醒事项"),
        ("Complete / Delete", "完成/删除"),
        ("Output Formats", "输出格式"),
        ("List Chats", "列出聊天"),
        ("View History", "查看历史"),
        ("Send Messages", "发送消息"),
        ("Watch for New Messages", "监听新消息"),
        ("Service Options", "服务选项"),
        ("Example Workflow", "示例工作流"),

        # ---- UI / interaction terms ----
        ("Interactive editor", "交互式编辑器"),
        ("Quick add with title", "快速添加带标题"),
        ("Interactive selection to edit", "交互式选择要编辑"),
        ("Interactive selection to delete", "交互式选择要删除"),
        ("Move note to folder (interactive)", "将笔记移动到文件夹（交互式）"),
        ("Export to HTML/Markdown", "导出为 HTML/Markdown"),
        ("Today's reminders", "今天的提醒"),
        ("Today", "今天"),
        ("Tomorrow", "明天"),
        ("This week", "本周"),
        ("Past due", "逾期"),
        ("Everything", "全部"),
        ("Specific date", "特定日期"),
        ("List all lists", "列出所有列表"),
        ("Show specific list", "显示特定列表"),
        ("Create list", "创建列表"),
        ("Delete list", "删除列表"),
        ("Complete by ID", "按 ID 完成"),
        ("Delete by ID", "按 ID 删除"),
        ("JSON for scripting", "JSON 格式（用于脚本）"),
        ("TSV format", "TSV 格式"),
        ("Counts only", "仅显示计数"),
        ("Filter by folder", "按文件夹筛选"),
        ("Search notes (fuzzy)", "搜索笔记（模糊匹配）"),
        ("List all notes", "列出所有笔记"),
        ("Text only", "仅文本"),
        ("With attachment", "带附件"),
        ("Force iMessage or SMS", "强制使用 iMessage 或 SMS"),

        # ---- Privacy & System Settings ----
        ("Privacy", "隐私"),
        ("Automation", "自动化"),
        ("Full Disk Access", "完全磁盘访问权限"),
        ("Screen Recording", "屏幕录制"),

        # ---- Find My specific ----
        ("Find My app", ""查找"应用"),
        ("FindMy.app on macOS", "macOS 上的"查找"应用"),
        ("AirTag", "AirTag"),
        ("Apple devices and AirTags", "Apple 设备和 AirTag"),

        # ---- iMessage specific ----
        ("iMessage/SMS", "iMessage/SMS"),
        ("Messages.app", "Messages.app"),
        ("phone numbers or Apple IDs", "电话号码或 Apple ID"),

        # ---- macOS Computer Use specific ----
        ("computer_use", "computer_use"),
        ("capture first", "先截屏"),
        ("Click by element index", "按元素索引点击"),
        ("Verify", "验证"),
        ("Capture modes", "截屏模式"),
        ("Actions", "操作"),
        ("Background rules", "后台规则"),
        ("Text input patterns", "文本输入模式"),
        ("Drag & drop", "拖放"),
        ("Scroll", "滚动"),
        ("Managing what's focused", "管理焦点"),
        ("Delivering screenshots to the user", "向用户发送截图"),
        ("Safety", "安全"),
        ("these are hard rules", "这些是硬性规则"),
        ("Failure modes", "故障模式"),
        ("When NOT to use", "何时不使用"),

        # ---- More common HTML-level translations ----
        ("List emails in INBOX (default):", "列出收件箱中的邮件（默认）："),
        ("List emails in a specific folder:", "列出特定文件夹中的邮件："),
        ("List with pagination:", "分页列出："),
        ("Search Emails", "搜索邮件"),
        ("Read an Email", "阅读邮件"),
        ("Read email by ID (shows plain text):", "按 ID 阅读邮件（显示纯文本）："),
        ("Export raw MIME:", "导出原始 MIME："),
        ("Reply to an Email", "回复邮件"),
        ("To reply non-interactively from Hermes", "要从 Hermes 非交互式回复"),
        ("read the original message, compose a reply, and pipe it:", "阅读原始邮件、编写回复并通过管道发送："),
        ("Forward an Email", "转发邮件"),
        ("Write a New Email", "撰写新邮件"),
        ("Non-interactive (use this from Hermes)", "非交互式（从 Hermes 使用此方式）"),
        ("pipe the message via stdin:", "通过 stdin 管道发送消息："),
        ("Move/Copy Emails", "移动/复制邮件"),
        ("Move to folder:", "移动到文件夹："),
        ("Copy to folder:", "复制到文件夹："),
        ("Delete an Email", "删除邮件"),
        ("Manage Flags", "管理标记"),
        ("Add flag:", "添加标记："),
        ("Remove flag:", "移除标记："),
        ("Multiple Accounts", "多个账户"),
        ("List accounts:", "列出账户："),
        ("Use a specific account:", "使用特定账户："),
        ("Attachments", "附件"),
        ("Save attachments from a message:", "从邮件中保存附件："),
        ("Save to specific directory:", "保存到特定目录："),
        ("Output Formats", "输出格式"),
        ("Most commands support", "大多数命令支持"),
        ("for structured output:", "结构化输出："),
        ("Debugging", "调试"),
        ("Enable debug logging:", "启用调试日志："),
        ("Full trace with backtrace:", "带回溯的完整跟踪："),

        # ---- Himalaya specific ----
        ("Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.",
         "Himalaya 是一个 CLI 邮件客户端，允许你使用 IMAP、SMTP、Notmuch 或 Sendmail 后端从终端管理邮件。"),
        ("Run the interactive wizard to set up an account:", "运行交互式向导设置账户："),
        ("Or create", "或创建"),
        ("manually:", "手动："),
        ("Hermes Integration Notes", "Hermes 集成说明"),
        ("all work directly through the terminal tool", "均直接通过终端工具工作"),
        ("is recommended for reliability", "推荐使用以确保可靠性"),
        ("Interactive mode works with", "交互模式可与"),
        ("but requires knowing the editor and its commands", "但需要知道编辑器及其命令"),
        ("for structured output that's easier to parse programmatically", "用于更易于程序化解析的结构化输出"),
        ("The wizard requires interactive input", "向导需要交互式输入"),
        ("use PTY mode", "使用 PTY 模式"),
        ("List Folders", "列出文件夹"),
        ("List Emails", "列出邮件"),

        # ---- Claude Code specific ----
        ("Delegate coding tasks to", "将编码任务委托给"),
        ("autonomous coding agent CLI", "自主编码代理 CLI"),
        ("via the Hermes terminal", "通过 Hermes 终端"),
        ("can read files, write code, run shell commands, spawn subagents, and manage git workflows autonomously.",
         "可以自主读取文件、编写代码、运行 Shell 命令、生成子代理和管理 git 工作流。"),
        ("Two Orchestration Modes", "两种编排模式"),
        ("Hermes interacts with Claude Code in two fundamentally different ways. Choose based on the task.",
         "Hermes 以两种根本不同的方式与 Claude Code 交互。根据任务选择。"),
        ("Print Mode", "打印模式"),
        ("Non-Interactive", "非交互式"),
        ("PREFERRED for most tasks", "大多数任务的首选"),
        ("Print mode runs a one-shot task, returns the result, and exits.",
         "打印模式运行一次性任务，返回结果并退出。"),
        ("No PTY needed. No interactive prompts. This is the cleanest integration path.",
         "不需要 PTY。没有交互式提示。这是最简洁的集成路径。"),
        ("When to use print mode:", "何时使用打印模式："),
        ("One-shot coding tasks", "一次性编码任务"),
        ("CI/CD automation and scripting", "CI/CD 自动化和脚本"),
        ("Structured data extraction", "结构化数据提取"),
        ("Piped input processing", "管道输入处理"),
        ("Any task where you don't need multi-turn conversation", "不需要多轮对话的任何任务"),
        ("Print mode skips ALL interactive dialogs", "打印模式跳过所有交互式对话框"),
        ("no workspace trust prompt, no permission confirmations",
         "无工作区信任提示，无权限确认"),
        ("This makes it ideal for automation.", "这使其成为自动化的理想选择。"),
        ("Interactive PTY via tmux", "通过 tmux 的交互式 PTY"),
        ("Multi-Turn Sessions", "多轮会话"),
        ("Interactive mode gives you a full conversational REPL",
         "交互模式为你提供完整的对话式 REPL"),
        ("where you can send follow-up prompts, use slash commands, and watch Claude work in real time.",
         "你可以在其中发送后续提示、使用斜杠命令并实时观看 Claude 工作。"),
        ("Requires tmux orchestration.", "需要 tmux 编排。"),
        ("When to use interactive mode:", "何时使用交互模式："),
        ("Multi-turn iterative work", "多轮迭代工作"),
        ("Tasks requiring human-in-the-loop decisions", "需要人在环路决策的任务"),
        ("Exploratory coding sessions", "探索性编码会话"),
        ("When you need to use Claude's slash commands", "当你需要使用 Claude 的斜杠命令时"),

        # ---- More general phrases ----
        ("automatically falls back to", "自动回退到"),
        ("when the default is overloaded", "当默认模型过载时"),
        ("print mode only", "仅打印模式"),
        ("interactive mode", "交互模式"),
        ("requires", "需要"),
        ("recommended", "推荐"),
        ("deprecated", "已弃用"),
        ("experimental", "实验性"),
        ("optional", "可选"),
    ]

    result = article
    for en, zh in translations:
        result = result.replace(en, zh)

    return result

def process_file(filepath):
    """Read, translate, and write back a single HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Translate article content
    article_tag = '<article class="docs-content">'
    article_start = content.find(article_tag)
    article_end = content.rfind('</article>')

    if article_start >= 0 and article_end >= 0:
        article_start += len(article_tag)
        article = content[article_start:article_end]

        article = translate_article_content(article)

        content = content[:article_start] + article + content[article_end:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

if __name__ == '__main__':
    files = find_all_html_files()
    skip_files = {'godmode.html', 'google-workspace.html', 'apple-apple-notes.html', 'apple-apple-reminders.html'}

    count = 0
    for f in files:
        fname = os.path.basename(f)
        if fname in skip_files:
            continue
        if process_file(f):
            count += 1

    print(f"Phase 2: Processed {count} files with content translations")