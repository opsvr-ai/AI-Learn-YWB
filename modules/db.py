"""数据库 — SQLite 初始化 / 自动迁移 / 统计 / 打卡"""
import sqlite3, os, threading, time
from datetime import date

DB_PATH = None
ROOT = None

def init(root):
    global DB_PATH, ROOT
    ROOT = root
    DB_PATH = os.path.join(ROOT, '.visit_stats.db')

_init_done = False
_migrated = False
_lock = threading.Lock()

def init_db():
    global _init_done
    if _init_done: return
    with _lock:
        if _init_done: return
        conn = sqlite3.connect(DB_PATH); conn.execute('PRAGMA journal_mode=WAL')
        for sql in _TABLES_SQL:
            conn.execute(sql)
        conn.commit(); conn.close()
        _init_done = True

def auto_migrate():
    global _migrated
    if _migrated: return
    _migrated = True
    if not os.path.exists(DB_PATH): return
    conn = sqlite3.connect(DB_PATH); conn.execute('PRAGMA journal_mode=WAL')
    # 补齐缺失表（全在 _TABLES_SQL 里，"CREATE TABLE IF NOT EXISTS" 保证了幂等）
    for sql in _TABLES_SQL:
        try: conn.execute(sql)
        except: pass
    # 补齐缺失列
    for table, cols in [
        ('visits',           ['user TEXT', 'fingerprint TEXT']),
        ('checkins',         ['user TEXT', 'fingerprint TEXT']),
        ('feedback',         ["images TEXT DEFAULT ''"]),
        ('feedback_replies', ["images TEXT DEFAULT ''"]),
    ]:
        for spec in cols:
            try: conn.execute(f'ALTER TABLE {table} ADD COLUMN {spec}')
            except sqlite3.OperationalError: pass
    conn.commit(); conn.close()
    print("[Token统计] auto_migrate：数据库升级检查完成")

def get_db():
    init_db(); auto_migrate()
    return sqlite3.connect(DB_PATH)

# ── SQL ──
_TABLES_SQL = [
    'CREATE TABLE IF NOT EXISTS visits (id INTEGER PRIMARY KEY AUTOINCREMENT, page TEXT NOT NULL, visit_date TEXT NOT NULL, user TEXT DEFAULT "", fingerprint TEXT DEFAULT "", created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
    'CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(visit_date)',
    'CREATE TABLE IF NOT EXISTS checkins (id INTEGER PRIMARY KEY AUTOINCREMENT, checkin_date TEXT NOT NULL, user TEXT DEFAULT "", fingerprint TEXT DEFAULT "", created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
    'CREATE INDEX IF NOT EXISTS idx_checkins_date ON checkins(checkin_date)',
    'CREATE TABLE IF NOT EXISTS help_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, request_date TEXT NOT NULL, user TEXT DEFAULT "", fingerprint TEXT DEFAULT "", page TEXT DEFAULT "", created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
    'CREATE INDEX IF NOT EXISTS idx_help_date ON help_requests(request_date)',
    'CREATE TABLE IF NOT EXISTS user_fingerprints (fingerprint TEXT PRIMARY KEY, account TEXT NOT NULL, updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
    'CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT DEFAULT "", file_path TEXT DEFAULT "", file_type TEXT DEFAULT "", author TEXT NOT NULL, author_name TEXT DEFAULT "", likes INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
    'CREATE TABLE IF NOT EXISTS case_likes (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, fingerprint TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(case_id, fingerprint))',
    'CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT DEFAULT "", images TEXT DEFAULT "", author TEXT NOT NULL, author_name TEXT DEFAULT "", status TEXT DEFAULT "open", created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
    'CREATE TABLE IF NOT EXISTS feedback_replies (id INTEGER PRIMARY KEY AUTOINCREMENT, feedback_id INTEGER NOT NULL, content TEXT NOT NULL, images TEXT DEFAULT "", author TEXT NOT NULL, author_name TEXT DEFAULT "", created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
]

_CASES = '''CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT DEFAULT '', file_path TEXT DEFAULT '', file_type TEXT DEFAULT '', author TEXT NOT NULL, author_name TEXT DEFAULT '', likes INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''
_CASE_LIKES = '''CREATE TABLE IF NOT EXISTS case_likes (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, fingerprint TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(case_id, fingerprint))'''
_FEEDBACK = '''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT DEFAULT '', images TEXT DEFAULT '', author TEXT NOT NULL, author_name TEXT DEFAULT '', status TEXT DEFAULT 'open', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''
_FEEDBACK_REPLIES = '''CREATE TABLE IF NOT EXISTS feedback_replies (id INTEGER PRIMARY KEY AUTOINCREMENT, feedback_id INTEGER NOT NULL, content TEXT NOT NULL, images TEXT DEFAULT '', author TEXT NOT NULL, author_name TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''

_CASES = '''CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT DEFAULT '', file_path TEXT DEFAULT '', file_type TEXT DEFAULT '', author TEXT NOT NULL, author_name TEXT DEFAULT '', likes INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''
_CASE_LIKES = '''CREATE TABLE IF NOT EXISTS case_likes (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL, fingerprint TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(case_id, fingerprint))'''
_FEEDBACK = '''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT DEFAULT '', images TEXT DEFAULT '', author TEXT NOT NULL, author_name TEXT DEFAULT '', status TEXT DEFAULT 'open', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''
_FEEDBACK_REPLIES = '''CREATE TABLE IF NOT EXISTS feedback_replies (id INTEGER PRIMARY KEY AUTOINCREMENT, feedback_id INTEGER NOT NULL, content TEXT NOT NULL, images TEXT DEFAULT '', author TEXT NOT NULL, author_name TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''

# ── 业务 API ──
def lookup_fingerprint(fp):
    if not fp: return None
    conn = get_db()
    row = conn.execute('SELECT account FROM user_fingerprints WHERE fingerprint = ?', (fp,)).fetchone()
    conn.close()
    return row[0] if row else None

def register_fingerprint(fp, account):
    if not fp or not account: return
    conn = get_db()
    conn.execute('INSERT OR REPLACE INTO user_fingerprints (fingerprint, account, updated) VALUES (?, ?, CURRENT_TIMESTAMP)', (fp, account))
    conn.commit(); conn.close()

def get_stats(resolve_fp=None):
    today = date.today().isoformat(); conn = get_db()
    cur = conn.execute('SELECT COUNT(*) FROM visits'); total = cur.fetchone()[0]
    cur = conn.execute('SELECT COUNT(*) FROM visits WHERE visit_date = ?', (today,)); today_count = cur.fetchone()[0]
    cur = conn.execute('SELECT COUNT(*) FROM checkins'); total_ck = cur.fetchone()[0]
    cur = conn.execute('SELECT COUNT(*) FROM checkins WHERE checkin_date = ?', (today,)); today_ck = cur.fetchone()[0]
    cur = conn.execute("SELECT DISTINCT user FROM checkins WHERE checkin_date = ? AND user != '' ORDER BY created_at DESC", (today,)); recent = [r[0] for r in cur.fetchall()]
    cur = conn.execute('SELECT COUNT(*) FROM help_requests'); help_total = cur.fetchone()[0]
    cur = conn.execute('SELECT COUNT(*) FROM help_requests WHERE request_date = ?', (today,)); help_today = cur.fetchone()[0]
    cur = conn.execute('SELECT COUNT(DISTINCT account) FROM user_fingerprints'); registered_users = cur.fetchone()[0]
    resolved = lookup_fingerprint(resolve_fp) if resolve_fp else None
    conn.close()
    return {'total': total, 'today': today_count, 'checkins_total': total_ck, 'checkins_today': today_ck,
            'help_total': help_total, 'help_today': help_today, 'registered_users': registered_users,
            'recent': recent, 'resolved_user': resolved}

def record_visit(page, user='', fingerprint=''):
    today = date.today().isoformat(); conn = get_db()
    conn.execute('INSERT INTO visits (page, visit_date, user, fingerprint) VALUES (?, ?, ?, ?)', (page, today, user, fingerprint))
    conn.commit(); conn.close()
    if fingerprint and user: register_fingerprint(fingerprint, user)

def do_checkin(user='', fingerprint=''):
    today = date.today().isoformat(); conn = get_db()
    conn.execute('INSERT INTO checkins (checkin_date, user, fingerprint) VALUES (?, ?, ?)', (today, user, fingerprint))
    conn.commit(); conn.close()
    register_fingerprint(fingerprint, user)

def record_help_request(user='', fingerprint='', page=''):
    today = date.today().isoformat(); conn = get_db()
    if fingerprint:
        if conn.execute('SELECT COUNT(*) FROM help_requests WHERE request_date = ? AND fingerprint = ?', (today, fingerprint)).fetchone()[0] > 0:
            conn.close(); return
    conn.execute('INSERT INTO help_requests (request_date, user, fingerprint, page) VALUES (?, ?, ?, ?)', (today, user, fingerprint, page))
    conn.commit(); conn.close()
    if fingerprint and user: register_fingerprint(fingerprint, user)
