"""
数据库迁移脚本：将生产环境数据库结构对齐到开发环境
====================================================
用途：生产库缺少 user_fingerprints 表，需要补建。
      其余表（visits/checkins/help_requests）结构一致，无需变更。

用法：python migrate_db.py <数据库文件路径>
示例：python migrate_db.py .visit_stats.db

安全：所有操作使用 IF NOT EXISTS，可重复执行，不会丢失数据。
"""

import sqlite3
import sys
import os
from datetime import datetime


def migrate(db_path: str, dry_run: bool = False) -> dict:
    """
    执行迁移，返回 {操作: 结果} 的字典。
    dry_run=True 时只检查不执行。
    """
    results = {}

    print(f"数据库: {db_path}")
    print(f"时间: {datetime.now().isoformat()}")
    print(f"模式: {'试运行（不修改）' if dry_run else '执行迁移'}")
    print("-" * 50)

    conn = sqlite3.connect(db_path)

    # 1. 检查当前状态
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    existing_tables = [r[0] for r in cur.fetchall()]
    print(f"现有表: {existing_tables}")

    # 2. 检查 user_fingerprints 表是否存在
    if 'user_fingerprints' in existing_tables:
        # 已存在，检查列是否齐全
        cur = conn.execute("PRAGMA table_info(user_fingerprints)")
        cols = {r[1] for r in cur.fetchall()}
        expected = {'fingerprint', 'account', 'updated'}
        missing_cols = expected - cols
        if missing_cols:
            results['user_fingerprints'] = f'表存在但缺列: {missing_cols}'
        else:
            results['user_fingerprints'] = '已存在，无需迁移'
    else:
        if not dry_run:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_fingerprints (
                    fingerprint TEXT PRIMARY KEY,
                    account TEXT NOT NULL,
                    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            results['user_fingerprints'] = '已创建'
        else:
            results['user_fingerprints'] = '缺失（试运行）'

    # 3. 验证其他表结构（只读检查，不做修改）
    expected_schemas = {
        'visits': {'id', 'page', 'visit_date', 'created_at'},
        'checkins': {'id', 'checkin_date', 'created_at', 'user', 'fingerprint'},
        'help_requests': {'id', 'request_date', 'user', 'fingerprint', 'page', 'created_at'},
    }

    for table, expected_cols in expected_schemas.items():
        if table not in existing_tables:
            results[table] = '表不存在!'
            continue
        cur = conn.execute(f"PRAGMA table_info({table})")
        actual_cols = {r[1] for r in cur.fetchall()}
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cur.fetchone()[0]
        if actual_cols == expected_cols:
            results[table] = f'结构一致，{row_count} 行数据'
        else:
            extra = actual_cols - expected_cols
            missing = expected_cols - actual_cols
            parts = [f'{row_count} 行数据']
            if extra:
                parts.append(f'多余列: {extra}')
            if missing:
                parts.append(f'缺失列: {missing}')
            results[table] = '; '.join(parts)

    # 4. 检查索引
    expected_indexes = {'idx_visits_date', 'idx_checkins_date', 'idx_help_date'}
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
    existing_indexes = {r[0] for r in cur.fetchall()}
    for idx in expected_indexes:
        if idx not in existing_indexes:
            results[f'索引 {idx}'] = '缺失'
        else:
            results[f'索引 {idx}'] = '存在'

    if not dry_run:
        conn.commit()
    conn.close()

    # 打印结果
    print()
    for op, result in results.items():
        icon = "[OK]" if ('一致' in result or '存在' in result or '已创建' in result) else "[!!]"
        print(f"  {icon} {op}: {result}")
    print("-" * 50)

    all_ok = all(
        ('一致' in v or '存在' in v or '已创建' in v)
        for v in results.values()
    )
    if all_ok:
        print("迁移完成，数据库结构与开发环境一致。")
    else:
        print("存在差异项，请检查上述标记为 ✗ 的项目。")

    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python migrate_db.py <数据库文件路径> [--dry-run]")
        print("示例: python migrate_db.py .visit_stats.db")
        print("      python migrate_db.py /path/to/production.db --dry-run")
        sys.exit(1)

    db_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    if not os.path.exists(db_path):
        print(f"错误: 文件不存在 - {db_path}")
        sys.exit(1)

    migrate(db_path, dry_run=dry_run)
