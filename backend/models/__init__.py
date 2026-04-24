# Pydantic models for the application
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


# ============ ENUMS ============

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


class IssueStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    REMEDIATION_TESTING = "REMEDIATION_TESTING"
    VERIFICATION = "VERIFICATION"
    CLOSED = "CLOSED"
    ACCEPTED = "ACCEPTED"


class IssuePriority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class IssueType(str, Enum):
    CONTROL_DEFICIENCY = "CONTROL_DEFICIENCY"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    AUDIT_FINDING = "AUDIT_FINDING"
    REGULATORY_GAP = "REGULATORY_GAP"
    SECURITY_VULNERABILITY = "SECURITY_VULNERABILITY"


class RemediationStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    TESTING = "TESTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RiskAcceptanceStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


class ActivityStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    WAITING = "WAITING"


class EntityType(str, Enum):
    SYSTEM = "SYSTEM"
    RISK = "RISK"
    CONTROL = "CONTROL"
    REGULATION = "REGULATION"
    BUSINESS_UNIT = "BUSINESS_UNIT"
    PERSON = "PERSON"
    VENDOR = "VENDOR"
    ASSET = "ASSET"


class RelationType(str, Enum):
    MITIGATES = "MITIGATES"
    AFFECTS = "AFFECTS"
    IMPLEMENTS = "IMPLEMENTS"
    OWNED_BY = "OWNED_BY"
    REQUIRES = "REQUIRES"
    DEPENDS_ON = "DEPENDS_ON"
    MONITORS = "MONITORS"
    COMPLIES_WITH = "COMPLIES_WITH"


class ExplanationType(str, Enum):
    RISK_IDENTIFIED = "RISK_IDENTIFIED"
    CONTROL_RATED = "CONTROL_RATED"
    EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"
    DECISION_MADE = "DECISION_MADE"


class LLMProvider(str, Enum):
    EMERGENT = "EMERGENT"
    ANTHROPIC = "ANTHROPIC"
    OPENAI = "OPENAI"
    GEMINI = "GEMINI"
    MOCK = "MOCK"
    OLLAMA = "OLLAMA"
    AZURE = "AZURE"
    VERTEX_AI = "VERTEX_AI"


class ControlStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    REJECTED = "REJECTED"


class ControlTestStatus(str, Enum):
    NOT_TESTED = "NOT_TESTED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    FAILED = "FAILED"


class ControlCategory(str, Enum):
    TECHNICAL = "TECHNICAL"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    PHYSICAL = "PHYSICAL"
    OPERATIONAL = "OPERATIONAL"
    AI_GOVERNANCE = "AI_GOVERNANCE"
    AI_TECHNICAL = "AI_TECHNICAL"
    AI_OPERATIONAL = "AI_OPERATIONAL"


class AIRiskCategory(str, Enum):
    UNACCEPTABLE = "UNACCEPTABLE"
    HIGH = "HIGH"
    LIMITED = "LIMITED"
    MINIMAL = "MINIMAL"


# ============ USER MODELS ============

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


# ============ RISK & CONTROL MODELS ============

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


# ============ ASSESSMENT MODELS ============

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


# ============ REGULATION MODELS ============

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


# ============ WORKFLOW MODELS ============

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


# ============ ISSUE MANAGEMENT MODELS ============

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
    source: str
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


# ============ REMEDIATION MODELS ============

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


# ============ RISK ACCEPTANCE MODELS ============

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


# ============ AGENT ACTIVITY MODELS ============

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


# ============ KNOWLEDGE GRAPH MODELS ============

class KnowledgeEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: EntityType
    name: str
    description: Optional[str] = None
    properties: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeRelation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_entity_id: str
    target_entity_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============ MODEL OBSERVABILITY MODELS ============

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


class Explanation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    explanation_type: ExplanationType
    entity_id: str
    entity_name: str
    reasoning: str
    confidence_score: float
    supporting_facts: List[str] = []
    regulatory_references: List[str] = []
    alternative_considerations: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============ LLM CONFIG MODELS ============

class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.EMERGENT
    model_name: str = "claude-sonnet-4-5-20250929"
    api_key: Optional[str] = None  # User-supplied key for ANTHROPIC / OPENAI / GEMINI
    azure_endpoint: Optional[str] = None
    azure_deployment: Optional[str] = None
    vertex_project: Optional[str] = None
    vertex_location: Optional[str] = None
    ollama_host: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4096


class LLMConfigUpdate(BaseModel):
    provider: Optional[LLMProvider] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_deployment: Optional[str] = None
    vertex_project: Optional[str] = None
    vertex_location: Optional[str] = None
    ollama_host: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None



# ============ CUSTOM CONTROL LIBRARY MODELS ============

class CustomControl(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    control_id: str = Field(default_factory=lambda: f"CTRL-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}")
    name: str
    description: str
    category: ControlCategory
    frameworks: List[str] = []
    regulatory_references: List[str] = []
    implementation_guidance: Optional[str] = None
    testing_procedure: Optional[str] = None
    evidence_requirements: List[str] = []
    frequency: str = "Annual"  # Annual, Quarterly, Monthly, Continuous
    owner: Optional[str] = None
    status: ControlStatus = ControlStatus.DRAFT
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    last_tested: Optional[datetime] = None
    next_test_due: Optional[datetime] = None
    effectiveness: ControlEffectiveness = ControlEffectiveness.NOT_TESTED
    is_ai_control: bool = False
    ai_risk_category: Optional[AIRiskCategory] = None
    source: Optional[str] = None  # e.g. "REGULATORY_GAP", "IMPORT", None for manually created
    source_file: Optional[str] = None  # Framework / filename the control was derived from


class CustomControlCreate(BaseModel):
    name: str
    description: str
    category: ControlCategory
    frameworks: List[str] = []
    regulatory_references: List[str] = []
    implementation_guidance: Optional[str] = None
    testing_procedure: Optional[str] = None
    evidence_requirements: List[str] = []
    frequency: str = "Annual"
    owner: Optional[str] = None
    is_ai_control: bool = False
    ai_risk_category: Optional[AIRiskCategory] = None


class CustomControlUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ControlCategory] = None
    frameworks: Optional[List[str]] = None
    regulatory_references: Optional[List[str]] = None
    implementation_guidance: Optional[str] = None
    testing_procedure: Optional[str] = None
    evidence_requirements: Optional[List[str]] = None
    frequency: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[ControlStatus] = None
    is_ai_control: Optional[bool] = None
    ai_risk_category: Optional[AIRiskCategory] = None


# ============ CONTROL TEST MODELS ============

class ControlTest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_id: str = Field(default_factory=lambda: f"TEST-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}")
    control_id: str
    control_name: str
    assessment_id: Optional[str] = None
    test_type: str = "Manual"  # Manual, Automated, AI-Assisted
    status: ControlTestStatus = ControlTestStatus.NOT_TESTED
    tester: str
    tester_role: str  # LOD1_USER or LOD2_USER
    test_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    test_procedure: str
    expected_result: str
    actual_result: Optional[str] = None
    evidence_collected: List[str] = []
    evidence_links: List[str] = []
    effectiveness_rating: ControlEffectiveness = ControlEffectiveness.NOT_TESTED
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    reviewer: Optional[str] = None
    reviewer_role: Optional[str] = None
    review_date: Optional[datetime] = None
    review_comments: Optional[str] = None
    review_status: Optional[str] = None  # APPROVED, REJECTED, NEEDS_REWORK


class ControlTestCreate(BaseModel):
    control_id: str
    assessment_id: Optional[str] = None
    test_type: str = "Manual"
    test_procedure: str
    expected_result: str


class ControlTestUpdate(BaseModel):
    actual_result: Optional[str] = None
    evidence_collected: Optional[List[str]] = None
    evidence_links: Optional[List[str]] = None
    effectiveness_rating: Optional[ControlEffectiveness] = None
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    status: Optional[ControlTestStatus] = None


class ControlTestReview(BaseModel):
    review_comments: str
    review_status: str  # APPROVED, REJECTED, NEEDS_REWORK


# ============ GAP ANALYSIS MODELS ============

class ControlGap(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gap_id: str = Field(default_factory=lambda: f"GAP-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}")
    framework: str
    requirement: str
    requirement_id: str
    gap_description: str
    risk_if_unaddressed: str
    severity: RiskSeverity
    current_state: str
    target_state: str
    recommended_controls: List[str] = []
    remediation_options: List[str] = []
    estimated_effort: str  # Low, Medium, High
    business_unit: str
    identified_by: str
    identified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "OPEN"  # OPEN, IN_PROGRESS, REMEDIATED, ACCEPTED
    assigned_to: Optional[str] = None
    target_date: Optional[datetime] = None
    closed_at: Optional[datetime] = None


# ============ AI COMPLIANCE MODELS ============

class AISystem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    system_id: str = Field(default_factory=lambda: f"AI-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}")
    name: str
    description: str
    purpose: str
    ai_type: str  # ML Model, Deep Learning, LLM, Computer Vision, etc.
    deployment_status: str  # Development, Testing, Production, Retired
    risk_category: AIRiskCategory
    business_unit: str
    owner: str
    data_types_processed: List[str] = []
    decision_impact: str  # Low, Medium, High, Critical
    human_oversight_level: str  # None, Limited, Significant, Full
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_assessment_date: Optional[datetime] = None
    next_assessment_due: Optional[datetime] = None
    eu_ai_act_compliant: Optional[bool] = None
    nist_ai_rmf_compliant: Optional[bool] = None


class AISystemCreate(BaseModel):
    name: str
    description: str
    purpose: str
    ai_type: str
    deployment_status: str
    risk_category: AIRiskCategory
    business_unit: str
    owner: str
    data_types_processed: List[str] = []
    decision_impact: str
    human_oversight_level: str


class AIControlAssessment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assessment_id: str = Field(default_factory=lambda: f"AICA-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}")
    ai_system_id: str
    ai_system_name: str
    framework: str  # EU_AI_ACT, NIST_AI_RMF
    assessment_type: str  # Initial, Periodic, Triggered
    assessor: str
    assessment_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "IN_PROGRESS"  # IN_PROGRESS, COMPLETED, REQUIRES_ACTION
    overall_compliance: Optional[str] = None  # COMPLIANT, PARTIALLY_COMPLIANT, NON_COMPLIANT
    control_results: List[Dict[str, Any]] = []
    findings: List[str] = []
    recommendations: List[str] = []
    required_actions: List[str] = []
    reviewer: Optional[str] = None
    review_date: Optional[datetime] = None
    review_comments: Optional[str] = None


class AIControlAssessmentCreate(BaseModel):
    ai_system_id: str
    framework: str  # EU_AI_ACT, NIST_AI_RMF
    assessment_type: str = "Initial"



# ============ AUTOMATED CONTROL TESTING MODELS ============

class AutomatedTestType(str, Enum):
    CONFIGURATION_CHECK = "CONFIGURATION_CHECK"
    LOG_ANALYSIS = "LOG_ANALYSIS"
    ACCESS_REVIEW = "ACCESS_REVIEW"
    VULNERABILITY_SCAN = "VULNERABILITY_SCAN"
    POLICY_COMPLIANCE = "POLICY_COMPLIANCE"
    DATA_QUALITY = "DATA_QUALITY"
    AI_BIAS_CHECK = "AI_BIAS_CHECK"
    AI_FAIRNESS = "AI_FAIRNESS"
    AI_EXPLAINABILITY = "AI_EXPLAINABILITY"


class EvidenceSource(str, Enum):
    AWS_CONFIG = "AWS_CONFIG"
    AZURE_POLICY = "AZURE_POLICY"
    GCP_SECURITY = "GCP_SECURITY"
    SPLUNK = "SPLUNK"
    CLOUDWATCH = "CLOUDWATCH"
    IAM_EXPORT = "IAM_EXPORT"
    VULNERABILITY_SCANNER = "VULNERABILITY_SCANNER"
    SIEM = "SIEM"
    GRC_SYSTEM = "GRC_SYSTEM"
    MANUAL_UPLOAD = "MANUAL_UPLOAD"
    AI_ANALYSIS = "AI_ANALYSIS"


class AutomatedTestRun(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: f"ATR-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}")
    control_id: str
    control_name: str
    test_type: AutomatedTestType
    triggered_by: str  # user_id or "SCHEDULED"
    trigger_reason: str = "Manual"  # Manual, Scheduled, Risk-Based, Incident
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    status: str = "RUNNING"  # RUNNING, COMPLETED, FAILED, CANCELLED
    evidence_sources: List[str] = []
    evidence_collected: List[Dict[str, Any]] = []
    ai_analysis: Optional[Dict[str, Any]] = None
    effectiveness_rating: Optional[str] = None
    confidence_score: float = 0.0
    findings: List[str] = []
    recommendations: List[str] = []
    auto_generated_report: Optional[str] = None
    requires_human_review: bool = True
    reviewed_by: Optional[str] = None
    review_date: Optional[datetime] = None
    review_outcome: Optional[str] = None  # CONFIRMED, OVERRIDDEN, ESCALATED


class AutomatedTestConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    control_id: str
    test_type: AutomatedTestType
    schedule: str = "MANUAL"  # MANUAL, DAILY, WEEKLY, MONTHLY, QUARTERLY
    evidence_sources: List[EvidenceSource] = []
    test_parameters: Dict[str, Any] = {}
    pass_criteria: Dict[str, Any] = {}
    auto_remediate: bool = False
    escalation_threshold: int = 3  # Number of failures before escalation
    notification_emails: List[str] = []
    enabled: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AutomatedTestConfigCreate(BaseModel):
    control_id: str
    test_type: AutomatedTestType
    schedule: str = "MANUAL"
    evidence_sources: List[str] = []
    test_parameters: Dict[str, Any] = {}
    pass_criteria: Dict[str, Any] = {}
    auto_remediate: bool = False
    escalation_threshold: int = 3
    notification_emails: List[str] = []


# ============ GAP REMEDIATION MODELS ============

class RemediationPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RemediationAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str  # IMPLEMENT_CONTROL, UPDATE_POLICY, CONFIGURE_SYSTEM, TRAINING, ACCEPT_RISK
    description: str
    assigned_to: Optional[str] = None
    target_date: Optional[datetime] = None
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, BLOCKED
    completion_date: Optional[datetime] = None
    evidence: List[str] = []
    notes: Optional[str] = None


class GapRemediation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    remediation_id: str = Field(default_factory=lambda: f"REM-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}")
    gap_id: str
    gap_description: str
    framework: str
    requirement_id: str
    priority: RemediationPriority
    status: str = "DRAFT"  # DRAFT, APPROVED, IN_PROGRESS, COMPLETED, ACCEPTED
    
    # AI-generated recommendations
    ai_recommended_controls: List[Dict[str, Any]] = []
    ai_implementation_plan: Optional[str] = None
    ai_effort_estimate: Optional[str] = None
    ai_risk_if_delayed: Optional[str] = None
    
    # Selected approach
    selected_approach: Optional[str] = None  # IMPLEMENT, COMPENSATING, ACCEPT_RISK
    selected_controls: List[str] = []  # Control IDs
    compensating_controls: List[str] = []
    
    # Execution
    actions: List[RemediationAction] = []
    progress_percentage: int = 0
    
    # Tracking
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    target_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    
    # Verification
    verification_required: bool = True
    verification_method: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None


class GapRemediationCreate(BaseModel):
    gap_id: str
    priority: RemediationPriority = RemediationPriority.MEDIUM
    selected_approach: Optional[str] = None
    target_completion: Optional[datetime] = None


class ControlRecommendation(BaseModel):
    control_name: str
    description: str
    category: str
    frameworks: List[str]
    implementation_effort: str  # Low, Medium, High
    effectiveness_estimate: str  # High, Medium, Low
    cost_estimate: str  # Low, Medium, High
    time_to_implement: str  # Days, Weeks, Months
    prerequisites: List[str] = []
    related_controls: List[str] = []
    regulatory_coverage: List[str] = []
    ai_confidence: float = 0.0
    rationale: str = ""
