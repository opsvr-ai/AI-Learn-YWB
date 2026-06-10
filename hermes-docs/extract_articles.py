import os, re, json

BASE = r'F:\培训\AI辅助日常工作材料\hermes-docs\user-guide\skills'

# Extract all article content to a JSON file for translation reference
files = []
for root, dirs, fnames in os.walk(BASE):
    for fname in fnames:
        if fname.endswith('.html'):
            files.append(os.path.join(root, fname))
files.sort()

result = {}
for f in files:
    rel = os.path.relpath(f, BASE).replace(os.sep, '/')
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()

    # Title
    title_match = re.search(r'<title>(.*?)</title>', content)
    title = title_match.group(1) if title_match else ''

    # Article
    article_tag = '<article class="docs-content">'
    astart = content.find(article_tag)
    aend = content.rfind('</article>')
    article = ''
    if astart >= 0 and aend >= 0:
        article = content[astart+len(article_tag):aend]

    result[rel] = {
        'title': title,
        'article': article
    }

# Write to a JSON file for reference
out_path = os.path.join(BASE, '_articles_for_translation.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(result)} articles to {out_path}")
print(f"File size: {os.path.getsize(out_path)} bytes")