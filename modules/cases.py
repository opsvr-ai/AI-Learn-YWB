"""案例分享 — CRUD + 点赞"""
import modules.db as db

def list(view='latest'):
    conn = db.get_db()
    order = 'created_at DESC' if view == 'latest' else 'likes DESC'
    cur = conn.execute(f'SELECT id, title, description, file_path, file_type, author, author_name, likes, created_at FROM cases ORDER BY {order}')
    rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
    conn.close(); return rows

def detail(case_id):
    conn = db.get_db()
    cur = conn.execute('SELECT id, title, description, file_path, file_type, author, author_name, likes, created_at FROM cases WHERE id = ?', (case_id,))
    row = cur.fetchone()
    if not row: conn.close(); return None
    result = dict(zip([d[0] for d in cur.description], row))
    conn.close(); return result

def like(case_id, fingerprint):
    conn = db.get_db()
    try:
        conn.execute('INSERT OR IGNORE INTO case_likes (case_id, fingerprint) VALUES (?, ?)', (case_id, fingerprint))
        likes = conn.execute('SELECT COUNT(*) FROM case_likes WHERE case_id = ?', (case_id,)).fetchone()[0]
        conn.execute('UPDATE cases SET likes = ? WHERE id = ?', (likes, case_id)); conn.commit()
    finally: conn.close()
    return likes

def has_liked(case_id, fingerprint):
    conn = db.get_db()
    result = conn.execute('SELECT COUNT(*) FROM case_likes WHERE case_id = ? AND fingerprint = ?', (case_id, fingerprint)).fetchone()[0] > 0
    conn.close(); return result

def create(title, description, file_path, file_type, author, author_name):
    conn = db.get_db()
    conn.execute('INSERT INTO cases (title, description, file_path, file_type, author, author_name) VALUES (?,?,?,?,?,?)',
                 (title, description, file_path, file_type, author, author_name))
    conn.commit(); conn.close()
