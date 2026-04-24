from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
from fastapi import status as http_status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import json
import jwt
import bcrypt
import io
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required")
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    LOD1_USER = "LOD1_USER"
    LOD2_USER = "LOD2_USER"
    ADMIN = "ADMIN"

class AssessmentStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class RiskSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ControlEffectiveness(str, Enum):
    EFFECTIVE = "EFFECTIVE"
    PARTIALLY_EFFECTIVE = "PARTIALLY_EFFECTIVE"
    INEFFECTIVE = "INEFFECTIVE"
    NOT_TESTED = "NOT_TESTED"

class WorkflowTrigger(str, Enum):
    ON_HIGH_RISK = "ON_HIGH_RISK"
    ON_FAILED_CONTROL = "ON_FAILED_CONTROL"
    ON_TREND_WORSENING = "ON_TREND_WORSENING"
    MANUAL = "MANUAL"

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: UserRole
    business_unit: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole
    business_unit: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class Risk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    severity: RiskSeverity
    framework: str
    control_ids: List[str] = []
    likelihood: str
    impact: str
    mitigation: str
    regulatory_reference: Optional[str] = None

class Control(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    effectiveness: ControlEffectiveness
    test_result: Optional[str] = None
    evidence_ids: List[str] = []
    framework: str
    last_tested: Optional[datetime] = None

class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    type: str
    description: str
    status: str
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = {}

class AssessmentCreate(BaseModel):
    name: str
    system_name: str
    business_unit: str
    frameworks: List[str]
    description: Optional[str] = None
    scenario: Optional[str] = None

class Assessment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    system_name: str
    business_unit: str
    frameworks: List[str]
    description: Optional[str] = None
    scenario: Optional[str] = None
    status: AssessmentStatus = AssessmentStatus.PENDING
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    risks: List[Risk] = []
    controls: List[Control] = []
    evidence: List[Evidence] = []
    summary: Dict[str, Any] = {}

class Regulation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    framework: str
    file_name: str
    content: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    chunk_count: int = 0

class WorkflowStep(BaseModel):
    action: str
    params: Dict[str, Any] = {}

class Workflow(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    trigger: WorkflowTrigger
    conditions: Dict[str, Any] = {}
    steps: List[WorkflowStep]
    active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WorkflowRun(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    assessment_id: str
    status: str
    results: List[Dict[str, Any]] = []
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Issue Management Models
class IssueStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    REMEDIATION_TESTING = "REMEDIATION_TESTING"
    VERIFICATION = "VERIFICATION"
    CLOSED = "CLOSED"
    ACCEPTED = "ACCEPTED"

class IssuePriority(str, Enum):
    P1 = "P1"  # Critical - 24 hours
    P2 = "P2"  # High - 7 days
    P3 = "P3"  # Medium - 30 days
    P4 = "P4"  # Low - 90 days

class IssueType(str, Enum):
    CONTROL_DEFICIENCY = "CONTROL_DEFICIENCY"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    AUDIT_FINDING = "AUDIT_FINDING"
    REGULATORY_GAP = "REGULATORY_GAP"
    SECURITY_VULNERABILITY = "SECURITY_VULNERABILITY"

class Issue(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issue_number: str = Field(default_factory=lambda: f"ISSUE-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}")
    title: str
    description: str
    type: IssueType
    severity: RiskSeverity
    priority: IssuePriority
    status: IssueStatus = IssueStatus.NEW
    source: str  # "Assessment", "Audit", "Manual"
    source_id: Optional[str] = None
    business_unit: str
    owner: Optional[str] = None
    assignees: List[str] = []
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    related_risk_ids: List[str] = []
    related_control_ids: List[str] = []
    frameworks: List[str] = []
    impact: Optional[str] = None
    remediation_plan_id: Optional[str] = None
    progress: int = 0
    sla_status: str = "On Track"

class IssueCreate(BaseModel):
    title: str
    description: str
    type: IssueType
    severity: RiskSeverity
    priority: IssuePriority
    source: str
    source_id: Optional[str] = None
    business_unit: str
    owner: Optional[str] = None
    assignees: List[str] = []
    frameworks: List[str] = []
    impact: Optional[str] = None

# Remediation Plan Models
class RemediationStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    TESTING = "TESTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class RemediationStep(BaseModel):
    step_number: int
    description: str
    owner: str
    status: str = "Not Started"
    target_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None

class RemediationPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_number: str = Field(default_factory=lambda: f"PLAN-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}")
    issue_id: str
    title: str
    approach: str
    root_cause: Optional[str] = None
    steps: List[RemediationStep] = []
    resources_required: Dict[str, Any] = {}
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    status: RemediationStatus = RemediationStatus.DRAFT
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    target_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    progress_percentage: int = 0

class RemediationPlanCreate(BaseModel):
    issue_id: str
    title: str
    approach: str
    root_cause: Optional[str] = None
    steps: List[RemediationStep] = []
    resources_required: Dict[str, Any] = {}
    estimated_cost: Optional[float] = None
    target_completion: Optional[datetime] = None

# Risk Acceptance Models
class RiskAcceptanceStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"

class RiskAcceptance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    acceptance_number: str = Field(default_factory=lambda: f"RA-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}")
    risk_id: Optional[str] = None
    issue_id: str
    title: str
    justification: str
    business_impact: str
    compensating_controls: List[str] = []
    duration_months: int
    review_frequency: str
    expiry_date: datetime
    requested_by: str
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: RiskAcceptanceStatus = RiskAcceptanceStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    conditions: List[str] = []

class RiskAcceptanceCreate(BaseModel):
    issue_id: str
    title: str
    justification: str
    business_impact: str
    compensating_controls: List[str] = []
    duration_months: int
    review_frequency: str = "Monthly"
    conditions: List[str] = []

# Agent Activity Tracking Models
class ActivityStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    WAITING = "WAITING"

class AgentActivity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    agent_name: str
    activity_type: str
    description: str
    status: ActivityStatus
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

# Knowledge Graph Models
class EntityType(str, Enum):
    SYSTEM = "SYSTEM"
    RISK = "RISK"
    CONTROL = "CONTROL"
    REGULATION = "REGULATION"
    BUSINESS_UNIT = "BUSINESS_UNIT"
    PERSON = "PERSON"
    VENDOR = "VENDOR"
    ASSET = "ASSET"

class KnowledgeEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: EntityType
    name: str
    description: Optional[str] = None
    properties: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RelationType(str, Enum):
    MITIGATES = "MITIGATES"
    AFFECTS = "AFFECTS"
    IMPLEMENTS = "IMPLEMENTS"
    OWNED_BY = "OWNED_BY"
    REQUIRES = "REQUIRES"
    DEPENDS_ON = "DEPENDS_ON"
    MONITORS = "MONITORS"
    COMPLIES_WITH = "COMPLIES_WITH"

class KnowledgeRelation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_entity_id: str
    target_entity_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Model Observability Models
class ModelMetrics(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    model_name: str
    endpoint: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    cost_usd: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = True
    error_message: Optional[str] = None

# Explainability Models
class ExplanationType(str, Enum):
    RISK_IDENTIFIED = "RISK_IDENTIFIED"
    CONTROL_RATED = "CONTROL_RATED"
    EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"
    DECISION_MADE = "DECISION_MADE"

class Explanation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    explanation_type: ExplanationType
    entity_id: str  # ID of risk, control, etc.
    entity_name: str
    reasoning: str
    confidence_score: float  # 0-1
    supporting_facts: List[str] = []
    regulatory_references: List[str] = []
    alternative_considerations: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Multi-Agent System
class MockLLMClient:
    """Mock LLM client - in production would connect to Ollama"""
    
    async def generate(self, prompt: str, context: str = "") -> str:
        # Mock responses based on prompt keywords
        if "risk" in prompt.lower():
            return json.dumps({
                "risks": [
                    {"title": "Insufficient Access Controls", "severity": "HIGH", "framework": "NIST CSF"},
                    {"title": "Weak Encryption Standards", "severity": "MEDIUM", "framework": "ISO 27001"},
                    {"title": "Inadequate Audit Logging", "severity": "MEDIUM", "framework": "SOC2"}
                ]
            })
        elif "control" in prompt.lower():
            return json.dumps({
                "controls": [
                    {"name": "IAM Policy Review", "effectiveness": "EFFECTIVE"},
                    {"name": "Encryption at Rest", "effectiveness": "PARTIALLY_EFFECTIVE"},
                    {"name": "Log Monitoring", "effectiveness": "INEFFECTIVE"}
                ]
            })
        return "{}"

class RAGAgent:
    """Regulation & Knowledge Agent - handles regulatory document retrieval"""
    
    def __init__(self):
        self.vector_store = {}  # Mock FAISS - would use real FAISS in production
    
    async def query(self, question: str, frameworks: List[str]) -> str:
        # Mock RAG retrieval
        context = f"Relevant regulatory requirements for {', '.join(frameworks)}:\n"
        context += "- Access controls must follow principle of least privilege (NIST CSF PR.AC-4)\n"
        context += "- Encryption must use AES-256 or equivalent (ISO 27001 A.10.1.1)\n"
        context += "- Audit logs must be retained for minimum 90 days (SOC2 CC7.2)\n"
        return context

class RiskAssessmentAgent:
    """Identifies and assesses risks"""
    
    def __init__(self, llm_client: MockLLMClient, rag_agent: RAGAgent):
        self.llm = llm_client
        self.rag = rag_agent
    
    async def assess(self, system_name: str, frameworks: List[str], description: str) -> List[Risk]:
        # Get regulatory context from RAG
        _ = await self.rag.query(f"risks for {system_name}", frameworks)
        
        # Mock risk generation (in production, use LLM with context)
        risks = [
            Risk(
                title="Inadequate Identity and Access Management",
                description="IAM policies do not enforce MFA and principle of least privilege",
                severity=RiskSeverity.HIGH,
                framework="NIST CSF, ISO 27001",
                likelihood="High",
                impact="Critical",
                mitigation="Implement MFA, role-based access controls, and periodic access reviews",
                regulatory_reference="NIST CSF PR.AC-1, ISO 27001 A.9.2.1"
            ),
            Risk(
                title="Insufficient Data Encryption",
                description="Data at rest not encrypted with industry-standard algorithms",
                severity=RiskSeverity.MEDIUM,
                framework="ISO 27001, PCI-DSS",
                likelihood="Medium",
                impact="High",
                mitigation="Enable AES-256 encryption for all data stores",
                regulatory_reference="ISO 27001 A.10.1.1, PCI-DSS Req 3.4"
            ),
            Risk(
                title="Weak Audit Logging and Monitoring",
                description="Insufficient logging of security events and access attempts",
                severity=RiskSeverity.MEDIUM,
                framework="SOC2, GDPR",
                likelihood="Medium",
                impact="Medium",
                mitigation="Implement comprehensive logging with SIEM integration",
                regulatory_reference="SOC2 CC7.2, GDPR Article 32"
            ),
            Risk(
                title="Unpatched Vulnerabilities",
                description="Critical security patches not applied within SLA",
                severity=RiskSeverity.CRITICAL,
                framework="NIST CSF, Basel III",
                likelihood="High",
                impact="Critical",
                mitigation="Establish patch management process with automated scanning",
                regulatory_reference="NIST CSF PR.IP-12, Basel BCBS 239"
            )
        ]
        
        return risks[:3]  # Return subset for variation

class ControlTestingAgent:
    """Tests control effectiveness"""
    
    def __init__(self, llm_client: MockLLMClient):
        self.llm = llm_client
    
    async def test_controls(self, risks: List[Risk], frameworks: List[str]) -> List[Control]:
        controls = [
            Control(
                name="Multi-Factor Authentication (MFA)",
                description="MFA enforced for all privileged accounts",
                effectiveness=ControlEffectiveness.PARTIALLY_EFFECTIVE,
                test_result="MFA enabled but not enforced for 15% of admin accounts",
                framework="NIST CSF, ISO 27001",
                last_tested=datetime.now(timezone.utc)
            ),
            Control(
                name="Encryption at Rest",
                description="AES-256 encryption for all databases",
                effectiveness=ControlEffectiveness.EFFECTIVE,
                test_result="All databases encrypted with AES-256. Key rotation: 90 days",
                framework="ISO 27001, PCI-DSS",
                last_tested=datetime.now(timezone.utc)
            ),
            Control(
                name="Security Event Logging",
                description="Comprehensive audit trail for security events",
                effectiveness=ControlEffectiveness.INEFFECTIVE,
                test_result="Logging incomplete. Missing events: password changes, privilege escalation",
                framework="SOC2, GDPR",
                last_tested=datetime.now(timezone.utc)
            ),
            Control(
                name="Vulnerability Scanning",
                description="Automated weekly vulnerability scans",
                effectiveness=ControlEffectiveness.PARTIALLY_EFFECTIVE,
                test_result="Scans running but 23 critical vulnerabilities unresolved >30 days",
                framework="NIST CSF, Basel III",
                last_tested=datetime.now(timezone.utc)
            ),
            Control(
                name="Access Review Process",
                description="Quarterly access rights review",
                effectiveness=ControlEffectiveness.EFFECTIVE,
                test_result="Process documented and executed on schedule. 5% access revoked last quarter",
                framework="NIST CSF, ISO 27001",
                last_tested=datetime.now(timezone.utc)
            )
        ]
        
        return controls

class EvidenceCollectionAgent:
    """Collects evidence from various sources"""
    
    async def collect(self, controls: List[Control]) -> List[Evidence]:
        evidence = [
            Evidence(
                source="AWS IAM",
                type="Configuration",
                description="IAM policy export showing MFA configuration",
                status="Collected",
                metadata={"accounts_with_mfa": 85, "total_accounts": 100}
            ),
            Evidence(
                source="Database Config",
                type="Configuration",
                description="RDS encryption settings and key rotation policy",
                status="Collected",
                metadata={"encryption_algorithm": "AES-256", "key_rotation_days": 90}
            ),
            Evidence(
                source="CloudWatch Logs",
                type="Log Analysis",
                description="Security event log sample showing coverage gaps",
                status="Collected",
                metadata={"events_logged": ["login", "api_call"], "events_missing": ["password_change", "privilege_escalation"]}
            ),
            Evidence(
                source="Vulnerability Scanner",
                type="Scan Report",
                description="Weekly vulnerability scan results",
                status="Collected",
                metadata={"critical": 23, "high": 45, "medium": 120, "scan_date": datetime.now(timezone.utc).isoformat()}
            )
        ]
        
        return evidence

class ReportingAgent:
    """Generates reports and summaries"""
    
    def generate_summary(self, assessment: Assessment) -> Dict[str, Any]:
        critical_risks = len([r for r in assessment.risks if r.severity == RiskSeverity.CRITICAL])
        high_risks = len([r for r in assessment.risks if r.severity == RiskSeverity.HIGH])
        medium_risks = len([r for r in assessment.risks if r.severity == RiskSeverity.MEDIUM])
        low_risks = len([r for r in assessment.risks if r.severity == RiskSeverity.LOW])
        
        ineffective_controls = len([c for c in assessment.controls if c.effectiveness == ControlEffectiveness.INEFFECTIVE])
        partially_effective = len([c for c in assessment.controls if c.effectiveness == ControlEffectiveness.PARTIALLY_EFFECTIVE])
        effective_controls = len([c for c in assessment.controls if c.effectiveness == ControlEffectiveness.EFFECTIVE])
        
        overall_score = max(0, 100 - (critical_risks * 25) - (high_risks * 15) - (ineffective_controls * 10))
        
        return {
            "overall_score": overall_score,
            "risk_summary": {
                "critical": critical_risks,
                "high": high_risks,
                "medium": medium_risks,
                "low": low_risks,
                "total": len(assessment.risks)
            },
            "control_summary": {
                "effective": effective_controls,
                "partially_effective": partially_effective,
                "ineffective": ineffective_controls,
                "total": len(assessment.controls)
            },
            "compliance_status": "Non-Compliant" if ineffective_controls > 0 or critical_risks > 0 else "Compliant",
            "recommendations": [
                "Address all critical and high severity risks within 30 days",
                "Remediate ineffective controls immediately",
                "Implement compensating controls for partially effective controls",
                "Schedule follow-up assessment in 90 days"
            ]
        }

class AssessmentOrchestrator:
    """Orchestrates the multi-agent assessment process"""
    
    def __init__(self):
        self.llm = MockLLMClient()
        self.rag_agent = RAGAgent()
        self.risk_agent = RiskAssessmentAgent(self.llm, self.rag_agent)
        self.control_agent = ControlTestingAgent(self.llm)
        self.evidence_agent = EvidenceCollectionAgent()
        self.reporting_agent = ReportingAgent()
    
    async def log_activity(self, session_id: str, agent_name: str, activity_type: str, 
                          description: str, status: str, inputs: Dict = None, 
                          outputs: Dict = None, duration_ms: int = None):
        """Log agent activity for visibility"""
        activity = AgentActivity(
            session_id=session_id,
            agent_name=agent_name,
            activity_type=activity_type,
            description=description,
            status=ActivityStatus(status),
            inputs=inputs or {},
            outputs=outputs or {},
            duration_ms=duration_ms
        )
        
        if status in ["COMPLETED", "FAILED"]:
            activity.completed_at = datetime.now(timezone.utc)
        
        doc = activity.model_dump()
        doc['started_at'] = doc['started_at'].isoformat()
        if doc.get('completed_at'):
            doc['completed_at'] = doc['completed_at'].isoformat()
        
        await db.agent_activities.insert_one(doc)
        return activity
    
    async def log_explanation(self, session_id: str, explanation_type: str, 
                             entity_id: str, entity_name: str, reasoning: str,
                             confidence: float, supporting_facts: List[str],
                             regulatory_refs: List[str]):
        """Log explanation for explainability"""
        explanation = Explanation(
            session_id=session_id,
            explanation_type=ExplanationType(explanation_type),
            entity_id=entity_id,
            entity_name=entity_name,
            reasoning=reasoning,
            confidence_score=confidence,
            supporting_facts=supporting_facts,
            regulatory_references=regulatory_refs
        )
        
        doc = explanation.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.explanations.insert_one(doc)
        return explanation
    
    async def log_model_metrics(self, session_id: str, model_name: str, endpoint: str,
                                prompt_tokens: int, completion_tokens: int,
                                latency_ms: int, success: bool = True):
        """Log model metrics for observability"""
        # Simple cost calculation (example rates)
        cost_per_1k_prompt = 0.0015  # $0.0015 per 1K prompt tokens
        cost_per_1k_completion = 0.002  # $0.002 per 1K completion tokens
        
        cost = (prompt_tokens / 1000 * cost_per_1k_prompt + 
                completion_tokens / 1000 * cost_per_1k_completion)
        
        metrics = ModelMetrics(
            session_id=session_id,
            model_name=model_name,
            endpoint=endpoint,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            cost_usd=cost,
            success=success
        )
        
        doc = metrics.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.model_metrics.insert_one(doc)
        return metrics
    
    async def build_knowledge_graph(self, assessment: Assessment):
        """Build knowledge graph from assessment"""
        entities = []
        relations = []
        
        # Create system entity
        system_entity = KnowledgeEntity(
            entity_type=EntityType.SYSTEM,
            name=assessment.system_name,
            description=assessment.description,
            properties={
                "business_unit": assessment.business_unit,
                "frameworks": assessment.frameworks
            }
        )
        entities.append(system_entity)
        
        # Create risk entities and relations
        for risk in assessment.risks:
            risk_entity = KnowledgeEntity(
                entity_type=EntityType.RISK,
                name=risk.title,
                description=risk.description,
                properties={
                    "severity": risk.severity,
                    "framework": risk.framework,
                    "likelihood": risk.likelihood,
                    "impact": risk.impact
                }
            )
            entities.append(risk_entity)
            
            # Relation: System -> Affects -> Risk
            relation = KnowledgeRelation(
                source_entity_id=system_entity.id,
                target_entity_id=risk_entity.id,
                relation_type=RelationType.AFFECTS,
                properties={"assessment_id": assessment.id}
            )
            relations.append(relation)
        
        # Create control entities and relations
        for control in assessment.controls:
            control_entity = KnowledgeEntity(
                entity_type=EntityType.CONTROL,
                name=control.name,
                description=control.description,
                properties={
                    "effectiveness": control.effectiveness,
                    "framework": control.framework
                }
            )
            entities.append(control_entity)
            
            # Relation: Control -> Mitigates -> Risk (simplified)
            if assessment.risks:
                relation = KnowledgeRelation(
                    source_entity_id=control_entity.id,
                    target_entity_id=assessment.risks[0].id if hasattr(assessment.risks[0], 'id') else str(uuid.uuid4()),
                    relation_type=RelationType.MITIGATES,
                    properties={"assessment_id": assessment.id}
                )
                relations.append(relation)
        
        # Save to database
        for entity in entities:
            doc = entity.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            doc['updated_at'] = doc['updated_at'].isoformat()
            await db.knowledge_entities.insert_one(doc)
        
        for relation in relations:
            doc = relation.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            await db.knowledge_relations.insert_one(doc)
        
        return {"entities": len(entities), "relations": len(relations)}
    
    async def run_assessment(self, assessment: Assessment) -> Assessment:
        session_id = assessment.id
        start_time = datetime.now(timezone.utc)
        
        try:
            assessment.status = AssessmentStatus.IN_PROGRESS
            
            # Step 1: Risk Assessment
            await self.log_activity(
                session_id, "RiskAssessmentAgent", "risk_identification",
                "Identifying technology risks based on system and frameworks",
                "RUNNING"
            )
            
            step_start = datetime.now(timezone.utc)
            risks = await self.risk_agent.assess(
                assessment.system_name,
                assessment.frameworks,
                assessment.description or ""
            )
            step_duration = int((datetime.now(timezone.utc) - step_start).total_seconds() * 1000)
            
            assessment.risks = risks
            
            await self.log_activity(
                session_id, "RiskAssessmentAgent", "risk_identification",
                f"Identified {len(risks)} risks",
                "COMPLETED",
                inputs={"system": assessment.system_name, "frameworks": assessment.frameworks},
                outputs={"risk_count": len(risks)},
                duration_ms=step_duration
            )
            
            # Log model metrics
            await self.log_model_metrics(
                session_id, "llama-3-70b", "risk_assessment",
                prompt_tokens=450, completion_tokens=320,
                latency_ms=step_duration
            )
            
            # Log explanations for each risk
            for risk in risks:
                await self.log_explanation(
                    session_id, "RISK_IDENTIFIED",
                    risk.id, risk.title,
                    f"Risk identified due to {risk.description}. Likelihood: {risk.likelihood}, Impact: {risk.impact}",
                    confidence=0.85,
                    supporting_facts=[
                        f"System {assessment.system_name} analyzed against {', '.join(assessment.frameworks)}",
                        f"Severity rated as {risk.severity} based on likelihood and impact matrix"
                    ],
                    regulatory_refs=[risk.regulatory_reference] if risk.regulatory_reference else []
                )
            
            # Step 2: Control Testing
            await self.log_activity(
                session_id, "ControlTestingAgent", "control_testing",
                "Testing control effectiveness",
                "RUNNING"
            )
            
            step_start = datetime.now(timezone.utc)
            controls = await self.control_agent.test_controls(risks, assessment.frameworks)
            step_duration = int((datetime.now(timezone.utc) - step_start).total_seconds() * 1000)
            
            assessment.controls = controls
            
            await self.log_activity(
                session_id, "ControlTestingAgent", "control_testing",
                f"Tested {len(controls)} controls",
                "COMPLETED",
                inputs={"risk_count": len(risks)},
                outputs={"control_count": len(controls)},
                duration_ms=step_duration
            )
            
            # Log model metrics
            await self.log_model_metrics(
                session_id, "llama-3-70b", "control_testing",
                prompt_tokens=380, completion_tokens=290,
                latency_ms=step_duration
            )
            
            # Log explanations for controls
            for control in controls:
                await self.log_explanation(
                    session_id, "CONTROL_RATED",
                    control.id, control.name,
                    f"Control effectiveness rated as {control.effectiveness}. {control.test_result}",
                    confidence=0.90,
                    supporting_facts=[
                        f"Control tested against framework requirements: {control.framework}",
                        f"Test result: {control.test_result}"
                    ],
                    regulatory_refs=[]
                )
            
            # Step 3: Evidence Collection
            await self.log_activity(
                session_id, "EvidenceCollectionAgent", "evidence_collection",
                "Collecting evidence from systems",
                "RUNNING"
            )
            
            step_start = datetime.now(timezone.utc)
            evidence = await self.evidence_agent.collect(controls)
            step_duration = int((datetime.now(timezone.utc) - step_start).total_seconds() * 1000)
            
            assessment.evidence = evidence
            
            await self.log_activity(
                session_id, "EvidenceCollectionAgent", "evidence_collection",
                f"Collected {len(evidence)} evidence items",
                "COMPLETED",
                inputs={"control_count": len(controls)},
                outputs={"evidence_count": len(evidence)},
                duration_ms=step_duration
            )
            
            # Step 4: Generate Summary
            await self.log_activity(
                session_id, "ReportingAgent", "report_generation",
                "Generating assessment summary",
                "RUNNING"
            )
            
            step_start = datetime.now(timezone.utc)
            summary = self.reporting_agent.generate_summary(assessment)
            step_duration = int((datetime.now(timezone.utc) - step_start).total_seconds() * 1000)
            
            assessment.summary = summary
            
            await self.log_activity(
                session_id, "ReportingAgent", "report_generation",
                "Summary generated",
                "COMPLETED",
                inputs={},
                outputs={"overall_score": summary["overall_score"]},
                duration_ms=step_duration
            )
            
            # Step 5: Build Knowledge Graph
            await self.log_activity(
                session_id, "KnowledgeGraphBuilder", "graph_construction",
                "Building organizational knowledge graph",
                "RUNNING"
            )
            
            step_start = datetime.now(timezone.utc)
            kg_stats = await self.build_knowledge_graph(assessment)
            step_duration = int((datetime.now(timezone.utc) - step_start).total_seconds() * 1000)
            
            await self.log_activity(
                session_id, "KnowledgeGraphBuilder", "graph_construction",
                f"Knowledge graph built with {kg_stats['entities']} entities and {kg_stats['relations']} relations",
                "COMPLETED",
                inputs={},
                outputs=kg_stats,
                duration_ms=step_duration
            )
            
            assessment.status = AssessmentStatus.COMPLETED
            assessment.completed_at = datetime.now(timezone.utc)
            
            total_duration = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            logger.info(f"Assessment {session_id} completed in {total_duration}ms")
            
            return assessment
            
        except Exception as e:
            assessment.status = AssessmentStatus.FAILED
            assessment.summary = {"error": str(e)}
            
            await self.log_activity(
                session_id, "Orchestrator", "assessment",
                f"Assessment failed: {str(e)}",
                "FAILED"
            )
            
            return assessment

# Workflow Engine
class WorkflowEngine:
    """Manages workflow execution and GRC integrations"""
    
    async def evaluate_triggers(self, assessment: Assessment) -> List[Workflow]:
        # Find workflows that should be triggered
        workflows_cursor = db.workflows.find({"active": True}, {"_id": 0})
        workflows = await workflows_cursor.to_list(1000)
        
        triggered = []
        for wf_dict in workflows:
            workflow = Workflow(**wf_dict)
            
            if workflow.trigger == WorkflowTrigger.ON_HIGH_RISK:
                high_risks = [r for r in assessment.risks if r.severity in [RiskSeverity.CRITICAL, RiskSeverity.HIGH]]
                if high_risks:
                    triggered.append(workflow)
            
            elif workflow.trigger == WorkflowTrigger.ON_FAILED_CONTROL:
                failed = [c for c in assessment.controls if c.effectiveness == ControlEffectiveness.INEFFECTIVE]
                if failed:
                    triggered.append(workflow)
        
        return triggered
    
    async def execute_workflow(self, workflow: Workflow, assessment: Assessment) -> WorkflowRun:
        run = WorkflowRun(
            workflow_id=workflow.id,
            assessment_id=assessment.id,
            status="COMPLETED"
        )
        
        for step in workflow.steps:
            if step.action == "CREATE_GRC_TICKET":
                ticket_result = {
                    "action": "CREATE_GRC_TICKET",
                    "ticket_id": f"RISK-{uuid.uuid4().hex[:8].upper()}",
                    "system": step.params.get("system", "ServiceNow"),
                    "created": True
                }
                run.results.append(ticket_result)
            
            elif step.action == "SEND_EMAIL":
                email_result = {
                    "action": "SEND_EMAIL",
                    "to": step.params.get("to", []),
                    "sent": True
                }
                run.results.append(email_result)
        
        # Save workflow run
        doc = run.model_dump()
        doc['executed_at'] = doc['executed_at'].isoformat()
        await db.workflow_runs.insert_one(doc)
        
        return run

# Auth utilities
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user_doc)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# Initialize demo users
async def init_demo_users():
    existing = await db.users.find_one({"email": "lod1@bank.com"})
    if not existing:
        users = [
            {
                **User(
                    email="lod1@bank.com",
                    full_name="John Smith",
                    role=UserRole.LOD1_USER,
                    business_unit="Technology Risk"
                ).model_dump(),
                "password": hash_password("password123")
            },
            {
                **User(
                    email="lod2@bank.com",
                    full_name="Sarah Johnson",
                    role=UserRole.LOD2_USER,
                    business_unit="Compliance"
                ).model_dump(),
                "password": hash_password("password123")
            }
        ]
        for user in users:
            user['created_at'] = user['created_at'].isoformat()
            await db.users.insert_one(user)

# API Routes
@api_router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user_doc = await db.users.find_one({"email": request.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(request.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_doc.pop("password")
    if isinstance(user_doc['created_at'], str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    user = User(**user_doc)
    token = create_token(user)
    
    return TokenResponse(access_token=token, user=user)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/regulations")
async def list_regulations(current_user: User = Depends(get_current_user)):
    regs = await db.regulations.find({}, {"_id": 0, "content": 0}).to_list(1000)
    for reg in regs:
        if isinstance(reg.get('uploaded_at'), str):
            reg['uploaded_at'] = datetime.fromisoformat(reg['uploaded_at'])
    return regs

@api_router.post("/regulations/upload")
async def upload_regulation(
    name: str,
    framework: str,
    content: str,
    current_user: User = Depends(get_current_user)
):
    regulation = Regulation(
        name=name,
        framework=framework,
        file_name=f"{name}.txt",
        content=content,
        uploaded_by=current_user.id,
        chunk_count=len(content) // 500
    )
    
    doc = regulation.model_dump()
    doc['uploaded_at'] = doc['uploaded_at'].isoformat()
    await db.regulations.insert_one(doc)
    
    return {"message": "Regulation uploaded successfully", "id": regulation.id}

@api_router.get("/controls")
async def list_controls(current_user: User = Depends(get_current_user)):
    # Return sample controls library
    return [
        {"id": "1", "name": "Multi-Factor Authentication", "framework": "NIST CSF, ISO 27001"},
        {"id": "2", "name": "Encryption at Rest", "framework": "ISO 27001, PCI-DSS"},
        {"id": "3", "name": "Security Event Logging", "framework": "SOC2, GDPR"},
        {"id": "4", "name": "Vulnerability Scanning", "framework": "NIST CSF, Basel III"},
        {"id": "5", "name": "Access Review Process", "framework": "NIST CSF, ISO 27001"}
    ]

@api_router.post("/assessments", response_model=Assessment)
async def create_assessment(
    request: AssessmentCreate,
    current_user: User = Depends(get_current_user)
):
    assessment = Assessment(
        **request.model_dump(),
        created_by=current_user.id
    )
    
    # Save initial assessment
    doc = assessment.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('completed_at'):
        doc['completed_at'] = doc['completed_at'].isoformat()
    await db.assessments.insert_one(doc)
    
    # Run assessment asynchronously (in production, use background tasks)
    orchestrator = AssessmentOrchestrator()
    assessment = await orchestrator.run_assessment(assessment)
    
    # Update assessment with results
    update_doc = assessment.model_dump()
    update_doc['created_at'] = update_doc['created_at'].isoformat()
    if update_doc.get('completed_at'):
        update_doc['completed_at'] = update_doc['completed_at'].isoformat()
    
    await db.assessments.replace_one({"id": assessment.id}, update_doc)
    
    # Check for workflow triggers
    workflow_engine = WorkflowEngine()
    triggered_workflows = await workflow_engine.evaluate_triggers(assessment)
    
    for workflow in triggered_workflows:
        await workflow_engine.execute_workflow(workflow, assessment)
    
    return assessment

@api_router.get("/assessments", response_model=List[Assessment])
async def list_assessments(current_user: User = Depends(get_current_user)):
    query = {}
    if current_user.role == UserRole.LOD1_USER:
        query["created_by"] = current_user.id
    
    assessments = await db.assessments.find(query, {"_id": 0}).to_list(1000)
    
    for assessment in assessments:
        if isinstance(assessment.get('created_at'), str):
            assessment['created_at'] = datetime.fromisoformat(assessment['created_at'])
        if assessment.get('completed_at') and isinstance(assessment['completed_at'], str):
            assessment['completed_at'] = datetime.fromisoformat(assessment['completed_at'])
    
    return assessments

@api_router.get("/assessments/{assessment_id}", response_model=Assessment)
async def get_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    assessment_doc = await db.assessments.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment_doc:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    if isinstance(assessment_doc.get('created_at'), str):
        assessment_doc['created_at'] = datetime.fromisoformat(assessment_doc['created_at'])
    if assessment_doc.get('completed_at') and isinstance(assessment_doc['completed_at'], str):
        assessment_doc['completed_at'] = datetime.fromisoformat(assessment_doc['completed_at'])
    
    return Assessment(**assessment_doc)

@api_router.post("/assessments/{assessment_id}/trigger-workflows")
async def trigger_workflows(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    assessment_doc = await db.assessments.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment_doc:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    if isinstance(assessment_doc.get('created_at'), str):
        assessment_doc['created_at'] = datetime.fromisoformat(assessment_doc['created_at'])
    if assessment_doc.get('completed_at') and isinstance(assessment_doc['completed_at'], str):
        assessment_doc['completed_at'] = datetime.fromisoformat(assessment_doc['completed_at'])
    
    assessment = Assessment(**assessment_doc)
    
    workflow_engine = WorkflowEngine()
    triggered = await workflow_engine.evaluate_triggers(assessment)
    
    runs = []
    for workflow in triggered:
        run = await workflow_engine.execute_workflow(workflow, assessment)
        runs.append(run.model_dump())
    
    return {"triggered_count": len(runs), "runs": runs}

@api_router.post("/workflows", response_model=Workflow)
async def create_workflow(
    workflow: Workflow,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.LOD2_USER and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only LOD2 users can create workflows")
    
    workflow.created_by = current_user.id
    doc = workflow.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.workflows.insert_one(doc)
    
    return workflow

@api_router.get("/workflows", response_model=List[Workflow])
async def list_workflows(current_user: User = Depends(get_current_user)):
    workflows = await db.workflows.find({}, {"_id": 0}).to_list(1000)
    for wf in workflows:
        if isinstance(wf.get('created_at'), str):
            wf['created_at'] = datetime.fromisoformat(wf['created_at'])
    return workflows

@api_router.get("/analytics/summary")
async def analytics_summary(current_user: User = Depends(get_current_user)):
    total_assessments = await db.assessments.count_documents({})
    
    # Get all assessments for aggregation
    all_assessments = await db.assessments.find({}, {"_id": 0}).to_list(1000)
    
    high_risks_count = 0
    ineffective_controls_count = 0
    
    for assessment in all_assessments:
        for risk in assessment.get('risks', []):
            if risk.get('severity') in ['CRITICAL', 'HIGH']:
                high_risks_count += 1
        
        for control in assessment.get('controls', []):
            if control.get('effectiveness') == 'INEFFECTIVE':
                ineffective_controls_count += 1
    
    return {
        "total_assessments": total_assessments,
        "high_risks": high_risks_count,
        "ineffective_controls": ineffective_controls_count,
        "avg_compliance_score": 72,
        "frameworks_covered": ["NIST CSF", "ISO 27001", "SOC2", "PCI-DSS", "GDPR", "Basel III"]
    }

@api_router.get("/analytics/trends")
async def analytics_trends(current_user: User = Depends(get_current_user)):
    # Mock trend data
    return {
        "quarters": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"],
        "risk_scores": [65, 68, 72, 75],
        "compliance_scores": [70, 73, 75, 78],
        "assessments_count": [12, 15, 18, 21]
    }

# Issue Management Endpoints
@api_router.post("/issues", response_model=Issue)
async def create_issue(
    issue_data: IssueCreate,
    current_user: User = Depends(get_current_user)
):
    issue = Issue(**issue_data.model_dump(), created_by=current_user.id)
    
    # Calculate due date based on priority
    due_days = {"P1": 1, "P2": 7, "P3": 30, "P4": 90}
    issue.due_date = datetime.now(timezone.utc) + timedelta(days=due_days[issue.priority])
    
    doc = issue.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('due_date'):
        doc['due_date'] = doc['due_date'].isoformat()
    if doc.get('closed_at'):
        doc['closed_at'] = doc['closed_at'].isoformat()
    
    await db.issues.insert_one(doc)
    return issue

@api_router.get("/issues", response_model=List[Issue])
async def list_issues(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    query = {}
    if current_user.role == UserRole.LOD1_USER:
        query["$or"] = [
            {"created_by": current_user.id},
            {"owner": current_user.email},
            {"assignees": current_user.email}
        ]
    
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    
    issues = await db.issues.find(query, {"_id": 0}).to_list(1000)
    
    for issue in issues:
        if isinstance(issue.get('created_at'), str):
            issue['created_at'] = datetime.fromisoformat(issue['created_at'])
        if issue.get('due_date') and isinstance(issue['due_date'], str):
            issue['due_date'] = datetime.fromisoformat(issue['due_date'])
        if issue.get('closed_at') and isinstance(issue['closed_at'], str):
            issue['closed_at'] = datetime.fromisoformat(issue['closed_at'])
    
    return issues

@api_router.get("/issues/{issue_id}", response_model=Issue)
async def get_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user)
):
    issue_doc = await db.issues.find_one({"id": issue_id}, {"_id": 0})
    if not issue_doc:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    if isinstance(issue_doc.get('created_at'), str):
        issue_doc['created_at'] = datetime.fromisoformat(issue_doc['created_at'])
    if issue_doc.get('due_date') and isinstance(issue_doc['due_date'], str):
        issue_doc['due_date'] = datetime.fromisoformat(issue_doc['due_date'])
    if issue_doc.get('closed_at') and isinstance(issue_doc['closed_at'], str):
        issue_doc['closed_at'] = datetime.fromisoformat(issue_doc['closed_at'])
    
    return Issue(**issue_doc)

@api_router.put("/issues/{issue_id}", response_model=Issue)
async def update_issue(
    issue_id: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    issue_doc = await db.issues.find_one({"id": issue_id}, {"_id": 0})
    if not issue_doc:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Update fields
    for key, value in updates.items():
        if key in issue_doc and key not in ['id', 'issue_number', 'created_by', 'created_at']:
            issue_doc[key] = value
    
    # Handle datetime serialization
    for date_field in ['created_at', 'due_date', 'closed_at']:
        if issue_doc.get(date_field) and isinstance(issue_doc[date_field], datetime):
            issue_doc[date_field] = issue_doc[date_field].isoformat()
    
    await db.issues.replace_one({"id": issue_id}, issue_doc)
    
    # Convert back for response
    for date_field in ['created_at', 'due_date', 'closed_at']:
        if issue_doc.get(date_field) and isinstance(issue_doc[date_field], str):
            issue_doc[date_field] = datetime.fromisoformat(issue_doc[date_field])
    
    return Issue(**issue_doc)

# Remediation Plan Endpoints
@api_router.post("/remediation-plans", response_model=RemediationPlan)
async def create_remediation_plan(
    plan_data: RemediationPlanCreate,
    current_user: User = Depends(get_current_user)
):
    plan = RemediationPlan(**plan_data.model_dump(), created_by=current_user.id)
    
    doc = plan.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('approved_at'):
        doc['approved_at'] = doc['approved_at'].isoformat()
    if doc.get('target_completion'):
        doc['target_completion'] = doc['target_completion'].isoformat()
    if doc.get('actual_completion'):
        doc['actual_completion'] = doc['actual_completion'].isoformat()
    
    # Serialize dates in steps
    for step in doc.get('steps', []):
        if step.get('target_date') and isinstance(step['target_date'], datetime):
            step['target_date'] = step['target_date'].isoformat()
        if step.get('completion_date') and isinstance(step['completion_date'], datetime):
            step['completion_date'] = step['completion_date'].isoformat()
    
    await db.remediation_plans.insert_one(doc)
    
    # Link to issue
    await db.issues.update_one(
        {"id": plan.issue_id},
        {"$set": {"remediation_plan_id": plan.id}}
    )
    
    return plan

@api_router.get("/remediation-plans", response_model=List[RemediationPlan])
async def list_remediation_plans(current_user: User = Depends(get_current_user)):
    query = {}
    if current_user.role == UserRole.LOD1_USER:
        query["created_by"] = current_user.id
    
    plans = await db.remediation_plans.find(query, {"_id": 0}).to_list(1000)
    
    for plan in plans:
        if isinstance(plan.get('created_at'), str):
            plan['created_at'] = datetime.fromisoformat(plan['created_at'])
        if plan.get('approved_at') and isinstance(plan['approved_at'], str):
            plan['approved_at'] = datetime.fromisoformat(plan['approved_at'])
        if plan.get('target_completion') and isinstance(plan['target_completion'], str):
            plan['target_completion'] = datetime.fromisoformat(plan['target_completion'])
        if plan.get('actual_completion') and isinstance(plan['actual_completion'], str):
            plan['actual_completion'] = datetime.fromisoformat(plan['actual_completion'])
        
        # Deserialize dates in steps
        for step in plan.get('steps', []):
            if step.get('target_date') and isinstance(step['target_date'], str):
                step['target_date'] = datetime.fromisoformat(step['target_date'])
            if step.get('completion_date') and isinstance(step['completion_date'], str):
                step['completion_date'] = datetime.fromisoformat(step['completion_date'])
    
    return plans

# Risk Acceptance Endpoints
@api_router.post("/risk-acceptance", response_model=RiskAcceptance)
async def create_risk_acceptance(
    acceptance_data: RiskAcceptanceCreate,
    current_user: User = Depends(get_current_user)
):
    acceptance = RiskAcceptance(
        **acceptance_data.model_dump(),
        requested_by=current_user.id,
        expiry_date=datetime.now(timezone.utc) + timedelta(days=acceptance_data.duration_months * 30)
    )
    
    doc = acceptance.model_dump()
    doc['requested_at'] = doc['requested_at'].isoformat()
    doc['expiry_date'] = doc['expiry_date'].isoformat()
    if doc.get('approved_at'):
        doc['approved_at'] = doc['approved_at'].isoformat()
    
    await db.risk_acceptances.insert_one(doc)
    return acceptance

@api_router.get("/risk-acceptance", response_model=List[RiskAcceptance])
async def list_risk_acceptances(current_user: User = Depends(get_current_user)):
    query = {}
    if current_user.role == UserRole.LOD1_USER:
        query["requested_by"] = current_user.id
    
    acceptances = await db.risk_acceptances.find(query, {"_id": 0}).to_list(1000)
    
    for acc in acceptances:
        if isinstance(acc.get('requested_at'), str):
            acc['requested_at'] = datetime.fromisoformat(acc['requested_at'])
        if isinstance(acc.get('expiry_date'), str):
            acc['expiry_date'] = datetime.fromisoformat(acc['expiry_date'])
        if acc.get('approved_at') and isinstance(acc['approved_at'], str):
            acc['approved_at'] = datetime.fromisoformat(acc['approved_at'])
    
    return acceptances

@api_router.post("/risk-acceptance/{acceptance_id}/approve")
async def approve_risk_acceptance(
    acceptance_id: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.LOD2_USER and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only LOD2 users can approve risk acceptances")
    
    await db.risk_acceptances.update_one(
        {"id": acceptance_id},
        {
            "$set": {
                "status": "APPROVED",
                "approved_by": current_user.id,
                "approved_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Risk acceptance approved"}

# Agent Activity & Observability Endpoints
@api_router.get("/agent-activities/{session_id}")
async def get_agent_activities(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get real-time agent activities for a session"""
    activities = await db.agent_activities.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("started_at", 1).to_list(1000)
    
    for activity in activities:
        if isinstance(activity.get('started_at'), str):
            activity['started_at'] = datetime.fromisoformat(activity['started_at'])
        if activity.get('completed_at') and isinstance(activity['completed_at'], str):
            activity['completed_at'] = datetime.fromisoformat(activity['completed_at'])
    
    return activities

@api_router.get("/model-metrics/{session_id}")
async def get_model_metrics(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get model performance metrics for a session"""
    metrics = await db.model_metrics.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    for metric in metrics:
        if isinstance(metric.get('timestamp'), str):
            metric['timestamp'] = datetime.fromisoformat(metric['timestamp'])
    
    # Calculate aggregated stats
    total_tokens = sum(m.get('total_tokens', 0) for m in metrics)
    total_cost = sum(m.get('cost_usd', 0) for m in metrics)
    avg_latency = sum(m.get('latency_ms', 0) for m in metrics) / len(metrics) if metrics else 0
    
    return {
        "metrics": metrics,
        "summary": {
            "total_requests": len(metrics),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_latency_ms": int(avg_latency),
            "success_rate": sum(1 for m in metrics if m.get('success', True)) / len(metrics) if metrics else 1.0
        }
    }

@api_router.get("/explanations/{session_id}")
async def get_explanations(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get AI explanations for assessment decisions"""
    explanations = await db.explanations.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    
    for exp in explanations:
        if isinstance(exp.get('created_at'), str):
            exp['created_at'] = datetime.fromisoformat(exp['created_at'])
    
    return explanations

@api_router.get("/knowledge-graph")
async def get_knowledge_graph(
    entity_type: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get knowledge graph entities and relations"""
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    
    entities = await db.knowledge_entities.find(query, {"_id": 0}).limit(limit).to_list(limit)
    
    # Get entity IDs
    entity_ids = [e['id'] for e in entities]
    
    # Get relations for these entities
    relations = await db.knowledge_relations.find(
        {
            "$or": [
                {"source_entity_id": {"$in": entity_ids}},
                {"target_entity_id": {"$in": entity_ids}}
            ]
        },
        {"_id": 0}
    ).to_list(1000)
    
    # Deserialize dates
    for entity in entities:
        if isinstance(entity.get('created_at'), str):
            entity['created_at'] = datetime.fromisoformat(entity['created_at'])
        if isinstance(entity.get('updated_at'), str):
            entity['updated_at'] = datetime.fromisoformat(entity['updated_at'])
    
    for relation in relations:
        if isinstance(relation.get('created_at'), str):
            relation['created_at'] = datetime.fromisoformat(relation['created_at'])
    
    return {
        "entities": entities,
        "relations": relations,
        "stats": {
            "total_entities": len(entities),
            "total_relations": len(relations)
        }
    }

@api_router.get("/knowledge-graph/query")
async def query_knowledge_graph(
    entity_name: str,
    depth: int = 2,
    current_user: User = Depends(get_current_user)
):
    """Query knowledge graph starting from an entity"""
    # Find entity by name
    entity = await db.knowledge_entities.find_one(
        {"name": {"$regex": entity_name, "$options": "i"}},
        {"_id": 0}
    )
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Get all relations (simplified - in production use graph traversal)
    relations = await db.knowledge_relations.find(
        {
            "$or": [
                {"source_entity_id": entity['id']},
                {"target_entity_id": entity['id']}
            ]
        },
        {"_id": 0}
    ).to_list(1000)
    
    # Get related entities
    related_ids = set()
    for rel in relations:
        related_ids.add(rel['source_entity_id'])
        related_ids.add(rel['target_entity_id'])
    
    related_entities = await db.knowledge_entities.find(
        {"id": {"$in": list(related_ids)}},
        {"_id": 0}
    ).to_list(1000)
    
    return {
        "root_entity": entity,
        "related_entities": related_entities,
        "relations": relations
    }

@api_router.get("/observability/dashboard")
async def get_observability_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get observability dashboard data"""
    # Get recent metrics (last 24 hours)
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    
    recent_metrics = await db.model_metrics.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(100).to_list(100)
    
    # Calculate stats
    total_requests = len(recent_metrics)
    total_tokens = sum(m.get('total_tokens', 0) for m in recent_metrics)
    total_cost = sum(m.get('cost_usd', 0) for m in recent_metrics)
    avg_latency = sum(m.get('latency_ms', 0) for m in recent_metrics) / total_requests if total_requests > 0 else 0
    success_rate = sum(1 for m in recent_metrics if m.get('success', True)) / total_requests if total_requests > 0 else 1.0
    
    # Get activity summary
    recent_activities = await db.agent_activities.find(
        {},
        {"_id": 0}
    ).sort("started_at", -1).limit(50).to_list(50)
    
    completed_activities = sum(1 for a in recent_activities if a.get('status') == 'COMPLETED')
    failed_activities = sum(1 for a in recent_activities if a.get('status') == 'FAILED')
    
    # Get knowledge graph stats
    entity_count = await db.knowledge_entities.count_documents({})
    relation_count = await db.knowledge_relations.count_documents({})
    
    return {
        "model_performance": {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_latency_ms": int(avg_latency),
            "success_rate": round(success_rate * 100, 2)
        },
        "agent_activity": {
            "total_activities": len(recent_activities),
            "completed": completed_activities,
            "failed": failed_activities,
            "success_rate": round(completed_activities / len(recent_activities) * 100, 2) if recent_activities else 100
        },
        "knowledge_graph": {
            "total_entities": entity_count,
            "total_relations": relation_count
        },
        "recent_metrics": recent_metrics[:10],
        "recent_activities": recent_activities[:10]
    }

# Initialize
@app.on_event("startup")
async def startup():
    # Create demo users
    await init_demo_users()
    
    # Create database indexes for performance
    try:
        await db.assessments.create_index("created_by")
        await db.assessments.create_index("status")
        await db.assessments.create_index("business_unit")
        await db.assessments.create_index([("created_at", -1)])
        await db.users.create_index("email", unique=True)
        await db.workflows.create_index("trigger")
        await db.workflows.create_index("active")
        
        # New indexes for advanced features
        await db.agent_activities.create_index("session_id")
        await db.agent_activities.create_index([("started_at", -1)])
        await db.model_metrics.create_index("session_id")
        await db.model_metrics.create_index([("timestamp", -1)])
        await db.explanations.create_index("session_id")
        await db.knowledge_entities.create_index("entity_type")
        await db.knowledge_entities.create_index("name")
        await db.knowledge_relations.create_index("source_entity_id")
        await db.knowledge_relations.create_index("target_entity_id")
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")
    
    # Create sample workflow if none exist
    existing = await db.workflows.count_documents({})
    if existing == 0:
        sample_workflow = Workflow(
            name="High Risk Auto-Escalation",
            description="Automatically create GRC tickets for high/critical risks",
            trigger=WorkflowTrigger.ON_HIGH_RISK,
            conditions={"min_severity": "HIGH"},
            steps=[
                WorkflowStep(
                    action="CREATE_GRC_TICKET",
                    params={"system": "ServiceNow", "priority": "High"}
                ),
                WorkflowStep(
                    action="SEND_EMAIL",
                    params={"to": ["risk-team@bank.com"], "template": "high_risk_alert"}
                )
            ],
            created_by="system"
        )
        doc = sample_workflow.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.workflows.insert_one(doc)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
