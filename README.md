# RiskShield - Enterprise Technology Risk & Control Platform

A production-grade, full-stack platform for bank technology risk and control assurance, powered by a multi-agent AI system.

## Features

### Core Capabilities
- **Multi-Agent AI System**: Orchestrated AI agents for risk assessment, control testing, and evidence collection
- **Multi-Framework Support**: NIST CSF, ISO 27001, SOC2, PCI-DSS, GDPR, Basel III, EU AI Act, NIST AI RMF
- **Three Lines of Defense**: Role-based access for LOD1 (Risk Owners), LOD2 (Oversight), and Admin
- **Knowledge Graph**: Organizational context mapping with entity relationships

### AI-Powered Automation
- **Automated Risk Assessment**: AI-driven risk identification with regulatory alignment
- **Automated Control Testing**: AI-powered control effectiveness evaluation with evidence collection
- **Gap Remediation**: Intelligent recommendations and implementation planning
- **AI Compliance**: EU AI Act and NIST AI RMF compliance tracking

### Observability & Governance
- **Agent Activity Monitoring**: Real-time tracking of AI agent operations
- **Model Metrics**: Token usage, latency, and cost tracking
- **AI Explainability**: Confidence scores and decision reasoning
- **GDPR Compliance**: Data anonymization and reset capabilities

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- MongoDB 6.0+

### Installation

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Configure MONGO_URL in .env

# Frontend
cd frontend
yarn install
```

### Running Locally

```bash
# Start backend
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Start frontend (separate terminal)
cd frontend
yarn start
```

### Test Credentials

| Role | Email | Password |
|------|-------|----------|
| LOD1 (Risk Owner) | lod1@bank.com | password123 |
| LOD2 (Oversight) | lod2@bank.com | password123 |
| Admin | admin@bank.com | admin123 |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
├─────────────────────────────────────────────────────────────────┤
│  Dashboard │ Assessments │ Controls │ AI Compliance │ Admin    │
│  Automated Testing │ Gap Remediation │ Observability           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
├─────────────────────────────────────────────────────────────────┤
│                    API Router (/api/*)                          │
├──────────────────────┬──────────────────────────────────────────┤
│                      │                                          │
│  ┌────────────────┐  │  ┌────────────────────────────────────┐  │
│  │   Services     │  │  │         Multi-Agent System         │  │
│  │  ├── Auth      │  │  │  ├── RAG Agent                     │  │
│  │  └── LLM Client│  │  │  ├── Risk Assessment Agent         │  │
│  └────────────────┘  │  │  ├── Control Testing Agent         │  │
│                      │  │  ├── Evidence Collection Agent      │  │
│                      │  │  ├── Automated Testing Agent        │  │
│                      │  │  └── Gap Remediation Agent          │  │
│                      │  └────────────────────────────────────┘  │
└──────────────────────┴──────────────────────────────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           ▼                    ▼                    ▼
    ┌────────────┐      ┌────────────┐      ┌────────────┐
    │  MongoDB   │      │ LLM Provider│      │ Knowledge  │
    │            │      │ (Ollama/   │      │   Graph    │
    │            │      │ Azure/etc) │      │            │
    └────────────┘      └────────────┘      └────────────┘
```

## API Documentation

See [API_DOCUMENTATION.md](/app/memory/API_DOCUMENTATION.md) for complete API reference.

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | Authenticate user |
| `/api/assessments` | POST/GET | Create/list assessments |
| `/api/controls/library` | POST/GET | Manage controls library |
| `/api/automated-tests/run/{id}` | POST | Run automated test |
| `/api/gap-analysis/run` | POST | Run gap analysis |
| `/api/gap-remediation` | POST/GET | Manage remediations |
| `/api/ai-systems` | POST/GET | Register AI systems |
| `/api/llm/config` | GET/PUT | Configure LLM provider |

## LLM Provider Configuration

RiskShield supports multiple LLM providers:

| Provider | Description | Use Case |
|----------|-------------|----------|
| Mock | Simulated responses | Development/Testing |
| Ollama | Local LLM | Air-gapped deployments |
| Azure AI | Azure AI Agent Service | Enterprise Azure |
| Vertex AI | Google Vertex AI | Google Cloud |

Configure via Admin Panel > LLM Configuration.

## Compliance Frameworks

### Banking & Security
- **NIST CSF** - Cybersecurity Framework
- **ISO 27001** - Information Security Management
- **SOC2** - Service Organization Controls
- **PCI-DSS** - Payment Card Industry
- **GDPR** - General Data Protection Regulation
- **Basel III** - Banking Supervision

### AI Governance
- **EU AI Act** - European Union AI Regulation
- **NIST AI RMF** - AI Risk Management Framework

## Project Structure

```
/app/
├── backend/
│   ├── server.py          # FastAPI application
│   ├── db/                # Database utilities
│   ├── models/            # Pydantic models
│   ├── services/          # Business logic
│   ├── agents/            # AI agent system
│   ├── routes/            # API routes
│   └── tests/             # Backend tests
├── frontend/
│   ├── src/
│   │   ├── App.js         # Main router
│   │   ├── components/    # React components
│   │   └── pages/         # Page components
│   └── package.json
├── tests/
│   └── e2e/               # Playwright E2E tests
└── memory/
    ├── PRD.md             # Product requirements
    ├── CHANGELOG.md       # Version history
    └── API_DOCUMENTATION.md
```

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend E2E tests
cd frontend
npx playwright test
```

## Environment Variables

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=riskshield
JWT_SECRET=your-secret-key
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://your-domain.com
```

## License

Proprietary - All Rights Reserved

## Support

For support, contact: support@riskshield.example.com
