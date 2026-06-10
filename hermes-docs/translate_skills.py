#!/usr/bin/env python3
"""
Translation helper script for Hermes docs skill HTML files.
Extracts article content, title, and breadcrumb from HTML files,
outputs a JSON structure for translation, and writes back translated content.
"""
import os, json, re, sys

BASE = r'F:\培训\AI辅助日常工作材料\hermes-docs\user-guide\skills'

def extract_article(filepath):
    """Extract article content, title English part, and breadcrumb from HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title tag content (English part before " - Hermes 官方文档")
    title_match = re.search(r'<title>(.*?)\s*-\s*Hermes 官方文档</title>', content)
    title_en = title_match.group(1) if title_match else ''

    # Extract article content
    article_match = re.search(r'<article class="docs-content">(.*?)</article>', content, re.DOTALL)
    article_content = article_match.group(1) if article_match else ''

    # Extract breadcrumb text (the last segment after last /)
    breadcrumb_match = re.search(r'<div class="docs-breadcrumb">.*?/\s*([^<]+)</div>', article_content)
    breadcrumb_en = breadcrumb_match.group(1).strip() if breadcrumb_match else ''

    return {
        'filepath': filepath,
        'title_en': title_en,
        'breadcrumb_en': breadcrumb_en,
        'article_content': article_content,
        'full_content': content
    }

def find_article_boundaries(content):
    """Find start and end positions of article tag in content."""
    start_match = re.search(r'<article class="docs-content">', content)
    if not start_match:
        return None, None
    start_pos = start_match.end()

    # Find matching </article>
    end_match = re.search(r'</article>', content[start_pos:])
    if not end_match:
        return None, None
    end_pos = start_pos + end_match.start()

    return start_pos, end_pos

def write_translated(filepath, original_content, translated_article, translated_title, translated_breadcrumb):
    """Write back translated content to HTML file."""
    # Replace title
    new_content = re.sub(
        r'<title>.*?-\s*Hermes 官方文档</title>',
        f'<title>{translated_title} - Hermes 官方文档</title>',
        original_content
    )

    # Replace breadcrumb last segment
    new_content = re.sub(
        r'(<div class="docs-breadcrumb">.*?/)\s*[^<]+(</div>)',
        lambda m: m.group(1) + ' ' + translated_breadcrumb + m.group(2),
        new_content
    )

    # Replace article content
    start_pos, end_pos = find_article_boundaries(new_content)
    if start_pos is not None:
        new_content = new_content[:start_pos] + translated_article + new_content[end_pos:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == '__main__':
    # List all HTML files
    files = []
    for root, dirs, fnames in os.walk(BASE):
        for fname in fnames:
            if fname.endswith('.html'):
                files.append(os.path.join(root, fname))
    files.sort()

    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        for f in files:
            print(f)
        print(f'Total: {len(files)}')
    elif len(sys.argv) > 1 and sys.argv[1] == '--extract':
        idx = int(sys.argv[2])
        info = extract_article(files[idx])
        print(json.dumps({
            'filepath': info['filepath'],
            'title_en': info['title_en'],
            'breadcrumb_en': info['breadcrumb_en']
        }, ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == '--count':
        print(len(files))
    else:
        print(f"Usage: {sys.argv[0]} --list|--extract N|--count")