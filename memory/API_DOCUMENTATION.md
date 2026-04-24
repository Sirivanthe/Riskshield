# RiskShield Platform - API Documentation

## Overview

RiskShield is a production-grade technology risk and control assurance platform for banks. This document provides comprehensive API documentation for all endpoints.

**Base URL:** `https://audit-control-hub-4.preview.emergentagent.com/api`

**API Version:** v2.2.0

---

## Table of Contents
1. [Authentication](#authentication)
2. [Assessments](#assessments)
3. [Controls Library](#controls-library)
4. [Control Testing](#control-testing)
5. [Automated Testing](#automated-testing)
6. [Gap Analysis](#gap-analysis)
7. [Gap Remediation](#gap-remediation)
8. [AI Systems & Compliance](#ai-systems--compliance)
9. [RAG & Documents](#rag--documents)
10. [Trend Analytics](#trend-analytics)
11. [ServiceNow Integration](#servicenow-integration)
12. [Multi-Tenancy](#multi-tenancy)
13. [LLM Configuration](#llm-configuration)
14. [Knowledge Graph](#knowledge-graph)
15. [Observability](#observability)
16. [Issues Management](#issues-management)
17. [Workflows](#workflows)

---

## Authentication

All endpoints (except `/auth/login`) require a JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "admin@bank.com",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "usr-123",
    "email": "admin@bank.com",
    "full_name": "Admin User",
    "role": "ADMIN",
    "business_unit": "IT Security"
  }
}
```

### Get Current User

```http
GET /auth/me
Authorization: Bearer <token>
```

---

## Assessments

### Create Assessment

```http
POST /assessments
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Payment Gateway Risk Assessment",
  "system_name": "Payment Gateway v2.5",
  "description": "Annual risk assessment for core payment processing",
  "business_unit": "Technology",
  "frameworks": ["NIST CSF", "ISO 27001", "PCI-DSS"]
}
```

**Response:** Full Assessment object with AI-generated risks, controls, and evidence.

### List Assessments

```http
GET /assessments
Authorization: Bearer <token>
```

### Get Assessment

```http
GET /assessments/{assessment_id}
Authorization: Bearer <token>
```

---

## Controls Library

### Create Control

```http
POST /controls/library
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Multi-Factor Authentication",
  "control_id": "CTRL-MFA-001",
  "description": "MFA enforcement for all privileged accounts",
  "category": "ACCESS_CONTROL",
  "frameworks": ["NIST CSF", "ISO 27001"],
  "objectives": ["Prevent unauthorized access", "Comply with PR.AC-1"],
  "implementation_guidance": "Enable MFA via Azure AD or Okta",
  "testing_procedure": "Verify MFA is enforced for 100% of admin accounts",
  "frequency": "QUARTERLY",
  "is_ai_control": false
}
```

**Note:** LOD1 users create controls in DRAFT status. LOD2/Admin controls are auto-approved.

### List Controls

```http
GET /controls/library?framework=NIST%20CSF&status=APPROVED&is_ai_control=false
Authorization: Bearer <token>
```

### Approve Control (LOD2/Admin only)

```http
POST /controls/library/{control_id}/approve
Authorization: Bearer <token>
```

### Reject Control (LOD2/Admin only)

```http
POST /controls/library/{control_id}/reject?reason=Missing%20implementation%20details
Authorization: Bearer <token>
```

---

## Control Testing

### Create Control Test

```http
POST /control-tests
Authorization: Bearer <token>
Content-Type: application/json

{
  "control_id": "ctrl-123",
  "test_scope": "All production IAM accounts",
  "test_methodology": "Configuration review and access logs analysis",
  "sample_size": "100% of admin accounts, 25% sample of user accounts"
}
```

### Submit Test for Review

```http
POST /control-tests/{test_id}/submit
Authorization: Bearer <token>
```

### Review Test (LOD2/Admin only)

```http
POST /control-tests/{test_id}/review
Authorization: Bearer <token>
Content-Type: application/json

{
  "review_status": "APPROVED",
  "review_comments": "Evidence sufficient. Control operating effectively."
}
```

---

## Automated Testing

### List Test Runs

```http
GET /automated-tests/runs
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "run-123",
    "run_id": "ATR-2026-001",
    "control_id": "ctrl-123",
    "control_name": "MFA Enforcement",
    "test_type": "CONFIGURATION_CHECK",
    "effectiveness_rating": "PARTIALLY_EFFECTIVE",
    "confidence_score": 0.85,
    "findings": ["MFA enabled for 85% of accounts"],
    "recommendations": ["Enforce MFA for remaining 15%"],
    "requires_human_review": true,
    "started_at": "2026-03-20T10:00:00Z"
  }
]
```

### Run Automated Test

```http
POST /automated-tests/run/{control_id}?test_type=CONFIGURATION_CHECK
Authorization: Bearer <token>
```

**Available Test Types:**
- `CONFIGURATION_CHECK` - Verify system configurations
- `LOG_ANALYSIS` - Analyze security logs
- `ACCESS_REVIEW` - Review access permissions
- `VULNERABILITY_SCAN` - Check for vulnerabilities
- `POLICY_COMPLIANCE` - Verify policy adherence
- `DATA_QUALITY` - Check data integrity
- `AI_BIAS_CHECK` - Test AI model for bias
- `AI_FAIRNESS` - Evaluate AI fairness metrics
- `AI_EXPLAINABILITY` - Assess model explainability

### Review Test Run (LOD2/Admin only)

```http
POST /automated-tests/runs/{run_id}/review?outcome=CONFIRMED
Authorization: Bearer <token>
```

**Outcomes:** `CONFIRMED`, `OVERRIDDEN`, `ESCALATED`

### Get Test Types

```http
GET /automated-tests/test-types
Authorization: Bearer <token>
```

### Get Evidence Sources

```http
GET /automated-tests/evidence-sources
Authorization: Bearer <token>
```

---

## Gap Analysis

### Run Gap Analysis

```http
POST /gap-analysis/run?assessment_id={id}&framework=NIST%20CSF
Authorization: Bearer <token>
```

**Response:**
```json
{
  "assessment_id": "assess-123",
  "framework": "NIST CSF",
  "total_requirements": 15,
  "gaps_identified": 4,
  "coverage_percentage": 73.33,
  "gaps": [
    {
      "id": "gap-123",
      "gap_id": "GAP-2026-001",
      "framework": "NIST CSF",
      "requirement_id": "PR.AC-1",
      "gap_description": "No control mapped to identity management requirement",
      "severity": "HIGH",
      "status": "OPEN"
    }
  ]
}
```

### List Control Gaps

```http
GET /gap-analysis?framework=NIST%20CSF&status=OPEN
Authorization: Bearer <token>
```

---

## Gap Remediation

### Create Remediation Plan

```http
POST /gap-remediation
Authorization: Bearer <token>
Content-Type: application/json

{
  "gap_id": "gap-123",
  "priority": "HIGH"
}
```

### List Remediation Plans

```http
GET /gap-remediation?status=IN_PROGRESS
Authorization: Bearer <token>
```

### Get AI Recommendations

```http
GET /gap-remediation/recommendations/{gap_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "gap_id": "gap-123",
  "framework": "NIST CSF",
  "requirement_id": "PR.AC-1",
  "recommendations": {
    "recommended_controls": [
      {
        "name": "Identity and Access Management Enhancement",
        "description": "Implement comprehensive IAM with MFA, RBAC",
        "category": "TECHNICAL",
        "implementation_effort": "Medium",
        "effectiveness_estimate": "High",
        "cost_estimate": "Medium",
        "time_to_implement": "4-6 weeks",
        "ai_confidence": 0.88
      }
    ],
    "implementation_plan": "## Implementation Plan...",
    "risk_if_delayed": "Increased compliance exposure...",
    "compensating_controls": ["Enhanced monitoring", "Manual reviews"]
  }
}
```

### Select Remediation Approach

```http
PUT /gap-remediation/{remediation_id}/select-approach?approach=IMPLEMENT
Authorization: Bearer <token>
```

**Approaches:** `IMPLEMENT`, `COMPENSATING`, `ACCEPT_RISK`

### Approve Remediation (LOD2/Admin)

```http
POST /gap-remediation/{remediation_id}/approve
Authorization: Bearer <token>
```

### Complete Remediation

```http
POST /gap-remediation/{remediation_id}/complete
Authorization: Bearer <token>
```

### Verify Remediation (LOD2/Admin)

```http
POST /gap-remediation/{remediation_id}/verify?verification_method=Automated%20retest&verification_result=PASSED
Authorization: Bearer <token>
```

---

## AI Systems & Compliance

### Register AI System

```http
POST /ai-systems
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Credit Scoring Model",
  "description": "ML model for credit risk assessment",
  "risk_category": "HIGH",
  "deployment_status": "PRODUCTION",
  "intended_purpose": "Automated credit decisions",
  "business_owner": "Risk Management",
  "technical_owner": "ML Engineering"
}
```

**Risk Categories (EU AI Act):**
- `UNACCEPTABLE` - Prohibited systems
- `HIGH` - High-risk, requires compliance
- `LIMITED` - Limited transparency obligations
- `MINIMAL` - Minimal requirements

### List AI Systems

```http
GET /ai-systems?risk_category=HIGH&deployment_status=PRODUCTION
Authorization: Bearer <token>
```

### Create AI Control Assessment

```http
POST /ai-assessments
Authorization: Bearer <token>
Content-Type: application/json

{
  "ai_system_id": "sys-123",
  "framework": "EU_AI_ACT"
}
```

**Frameworks:** `EU_AI_ACT`, `NIST_AI_RMF`

### Get AI Frameworks

```http
GET /ai-frameworks
Authorization: Bearer <token>
```

---

## RAG & Documents

### Upload PDF Document

```http
POST /rag/documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <PDF file>
tenant_id: default (optional)
```

**Response:**
```json
{
  "success": true,
  "message": "Document 'compliance-guide.pdf' ingested successfully",
  "document_id": "abc123def456",
  "chunks_created": 45
}
```

### Semantic Search

```http
POST /rag/documents/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "What are the access control requirements for PCI-DSS?",
  "k": 5,
  "threshold": 0.7,
  "framework": "PCI-DSS"
}
```

**Response:**
```json
{
  "query": "What are the access control requirements for PCI-DSS?",
  "results": [
    {
      "document_id": "abc123_chunk_5",
      "content": "PCI-DSS Requirement 7 mandates that access to cardholder data...",
      "similarity_score": 0.89,
      "metadata": {
        "source": "pci-dss-guide.pdf",
        "chunk_index": 5
      }
    }
  ],
  "total_results": 5
}
```

### RAG Context Query

```http
POST /rag/documents/rag-query
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "access control requirements",
  "k": 5
}
```

**Response:**
```json
{
  "query": "access control requirements",
  "context": "Combined text from relevant chunks...",
  "context_length": 2500,
  "sources": [
    {"document_id": "...", "similarity": 0.89, "metadata": {...}}
  ],
  "total_sources": 5
}
```

### Get Vector Store Stats

```http
GET /rag/documents/stats?tenant_id=default
Authorization: Bearer <token>
```

**Response:**
```json
{
  "tenant_id": "default",
  "total_vectors": 450,
  "total_documents": 450,
  "dimension": 1536,
  "index_type": "IndexFlatIP"
}
```

### Delete Document

```http
DELETE /rag/documents/{document_id}?tenant_id=default
Authorization: Bearer <token>
```

---

## Trend Analytics

### Get Dashboard Trends

```http
GET /trends/dashboard?days=90
Authorization: Bearer <token>
```

**Response:**
```json
{
  "period_days": 90,
  "aggregation": "weekly",
  "trends": {
    "risk_score": {
      "metric": "risk_score",
      "period": "weekly",
      "labels": ["2026-01-06", "2026-01-13", ...],
      "values": [65.2, 66.8, 68.5, ...],
      "aggregation": "average"
    },
    "compliance_score": {...},
    "control_effectiveness": {...}
  },
  "generated_at": "2026-03-20T12:00:00Z"
}
```

### Get Specific Metric Trend

```http
GET /trends/metrics/{metric_type}?period=weekly&days=30
Authorization: Bearer <token>
```

**Available Metrics:**
- `risk_score`
- `compliance_score`
- `control_effectiveness`
- `assessment_count`
- `open_issues`
- `critical_risks`
- `high_risks`
- `ineffective_controls`
- `gap_count`
- `remediation_progress`

**Periods:** `daily`, `weekly`, `monthly`, `quarterly`

### Get Period Comparison

```http
GET /trends/comparison/{metric_type}?period_days=30
Authorization: Bearer <token>
```

**Response:**
```json
{
  "metric": "risk_score",
  "current_period": {
    "start": "2026-02-20T00:00:00Z",
    "end": "2026-03-20T00:00:00Z",
    "average": 73.2,
    "data_points": 30
  },
  "previous_period": {
    "start": "2026-01-21T00:00:00Z",
    "end": "2026-02-20T00:00:00Z",
    "average": 70.1,
    "data_points": 30
  },
  "change_percent": 4.42,
  "trend": "improving"
}
```

### Get Trends Summary

```http
GET /trends/summary
Authorization: Bearer <token>
```

### Record Snapshot

```http
POST /trends/snapshot
Authorization: Bearer <token>
```

### Generate Sample Data

```http
POST /trends/generate-sample-data?days=90
Authorization: Bearer <token>
```

---

## ServiceNow Integration

### Get Integration Status

```http
GET /servicenow/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "configured": false,
  "mode": "mock",
  "mock_tickets_count": 5
}
```

### Create Incident

```http
POST /servicenow/incidents
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Control Deficiency - MFA Not Enforced",
  "description": "15% of admin accounts do not have MFA enabled",
  "priority": "HIGH",
  "category": "Risk Management",
  "subcategory": "Control Deficiency",
  "assignment_group": "IT Risk Management",
  "risk_id": "RSK-001",
  "control_id": "CTRL-MFA-001",
  "framework": "NIST CSF"
}
```

**Response:**
```json
{
  "success": true,
  "sys_id": "mock-1001",
  "number": "INC0001001",
  "state": "1",
  "mock": true
}
```

### Create Risk Incident

```http
POST /servicenow/incidents/risk
Authorization: Bearer <token>
Content-Type: application/json

{
  "risk_title": "Unauthorized Access Risk",
  "risk_description": "Potential for unauthorized access due to weak controls",
  "risk_id": "RSK-001",
  "framework": "NIST CSF",
  "severity": "HIGH",
  "assignment_group": "IT Risk Management"
}
```

### Create Control Deficiency Incident

```http
POST /servicenow/incidents/control-deficiency
Authorization: Bearer <token>
Content-Type: application/json

{
  "control_name": "Multi-Factor Authentication",
  "control_id": "CTRL-MFA-001",
  "deficiency": "MFA not enforced for 15% of admin accounts",
  "framework": "NIST CSF",
  "effectiveness": "INEFFECTIVE",
  "assignment_group": "IT Risk Management"
}
```

### List Incidents

```http
GET /servicenow/incidents?status=1&limit=50
Authorization: Bearer <token>
```

### Get Incident

```http
GET /servicenow/incidents/{sys_id}
Authorization: Bearer <token>
```

### Update Incident

```http
PATCH /servicenow/incidents/{sys_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "state": "2",
  "work_notes": "Investigation in progress"
}
```

### Close Incident

```http
POST /servicenow/incidents/{sys_id}/close?resolution_notes=Issue%20resolved
Authorization: Bearer <token>
```

### Bulk Create Incidents

```http
POST /servicenow/bulk-create
Authorization: Bearer <token>
Content-Type: application/json

[
  {"title": "Incident 1", "description": "...", "priority": "HIGH"},
  {"title": "Incident 2", "description": "...", "priority": "MEDIUM"}
]
```

---

## Multi-Tenancy

### List Tenants

```http
GET /tenants/
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "default",
    "name": "default",
    "display_name": "Default Tenant",
    "database_name": "riskshield",
    "status": "active",
    "created_at": "2026-03-20T00:00:00Z",
    "settings": {}
  }
]
```

### Create Tenant

```http
POST /tenants/
Authorization: Bearer <token>
Content-Type: application/json

{
  "tenant_id": "acme-corp",
  "name": "ACME Corporation",
  "display_name": "ACME Corp",
  "settings": {
    "max_users": 100,
    "features": ["advanced_analytics"]
  }
}
```

### Get Tenant

```http
GET /tenants/{tenant_id}
Authorization: Bearer <token>
```

### Get Tenant Statistics

```http
GET /tenants/{tenant_id}/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "tenant_id": "acme-corp",
  "collections": {
    "users": 25,
    "assessments": 10,
    "custom_controls": 50,
    "control_tests": 30,
    "issues": 15
  }
}
```

### Suspend Tenant

```http
POST /tenants/{tenant_id}/suspend
Authorization: Bearer <token>
```

### Activate Tenant

```http
POST /tenants/{tenant_id}/activate
Authorization: Bearer <token>
```

### Delete Tenant

```http
DELETE /tenants/{tenant_id}?hard_delete=false
Authorization: Bearer <token>
```

**Note:** `hard_delete=true` permanently drops the tenant's database.

---

## LLM Configuration

### Get Current Config

```http
GET /llm/config
Authorization: Bearer <token>
```

### Update Config (LOD2/Admin)

```http
PUT /llm/config
Authorization: Bearer <token>
Content-Type: application/json

{
  "provider": "OLLAMA",
  "model_name": "llama3:8b",
  "ollama_host": "http://localhost:11434"
}
```

**Providers:** `MOCK`, `OLLAMA`, `AZURE`, `VERTEX_AI`

### Test LLM Connection

```http
POST /llm/test?prompt=Hello
Authorization: Bearer <token>
```

### Check Health

```http
GET /llm/health
Authorization: Bearer <token>
```

---

## Knowledge Graph

### Get Graph

```http
GET /knowledge-graph?entity_type=RISK&limit=100
Authorization: Bearer <token>
```

### Query Graph

```http
GET /knowledge-graph/query?entity_name=MFA&depth=2
Authorization: Bearer <token>
```

---

## Observability

### Dashboard

```http
GET /observability/dashboard
Authorization: Bearer <token>
```

### Agent Activities

```http
GET /agent-activities/{session_id}
Authorization: Bearer <token>
```

### Model Metrics

```http
GET /model-metrics/{session_id}
Authorization: Bearer <token>
```

### AI Explanations

```http
GET /explanations/{session_id}
Authorization: Bearer <token>
```

---

## Issues Management

### Create Issue

```http
POST /issues
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "MFA Not Enforced for Admin Accounts",
  "description": "15% of admin accounts do not have MFA enabled",
  "type": "CONTROL_DEFICIENCY",
  "severity": "HIGH",
  "priority": "P1",
  "source": "ASSESSMENT",
  "business_unit": "IT Security",
  "owner": "security-team@bank.com"
}
```

### List Issues

```http
GET /issues?status=OPEN&priority=P1
Authorization: Bearer <token>
```

---

## Workflows

### Create Workflow

```http
POST /workflows
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "High Risk Escalation",
  "description": "Auto-escalate critical risks",
  "trigger": "ON_HIGH_RISK",
  "steps": [
    {
      "action": "CREATE_GRC_TICKET",
      "params": {"system": "ServiceNow", "priority": "High"}
    },
    {
      "action": "SEND_EMAIL",
      "params": {"to": ["risk-team@bank.com"]}
    }
  ]
}
```

**Triggers:** `ON_HIGH_RISK`, `ON_FAILED_CONTROL`, `MANUAL`, `SCHEDULED`

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message describing the issue"
}
```

**Common HTTP Status Codes:**
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

---

## Rate Limits

- Authentication: 10 requests/minute
- Read operations: 100 requests/minute
- Write operations: 30 requests/minute
- AI operations (assessments, tests): 5 requests/minute

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| LOD1 (Risk Owner) | lod1@bank.com | password123 |
| LOD2 (Oversight) | lod2@bank.com | password123 |
| Admin | admin@bank.com | admin123 |
