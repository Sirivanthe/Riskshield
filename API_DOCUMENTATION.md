# RiskShield API Documentation

## Base URL
`https://your-domain.com/api`

## Authentication
All API endpoints (except `/auth/login`) require a valid JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

---

## Authentication Endpoints

### POST /auth/login
Login and obtain JWT token.

**Request Body:**
```json
{
  "email": "lod1@bank.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "lod1@bank.com",
    "full_name": "John Smith",
    "role": "LOD1_USER",
    "business_unit": "Technology Risk",
    "created_at": "2026-03-20T12:00:00Z"
  }
}
```

### GET /auth/me
Get current authenticated user info.

**Response:**
```json
{
  "id": "uuid",
  "email": "lod1@bank.com",
  "full_name": "John Smith",
  "role": "LOD1_USER",
  "business_unit": "Technology Risk",
  "created_at": "2026-03-20T12:00:00Z"
}
```

---

## LLM Configuration Endpoints

### GET /llm/config
Get current LLM configuration.

**Response:**
```json
{
  "provider": "MOCK",
  "model_name": "llama-3-70b",
  "azure_endpoint": null,
  "azure_deployment": null,
  "vertex_project": null,
  "vertex_location": null,
  "ollama_host": null,
  "temperature": 0.1,
  "max_tokens": 4096
}
```

### PUT /llm/config
Update LLM configuration (LOD2/Admin only).

**Request Body:**
```json
{
  "provider": "AZURE",
  "model_name": "gpt-4",
  "azure_endpoint": "https://your-resource.openai.azure.com/",
  "azure_deployment": "gpt-4-deployment",
  "temperature": 0.1,
  "max_tokens": 4096
}
```

**Supported Providers:**
- `MOCK` - Development/testing
- `OLLAMA` - Local LLM
- `AZURE` - Azure AI Agent Service
- `VERTEX_AI` - Google Vertex AI

### GET /llm/providers
List available LLM providers.

**Response:**
```json
{
  "providers": [
    {
      "id": "MOCK",
      "name": "Mock (Development)",
      "description": "Mock LLM for development and testing",
      "requires_credentials": false
    },
    {
      "id": "OLLAMA",
      "name": "Ollama (Local)",
      "description": "Local LLM using Ollama",
      "requires_credentials": false,
      "config_fields": ["ollama_host", "model_name"]
    },
    {
      "id": "AZURE",
      "name": "Azure AI Agent Service",
      "description": "Enterprise Azure AI Agent Service",
      "requires_credentials": true,
      "config_fields": ["azure_endpoint", "azure_deployment", "model_name"]
    },
    {
      "id": "VERTEX_AI",
      "name": "Google Vertex AI",
      "description": "Google Cloud Vertex AI Agent Builder",
      "requires_credentials": true,
      "config_fields": ["vertex_project", "vertex_location", "model_name"]
    }
  ]
}
```

### GET /llm/health
Check LLM service health.

**Response:**
```json
{
  "provider": "MOCK",
  "model_name": "llama-3-70b",
  "healthy": true,
  "timestamp": "2026-03-20T12:00:00Z"
}
```

### POST /llm/test
Test LLM connection with a sample prompt.

**Query Parameters:**
- `prompt` (optional): Test prompt (default: "Hello, are you working?")

**Response:**
```json
{
  "success": true,
  "provider": "MOCK",
  "model": "llama-3-70b",
  "response": "Mock response generated...",
  "tokens": {
    "prompt": 5,
    "completion": 10
  }
}
```

---

## Assessment Endpoints

### POST /assessments
Create and run a new assessment.

**Request Body:**
```json
{
  "name": "AWS Production Environment Risk Assessment",
  "system_name": "AWS Production Infrastructure",
  "business_unit": "Cloud Operations",
  "frameworks": ["NIST CSF", "ISO 27001", "SOC2"],
  "description": "Risk assessment of AWS environment",
  "scenario": "Annual compliance review"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "AWS Production Environment Risk Assessment",
  "system_name": "AWS Production Infrastructure",
  "business_unit": "Cloud Operations",
  "frameworks": ["NIST CSF", "ISO 27001", "SOC2"],
  "status": "COMPLETED",
  "created_by": "user-uuid",
  "created_at": "2026-03-20T12:00:00Z",
  "completed_at": "2026-03-20T12:00:05Z",
  "risks": [...],
  "controls": [...],
  "evidence": [...],
  "summary": {
    "overall_score": 75,
    "risk_summary": { "critical": 1, "high": 2, "medium": 1, "low": 0, "total": 4 },
    "control_summary": { "effective": 2, "partially_effective": 2, "ineffective": 1, "total": 5 },
    "compliance_status": "Non-Compliant",
    "recommendations": [...]
  }
}
```

### GET /assessments
List assessments (filtered by user for LOD1).

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Assessment Name",
    "status": "COMPLETED",
    "summary": { "overall_score": 75 }
  }
]
```

### GET /assessments/{assessment_id}
Get assessment details by ID.

---

## Issue Management Endpoints

### POST /issues
Create a new issue.

**Request Body:**
```json
{
  "title": "MFA Not Enforced for Admin Accounts",
  "description": "15% of admin accounts do not have MFA enabled",
  "type": "CONTROL_DEFICIENCY",
  "severity": "HIGH",
  "priority": "P2",
  "source": "Assessment",
  "business_unit": "Cloud Operations",
  "frameworks": ["NIST CSF", "ISO 27001"],
  "owner": "john@bank.com",
  "assignees": ["jane@bank.com"]
}
```

**Issue Types:**
- `CONTROL_DEFICIENCY`
- `POLICY_VIOLATION`
- `AUDIT_FINDING`
- `REGULATORY_GAP`
- `SECURITY_VULNERABILITY`

**Priority Levels:**
- `P1` - Critical (1 day SLA)
- `P2` - High (7 days SLA)
- `P3` - Medium (30 days SLA)
- `P4` - Low (90 days SLA)

### GET /issues
List issues with optional filters.

**Query Parameters:**
- `status` (optional): Filter by status
- `priority` (optional): Filter by priority

### GET /issues/{issue_id}
Get issue details by ID.

### PUT /issues/{issue_id}
Update an issue.

---

## Knowledge Graph Endpoints

### GET /knowledge-graph
Get knowledge graph entities and relations.

**Query Parameters:**
- `entity_type` (optional): Filter by type (SYSTEM, RISK, CONTROL, REGULATION)
- `limit` (optional): Maximum entities (default: 100)

**Response:**
```json
{
  "entities": [
    {
      "id": "uuid",
      "entity_type": "SYSTEM",
      "name": "AWS Production",
      "description": "Production environment",
      "properties": {...}
    }
  ],
  "relations": [
    {
      "id": "uuid",
      "source_entity_id": "uuid",
      "target_entity_id": "uuid",
      "relation_type": "MITIGATES",
      "properties": {...}
    }
  ],
  "stats": {
    "entity_count": 9,
    "relation_count": 8,
    "entity_types": ["SYSTEM", "RISK", "CONTROL"]
  }
}
```

### GET /knowledge-graph/query
Query knowledge graph by entity name.

**Query Parameters:**
- `entity_name`: Entity name to search
- `depth` (optional): Traversal depth (default: 2)

---

## Observability Endpoints

### GET /observability/dashboard
Get observability dashboard data.

**Response:**
```json
{
  "model_performance": {
    "total_requests": 2,
    "total_tokens": 1440,
    "total_cost_usd": 0.0025,
    "avg_latency_ms": 150,
    "success_rate": 100.0
  },
  "agent_activity": {
    "total_activities": 10,
    "completed": 8,
    "failed": 0,
    "success_rate": 80.0
  },
  "knowledge_graph": {
    "total_entities": 9,
    "total_relations": 8
  },
  "llm_config": {
    "provider": "MOCK",
    "model_name": "llama-3-70b"
  },
  "recent_metrics": [...],
  "recent_activities": [...]
}
```

### GET /agent-activities/{session_id}
Get agent activities for a session (assessment ID).

### GET /model-metrics/{session_id}
Get model metrics for a session.

### GET /explanations/{session_id}
Get AI explanations for a session.

---

## Analytics Endpoints

### GET /analytics/summary
Get analytics summary.

**Response:**
```json
{
  "total_assessments": 3,
  "high_risks": 5,
  "ineffective_controls": 3,
  "avg_compliance_score": 72,
  "frameworks_covered": ["NIST CSF", "ISO 27001", "SOC2", "PCI-DSS", "GDPR", "Basel III"]
}
```

### GET /analytics/trends
Get analytics trends over time.

---

## Workflow Endpoints

### POST /workflows
Create a new workflow (LOD2/Admin only).

### GET /workflows
List workflows.

### POST /assessments/{assessment_id}/trigger-workflows
Manually trigger workflows for an assessment.

---

## GDPR Compliance

### POST /gdpr/reset-history
Reset user history for GDPR compliance (Admin only).

Anonymizes:
- Agent activity inputs/outputs
- Explanation supporting facts

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message"
}
```

**Common Status Codes:**
- `401 Unauthorized` - Invalid or missing token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
