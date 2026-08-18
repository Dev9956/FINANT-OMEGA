"""G7: ClickHouse Live Verification."""

import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

print("=" * 60)
print("G7: CLICKHOUSE LIVE VERIFICATION")
print("=" * 60)

import clickhouse_connect

start = time.perf_counter()
client = clickhouse_connect.get_client(host='localhost', port=8123, database='finintel_omega', username='default', password='clickhouse_dev')
connect_elapsed = time.perf_counter() - start
print(f"\nConnection: {'OK' if client else 'FAIL'}")
print(f"Latency: {connect_elapsed:.3f}s")

# 1. Check database
print("\n--- 1. Database ---")
result = client.query("SELECT currentDatabase()")
print(f"  Current DB: {result.result_rows[0][0]}")

# 2. List tables
print("\n--- 2. Tables ---")
result = client.query("SHOW TABLES FROM finintel_omega")
tables = [r[0] for r in result.result_rows]
print(f"  Tables: {len(tables)}")
for t in tables:
    print(f"    - {t}")

# 3. Create test table and insert
print("\n--- 3. Insert + Query ---")
client.command("""
    CREATE TABLE IF NOT EXISTS finintel_omega.live_test (
        symbol String,
        date Date,
        close Float64,
        volume UInt64
    ) ENGINE = MergeTree()
    ORDER BY (symbol, date)
""")

# Insert test data
from datetime import date
test_data = [
    ("AAPL", date(2026, 8, 17), 308.26, 44812500),
    ("MSFT", date(2026, 8, 17), 450.12, 22000000),
    ("GOOGL", date(2026, 8, 17), 175.50, 18000000),
]
client.insert("live_test", test_data, column_names=["symbol", "date", "close", "volume"])
print(f"  Inserted: {len(test_data)} rows")

# Query
result = client.query("SELECT symbol, close, volume FROM finintel_omega.live_test ORDER BY symbol")
print(f"  Queried: {len(result.result_rows)} rows")
for r in result.result_rows:
    print(f"    {r[0]}: close={r[1]}, volume={r[2]}")

# 4. Aggregation
print("\n--- 4. Aggregation ---")
result = client.query("""
    SELECT symbol, avg(close) as avg_close, sum(volume) as total_volume
    FROM finintel_omega.live_test
    GROUP BY symbol
    ORDER BY symbol
""")
for r in result.result_rows:
    print(f"    {r[0]}: avg_close={r[1]:.2f}, total_volume={r[2]}")

# 5. Date range filter
print("\n--- 5. Date Range Filter ---")
result = client.query("""
    SELECT count(*) FROM finintel_omega.live_test
    WHERE date >= '2026-08-01' AND date <= '2026-08-31'
""")
print(f"  Records in Aug 2026: {result.result_rows[0][0]}")

# 6. Concurrent reads
print("\n--- 6. Concurrent Reads ---")
import concurrent.futures
def query_fn(_):
    c = clickhouse_connect.get_client(host='localhost', port=8123, database='finintel_omega', username='default', password='clickhouse_dev')
    return c.query("SELECT count(*) FROM finintel_omega.live_test").result_rows[0][0]

start = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(query_fn, i) for i in range(100)]
    results_list = [f.result() for f in futures]
concurrent_elapsed = time.perf_counter() - start
print(f"  100 concurrent reads: {concurrent_elapsed:.3f}s")
assert all(r == 3 for r in results_list)

# 7. Performance
print("\n--- 7. Performance ---")
start = time.perf_counter()
for _ in range(100):
    client.query("SELECT * FROM finintel_omega.live_test WHERE symbol = 'AAPL'")
perf_elapsed = time.perf_counter() - start
print(f"  100 filtered queries: {perf_elapsed:.3f}s ({perf_elapsed/100*1000:.1f}ms avg)")

# Cleanup
client.command("DROP TABLE IF EXISTS finintel_omega.live_test")
print("\n  Cleanup: OK")

print("\n" + "=" * 60)
print("G7: ClickHouse verification COMPLETE")
print("=" * 60)
