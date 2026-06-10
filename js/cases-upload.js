/* ============================================
   案例页面 - 图片上传 & 粘贴支持
   ============================================ */
'use strict';

var caseImages = [];

function uploadImg(file, cb) {
  var fd = new FormData();
  fd.append('image', file);
  var x = new XMLHttpRequest();
  x.open('POST', '/api/upload-image');
  x.onload = function() { try { cb(JSON.parse(x.responseText)); } catch(e) { cb(null); } };
  x.onerror = function() { cb(null); };
  x.send(fd);
}

function renderCasePreviews() {
  var el = document.getElementById('case-img-preview');
  if (!el) return;
  el.innerHTML = caseImages.map(function(f, i) {
    return '<span class="img-preview-wrap">' + f +
      '<span class="del-btn" onclick="delCaseImage(' + i + ')">&#10005;</span></span>';
  }).join('');
}

function addCaseImage(file) {
  uploadImg(file, function(r) {
    if (r && r.ok) {
      caseImages.push(r.filename);
      renderCasePreviews();
    }
  });
}

function delCaseImage(idx) {
  caseImages.splice(idx, 1);
  renderCasePreviews();
}

function setupCasePaste() {
  var el = document.getElementById('case-desc');
  if (!el) return;
  el.addEventListener('paste', function(e) {
    var items = (e.clipboardData || e.originalEvent.clipboardData).items;
    for (var i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        addCaseImage(items[i].getAsFile());
      }
    }
  });
}

// 文件选择触发
document.addEventListener('DOMContentLoaded', function() {
  var fileInput = document.getElementById('case-file');
  if (fileInput) {
    fileInput.addEventListener('change', function() {
      for (var i = 0; i < this.files.length; i++) {
        if (this.files[i].type.indexOf('image') !== -1) {
          addCaseImage(this.files[i]);
        }
      }
      this.value = '';
    });
  }
  setupCasePaste();
});

function renderCaseDetail(c) {
  var html = '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;"><div class="card-icon" style="background:' + (c.catStyle||"") + '">' + (c.catIcon||"") + '</div><div><h3 style="margin:0;">' + esc(c.title) + '</h3><p style="margin:4px 0 0;color:var(--gray-400);font-size:0.8rem;">&#128100; ' + esc(c.author) + ' &middot; &#128197; ' + (c.date||"") + '</p></div></div>';
  if (c.desc) html += '<div style="color:var(--gray-700);line-height:1.7;font-size:0.95rem;">' + esc(c.desc).replace(/\n/g,"<br>") + '</div>';
  if (c.images) {
    var imgs = c.images.split(",").filter(Boolean);
    if (imgs.length) {
      html += '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;margin-bottom:8px;">';
      for (var i = 0; i < imgs.length; i++) {
        html += '<img src="uploads/' + imgs[i].trim() + '" alt="" loading="lazy" style="max-width:280px;max-height:200px;border-radius:var(--radius);border:1px solid var(--gray-100);cursor:pointer;object-fit:cover;transition:opacity .2s" onclick="var lb=document.getElementById(\"case-lb\");if(!lb){lb=document.createElement(\"div\");lb.id=\"case-lb\";lb.style.cssText=\"position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.85);z-index:300;display:flex;justify-content:center;align-items:center;cursor:pointer\";var lbi=document.createElement(\"img\");lbi.style.cssText=\"max-width:90vw;max-height:90vh;border-radius:var(--radius)\";lb.appendChild(lbi);lb.onclick=function(){this.remove()};document.body.appendChild(lb)}document.getElementById(\"case-lb\").querySelector(\"img\").src=this.src">';
      }
      html += '</div>';
    }
  }
  if (c.filePath && c.fileType) {
    var url = "uploads/" + encodeURIComponent(c.filePath);
    if (c.fileType === "html") {
      html += "<div class=\"detail-preview\"><iframe src=\"" + escAttr(url) + "\"></iframe></div>";
    } else if (["jpg","jpeg","png","gif"].indexOf(c.fileType) >= 0) {
      html += "<div class=\"detail-preview\"><img src=\"" + escAttr(url) + "\" alt=\"\" loading=\"lazy\"></div>";
    } else {
      html += "<p style=\"margin-top:12px;\"><a href=\"" + escAttr(url) + "\" download class=\"btn btn-outline btn-sm\">&#128229; \u4E0B\u8F7D\u9644\u4EF6 (." + esc(c.fileType) + ")</a></p>";
    }
  }
  return html;
}