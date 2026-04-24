# System health + LLM usage endpoints
# Feeds the Dashboard health strip and the Admin "Usage & Cost" tab.

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query

from db import db
from models import User
from services.auth import get_current_user
from services.llm_client import LLMClientFactory

logger = logging.getLogger(__name__)
api_router = APIRouter()


# -------- System health --------

def _llm_pill() -> Dict[str, Any]:
    cfg = LLMClientFactory.get_current_config()
    provider = cfg.provider.value
    requires_user_key = provider in ("ANTHROPIC", "OPENAI", "GEMINI")
    # Prefer user-supplied key; fall back to EMERGENT_LLM_KEY for EMERGENT
    healthy = False
    note = ""
    if provider == "MOCK":
        return {"status": "warn", "label": f"LLM · Mock", "detail": "Mock provider — responses are not from a real model."}
    if requires_user_key:
        healthy = bool(cfg.api_key)
        note = "API key stored" if healthy else "No key configured"
    elif provider == "EMERGENT":
        healthy = bool(os.environ.get("EMERGENT_LLM_KEY"))
        note = "Emergent universal key" if healthy else "EMERGENT_LLM_KEY missing"
    elif provider == "OLLAMA":
        healthy = bool(cfg.ollama_host)
        note = "Ollama host set" if healthy else "ollama_host missing"
    elif provider == "AZURE":
        healthy = bool(cfg.azure_endpoint and cfg.azure_deployment)
        note = "Azure endpoint + deployment set" if healthy else "Missing Azure config"
    elif provider == "VERTEX_AI":
        healthy = bool(cfg.vertex_project and cfg.vertex_location)
        note = "Vertex project + region set" if healthy else "Missing Vertex config"
    return {
        "status": "healthy" if healthy else "error",
        "label": f"LLM · {provider}",
        "detail": f"{cfg.model_name} · {note}",
    }


async def _servicenow_pill() -> Dict[str, Any]:
    try:
        from routes.servicenow import connector
    except Exception as e:
        return {"status": "error", "label": "ServiceNow", "detail": f"Connector load failed: {e}"}

    if connector.is_configured:
        return {
            "status": "healthy",
            "label": "ServiceNow · Live",
            "detail": f"Connected to {connector.config.instance_url} ({connector.config.auth_type})",
        }
    return {
        "status": "warn",
        "label": "ServiceNow · Mock",
        "detail": "No credentials configured — running in mock mode.",
    }


async def _rag_pill() -> Dict[str, Any]:
    try:
        count = await db.documents.count_documents({})
    except Exception:
        count = 0
    try:
        from services.vector_store import vector_store  # type: ignore
        has_index = bool(getattr(vector_store, "index", None))
    except Exception:
        has_index = False
    if count == 0 and not has_index:
        return {"status": "warn", "label": "RAG · Empty", "detail": "No documents indexed yet."}
    return {
        "status": "healthy",
        "label": "RAG · Ready",
        "detail": f"{count} documents indexed",
    }


async def _tenancy_pill() -> Dict[str, Any]:
    try:
        count = await db.tenants.count_documents({})
    except Exception:
        count = 0
    return {
        "status": "healthy" if count > 0 else "warn",
        "label": f"Multi-Tenancy · {count} tenant{'s' if count != 1 else ''}",
        "detail": "Database-per-tenant isolation" if count > 0 else "Using default tenant only.",
    }


@api_router.get("/health")
async def system_health(current_user: User = Depends(get_current_user)):
    """Aggregated health check used by the Dashboard health strip."""
    llm = _llm_pill()
    snow = await _servicenow_pill()
    rag = await _rag_pill()
    tenancy = await _tenancy_pill()
    pills = [llm, snow, rag, tenancy]
    worst = "healthy"
    for p in pills:
        if p["status"] == "error":
            worst = "error"
            break
        if p["status"] == "warn" and worst == "healthy":
            worst = "warn"
    return {
        "overall": worst,
        "pills": pills,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


# -------- LLM usage & cost --------

@api_router.get("/llm/usage")
async def llm_usage(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
):
    """Aggregate token usage and cost from the model_metrics collection."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    since_iso = since.isoformat()

    cursor = db.model_metrics.find(
        {"timestamp": {"$gte": since_iso}},
        {"_id": 0},
    ).sort("timestamp", -1)
    records = await cursor.to_list(50000)

    totals = {
        "calls": len(records),
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
        "successful": 0,
        "failed": 0,
        "avg_latency_ms": 0,
    }
    by_model: Dict[str, Dict[str, Any]] = {}
    by_endpoint: Dict[str, Dict[str, Any]] = {}
    by_day: Dict[str, Dict[str, Any]] = {}
    latencies = []

    for r in records:
        pt = int(r.get("prompt_tokens") or 0)
        ct = int(r.get("completion_tokens") or 0)
        tt = int(r.get("total_tokens") or (pt + ct))
        cost = float(r.get("cost_usd") or 0.0)
        totals["prompt_tokens"] += pt
        totals["completion_tokens"] += ct
        totals["total_tokens"] += tt
        totals["cost_usd"] += cost
        success = bool(r.get("success", True))
        totals["successful" if success else "failed"] += 1
        lat = int(r.get("latency_ms") or 0)
        if lat:
            latencies.append(lat)

        mkey = r.get("model_name") or "unknown"
        m = by_model.setdefault(mkey, {"calls": 0, "tokens": 0, "cost_usd": 0.0})
        m["calls"] += 1
        m["tokens"] += tt
        m["cost_usd"] += cost

        ekey = r.get("endpoint") or "unknown"
        e = by_endpoint.setdefault(ekey, {"calls": 0, "tokens": 0, "cost_usd": 0.0})
        e["calls"] += 1
        e["tokens"] += tt
        e["cost_usd"] += cost

        day = (r.get("timestamp") or "")[:10] or since_iso[:10]
        d = by_day.setdefault(day, {"calls": 0, "tokens": 0, "cost_usd": 0.0})
        d["calls"] += 1
        d["tokens"] += tt
        d["cost_usd"] += cost

    if latencies:
        totals["avg_latency_ms"] = int(sum(latencies) / len(latencies))

    # Round costs
    totals["cost_usd"] = round(totals["cost_usd"], 4)
    for bucket in (by_model, by_endpoint, by_day):
        for v in bucket.values():
            v["cost_usd"] = round(v["cost_usd"], 4)

    return {
        "period_days": days,
        "since": since_iso,
        "totals": totals,
        "by_model": by_model,
        "by_endpoint": by_endpoint,
        "by_day": sorted(
            [{"day": k, **v} for k, v in by_day.items()],
            key=lambda x: x["day"],
        ),
        "recent": records[:25],
    }
