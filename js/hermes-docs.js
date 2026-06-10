/* Hermes Docs page interactions */
(function() {
  var toggle = document.getElementById('sidebar-toggle');
  var page = document.querySelector('.docs-page');
  if (toggle && page) {
    toggle.addEventListener('click', function() {
      page.classList.toggle('open-sidebar');
    });
  }
})();

/* 侧边栏滚动到当前页 — 导航后自动定位到活动链接 */
(function() {
  var sidebar = document.querySelector('.docs-sidebar');
  var active = document.querySelector('#sidebar-nav a.active');
  if (sidebar && active) {
    function scrollToActive() {
      var sbRect = sidebar.getBoundingClientRect();
      var linkRect = active.getBoundingClientRect();
      // 计算将活动链接居中到侧边栏所需的 scrollTop
      var delta = (linkRect.top - sbRect.top) - sbRect.height / 2 + linkRect.height / 2;
      sidebar.scrollTop = Math.max(0, sidebar.scrollTop + delta);
    }
    // 立即执行 + 延迟重试等待布局稳定
    scrollToActive();
    setTimeout(scrollToActive, 100);
    setTimeout(scrollToActive, 300);
  }
})();

function filterSidebar() {
  var input = document.getElementById('sidebar-search-input');
  var q = (input.value || '').toLowerCase();
  var items = document.querySelectorAll('.sidebar-menu .sidebar-category');
  items.forEach(function(cat) {
    var links = cat.querySelectorAll('a');
    var found = false;
    links.forEach(function(a) {
      if (a.textContent.toLowerCase().indexOf(q) !== -1) {
        found = true;
        a.style.display = 'flex';
      } else {
        a.style.display = 'none';
      }
    });
    cat.style.display = found || !q ? '' : 'none';
  });
}

function copyDocCode(btn) {
  var block = btn.parentElement;
  var text = block.innerText.replace(/^copy\n?/, '');
  navigator.clipboard.writeText(text).then(function() {
    btn.textContent = 'OK';
    btn.classList.add('copied');
    setTimeout(function() {
      btn.textContent = 'copy';
      btn.classList.remove('copied');
    }, 2000);
  });
}
