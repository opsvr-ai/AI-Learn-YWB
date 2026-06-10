#!/usr/bin/env python3
"""
Hermes 文档批量生成器 v3 — 从 hermes-website 中文翻译生成 hermes-docs HTML。
逐行状态机处理，HTML 注释占位符策略避免 markdown 污染。
"""

import os, re
from markdown_it import MarkdownIt

SRC_DIR = r"E:\dev\AI辅助日常工作材料\hermes-website\i18n\zh-Hans\docusaurus-plugin-content-docs\current"
OUT_DIR = r"E:\dev\AI辅助日常工作材料\hermes-docs"

SIDEBAR_ORDER = [
    ("Getting Started", [
        ("快速入门",              "getting-started/quickstart.html"),
        ("安装指南",              "getting-started/installation.html"),
        ("Android (Termux)",      "getting-started/termux.html"),
        ("Nix 设置",              "getting-started/nix-setup.html"),
        ("更新",                  "getting-started/updating.html"),
        ("学习路径",              "getting-started/learning-path.html"),
    ]),
    ("用户指南", [
        ("CLI 界面",              "user-guide/cli.html"),
        ("TUI 界面",              "user-guide/tui.html"),
        ("Desktop 应用",          "user-guide/desktop.html"),
        ("Windows 原生",          "user-guide/windows-native.html"),
        ("配置",                  "user-guide/configuration.html"),
        ("模型配置",              "user-guide/configuring-models.html"),
        ("会话管理",              "user-guide/sessions.html"),
        ("配置文件",              "user-guide/profiles.html"),
        ("配置文件分发",          "user-guide/profile-distributions.html"),
        ("Git Worktrees",         "user-guide/git-worktrees.html"),
        ("Docker",                "user-guide/docker.html"),
        ("安全",                  "user-guide/security.html"),
        ("消息网关",              "user-guide/messaging/index.html"),
    ]),
    ("核心功能", [
        ("功能概览",              "user-guide/features/overview.html"),
        ("工具 & 工具集",         "user-guide/features/tools.html"),
        ("Skills 系统",           "user-guide/features/skills.html"),
        ("记忆系统",              "user-guide/features/memory.html"),
        ("MCP 集成",              "user-guide/features/mcp.html"),
        ("浏览器",                "user-guide/features/browser.html"),
        ("语音模式",              "user-guide/features/voice-mode.html"),
        ("定时任务",              "user-guide/features/cron.html"),
        ("网络搜索",              "user-guide/features/web-search.html"),
        ("Hook",                  "user-guide/features/hooks.html"),
        ("插件",                  "user-guide/features/plugins.html"),
        ("子智能体委派",          "user-guide/features/delegation.html"),
        ("Kanban",                "user-guide/features/kanban.html"),
        ("代码执行",              "user-guide/features/code-execution.html"),
        ("计算机使用",            "user-guide/features/computer-use.html"),
        ("批量处理",              "user-guide/features/batch-processing.html"),
        ("API 服务器",            "user-guide/features/api-server.html"),
        ("图片生成",              "user-guide/features/image-generation.html"),
        ("秘密管理",              "user-guide/secrets/index.html"),
    ]),
    ("实用指南", [
        ("使用 MCP",              "guides/use-mcp-with-hermes.html"),
        ("使用 Soul/人格",        "guides/use-soul-with-hermes.html"),
        ("使用语音模式",          "guides/use-voice-mode-with-hermes.html"),
        ("使用 Skills",           "guides/work-with-skills.html"),
        ("Telegram 助手",         "guides/team-telegram-assistant.html"),
        ("每日简报机器人",        "guides/daily-briefing-bot.html"),
        ("GitHub PR Review",      "guides/github-pr-review-agent.html"),
        ("自动化模板",            "guides/automation-templates.html"),
        ("用 Cron 自动化",        "guides/automate-with-cron.html"),
        ("委托模式",              "guides/delegation-patterns.html"),
        ("提示技巧",              "guides/tips.html"),
        ("构建 Hermes 插件",      "guides/build-a-hermes-plugin.html"),
        ("MCP 配置",              "reference/mcp-config-reference.html"),
    ]),
    ("参考文档", [
        ("CLI 命令参考",           "reference/cli-commands.html"),
        ("环境变量",               "reference/environment-variables.html"),
        ("Skills 目录",            "reference/skills-catalog.html"),
        ("可选 Skills 目录",       "reference/optional-skills-catalog.html"),
        ("工具参考",               "reference/tools-reference.html"),
        ("工具集参考",             "reference/toolsets-reference.html"),
        ("斜杠命令",               "reference/slash-commands.html"),
        ("配置文件命令",           "reference/profile-commands.html"),
        ("模型目录",               "reference/model-catalog.html"),
        ("FAQ",                    "reference/faq.html"),
    ]),
]

ADMONITION_ICONS = {
    'tip': '💡', 'note': '📝', 'info': 'ℹ️',
    'warning': '⚠️', 'danger': '🔴', 'caution': '⚡',
}
ADMONITION_LABELS = {
    'tip': '提示', 'note': '注意', 'info': '信息',
    'warning': '警告', 'danger': '危险', 'caution': '注意',
}

CATEGORY_CN = {
    "getting-started": "Getting Started", "user-guide": "用户指南",
    "features": "核心功能", "guides": "实用指南",
    "reference": "参考文档", "developer-guide": "开发者指南",
    "integrations": "集成", "messaging": "消息网关",
    "secrets": "秘密管理", "skills": "Skills",
}

EXCLUDE_PREFIXES = {'skills'}


# ── 预处理 ─────────────────────────────────────────────────

def preprocess(text):
    """逐行处理，用 HTML 注释占位符替换代码块和 admonition。"""
    lines = text.split('\n')
    out_lines = []
    placeholders = []

    code_lines = []
    in_code = False

    admon_lines = []
    admon_type = None
    admon_title = None
    in_admon = False

    for line in lines:
        stripped = line.strip()

        # code blocks
        if stripped.startswith('```'):
            if in_code:
                lang = code_lines[0] if code_lines else ''
                body = '\n'.join(code_lines[1:]) if len(code_lines) > 1 else ''
                body_esc = (body.replace('&', '&amp;')
                               .replace('<', '&lt;')
                               .replace('>', '&gt;'))
                html = (f'<div class="code-block"><span class="code-lang">{lang}</span>'
                        f'<button class="copy-btn" onclick="copyDocCode(this)">copy</button>\n'
                        f'{body_esc}\n'
                        f'</div>')
                ph = f'<!--PH_C{len(placeholders)}-->'
                placeholders.append((ph, html))
                out_lines.append(ph)
                code_lines = []
                in_code = False
            else:
                in_code = True
                code_lines = [stripped[3:].strip()]
            continue

        if in_code:
            code_lines.append(line)
            continue

        # admonitions
        if stripped.startswith(':::'):
            adv = stripped[3:].strip()
            parts = adv.split(None, 1)
            kw = parts[0].lower() if parts else ''

            if not in_admon:
                if kw in ADMONITION_ICONS:
                    in_admon = True
                    admon_type = kw
                    admon_title = parts[1] if len(parts) > 1 else ''
                    admon_lines = []
                else:
                    out_lines.append(line)
            else:
                html = _build_admon_html(admon_type, admon_title, '\n'.join(admon_lines))
                ph = f'<!--PH_A{len(placeholders)}-->'
                placeholders.append((ph, html))
                out_lines.append(ph)
                in_admon = False
                admon_lines = []
                admon_type = None
                admon_title = None
            continue

        if in_admon:
            admon_lines.append(line)
            continue

        # regular lines: convert internal links and images
        line = re.sub(r'(\[[^\]]*\]\()([^)]*)\.mdx?(#[^)]*)?(\))',
                     lambda m: m.group(1) + m.group(2) + '.html' + (m.group(3) or '') + m.group(4),
                     line)
        line = re.sub(r'!\[([^\]]*)\]\(/img/([^)]+)\)',
                     lambda m: (f'<img src="images/{os.path.basename(m.group(2))}" '
                                f'alt="{m.group(1)}" '
                                f'style="max-width:100%;border-radius:8px;border:1px solid #e5e7eb;">'),
                     line)
        out_lines.append(line)

    if in_admon:
        html = _build_admon_html(admon_type, admon_title, '\n'.join(admon_lines))
        ph = f'<!--PH_A{len(placeholders)}-->'
        placeholders.append((ph, html))
        out_lines.append(ph)

    return '\n'.join(out_lines), placeholders


def _build_admon_html(kind, title, content):
    icon = ADMONITION_ICONS.get(kind, '💡')
    label = title or ADMONITION_LABELS.get(kind, '提示')
    css = 'tip warning' if kind in ('warning', 'danger', 'caution') else 'tip'
    # Process content through markdown-it to render inline code, links, bold etc.
    # Also convert .md links to .html and images
    content = re.sub(r'(\[[^\]]*\]\()([^)]*)\.mdx?(#[^)]*)?(\))',
                     lambda m: m.group(1) + m.group(2) + '.html' + (m.group(3) or '') + m.group(4),
                     content)
    content = re.sub(r'!\[([^\]]*)\]\(/img/([^)]+)\)',
                     lambda m: f'<img src="images/{os.path.basename(m.group(2))}" alt="{m.group(1)}" style="max-width:100%;border-radius:8px;border:1px solid #e5e7eb;">',
                     content)
    content_html = _md_admon.render(content)
    # Strip wrapping <p> tags if the content is inline
    content_html = re.sub(r'^<p>(.*)</p>\n?$', r'\1', content_html)
    return f'<div class="{css}"><strong>{icon} {label}</strong>\n{content_html}\n</div>'


_md_admon = MarkdownIt("commonmark", {"breaks": False, "html": True})


# ── Frontmatter & Markdown ───────────────────────────────

def extract_frontmatter(text):
    meta = {"title": "", "description": ""}
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if m:
        block = m.group(1)
        for line in block.split('\n'):
            if ':' in line:
                key, _, val = line.partition(':')
                key = key.strip().lower()
                val = val.strip().strip('"').strip("'")
                if key in ('title', 'description'):
                    meta[key] = val
        text = text[m.end():]
    return text, meta


def extract_title(body):
    m = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
    return m.group(1).strip() if m else ''


def markdown_to_html(text):
    md = MarkdownIt("commonmark", {"breaks": False, "html": True})
    md.enable(["table"])
    return md.render(text)


def render_doc(text):
    """处理单篇文档：frontmatter -> 预处理 -> markdown-it -> 恢复占位符"""
    body, meta = extract_frontmatter(text)
    title = meta.get('title') or extract_title(body)

    processed, phs = preprocess(body)
    html_body = markdown_to_html(processed)

    for ph, html in phs:
        html_body = html_body.replace(ph, html)

    html_body = re.sub(r'^<h1>.*?</h1>\n?', '', html_body, count=1)
    return title, html_body


# ── 模板 ─────────────────────────────────────────────────

def make_sidebar(current_path):
    lines = ['<ul class="sidebar-menu">']
    lines.append('  <li class="sidebar-top"><a href="/hermes-docs/index.html">文档首页</a></li>')
    for cat_name, items in SIDEBAR_ORDER:
        lines.append(f'  <li class="sidebar-category"><span class="sidebar-cat-title">{cat_name}</span>')
        lines.append('    <ul>')
        for label, href in items:
            active = ' class="active"' if href == current_path else ''
            lines.append(f'      <li><a href="/hermes-docs/{href}"{active}>{label}</a></li>')
        lines.append('    </ul>')
        lines.append('  </li>')
    lines.append('</ul>')
    return '\n'.join(lines)


def make_page(title, breadcrumb, sidebar, body_html):
    tmpl = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - Hermes 官方文档</title>
  <link rel="stylesheet" href="/css/style.css">
  <link rel="stylesheet" href="/css/hermes-docs.css">
</head>
<body>
<nav class="nav">
  <div class="nav-inner">
    <a href="/index.html" class="nav-logo"><span class="icon">AI</span>运维部AI学习平台</a>
    <div id="visit-counter" class="visit-counter">---</div>
    <div class="checkin-wrapper">
      <button class="checkin-btn" onclick="doCheckin(this)">\u5b66\u4e60\u6253\u5361</button>
      <span id="checkin-area" class="checkin-area">---</span>
    </div>
    <ul class="nav-links">
      <li><a href="/index.html">首页</a></li>
      <li class="has-submenu">
        <span class="nav-label">🎓 AI学习</span>
        <ul class="nav-submenu">
          <li><a href="/hermes.html">Hermes-Agent</a></li>
          <li><a href="/claude.html">Claude Code</a></li>
          <li class="menu-divider"></li>
          <li><a href="/ai-basics.html">大模型基础</a></li>
          <li><a href="/hermes-docs/index.html">Hermes 官方文档</a></li>
          <li><a href="/api-key.html">API Key 申请</a></li>
        </ul>
      </li>
      <li><a href="/token-stats.html">📊 Token统计</a></li>
      <li class="has-submenu">
        <span class="nav-label">💬 社区</span>
        <ul class="nav-submenu">
          <li><a href="/cases.html">案例分享</a></li>
          <li><a href="/feedback.html">问题反馈</a></li>
        </ul>
      </li>
    </ul>
  </div>
</nav>
<main class="docs-page">
  <aside class="docs-sidebar" id="sidebar">
    <div class="sidebar-search">
      <input type="text" id="sidebar-search-input" placeholder="\u641c\u7d22\u6587\u6863..." oninput="filterSidebar()">
    </div>
    <nav class="sidebar-nav" id="sidebar-nav">
{sidebar}
    </nav>
  </aside>
  <button id="sidebar-toggle" class="sidebar-toggle" title="\u5207\u6362\u4fa7\u8fb9\u680f">&#9776;</button>
  <article class="docs-content">
    <div class="docs-breadcrumb">{breadcrumb}</div>{body_html}
  </article>
</main>
<footer class="footer">
  <div class="container">
    <p>Copyright &copy; \u751f\u4ea7\u8fd0\u7ef4\u90e8\uff0c\u5185\u90e8\u5b66\u4e60\u8d44\u6599</p>
  </div>
</footer>
<button id="backToTop" class="back-to-top" title="\u56de\u5230\u9876\u90e8">&#8593;</button>
<script src="/js/main.js"></script>
<script src="/js/hermes-docs.js"></script>
</body>
</html>'''
    return tmpl.format(title=title, breadcrumb=breadcrumb, sidebar=sidebar, body_html=body_html)


# ── 主流程 ─────────────────────────────────────────────────

def process_file(src_path, rel_path):
    parts = rel_path.replace('\\', '/').split('/')
    basename = os.path.basename(rel_path)

    if basename in ('index.md', 'index.mdx'):
        if len(parts) == 1:
            return None, None
        out_rel = os.path.join(os.path.dirname(rel_path), 'index.html')
    else:
        out_rel = re.sub(r'\.mdx?$', '.html', rel_path)

    with open(src_path, 'r', encoding='utf-8') as f:
        text = f.read()

    title, html_body = render_doc(text)
    if not title:
        return None, None

    cat = parts[0] if len(parts) >= 2 else ''
    cat_cn = CATEGORY_CN.get(cat, cat)
    breadcrumb = f'<a href="/hermes-docs/index.html">文档</a> / {cat_cn} / {title}'

    sidebar = make_sidebar(out_rel.replace('\\', '/'))
    full_html = make_page(title, breadcrumb, sidebar, html_body)

    out_path = os.path.join(OUT_DIR, out_rel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    return out_rel, title


def make_index():
    sidebar = make_sidebar('')
    body = '''<div class="docs-breadcrumb"><a href="/hermes-docs/index.html">docs</a> / Hermes Agent 文档</div>
<h1>Hermes Agent</h1>
<p>由 <a href="https://nousresearch.com">Nous Research</a> 打造的自我进化 AI 智能体。唯一内置学习循环的智能体 — 它能从经验中创建技能，在使用过程中自我改进，主动提示自己持续积累知识，并逐步构建对你的深度理解。</p>
<div style="display:flex;gap:1rem;margin-bottom:2rem;flex-wrap:wrap;">
  <a href="/hermes-docs/getting-started/quickstart.html" style="display:inline-block;padding:0.6rem 1.2rem;background:#2563eb;color:#fff;border-radius:8px;font-weight:600;text-decoration:none;">快速开始 &rarr;</a>
  <a href="https://github.com/NousResearch/hermes-agent" style="display:inline-block;padding:0.6rem 1.2rem;border:1px solid var(--gray-300);border-radius:8px;text-decoration:none;">GitHub 仓库</a>
</div>
<h2>安装</h2>
<p><strong>Linux / macOS / WSL2</strong></p>
<div class="code-block"><span class="code-lang">bash</span><button class="copy-btn" onclick="copyDocCode(this)">copy</button>
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
</div>
<p><strong>Windows（原生 PowerShell）</strong></p>
<div class="code-block"><span class="code-lang">powershell</span><button class="copy-btn" onclick="copyDocCode(this)">copy</button>
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
</div>
<p>详见完整的 <a href="/hermes-docs/getting-started/installation.html">安装指南</a>。</p>'''
    full = make_page("Hermes Agent 文档", "", sidebar, body)
    with open(os.path.join(OUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(full)
    print("  OK 首页 -> index.html")


def main():
    print("=" * 60)
    print("Hermes 文档批量生成器 v3")
    print(f"源: {SRC_DIR}")
    print(f"出: {OUT_DIR}")
    print("=" * 60)

    converted = 0
    skipped = 0

    for root, dirs, files in os.walk(SRC_DIR):
        rel_root = os.path.relpath(root, SRC_DIR)
        if any(ex in rel_root.split(os.sep) for ex in EXCLUDE_PREFIXES):
            continue

        for fname in files:
            if not fname.endswith(('.md', '.mdx')):
                continue
            if fname.startswith('_'):
                continue
            src_path = os.path.join(root, fname)
            rel_path = os.path.relpath(src_path, SRC_DIR)

            out_rel, title = process_file(src_path, rel_path)
            if out_rel:
                print(f"  OK {rel_path} -> {out_rel}")
                converted += 1
            else:
                skipped += 1

    make_index()
    print(f"\n完成！已生成 {converted} 个页面，跳过 {skipped} 个文件")


if __name__ == '__main__':
    main()
