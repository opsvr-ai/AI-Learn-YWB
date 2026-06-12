"""Token 统计 — 基于 ai_metrics_daily 按人日聚合查询（参照 ywb_token_usage.py）"""
import json, os, calendar, threading, time
from datetime import date

ROOT, DAILY_DIR, MONTHLY_DIR = None, None, None

def _load_env():
    """从 .env 文件加载数据库配置，缺失时使用内置默认值"""
    cfg = {
        'host': '127.0.0.1', 'port': 3306, 'user': 'root',
        'password': '', 'database': 'ai_gateway', 'charset': 'utf8mb4',
        'connect_timeout': 10, 'read_timeout': 300, 'write_timeout': 300,
    }
    env_path = os.path.join(ROOT, '.env') if ROOT else '.env'
    if os.path.exists(env_path):
        try:
            for line in open(env_path, encoding='utf-8'):
                line = line.strip()
                if not line or line.startswith('#'): continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip(); v = v.strip().strip('"').strip("'")
                    if k == 'DB_HOST':             cfg['host'] = v
                    elif k == 'DB_PORT':           cfg['port'] = int(v)
                    elif k == 'DB_USER':           cfg['user'] = v
                    elif k == 'DB_PASSWORD':       cfg['password'] = v
                    elif k == 'DB_NAME':           cfg['database'] = v
                    elif k == 'DB_CHARSET':        cfg['charset'] = v
                    elif k == 'DB_CONNECT_TIMEOUT': cfg['connect_timeout'] = int(v)
                    elif k == 'DB_READ_TIMEOUT':    cfg['read_timeout'] = int(v)
                    elif k == 'DB_WRITE_TIMEOUT':   cfg['write_timeout'] = int(v)
        except Exception as e: print(f"[Token] .env 读取失败: {e}，使用默认配置")
    return cfg

AIGW_DB_CONFIG = None
_org_accounts = []      # 部门所有域账号列表
_org_map = {}            # 域账号 → {name, center, group}
_sync_lock = threading.Lock()
_syncing = set()


def init(root):
    global ROOT, DAILY_DIR, MONTHLY_DIR, AIGW_DB_CONFIG
    ROOT = root
    AIGW_DB_CONFIG = _load_env()
    DAILY_DIR = os.path.join(ROOT, 'data', 'daily');  os.makedirs(DAILY_DIR, exist_ok=True)
    MONTHLY_DIR = os.path.join(ROOT, 'data', 'monthly'); os.makedirs(MONTHLY_DIR, exist_ok=True)
    _load_org()

def _load_org():
    global _org_accounts, _org_map
    csv_path = os.path.join(ROOT, 'ywb-users.csv')
    if not os.path.exists(csv_path): return
    try:
        import csv
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                acc = row.get('域账号', '').strip()
                if not acc: continue
                _org_accounts.append(acc)
                _org_map[acc] = {"name": row.get('姓名', '').strip(), "center": row.get('中心名称', '').strip(), "group": row.get('组别', '').strip()}
        print(f"[Token] ywb-users.csv: {len(_org_map)} 人")
    except Exception as e: print(f"[Token] CSV 加载失败: {e}")


# ═══════════════ 日/月文件 IO ═══════════════

def _daily_path(day): return os.path.join(DAILY_DIR, f'{day}.json')
def _monthly_path(m): return os.path.join(MONTHLY_DIR, f'{m}.json')

def _daily_write(day_str, data):
    with open(_daily_path(day_str), 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False)

def _daily_read(day_str):
    with open(_daily_path(day_str), 'r', encoding='utf-8') as f: return json.load(f)

def _monthly_write(month, data):
    with open(_monthly_path(month), 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False)

def _monthly_read(month):
    with open(_monthly_path(month), 'r', encoding='utf-8') as f: return json.load(f)

def _daily_exists(day): return os.path.exists(_daily_path(day))


# ═══════════════ DB 查询（核心：一条 SQL 查全部部门用户） ═══════════════

def _fetch_month_from_db(month):
    """从 ai_metrics_daily 一次性查询全月所有运维部人员的日用量。
    返回: { 'YYYY-MM-DD': { 'lilong': {input,output,request}, ... }, ... }
    """
    if not _org_accounts: return None
    import pymysql
    y, m = map(int, month.split('-')); days = calendar.monthrange(y, m)[1]
    start, end = f"{y}-{m:02d}-01", f"{y}-{m:02d}-{days:02d}"

    # 构建 WHERE：每个域账号一个 LIKE 条件（与 ywb_token_usage.py 完全一致）
    likes = ["ai_consumer LIKE %s" for _ in _org_accounts]
    params = [f"{a}_%" for a in _org_accounts]
    where = " OR ".join(likes)
    params.extend([start, end])

    sql = (
        "SELECT stat_date, "
        "  CASE "
        "    WHEN ai_consumer LIKE '800P_%%' THEN "
        "      CONCAT('800P_', SUBSTRING_INDEX(SUBSTRING(ai_consumer, 6), '_', 1)) "
        "    ELSE "
        "      SUBSTRING_INDEX(ai_consumer, '_', 1) "
        "  END AS domain_account, "
        "  SUM(input_tokens)   AS input_tokens, "
        "  SUM(output_tokens)  AS output_tokens, "
        "  SUM(request_count)  AS request_count "
        "FROM ai_metrics_daily "
        f"WHERE ({where}) AND stat_date >= %s AND stat_date <= %s "
        "GROUP BY stat_date, domain_account "
        "ORDER BY stat_date, domain_account"
    )

    print(f"[Token] 查询 {month}: {len(_org_accounts)} 个域账号, 范围 [{start}, {end}]", flush=True)
    try:
        conn = pymysql.connect(**AIGW_DB_CONFIG); cur = conn.cursor()
        t0 = time.time()
        cur.execute(sql, params)
        rows = cur.fetchall()
        elapsed = time.time() - t0
        result = {}
        for d, acc, inp, out, req in rows:
            ds = d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d)
            result.setdefault(ds, {})[acc] = {"input_tokens": int(inp or 0), "output_tokens": int(out or 0), "request_count": int(req or 0)}
        cur.close(); conn.close()
        print(f"[Token] 查询完成: {len(rows)} 条日-人记录, {len(result)} 天, {elapsed:.1f}s", flush=True)
        return result
    except Exception as e:
        import traceback; print(f"[Token] 查询失败: {e}", flush=True); traceback.print_exc(); return None


# ═══════════════ 差量同步 + 月度聚合 ═══════════════

def _missing_days(month):
    y, m = map(int, month.split('-')); days = calendar.monthrange(y, m)[1]
    today = date.today().strftime('%Y-%m-%d')
    missing = []
    for d in range(1, days + 1):
        ds = f"{y}-{m:02d}-{d:02d}"
        if ds > today: break
        if not _daily_exists(ds): missing.append(ds)
    return missing

def _sync_month_single_query(month):
    """后台线程：一次性 SQL 拉取全月 → 按天写文件 → 聚合月度文件"""
    with _sync_lock:
        if month in _syncing: return
        _syncing.add(month)
    try:
        missing = _missing_days(month)
        if not missing:
            print(f"[Token] {month} 所有天已缓存，跳过 DB 查询", flush=True)
            _build_monthly(month); return

        print(f"[Token] 后台同步 {month}: 缺失 {len(missing)} 天", flush=True)
        data = _fetch_month_from_db(month)
        if not data:
            print(f"[Token] {month} 查询无数据或失败", flush=True); return

        # 按天写入文件
        written = 0
        for ds in sorted(data):
            if not _daily_exists(ds):
                _daily_write(ds, {"day": ds, "users": data[ds]})
                written += 1
        print(f"[Token] {month} 写入 {written} 个新日文件", flush=True)
        _build_monthly(month)
    except Exception as e:
        import traceback; print(f"[Token] {month} 同步异常: {e}", flush=True); traceback.print_exc()
    finally:
        with _sync_lock: _syncing.discard(month)


def _build_monthly(month):
    """从日文件聚合月度结果并写入 data/monthly/"""
    y, m = map(int, month.split('-')); days = calendar.monthrange(y, m)[1]
    consumers = {}
    for d in range(1, days + 1):
        ds = f"{y}-{m:02d}-{d:02d}"
        if not _daily_exists(ds): continue
        for acc, stats in _daily_read(ds).get("users", {}).items():
            c = consumers.setdefault(acc, {"input_tokens":0,"output_tokens":0,"request_count":0})
            c["input_tokens"] += stats["input_tokens"]
            c["output_tokens"] += stats["output_tokens"]
            c["request_count"] += stats["request_count"]
    if not consumers: return
    flat = []
    for acc, info in _org_map.items():
        u = consumers.get(acc, {"input_tokens":0,"output_tokens":0,"request_count":0})
        t = u["input_tokens"] + u["output_tokens"]
        flat.append({"account":acc,"name":info["name"],"center":info["center"],"group":info["group"],
                      "input_tokens":u["input_tokens"],"output_tokens":u["output_tokens"],
                      "request_count":u["request_count"],"total_tokens":t,"has_usage":t>0})
    flat.sort(key=lambda x: x["total_tokens"], reverse=True)
    packaged = _package(month, "db", flat)
    _monthly_write(month, packaged)
    print(f"[Token] 月度聚合: {month} source=db users={packaged['total_users']} active={packaged['active_users']}", flush=True)


# ═══════════════ 数据打包 + JSON 兜底 ═══════════════

def _package(month, source, flat):
    active = [u for u in flat if u["has_usage"]]; cs = {}
    for u in flat:
        c, g = u["center"] or "其他", u["group"] or ""
        ct = cs.setdefault(c, {"t":0,"uc":0,"ac":0,"g":{}})
        ct["t"] += u["total_tokens"]; ct["uc"] += 1
        if u["has_usage"]: ct["ac"] += 1
        gt = ct["g"].setdefault(g, {"t":0,"uc":0,"ac":0})
        gt["t"] += u["total_tokens"]; gt["uc"] += 1
        if u["has_usage"]: gt["ac"] += 1
    idx = {}
    for i, u in enumerate(sorted(active, key=lambda x: x["total_tokens"], reverse=True)):
        idx[u["account"]] = {"name":u["name"],"rank":i+1,"center":u["center"],"group":u["group"],
                             "total_tokens":u["total_tokens"],"input_tokens":u["input_tokens"],
                             "output_tokens":u["output_tokens"],"request_count":u["request_count"],"has_usage":True}
    for u in flat:
        if not u["has_usage"]:
            idx[u["account"]] = {"name":u["name"],"rank":-1,"center":u["center"],"group":u["group"],
                                 "total_tokens":0,"input_tokens":0,"output_tokens":0,"request_count":0,"has_usage":False}
    return {"month":month,"source":source,"total_users":len(flat),"active_users":len(active),
            "total_all":sum(x["total_tokens"] for x in flat),
            "total_input":sum(x["input_tokens"] for x in flat),
            "total_output":sum(x["output_tokens"] for x in flat),
            "centers":[{"name":c,"total_tokens":s["t"],"user_count":s["uc"],"active_count":s["ac"],
                         "groups":[{"name":g,"total_tokens":gs["t"],"user_count":gs["uc"],"active_count":gs["ac"],
                                      "users":[u for u in flat if (u["center"] or "其他")==c and (u["group"] or "")==g]}
                                     for g,gs in sorted(s["g"].items(),key=lambda x:x[1]["t"],reverse=True)]}
                        for c,s in sorted(cs.items(),key=lambda x:x[1]["t"],reverse=True)],
            "rankings":[{"rank":i+1,"account":u["account"],"name":u["name"],"center":u["center"],
                          "group":u["group"],"total_tokens":u["total_tokens"],"input_tokens":u["input_tokens"],
                          "output_tokens":u["output_tokens"],"request_count":u["request_count"]} for i,u in enumerate(active)],
            "_user_index":idx}

def _build_fallback(month):
    jp = os.path.join(ROOT, 'report_data.json')
    if not os.path.exists(jp): return None
    with open(jp,'r',encoding='utf-8') as f: fb = json.load(f)
    flat = []
    for cn,cd in fb.get("centers",{}).items():
        for gn,gd in cd.get("groups",{}).items():
            for u in gd.get("users",[]):
                un = u.get("username",""); 
                if not un or un=="合计": continue
                t = u.get("total_tokens",0)
                flat.append({"account":un,"name":u.get("name",""),"center":cn,"group":gn,
                              "input_tokens":u.get("input_tokens",0),"output_tokens":u.get("output_tokens",0),
                              "request_count":u.get("request_count",0),"total_tokens":t,"has_usage":t>0})
    if not flat: return None
    flat.sort(key=lambda x:x["total_tokens"],reverse=True)
    return _package(month,"json",flat)


# ═══════════════ API ═══════════════

def get(view, params):
    month = params.get("month", [date.today().strftime("%Y-%m")])[0]
    mp = _monthly_path(month)

    if os.path.exists(mp):
        data = _monthly_read(month)
        print(f"[Token] 月度缓存命中 {month} source={data.get('source','?')}", flush=True)
        return _serve(view, data, params)

    missing = _missing_days(month)
    if not missing:
        print(f"[Token] {month} 日文件齐备，内存聚合", flush=True)
        _build_monthly(month)
        if os.path.exists(mp): return _serve(view, _monthly_read(month), params)

    if missing:
        threading.Thread(target=_sync_month_single_query, args=(month,), daemon=True).start()

    data = _build_fallback(month)
    if data is None: return {"ok":False,"error":"数据不可用"}
    print(f"[Token] JSON 兜底 {month}（后台拉取 {len(missing)} 天）", flush=True)
    return _serve(view, data, params)


def _serve(view, data, params):
    a = params.get("account", [None])[0]
    if view == "overview":
        return {"ok":True,"month":data["month"],"source":data["source"],
                "total_users":data["total_users"],"active_users":data["active_users"],
                "total_all":data["total_all"],"total_input":data["total_input"],"total_output":data["total_output"],
                "coverage":round(data["active_users"]/max(data["total_users"],1)*100,1),
                "centers":[{"name":c["name"],"total_tokens":c["total_tokens"],"user_count":c["user_count"],"active_count":c["active_count"]} for c in data["centers"]]}
    if view == "my":
        idx = data.get("_user_index",{}).get(a)
        if not idx: return {"ok":False,"error":f"未找到账号 {a}"}
        tr = len(data["rankings"])
        return {"ok":True,"month":data["month"],"source":data["source"],"account":a,
                "name":idx["name"],"center":idx["center"],"group":idx["group"],
                "total_tokens":idx["total_tokens"],"input_tokens":idx["input_tokens"],"output_tokens":idx["output_tokens"],
                "request_count":idx["request_count"],"has_usage":idx["has_usage"],
                "rank":idx["rank"] if idx["has_usage"] else -1,"total_ranked":tr,
                "percentile":round((1-idx["rank"]/max(tr,1))*100,1) if idx["has_usage"] and idx["rank"]>0 else 0,
                "total_users":data["total_users"]}
    if view == "centers":
        return {"ok":True,"month":data["month"],"source":data["source"],
                "centers":[{"name":c["name"],"total_tokens":c["total_tokens"],"user_count":c["user_count"],"active_count":c["active_count"]} for c in data["centers"]],
                "max_tokens":max((c["total_tokens"] for c in data["centers"]),default=1)}
    if view == "center":
        found = next((c for c in data["centers"] if c["name"]==params.get("name",[""])[0]),None)
        if not found: return {"ok":False,"error":f"未找到中心 {params.get('name',[''])[0]}"}
        return {"ok":True,"center":found,"max_tokens":max((g["total_tokens"] for g in found["groups"]),default=1)}
    if view == "rankings":
        top = int(params.get("top",[20])[0])
        rankings = data["rankings"][:top]
        result = {"ok":True,"month":data["month"],"source":data["source"],"rankings":rankings,
                  "max_tokens":max((r["total_tokens"] for r in rankings),default=1)}
        if a:
            idx = data.get("_user_index",{}).get(a)
            if idx: result["my_rank"]=idx["rank"] if idx["has_usage"] else -1; result["my_total"]=idx["total_tokens"]
        return result
    if view == "groups":
        ag = [{"name":g["name"],"center":c["name"],"total_tokens":g["total_tokens"],"user_count":g["user_count"],"active_count":g["active_count"]}
              for c in data["centers"] for g in c.get("groups",[]) if g["name"] and g["user_count"]>0]
        ag.sort(key=lambda x:x["total_tokens"],reverse=True)
        return {"ok":True,"month":data["month"],"source":data["source"],"groups":ag,
                "max_tokens":max((g["total_tokens"] for g in ag),default=1)}
    return {"ok":False,"error":f"未知视图: {view}"}
