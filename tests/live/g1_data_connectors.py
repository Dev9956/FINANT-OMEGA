"""G1: Real Data Connector Verification — live test script."""

import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import real connectors to trigger self-registration
import core.data.connectors.yfinance_connector  # noqa: F401
import core.data.connectors.sec_edgar_connector  # noqa: F401
import core.data.connectors.fred_connector  # noqa: F401

from core.data.connectors.base import get_connector, ConnectorConfig, list_connectors

print("=" * 60)
print("G1: REAL DATA CONNECTOR VERIFICATION")
print("=" * 60)

results = {}

# --- 1. yfinance_market ---
print("\n--- yfinance_market ---")
config = ConnectorConfig(timeout_seconds=30, max_retries=2)
start = time.perf_counter()
connector = get_connector("yfinance_market", config=config)
health = connector.health_check()
try:
    records = connector.fetch(symbol="AAPL", period="5d", interval="1d")
    elapsed = time.perf_counter() - start
    print(f"  Provider: yfinance_market")
    print(f"  Request: AAPL 5d/1d")
    print(f"  Health: {health}")
    print(f"  Records: {len(records)}")
    if records:
        r = records[0]
        print(f"  Quality: {r.provenance.quality.value}")
        print(f"  Source: {r.provenance.source}")
        print(f"  Provider: {r.provenance.provider}")
        print(f"  Retrieved: {r.provenance.retrieved_at}")
        print(f"  Data keys: {list(r.data.keys())[:8]}")
        # Check for NaN/Inf values
        nan_count = sum(1 for k, v in r.data.items() if isinstance(v, float) and (v != v or v == float('inf') or v == float('-inf')))
        print(f"  NaN/Inf values: {nan_count}")
    print(f"  Latency: {elapsed:.2f}s")
    print(f"  Errors: none")
    results["yfinance_market"] = "PASS"
except Exception as e:
    elapsed = time.perf_counter() - start
    print(f"  Latency: {elapsed:.2f}s")
    print(f"  Errors: {e}")
    results["yfinance_market"] = "FAIL"

# --- 2. yfinance_fundamentals ---
print("\n--- yfinance_fundamentals ---")
start = time.perf_counter()
try:
    connector = get_connector("yfinance_fundamentals", config=config)
    records = connector.fetch(symbol="AAPL")
    elapsed = time.perf_counter() - start
    print(f"  Records: {len(records)}")
    if records:
        print(f"  Quality: {records[0].provenance.quality.value}")
        print(f"  Data keys: {list(records[0].data.keys())[:8]}")
    print(f"  Latency: {elapsed:.2f}s")
    results["yfinance_fundamentals"] = "PASS"
except Exception as e:
    elapsed = time.perf_counter() - start
    print(f"  Latency: {elapsed:.2f}s")
    print(f"  Errors: {e}")
    results["yfinance_fundamentals"] = "FAIL"

# --- 3. SEC EDGAR ---
print("\n--- sec_edgar ---")
start = time.perf_counter()
try:
    connector = get_connector("sec_edgar", config=config)
    health = connector.health_check()
    records = connector.fetch(symbol="AAPL")
    elapsed = time.perf_counter() - start
    print(f"  Health: {health}")
    print(f"  Records: {len(records)}")
    if records:
        print(f"  Quality: {records[0].provenance.quality.value}")
    print(f"  Latency: {elapsed:.2f}s")
    results["sec_edgar"] = "PASS"
except Exception as e:
    elapsed = time.perf_counter() - start
    print(f"  Latency: {elapsed:.2f}s")
    print(f"  Errors: {e}")
    results["sec_edgar"] = "FAIL"

# --- 4. FRED ---
print("\n--- fred ---")
start = time.perf_counter()
try:
    connector = get_connector("fred", config=config)
    health = connector.health_check()
    records = connector.fetch(indicator_name="GDP")
    elapsed = time.perf_counter() - start
    print(f"  Health: {health}")
    print(f"  Records: {len(records)}")
    print(f"  Latency: {elapsed:.2f}s")
    results["fred"] = "PASS"
except Exception as e:
    elapsed = time.perf_counter() - start
    print(f"  Latency: {elapsed:.2f}s")
    print(f"  Errors: {e}")
    results["fred"] = "FAIL"

# --- Summary ---
print("\n" + "=" * 60)
print("RESULTS:")
for name, status in results.items():
    print(f"  {name}: {status}")
pass_count = sum(1 for v in results.values() if v == "PASS")
print(f"\n  {pass_count}/{len(results)} connectors verified")
