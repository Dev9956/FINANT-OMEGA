# FININT OMEGA — Integration Manager (Provider Registry + Health + Secrets)

import os
import time
import secrets
import json
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any
from pathlib import Path
import structlog

logger = structlog.get_logger()

INTEGRATIONS_DIR = Path(os.environ.get("FININT_DATA_DIR", "data")) / "integrations"
INTEGRATIONS_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = INTEGRATIONS_DIR / "registry.json"
SECRETS_FILE = INTEGRATIONS_DIR / "secrets.enc"


class ProviderType(str, Enum):
    AI = "ai"
    MARKET_DATA = "market_data"
    NEWS = "news"
    MACRO = "macro"
    EMBEDDING = "embedding"
    DOCUMENT = "document"
    STORAGE = "storage"
    DATABASE = "database"
    NOTIFICATION = "notification"


class ProviderStatus(str, Enum):
    CONNECTED = "connected"
    RUNNING = "running"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class ProviderHealth:
    status: ProviderStatus = ProviderStatus.DISCONNECTED
    latency_ms: float = 0
    success_rate: float = 0
    last_checked: float = 0
    error_message: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class ProviderConfig:
    provider_id: str
    provider_type: ProviderType
    name: str
    description: str = ""
    enabled: bool = False
    priority: int = 0
    config: dict = field(default_factory=dict)
    health: ProviderHealth = field(default_factory=ProviderHealth)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self):
        d = asdict(self)
        d["provider_type"] = self.provider_type.value
        d["health"]["status"] = self.health.status.value
        return d


class IntegrationManager:
    def __init__(self):
        self._registry: dict[str, ProviderConfig] = {}
        self._secrets: dict[str, str] = {}
        self._load_registry()
        self._load_secrets()
        self._register_defaults()

    def _load_registry(self):
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                for pid, pdata in data.items():
                    pdata["provider_type"] = ProviderType(pdata["provider_type"])
                    pdata["health"] = ProviderHealth(
                        status=ProviderStatus(pdata["health"]["status"]),
                        latency_ms=pdata["health"].get("latency_ms", 0),
                        success_rate=pdata["health"].get("success_rate", 0),
                        last_checked=pdata["health"].get("last_checked", 0),
                        error_message=pdata["health"].get("error_message", ""),
                        extra=pdata["health"].get("extra", {}),
                    )
                    self._registry[pid] = ProviderConfig(**pdata)
                logger.info("integrations_loaded", count=len(self._registry))
            except Exception as e:
                logger.error("integration_load_failed", error=str(e))

    def _save_registry(self):
        data = {pid: p.to_dict() for pid, p in self._registry.items()}
        CONFIG_FILE.write_text(json.dumps(data, indent=2, default=str))

    def _load_secrets(self):
        if SECRETS_FILE.exists():
            try:
                raw = SECRETS_FILE.read_text()
                self._secrets = json.loads(raw)
            except Exception:
                self._secrets = {}

    def _save_secrets(self):
        SECRETS_FILE.write_text(json.dumps(self._secrets, indent=2))

    def _register_defaults(self):
        defaults = [
            ProviderConfig(
                provider_id="openai",
                provider_type=ProviderType.AI,
                name="OpenAI",
                description="GPT-4o, GPT-4o-mini, GPT-3.5-turbo",
                enabled=bool(os.environ.get("OPENAI_API_KEY")),
                priority=1,
                config={"model": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 4096, "timeout": 30},
            ),
            ProviderConfig(
                provider_id="ollama",
                provider_type=ProviderType.AI,
                name="Ollama (Local)",
                description="Local LLM inference via Ollama",
                enabled=False,
                priority=2,
                config={"base_url": "http://localhost:11434", "model": "qwen3:4b", "temperature": 0.3},
            ),
            ProviderConfig(
                provider_id="anthropic",
                provider_type=ProviderType.AI,
                name="Anthropic",
                description="Claude 3.5 Sonnet, Claude 3 Haiku",
                enabled=bool(os.environ.get("ANTHROPIC_API_KEY")),
                priority=3,
                config={"model": "claude-3-5-sonnet-20241022", "max_tokens": 4096},
            ),
            ProviderConfig(
                provider_id="yfinance",
                provider_type=ProviderType.MARKET_DATA,
                name="Yahoo Finance",
                description="Free market data via yfinance (bootstrap/dev)",
                enabled=True,
                priority=1,
                config={"rate_limit": 2000, "timeout": 10},
            ),
            ProviderConfig(
                provider_id="sec_edgar",
                provider_type=ProviderType.DOCUMENT,
                name="SEC EDGAR",
                description="SEC filings (10-K, 10-Q, 8-K, proxy)",
                enabled=True,
                priority=1,
                config={"rate_limit": 10, "timeout": 15, "user_agent": "FININT-OMEGA/0.1"},
            ),
            ProviderConfig(
                provider_id="fred",
                provider_type=ProviderType.MACRO,
                name="FRED",
                description="Federal Reserve Economic Data",
                enabled=bool(os.environ.get("FRED_API_KEY")),
                priority=1,
                config={"rate_limit": 120, "timeout": 10},
            ),
            ProviderConfig(
                provider_id="postgres",
                provider_type=ProviderType.DATABASE,
                name="PostgreSQL",
                description="Primary relational database",
                enabled=True,
                priority=1,
                config={"host": "localhost", "port": 5432, "database": "finintel_omega"},
            ),
            ProviderConfig(
                provider_id="clickhouse",
                provider_type=ProviderType.DATABASE,
                name="ClickHouse",
                description="Analytics and time-series data",
                enabled=True,
                priority=1,
                config={"host": "localhost", "port": 8123, "database": "finintel_omega"},
            ),
            ProviderConfig(
                provider_id="redis",
                provider_type=ProviderType.STORAGE,
                name="Redis",
                description="Cache and pub/sub",
                enabled=True,
                priority=1,
                config={"host": "localhost", "port": 6379},
            ),
        ]
        for p in defaults:
            if p.provider_id not in self._registry:
                self._registry[p.provider_id] = p
                logger.info("default_provider_registered", provider_id=p.provider_id, name=p.name)
        self._save_registry()

    def list_providers(self, provider_type: ProviderType | None = None) -> list[dict]:
        providers = list(self._registry.values())
        if provider_type:
            providers = [p for p in providers if p.provider_type == provider_type]
        return [p.to_dict() for p in sorted(providers, key=lambda x: x.priority)]

    def get_provider(self, provider_id: str) -> dict | None:
        p = self._registry.get(provider_id)
        return p.to_dict() if p else None

    def update_provider(self, provider_id: str, updates: dict) -> dict | None:
        p = self._registry.get(provider_id)
        if not p:
            return None
        for key in ["enabled", "priority", "config", "name", "description"]:
            if key in updates:
                if key == "config":
                    p.config.update(updates["config"])
                else:
                    setattr(p, key, updates[key])
        p.updated_at = time.time()
        self._save_registry()
        logger.info("provider_updated", provider_id=provider_id)
        return p.to_dict()

    def set_secret(self, provider_id: str, secret_key: str, secret_value: str):
        key = f"{provider_id}:{secret_key}"
        self._secrets[key] = secret_value
        self._save_secrets()
        logger.info("secret_set", provider_id=provider_id, key=secret_key)

    def get_secret(self, provider_id: str, secret_key: str) -> str | None:
        return self._secrets.get(f"{provider_id}:{secret_key}")

    def delete_secret(self, provider_id: str, secret_key: str):
        key = f"{provider_id}:{secret_key}"
        if key in self._secrets:
            del self._secrets[key]
            self._save_secrets()

    def mask_secret(self, value: str) -> str:
        if len(value) <= 8:
            return "*" * len(value)
        return value[:4] + "*" * (len(value) - 8) + value[-4:]

    async def test_provider(self, provider_id: str) -> dict:
        p = self._registry.get(provider_id)
        if not p:
            return {"success": False, "error": "Provider not found"}

        start = time.time()
        result = {"provider_id": provider_id, "name": p.name, "tests": []}

        if p.provider_type == ProviderType.AI:
            result = await self._test_ai_provider(p, result)
        elif p.provider_type == ProviderType.MARKET_DATA:
            result = await self._test_market_provider(p, result)
        elif p.provider_type == ProviderType.DOCUMENT:
            result = await self._test_document_provider(p, result)
        elif p.provider_type == ProviderType.MACRO:
            result = await self._test_macro_provider(p, result)
        elif p.provider_type == ProviderType.DATABASE:
            result = await self._test_database_provider(p, result)
        else:
            result["tests"].append({"name": "Basic", "passed": True, "detail": "No specific test available"})

        result["latency_ms"] = round((time.time() - start) * 1000)
        result["success"] = all(t["passed"] for t in result["tests"])

        p.health.last_checked = time.time()
        p.health.status = ProviderStatus.CONNECTED if result["success"] else ProviderStatus.ERROR
        p.health.latency_ms = result["latency_ms"]
        self._save_registry()

        return result

    async def _test_ai_provider(self, p: ProviderConfig, result: dict) -> dict:
        if p.provider_id == "openai":
            api_key = self.get_secret("openai", "api_key") or os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                result["tests"].append({"name": "API Key", "passed": False, "detail": "No API key configured"})
                p.health.status = ProviderStatus.DISCONNECTED
                return result
            result["tests"].append({"name": "API Key", "passed": True, "detail": f"Key: {self.mask_secret(api_key)}"})
            try:
                import httpx
                start = time.time()
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5},
                    )
                    latency = round((time.time() - start) * 1000)
                    if resp.status_code == 200:
                        data = resp.json()
                        result["tests"].append({"name": "Model Access", "passed": True, "detail": f"Response in {latency}ms"})
                        result["tests"].append({"name": "Response Valid", "passed": "choices" in data, "detail": data.get("choices", [{}])[0].get("message", {}).get("content", "")[:50]})
                        p.health.status = ProviderStatus.CONNECTED
                    else:
                        result["tests"].append({"name": "Model Access", "passed": False, "detail": f"HTTP {resp.status_code}: {resp.text[:100]}"})
                        p.health.status = ProviderStatus.ERROR
            except ImportError:
                result["tests"].append({"name": "HTTP Client", "passed": False, "detail": "httpx not installed"})
            except Exception as e:
                result["tests"].append({"name": "Connection", "passed": False, "detail": str(e)[:100]})
                p.health.status = ProviderStatus.ERROR

        elif p.provider_id == "ollama":
            base_url = p.config.get("base_url", "http://localhost:11434")
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(f"{base_url}/api/tags")
                    if resp.status_code == 200:
                        models = resp.json().get("models", [])
                        model_names = [m["name"] for m in models]
                        result["tests"].append({"name": "Ollama Running", "passed": True, "detail": f"Models: {', '.join(model_names) or 'none'}"})
                        p.health.status = ProviderStatus.RUNNING
                        p.health.extra = {"models": model_names}
                    else:
                        result["tests"].append({"name": "Ollama Running", "passed": False, "detail": f"HTTP {resp.status_code}"})
                        p.health.status = ProviderStatus.ERROR
            except ImportError:
                result["tests"].append({"name": "HTTP Client", "passed": False, "detail": "httpx not installed"})
            except Exception as e:
                result["tests"].append({"name": "Ollama Running", "passed": False, "detail": str(e)[:100]})
                p.health.status = ProviderStatus.DISCONNECTED

        return result

    async def _test_market_provider(self, p: ProviderConfig, result: dict) -> dict:
        try:
            import yfinance as yf
            ticker = yf.Ticker("AAPL")
            hist = ticker.history(period="1d")
            if len(hist) > 0:
                price = float(hist["Close"].iloc[-1])
                result["tests"].append({"name": "Data Fetch", "passed": True, "detail": f"AAPL: ${price:.2f}"})
                p.health.status = ProviderStatus.CONNECTED
            else:
                result["tests"].append({"name": "Data Fetch", "passed": False, "detail": "No data returned"})
                p.health.status = ProviderStatus.ERROR
        except Exception as e:
            result["tests"].append({"name": "Data Fetch", "passed": False, "detail": str(e)[:100]})
            p.health.status = ProviderStatus.ERROR
        return result

    async def _test_document_provider(self, p: ProviderConfig, result: dict) -> dict:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://efts.sec.gov/LATEST/search-index?q=%22annual+report%22&dateRange=custom&startdt=2026-01-01&enddt=2026-12-31&forms=10-K",
                    headers={"User-Agent": p.config.get("user_agent", "FININT-OMEGA/0.1")},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    hits = data.get("hits", {}).get("total", {}).get("value", 0)
                    result["tests"].append({"name": "EDGAR Search", "passed": True, "detail": f"{hits} 10-K filings found"})
                    p.health.status = ProviderStatus.CONNECTED
                else:
                    result["tests"].append({"name": "EDGAR Search", "passed": False, "detail": f"HTTP {resp.status_code}"})
        except Exception as e:
            result["tests"].append({"name": "EDGAR Connection", "passed": False, "detail": str(e)[:100]})
        return result

    async def _test_macro_provider(self, p: ProviderConfig, result: dict) -> dict:
        api_key = self.get_secret("fred", "api_key") or os.environ.get("FRED_API_KEY", "")
        if not api_key:
            result["tests"].append({"name": "API Key", "passed": False, "detail": "No FRED API key"})
            p.health.status = ProviderStatus.DISCONNECTED
            return result
        result["tests"].append({"name": "API Key", "passed": True, "detail": f"Key: {self.mask_secret(api_key)}"})
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.stlouisfed.org/fred/series/observations",
                    params={"series_id": "UNRATE", "api_key": api_key, "file_type": "json", "limit": 1, "sort_order": "desc"},
                )
                if resp.status_code == 200:
                    result["tests"].append({"name": "Data Fetch", "passed": True, "detail": "UNRATE series accessible"})
                    p.health.status = ProviderStatus.CONNECTED
                else:
                    result["tests"].append({"name": "Data Fetch", "passed": False, "detail": f"HTTP {resp.status_code}"})
        except Exception as e:
            result["tests"].append({"name": "Connection", "passed": False, "detail": str(e)[:100]})
        return result

    async def _test_database_provider(self, p: ProviderConfig, result: dict) -> dict:
        if p.provider_id == "postgres":
            try:
                import asyncpg
                dsn = os.environ.get("POSTGRES_DSN", f"postgresql://finintel:change-me@{p.config['host']}:{p.config['port']}/finintel_omega")
                conn = await asyncpg.connect(dsn, timeout=5)
                version = await conn.fetchval("SELECT version()")
                await conn.close()
                result["tests"].append({"name": "Connection", "passed": True, "detail": version[:60]})
                p.health.status = ProviderStatus.CONNECTED
            except ImportError:
                result["tests"].append({"name": "Driver", "passed": False, "detail": "asyncpg not installed"})
            except Exception as e:
                result["tests"].append({"name": "Connection", "passed": False, "detail": str(e)[:100]})
                p.health.status = ProviderStatus.ERROR

        elif p.provider_id == "clickhouse":
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(
                        f"http://{p.config['host']}:{p.config['port']}/",
                        params={"query": "SELECT version()"},
                    )
                    if resp.status_code == 200:
                        version = resp.text.strip()
                        result["tests"].append({"name": "Connection", "passed": True, "detail": f"ClickHouse {version}"})
                        p.health.status = ProviderStatus.CONNECTED
                    else:
                        result["tests"].append({"name": "Connection", "passed": False, "detail": f"HTTP {resp.status_code}"})
            except Exception as e:
                result["tests"].append({"name": "Connection", "passed": False, "detail": str(e)[:100]})

        elif p.provider_id == "redis":
            try:
                import redis.asyncio as aioredis
                r = aioredis.from_url(f"redis://{p.config['host']}:{p.config['port']}")
                pong = await r.ping()
                await r.aclose()
                result["tests"].append({"name": "Connection", "passed": pong, "detail": "PONG received"})
                p.health.status = ProviderStatus.CONNECTED if pong else ProviderStatus.ERROR
            except ImportError:
                result["tests"].append({"name": "Driver", "passed": False, "detail": "redis not installed"})
            except Exception as e:
                result["tests"].append({"name": "Connection", "passed": False, "detail": str(e)[:100]})

        return result

    def get_model_router_config(self) -> dict:
        ai_providers = [p for p in self._registry.values() if p.provider_type == ProviderType.AI and p.enabled]
        return {
            "providers": [{"id": p.provider_id, "name": p.name, "priority": p.priority, "config": p.config} for p in sorted(ai_providers, key=lambda x: x.priority)],
            "routing": {
                "simple_query": "lowest priority enabled provider",
                "research_query": "highest priority enabled provider with context > 4k",
                "complex_query": "cloud LLM (skip local)",
            },
        }


_manager: IntegrationManager | None = None


def get_integration_manager() -> IntegrationManager:
    global _manager
    if _manager is None:
        _manager = IntegrationManager()
    return _manager
