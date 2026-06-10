import os, re, json, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / 'hermes-website' / 'docs'
OUT = ROOT / 'hermes-website-i18n' / 'docs'

API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
API_BASE = os.environ.get('ANTHROPIC_BASE_URL', 'http://7.24.28.9:8080')
API_URL = f'{API_BASE}/v1/chat/completions'

# 每分钟最多6次请求（限制8次，留余量）
DELAY = 12


def call_api(prompt):
    """调用 OpenAI 兼容接口翻译"""
    data = json.dumps({
        'model': 'anthropic/claude-sonnet-4-6',
        'messages': [
            {'role': 'system', 'content': 'You are a technical translator. Translate the following English technical documentation into Simplified Chinese. Keep these rules:\n1. Preserve ALL markdown syntax (##, **, `, [], etc)\n2. Preserve ALL code blocks, HTML tags, URLs unchanged\n3. Translate natural language text only\n4. Keep technical terms reasonably - use English terms when the Chinese equivalent is uncommon (e.g. "API", "MCP", "CLI")\n5. Output ONLY the translated text, no explanations'},
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 4096,
        'temperature': 0.1
    }).encode('utf-8')

    req = urllib.request.Request(API_URL, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    })

    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read())
    return result['choices'][0]['message']['content']


def should_translate(line):
    """判断某行是否需要翻译"""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith('```'):
        return False
    if stripped.startswith('#'):
        return True
    if re.match(r'^[\s\-:|]+$', stripped):
        return False
    if stripped.startswith('|') or stripped.startswith('>'):
        return True
    if stripped.startswith('<') and not stripped.startswith('<<'):
        return False
    if stripped.startswith('http'):
        return False
    if stripped == '---':
        return False
    return True


def translate_text(text):
    """翻译一段文本，处理可能的长文本"""
    if len(text) < 20:
        return text
    try:
        result = call_api(text)
        return result
    except Exception as e:
        print(f'  Translation error: {e}')
        return text


def translate_file(md_file, out_file):
    """翻译单个 .md 文件"""
    content = md_file.read_text(encoding='utf-8')

    # 分离 frontmatter 和 body
    m = re.match(r'^(---\s*\n.*?\n---\s*\n)', content, re.DOTALL)
    fm = m.group(1) if m else ''
    body = content[m.end():] if m else content

    # 收集要翻译的段落
    paragraphs = []
    current = []
    in_code = False

    for line in body.split('\n'):
        if line.startswith('```'):
            in_code = not in_code
            if current:
                paragraphs.append('\n'.join(current))
                current = []
            current.append(line)
            continue

        if in_code:
            current.append(line)
            continue

        if should_translate(line):
            current.append(line)
        else:
            if current:
                paragraphs.append('\n'.join(current))
                current = []
            if line.strip():
                paragraphs.append(line)

    if current:
        paragraphs.append('\n'.join(current))

    # 逐段翻译
    translated = []
    for i, para in enumerate(paragraphs):
        if any(para.strip().startswith(c) for c in ['```', '---', '<', 'http']):
            translated.append(para)
        elif len(para.strip()) < 10:
            translated.append(para)
        else:
            print(f'    [{i+1}/{len(paragraphs)}]', end='', flush=True)
            result = translate_text(para)
            translated.append(result)
            if i < len(paragraphs) - 1:
                time.sleep(DELAY)
        print('')

    # 重建
    result = fm + '\n'.join(translated)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(result, encoding='utf-8')


def main():
    if not API_KEY:
        print('Error: Set ANTHROPIC_API_KEY environment variable')
        return

    files = sorted(SRC.rglob('*.md'))
    total = len(files)
    print(f'Translating {total} files...')
    print(f'API: {API_URL}')
    print(f'Delay between requests: {DELAY}s')
    print()

    done = 0
    for md_f in files:
        rel = md_f.relative_to(SRC)
        out_f = OUT / rel

        if out_f.exists():
            print(f'  SKIP {rel} (already translated)')
            done += 1
            continue

        print(f'  [{done+1}/{total}] {rel}')
        try:
            translate_file(md_f, out_f)
            done += 1
        except Exception as e:
            print(f'    FAILED: {e}')
            time.sleep(30)

        if done < total:
            time.sleep(DELAY)

    print(f'\nDone: {done}/{total} files translated')


if __name__ == '__main__':
    main()
