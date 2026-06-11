"""
AI赋能日常工作 — 本地静态服务器 + 访问统计
启动方式: python server.py
访问地址: http://localhost:8080

零第三方依赖，Python 3 内置库即可运行。

安全说明：
- 默认绑定 0.0.0.0:8080（所有网卡），局域网内设备均可访问。这是有意为之，便于部门内部通过局域网分享培训站点。
- 若仅需本机访问，将 server_address 改为 ('127.0.0.1', PORT)。
- 此服务器仅用于内部培训，请勿在公网环境运行。
- .visit_stats.db 包含打卡记录（域账号 + 浏览器指纹），注意保护隐私数据。
- packages/settings.json 中的 API Token 已替换为占位符，不含真实密钥。
"""
import http.server
import sqlite3
import json
import os
import socket
import threading
import time
import traceback
import uuid
import urllib.parse
from datetime import date

PORT = 9010
ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, '.visit_stats.db')
UPLOAD_DIR = os.path.join(ROOT, 'uploads')

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── 数据库初始化 + 自动迁移 ────────────────────────────
_DB_INITIALIZED = False
_DB_MIGRATED   = False
_DB_LOCK = threading.Lock()

def init_db():
    """建表 + WAL，仅执行一次"""
    global _DB_INITIALIZED
    if _DB_INITIALIZED:
        return
    with _DB_LOCK:
        if _DB_INITIALIZED:
            return
        conn = sqlite3.connect(DB_PATH)
        conn.execute('PRAGMA journal_mode=WAL')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, page TEXT NOT NULL,
                visit_date TEXT NOT NULL, user TEXT DEFAULT '',
                fingerprint TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(visit_date)''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT, checkin_date TEXT NOT NULL,
                user TEXT DEFAULT '', fingerprint TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_checkins_date ON checkins(checkin_date)''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS help_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT, request_date TEXT NOT NULL,
                user TEXT DEFAULT '', fingerprint TEXT DEFAULT '',
                page TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''CREATE INDEX IF NOT EXISTS idx_help_date ON help_requests(request_date)''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_fingerprints (
                fingerprint TEXT PRIMARY KEY, account TEXT NOT NULL,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
                description TEXT DEFAULT '', file_path TEXT DEFAULT '',
                file_type TEXT DEFAULT '', author TEXT NOT NULL,
                author_name TEXT DEFAULT '', likes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS case_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL,
                fingerprint TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(case_id, fingerprint)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
                content TEXT DEFAULT '', images TEXT DEFAULT '',
                author TEXT NOT NULL, author_name TEXT DEFAULT '',
                status TEXT DEFAULT 'open', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT, feedback_id INTEGER NOT NULL,
                content TEXT NOT NULL, images TEXT DEFAULT '',
                author TEXT NOT NULL, author_name TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        _DB_INITIALIZED = True


def auto_migrate():
    """每次服务器启动时执行一次——补齐旧 DB 可能缺失的表和列"""
    global _DB_MIGRATED
    if _DB_MIGRATED:
        return
    _DB_MIGRATED = True

    # 如果 db 文件还不存在，等 init_db() 先创建
    if not os.path.exists(DB_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')

    # ── 补齐可能缺失的表（生产环境旧 DB 升级时自动创建）──
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            description TEXT DEFAULT '', file_path TEXT DEFAULT '',
            file_type TEXT DEFAULT '', author TEXT NOT NULL,
            author_name TEXT DEFAULT '', likes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS case_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL,
            fingerprint TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(case_id, fingerprint)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            content TEXT DEFAULT '', images TEXT DEFAULT '',
            author TEXT NOT NULL, author_name TEXT DEFAULT '',
            status TEXT DEFAULT 'open', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS feedback_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT, feedback_id INTEGER NOT NULL,
            content TEXT NOT NULL, images TEXT DEFAULT '',
            author TEXT NOT NULL, author_name TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── 补齐可能缺失的列 ──
    for table, cols in [
        ('visits',           [('user', 'TEXT'), ('fingerprint', 'TEXT')]),
        ('checkins',         [('user', 'TEXT'), ('fingerprint', 'TEXT')]),
        ('feedback',         [('images', "TEXT DEFAULT ''")]),
        ('feedback_replies', [('images', "TEXT DEFAULT ''")]),
    ]:
        for col_spec in cols:
            try:
                if isinstance(col_spec, tuple):
                    conn.execute(f'ALTER TABLE {table} ADD COLUMN {col_spec[0]} {col_spec[1]}')
                else:
                    conn.execute(f'ALTER TABLE {table} ADD COLUMN {col_spec}')
            except sqlite3.OperationalError:
                pass  # 列已存在 → 静默跳过

    conn.commit()
    conn.close()
    print(f"[Token统计] auto_migrate：数据库升级检查完成")


def get_db():
    """获取数据库连接（自动建表 + 升级）"""
    init_db()
    auto_migrate()
    return sqlite3.connect(DB_PATH)


def lookup_fingerprint(fp):
    """返回指纹绑定的域账号，未绑定时返回 None"""
    if not fp:
        return None
    conn = get_db()
    cur = conn.execute('SELECT account FROM user_fingerprints WHERE fingerprint = ?', (fp,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def register_fingerprint(fp, account):
    """绑定浏览器指纹到域账号（INSERT OR REPLACE）"""
    if not fp or not account:
        return
    conn = get_db()
    conn.execute(
        'INSERT OR REPLACE INTO user_fingerprints (fingerprint, account, updated) VALUES (?, ?, CURRENT_TIMESTAMP)',
        (fp, account))
    conn.commit()
    conn.close()


def get_stats(resolve_fp=None):
    today = date.today().isoformat()
    conn = get_db()
    cur = conn.execute('SELECT COUNT(*) FROM visits')
    total = cur.fetchone()[0]
    cur = conn.execute('SELECT COUNT(*) FROM visits WHERE visit_date = ?', (today,))
    today_count = cur.fetchone()[0]
    cur = conn.execute('SELECT COUNT(*) FROM checkins')
    total_ck = cur.fetchone()[0]
    cur = conn.execute('SELECT COUNT(*) FROM checkins WHERE checkin_date = ?', (today,))
    today_ck = cur.fetchone()[0]
    # 今日打卡用户列表（去重）
    cur = conn.execute(
        'SELECT DISTINCT user FROM checkins WHERE checkin_date = ? AND user != \'\' ORDER BY created_at DESC',
        (today,))
    recent = [r[0] for r in cur.fetchall()]
    cur = conn.execute('SELECT COUNT(*) FROM help_requests')
    help_total = cur.fetchone()[0]
    cur = conn.execute('SELECT COUNT(*) FROM help_requests WHERE request_date = ?', (today,))
    help_today = cur.fetchone()[0]

    # 已注册的指纹→账号绑定数（去重账号）
    cur = conn.execute('SELECT COUNT(DISTINCT account) FROM user_fingerprints')
    registered_users = cur.fetchone()[0]

    resolved_user = lookup_fingerprint(resolve_fp) if resolve_fp else None

    conn.close()
    return {'total': total, 'today': today_count,
            'checkins_total': total_ck, 'checkins_today': today_ck,
            'help_total': help_total, 'help_today': help_today,
            'registered_users': registered_users,
            'recent': recent,
            'resolved_user': resolved_user}


def record_visit(page, user='', fingerprint=''):
    today = date.today().isoformat()
    conn = get_db()
    conn.execute('INSERT INTO visits (page, visit_date, user, fingerprint) VALUES (?, ?, ?, ?)',
                 (page, today, user, fingerprint))
    conn.commit()
    conn.close()
    if fingerprint and user:
        register_fingerprint(fingerprint, user)


def do_checkin(user='', fingerprint=''):
    today = date.today().isoformat()
    conn = get_db()
    conn.execute('INSERT INTO checkins (checkin_date, user, fingerprint) VALUES (?, ?, ?)',
                 (today, user, fingerprint))
    conn.commit()
    conn.close()
    # 打卡时同时注册指纹→账号绑定
    register_fingerprint(fingerprint, user)


def record_help_request(user='', fingerprint='', page=''):
    today = date.today().isoformat()
    conn = get_db()
    if fingerprint:
        cur = conn.execute(
            'SELECT COUNT(*) FROM help_requests WHERE request_date = ? AND fingerprint = ?',
            (today, fingerprint))
        if cur.fetchone()[0] > 0:
            conn.close()
            return
    conn.execute(
        'INSERT INTO help_requests (request_date, user, fingerprint, page) VALUES (?, ?, ?, ?)',
        (today, user, fingerprint, page))
    conn.commit()
    conn.close()
    if fingerprint and user:
        register_fingerprint(fingerprint, user)


# ═══════════════════════════════════════════════════════════
#  Token 消耗统计模块（方案 B：pymysql 查库 + JSON 兜底）
# ═══════════════════════════════════════════════════════════

# ── pymysql 可选导入 ──
try:
    import pymysql
    _HAS_PYMYSQL = True
except ImportError:
    _HAS_PYMYSQL = False

# ── AI Gateway 数据库配置 ──
AIGW_DB_CONFIG = {
    'host': '7.22.1.162',
    'port': 3306,
    'user': 'llmdbappusr',
    'password': 'pP1<zW1+',
    'database': 'ai_gateway',
    'charset': 'utf8mb4',
    'connect_timeout': 10,
    'read_timeout': 60
}

def _db_connect():
    """连接 MySQL 并启用 TCP keepalive 防止防火墙断连"""
    conn = pymysql.connect(**AIGW_DB_CONFIG)
    sock = conn.socket
    if sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if hasattr(socket, 'TCP_KEEPIDLE'):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
        if hasattr(socket, 'TCP_KEEPINTVL'):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
        if hasattr(socket, 'TCP_KEEPCNT'):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
    conn.cursor().execute("SET SESSION wait_timeout = 600")
    conn.commit()
    return conn

TOKEN_CACHE_TTL = 300  # 缓存 5 分钟

_token_cache_lock = threading.Lock()
_token_cache = {"data": None, "ts": 0, "source": ""}


# ── 人员组织结构加载 ──
def _load_org_structure():
    """从 ywb-users.csv 加载中心→小组→(姓名,账号) 组织树"""
    org = {}
    acc_lookup = {}

    csv_path = os.path.join(ROOT, 'ywb-users.csv')
    if not os.path.exists(csv_path):
        print(f"[Token统计] ywb-users.csv 不存在: {csv_path}")
        return org, acc_lookup

    try:
        import csv
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # 跳过表头
            for row in reader:
                if len(row) < 6:
                    continue
                name    = (row[1] or '').strip()
                account = (row[2] or '').strip()
                center  = (row[3] or '').strip()
                group   = (row[4] or '').strip()
                if not account:
                    continue
                org.setdefault(center, {})
                org[center].setdefault(group, [])
                org[center][group].append((name, account))
                acc_lookup[account] = {"name": name, "center": center, "group": group}
        print(f"[Token统计] ywb-users.csv 加载完成: {len(org)} 个中心, {len(acc_lookup)} 人")
        return org, acc_lookup
    except Exception as e:
        print(f"[Token统计] ywb-users.csv 加载失败: {e}")
        return org, acc_lookup


_org_tree, _org_account_map = _load_org_structure()


def _extract_username(ai_consumer):
    """从 ai_consumer 中提取用户名（前缀匹配）"""
    if '_' in ai_consumer:
        return ai_consumer.split('_')[0]
    return ai_consumer


def _fetch_db_token_data(month):
    """从 ai_gateway 聚合查询指定月份的 Token 数据"""
    if not _HAS_PYMYSQL:
        print("[Token统计] pymysql 未安装，跳过 DB 查询，走兜底")
        return None
    y, m = map(int, month.split('-'))
    start_ts = f"{y:04d}-{m:02d}-01 00:00:00"
    if m == 12:
        end_ts = f"{y+1:04d}-01-01 00:00:00"
    else:
        end_ts = f"{y:04d}-{m+1:02d}-01 00:00:00"

    print(f"[Token统计] 开始查询 ai_gateway: month={month}, time_bucket [{start_ts}, {end_ts})", flush=True)
    try:
        conn = _db_connect()
        t0 = time.time()
        cursor = conn.cursor()  # 默认 buffered cursor，一次性传输聚合结果（比 SSCursor 快得多）
        cursor.execute("""
            SELECT ai_consumer,
                   COALESCE(SUM(input_tokens), 0) as input_tokens,
                   COALESCE(SUM(output_tokens), 0) as output_tokens,
                   COALESCE(SUM(request_count), 0) as request_count
            FROM ai_metrics
            WHERE time_bucket >= %s AND time_bucket < %s
            GROUP BY ai_consumer
        """, (start_ts, end_ts))
        elapsed = time.time() - t0
        print(f"[Token统计] SQL 执行完成，耗时 {elapsed:.1f}s，开始读取结果...", flush=True)

        consumers = {}
        row_count = 0
        for ai_consumer, inp, out, req in cursor.fetchall():
            row_count += 1
            username = _extract_username(ai_consumer)
            if username not in consumers:
                consumers[username] = {"input_tokens": 0, "output_tokens": 0, "request_count": 0}
            consumers[username]["input_tokens"] += inp
            consumers[username]["output_tokens"] += out
            consumers[username]["request_count"] += req

        cursor.close()
        conn.close()
        print(f"[Token统计] DB 查询成功: {row_count} 条记录, {len(consumers)} 个去重用户", flush=True)
        return consumers
    except Exception as e:
        print(f"[Token统计] DB 查询失败: {e}", flush=True)
        traceback.print_exc()
        return None


def _load_json_fallback():
    """从本地 report_data.json 加载作为兜底数据"""
    json_path = os.path.join(ROOT, 'report_data.json')
    if not os.path.exists(json_path):
        print(f"[Token统计] report_data.json 不存在: {json_path}")
        return None
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[Token统计] report_data.json 加载成功: centers={len(data.get('centers',{}))}")
        return data
    except Exception as e:
        print(f"[Token统计] report_data.json 解析失败: {e}")
        return None


def _build_token_result(month):
    """构建标准化的 Token 统计结果"""
    print(f"[Token统计] _build_token_result() month={month}, org_users={len(_org_account_map)}", flush=True)

    # 尝试查库
    db_data = _fetch_db_token_data(month)
    source = "db"

    if db_data is not None:
        print(f"[Token统计] 使用 DB 数据构建，匹配组织树...", flush=True)
        # 用 DB 数据 + 组织树构建结果
        matched = 0
        flat_users = []
        for account, info in _org_account_map.items():
            usage = db_data.get(account, {"input_tokens": 0, "output_tokens": 0, "request_count": 0})
            total = usage["input_tokens"] + usage["output_tokens"]
            if total > 0:
                matched += 1
            flat_users.append({
                "account": account,
                "name": info["name"],
                "center": info["center"],
                "group": info["group"],
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "request_count": usage["request_count"],
                "total_tokens": total,
                "has_usage": total > 0
            })
        print(f"[Token统计] 组织树匹配完成: {len(flat_users)} 人, 有用量 {matched} 人", flush=True)
    else:
        # 兜底：从 report_data.json 构建
        print(f"[Token统计] DB 数据不可用，尝试 JSON 兜底...")
        fallback = _load_json_fallback()
        if fallback is None:
            print(f"[Token统计] JSON 兜底也不可用，返回 None")
            return None
        source = "json"
        flat_users = []
        acc_index = {}
        for cname, cdata in fallback.get("centers", {}).items():
            for gname, gdata in cdata.get("groups", {}).items():
                for u in gdata.get("users", []):
                    username = u.get("username", "")
                    if not username or username == "合计":
                        continue
                    total = u.get("total_tokens", 0)
                    flat_users.append({
                        "account": username,
                        "name": u.get("name", ""),
                        "center": cname,
                        "group": gname,
                        "input_tokens": u.get("input_tokens", 0),
                        "output_tokens": u.get("output_tokens", 0),
                        "request_count": u.get("request_count", 0),
                        "total_tokens": total,
                        "has_usage": total > 0
                    })
        print(f"[Token统计] JSON 兜底构建完成: {len(flat_users)} 人")

    if not flat_users:
        return None

    # 排序
    flat_users.sort(key=lambda x: x["total_tokens"], reverse=True)

    # 统计
    total_users = len(flat_users)
    active_users = [u for u in flat_users if u["has_usage"]]
    active_count = len(active_users)
    total_all = sum(u["total_tokens"] for u in flat_users)
    total_input = sum(u["input_tokens"] for u in flat_users)
    total_output = sum(u["output_tokens"] for u in flat_users)

    # 中心统计
    center_stats = {}
    for u in flat_users:
        c = u["center"] or "其他"
        if c not in center_stats:
            center_stats[c] = {"total_tokens": 0, "user_count": 0, "active_count": 0, "groups": {}}
        center_stats[c]["total_tokens"] += u["total_tokens"]
        center_stats[c]["user_count"] += 1
        if u["has_usage"]:
            center_stats[c]["active_count"] += 1
        g = u["group"] or ""
        if g not in center_stats[c]["groups"]:
            center_stats[c]["groups"][g] = {"total_tokens": 0, "user_count": 0, "active_count": 0}
        center_stats[c]["groups"][g]["total_tokens"] += u["total_tokens"]
        center_stats[c]["groups"][g]["user_count"] += 1
        if u["has_usage"]:
            center_stats[c]["groups"][g]["active_count"] += 1

    return {
        "month": month,
        "source": source,
        "total_users": total_users,
        "active_users": active_count,
        "total_all": total_all,
        "total_input": total_input,
        "total_output": total_output,
        "centers": [{
            "name": c,
            "total_tokens": s["total_tokens"],
            "user_count": s["user_count"],
            "active_count": s["active_count"],
            "groups": [{
                "name": g,
                "total_tokens": gs["total_tokens"],
                "user_count": gs["user_count"],
                "active_count": gs["active_count"],
                "users": [u for u in flat_users if (u["center"] or "其他") == c and (u["group"] or "") == g]
            } for g, gs in sorted(s["groups"].items(), key=lambda x: x[1]["total_tokens"], reverse=True)]
        } for c, s in sorted(center_stats.items(), key=lambda x: x[1]["total_tokens"], reverse=True)],
        "rankings": [{
            "rank": i + 1,
            "account": u["account"],
            "name": u["name"],
            "center": u["center"],
            "group": u["group"],
            "total_tokens": u["total_tokens"],
            "input_tokens": u["input_tokens"],
            "output_tokens": u["output_tokens"],
            "request_count": u["request_count"]
        } for i, u in enumerate(active_users)],
        "_user_index": {u["account"]: {
            "name": u["name"],
            "rank": active_users.index(u) + 1 if u in active_users else -1,
            "center": u["center"], "group": u["group"],
            "total_tokens": u["total_tokens"], "input_tokens": u["input_tokens"],
            "output_tokens": u["output_tokens"], "request_count": u["request_count"],
            "has_usage": u["has_usage"]
        } for u in flat_users}
    }


def get_token_stats(view, params):
    """Token 统计 API 数据获取"""
    month = params.get("month", [date.today().strftime("%Y-%m")])[0]
    cache_key = f"{month}"

    # 检查缓存
    with _token_cache_lock:
        now = time.time()
        if _token_cache["data"] is not None and _token_cache["ts"] > now - TOKEN_CACHE_TTL and _token_cache.get("key") == cache_key:
            data = _token_cache["data"]
            print(f"[Token统计] API view={view} 命中缓存 source={data.get('source','?')}", flush=True)
        else:
            print(f"[Token统计] API view={view} 缓存失效，重新构建 month={month}...", flush=True)
            data = _build_token_result(month)
            if data is None:
                print(f"[Token统计] API view={view} 数据构建失败", flush=True)
                return {"ok": False, "error": "数据不可用，请确认数据库连接或 report_data.json 已就绪"}
            _token_cache["data"] = data
            _token_cache["ts"] = now
            _token_cache["key"] = cache_key
            _token_cache["source"] = data["source"]
            print(f"[Token统计] 缓存已更新 source={data['source']}, users={data['total_users']}, active={data['active_users']}", flush=True)

    if view == "overview":
        return {
            "ok": True,
            "month": data["month"],
            "source": data["source"],
            "total_users": data["total_users"],
            "active_users": data["active_users"],
            "total_all": data["total_all"],
            "total_input": data["total_input"],
            "total_output": data["total_output"],
            "coverage": round(data["active_users"] / max(data["total_users"], 1) * 100, 1),
            "centers": [{"name": c["name"], "total_tokens": c["total_tokens"], "user_count": c["user_count"], "active_count": c["active_count"]} for c in data["centers"]]
        }

    if view == "my":
        account = params.get("account", [""])[0]
        idx = data.get("_user_index", {}).get(account)
        if not idx:
            return {"ok": False, "error": f"未找到账号 {account}"}
        total_ranked = len(data["rankings"])
        return {
            "ok": True,
            "month": data["month"],
            "source": data["source"],
            "account": account,
            "name": idx["name"],
            "center": idx["center"],
            "group": idx["group"],
            "total_tokens": idx["total_tokens"],
            "input_tokens": idx["input_tokens"],
            "output_tokens": idx["output_tokens"],
            "request_count": idx["request_count"],
            "has_usage": idx["has_usage"],
            "rank": idx["rank"] if idx["has_usage"] else -1,
            "total_ranked": total_ranked,
            "percentile": round((1 - idx["rank"] / max(total_ranked, 1)) * 100, 1) if idx["has_usage"] and idx["rank"] > 0 else 0,
            "total_users": data["total_users"]
        }

    if view == "centers":
        return {
            "ok": True,
            "month": data["month"],
            "source": data["source"],
            "centers": [{"name": c["name"], "total_tokens": c["total_tokens"], "user_count": c["user_count"], "active_count": c["active_count"]} for c in data["centers"]],
            "max_tokens": max((c["total_tokens"] for c in data["centers"]), default=1)
        }

    if view == "center":
        name = params.get("name", [""])[0]
        found = next((c for c in data["centers"] if c["name"] == name), None)
        if not found:
            return {"ok": False, "error": f"未找到中心 {name}"}
        return {
            "ok": True,
            "center": found,
            "max_tokens": max((g["total_tokens"] for g in found["groups"]), default=1)
        }

    if view == "rankings":
        top = int(params.get("top", [20])[0])
        account = params.get("account", [None])[0]
        rankings = data["rankings"][:top]
        result = {"ok": True, "month": data["month"], "source": data["source"], "rankings": rankings, "max_tokens": max((r["total_tokens"] for r in rankings), default=1)}
        if account:
            idx = data.get("_user_index", {}).get(account)
            if idx:
                result["my_rank"] = idx["rank"] if idx["has_usage"] else -1
                result["my_total"] = idx["total_tokens"]
        return result

    if view == "groups":
        all_groups = []
        for c in data["centers"]:
            for g in c.get("groups", []):
                if g["name"] and g["user_count"] > 0:
                    all_groups.append({
                        "name": g["name"],
                        "center": c["name"],
                        "total_tokens": g["total_tokens"],
                        "user_count": g["user_count"],
                        "active_count": g["active_count"]
                    })
        all_groups.sort(key=lambda x: x["total_tokens"], reverse=True)
        return {
            "ok": True,
            "month": data["month"],
            "source": data["source"],
            "groups": all_groups,
            "max_tokens": max((g["total_tokens"] for g in all_groups), default=1)
        }

    return {"ok": False, "error": f"未知视图: {view}"}


# ═══════════════════════════════════════════════════════════
#  案例分享 API
# ═══════════════════════════════════════════════════════════

def case_list(view='latest'):
    conn = get_db()
    order = 'ORDER BY created_at DESC' if view == 'latest' else 'ORDER BY likes DESC'
    cur = conn.execute(f'SELECT id, title, description, file_path, file_type, author, author_name, likes, created_at FROM cases {order}')
    rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
    conn.close()
    return rows

def case_detail(case_id):
    conn = get_db()
    cur = conn.execute('SELECT id, title, description, file_path, file_type, author, author_name, likes, created_at FROM cases WHERE id = ?', (case_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    cols = [d[0] for d in cur.description]
    case = dict(zip(cols, row))
    conn.close()
    return case

def case_like(case_id, fingerprint):
    conn = get_db()
    try:
        conn.execute('INSERT OR IGNORE INTO case_likes (case_id, fingerprint) VALUES (?, ?)', (case_id, fingerprint))
        cur = conn.execute('SELECT COUNT(*) FROM case_likes WHERE case_id = ?', (case_id,))
        likes = cur.fetchone()[0]
        conn.execute('UPDATE cases SET likes = ? WHERE id = ?', (likes, case_id))
        conn.commit()
    finally:
        conn.close()
    return likes

def case_has_liked(case_id, fingerprint):
    conn = get_db()
    cur = conn.execute('SELECT COUNT(*) FROM case_likes WHERE case_id = ? AND fingerprint = ?', (case_id, fingerprint))
    result = cur.fetchone()[0] > 0
    conn.close()
    return result

def case_create(title, description, file_path, file_type, author, author_name):
    conn = get_db()
    conn.execute('INSERT INTO cases (title, description, file_path, file_type, author, author_name) VALUES (?,?,?,?,?,?)',
                 (title, description, file_path, file_type, author, author_name))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════
#  问题反馈 API
# ═══════════════════════════════════════════════════════════

def feedback_list():
    conn = get_db()
    cur = conn.execute('''
        SELECT f.id, f.title, f.content, f.author, f.author_name, f.images, f.status, f.created_at,
               (SELECT COUNT(*) FROM feedback_replies WHERE feedback_id = f.id) as reply_count
        FROM feedback f ORDER BY f.created_at DESC
    ''')
    rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
    conn.close()
    return rows

def feedback_detail(fb_id):
    conn = get_db()
    cur = conn.execute('SELECT id, title, content, author, author_name, images, status, created_at FROM feedback WHERE id = ?', (fb_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    cols = [d[0] for d in cur.description]
    fb = dict(zip(cols, row))
    cur = conn.execute('SELECT id, content, author, author_name, images, created_at FROM feedback_replies WHERE feedback_id = ? ORDER BY created_at', (fb_id,))
    fb['replies'] = [dict(zip(['id','content','author','author_name','images','created_at'], r)) for r in cur.fetchall()]
    conn.close()
    return fb

def feedback_create(title, content, author, author_name, images=''):
    conn = get_db()
    conn.execute('INSERT INTO feedback (title, content, author, author_name, images) VALUES (?,?,?,?,?)',
                 (title, content, author, author_name, images))
    conn.commit()
    conn.close()

def feedback_reply(fb_id, content, author, author_name, images=''):
    conn = get_db()
    conn.execute('INSERT INTO feedback_replies (feedback_id, content, author, author_name, images) VALUES (?,?,?,?,?)',
                 (fb_id, content, author, author_name, images))
    conn.commit()
    conn.close()

def feedback_resolve(fb_id):
    conn = get_db()
    conn.execute("UPDATE feedback SET status = 'resolved' WHERE id = ?", (fb_id,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════
#  Multipart 文件上传解析
# ═══════════════════════════════════════════════════════════
#  图片上传
# ═══════════════════════════════════════════════════════════

def upload_image(file_bytes, orig_name):
    """保存上传的图片到 uploads/，返回文件名"""
    ext = orig_name.rsplit('.', 1)[-1].lower() if '.' in orig_name else 'png'
    if ext not in ('png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'):
        ext = 'png'
    fname = uuid.uuid4().hex[:12] + '.' + ext
    with open(os.path.join(UPLOAD_DIR, fname), 'wb') as f:
        f.write(file_bytes)
    return fname


# ═══════════════════════════════════════════════════════════
#  Multipart 文件上传解析
# ═══════════════════════════════════════════════════════════

def parse_multipart(data, boundary):
    """解析完整 multipart/form-data body，返回 {fieldname: (filename, value)} 字典"""
    boundary = boundary.encode()
    result = {}
    parts = data.split(b'--' + boundary)
    for part in parts:
        if b'\r\n\r\n' not in part:
            continue
        header_section, _, body_section = part.partition(b'\r\n\r\n')
        body_section = body_section.rstrip(b'\r\n')
        headers = header_section.decode(errors='replace')
        if 'name="' not in headers:
            continue
        # 提取 field name
        name_m = headers.split('name="')[1].split('"')[0] if 'name="' in headers else ''
        filename = ''
        if 'filename="' in headers:
            filename = headers.split('filename="')[1].split('"')[0]
        result[name_m] = (filename, body_section)
    return result




class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == '/api/stats':
                qs = urllib.parse.parse_qs(parsed.query)
                fp = qs.get('fingerprint', [None])[0]
                self.send_json(get_stats(resolve_fp=fp))
                return

            if parsed.path == '/api/token-stats':
                qs = urllib.parse.parse_qs(parsed.query)
                view = qs.get('view', ['overview'])[0]
                self.send_json(get_token_stats(view, qs))
                return

            if parsed.path == '/api/cases':
                qs = urllib.parse.parse_qs(parsed.query)
                vid = qs.get('view', ['list'])[0]
                if vid == 'detail':
                    self.send_json(case_detail(int(qs.get('id', [0])[0])) or {'error': 'not found'})
                else:
                    self.send_json(case_list(view=vid))
                return

            if parsed.path == '/api/feedback':
                qs = urllib.parse.parse_qs(parsed.query)
                vid = qs.get('view', ['list'])[0]
                if vid == 'detail':
                    self.send_json(feedback_detail(int(qs.get('id', [0])[0])) or {'error': 'not found'})
                else:
                    self.send_json(feedback_list())
                return

            # /uploads/ 静态文件
            if parsed.path.startswith('/uploads/'):
                fs_path = self.translate_path(parsed.path)
                if os.path.isfile(fs_path):
                    self.send_response(200)
                    self.send_header('Content-Type', self.guess_type(parsed.path))
                    self.send_header('Content-Length', os.path.getsize(fs_path))
                    self.end_headers()
                    with open(fs_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
                self.send_response(404)
                self.end_headers()
                return

            # Range 请求支持（视频拖动进度条依赖此功能）
            fs_path = self.translate_path(parsed.path)
            range_header = self.headers.get('Range')
            if range_header and os.path.isfile(fs_path):
                try:
                    self._serve_range(fs_path, range_header)
                    return
                except Exception:
                    pass  # 降级到完整文件传输
            super().do_GET()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass  # 客户端断开连接（如刷新页面），静默忽略

    def _serve_range(self, path, range_header):
        """处理 HTTP Range 请求，返回 206 Partial Content"""
        file_size = os.path.getsize(path)
        range_match = range_header.replace('bytes=', '').split('-')
        if range_header.endswith('-'):
            # bytes=N- 格式：从 N 到末尾
            start = int(range_match[0])
            end = file_size - 1
        elif range_match[0] == '':
            # bytes=-N 格式：末尾 N 字节
            suffix_len = int(range_match[1])
            start = file_size - suffix_len
            end = file_size - 1
        else:
            # bytes=N-M 格式
            start = int(range_match[0])
            end = int(range_match[1])
        end = min(end, file_size - 1)

        if start >= file_size:
            self.send_response(416)
            self.send_header('Content-Range', f'bytes */{file_size}')
            self.end_headers()
            return

        chunk_size = end - start + 1
        with open(path, 'rb') as f:
            f.seek(start)
            data = f.read(chunk_size)

        try:
            self.send_response(206)
            self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(chunk_size))
            self.send_header('Content-Type', self.guess_type(path))
            self.end_headers()
            self.wfile.write(data)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass  # 客户端断开，静默忽略

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/stats':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b'{}'
            data = json.loads(body)
            page = data.get('page', '/')
            user = data.get('user', '')
            fp = data.get('fingerprint', '')
            record_visit(page, user=user, fingerprint=fp)
            self.send_json(get_stats(resolve_fp=fp if fp else None))
            return
        if parsed.path == '/api/register-user':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b'{}'
            data = json.loads(body)
            fp = data.get('fingerprint', '')
            account = data.get('account', '')
            register_fingerprint(fp, account)
            self.send_json({'ok': True, 'resolved_user': account})
            return
        if parsed.path == '/api/checkin':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b'{}'
            data = json.loads(body)
            fp = data.get('fingerprint', '')
            do_checkin(user=data.get('user', ''), fingerprint=fp)
            self.send_json(get_stats(resolve_fp=fp if fp else None))
            return
        if parsed.path == '/api/help-request':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else b'{}'
            data = json.loads(body)
            fp = data.get('fingerprint', '')
            record_help_request(
                user=data.get('user', ''),
                fingerprint=fp,
                page=data.get('page', ''))
            self.send_json(get_stats(resolve_fp=fp if fp else None))
            return

        # 案例上传 (multipart/form-data)
        if parsed.path == '/api/cases':
            ctype = self.headers.get('Content-Type', '')
            if 'multipart/form-data' in ctype:
                boundary = ctype.split('boundary=')[1]
                clen = int(self.headers.get('Content-Length', 0))
                data = self.rfile.read(clen)
                fields = parse_multipart(data, boundary)
                title = fields.get('title', ('', b''))[1].decode()
                desc = fields.get('description', ('', b''))[1].decode()
                author = fields.get('author', ('', b''))[1].decode()
                author_name = fields.get('author_name', ('', b''))[1].decode()
                # 文件处理
                file_info = fields.get('file', ('', b''))
                fname, fbytes = file_info
                file_type = ''; saved_path = ''
                if fname and fbytes:
                    ext = fname.rsplit('.', 1)[-1].lower() if '.' in fname else ''
                    file_type = ext
                    saved_name = uuid.uuid4().hex[:12] + ('.' + ext if ext else '')
                    saved_path = os.path.join(UPLOAD_DIR, saved_name)
                    with open(saved_path, 'wb') as f:
                        f.write(fbytes)
                case_create(title, desc, saved_name if fname else '', file_type, author, author_name)
                self.send_json({'ok': True})
            else:
                self.send_response(400); self.end_headers()
            return

        # 案例点赞
        if parsed.path == '/api/cases/like':
            clen = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(clen) if clen else b'{}'
            data = json.loads(body)
            case_id = data.get('case_id', 0)
            fp = data.get('fingerprint', '')
            likes = case_like(case_id, fp)
            self.send_json({'ok': True, 'likes': likes, 'has_liked': True})
            return

        # 案例点赞检查
        if parsed.path == '/api/cases/liked':
            clen = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(clen) if clen else b'{}'
            data = json.loads(body)
            has = case_has_liked(data.get('case_id', 0), data.get('fingerprint', ''))
            self.send_json({'has_liked': has})
            return

        # 反馈提交
        if parsed.path == '/api/feedback':
            clen = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(clen) if clen else b'{}'
            data = json.loads(body)
            feedback_create(data.get('title',''), data.get('content',''), data.get('author',''), data.get('author_name',''), data.get('images',''))
            self.send_json({'ok': True})
            return

        # 反馈回复
        if parsed.path == '/api/feedback/reply':
            clen = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(clen) if clen else b'{}'
            data = json.loads(body)
            feedback_reply(data.get('feedback_id',0), data.get('content',''), data.get('author',''), data.get('author_name',''), data.get('images',''))
            self.send_json({'ok': True})
            return

        # 标记已解决
        if parsed.path == '/api/feedback/resolve':
            clen = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(clen) if clen else b'{}'
            data = json.loads(body)
            feedback_resolve(data.get('feedback_id', 0))
            self.send_json({'ok': True})
            return

        # 图片上传
        if parsed.path == '/api/upload-image':
            ctype = self.headers.get('Content-Type', '')
            if 'multipart/form-data' in ctype:
                boundary = ctype.split('boundary=')[1]
                clen = int(self.headers.get('Content-Length', 0))
                data = self.rfile.read(clen)
                fields = parse_multipart(data, boundary)
                fname, fbytes = fields.get('image', ('', b''))
                if fname and fbytes:
                    saved = upload_image(fbytes, fname)
                    self.send_json({'ok': True, 'filename': saved})
                    return
            self.send_json({'ok': False, 'error': 'no image'})
            return

        self.send_response(405)
        self.end_headers()

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # 抑制 API 请求日志，只保留静态文件请求日志
        if '/api/' not in str(args[0] if args else ''):
            super().log_message(format, *args)


if __name__ == '__main__':
    db_status = "DB直连" if _HAS_PYMYSQL else "JSON兜底"
    print(f'''
╔══════════════════════════════════════════════╗
║     AI赋能日常工作 — 本地服务器已启动        ║
║                                               ║
║     访问地址:  http://localhost:{PORT}          ║
║     Token统计:  {db_status}                       ║
║     按 Ctrl+C 停止服务器                      ║
╚══════════════════════════════════════════════╝
''')
    http.server.ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
