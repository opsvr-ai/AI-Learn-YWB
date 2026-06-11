"""Token 统计 — data/ 日文件缓存 + 月度聚合 + 差量拉取"""
import json, os, threading, time, calendar
from datetime import date

ROOT, DATA_DIR, DAILY_DIR, MONTHLY_DIR = None, None, None, None
AIGW_DB_CONFIG = {
    'host': '7.22.1.162', 'port': 3306, 'user': 'llmdbappusr',
    'password': 'pP1<zW1+', 'database': 'ai_gateway', 'charset': 'utf8mb4',
    'connect_timeout': 10, 'read_timeout': 300, 'write_timeout': 300,
}
_org_account_map = {}
_sync_lock = threading.Lock()
_syncing = set()  # 正在同步的月份


# ═══════════════ 初始化 ═══════════════

def init(root):
    global ROOT, DATA_DIR, DAILY_DIR, MONTHLY_DIR
    ROOT = root
    DATA_DIR = os.path.join(ROOT, 'data');       os.makedirs(DATA_DIR, exist_ok=True)
    DAILY_DIR = os.path.join(DATA_DIR, 'daily');  os.makedirs(DAILY_DIR, exist_ok=True)
    MONTHLY_DIR = os.path.join(DATA_DIR, 'monthly'); os.makedirs(MONTHLY_DIR, exist_ok=True)
    _load_org()

def _load_org():
    global _org_account_map
    csv_path = os.path.join(ROOT, 'ywb-users.csv')
    if not os.path.exists(csv_path): return
    try:
        import csv
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            for row in csv.reader(f):
                if row[0] == '序号' or len(row) < 6: continue
                n, a, c, g = (row[1] or '').strip(), (row[2] or '').strip(), (row[3] or '').strip(), (row[4] or '').strip()
                if not a: continue
                _org_account_map[a] = {"name": n, "center": c, "group": g}
        print(f"[Token] ywb-users.csv: {len(_org_account_map)} 人")
    except Exception as e: print(f"[Token] CSV 加载失败: {e}")


# ═══════════════ 天文件 ═══════════════

def _daily_path(day_str):       return os.path.join(DAILY_DIR, f'{day_str}.json')

def _daily_exists(day_str):     return os.path.exists(_daily_path(day_str))

def _daily_read(day_str):
    with open(_daily_path(day_str), 'r', encoding='utf-8') as f: return json.load(f)

def _daily_write(day_str, data):
    with open(_daily_path(day_str), 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False)


# ═══════════════ 月文件 ═══════════════

def _monthly_path(month):       return os.path.join(MONTHLY_DIR, f'{month}.json')

def _monthly_read(month):
    with open(_monthly_path(month), 'r', encoding='utf-8') as f: return json.load(f)

def _monthly_write(month, data):
    with open(_monthly_path(month), 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False)


# ═══════════════ DB 拉取（单天） ═══════════════

def _extract_username(c): return c.split('_')[0] if '_' in c else c

def _fetch_one_day(day_start, day_end):
    import pymysql
    for attempt in range(3):
        try:
            conn = pymysql.connect(**AIGW_DB_CONFIG); cur = conn.cursor()
            cur.execute("SELECT ai_consumer, input_tokens, output_tokens, request_count FROM ai_metrics WHERE time_bucket>=%s AND time_bucket<%s", (day_start, day_end))
            rows = cur.fetchall(); cur.close(); conn.close()
            return rows
        except Exception as e:
            if attempt < 2: time.sleep(2)
            else: print(f"[Token] 单天查询失败 {day_start}: {e}", flush=True)
    return []


# ═══════════════ 差量同步 ═══════════════

def _days_of_month(month):
    y, m = map(int, month.split('-')); return calendar.monthrange(y, m)[1]

def _day_range(y, m, d, days):
    ds = f"{y}-{m:02d}-{d:02d} 00:00:00"
    if d < days: de = f"{y}-{m:02d}-{d+1:02d} 00:00:00"
    else: de = f"{y+(m//12)}-{(m%12)+1:02d}-01 00:00:00"
    return ds, de

def _missing_days(month):
    """返回某月所有尚未拉取的天的列表"""
    y, m = map(int, month.split('-')); days = _days_of_month(month)
    today = date.today().strftime('%Y-%m-%d')
    missing = []
    for d in range(1, days + 1):
        day_str = f"{y}-{m:02d}-{d:02d}"
        if day_str > today: break
        if not _daily_exists(day_str):
            missing.append(d)
    return missing

def _sync_month(month):
    """后台线程：拉取某月份所有缺失的天，完成后聚合写入月度文件"""
    with _sync_lock:
        if month in _syncing: return
        _syncing.add(month)

    try:
        missing = _missing_days(month)
        if not missing:
            print(f"[Token] {month} 所有天已缓存，无需拉取", flush=True)
            _build_monthly_from_daily(month)
            return

        y, m = map(int, month.split('-')); total_days = _days_of_month(month)
        print(f"[Token] 开始同步 {month}：需拉取 {len(missing)}/{total_days} 天", flush=True)
        success = 0
        for d in missing:
            ds, de = _day_range(y, m, d, total_days)
            day_str = f"{y}-{m:02d}-{d:02d}"
            rows = _fetch_one_day(ds, de)
            if rows is None:
                print(f"[Token] {day_str} 拉取失败（连接问题），跳过", flush=True)
                continue
            users = {}
            for c, inp, out, req in rows:
                u = _extract_username(c)
                ud = users.setdefault(u, {"input_tokens": 0, "output_tokens": 0, "request_count": 0})
                ud["input_tokens"]  += inp or 0
                ud["output_tokens"] += out or 0
                ud["request_count"] += req or 0
            _daily_write(day_str, {"day": day_str, "users": users})
            success += 1
            dt_rows = len(rows); dt_users = len(users)
            print(f"[Token] {day_str} ✓ {dt_rows:>7} 行 → {dt_users} 用户  进度 {success}/{len(missing)}", flush=True)
        print(f"[Token] {month} 同步完成：{success}/{len(missing)} 天成功", flush=True)
        _build_monthly_from_daily(month)
    except Exception as e:
        import traceback; print(f"[Token] {month} 同步异常: {e}", flush=True); traceback.print_exc()
    finally:
        with _sync_lock: _syncing.discard(month)


def _build_monthly_from_daily(month):
    """从已缓存的日文件聚合出完整月度结果"""
    y, m = map(int, month.split('-')); total_days = _days_of_month(month)
    consumers = {}
    for d in range(1, total_days + 1):
        day_str = f"{y}-{m:02d}-{d:02d}"
        if not _daily_exists(day_str): continue
        day_data = _daily_read(day_str)
        for u, stats in day_data.get("users", {}).items():
            c = consumers.setdefault(u, {"input_tokens": 0, "output_tokens": 0, "request_count": 0})
            c["input_tokens"]  += stats["input_tokens"]
            c["output_tokens"] += stats["output_tokens"]
            c["request_count"] += stats["request_count"]
    if not consumers:
        print(f"[Token] {month} 无任何天数据，月度结果为空", flush=True)
        return

    flat = []
    for a, info in _org_account_map.items():
        u = consumers.get(a, {"input_tokens": 0, "output_tokens": 0, "request_count": 0})
        t = u["input_tokens"] + u["output_tokens"]
        flat.append({"account": a, "name": info["name"], "center": info["center"], "group": info["group"],
                      "input_tokens": u["input_tokens"], "output_tokens": u["output_tokens"],
                      "request_count": u["request_count"], "total_tokens": t, "has_usage": t > 0})
    if not flat: return
    flat.sort(key=lambda x: x["total_tokens"], reverse=True)
    active = [u for u in flat if u["has_usage"]]
    packaged = _package(month, "db", flat)
    _monthly_write(month, packaged)
    print(f"[Token] 月度聚合完成: {month} source=db users={packaged['total_users']} active={packaged['active_users']}", flush=True)


# ═══════════════ 数据打包 ═══════════════

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
        idx[u["account"]] = {"name": u["name"], "rank": i+1, "center": u["center"], "group": u["group"],
                             "total_tokens": u["total_tokens"], "input_tokens": u["input_tokens"],
                             "output_tokens": u["output_tokens"], "request_count": u["request_count"], "has_usage": True}
    for u in flat:
        if not u["has_usage"]:
            idx[u["account"]] = {"name": u["name"], "rank": -1, "center": u["center"], "group": u["group"],
                                 "total_tokens": 0, "input_tokens": 0, "output_tokens": 0, "request_count": 0, "has_usage": False}
    return {"month": month, "source": source, "total_users": len(flat), "active_users": len(active),
            "total_all": sum(x["total_tokens"] for x in flat),
            "total_input": sum(x["input_tokens"] for x in flat),
            "total_output": sum(x["output_tokens"] for x in flat),
            "centers": [{"name": c, "total_tokens": s["t"], "user_count": s["uc"], "active_count": s["ac"],
                          "groups": [{"name": g, "total_tokens": gs["t"], "user_count": gs["uc"], "active_count": gs["ac"],
                                       "users": [u for u in flat if (u["center"] or "其他") == c and (u["group"] or "") == g]}
                                      for g, gs in sorted(s["g"].items(), key=lambda x: x[1]["t"], reverse=True)]}
                         for c, s in sorted(cs.items(), key=lambda x: x[1]["t"], reverse=True)],
            "rankings": [{"rank": i+1, "account": u["account"], "name": u["name"], "center": u["center"],
                           "group": u["group"], "total_tokens": u["total_tokens"], "input_tokens": u["input_tokens"],
                           "output_tokens": u["output_tokens"], "request_count": u["request_count"]} for i, u in enumerate(active)],
            "_user_index": idx}


# ═══════════════ VIP 层（从 report_data.json） ═══════════════

def _build_fallback(month):
    """report_data.json 兜底（跨月份都返回同一份静态数据，标注 source=json）"""
    jp = os.path.join(ROOT, 'report_data.json')
    if not os.path.exists(jp): return None
    with open(jp, 'r', encoding='utf-8') as f: fb = json.load(f)
    flat = []
    for cn, cd in fb.get("centers", {}).items():
        for gn, gd in cd.get("groups", {}).items():
            for u in gd.get("users", []):
                un = u.get("username", "")
                if not un or un == "合计": continue
                t = u.get("total_tokens", 0)
                flat.append({"account": un, "name": u.get("name", ""), "center": cn, "group": gn,
                              "input_tokens": u.get("input_tokens", 0), "output_tokens": u.get("output_tokens", 0),
                              "request_count": u.get("request_count", 0), "total_tokens": t, "has_usage": t > 0})
    if not flat: return None
    flat.sort(key=lambda x: x["total_tokens"], reverse=True)
    return _package(month, "json", flat)


# ═══════════════ API 入口 ═══════════════

def get(view, params):
    month = params.get("month", [date.today().strftime("%Y-%m")])[0]
    mp = _monthly_path(month)

    # 1) 月文件已存在 → 直接返回
    if os.path.exists(mp):
        data = _monthly_read(month)
        print(f"[Token] 月度缓存命中 {month} source={data.get('source','?')}", flush=True)
        return _serve(view, data, params)

    # 2) 所有天文件都存在 → 直接聚合出月度结果（不查DB）
    missing = _missing_days(month)
    if not missing:
        print(f"[Token] {month} 所有天已缓存，内存聚合中...", flush=True)
        _build_monthly_from_daily(month)
        if os.path.exists(mp):
            return _serve(view, _monthly_read(month), params)
        print(f"[Token] {month} 聚合失败，降级 JSON 兜底", flush=True)

    # 3) 后台启动差量拉取（不阻塞当前请求）
    if missing:
        threading.Thread(target=_sync_month, args=(month,), daemon=True).start()

    # 4) 当前请求用 JSON 兜底返回
    data = _build_fallback(month)
    if data is None:
        return {"ok": False, "error": "数据不可用"}
    print(f"[Token] JSON 兜底 {month}（后台拉取 {len(missing)} 天中...）", flush=True)
    return _serve(view, data, params)


def _serve(view, data, params):
    a = params.get("account", [None])[0]
    if view == "overview":
        return {"ok": True, "month": data["month"], "source": data["source"],
                "total_users": data["total_users"], "active_users": data["active_users"],
                "total_all": data["total_all"], "total_input": data["total_input"], "total_output": data["total_output"],
                "coverage": round(data["active_users"] / max(data["total_users"], 1) * 100, 1),
                "centers": [{"name": c["name"], "total_tokens": c["total_tokens"], "user_count": c["user_count"], "active_count": c["active_count"]} for c in data["centers"]]}
    if view == "my":
        idx = data.get("_user_index", {}).get(a)
        if not idx: return {"ok": False, "error": f"未找到账号 {a}"}
        tr = len(data["rankings"])
        return {"ok": True, "month": data["month"], "source": data["source"], "account": a,
                "name": idx["name"], "center": idx["center"], "group": idx["group"],
                "total_tokens": idx["total_tokens"], "input_tokens": idx["input_tokens"], "output_tokens": idx["output_tokens"],
                "request_count": idx["request_count"], "has_usage": idx["has_usage"],
                "rank": idx["rank"] if idx["has_usage"] else -1, "total_ranked": tr,
                "percentile": round((1 - idx["rank"] / max(tr, 1)) * 100, 1) if idx["has_usage"] and idx["rank"] > 0 else 0,
                "total_users": data["total_users"]}
    if view == "centers":
        return {"ok": True, "month": data["month"], "source": data["source"],
                "centers": [{"name": c["name"], "total_tokens": c["total_tokens"], "user_count": c["user_count"], "active_count": c["active_count"]} for c in data["centers"]],
                "max_tokens": max((c["total_tokens"] for c in data["centers"]), default=1)}
    if view == "center":
        found = next((c for c in data["centers"] if c["name"] == params.get("name", [""])[0]), None)
        if not found: return {"ok": False, "error": f"未找到中心 {params.get('name', [''])[0]}"}
        return {"ok": True, "center": found, "max_tokens": max((g["total_tokens"] for g in found["groups"]), default=1)}
    if view == "rankings":
        top = int(params.get("top", [20])[0])
        rankings = data["rankings"][:top]
        result = {"ok": True, "month": data["month"], "source": data["source"], "rankings": rankings,
                  "max_tokens": max((r["total_tokens"] for r in rankings), default=1)}
        if a:
            idx = data.get("_user_index", {}).get(a)
            if idx: result["my_rank"] = idx["rank"] if idx["has_usage"] else -1; result["my_total"] = idx["total_tokens"]
        return result
    if view == "groups":
        ag = [{"name": g["name"], "center": c["name"], "total_tokens": g["total_tokens"], "user_count": g["user_count"], "active_count": g["active_count"]}
              for c in data["centers"] for g in c.get("groups", []) if g["name"] and g["user_count"] > 0]
        ag.sort(key=lambda x: x["total_tokens"], reverse=True)
        return {"ok": True, "month": data["month"], "source": data["source"], "groups": ag,
                "max_tokens": max((g["total_tokens"] for g in ag), default=1)}
    return {"ok": False, "error": f"未知视图: {view}"}
