# -*- coding: utf-8 -*-
import re

with open('ai-news.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update hero date
content = content.replace('2026年6月23日', '2026年6月24日')
content = content.replace('第 23 期', '第 24 期')
content = content.replace('星期二', '星期三')

# 2. Update trends
old_t = '<div class="card"><div class="card-icon blue">&#127760;</div><h4>'
idx = content.find(old_t)
if idx > 0:
    # Find the end of trends section
    end_marker = '</div>\n    </div>\n  </section>\n\n</main>'
    trends_end = content.find(end_marker)
    if trends_end == -1:
        trends_end = content.find('</section>\n\n</main>')

    # Find start of news section end
    news_section_end = content.find('<!-- Key Trends -->')

    # Replace trends cards
    old_trends_start = content.find('<!-- Key Trends -->')
    old_trends_block = content[old_trends_start:trends_end] if trends_end > old_trends_start else ""

    new_trends_block = '''<!-- Key Trends -->
  <section class="section section-gray">
    <div class="container">
      <h2 class="section-title">本月关键趋势</h2>
      <div class="grid-3" style="margin-top:16px;">
        <div class="card"><div class="card-icon blue">&#127760;</div><h4>国产大模型跨越"质变点"</h4><p>豆包2.1和GLM-5.2在编程与Agent能力上实现质变。中国Token日消费突破180万亿，国产模型从"追赶"进入"并跑"阶段。</p></div>
        <div class="card"><div class="card-icon purple">&#129504;</div><h4>AI Agent生态全面爆发</h4><p>微信"小微"开启内测，京东美团携程等10+企业接入。支付宝完成3亿笔AI智能体支付，Agent从概念走向规模化应用。</p></div>
        <div class="card"><div class="card-icon orange">&#128200;</div><h4>AI芯片股剧烈震荡</h4><p>韩国KOSPI单日暴跌10%触发熔断，纳斯达克跌3.3%。投资者开始质疑AI基建投入回报，但中国AI板块逆势上涨。</p></div>
      </div>
    </div>
  </section>'''

    content = content[:old_trends_start] + new_trends_block + content[trends_end:] if trends_end > old_trends_start else content[:old_trends_start] + new_trends_block + content[content.find('</main>', old_trends_start):]

print("Updated hero + trends. Now replacing news items...")

# 3. Replace all news items
# Find the news list boundaries
news_list_start = content.find('<div class="news-list" id="newsList">')
# Find the end of the news list - look for the closing pattern
closing = content.find('</div><!-- /news-list -->', news_list_start)
if closing == -1:
    closing = content.find('</div>\n    </div>\n  </section>\n\n', news_list_start)

before = content[:news_list_start]
after_start = content.find('</div>\n    </div>\n  </section>\n\n  <!-- Key Trends -->', news_list_start)
if after_start == -1:
    after_start = content.find('\n  <!-- Key Trends -->', news_list_start)
after = content[after_start:]

print(f"news_list_start={news_list_start}, after_start={after_start}")

# Read new items from external file
with open('news_items_20260624.html', 'r', encoding='utf-8') as f:
    new_items = f.read()

content = before + new_items + after

with open('ai-news.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Done! File size: {len(content)} chars")
