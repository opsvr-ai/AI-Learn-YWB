#!/usr/bin/env python3
"""测试 MySQL 连接 + Token 聚合查询 — 独立运行，不依赖 server.py"""
import time
import traceback

# 1) 检查 pymysql 是否安装
try:
    import pymysql
    print("✅ pymysql 已安装", flush=True)
except ImportError:
    print("❌ pymysql 未安装  →  pip install pymysql", flush=True)
    exit(1)

# 2) 链接数据库配置（与 server.py/AIGW_DB_CONFIG 完全一致）
import socket
config = {
    'host': '7.22.1.162',
    'port': 3306,
    'user': 'llmdbappusr',
    'password': 'pP1<zW1+',
    'database': 'ai_gateway',
    'charset': 'utf8mb4',
    'connect_timeout': 10,
    'read_timeout': 60,
}

# ── 阶段 1：连接测试 ──
print("=" * 60, flush=True)
print("阶段 1：连接 MySQL ...", flush=True)
t0 = time.time()
try:
    conn = pymysql.connect(**config)
    sock = conn.socket
    if sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        for opt, name in [(socket.TCP_KEEPIDLE, 'TCP_KEEPIDLE'), (socket.TCP_KEEPINTVL, 'TCP_KEEPINTVL'), (socket.TCP_KEEPCNT, 'TCP_KEEPCNT')]:
            if hasattr(socket, name):
                try:
                    sock.setsockopt(socket.IPPROTO_TCP, opt, 30 if 'IDLE' in name else 10 if 'INTVL' in name else 5)
                except Exception:
                    pass
    print(f"✅ 连接成功，耗时 {(time.time() - t0):.1f}s", flush=True)
except Exception:
    print(f"❌ 连接失败，耗时 {(time.time() - t0):.1f}s", flush=True)
    traceback.print_exc()
    exit(1)

# ── 阶段 2：基本读权限测试 ──
print("")
print("=" * 60, flush=True)
print("阶段 2：检查表是否存在 ...", flush=True)
try:
    cur = conn.cursor()
    cur.execute("SHOW TABLES LIKE 'ai_metrics'")
    row = cur.fetchone()
    cur.close()
    if row:
        print(f"✅ ai_metrics 表存在", flush=True)
    else:
        print("❌ ai_metrics 表不存在！", flush=True)
        conn.close()
        exit(1)
except Exception:
    print("❌ SHOW TABLES 失败", flush=True)
    traceback.print_exc()
    conn.close()
    exit(1)

# ── 阶段 3：小范围聚合测试（只查 1 天数据） ──
print("")
print("=" * 60, flush=True)
print("阶段 3：聚合查询（只查 1 天，验证 SQL）...", flush=True)
try:
    t0 = time.time()
    cur = conn.cursor()
    cur.execute("""
        SELECT ai_consumer,
               COALESCE(SUM(input_tokens), 0) as input_tokens,
               COALESCE(SUM(output_tokens), 0) as output_tokens,
               COALESCE(SUM(request_count), 0) as request_count
        FROM ai_metrics
        WHERE time_bucket >= '2026-06-01 00:00:00' AND time_bucket < '2026-06-02 00:00:00'
        GROUP BY ai_consumer
    """)
    rows = cur.fetchall()
    elapsed = time.time() - t0
    cur.close()
    print(f"✅ 1 天聚合完成，耗时 {elapsed:.1f}s，{len(rows)} 条记录", flush=True)
    if rows:
        print(f"   样例: {rows[:3]}", flush=True)
except Exception:
    print(f"❌ 聚合查询失败，耗时 {(time.time() - t0):.1f}s", flush=True)
    traceback.print_exc()
    conn.close()
    exit(1)

# ── 阶段 4：全月聚合测试 ──
print("")
print("=" * 60, flush=True)
print("阶段 4：全月聚合查询（2026-06 整月）...", flush=True)
print("（此阶段可能较慢，请耐心等待...）", flush=True)
try:
    t0 = time.time()
    cur = conn.cursor()
    cur.execute("""
        SELECT ai_consumer,
               COALESCE(SUM(input_tokens), 0) as input_tokens,
               COALESCE(SUM(output_tokens), 0) as output_tokens,
               COALESCE(SUM(request_count), 0) as request_count
        FROM ai_metrics
        WHERE time_bucket >= '2026-06-01 00:00:00' AND time_bucket < '2026-07-01 00:00:00'
        GROUP BY ai_consumer
    """)
    rows = cur.fetchall()
    elapsed = time.time() - t0
    cur.close()
    print(f"✅ 全月聚合完成，耗时 {elapsed:.1f}s，{len(rows)} 条记录（{len(set(r[0].split('_')[0] for r in rows if '_' in str(r[0]))|{r[0] for r in rows if '_' not in str(r[0])})} 个去重用户）", flush=True)
except Exception:
    print(f"❌ 全月聚合失败，耗时 {(time.time() - t0):.1f}s", flush=True)
    traceback.print_exc()

conn.close()
print("")
print("=" * 60, flush=True)
print("测试完成", flush=True)
