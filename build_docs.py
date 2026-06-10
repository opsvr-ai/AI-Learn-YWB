import os, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).parent

LANG = 'en'
if '--lang' in sys.argv:
    idx = sys.argv.index('--lang')
    if idx + 1 < len(sys.argv):
        LANG = sys.argv[idx + 1]

SRC = ROOT / 'hermes-website' / 'docs'
I18N = ROOT / 'hermes-website-i18n' / 'docs'
OUT = ROOT / 'hermes-docs'

nav_tpl = (ROOT / 'templates' / 'nav.html').read_text(encoding='utf-8')
footer_tpl = (ROOT / 'templates' / 'footer.html').read_text(encoding='utf-8')
page_top = (ROOT / 'templates' / 'page-top.html').read_text(encoding='utf-8')
page_bot = (ROOT / 'templates' / 'page-bot.html').read_text(encoding='utf-8')
sidebar_html = (ROOT / 'templates' / 'sidebar.html').read_text(encoding='utf-8')


def parse_frontmatter(text):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).strip().split('\n'):
        if ':' in line:
            k, _, v = line.partition(':')
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, text[m.end():]


def md_to_html(text):
    lines = []
    in_code = False
    code_buf = []
    code_lang = ''
    in_table = False

    for raw in text.split('\n'):
        line = raw.rstrip()

        if line.startswith('```'):
            if in_code:
                lang_label = f'<span class="code-lang">{code_lang}</span>' if code_lang else ''
                code_text = '\n'.join(code_buf)
                lines.append(f'<div class="code-block">{lang_label}<button class="copy-btn" onclick="copyDocCode(this)">copy</button>\n{code_text}\n</div>')
                code_buf = []
                in_code = False
            else:
                code_lang = line[3:].strip()
                in_code = True
            continue

        if in_code:
            code_buf.append(line)
            continue

        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            txt = line.lstrip('#').strip()
            lines.append(f'<h{level}>{txt}</h{level}>')
            continue

        if line.strip() == '---':
            lines.append('<hr>')
            continue

        if line.strip() == '' and in_table:
            lines.append('</tbody></table>')
            in_table = False
            continue

        line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
        line = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', line)
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)

        def fix_link(m):
            label = m.group(1)
            href = m.group(2)
            if href.endswith('.md') and not href.startswith('http'):
                href = href.replace('.md', '.html')
            if href.startswith('../'):
                href = '/' + href[3:]
            if href.startswith('/docs/'):
                href = '/hermes-docs' + href[5:]
            return f'<a href="{href}">{label}</a>'

        line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', fix_link, line)
        line = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', line)

        if '|' in line and line.strip().startswith('|'):
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if not cells:
                continue
            if not in_table:
                lines.append('<table><thead><tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr></thead><tbody>')
                in_table = True
            elif re.match(r'^[\s\-:|]+$', cells[0]):
                pass
            elif in_table:
                lines.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
            continue

        if line.strip():
            lines.append(f'<p>{line}</p>')

    if in_table:
        lines.append('</tbody></table>')
    return '\n'.join(lines)


def build():
    if OUT.exists():
        shutil.rmtree(OUT)

    count = 0
    translated_count = 0
    for md_file in sorted(SRC.rglob('*.md')):
        rel = md_file.relative_to(SRC)
        out_file = OUT / rel.with_suffix('.html')
        out_file.parent.mkdir(parents=True, exist_ok=True)

        src_file = md_file
        if LANG == 'zh':
            i18n_file = I18N / rel
            if i18n_file.exists():
                src_file = i18n_file
                translated_count += 1

        content = src_file.read_text(encoding='utf-8')
        meta, body = parse_frontmatter(content)
        title = meta.get('title', rel.stem)

        parts = rel.parts
        bc = '<a href="/hermes-docs/index.html">docs</a>'
        acc = '/hermes-docs'
        for p in parts[:-1]:
            acc += '/' + p
            bc += f' / <a href="{acc}/">{p}</a>'
        bc += f' / {title}'

        html = page_top.replace('{TITLE}', title)
        html = html.replace('{{NAV}}', nav_tpl)
        html = html.replace('{{SIDEBAR}}', sidebar_html)
        html = html.replace('{BREADCRUMB}', bc)
        html += md_to_html(body)
        html += page_bot.replace('{{FOOTER}}', footer_tpl)

        out_file.write_text(html, encoding='utf-8')
        count += 1

    msg = f'Done: {count} files -> {OUT}'
    if LANG == 'zh':
        msg += f' ({translated_count} translated)'
    print(msg)


if __name__ == '__main__':
    build()
