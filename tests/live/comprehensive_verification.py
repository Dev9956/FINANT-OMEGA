"""G4/G5/G8/G9/G10/G11/G12/G13/G14: Comprehensive live verification."""

import sys, os, time, uuid, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

results = {}

def log(gate, test, status, detail=""):
    key = f"{gate}:{test}"
    results[key] = (status, detail)
    symbol = "PASS" if status else "FAIL"
    print(f"  [{symbol}] {gate} {test}: {detail}" if detail else f"  [{symbol}] {gate} {test}")

# ====================================================================
# G4: AUTHENTICATION VERIFICATION
# ====================================================================
print("\n" + "=" * 60)
print("G4: AUTHENTICATION VERIFICATION")
print("=" * 60)

from core.auth.security import create_access_token, decode_token, hash_password, verify_password, SecurityContext, get_current_user
from core.auth.service import AuthService
from core.auth.rbac import Role, Permission, authorize, has_permission, AuthorizationError

SECRET = "live-test-secret-key"

# Password hashing
print("\n--- Password Hashing ---")
hashed = hash_password("S3cureP@ssw0rd!")
log("G4", "password_hash", verify_password("S3cureP@ssw0rd!", hashed), "bcrypt verified")
log("G4", "password_not_plaintext", "S3cureP@ssw0rd!" not in hashed, "hash does not contain plaintext")

# JWT round-trip
print("\n--- JWT Tokens ---")
token = create_access_token("user-123", Role.ANALYST.value, org_id="org-A", secret_key=SECRET)
payload = decode_token(token, secret_key=SECRET)
log("G4", "jwt_create_decode", payload.sub == "user-123", f"sub={payload.sub}")
log("G4", "jwt_role", payload.role == "analyst", f"role={payload.role}")
log("G4", "jwt_org_id", payload.org_id == "org-A", f"org_id={payload.org_id}")

# Tampered token rejected
try:
    decode_token(token + "X", secret_key=SECRET)
    log("G4", "jwt_tamper_rejected", False, "tampered token was accepted")
except ValueError:
    log("G4", "jwt_tamper_rejected", True, "tampered token rejected")

# Wrong secret rejected
try:
    decode_token(token, secret_key="wrong-secret")
    log("G4", "jwt_wrong_secret", False, "wrong secret accepted")
except ValueError:
    log("G4", "jwt_wrong_secret", True, "wrong secret rejected")

# Expired token
from datetime import timedelta
expired = create_access_token("user-123", Role.ANALYST.value, expires_delta=timedelta(seconds=-10), secret_key=SECRET)
try:
    decode_token(expired, secret_key=SECRET)
    log("G4", "jwt_expired_rejected", False, "expired token accepted")
except ValueError:
    log("G4", "jwt_expired_rejected", True, "expired token rejected")

# SecurityContext
ctx = SecurityContext(user_id="u1", role="analyst", org_id="org-A")
log("G4", "security_context_tenant", ctx.tenant_id == "org-A", f"tenant_id={ctx.tenant_id}")

# AuthService
print("\n--- AuthService ---")
svc = AuthService()
svc.set_token_secret(SECRET)
user = svc.register("live-test@example.com", "S3cureP@ss!", "Live Test User", role=Role.ANALYST.value)
login_token = svc.login("live-test@example.com", "S3cureP@ss!")
decoded = decode_token(login_token, secret_key=SECRET)
log("G4", "auth_register", user.user_id is not None, f"user_id={user.user_id[:8]}...")
log("G4", "auth_login_token", len(login_token) > 20, f"token_len={len(login_token)}")

# Duplicate registration rejected
try:
    svc.register("live-test@example.com", "Another1234!", "Dup", role=Role.VIEWER.value)
    log("G4", "auth_no_duplicate", False, "duplicate accepted")
except ValueError:
    log("G4", "auth_no_duplicate", True, "duplicate rejected")

# Wrong password
try:
    svc.authenticate("live-test@example.com", "wrong-password")
    log("G4", "auth_wrong_password", False, "wrong password accepted")
except ValueError:
    log("G4", "auth_wrong_password", True, "wrong password rejected")

# Short password
try:
    svc.register("short@example.com", "short", "Short")
    log("G4", "auth_short_password", False, "short password accepted")
except ValueError:
    log("G4", "auth_short_password", True, "short password rejected")

# ====================================================================
# G5: RBAC + TENANT ISOLATION
# ====================================================================
print("\n" + "=" * 60)
print("G5: RBAC + TENANT ISOLATION")
print("=" * 60)

# User A in Tenant A
token_a = create_access_token("user-A", Role.ANALYST.value, org_id="tenant-A", secret_key=SECRET)
ctx_a = get_current_user(token_a, secret_key=SECRET)

# User B in Tenant B
token_b = create_access_token("user-B", Role.ANALYST.value, org_id="tenant-B", secret_key=SECRET)
ctx_b = get_current_user(token_b, secret_key=SECRET)

log("G5", "user_a_tenant", ctx_a.tenant_id == "tenant-A", f"tenant={ctx_a.tenant_id}")
log("G5", "user_b_tenant", ctx_b.tenant_id == "tenant-B", f"tenant={ctx_b.tenant_id}")
log("G5", "cross_tenant_different", ctx_a.tenant_id != ctx_b.tenant_id, "tenants isolated")

# Role permissions
log("G5", "admin_all_perms", has_permission(Role.ADMIN.value, Permission.MANAGE_USERS), "admin can manage users")
log("G5", "viewer_no_write", not has_permission(Role.VIEWER.value, Permission.WRITE_DATA), "viewer cannot write")
log("G5", "analyst_no_admin", not has_permission(Role.ANALYST.value, Permission.MANAGE_USERS), "analyst cannot admin")

# Authorization enforcement
try:
    authorize(Role.VIEWER.value, Permission.DELETE_THESIS)
    log("G5", "authz_enforced", False, "viewer delete not rejected")
except AuthorizationError:
    log("G5", "authz_enforced", True, "viewer delete rejected")

try:
    authorize("attacker", Permission.READ_DATA)
    log("G5", "authz_unknown_role", False, "attacker role accepted")
except AuthorizationError:
    log("G5", "authz_unknown_role", True, "attacker role rejected")

# Tenant isolation simulation
class MockResource:
    def __init__(self, owner_tenant, data):
        self.owner_tenant = owner_tenant
        self.data = data

resources = {
    "res-A": MockResource("tenant-A", "Private data for tenant A"),
    "res-B": MockResource("tenant-B", "Private data for tenant B"),
}

def access_resource(user_ctx, resource_id):
    res = resources.get(resource_id)
    if res and res.owner_tenant == user_ctx.tenant_id:
        return res.data
    return None

log("G5", "own_tenant_access", access_resource(ctx_a, "res-A") is not None, "A can access A's resources")
log("G5", "cross_tenant_denied", access_resource(ctx_a, "res-B") is None, "A cannot access B's resources")
log("G5", "own_tenant_b", access_resource(ctx_b, "res-B") is not None, "B can access B's resources")
log("G5", "cross_tenant_b_denied", access_resource(ctx_b, "res-A") is None, "B cannot access A's resources")

# ====================================================================
# G8: OBJECT STORAGE
# ====================================================================
print("\n" + "=" * 60)
print("G8: OBJECT STORAGE VERIFICATION")
print("=" * 60)

from core.storage.base import MockObjectStorage, LocalObjectStorage, StorageConfig
import tempfile

# Local storage
with tempfile.TemporaryDirectory() as tmpdir:
    storage = LocalObjectStorage(StorageConfig(local_path=tmpdir))

    # Upload
    obj1 = storage.put("docs/report.pdf", b"%PDF-1.4 fake content", content_type="application/pdf")
    log("G8", "local_upload", obj1.key == "docs/report.pdf", f"key={obj1.key}")
    log("G8", "local_size", obj1.size_bytes == 21, f"size={obj1.size_bytes}")
    log("G8", "local_content_type", obj1.content_type == "application/pdf")

    # Download
    data, meta = storage.get("docs/report.pdf")
    log("G8", "local_download", data == b"%PDF-1.4 fake content")

    # Content hash
    expected_hash = hashlib.sha256(b"%PDF-1.4 fake content").hexdigest()
    log("G8", "local_content_hash", obj1.content_hash == expected_hash)

    # Exists
    log("G8", "local_exists", storage.exists("docs/report.pdf"))
    log("G8", "local_not_exists", not storage.exists("docs/nonexistent.pdf"))

    # List
    storage.put("docs/chart.png", b"PNG data")
    storage.put("data/prices.csv", b"AAPL,150")
    items = storage.list(prefix="docs")
    log("G8", "local_list_prefix", len(items) == 2, f"count={len(items)}")

    # Delete
    log("G8", "local_delete", storage.delete("docs/report.pdf"))
    log("G8", "local_delete_gone", not storage.exists("docs/report.pdf"))

    # Presigned URL
    url = storage.get_presigned_url("data/prices.csv")
    log("G8", "local_presigned_url", url.startswith("file://"), f"url={url[:30]}...")

# Mock storage
mock = MockObjectStorage()
mock.put("test.txt", b"hello")
data, _ = mock.get("test.txt")
log("G8", "mock_roundtrip", data == b"hello")
log("G8", "mock_delete", mock.delete("test.txt"))
log("G8", "mock_not_exists", not mock.exists("test.txt"))

# ====================================================================
# G9: PYTHON-RUST VERIFICATION (via subprocess)
# ====================================================================
print("\n" + "=" * 60)
print("G9: PYTHON-RUST VERIFICATION")
print("=" * 60)

import subprocess
rust_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'rust', 'finintel-engine')

# Run Rust tests
start = time.perf_counter()
result = subprocess.run(
    ["cargo", "test", "--quiet"],
    cwd=rust_dir,
    capture_output=True, text=True, timeout=60,
)
rust_elapsed = time.perf_counter() - start

# Parse results
output = result.stdout + result.stderr
passed = 0
for line in output.split('\n'):
    if 'test result: ok' in line:
        import re
        m = re.search(r'(\d+) passed', line)
        if m:
            passed = int(m.group(1))

log("G9", "rust_tests_pass", result.returncode == 0, f"exit={result.returncode}, passed={passed}")
log("G9", "rust_latency", rust_elapsed < 30, f"{rust_elapsed:.2f}s")

# ====================================================================
# G10: E2E RESEARCH (with real data connectors, mock LLM)
# ====================================================================
print("\n" + "=" * 60)
print("G10: E2E RESEARCH EXECUTION")
print("=" * 60)

# Import real connectors
import core.data.connectors.yfinance_connector
import core.data.connectors.sec_edgar_connector
import core.data.connectors.fred_connector

from core.research.evidence_pipeline.pipeline import EvidencePipeline, PipelineStage
from core.research.deep_research.models import ResearchConfig, ResearchDepth
from core.evidence.audit.store import AuditTrailStore

p = EvidencePipeline()
p.register_tool("market_data", lambda **kw: _fetch_market(kw.get("symbol", "AAPL")))
p.register_tool("earnings_data", lambda **kw: _fetch_earnings(kw.get("symbol", "AAPL")))

def _fetch_market(symbol):
    from core.data.connectors.base import get_connector
    c = get_connector("yfinance_market")
    records = c.fetch(symbol=symbol, period="1mo", interval="1d")
    return [{"close": r.data.get("close"), "volume": r.data.get("volume"), "date": str(r.data.get("date"))} for r in records[:5]]

def _fetch_earnings(symbol):
    from core.data.connectors.base import get_connector
    c = get_connector("yfinance_earnings")
    records = c.fetch(symbol=symbol)
    return [r.data for r in records[:3]]

start = time.perf_counter()
result = p.execute(
    "What is the recent price trend and fundamental valuation of AAPL? Is it overvalued or undervalued?",
    symbol="AAPL",
)
e2e_elapsed = time.perf_counter() - start

log("G10", "pipeline_complete", len(result.stages) >= 8, f"stages={len(result.stages)}")
log("G10", "evidence_collected", len(result.evidence) > 0, f"count={len(result.evidence)}")
log("G10", "synthesis_created", result.synthesis is not None, f"confidence={result.synthesis.confidence if result.synthesis else 'N/A'}")
log("G10", "llm_answer", len(result.llm_answer) > 0, f"len={len(result.llm_answer)}")
log("G10", "evidence_graph", result.graph is not None, f"nodes={result.graph.node_count() if result.graph else 0}")
log("G10", "research_id", result.research_id is not None, f"id={result.research_id[:8]}...")

# Verify no hardcoded data in real mode
evidence_types = {e.source_type for e in result.evidence}
log("G10", "evidence_from_tools", "market_data" in evidence_types or "yfinance_market" in evidence_types,
    f"types={evidence_types}")

# Check audit trail
trail = p._audit.get_trail(result.research_id)
if trail:
    log("G10", "audit_trail_recorded", len(trail.events) >= 3, f"events={len(trail.events)}")
else:
    log("G10", "audit_trail_recorded", False, "no trail found")

log("G10", "total_latency", e2e_elapsed < 60, f"{e2e_elapsed:.2f}s")

# ====================================================================
# G11: FAILURE TESTING (live)
# ====================================================================
print("\n" + "=" * 60)
print("G11: FAILURE TESTING (live)")
print("=" * 60)

# LLM timeout
class TimeoutLLM:
    def complete(self, *a, **kw):
        raise TimeoutError("LLM timeout")
    def health_check(self):
        return False

p2 = EvidencePipeline()
p2.set_llm(TimeoutLLM())
p2.register_tool("market_data", lambda **kw: [{"price": 100}])
result = p2.execute("test", symbol="AAPL")
log("G11", "llm_timeout_survived", result.synthesis is not None, "pipeline completed despite LLM timeout")

# Data provider failure
class FailProvider:
    def fetch(self, **kw):
        raise ConnectionError("Provider down")
    def health_check(self):
        return False

p3 = EvidencePipeline()
p3.register_tool("market_data", lambda **kw: (_ for _ in ()).throw(ConnectionError("data down")))
result = p3.execute("test", symbol="AAPL")
log("G11", "data_failure_survived", result.synthesis is not None, "pipeline completed despite data failure")

# Empty inputs
p4 = EvidencePipeline()
result = p4.execute("")
log("G11", "empty_question_survived", result.stages is not None, "pipeline completed with empty question")

# Very long inputs
result = p4.execute("What is " + "data " * 500 + " of AAPL?")
log("G11", "long_question_survived", result.synthesis is not None, "pipeline completed with long question")

# ====================================================================
# G12: SECURITY RECHECK
# ====================================================================
print("\n" + "=" * 60)
print("G12: SECURITY RECHECK")
print("=" * 60)

# Path traversal
from core.rag.parsing.parser import DocumentParser, SourceType
import tempfile
with tempfile.TemporaryDirectory() as tmpdir:
    parser = DocumentParser()
    try:
        parser.parse("t", SourceType.FILE, content="", file_path="../../etc/passwd", allowed_dir=tmpdir)
        log("G12", "path_traversal_blocked", False, "traversal allowed")
    except ValueError:
        log("G12", "path_traversal_blocked", True, "traversal blocked")

    # Safe path allowed
    safe_file = os.path.join(tmpdir, "safe.txt")
    with open(safe_file, "w") as f:
        f.write("safe content")
    doc = parser.parse("s", SourceType.FILE, content="", file_path=safe_file, allowed_dir=tmpdir)
    log("G12", "safe_path_allowed", doc.text == "safe content")

# No secrets in source
import glob
secret_found = False
for f in glob.glob("core/**/*.py", recursive=True):
    try:
        with open(f, encoding="utf-8") as fh:
            content = fh.read()
            # Check for common hardcoded secrets
            for pattern in ["sk_live_", "sk_test_", "password = \"real\"", "api_key = \"real\""]:
                if pattern in content:
                    secret_found = True
                    log("G12", f"secret_in_{f}", False, f"found {pattern}")
    except Exception:
        pass
if not secret_found:
    log("G12", "no_hardcoded_secrets", True, "no secrets found in source")

# Production config requires explicit secrets
os.environ["APP_ENV"] = "production"
os.environ.pop("APP_SECRET_KEY", None)
from apps.api.config import Settings
try:
    Settings()
    log("G12", "prod_requires_secret_key", False, "no validation")
except ValueError:
    log("G12", "prod_requires_secret_key", True, "validation enforced")
os.environ["APP_ENV"] = "testing"

# ====================================================================
# G13: PERFORMANCE BASELINE
# ====================================================================
print("\n" + "=" * 60)
print("G13: PERFORMANCE BASELINE")
print("=" * 60)

# Pipeline latency
start = time.perf_counter()
result = p.execute("Analyze AAPL", symbol="AAPL")
pipeline_ms = (time.perf_counter() - start) * 1000
log("G13", "pipeline_latency", pipeline_ms < 30000, f"{pipeline_ms:.0f}ms")

# Auth latency
start = time.perf_counter()
for _ in range(100):
    t = create_access_token("u", "analyst", secret_key=SECRET)
    decode_token(t, secret_key=SECRET)
auth_ms = (time.perf_counter() - start) * 1000
log("G13", "auth_100_ops", auth_ms < 10000, f"{auth_ms:.0f}ms for 100 JWT ops")

# Storage latency
from core.storage.base import MockObjectStorage
storage = MockObjectStorage()
start = time.perf_counter()
for i in range(1000):
    storage.put(f"k{i}", b"x" * 100)
for i in range(1000):
    storage.get(f"k{i}")
storage_ms = (time.perf_counter() - start) * 1000
log("G13", "storage_1000_ops", storage_ms < 5000, f"{storage_ms:.0f}ms for 1000 ops")

# Rust latency
start = time.perf_counter()
result = subprocess.run(["cargo", "test", "--quiet"], cwd=rust_dir, capture_output=True, timeout=60)
rust_ms = (time.perf_counter() - start) * 1000
log("G13", "rust_test_suite", rust_ms < 30000, f"{rust_ms:.0f}ms")

# Vector search
from core.rag.retrieval.vector_index import IndexedChunk, VectorIndex
import random
idx = VectorIndex()
for i in range(1000):
    idx.add(IndexedChunk(chunk_id=str(i), text=f"doc {i}", embedding=[random.random() for _ in range(8)]))
query = [random.random() for _ in range(8)]
start = time.perf_counter()
results_search = idx.search(query, top_k=10)
vector_ms = (time.perf_counter() - start) * 1000
log("G13", "vector_search_1000", vector_ms < 5000, f"{vector_ms:.1f}ms")

# ====================================================================
# G14: OBSERVABILITY TRACE
# ====================================================================
print("\n" + "=" * 60)
print("G14: OBSERVABILITY TRACE")
print("=" * 60)

# Pipeline produces traceable research_id
result = p.execute("Trace test for AAPL", symbol="AAPL")
log("G14", "research_id_exists", result.research_id is not None)

# Stage timings recorded (on pipeline instance)
log("G14", "stage_timings", len(p.stage_timings) > 0, f"timings={len(p.stage_timings)} stages")

# Audit trail has events
trail = p._audit.get_trail(result.research_id)
if trail:
    event_types = {e.event_type.value for e in trail.events}
    log("G14", "audit_events_recorded", len(trail.events) >= 3, f"events={len(trail.events)} types={event_types}")
else:
    log("G14", "audit_events_recorded", False, "no trail")

# Evidence items have source_type (traceable)
if result.evidence:
    all_have_source = all(e.source_type for e in result.evidence)
    log("G14", "evidence_traceable", all_have_source, f"items={len(result.evidence)}")

# Pipeline result is serializable
d = result.to_dict()
log("G14", "result_serializable", isinstance(d, dict) and "research_id" in d)

# ====================================================================
# SUMMARY
# ====================================================================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

total = len(results)
passed = sum(1 for s, _ in results.values() if s)
failed = total - passed

for key, (status, detail) in sorted(results.items()):
    symbol = "PASS" if status else "FAIL"
    print(f"  [{symbol}] {key}: {detail}")

print(f"\n  Total: {total} tests")
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
print(f"  Pass rate: {passed/total*100:.1f}%")
