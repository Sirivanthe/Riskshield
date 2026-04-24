# RiskShield Changelog

## [2.2.0] - March 20, 2026

### Added - FAISS Vector Store & RAG
- **FAISS Vector Store**: Production-ready vector database with IndexFlatIP for cosine similarity
- **Multi-tenant Vector Storage**: Each tenant gets isolated vector index (database-per-tenant)
- **PDF Parser**: Document ingestion using PyMuPDF with intelligent text extraction
- **Chunking Service**: Configurable chunk size (500 words) with overlap for context preservation
- **Embedding Service**: OpenAI text-embedding-3-small with Emergent LLM key integration
- **RAG Query Endpoint**: `/api/rag/documents/search` for semantic document search

### Added - ServiceNow Integration
- **ServiceNow Connector**: Full REST API integration for GRC ticket management
- **Incident Creation**: Create incidents for risk findings and control deficiencies
- **Mock Mode**: Built-in mock mode for development/testing without ServiceNow access
- **Bulk Operations**: Create multiple incidents at once
- **Ticket Lifecycle**: Create, update, close tickets with resolution notes

### Added - Trend Analytics
- **Time-Series Tracking**: Record and track metrics over time
- **10 Metric Types**: Risk score, compliance score, control effectiveness, open issues, critical/high risks, ineffective controls, gap count, remediation progress
- **Aggregation**: Daily, weekly, monthly, quarterly data aggregation
- **Visualization**: Interactive charts with sparklines and full trend charts
- **Period Comparison**: Compare current vs previous period with trend indicators
- **Sample Data Generation**: Generate realistic demo data for presentations

### Added - Multi-Tenancy
- **Database-per-Tenant**: Complete data isolation with separate MongoDB databases
- **Tenant Management API**: Create, suspend, activate, delete tenants
- **Tenant Statistics**: View collection counts and database stats per tenant
- **Auto-Initialization**: New tenants get all required collections with indexes

### Added - Frontend
- **Trend Analytics Page** (`/trend-analytics`): Full dashboard with metric cards and charts
- **Navigation**: Added trend analytics to sidebar

### API Endpoints Added
- `/api/rag/documents/upload` - Upload and ingest PDF documents
- `/api/rag/documents/search` - Semantic search across documents
- `/api/rag/documents/stats` - Vector store statistics
- `/api/rag/documents/rag-query` - RAG context retrieval
- `/api/trends/dashboard` - Dashboard trend data for charts
- `/api/trends/metrics/{type}` - Individual metric trends
- `/api/trends/comparison/{type}` - Period-over-period comparison
- `/api/trends/snapshot` - Record current metric snapshot
- `/api/servicenow/incidents` - CRUD for ServiceNow incidents
- `/api/servicenow/incidents/risk` - Create risk-specific incidents
- `/api/servicenow/incidents/control-deficiency` - Create control deficiency incidents
- `/api/tenants/` - Tenant management (list, create, get, suspend, activate, delete)

---

## [2.1.0] - March 20, 2026

### Added - Automated Control Testing
- **AI-Powered Test Execution**: Automated control testing with configurable test types
- **Evidence Collection**: Automated evidence gathering from multiple sources (AWS Config, IAM, SIEM, etc.)
- **Test Types**: Configuration check, log analysis, access review, vulnerability scan, policy compliance, AI bias/fairness/explainability
- **Confidence Scoring**: AI-generated confidence scores for test results
- **Human Review Workflow**: LOD2 review and approval for high-risk automated tests
- **Automated Reports**: AI-generated test reports with findings and recommendations

### Added - Gap Remediation
- **AI Recommendations**: Intelligent control recommendations for identified gaps
- **Framework-Specific Guidance**: Tailored recommendations for NIST CSF, EU AI Act, NIST AI RMF
- **Implementation Planning**: Automated action item generation with timelines
- **Approach Selection**: Support for IMPLEMENT, COMPENSATING, and ACCEPT_RISK approaches
- **Progress Tracking**: Real-time progress monitoring with percentage completion
- **Verification Workflow**: LOD2 verification of completed remediations

### Added - Frontend Pages
- **Automated Testing Page** (`/automated-testing`): Full UI for running and reviewing automated tests
- **Gap Remediation Page** (`/gap-remediation`): Complete interface for gap analysis and remediation planning
- **Navigation Links**: Sidebar navigation for new pages

### Fixed
- Fixed `timedelta` import error in agents/__init__.py that prevented remediation approach selection

### Testing
- Added 26 new backend tests for automated testing and gap remediation APIs
- Added 33 new frontend E2E tests for both pages
- Total test count: 160+ tests (backend pytest + frontend Playwright)

---

## [2.0.0] - March 20, 2026

### Added - Multi-Provider LLM Support
- **Azure AI Agent Service Integration**: Enterprise-grade Azure AI integration with Agent Service support
- **Google Vertex AI Integration**: Full support for Vertex AI Agent Builder with Gemini models
- **Ollama Integration**: Air-gapped deployment support with local LLM capabilities
- **Mock Provider**: Development and testing without external dependencies
- **LLM Configuration UI**: Admin panel for managing LLM providers with real-time testing

### Added - Modular Backend Architecture
- Refactored monolithic `server.py` into modular structure:
  - `/models/` - Pydantic models and enums
  - `/services/` - Business logic (auth, llm_client)
  - `/agents/` - Multi-agent AI system
  - `/db/` - Database connection utilities
  - `/routes/` - API route modules

### Added - Multi-Agent AI System
- **RAG Agent**: Regulatory document retrieval and context injection
- **Risk Assessment Agent**: AI-powered risk identification with framework alignment
- **Control Testing Agent**: Automated control effectiveness evaluation
- **Evidence Collection Agent**: Multi-source evidence gathering
- **Reporting Agent**: Comprehensive assessment summaries
- **Knowledge Graph Builder**: Organizational context mapping

### Added - AI Observability Features
- Real-time agent activity tracking
- Model metrics (tokens, latency, cost)
- AI decision explanations with confidence scores
- Knowledge graph visualization

### Added - Issue Management
- Issue creation with severity and priority
- Remediation planning
- Risk acceptance workflow
- SLA tracking

### Added - Comprehensive Documentation
- Enterprise README
- API Documentation
- Product Requirements Document
- Deployment guides

### Improved - Admin Panel
- Tabbed interface (LLM Config, Regulations, System Info)
- Visual provider cards with status indicators
- Real-time LLM connection testing
- Supported frameworks display

### Fixed
- Demo user initialization now checks each user individually
- MongoDB ObjectId serialization in all responses
- DateTime handling across all endpoints

---

## [1.0.0] - Initial Release

### Added
- Basic FastAPI backend with MongoDB
- React frontend with routing
- JWT authentication (LOD1/LOD2 roles)
- Assessment creation wizard
- Dashboard with risk metrics
- Workflow automation

---

## Roadmap

### Planned for v2.1.0
- [ ] Real FAISS vector store integration
- [ ] PyMuPDF PDF parsing
- [ ] Advanced analytics dashboard
- [ ] Time-series trend analysis

### Planned for v3.0.0
- [ ] What-if risk simulations
- [ ] Real GRC tool integrations
- [ ] Multi-tenancy support
- [ ] Real-time collaboration
