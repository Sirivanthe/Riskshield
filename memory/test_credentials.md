# Test Credentials

## RiskShield Platform

| Role  | Email             | Password    |
|-------|-------------------|-------------|
| Admin | admin@bank.com    | admin123    |
| LOD1  | lod1@bank.com     | password123 |
| LOD2  | lod2@bank.com     | password123 |

Seeded at startup via `init_demo_users()` in `backend/services/auth.py`.

## LLM Configuration (new)
- Default provider: `EMERGENT` (universal key from `backend/.env`)
- User-supplied keys for `ANTHROPIC`, `OPENAI`, `GEMINI` are entered via Admin UI → Quick Switch LLM
- Keys are stored in MongoDB (`llm_config` collection, `_id="active"`) and returned masked (`api_key_set`, `api_key_last4`) from GET `/api/llm/config`
- No provider keys are hardcoded
