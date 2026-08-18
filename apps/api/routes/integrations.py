# FININT OMEGA — Integration Control Plane API

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from core.auth.dependencies import get_current_user
from core.integrations.manager import get_integration_manager, ProviderType

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


class ProviderUpdateRequest(BaseModel):
    enabled: bool | None = None
    priority: int | None = None
    name: str | None = None
    description: str | None = None
    config: dict | None = None


class SecretRequest(BaseModel):
    secret_key: str
    secret_value: str


@router.get("")
def list_providers(provider_type: str | None = None):
    mgr = get_integration_manager()
    pt = ProviderType(provider_type) if provider_type else None
    return {"providers": mgr.list_providers(pt)}


@router.get("/categories")
def list_categories():
    mgr = get_integration_manager()
    categories = {}
    for p in mgr.list_providers():
        cat = p["provider_type"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)
    return {"categories": categories}


@router.get("/{provider_id}")
def get_provider(provider_id: str):
    mgr = get_integration_manager()
    p = mgr.get_provider(provider_id)
    if not p:
        raise HTTPException(404, "Provider not found")
    return p


@router.put("/{provider_id}")
def update_provider(provider_id: str, req: ProviderUpdateRequest):
    mgr = get_integration_manager()
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    result = mgr.update_provider(provider_id, updates)
    if not result:
        raise HTTPException(404, "Provider not found")
    return result


@router.post("/{provider_id}/test")
async def test_provider(provider_id: str):
    mgr = get_integration_manager()
    return await mgr.test_provider(provider_id)


@router.post("/{provider_id}/secrets")
def set_secret(provider_id: str, req: SecretRequest):
    mgr = get_integration_manager()
    mgr.set_secret(provider_id, req.secret_key, req.secret_value)
    return {"status": "ok", "key": req.secret_key, "masked": mgr.mask_secret(req.secret_value)}


@router.delete("/{provider_id}/secrets/{secret_key}")
def delete_secret(provider_id: str, secret_key: str):
    mgr = get_integration_manager()
    mgr.delete_secret(provider_id, secret_key)
    return {"status": "deleted"}


@router.get("/{provider_id}/secrets")
def list_secrets(provider_id: str):
    mgr = get_integration_manager()
    keys = [k.split(":", 1)[1] for k in mgr._secrets if k.startswith(f"{provider_id}:")]
    return {"provider_id": provider_id, "secrets": [{"key": k, "masked": True} for k in keys]}


@router.get("/ai/model-router")
def get_model_router():
    mgr = get_integration_manager()
    return mgr.get_model_router_config()


@router.get("/health/summary")
def health_summary():
    mgr = get_integration_manager()
    providers = mgr.list_providers()
    summary = {
        "total": len(providers),
        "connected": sum(1 for p in providers if p["health"]["status"] in ("connected", "running", "healthy")),
        "disconnected": sum(1 for p in providers if p["health"]["status"] in ("disconnected", "error")),
        "disabled": sum(1 for p in providers if p["health"]["status"] == "disabled"),
    }
    return summary
