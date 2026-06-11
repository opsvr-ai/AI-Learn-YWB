"""Token 统计 — 磁盘缓存 + 后台刷新 + API 视图"""
import json, os, threading, time, traceback, calendar
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import modules.db as db

ROOT = None
AIGW_DB_CONFIG = {
    'host': '7.22.1.162', 'port': 3306, 'user': 'llmdbappusr',
    'password': 'pP1<zW1+', 'database': 'ai_gateway', 'charset': 'utf8mb4',
    'connect_timeout': 10, 'read_timeout': 120, 'write_timeout': 120,
}

def _has_pymysql():
    try: import pymysql; return True
    except: return False

CACHE_FILE = None; _cache_lock = threading.Lock()
_org_account_map = {}

def init(root):
    global ROOT, CACHE_FILE
    ROOT = root; CACHE_FILE = os.path.join(ROOT, 'token_cache.json')
    _load_org()
    # 清理旧格式缓存（单月格式），强制触发后台 DB 刷新
    _migrate_cache_format()

def _migrate_cache_format():
    """清理旧格式缓存文件"""
    if not CACHE_FILE or not os.path.exists(CACHE_FILE): return
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f: d = json.load(f)
        if isinstance(d, dict) and "ts" in d and "data" in d:
            # 旧单月格式 → 删除，触发全量重建
            os.remove(CACHE_FILE)
            print("[Token] 已清理旧格式缓存，下次访问将触发 DB 刷新")
    except: pass

def _load_org():
    global _org_account_map
    org = {}
    csv_path = os.path.join(ROOT, 'ywb-users.csv')
    if not os.path.exists(csv_path): return
    try:
        import csv
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            for row in csv.reader(f):
                if row[0] == '序号': continue
                if len(row) < 6: continue
                n, a, c, g = (row[1] or '').strip(), (row[2] or '').strip(), (row[3] or '').strip(), (row[4] or '').strip()
                if not a: continue
                _org_account_map[a] = {"name": n, "center": c, "group": g}
        print(f"[Token] ywb-users.csv: {len(_org_account_map)} 人")
    except Exception as e: print(f"[Token] CSV 加载失败: {e}")

def _extract_username(c): return c.split('_')[0] if '_' in c else c

def _fetch_one_day(day_start, day_end):
    """查询单天明细（无聚合），异常时返回 []"""
    import pymysql
    try:
        conn = pymysql.connect(**AIGW_DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT ai_consumer, input_tokens, output_tokens, request_count FROM ai_metrics WHERE time_bucket>=%s AND time_bucket<%s", (day_start, day_end))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows
    except Exception as e:
        print(f"[Token] 单天查询失败 {day_start}: {e}", flush=True)
        return []

def _fetch(month):
    """分天并发查询 + Python 端聚合"""
    if not _has_pymysql():
        print("[Token] pymysql 未安装，跳过 DB 查询", flush=True)
        return None
    y, m = map(int, month.split('-'))
    days = calendar.monthrange(y, m)[1]
    print(f"[Token] 后台分天查询 {month} (共 {days} 天, 7 线程并发)", flush=True)
    t0 = time.time()
    consumers = {}
    total_rows = 0
    try:
        with ThreadPoolExecutor(max_workers=7) as pool:
            futures = {}
            for d in range(1, days + 1):
                ds = f"{y}-{m:02d}-{d:02d} 00:00:00"
                de = f"{y}-{m:02d}-{d+1:02d} 00:00:00" if d < days else f"{y+(m//12)}-{(m%12)+1:02d}-01 00:00:00"
                futures[pool.submit(_fetch_one_day, ds, de)] = d
            for future in as_completed(futures):
                day = futures[future]
                try:
                    rows = future.result()
                except Exception as e:
                    print(f"[Token] day {day:2d} 线程异常: {e}", flush=True); traceback.print_exc()
                    rows = []
                day_rows = len(rows)
                total_rows += day_rows
                for c, inp, out, req in rows:
                    u = _extract_username(c)
                    dct = consumers.setdefault(u, {"input_tokens": 0, "output_tokens": 0, "request_count": 0})
                    dct["input_tokens"] += inp or 0
                    dct["output_tokens"] += out or 0
                    dct["request_count"] += req or 0
                print(f"[Token] day {day:2d} ✓ {day_rows:>8} 行, 累计 {total_rows:>9} 行, {len(consumers)} 用户", flush=True)
        elapsed = time.time() - t0
        print(f"[Token] 分天聚合完成: {total_rows} 行 -> {len(consumers)} 用户, {elapsed:.1f}s", flush=True)
        return consumers if consumers else None
    except Exception as e:
        print(f"[Token] 分天查询整体失败: {e}", flush=True); traceback.print_exc()
        return None

def _build(consumers, month):
    flat = []
    for a, info in _org_account_map.items():
        u = consumers.get(a, {"input_tokens": 0, "output_tokens": 0, "request_count": 0})
        t = u["input_tokens"] + u["output_tokens"]
        flat.append({"account": a, "name": info["name"], "center": info["center"], "group": info["group"],
                      "input_tokens": u["input_tokens"], "output_tokens": u["output_tokens"],
                      "request_count": u["request_count"], "total_tokens": t, "has_usage": t > 0})
    if not flat: return None
    flat.sort(key=lambda x: x["total_tokens"], reverse=True)
    return _package(month, "db", flat)

def _build_json_fallback(month):
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

def _cache_get(month):
    if not CACHE_FILE or not os.path.exists(CACHE_FILE): return None
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f: d = json.load(f)
        slot = d.get(month) if isinstance(d, dict) else None
        if slot:
            src = slot.get("data", {}).get("source", "")
            ttl = 3600 if src == "json" else 86400  # JSON兜底 1h 过期，DB 数据 24h
            if (time.time() - slot.get("ts", 0)) < ttl:
                return slot.get("data")
        if isinstance(d, dict) and not slot:
            if d.get("month") == month and (time.time() - d.get("ts", 0)) < 86400:
                return d.get("data")
        return None
    except: return None

def _get_stale(month):
    """返回过期的旧数据（任意月份），用于stale-while-revalidate"""
    if not CACHE_FILE or not os.path.exists(CACHE_FILE): return None
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f: d = json.load(f)
        if isinstance(d, dict) and "ts" in d and "data" in d:
            return d.get("data")  # 旧格式
        return None
    except: return None

def _cache_put(data):
    month = data["month"]
    all_cache = {}
    if CACHE_FILE and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f: all_cache = json.load(f)
        except: all_cache = {}
    # 兼容旧格式 → 转新格式
    if not isinstance(all_cache, dict) or ("ts" in all_cache and "data" in all_cache):
        all_cache = {}
    all_cache[month] = {"ts": time.time(), "data": data}
    # 只保留最近 3 个月
    keys = sorted(all_cache.keys(), reverse=True)[:3]
    trimmed = {k: all_cache[k] for k in keys}
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(trimmed, f, ensure_ascii=False)

def _bg_refresh(month):
    """后台线程刷新磁盘缓存"""
    print(f"[Token] 后台刷新线程启动: month={month}", flush=True)
    try:
        consumers = _fetch(month)
        if consumers is None:
            print(f"[Token] 后台刷新: _fetch 返回 None（DB不可达或无pymysql）", flush=True)
            return
        data = _build(consumers, month)
        if data:
            _cache_put(data)
            print(f"[Token] 磁盘缓存已更新: {data['month']} source=db users={data['total_users']}", flush=True)
        else:
            print(f"[Token] 后台刷新: _build 返回 None", flush=True)
    except Exception as e:
        print(f"[Token] 后台刷新异常: {e}", flush=True); traceback.print_exc()

def get(view, params):
    month = params.get("month", [date.today().strftime("%Y-%m")])[0]

    # 1) 精准命中
    data = _cache_get(month)
    if data:
        print(f"[Token] 磁盘缓存命中 {month}", flush=True)
        return _serve(view, data, params)

    # 2) stale-while-revalidate：返回旧月数据（如果存在）+ 后台刷新
    stale = _get_stale(month)
    threading.Thread(target=_bg_refresh, args=(month,), daemon=True).start()
    if stale:
        print(f"[Token] 缓存过期，返回旧数据 + 后台刷新 {month}", flush=True)
        return _serve(view, stale, params)

    # 3) JSON 兜底
    print(f"[Token] 无缓存 {month}，JSON 兜底 + 后台刷新", flush=True)
    data = _build_json_fallback(month)
    if data is None:
        return {"ok": False, "error": "数据不可用"}
    _cache_put(data)
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
