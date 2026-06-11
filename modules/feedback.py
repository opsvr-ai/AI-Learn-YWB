"""问题反馈 — CRUD + 图片上传"""
import os, uuid
import modules.db as db

UPLOAD_DIR = None

def init(upload_dir):
    global UPLOAD_DIR
    UPLOAD_DIR = upload_dir
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def upload_image(file_bytes, orig_name):
    ext = orig_name.rsplit('.', 1)[-1].lower() if '.' in orig_name else 'png'
    if ext not in ('png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'): ext = 'png'
    fname = uuid.uuid4().hex[:12] + '.' + ext
    with open(os.path.join(UPLOAD_DIR, fname), 'wb') as f: f.write(file_bytes)
    return fname

def list_fb():
    conn = db.get_db()
    cur = conn.execute("""SELECT f.id, f.title, f.content, f.author, f.author_name, f.images, f.status, f.created_at,
                           (SELECT COUNT(*) FROM feedback_replies WHERE feedback_id = f.id) as reply_count
                        FROM feedback f ORDER BY f.created_at DESC""")
    rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
    conn.close(); return rows

def detail_fb(fb_id):
    conn = db.get_db()
    cur = conn.execute('SELECT id, title, content, author, author_name, images, status, created_at FROM feedback WHERE id = ?', (fb_id,))
    row = cur.fetchone()
    if not row: conn.close(); return None
    fb = dict(zip([d[0] for d in cur.description], row))
    cur = conn.execute('SELECT id, content, author, author_name, images, created_at FROM feedback_replies WHERE feedback_id = ? ORDER BY created_at', (fb_id,))
    fb['replies'] = [dict(zip(['id','content','author','author_name','images','created_at'], r)) for r in cur.fetchall()]
    conn.close(); return fb

def create_fb(title, content, author, author_name, images=''):
    conn = db.get_db()
    conn.execute('INSERT INTO feedback (title, content, author, author_name, images) VALUES (?,?,?,?,?)',
                 (title, content, author, author_name, images))
    conn.commit(); conn.close()

def reply_fb(fb_id, content, author, author_name, images=''):
    conn = db.get_db()
    conn.execute('INSERT INTO feedback_replies (feedback_id, content, author, author_name, images) VALUES (?,?,?,?,?)',
                 (fb_id, content, author, author_name, images))
    conn.commit(); conn.close()

def resolve_fb(fb_id):
    conn = db.get_db()
    conn.execute("UPDATE feedback SET status = 'resolved' WHERE id = ?", (fb_id,))
    conn.commit(); conn.close()

def parse_multipart(data, boundary):
    boundary = boundary.encode(); result = {}
    for part in data.split(b'--' + boundary):
        if b'\r\n\r\n' not in part: continue
        header, _, body = part.partition(b'\r\n\r\n'); body = body.rstrip(b'\r\n')
        headers = header.decode(errors='replace')
        if 'name="' not in headers: continue
        name_m = headers.split('name="')[1].split('"')[0] if 'name="' in headers else ''
        filename = headers.split('filename="')[1].split('"')[0] if 'filename="' in headers else ''
        result[name_m] = (filename, body)
    return result
