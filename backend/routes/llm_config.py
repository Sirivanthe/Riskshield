# LLM Configuration routes
from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict

from models import User, UserRole, LLMConfig, LLMConfigUpdate, LLMProvider
from services.auth import get_current_user
from services.llm_client import LLMClientFactory

router = APIRouter(prefix="/llm", tags=["LLM Configuration"])


def _safe_config(config: LLMConfig) -> Dict[str, Any]:
    """Return the config with the api_key masked. Never expose the raw key."""
    data = config.model_dump()
    raw_key = data.pop("api_key", None)
    data["api_key_set"] = bool(raw_key)
    data["api_key_last4"] = raw_key[-4:] if raw_key and len(raw_key) >= 4 else None
    return data


@router.get("/config")
async def get_llm_config(current_user: User = Depends(get_current_user)):
    """Get current LLM configuration (api_key masked)."""
    return _safe_config(LLMClientFactory.get_current_config())


@router.put("/config")
async def update_llm_config(
    config_update: LLMConfigUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update LLM configuration (Admin/LOD2 only). Accepts a user-supplied api_key
    for Anthropic / OpenAI / Gemini providers."""
    if current_user.role not in [UserRole.ADMIN, UserRole.LOD2_USER]:
        raise HTTPException(status_code=403, detail="Only Admin or LOD2 users can update LLM configuration")

    current_config = LLMClientFactory.get_current_config()

    update_data = config_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        # Allow explicit clearing for string fields with empty string;
        # otherwise skip None so we don't wipe existing values accidentally.
        if value is None:
            continue
        setattr(current_config, key, value)

    # Validate provider requirements up-front for a clearer error message
    if current_config.provider in (LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GEMINI):
        if not current_config.api_key:
            raise HTTPException(
                status_code=400,
                detail=f"{current_config.provider.value} provider requires an api_key.",
            )

    LLMClientFactory.update_config(current_config)
    await LLMClientFactory.save_to_db(current_config)

    return _safe_config(current_config)


@router.delete("/config/api-key")
async def clear_api_key(current_user: User = Depends(get_current_user)):
    """Remove the stored user-supplied API key."""
    if current_user.role not in [UserRole.ADMIN, UserRole.LOD2_USER]:
        raise HTTPException(status_code=403, detail="Only Admin or LOD2 users can modify LLM configuration")

    cfg = LLMClientFactory.get_current_config()
    cfg.api_key = None
    LLMClientFactory.update_config(cfg)
    await LLMClientFactory.save_to_db(cfg)
    return _safe_config(cfg)


@router.get("/providers")
async def list_providers(current_user: User = Depends(get_current_user)):
    """List available LLM providers."""
    return {
        "providers": [
            {
                "id": LLMProvider.EMERGENT.value,
                "name": "Emergent (Universal Key)",
                "description": "Default. Real LLM via Emergent universal key — no extra credentials.",
                "requires_credentials": False,
                "config_fields": ["model_name"],
                "suggested_models": [
                    "claude-sonnet-4-5-20250929",
                    "gpt-5.2",
                    "gemini-2.5-pro",
                ],
            },
            {
                "id": LLMProvider.ANTHROPIC.value,
                "name": "Anthropic (Your Key)",
                "description": "Use your own Anthropic API key.",
                "requires_credentials": True,
                "config_fields": ["api_key", "model_name"],
                "suggested_models": [
                    "claude-sonnet-4-5-20250929",
                    "claude-opus-4-5-20251101",
                    "claude-haiku-4-5-20251001",
                ],
            },
            {
                "id": LLMProvider.OPENAI.value,
                "name": "OpenAI (Your Key)",
                "description": "Use your own OpenAI API key.",
                "requires_credentials": True,
                "config_fields": ["api_key", "model_name"],
                "suggested_models": ["gpt-5.2", "gpt-5.1", "gpt-4o", "gpt-4.1"],
            },
            {
                "id": LLMProvider.GEMINI.value,
                "name": "Google Gemini (Your Key)",
                "description": "Use your own Google Gemini API key.",
                "requires_credentials": True,
                "config_fields": ["api_key", "model_name"],
                "suggested_models": [
                    "gemini-2.5-pro",
                    "gemini-2.5-flash",
                    "gemini-3-flash-preview",
                ],
            },
            {
                "id": LLMProvider.OLLAMA.value,
                "name": "Ollama (Local)",
                "description": "Local LLM using Ollama. Point it at your Ollama host.",
                "requires_credentials": False,
                "config_fields": ["ollama_host", "model_name"],
                "suggested_models": ["llama3", "llama3:70b", "mistral", "mixtral"],
            },
            {
                "id": LLMProvider.AZURE.value,
                "name": "Azure AI Agent Service",
                "description": "Enterprise Azure AI Agent Service.",
                "requires_credentials": True,
                "config_fields": ["azure_endpoint", "azure_deployment", "model_name"],
            },
            {
                "id": LLMProvider.VERTEX_AI.value,
                "name": "Google Vertex AI",
                "description": "Google Cloud Vertex AI Agent Builder.",
                "requires_credentials": True,
                "config_fields": ["vertex_project", "vertex_location", "model_name"],
            },
            {
                "id": LLMProvider.KIMI.value,
                "name": "Kimi (Moonshot AI)",
                "description": "Use your own Kimi API key from Moonshot AI.",
                "requires_credentials": True,
                "config_fields": ["api_key", "model_name"],
                "suggested_models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
            },
            {
                "id": LLMProvider.MOCK.value,
                "name": "Mock (Development)",
                "description": "Mock LLM for development and testing.",
                "requires_credentials": False,
            },
        ]
    }


@router.get("/health")
async def check_llm_health(current_user: User = Depends(get_current_user)):
    return await LLMClientFactory.health_check()


@router.post("/test")
async def test_llm(
    prompt: str = "Hello, are you working?",
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Test the current LLM configuration."""
    try:
        client = LLMClientFactory.get_client()
        result = await client.generate(prompt)
        cfg = LLMClientFactory.get_current_config()
        return {
            "success": True,
            "provider": cfg.provider.value,
            "model": cfg.model_name,
            "response": (result.get("response") or "")[:500],
            "tokens": {
                "prompt": result.get("prompt_tokens", 0),
                "completion": result.get("completion_tokens", 0),
            },
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": LLMClientFactory.get_current_config().provider.value,
        }
