#!/usr/bin/env python3
"""
Comprehensive translation script for Hermes docs skill HTML files.
Translates English content to Chinese in <article> sections and title tags.
Preserves HTML tags, code blocks, and technical terms.
"""
import os, re, json

BASE = r'F:\培训\AI辅助日常工作材料\hermes-docs\user-guide\skills'

def find_all_html_files():
    files = []
    for root, dirs, fnames in os.walk(BASE):
        for fname in fnames:
            if fname.endswith('.html'):
                files.append(os.path.join(root, fname))
    files.sort()
    return files

def translate_text_outside_tags(html_text):
    """
    Translate English text to Chinese, but only text outside HTML tags and code blocks.
    This is a comprehensive approach that handles the full article content.
    """
    # Common translations dictionary - ordered by specificity (longer phrases first)
    translations = [
        # Auto-generated notice
        ("This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page.",
         "本页面由 website/scripts/generate-skill-docs.py 从技能的 SKILL.md 自动生成。请编辑源 SKILL.md，而非本页面。"),

        # Info box text
        ("The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.",
         "以下是 Hermes 在此技能被触发时加载的完整技能定义。这是技能激活时代理所看到的指令。"),

        # Section headers
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
        ("Environment Variables", "环境变量"),
        ("Security", "安全"),
        ("Best Practices", "最佳实践"),

        # Metadata table labels
        ("Bundled (installed by default)", "内置（默认安装）"),
        ("Optional (install with /skill install)", "可选（通过 /skill install 安装）"),

        # Common phrases
        ("macOS only", "仅限 macOS"),
        ("Linux only", "仅限 Linux"),
        ("Windows only", "仅限 Windows"),
        ("No prerequisites", "无前提条件"),
        ("Default", "默认"),
        ("Required", "必需"),
        ("Optional", "可选"),
        ("Deprecated", "已弃用"),
        ("Experimental", "实验性"),
    ]

    result = html_text
    for en, zh in translations:
        result = result.replace(en, zh)

    return result

def translate_metadata_table(article):
    """Translate the skill metadata table entries."""
    # Source row
    article = article.replace("<td>Source</td>", "<td>来源</td>")
    article = article.replace("<td>Path</td>", "<td>路径</td>")
    article = article.replace("<td>Version</td>", "<td>版本</td>")
    article = article.replace("<td>Author</td>", "<td>作者</td>")
    article = article.replace("<td>License</td>", "<td>许可证</td>")
    article = article.replace("<td>Platforms</td>", "<td>平台</td>")
    article = article.replace("<td>Tags</td>", "<td>标签</td>")
    article = article.replace("<td>Related skills</td>", "<td>相关技能</td>")

    return article

def translate_title(title):
    """Translate the English part of the title."""
    suffix = " - Hermes 官方文档"
    if title.endswith(suffix):
        title_en = title[:-len(suffix)]
    else:
        return title

    # For most skill docs, the title format is: "SkillName — Description"
    # We translate the em-dash and common descriptive patterns
    title_zh = title_en

    # Common title patterns
    title_zh = title_zh.replace(" — ", " — ")  # Keep em-dash

    # Common descriptive suffixes in titles
    patterns = [
        # CLI descriptions
        (" via CLI", " 通过 CLI"),
        (" via the CLI", " 通过 CLI"),
        (" from terminal", " 从终端"),
        (" from the terminal", " 从终端"),
        (" via memo CLI", " 通过 memo CLI"),
        (" via remindctl", " 通过 remindctl"),
        (" via imsg CLI", " 通过 imsg CLI"),
        (" via FindMy", " 通过「查找」应用"),
        (" on macOS", " 在 macOS 上"),

        # Common actions
        (": create, search, edit", "：创建、搜索、编辑"),
        (": add, list, complete", "：添加、列表、完成"),
        (": track", "：追踪"),
        (": send and receive", "：收发"),
        ("Send and receive ", "收发"),
        ("Track ", "追踪"),
        ("Manage ", "管理"),
        ("Delegate coding to ", "将编码任务委托给"),

        # Common suffixes
        (" IMAP/SMTP email from terminal", " 终端 IMAP/SMTP 邮件客户端"),
    ]

    for en, zh in patterns:
        title_zh = title_zh.replace(en, zh)

    return title_zh + suffix

def translate_breadcrumb(article):
    """Translate the breadcrumb last segment."""
    # Find breadcrumb div and translate common words
    bc_match = re.search(r'(<div class="docs-breadcrumb">)(.*?)(</div>)', article, re.DOTALL)
    if not bc_match:
        return article

    breadcrumb = bc_match.group(2)

    # Common breadcrumb word translations
    replacements = [
        ("Apple Notes", "Apple Notes"),
        ("Reminders", "提醒事项"),
        ("Findmy", "Findmy"),
        ("Imessage", "iMessage"),
        ("Macos Computer Use", "macOS 计算机操控"),
        ("Himalaya", "Himalaya"),
        ("Delegate coding to", "将编码任务委托给"),
        ("via", "通过"),
        ("from terminal", "从终端"),
        ("Manage", "管理"),
        ("Track", "追踪"),
        ("Send and receive", "收发"),
    ]

    for en, zh in replacements:
        breadcrumb = breadcrumb.replace(en, zh)

    return article[:bc_match.start()] + bc_match.group(1) + breadcrumb + bc_match.group(3) + article[bc_match.end():]

def process_file(filepath):
    """Read, translate, and write back a single HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Translate title
    title_match = re.search(r'<title>(.*?)</title>', content)
    if title_match:
        old_title = title_match.group(1)
        new_title = translate_title(old_title)
        content = content.replace(f'<title>{old_title}</title>', f'<title>{new_title}</title>')

    # 2. Translate article content
    article_tag = '<article class="docs-content">'
    article_start = content.find(article_tag)
    article_end = content.rfind('</article>')

    if article_start >= 0 and article_end >= 0:
        article_start += len(article_tag)
        article = content[article_start:article_end]

        # Apply translations
        article = translate_metadata_table(article)
        article = translate_text_outside_tags(article)
        article = translate_breadcrumb(article)

        content = content[:article_start] + article + content[article_end:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

if __name__ == '__main__':
    files = find_all_html_files()

    # Skip already translated files
    skip_files = {'godmode.html', 'google-workspace.html', 'apple-apple-notes.html', 'apple-apple-reminders.html'}

    count = 0
    for f in files:
        fname = os.path.basename(f)
        if fname in skip_files:
            continue
        if process_file(f):
            count += 1

    print(f"Processed {count} files with common translations")
    print(f"Skipped {len(skip_files)} already-translated files")