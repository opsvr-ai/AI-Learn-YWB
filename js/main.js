/* ============================================
   公共交互脚本 - AI赋能日常工作 培训站点
   现代重构版 v2（含可访问性增强）
   ============================================ */
'use strict';

// ============================================
// DOMContentLoaded
// ============================================
document.addEventListener('DOMContentLoaded', () => {

  const backBtn = document.getElementById('backToTop');

  // --- 导航高亮 ---
  const current = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(link => {
    if (link.getAttribute('href') === current) link.classList.add('active');
  });

  // --- 回到顶部 ---
  if (backBtn) {
    backBtn.setAttribute('aria-label', '回到顶部');
    const toggle = () => backBtn.classList.toggle('visible', window.scrollY > 400);
    window.addEventListener('scroll', toggle, { passive: true });
    backBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
    toggle();
  }

  // --- Tab 切换（事件委托 + ARIA）---
  document.querySelectorAll('.tabs').forEach(tabs => {
    tabs.setAttribute('role', 'tablist');
    tabs.querySelectorAll('.tab-btn').forEach(btn => {
      btn.setAttribute('role', 'tab');
    });
    const panels = tabs.parentElement.querySelectorAll('.tab-panel');
    panels.forEach(p => p.setAttribute('role', 'tabpanel'));

    tabs.addEventListener('click', e => {
      const btn = e.target.closest('.tab-btn');
      if (!btn) return;
      const target = btn.dataset.tab;
      tabs.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      panels.forEach(p => p.classList.toggle('active', p.dataset.tab === target));
    });
  });

  // --- Accordion + ARIA ---
  document.querySelectorAll('.accordion-trigger').forEach(trigger => {
    trigger.setAttribute('aria-expanded', 'false');
    trigger.addEventListener('click', () => {
      const item = trigger.parentElement;
      const nowOpen = item.classList.toggle('open');
      trigger.setAttribute('aria-expanded', nowOpen ? 'true' : 'false');
    });
  });

  // --- 导航栏 ARIA ---
  document.querySelector('.nav')?.setAttribute('aria-label', '主导航');

  // --- IMG alt 补充 ---
  document.querySelectorAll('img:not([alt])').forEach(img => img.setAttribute('alt', ''));
  initPageNav();

});

// ============================================
// Code块 Tab 切换
// ============================================
window.switchCodeTab = (type, btn) => {
  if (btn) {
    const container = btn.parentElement;
    if (container?.classList.contains('code-tabs')) {
      container.querySelectorAll('.code-tab').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      let el = container.nextElementSibling;
      while (el) {
        if (el.classList.contains('code-block')) el.style.display = 'none';
        el = el.nextElementSibling;
      }
    }
  } else {
    const tabs = document.querySelectorAll('.code-tab');
    tabs.forEach(t => t.classList.remove('active'));
    tabs[type === 'cmd' ? 0 : 1]?.classList.add('active');
    document.querySelectorAll('[id^="code-"]').forEach(b => b.style.display = 'none');
  }
  const target = document.getElementById('code-' + type);
  if (target) target.style.display = 'block';
};

// ============================================
// 复制代码块
// ============================================
window.copyCode = (blockId, btn) => {
  const block = document.getElementById(blockId);
  if (!block) return;
  const text = block.innerText.replace(/^\s*\S+\s*\n/, '').replace(/\n\s*$/, '');

  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = '已复制!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 2000);
  }).catch(() => {
    const range = document.createRange();
    range.selectNodeContents(block);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  });
};

// ============================================
// Lightbox 图片放大
// ============================================
(() => {
  const lb = Object.assign(document.createElement('div'), { className: 'lightbox', id: 'lightbox' });
  lb.innerHTML = '<span class="lightbox-close" aria-label="关闭">&times;</span><img src="" alt="">';
  document.body.appendChild(lb);
  const img = lb.querySelector('img');

  lb.addEventListener('click', e => {
    if (e.target === lb || e.target.classList.contains('lightbox-close')) {
      lb.classList.remove('open');
    }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') lb.classList.remove('open'); });

  document.addEventListener('click', e => {
    const t = e.target;
    if (t.tagName === 'IMG' && (t.src.includes('/images/') || t.src.includes('images/'))) {
      img.src = t.src;
      img.alt = t.alt;
      lb.classList.add('open');
    }
  });
})();

// ============================================
// 指纹 / 用户 / 打卡 / 统计
// ============================================
(() => {

  const escapeHTML = str => {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
  };

  const getFingerprint = () => {
    const key = 'ai_train_fp';
    const cached = localStorage.getItem(key);
    if (cached) return cached;

    const fp = [
      navigator.userAgent, navigator.language, navigator.platform,
      navigator.hardwareConcurrency || 'unknown',
      screen.width + 'x' + screen.height + 'x' + screen.colorDepth,
      new Date().getTimezoneOffset(),
      navigator.maxTouchPoints || 0
    ].join('|');

    let hash = 0;
    for (let i = 0; i < fp.length; i++) {
      hash = ((hash << 5) - hash) + fp.charCodeAt(i);
      hash |= 0;
    }
    const result = 'fp_' + Math.abs(hash).toString(36);
    localStorage.setItem(key, result);
    return result;
  };

  const fingerprint = getFingerprint();
  const page = window.location.pathname.split('/').pop().replace('.html', '') || 'index';
  const today = new Date().toDateString();

  const getStoredUser = () => {
    try {
      const data = JSON.parse(localStorage.getItem('ai_train_users') || '{}');
      return data[fingerprint] || null;
    } catch { return null; }
  };

  const saveUser = (account) => {
    try {
      const data = JSON.parse(localStorage.getItem('ai_train_users') || '{}');
      data[fingerprint] = { account, updated: Date.now() };
      localStorage.setItem('ai_train_users', JSON.stringify(data));
    } catch { /* ignore */ }
    fetch('/api/register-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fingerprint, account })
    }).catch(() => {});
  };

  const getUserName = () => getStoredUser()?.account ?? null;
  window.getUserName = getUserName;
  let userName = getUserName();

  // --- API 请求（fetch + XHR 降级）---
  const apiFetch = (method, url, body) => {
    const opts = { method };
    if (body) {
      opts.headers = { 'Content-Type': 'application/json' };
      opts.body = JSON.stringify(body);
    }
    return fetch(url, opts);
  };

  const apiRequest = (method, url, body, onSuccess) => {
    apiFetch(method, url, body)
      .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(data => onSuccess(data))
      .catch(() => {
        try {
          const xhr = new XMLHttpRequest();
          xhr.open(method, url, true);
          if (body) xhr.setRequestHeader('Content-Type', 'application/json');
          xhr.onload = () => {
            if (xhr.status === 200) {
              try { onSuccess(JSON.parse(xhr.responseText)); } catch { renderFallback(); }
            } else { renderFallback(); }
          };
          xhr.onerror = renderFallback;
          xhr.send(body ? JSON.stringify(body) : null);
        } catch { renderFallback(); }
      });
  };

  const renderFallback = () => {
    const el = document.getElementById('visit-counter');
    if (el) el.innerHTML = '<span class="vc-icon">📊</span>统计服务连接中';
    const ck = document.getElementById('checkin-area');
    if (ck) ck.innerHTML = '<b>-</b>人今日';
  };

  const renderTicker = (users) => {
    const ticker = document.getElementById('checkin-ticker');
    if (!ticker) return;

    ticker.style.cssText = 'overflow:hidden;background:linear-gradient(90deg,#dbeafe,#d1fae5,#dbeafe);border-bottom:2px solid #10b981;white-space:nowrap;padding:8px 16px;font-size:0.92rem;color:#065f46;font-weight:500;';

    if (!users || users.length === 0) {
      ticker.innerHTML = '📝 今日还没有人打卡，在导航栏输入域账号后点击<strong>"打卡"</strong>成为第一个吧';
      return;
    }

    const names = users.map(u => escapeHTML(typeof u === 'string' ? u : (u.account || u))).join('  ⭐  ');
    const text = '🎉 ' + names + '  今日已完成学习打卡 ✓';
    const track = document.createElement('div');
    track.style.cssText = 'display:inline-flex;animation:ticker-scroll 24s linear infinite;';
    track.id = 'ticker-track';
    track.innerHTML = '<span style="display:inline-block;white-space:nowrap;padding-right:64px;">' + text + '</span><span style="display:inline-block;white-space:nowrap;padding-right:64px;">' + text + '</span>';
    ticker.innerHTML = '';
    ticker.appendChild(track);

    if (!document.getElementById('ticker-keyframes')) {
      const styleEl = Object.assign(document.createElement('style'), { id: 'ticker-keyframes' });
      styleEl.textContent = '@keyframes ticker-scroll{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}#checkin-ticker:hover #ticker-track{animation-play-state:paused}';
      document.head.appendChild(styleEl);
    }
  };

  const updateHelpCounter = (data) => {
    const el = document.getElementById('help-counter');
    if (el && data) {
      el.innerHTML = '<span class="help-icon">🙋</span> 累计 <span class="vc-num">' + (data.help_total || 0) + '</span>人需协助 · 今日 <span class="vc-num">' + (data.help_today || 0) + '</span>人';
    }
  };

  const renderStats = (data) => {
    const el = document.getElementById('visit-counter');
    if (el) {
      el.innerHTML = '<span class="vc-icon">📊</span>累计 <span class="vc-num">' + data.total + '</span> 访问 · 今日 <span class="vc-num">' + data.today + '</span>';
    }

    const ck = document.getElementById('checkin-area');
    const btn = document.querySelector('.checkin-btn');
    const checked = sessionStorage.getItem('study_checked_today') === today;

    if (ck) {
      ck.innerHTML = (checked ? '✓ ' : '') + '累计<b>' + (data.checkins_total || 0) + '</b>人打卡 · 今日<b>' + (data.checkins_today || 0) + '</b>人';
    }
    if (btn && checked) {
      btn.classList.add('checked');
      btn.textContent = '已打卡';
    }
    renderTicker(data.recent || []);
    updateHelpCounter(data);
  };

  // --- 打卡 ---
  window.doCheckin = (btn) => {
    if (sessionStorage.getItem('study_checked_today') === today) return;
    const currentUser = getUserName();
    if (!currentUser) {
      alert('请先在导航栏输入域账号，再打卡');
      document.getElementById('domain-input')?.focus();
      return;
    }
    const payload = { page, user: currentUser, fingerprint };
    apiRequest('POST', '/api/checkin', payload, (data) => {
      sessionStorage.setItem('study_checked_today', today);
      btn.classList.add('checked');
      btn.textContent = '已打卡';
      renderStats(data);
    });
  };

  // --- 协助请求 ---
  const helpKey = 'ai_train_help_requested';

  window.requestHelp = (btn) => {
    if (localStorage.getItem(helpKey) === today) return;

    const payload = { page, user: getUserName() || '', fingerprint };
    apiRequest('POST', '/api/help-request', payload, (data) => {
      localStorage.setItem(helpKey, today);
      document.querySelectorAll('.help-btn').forEach(b => {
        b.classList.add('requested');
        b.textContent = '已请求协助';
        b.disabled = true;
      });
      updateHelpCounter(data);
    });
  };

  // --- 上报访问 ---
  const reportVisit = () => {
    const payload = { page, fingerprint };
    if (userName) payload.user = userName;
    if (!sessionStorage.getItem('visit_reported')) {
      sessionStorage.setItem('visit_reported', '1');
      apiRequest('POST', '/api/stats', payload, renderStats);
    } else {
      apiRequest('GET', '/api/stats?fingerprint=' + encodeURIComponent(fingerprint), null, renderStats);
    }
  };

  // --- 注入 UI ---
  const injectUserUI = () => {
    const navRight = document.querySelector('.nav-right');
    if (!navRight) return;

    const stored = getStoredUser();
    const wrapper = Object.assign(document.createElement('span'), { id: 'user-identity' });

    if (stored) {
      wrapper.innerHTML = '<span class="user-badge" title="双击切换账号">👥 ' + escapeHTML(stored.account) + '</span>';
      wrapper.querySelector('span').addEventListener('dblclick', () => {
        if (confirm('是否切换账号？当前：' + stored.account)) {
          try {
            const users = JSON.parse(localStorage.getItem('ai_train_users') || '{}');
            delete users[fingerprint];
            localStorage.setItem('ai_train_users', JSON.stringify(users));
          } catch { /* ignore */ }
          location.reload();
        }
      });
    } else {
      wrapper.innerHTML = '<span style="display:inline-flex;align-items:center;gap:6px;">' +
        '<input id="domain-input" type="text" placeholder="域账号" class="domain-input">' +
        '<button id="domain-save" class="domain-save-btn">保存</button>' +
        '<span class="local-only-hint" title="该信息仅保存在浏览器本地（localStorage），仅在你主动点击打卡时上报，不会用于其他用途。">🔒 仅本地存储</span></span>';
    }

    const cw = navRight.querySelector('.checkin-wrapper');
    cw ? navRight.insertBefore(wrapper, cw) : navRight.appendChild(wrapper);

    const input = document.getElementById('domain-input');
    const saveBtn = document.getElementById('domain-save');
    if (input && saveBtn) {
      const doSave = () => {
        const val = input.value.trim();
        if (!val || !/^[a-zA-Z][a-zA-Z0-9._-]{1,31}$/.test(val)) {
          input.style.borderColor = '#ef4444';
          input.title = val ? '请输入有效的域账号（字母开头，2-32位）' : '';
          return;
        }
        saveUser(val);
        location.reload();
      };
      saveBtn.addEventListener('click', doSave);
      input.addEventListener('keydown', e => { if (e.key === 'Enter') doSave(); });
      input.focus();
    }
  };

  const injectHelpCounter = () => {
    const navRight = document.querySelector('.nav-right');
    if (!navRight) return;
    const counter = Object.assign(document.createElement('div'), { id: 'help-counter', className: 'help-counter', textContent: '🙋 ---' });
    const cw = navRight.querySelector('.checkin-wrapper');
    cw ? navRight.insertBefore(counter, cw) : navRight.appendChild(counter);
  };

  const injectHelpButton = () => {
    const bar = document.querySelector('.troubleshooting-bar .container');
    if (!bar) return;

    const already = localStorage.getItem(helpKey) === today;
    const div = document.createElement('div');
    div.style.cssText = 'margin-top:12px;display:flex;align-items:center;justify-content:center;gap:12px;flex-wrap:wrap;';

    const btn = Object.assign(document.createElement('button'), {
      className: 'help-btn' + (already ? ' requested' : ''),
      textContent: already ? '已请求协助' : '🙋 我需要协助',
      disabled: already
    });
    btn.onclick = () => window.requestHelp(btn);

    const hint = Object.assign(document.createElement('span'), {
      style: 'font-size:0.8rem;color:var(--gray-400);',
      textContent: '安装或配置遇到困难？点击按钮，我们会根据需求人数安排线下培训'
    });

    div.appendChild(btn);
    div.appendChild(hint);
    bar.appendChild(div);
  };

  const syncHelpButtons = () => {
    if (localStorage.getItem(helpKey) !== today) return;
    document.querySelectorAll('.help-btn').forEach(b => {
      b.classList.add('requested');
      b.textContent = '已请求协助';
      b.disabled = true;
    });
  };

  // --- 注入打卡提示条 ---
  const nav = document.querySelector('.nav');
  if (nav?.parentNode) {
    const ticker = Object.assign(document.createElement('div'), { id: 'checkin-ticker', textContent: '⏳ 打卡数据加载中...' });
    ticker.style.cssText = 'overflow:hidden;background:linear-gradient(90deg,#dbeafe,#e0e7ff,#dbeafe);border-bottom:2px solid #6366f1;padding:8px 16px;font-size:0.85rem;color:#4338ca;text-align:center;';
    nav.parentNode.insertBefore(ticker, nav.nextSibling);
  }

  // --- 初始化 ---
  let initDone = false;

  const doInit = (resolvedUser) => {
    if (initDone) return;
    initDone = true;
    if (resolvedUser) {
      saveUser(resolvedUser);
      userName = resolvedUser;
    }
    injectUserUI();
    injectHelpCounter();
    injectHelpButton();
    syncHelpButtons();
    reportVisit();
  };

  const lookupUrl = '/api/stats?fingerprint=' + encodeURIComponent(fingerprint);
  apiFetch('GET', lookupUrl)
    .then(r => r.ok ? r.json() : null)
    .then(data => doInit(data?.resolved_user || null))
    .catch(() => doInit(null));

})();

/* ============================================
   页面快速导航（浮动目录）
   ============================================ */

window.togglePageNav = function() {
  var nav = document.getElementById('page-nav');
  if (!nav) return;
  nav.classList.toggle('minimized');
  wrap.style.transform = nav.classList.contains('minimized') ? 'none' : 'translateY(-50%)';
  var btn = nav.querySelector('.page-nav-toggle');
  if (btn) btn.textContent = nav.classList.contains('minimized') ? '▶' : '−';
};

function initPageNav() {
  var sections = document.querySelectorAll('.section');
  if (sections.length < 3) return;

  var wrap = document.createElement('div');
  wrap.id = 'page-nav-wrap';
  
  // 内联定位样式，确保在任何情况下都生效
  var style = wrap.style;
  style.position = 'fixed';
  style.right = '24px';
  style.top = '50%';
  style.transform = 'translateY(-50%)';
  style.zIndex = '90';
  style.opacity = '0';
  style.pointerEvents = 'none';
  style.transition = 'opacity 0.3s';

  // 构建导航内容（避免 innerHTML 中的 class 冲突）
  var html = '<div class="page-nav" id="page-nav">';
  html += '<div class="page-nav-title">📖 快速导航<button class="page-nav-toggle" onclick="togglePageNav()" title="收起">−</button></div>';
  html += '<div class="nav-mini-icon">📖</div>';
  html += '<div id="page-nav-list"></div></div>';
  wrap.innerHTML = html;
  document.body.appendChild(wrap);

  var list = document.getElementById('page-nav-list');
  var items = [];
  var idx = 0;

  sections.forEach(function(section) {
    var label = section.querySelector('.section-label');
    var title = section.querySelector('.section-title');
    if (!label || !title) return;

    var id = 'sec-' + idx;
    section.id = id;
    idx++;

    var link = document.createElement('a');
    link.href = '#' + id;
    link.textContent = title.textContent.trim();
    link.addEventListener('click', function(e) {
      e.preventDefault();
      var target = document.getElementById(id);
      if (target) target.scrollIntoView({ behavior: 'smooth' });
    });
    list.appendChild(link);
    items.push({ el: link, section: section });
  });

  if (items.length < 2) { wrap.remove(); return; }

  // 滚动阈值
  var firstSection = sections[0];
  var showThreshold = firstSection ? firstSection.offsetTop - 100 : 100;

  var scrollHandler = function() {
    if (window.scrollY > showThreshold) {
      style.opacity = '1';
      style.pointerEvents = 'auto';
    } else {
      style.opacity = '0';
      style.pointerEvents = 'none';
    }
  };
  window.addEventListener('scroll', scrollHandler, { passive: true });
  scrollHandler();

  // 用 IntersectionObserver 高亮当前节
  try {
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (!entry.isIntersecting) return;
        var idx2 = parseInt(entry.target.id.replace('sec-', ''));
        if (isNaN(idx2)) return;
        items.forEach(function(item, i) {
          item.el.classList.toggle('active', i === idx2);
        });
      });
    }, { rootMargin: '-80px 0px -60% 0px' });
    items.forEach(function(item) { observer.observe(item.section); });
  } catch(e) {}
}
// ============================================
// 演示视频
// ============================================
window.playDemoVideo = () => {
  const container = document.getElementById('hermes-demo-video');
  if (!container) return;
  container.innerHTML = '<video controls autoplay playsinline style="width:100%;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,0.12);outline:none;"><source src="videos/演示视频.mp4" type="video/mp4">您的浏览器不支持视频播放。</video>';
};

// ============================================
// 演示模式 (Presentation Mode)
// ============================================
(function() {
  var sections = document.querySelectorAll('section.section, section.section-gray, .page-header');
  if (sections.length < 2) return;

  var overlay = document.createElement('div');
  overlay.className = 'present-overlay';
  var stage = document.createElement('div');
  stage.className = 'present-stage';

  // Welcome slide
  var welcomeSlide = document.createElement('div');
  welcomeSlide.className = 'present-slide active';
  welcomeSlide.innerHTML = '<div style="text-align:center;padding:80px 60px 60px;">' +
    '<div style="font-size:3.5rem;margin-bottom:16px;">👋</div>' +
    '<h1 style="font-size:2.2rem;font-weight:800;color:#1e293b;margin:0 0 12px;">欢迎参加 AI 赋能日常工作培训</h1>' +
    '<p style="font-size:1.1rem;color:#64748b;margin:0 0 8px;">感谢各位在百忙之中抽出时间参加本次培训</p>' +
    '<div style="width:60px;height:4px;background:linear-gradient(90deg,#2563eb,#10b981);margin:24px auto;border-radius:2px;"></div>' +
    '<div style="background:#eff6ff;border-radius:12px;padding:18px 28px;margin:20px auto;max-width:420px;text-align:left;">' +
      '<p style="font-size:0.95rem;color:#1e40af;margin:0 0 10px;font-weight:700;">📋 培训议程</p>' +
      '<p style="font-size:0.88rem;color:#475569;margin:0 0 6px;">🔹 AI工具概述与对比</p>' +
      '<p style="font-size:0.88rem;color:#475569;margin:0 0 6px;">🔹 Hermes-Agent 使用指南</p>' +
      '<p style="font-size:0.88rem;color:#475569;margin:0 0 6px;">🔹 Claude Code 开发工具</p>' +
      '<p style="font-size:0.88rem;color:#475569;margin:0 0 6px;">🔹 大模型基础知识</p>' +
      '<p style="font-size:0.88rem;color:#475569;margin:0;">🔹 API Key 申请与配置</p>' +
    '</div>' +
    '<div style="background:#fef3c7;border:2px solid #f59e0b;border-radius:12px;padding:20px 28px;margin:24px auto;max-width:420px;">' +
      '<p style="font-size:1rem;color:#b45309;margin:0 0 4px;font-weight:700;">⚠️ 请先完成签到</p>' +
      '<p style="font-size:0.88rem;color:#92400e;margin:0;">点击页面右上角「打卡」按钮完成签到</p>' +
    '</div>' +
    '<p style="font-size:0.82rem;color:#94a3b8;margin:28px 0 0;">按 → 键或点击 ▶ 开始浏览</p>' +
  '</div>';
  stage.appendChild(welcomeSlide);

  sections.forEach(function(sec, i) {
    var slide = document.createElement('div');
    slide.className = 'present-slide';
    slide.innerHTML = sec.innerHTML;
    stage.appendChild(slide);
  });
  overlay.appendChild(stage);

  var closeBtn = document.createElement('button');
  closeBtn.className = 'present-close';
  closeBtn.innerHTML = '&times;';
  overlay.appendChild(closeBtn);

  var controls = document.createElement('div');
  controls.className = 'present-controls';
  var prevBtn = document.createElement('button');
  prevBtn.className = 'present-ctrl-btn';
  prevBtn.innerHTML = '&#9664;';
  var counter = document.createElement('span');
  counter.className = 'present-counter';
  var nextBtn = document.createElement('button');
  nextBtn.className = 'present-ctrl-btn';
  nextBtn.innerHTML = '&#9654;';
  controls.appendChild(prevBtn);
  controls.appendChild(counter);
  controls.appendChild(nextBtn);
  overlay.appendChild(controls);
  document.body.appendChild(overlay);

  var idx = 0, total = sections.length + 1, active = false;

  function update() {
    var slides = stage.querySelectorAll('.present-slide');
    slides.forEach(function(s, i) { s.classList.toggle('active', i === idx); });
    counter.textContent = (idx + 1) + ' / ' + total;
    prevBtn.disabled = idx === 0;
    nextBtn.disabled = idx === total - 1;
    stage.scrollTop = 0;
  }

  function open() {
    active = true; idx = 0;
    overlay.classList.add('active');
    document.body.classList.add('presenting');
    update();
  }
  function close() {
    active = false;
    overlay.classList.remove('active');
    document.body.classList.remove('presenting');
  }
  function next() { if (idx < total - 1) { idx++; update(); } }
  function prev() { if (idx > 0) { idx--; update(); } }

  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', function(e) { if (e.target === overlay) close(); });
  nextBtn.addEventListener('click', next);
  prevBtn.addEventListener('click', prev);
  document.addEventListener('keydown', function(e) {
    if (!active) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); next(); }
    else if (e.key === 'ArrowLeft') prev();
    else if (e.key === 'Home') { idx = 0; update(); }
    else if (e.key === 'End') { idx = total - 1; update(); }
  });

  // Floating trigger
  var trigger = document.createElement('button');
  trigger.className = 'present-trigger';
  trigger.textContent = '🎬 演示模式';
  trigger.addEventListener('click', open);
  document.body.appendChild(trigger);

  // Nav trigger
  var navRight = document.querySelector('.nav-right');
  if (navRight) {
    var nb = document.createElement('button');
    nb.textContent = '🎬 演示';
    nb.style.cssText = 'background:#2563eb;color:#fff;border:none;padding:4px 12px;border-radius:16px;font-size:0.78rem;font-weight:600;cursor:pointer;margin-right:12px;';
    nb.addEventListener('click', open);
    navRight.insertBefore(nb, navRight.firstChild);
  }
})();
