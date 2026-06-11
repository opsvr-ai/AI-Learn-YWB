#!/usr/bin/env python3
"""MySQL connection test script for ai_gateway database."""

import pymysql
from pymysql.cursors import DictCursor

DB_CONFIG = {
    'host': '7.22.1.162',
    'port': 3306,
    'user': 'llmdbappusr',
    'password': 'pP1<zW1+',
    'database': 'ai_gateway',
    'charset': 'utf8mb4',
    'connect_timeout': 10,
    'read_timeout': 300,
    'write_timeout': 300,
}


def test_connection():
    """Test MySQL connection and run sample queries."""
    print("=" * 60)
    print("MySQL Connection Test")
    print("=" * 60)
    print(f"Host:     {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"User:     {DB_CONFIG['user']}")
    print()

    # 1. Test basic connection
    print("[1] Testing connection...")
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("    Connection established successfully!")
    except pymysql.MySQLError as e:
        print(f"    Connection FAILED: {e}")
        return
    except Exception as e:
        print(f"    Unexpected error: {e}")
        return

    # 2. Server info
    print("\n[2] Server info:")
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            version = cur.fetchone()[0]
            print(f"    MySQL Version: {version}")
    except pymysql.MySQLError as e:
        print(f"    Query failed: {e}")

    # 3. List tables
    print("\n[3] Tables in 'ai_gateway':")
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            tables = cur.fetchall()
            if tables:
                for t in tables:
                    print(f"    - {t[0]}")
                print(f"    Total: {len(tables)} tables")
            else:
                print("    (no tables found)")
    except pymysql.MySQLError as e:
        print(f"    Query failed: {e}")

    # 4. Sample query — show first 5 rows from the first table
    print("\n[4] Sample data query:")
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            tables = cur.fetchall()
            if tables:
                first_table = tables[0][0]
                cur.execute(f"SELECT * FROM `{first_table}` LIMIT 5")
                rows = cur.fetchall()
                cols = [desc[0] for desc in cur.description]
                print(f"    Table: {first_table} (columns: {', '.join(cols)})")
                if rows:
                    for row in rows:
                        print(f"    {row}")
                else:
                    print("    (empty table)")
            else:
                print("    No tables to query")
    except pymysql.MySQLError as e:
        print(f"    Query failed: {e}")

    # 5. Database size info
    print("\n[5] Database size:")
    try:
        with conn.cursor(DictCursor) as cur:
            cur.execute("""
                SELECT table_name AS `table`,
                       table_rows AS `rows`,
                       ROUND(data_length / 1024 / 1024, 2) AS `data_MB`,
                       ROUND(index_length / 1024 / 1024, 2) AS `index_MB`
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY data_length DESC
                LIMIT 10
            """, (DB_CONFIG['database'],))
            results = cur.fetchall()
            if results:
                print(f"    {'Table':<40} {'Rows':>10} {'Data(MB)':>10} {'Index(MB)':>10}")
                print(f"    {'-'*40} {'-'*10} {'-'*10} {'-'*10}")
                for r in results:
                    print(f"    {r['table']:<40} {r['rows']:>10} {r['data_MB']:>10} {r['index_MB']:>10}")
            else:
                print("    (no table info available)")
    except pymysql.MySQLError as e:
        print(f"    Query failed: {e}")

    conn.close()
    print("\n" + "=" * 60)
    print("Connection test completed. Connection closed.")
    print("=" * 60)


if __name__ == '__main__':
    test_connection()
