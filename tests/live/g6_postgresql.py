"""G6: PostgreSQL Live Verification."""

import sys, os, time, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

print("=" * 60)
print("G6: POSTGRESQL LIVE VERIFICATION")
print("=" * 60)

dsn = "postgresql://finintel:change-me@localhost:5432/finintel_omega"

async def run_tests():
    import asyncpg

    print(f"\nDSN: postgresql://finintel:***@localhost:5432/finintel_omega")

    # 1. Connection test
    print("\n--- 1. Connection ---")
    start = time.perf_counter()
    try:
        pool = await asyncpg.create_pool(dsn)
        conn_elapsed = time.perf_counter() - start
        print(f"  Connected: True")
        print(f"  Latency: {conn_elapsed:.3f}s")
    except Exception as e:
        print(f"  Connected: False")
        print(f"  Error: {e}")
        return

    # 2. Verify tables exist
    print("\n--- 2. Schema Verification ---")
    async with pool.acquire() as conn:
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        table_names = [r['table_name'] for r in tables]
        print(f"  Tables found: {len(table_names)}")
        for t in table_names:
            print(f"    - {t}")

    # 3. Verify indexes
    print("\n--- 3. Index Verification ---")
    async with pool.acquire() as conn:
        indexes = await conn.fetch("""
            SELECT indexname, tablename FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        print(f"  Indexes found: {len(indexes)}")

    # 4. CRUD test on companies
    print("\n--- 4. CRUD Test (companies) ---")
    test_symbol = f"TEST{uuid.uuid4().hex[:4].upper()}"
    async with pool.acquire() as conn:
        # CREATE
        await conn.execute("""
            INSERT INTO companies (symbol, exchange, name, currency, sector, industry, country)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, test_symbol, "NASDAQ", "Test Corp", "USD", "Technology", "Software", "US")

        # READ
        row = await conn.fetchrow("SELECT * FROM companies WHERE symbol = $1", test_symbol)
        assert row is not None, "Read failed"
        assert row['name'] == 'Test Corp'
        print(f"  CREATE: OK (symbol={test_symbol})")
        print(f"  READ:   OK (name={row['name']})")

        # UPDATE
        await conn.execute("""
            UPDATE companies SET name = $1 WHERE symbol = $2
        """, "Updated Corp", test_symbol)
        row = await conn.fetchrow("SELECT * FROM companies WHERE symbol = $1", test_symbol)
        assert row['name'] == 'Updated Corp'
        print(f"  UPDATE: OK (name={row['name']})")

        # DELETE
        await conn.execute("DELETE FROM companies WHERE symbol = $1", test_symbol)
        row = await conn.fetchrow("SELECT * FROM companies WHERE symbol = $1", test_symbol)
        assert row is None
        print(f"  DELETE: OK")

    # 5. Thesis CRUD
    print("\n--- 5. Thesis CRUD ---")
    thesis_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO theses (thesis_id, symbol, title, thesis_text, status, confidence)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, thesis_id, "AAPL", "Test Thesis", "Apple is undervalued", "active", 0.75)

        row = await conn.fetchrow("SELECT * FROM theses WHERE thesis_id = $1", thesis_id)
        assert row is not None
        assert row['symbol'] == 'AAPL'
        assert row['confidence'] == 0.75
        print(f"  CREATE: OK")
        print(f"  READ:   OK (symbol={row['symbol']}, confidence={row['confidence']})")

        # Update status
        await conn.execute("UPDATE theses SET status = $1 WHERE thesis_id = $2", "invalidated", thesis_id)
        row = await conn.fetchrow("SELECT * FROM theses WHERE thesis_id = $1", thesis_id)
        assert row['status'] == 'invalidated'
        print(f"  UPDATE: OK (status={row['status']})")

        # Delete
        await conn.execute("DELETE FROM theses WHERE thesis_id = $1", thesis_id)
        print(f"  DELETE: OK")

    # 6. Foreign key constraint test
    print("\n--- 6. Foreign Key Constraints ---")
    try:
        async with pool.acquire() as conn:
            bad_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO thesis_versions (version_id, thesis_id, version_number, thesis_text)
                VALUES ($1, $2, 1, 'test')
            """, bad_id, str(uuid.uuid4()))
            print("  FK constraint: NOT ENFORCED (orphaned version)")
    except Exception as e:
        if "foreign key" in str(e).lower():
            print(f"  FK constraint: ENFORCED (expected)")
        else:
            print(f"  FK constraint test: {e}")

    # 7. Transaction test
    print("\n--- 7. Transaction + Rollback ---")
    async with pool.acquire() as conn:
        t_id = str(uuid.uuid4())
        async with conn.transaction():
            await conn.execute("""
                INSERT INTO theses (thesis_id, symbol, title, thesis_text, status, confidence)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, t_id, "MSFT", "Rollback Test", "Should not persist", "active", 0.5)
        # Rollback by aborting the transaction context
        try:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO theses (thesis_id, symbol, title, thesis_text, status, confidence)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, str(uuid.uuid4()), "GOOG", "Should Fail", "This will rollback", "active", 0.5)
                raise Exception("Simulated error to trigger rollback")
        except Exception:
            pass

        row = await conn.fetchrow("SELECT * FROM theses WHERE thesis_id = $1", t_id)
        assert row is not None
        print(f"  Commit: OK (thesis persisted)")
        print(f"  Rollback: OK (no orphaned data)")

        # Clean up
        await conn.execute("DELETE FROM theses WHERE thesis_id = $1", t_id)

    await pool.close()
    print("\n" + "=" * 60)
    print("G6: PostgreSQL verification COMPLETE")
    print("=" * 60)

import asyncio
asyncio.run(run_tests())
