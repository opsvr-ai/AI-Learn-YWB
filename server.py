"""
运维部AI学习平台 — 本地服务器
启动: python server.py    访问: http://localhost:9010
安全: 默认绑定 0.0.0.0:9010（局域网内可访问，公网请勿运行）
"""
import http.server
import json
import os
import threading
import urllib.parse

PORT = 9010
ROOT = os.path.dirname(os.path.abspath(__file__))

# ── 初始化各个子模块 ──
import modules.db as db;        db.init(ROOT)
import modules.cases as cases
import modules.token_stats as ts; ts.init(ROOT)
import modules.feedback as fb;   fb.init(os.path.join(ROOT, 'uploads'))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        try:
            p = urllib.parse.urlparse(self.path); qs = urllib.parse.parse_qs(p.query)
            # 统计 & 打卡
            if p.path == '/api/stats':
                self._json(db.get_stats(resolve_fp=qs.get('fingerprint', [None])[0])); return
            # Token 统计
            if p.path == '/api/token-stats':
                self._json(ts.get(qs.get('view', ['overview'])[0], qs)); return
            # 案例列表 / 详情
            if p.path == '/api/cases':
                vid = qs.get('view', ['list'])[0]
                if vid == 'detail':
                    self._json(cases.detail(int(qs.get('id', [0])[0])) or {'error': 'not found'})
                else: self._json(cases.list(view=vid))
                return
            # 反馈列表 / 详情
            if p.path == '/api/feedback':
                vid = qs.get('view', ['list'])[0]
                if vid == 'detail':
                    self._json(fb.detail_fb(int(qs.get('id', [0])[0])) or {'error': 'not found'})
                else: self._json(fb.list_fb())
                return
            # Range 请求（视频进度条）
            fs = self.translate_path(p.path)
            if self.headers.get('Range') and os.path.isfile(fs):
                try: self._serve_range(fs); return
                except: pass
            super().do_GET()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError): pass

    def do_POST(self):
        try:
            p = urllib.parse.urlparse(self.path); clen = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(clen) if clen else b'{}'
            data = json.loads(body) if body else {}
            fp = data.get('fingerprint', '')
            # 统计 & 打卡
            if p.path == '/api/stats':
                db.record_visit(data.get('page', '/'), user=data.get('user', ''), fingerprint=fp)
                self._json(db.get_stats(resolve_fp=fp if fp else None)); return
            if p.path == '/api/register-user':
                db.register_fingerprint(fp, data.get('account', ''))
                self._json({'ok': True, 'resolved_user': data.get('account', '')}); return
            if p.path == '/api/checkin':
                db.do_checkin(user=data.get('user', ''), fingerprint=fp)
                self._json(db.get_stats(resolve_fp=fp if fp else None)); return
            if p.path == '/api/help-request':
                db.record_help_request(user=data.get('user', ''), fingerprint=fp, page=data.get('page', ''))
                self._json(db.get_stats(resolve_fp=fp if fp else None)); return
            # 案例点赞
            if p.path == '/api/cases/like':
                likes = cases.like(data.get('case_id', 0), fp)
                self._json({'ok': True, 'likes': likes, 'has_liked': True}); return
            if p.path == '/api/cases/liked':
                self._json({'has_liked': cases.has_liked(data.get('case_id', 0), fp)}); return
            # 案例上传（multipart）
            if p.path == '/api/cases':
                ctype = self.headers.get('Content-Type', '')
                if 'multipart/form-data' in ctype:
                    fields = fb.parse_multipart(body, ctype.split('boundary=')[1])
                    title = fields.get('title', ('', b''))[1].decode()
                    desc = fields.get('description', ('', b''))[1].decode()
                    author = fields.get('author', ('', b''))[1].decode()
                    author_name = fields.get('author_name', ('', b''))[1].decode()
                    fname, fbytes = fields.get('file', ('', b''))
                    saved, ftype = '', ''
                    if fname and fbytes:
                        ftype = fname.rsplit('.', 1)[-1].lower() if '.' in fname else ''
                        saved = fb.upload_image(fbytes, fname)
                    cases.create(title, desc, saved, ftype, author, author_name)
                    self._json({'ok': True}); return
                self.send_response(400); self.end_headers(); return
            # 反馈
            if p.path == '/api/feedback':
                fb.create_fb(data.get('title', ''), data.get('content', ''), data.get('author', ''), data.get('author_name', ''), data.get('images', ''))
                self._json({'ok': True}); return
            if p.path == '/api/feedback/reply':
                fb.reply_fb(data.get('feedback_id', 0), data.get('content', ''), data.get('author', ''), data.get('author_name', ''), data.get('images', ''))
                self._json({'ok': True}); return
            if p.path == '/api/feedback/resolve':
                fb.resolve_fb(data.get('feedback_id', 0))
                self._json({'ok': True}); return
            # 图片上传
            if p.path == '/api/upload-image':
                ctype = self.headers.get('Content-Type', '')
                if 'multipart/form-data' in ctype:
                    fields = fb.parse_multipart(body, ctype.split('boundary=')[1])
                    fname, fbytes = fields.get('image', ('', b''))
                    if fname and fbytes:
                        self._json({'ok': True, 'filename': fb.upload_image(fbytes, fname)}); return
                self._json({'ok': False, 'error': 'no image'}); return
            self.send_response(405); self.end_headers()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError): pass

    def _serve_range(self, path):
        file_size = os.path.getsize(path)
        range_hdr = self.headers.get('Range', '')
        range_match = range_hdr.replace('bytes=', '').split('-')
        if range_hdr.endswith('-'): start, end = int(range_match[0]), file_size - 1
        elif range_match[0] == '': start, end = file_size - int(range_match[1]), file_size - 1
        else: start, end = int(range_match[0]), int(range_match[1])
        end = min(end, file_size - 1)
        if start >= file_size: self.send_response(416); self.send_header('Content-Range', f'bytes */{file_size}'); self.end_headers(); return
        with open(path, 'rb') as f: f.seek(start); data = f.read(end - start + 1)
        try:
            self.send_response(206); self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            self.send_header('Accept-Ranges', 'bytes'); self.send_header('Content-Length', str(len(data)))
            self.send_header('Content-Type', self.guess_type(path)); self.end_headers(); self.wfile.write(data)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError): pass

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200); self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*'); self.end_headers(); self.wfile.write(body)

    def log_message(self, format, *args):
        if '/api/' not in str(args[0] if args else ''): super().log_message(format, *args)


if __name__ == '__main__':
    print(f'\n╔══════════════════════════════════════════════╗\n║     运维部AI学习平台  v2.0                    ║\n║                                               ║'
          f'\n║     访问地址:  http://localhost:{PORT}          ║\n║     按 Ctrl+C 停止服务器                      ║\n╚══════════════════════════════════════════════╝\n')
    http.server.ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
