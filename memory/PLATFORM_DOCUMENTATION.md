# RiskShield Platform - Complete Documentation

## Table of Contents
1. [Platform Overview](#platform-overview)
2. [Architecture](#architecture)
3. [Core Capabilities](#core-capabilities)
4. [API Reference](#api-reference)
5. [Services Documentation](#services-documentation)
6. [Frontend Pages](#frontend-pages)
7. [Configuration Guide](#configuration-guide)
8. [Deployment Guide](#deployment-guide)

---

## Platform Overview

RiskShield is an enterprise-grade Technology Risk and Control Assurance platform designed for banks and financial institutions. It leverages a multi-agent AI system to perform risk assessments, control testing, and evidence evaluation against multiple banking and security frameworks.

### Key Value Propositions
- **Automated Risk Assessment**: AI-powered identification and scoring of technology risks
- **Control Testing Automation**: Automated control effectiveness testing with evidence collection
- **Multi-Framework Compliance**: Support for NIST CSF, ISO 27001, SOC2, PCI-DSS, EU AI Act, NIST AI RMF
- **Three Lines of Defense**: Role-based workflows for LOD1 (Risk Owners) and LOD2 (Oversight)
- **Enterprise Integration**: ServiceNow, GRC systems, and LLM providers

### Technology Stack
| Component | Technology |
|-----------|------------|
| Backend | Python 3.10+, FastAPI |
| Frontend | React 18, TailwindCSS |
| Database | MongoDB 6.0+ |
| Vector Store | FAISS (CPU) |
| AI/ML | OpenAI Embeddings, Multi-LLM Support |
| Authentication | JWT with role-based access |

---

## Architecture

### System Architecture
```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                            │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│  │Dashboard │Assessments│Controls │AI Comply │Analytics │          │
│  │          │          │Library  │          │          │          │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    API Gateway (/api/*)                      │   │
│  │  • Authentication  • Rate Limiting  • Request Validation    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                │                                    │
│  ┌─────────────────────────────┼─────────────────────────────┐     │
│  │                             │                              │     │
│  │  ┌───────────────┐    ┌────────────────┐    ┌──────────┐  │     │
│  │  │   Services    │    │  Agent System  │    │  Routes  │  │     │
│  │  ├───────────────┤    ├────────────────┤    ├──────────┤  │     │
│  │  │• Auth         │    │• RAG Agent     │    │• Auth    │  │     │
│  │  │• LLM Client   │    │• Risk Agent    │    │• Assess  │  │     │
│  │  │• Embeddings   │    │• Control Agent │    │• Controls│  │     │
│  │  │• PDF Parser   │    │• Evidence Agent│    │• AI Comp │  │     │
│  │  │• Vector Store │    │• Testing Agent │    │• Trends  │  │     │
│  │  │• ServiceNow   │    │• Remediation   │    │• RAG     │  │     │
│  │  │• Multi-Tenant │    │                │    │• Tenants │  │     │
│  │  │• Trends       │    │                │    │          │  │     │
│  │  └───────────────┘    └────────────────┘    └──────────┘  │     │
│  │                                                            │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   MongoDB    │      │    FAISS     │      │  LLM Provider│
│              │      │ Vector Store │      │              │
│ • Users      │      │              │      │ • Ollama     │
│ • Assessments│      │ • Documents  │      │ • Azure AI   │
│ • Controls   │      │ • Embeddings │      │ • Vertex AI  │
│ • Trends     │      │ • Metadata   │      │ • OpenAI     │
└──────────────┘      └──────────────┘      └──────────────┘
```

### Multi-Tenancy Architecture (Database-per-Tenant)
```
┌─────────────────────────────────────────────────────────────┐
│                    Master Database                          │
│  • Tenant Registry                                          │
│  • Global Configuration                                     │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Tenant A    │   │  Tenant B    │   │  Tenant C    │
│  Database    │   │  Database    │   │  Database    │
├──────────────┤   ├──────────────┤   ├──────────────┤
│ • users      │   │ • users      │   │ • users      │
│ • assessments│   │ • assessments│   │ • assessments│
│ • controls   │   │ • controls   │   │ • controls   │
│ • trends     │   │ • trends     │   │ • trends     │
│ • ...        │   │ • ...        │   │ • ...        │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ FAISS Index  │   │ FAISS Index  │   │ FAISS Index  │
│  Tenant A    │   │  Tenant B    │   │  Tenant C    │
└──────────────┘   └──────────────┘   └──────────────┘
```

---

## Core Capabilities

### 1. Risk Assessment Engine

**Purpose**: Automated identification and scoring of technology risks against compliance frameworks.

**Features**:
- AI-powered risk identification from system descriptions
- Severity scoring (Critical, High, Medium, Low)
- Framework alignment (maps risks to specific requirements)
- Evidence collection recommendations
- Risk treatment options (Mitigate, Accept, Transfer, Avoid)

**Supported Frameworks**:
| Framework | Description | Controls |
|-----------|-------------|----------|
| NIST CSF | Cybersecurity Framework | 108 controls |
| ISO 27001 | Information Security Management | 114 controls |
| SOC2 | Service Organization Controls | 64 controls |
| PCI-DSS | Payment Card Industry | 250+ requirements |
| GDPR | General Data Protection | 99 articles |
| Basel III | Banking Supervision | Capital/Liquidity |
| EU AI Act | AI Regulation | 10+ categories |
| NIST AI RMF | AI Risk Management | 4 functions |

**API Endpoints**:
```
POST /api/assessments              - Create new assessment
GET  /api/assessments              - List all assessments
GET  /api/assessments/{id}         - Get assessment details
POST /api/assessments/{id}/run     - Run AI assessment
```

---

### 2. Controls Library & Testing

**Purpose**: Centralized control management with automated testing and LOD1/LOD2 approval workflow.

**Features**:
- Custom control creation with framework mapping
- Control effectiveness testing (Effective, Partially Effective, Ineffective)
- Evidence attachment and validation
- LOD1 submission → LOD2 review workflow
- AI-powered test recommendations

**Control Categories**:
- Technical Controls (firewalls, encryption, access controls)
- Administrative Controls (policies, procedures, training)
- Physical Controls (data centers, access badges)
- AI-Specific Controls (bias testing, explainability, fairness)

**Workflow**:
```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  DRAFT  │───▶│SUBMITTED│───▶│ APPROVED│───▶│ ACTIVE  │
│  (LOD1) │    │  (LOD1) │    │  (LOD2) │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                    │              │
                    │              ▼
                    │         ┌─────────┐
                    └────────▶│REJECTED │
                              │  (LOD2) │
                              └─────────┘
```

**API Endpoints**:
```
POST /api/controls/library                    - Create control
GET  /api/controls/library                    - List controls
POST /api/controls/library/{id}/approve       - LOD2 approve
POST /api/controls/library/{id}/reject        - LOD2 reject
POST /api/control-tests                       - Create test
POST /api/control-tests/{id}/submit           - Submit for review
POST /api/control-tests/{id}/review           - LOD2 review
```

---

### 3. Automated Control Testing

**Purpose**: AI-powered automated testing with evidence collection and confidence scoring.

**Test Types**:
| Test Type | Description | Automation Level |
|-----------|-------------|------------------|
| CONFIGURATION_CHECK | Verify system configurations | Full |
| LOG_ANALYSIS | Analyze security logs | Full |
| ACCESS_REVIEW | Review access permissions | Semi |
| VULNERABILITY_SCAN | Check for vulnerabilities | Full |
| POLICY_COMPLIANCE | Verify policy adherence | Semi |
| DATA_QUALITY | Check data integrity | Full |
| AI_BIAS_CHECK | Test AI model for bias | Full |
| AI_FAIRNESS | Evaluate AI fairness | Full |
| AI_EXPLAINABILITY | Assess explainability | Semi |

**Evidence Sources**:
- AWS Config, CloudTrail, IAM
- Azure AD, Security Center
- Splunk, ELK Stack
- ServiceNow CMDB
- GitHub, GitLab

**API Endpoints**:
```
GET  /api/automated-tests/runs                - List test runs
POST /api/automated-tests/run/{control_id}    - Run automated test
GET  /api/automated-tests/test-types          - Available test types
GET  /api/automated-tests/evidence-sources    - Evidence sources
POST /api/automated-tests/runs/{id}/review    - LOD2 review
```

---

### 4. Gap Analysis & Remediation

**Purpose**: Identify compliance gaps and provide AI-powered remediation recommendations.

**Features**:
- Framework gap analysis
- AI-recommended controls for gaps
- Implementation planning with timelines
- Progress tracking
- Approach selection (Implement, Compensating, Accept Risk)

**Remediation Workflow**:
```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   GAP    │───▶│  PLAN    │───▶│IN PROGRESS│───▶│COMPLETED │
│IDENTIFIED│    │ CREATED  │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                     │              │
                                     │              ▼
                                     │         ┌──────────┐
                                     │         │ VERIFIED │
                                     │         │  (LOD2)  │
                                     │         └──────────┘
```

**API Endpoints**:
```
GET  /api/gap-analysis                        - List gaps
POST /api/gap-analysis/run                    - Run gap analysis
GET  /api/gap-remediation                     - List remediation plans
POST /api/gap-remediation                     - Create plan
GET  /api/gap-remediation/recommendations/{id} - AI recommendations
PUT  /api/gap-remediation/{id}/select-approach - Select approach
POST /api/gap-remediation/{id}/complete       - Mark complete
POST /api/gap-remediation/{id}/verify         - LOD2 verify
```

---

### 5. AI Compliance (EU AI Act & NIST AI RMF)

**Purpose**: Specialized compliance management for AI/ML systems.

**EU AI Act Risk Categories**:
| Category | Description | Requirements |
|----------|-------------|--------------|
| UNACCEPTABLE | Prohibited AI | Banned |
| HIGH | High-risk AI | Full compliance |
| LIMITED | Limited transparency | Disclosure |
| MINIMAL | Minimal requirements | Best practices |

**NIST AI RMF Functions**:
- **GOVERN**: Establish AI governance structure
- **MAP**: Identify and document AI risks
- **MEASURE**: Assess AI system performance
- **MANAGE**: Implement risk treatments

**API Endpoints**:
```
POST /api/ai-systems                          - Register AI system
GET  /api/ai-systems                          - List AI systems
POST /api/ai-assessments                      - Create AI assessment
GET  /api/ai-frameworks                       - Get framework details
```

---

### 6. RAG Document System (FAISS + PDF)

**Purpose**: Semantic document search for compliance knowledge retrieval.

**Components**:
- **PDF Parser**: PyMuPDF-based text extraction
- **Chunking**: 500-word chunks with 50-word overlap
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Vector Store**: FAISS IndexFlatIP for cosine similarity

**Document Ingestion Flow**:
```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Upload  │───▶│  Parse   │───▶│  Chunk   │───▶│  Embed   │
│   PDF    │    │  Text    │    │  Text    │    │ Vectors  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                     │
                                                     ▼
                                               ┌──────────┐
                                               │  Store   │
                                               │  FAISS   │
                                               └──────────┘
```

**API Endpoints**:
```
POST /api/rag/documents/upload                - Upload PDF
POST /api/rag/documents/search                - Semantic search
POST /api/rag/documents/rag-query             - RAG context retrieval
GET  /api/rag/documents/stats                 - Vector store stats
DELETE /api/rag/documents/{id}                - Delete document
```

**Example Search Request**:
```json
{
  "query": "What are the access control requirements for PCI-DSS?",
  "k": 5,
  "threshold": 0.7
}
```

---

### 7. Trend Analytics

**Purpose**: Time-series tracking and visualization for risk metrics.

**Tracked Metrics**:
| Metric | Description | Target Trend |
|--------|-------------|--------------|
| risk_score | Overall risk score | ↑ Higher is better |
| compliance_score | Compliance percentage | ↑ Higher is better |
| control_effectiveness | Effective controls % | ↑ Higher is better |
| assessment_count | Total assessments | ↑ Growth |
| open_issues | Open issue count | ↓ Lower is better |
| critical_risks | Critical risk count | ↓ Lower is better |
| high_risks | High risk count | ↓ Lower is better |
| ineffective_controls | Ineffective controls | ↓ Lower is better |
| gap_count | Open gaps | ↓ Lower is better |
| remediation_progress | Remediation % | ↑ Higher is better |

**Aggregation Periods**:
- Daily
- Weekly
- Monthly
- Quarterly

**API Endpoints**:
```
GET  /api/trends/dashboard                    - All trends for dashboard
GET  /api/trends/metrics/{type}               - Specific metric trend
GET  /api/trends/comparison/{type}            - Period comparison
GET  /api/trends/summary                      - Executive summary
POST /api/trends/snapshot                     - Record current metrics
POST /api/trends/generate-sample-data         - Generate demo data
```

---

### 8. ServiceNow Integration

**Purpose**: GRC ticket management for risk findings and control deficiencies.

**Capabilities**:
- Create incidents for risk findings
- Create incidents for control deficiencies
- Update ticket status
- Close tickets with resolution
- Bulk ticket creation

**Mock Mode**: When ServiceNow credentials are not configured, the system operates in mock mode for development/testing.

**Ticket Priorities**:
| Priority | ServiceNow Value | Use Case |
|----------|------------------|----------|
| CRITICAL | 1 | Critical risks |
| HIGH | 2 | High severity |
| MEDIUM | 3 | Default |
| LOW | 4 | Minor findings |

**API Endpoints**:
```
GET  /api/servicenow/status                   - Integration status
POST /api/servicenow/incidents                - Create incident
POST /api/servicenow/incidents/risk           - Risk incident
POST /api/servicenow/incidents/control-deficiency - Control incident
GET  /api/servicenow/incidents                - List incidents
PATCH /api/servicenow/incidents/{id}          - Update incident
POST /api/servicenow/incidents/{id}/close     - Close incident
POST /api/servicenow/bulk-create              - Bulk create
```

---

### 9. Multi-Tenancy

**Purpose**: Complete data isolation for multiple organizations.

**Architecture**: Database-per-tenant
- Each tenant gets a dedicated MongoDB database
- Each tenant gets a dedicated FAISS vector index
- Tenant metadata stored in master database

**Tenant Lifecycle**:
```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  CREATE  │───▶│  ACTIVE  │───▶│ SUSPENDED│
│          │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘
                     │              │
                     │              ▼
                     │         ┌──────────┐
                     └────────▶│ DELETED  │
                               │          │
                               └──────────┘
```

**API Endpoints**:
```
GET  /api/tenants/                            - List tenants
POST /api/tenants/                            - Create tenant
GET  /api/tenants/{id}                        - Get tenant
GET  /api/tenants/{id}/stats                  - Tenant statistics
POST /api/tenants/{id}/suspend                - Suspend tenant
POST /api/tenants/{id}/activate               - Activate tenant
DELETE /api/tenants/{id}                      - Delete tenant
```

---

### 10. LLM Provider Support

**Purpose**: Flexible AI model integration for different deployment scenarios.

**Supported Providers**:
| Provider | Use Case | Configuration |
|----------|----------|---------------|
| Mock | Development/Testing | Default |
| Ollama | Air-gapped deployments | Local host |
| Azure AI | Enterprise Azure | API key + endpoint |
| Vertex AI | Google Cloud | Project + credentials |
| OpenAI | Direct API | API key |

**API Endpoints**:
```
GET  /api/llm/config                          - Get current config
PUT  /api/llm/config                          - Update config
POST /api/llm/test                            - Test connection
GET  /api/llm/health                          - Health check
```

---

## Services Documentation

### Vector Store Service (`/app/backend/services/vector_store.py`)

**Class: FAISSVectorStore**
```python
# Initialize
store = FAISSVectorStore(dimension=1536, tenant_id="tenant-1")

# Add documents
documents = [Document(id="doc1", content="...", embedding_vector=[...])]
store.add_documents(documents)

# Search
results = store.search(query_embedding, k=5, threshold=0.7)

# Get stats
stats = store.get_stats()
```

**Class: MultiTenantVectorStoreManager**
```python
# Get tenant-specific store
store = MultiTenantVectorStoreManager.get_store("tenant-1")

# Delete tenant's vectors
MultiTenantVectorStoreManager.delete_tenant("tenant-1")
```

---

### PDF Parser Service (`/app/backend/services/pdf_parser.py`)

**Class: PDFParserService**
```python
parser = PDFParserService(chunk_size=500, chunk_overlap=50)

# Parse from file
parsed = parser.parse_pdf_file("/path/to/document.pdf")

# Parse from bytes
parsed = parser.parse_pdf_bytes(pdf_bytes, "document.pdf")

# Chunk document
chunks = parser.chunk_document(parsed)
```

**Parsed Document Structure**:
```python
{
    "filename": "document.pdf",
    "title": "Compliance Guide",
    "author": "John Doe",
    "total_pages": 50,
    "text_content": "Full extracted text...",
    "metadata": {
        "parsed_at": "2026-03-20T12:00:00Z",
        "file_hash": "abc123..."
    }
}
```

---

### Embedding Service (`/app/backend/services/embedding_service.py`)

**Class: EmbeddingService**
```python
service = EmbeddingService(api_key="sk-emergent-...")

# Generate embeddings
embeddings = await service.generate_embeddings(["text1", "text2"])

# Single embedding
embedding = await service.generate_single_embedding("query text")

# Calculate similarity
similarity = service.calculate_similarity(embedding1, embedding2)
```

---

### ServiceNow Connector (`/app/backend/services/servicenow_connector.py`)

**Class: ServiceNowConnector**
```python
connector = ServiceNowConnector()

# Check if configured
if connector.is_configured:
    # Live mode
else:
    # Mock mode

# Create incident
ticket = ServiceNowTicket(
    short_description="Risk Finding",
    description="Details...",
    priority=TicketPriority.HIGH
)
result = await connector.create_incident(ticket)

# Helper functions
result = await create_risk_incident(connector, "Title", "Description", "RSK-001", "NIST")
result = await create_control_deficiency_incident(connector, "Control Name", "CTRL-001", "Deficiency", "ISO27001")
```

---

### Trend Analytics Service (`/app/backend/services/trend_analytics.py`)

**Class: TrendAnalyticsService**
```python
service = TrendAnalyticsService(tenant_id="default")

# Record metric
await service.record_metric(MetricType.RISK_SCORE, 75.5)

# Record full snapshot
await service.record_snapshot()

# Get trend data
series = await service.get_trend_data(
    MetricType.RISK_SCORE, 
    AggregationPeriod.WEEKLY, 
    days=90
)

# Get dashboard data
dashboard = await service.get_dashboard_trends(days=90)

# Get comparison
comparison = await service.get_comparison_data(MetricType.RISK_SCORE, period_days=30)
```

---

### Multi-Tenancy Service (`/app/backend/services/multi_tenancy.py`)

**Class: MultiTenancyService**
```python
service = MultiTenancyService()

# Create tenant
tenant = await service.create_tenant(
    tenant_id="acme-corp",
    name="ACME Corporation",
    display_name="ACME Corp"
)

# Get tenant database
db = await service.get_tenant_db("acme-corp")

# List tenants
tenants = await service.list_tenants()

# Suspend/Activate
await service.suspend_tenant("acme-corp")
await service.activate_tenant("acme-corp")

# Delete (soft or hard)
await service.delete_tenant("acme-corp", hard_delete=False)
```

---

## Frontend Pages

| Page | Route | Purpose |
|------|-------|---------|
| Login | `/login` | User authentication |
| Dashboard | `/` | Overview with metrics |
| Assessments | `/assessments` | Risk assessments list |
| Assessment Detail | `/assessments/:id` | Single assessment |
| Knowledge Graph | `/knowledge-graph` | Entity relationships |
| Observability | `/observability` | AI monitoring |
| Controls Library | `/controls-library` | Control management |
| AI Compliance | `/ai-compliance` | EU AI Act / NIST AI RMF |
| Automated Testing | `/automated-testing` | Automated tests |
| Gap Remediation | `/gap-remediation` | Gap analysis & remediation |
| Trend Analytics | `/trend-analytics` | Time-series visualization |
| Workflows | `/workflows` | Automation rules |
| Admin | `/admin` | System configuration |

---

## Configuration Guide

### Environment Variables

**Backend (`/app/backend/.env`)**
```bash
# Database
MONGO_URL="mongodb://localhost:27017"
DB_NAME="riskshield"

# Security
JWT_SECRET="your-secret-key"
JWT_ALGORITHM="HS256"

# CORS
CORS_ORIGINS="*"

# AI/Embeddings
EMERGENT_LLM_KEY="sk-emergent-..."

# Vector Store
FAISS_INDEX_PATH="/app/backend/data/faiss_index"

# ServiceNow (optional)
SERVICENOW_INSTANCE_URL="https://your-instance.service-now.com"
SERVICENOW_USERNAME="admin"
SERVICENOW_PASSWORD="password"

# LLM Provider (optional)
LLM_PROVIDER="MOCK"  # MOCK, OLLAMA, AZURE, VERTEX_AI
OLLAMA_HOST="http://localhost:11434"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
AZURE_OPENAI_KEY="your-key"
```

**Frontend (`/app/frontend/.env`)**
```bash
REACT_APP_BACKEND_URL=https://your-domain.com
```

### Test Credentials

| Role | Email | Password | Capabilities |
|------|-------|----------|--------------|
| LOD1 | lod1@bank.com | password123 | Create, submit for review |
| LOD2 | lod2@bank.com | password123 | Review, approve, reject |
| Admin | admin@bank.com | admin123 | Full access + config |

---

## Deployment Guide

### Docker Deployment

```dockerfile
# Backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

```dockerfile
# Frontend
FROM node:18-alpine
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install
COPY . .
RUN yarn build
CMD ["npx", "serve", "-s", "build", "-l", "3000"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: riskshield-backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: riskshield/backend:latest
        ports:
        - containerPort: 8001
        env:
        - name: MONGO_URL
          valueFrom:
            secretKeyRef:
              name: riskshield-secrets
              key: mongo-url
```

---

## Quick Reference

### Common API Patterns

**Authentication**:
```bash
# Login
curl -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bank.com","password":"admin123"}'

# Use token
curl -X GET "$API_URL/api/assessments" \
  -H "Authorization: Bearer $TOKEN"
```

**Create Assessment**:
```bash
curl -X POST "$API_URL/api/assessments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Payment Gateway Assessment",
    "system_name": "Payment Gateway v2.5",
    "frameworks": ["NIST CSF", "PCI-DSS"]
  }'
```

**Search Documents**:
```bash
curl -X POST "$API_URL/api/rag/documents/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "access control requirements",
    "k": 5
  }'
```

**Get Trend Data**:
```bash
curl -X GET "$API_URL/api/trends/dashboard?days=90" \
  -H "Authorization: Bearer $TOKEN"
```

---

*Documentation Version: 2.2.0*
*Last Updated: March 20, 2026*
