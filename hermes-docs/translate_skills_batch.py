#!/usr/bin/env python3
"""
Batch translate Hermes docs skill HTML files from English to Chinese.
Strategy: Read each file, apply translation mappings, write back.
Only translates content inside <article class="docs-content">...</article>,
title tag, and breadcrumb.
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

def translate_file(filepath, translations):
    """Translate a single HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    rel_path = os.path.relpath(filepath, BASE).replace('\\', '/')

    if rel_path not in translations:
        return False

    trans = translations[rel_path]

    # Replace title
    content = re.sub(
        r'(<title>).*?(</title>)',
        r'\g<1>' + trans['title'] + r'\2',
        content
    )

    # Replace article content
    article_tag = '<article class="docs-content">'
    article_start = content.find(article_tag) + len(article_tag)
    article_end = content.rfind('</article>')

    if article_start >= 0 and article_end >= 0:
        content = content[:article_start] + trans['article'] + content[article_end:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

if __name__ == '__main__':
    files = find_all_html_files()
    print(f"Found {len(files)} HTML files")
    # This script reads translations from a JSON file
    if len(os.sys.argv) > 1:
        trans_file = os.sys.argv[1]
        with open(trans_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        count = 0
        for f in files:
            if translate_file(f, translations):
                count += 1
        print(f"Translated {count} files")
    else:
        # Just list files needing translation
        for i, f in enumerate(files):
            rel = os.path.relpath(f, BASE).replace('\\', '/')
            print(f"{i}: {rel}")