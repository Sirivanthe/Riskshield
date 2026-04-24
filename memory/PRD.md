# RiskShield Platform - Product Requirements Document

## Original Problem Statement

Build a production-grade, full-stack platform for a bank's technology risk and control assurance. The platform must use a multi-agent AI system to perform risk assessments, control testing, and evidence evaluation against multiple banking and security frameworks (NIST, ISO 27001, SOC2, RBI, EU AI Act, NIST AI RMF, etc.). Added scope includes Control Analysis, Regulatory Analysis, RCM Testing, Tech Risk Assessment, Issue Management, encryption of secrets at rest, and multi-tenancy.

## User Personas

### LOD1 - Risk Owners (First Line of Defense)
- Technology teams responsible for managing systems
- Need to create and track risk assessments
- Require visibility into control effectiveness

### LOD2 - Oversight/Compliance (Second Line of Defense)
- Compliance and risk management professionals
- Need to review and approve assessments
- Require aggregated risk views and reporting

### Admin
- System administrators
- Configure LLM providers, ServiceNow, and system settings
- Manage user access and GDPR compliance

## Core Requirements

### Must Have (P0) — ALL DONE
- [x] Multi-agent AI system for risk assessment (real LLM, no longer mocked)
- [x] Support for multiple LLM providers (Emergent Key default + Anthropic/OpenAI/Gemini user keys, Ollama/Azure/Vertex configurable)
- [x] JWT-based authentication with LOD1/LOD2/Admin roles
- [x] Assessment creation wizard with AI-powered analysis
- [x] Risk and control management + Controls Library with quality metrics
- [x] Knowledge graph for organizational context
- [x] Agent activity tracking and observability
- [x] Model metrics and cost tracking
- [x] AI explainability features
- [x] **Control Analysis**: CSV/Excel/ServiceNow register ingestion, quality score, duplicate detection, domain coverage, regulatory mapping, evidence evaluation against test scripts, 5W1H audit narrative, PDF + Excel workpaper exports
- [x] **Regulatory Analysis**: upload regulations (PDF/TXT), LLM parses requirements, maps to controls, surfaces gaps, one-click "Add to Control Register" or "Create Issue"
- [x] **RCM Testing Wizard**: guided step-by-step control testing flow
- [x] **Command Center Landing Page**: 5-tile action hub
- [x] **At-Rest Encryption (Fernet)** of LLM and ServiceNow credentials via `RISKSHIELD_ENCRYPTION_KEY`

### Should Have (P1) — DONE
- [x] Issue management and tracking
- [x] Remediation planning / Gap Remediation
- [x] Risk acceptance workflow
- [x] Workflow automation (GRC ticket creation, email alerts)
- [x] Regulatory document upload and RAG (FAISS + PyMuPDF)
- [x] GDPR data reset capability
- [x] Tech Risk Assessment with contextual questionnaires + PDF reports
- [x] Trend Analytics with time-series charts
- [x] Multi-Tenancy (DB per tenant)
- [x] ServiceNow connector with dual auth (Basic + API token) — functional, defaults to Mock

### Could Have (P2)
- [x] Real FAISS vector store
- [x] Real PDF parsing with PyMuPDF
- [ ] What-if risk simulations
- [ ] Advanced analytics dashboards (beyond current Trend Analytics)

### Won't Have (This Release)
- Real-time collaboration
- Mobile app

## Technical Architecture

### Backend (Python / FastAPI)
```
/app/backend/
├── server.py                # Main FastAPI app (large; candidate for splitting into /routes)
├── agents/                  # Real LLM-powered agents (Claude Sonnet 4.5 via Emergent Key)
├── routes/
│   ├── auth.py, llm_config.py, control_analysis.py, system.py,
│   ├── tech_risk.py, issue_management.py, documents.py, trends.py,
│   ├── servicenow.py, tenants.py
├── services/
│   ├── auth.py, llm_client.py, llm_evaluator.py, workpaper_generator.py,
│   ├── encryption.py (Fernet, RISKSHIELD_ENCRYPTION_KEY),
│   ├── vector_store.py, pdf_parser.py, embedding_service.py,
│   ├── servicenow_connector.py, multi_tenancy.py, trend_analytics.py,
│   ├── tech_risk_assessment.py, pdf_report_generator.py,
│   ├── issue_management.py, control_analysis_service.py
├── models.py
└── tests/
```

### Frontend (React)
```
/app/frontend/src/
├── App.js
├── components/Layout.js, components/ui/ (Shadcn)
└── pages/
    ├── Login.js, Dashboard.js (Command Center), Assessments.js, AssessmentDetail.js
    ├── ControlsLibrary.js, AICompliance.js, AutomatedTesting.js, GapRemediation.js
    ├── TrendAnalytics.js, TechRiskAssessment.js, IssueManagement.js
    ├── ControlAnalysis.js, RegulatoryAnalysis.js, RCMTesting.js
    ├── AgentActivityViewer.js, KnowledgeGraph.js, Observability.js
    ├── Workflows.js, Admin.js
```

## Data Models (key)

- `users`: id, email, full_name, role, business_unit, created_at
- `assessments`: id, name, system_name, business_unit, frameworks, status, risks[], controls[], evidence[], summary{}
- `risks` / `controls`: standard fields (severity, effectiveness, framework, test_result, etc.)
- `issues`: id, title, description, type, severity, priority, status, source, business_unit, owner, related_risk_ids, related_control_ids
- `llm_config`: provider, api_key (**encrypted**), model_name, endpoint, temperature, max_tokens
- `servicenow_configs`: instance_url, username, password (**encrypted**), api_token (**encrypted**), auth_method
- `model_metrics`: provider, model, tokens_used, cost, latency
- `tenants`: tenant_id, database_name, status

## API Endpoints (non-exhaustive)
- Auth: `/api/auth/login`, `/api/auth/me`
- LLM: `/api/llm/config`, `/api/llm/providers`, `/api/llm/health`, `/api/llm/test`
- Assessments / Issues / KG / Observability: `/api/assessments/*`, `/api/issues/*`, `/api/knowledge-graph*`, `/api/observability/*`
- Control Analysis: `/api/control-analysis/*`
- Regulations: `/api/regulations/*`
- Documents / RAG: `/api/documents/*`, `/api/rag/documents/upload`
- Tech Risk / Trends / ServiceNow / Tenants: `/api/v1/tech-risk/*`, `/api/v1/trends/*`, `/api/v1/servicenow/*`, `/api/v1/tenants/*`
- System: `/api/system/health`, `/api/system/llm/usage`

## Implementation Status (history)

### Completed (rolling)
1–32. See prior entries (modular backend, multi-provider LLM, KG, observability, issues, remediation, AI Compliance, Automated Testing, FAISS, PyMuPDF, ServiceNow, Trend Analytics, Multi-Tenancy, Tech Risk, PDF reports, Issue Management)
33. ✅ **Control Analysis Module (Apr 18, 2026)** — real LLM evidence evaluation & 5W1H narratives, 4-sheet Excel + PDF workpapers
34. ✅ **Real AI Implementation (Apr 19, 2026)** — all `/agents/*` now use real Claude Sonnet 4.5 via Emergent Key
35. ✅ **Dynamic LLM Switcher UI (Apr 19, 2026)** — Admin can switch LLM provider live
36. ✅ **Command Center Dashboard (Apr 19, 2026)** — 5-tile action hub
37. ✅ **Regulatory Analysis page (Apr 19, 2026)** — upload → LLM parse → map → gaps → one-click remediation; auto-syncs to Regulations library
38. ✅ **RCM Testing Wizard (Apr 19, 2026)** — guided control testing
39. ✅ **ServiceNow Dual Auth (Apr 19, 2026)** — Basic + API token persistence
40. ✅ **System Health & Usage Dashboard (Apr 19, 2026)** — health strip, token usage, cost estimation
41. ✅ **At-Rest Encryption (Apr 19, 2026)** — Fernet + `RISKSHIELD_ENCRYPTION_KEY` for LLM + ServiceNow secrets
42. ✅ **Regulatory Analysis Upload UX Fix (Apr 19, 2026)** — file picker no longer gates on framework name; auto-derives from filename. **Verified via smoke test.**
43. ✅ **Controls Library regulation tagging (Apr 19, 2026)** — controls created from a regulatory gap in Regulatory Analysis are now mirrored into the central Controls Library (`db.custom_controls`) with framework badge, regulatory reference tag (`§ <framework> · <requirement_id>`), and a visible "From regulatory gap · <framework>" source tag. Backend: extended `POST /api/control-analysis/controls` to mirror with valid library category mapping. Models: added `source` / `source_file` to `CustomControl`. Frontend: `ControlsLibrary.js` now renders `regulatory_references` and source tags; `RegulatoryAnalysis.js` sends `regulatory_references` + `requirement_id` and surfaces the library-mirror status in the toast.
44. ✅ **Assessments now async (Apr 19, 2026)** — `POST /api/assessments` no longer blocks on 60-180s LLM orchestration; returns in ~115ms with `status=IN_PROGRESS` and runs the multi-agent pipeline via FastAPI `BackgroundTasks`. Frontend `AssessmentDetail.js` and `Assessments.js` auto-poll every 5s while any assessment is IN_PROGRESS, with a visible "AI agents running in background · auto-refreshing" pulse indicator. Failures are captured in `summary.error` and status flips to FAILED. Regression (iteration_5) surfaced this as the only P1 action item; now closed.

### Known Limitations
- ServiceNow running in MOCK mode by default (intentional; Admin flips to live after credentials are provided)
- `server.py` grown large (~2400 lines) — candidate for splitting into `/routes`

## Testing Credentials

```
LOD1 User: lod1@bank.com / password123
LOD2 User: lod2@bank.com / password123
Admin:     admin@bank.com / admin123
```

## Critical Environment Notes

- `RISKSHIELD_ENCRYPTION_KEY` in `/app/backend/.env` — DO NOT overwrite/delete, or encrypted secrets become unrecoverable.
- `EMERGENT_LLM_KEY` — default LLM auth; also do not overwrite.

## Next Steps / Backlog

- (P1) Flip ServiceNow to live once customer credentials are provided.
- (P2) What-if risk simulations.
- (P2) Build a rotation script for existing Fernet ciphertexts if `RISKSHIELD_ENCRYPTION_KEY` ever needs rotation.
- (P3) Split `server.py` into smaller route modules under `/app/backend/routes/`.
- (P3) Real-time collaboration.
