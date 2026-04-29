# FastAPI Application Entry Point
# Technology Risk and Control Assessment Platform
from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import modules
from db import db, init_indexes, close_connection
from models import (
    User, UserRole, LoginRequest, TokenResponse,
    Assessment, AssessmentCreate, AssessmentStatus,
    Risk, Control, Evidence, RiskSeverity, ControlEffectiveness,
    Regulation, Workflow, WorkflowStep, WorkflowRun, WorkflowTrigger,
    Issue, IssueCreate, IssueStatus, IssuePriority, IssueType,
    RemediationPlan, RemediationPlanCreate, RemediationStatus, RemediationStep,
    RiskAcceptance, RiskAcceptanceCreate, RiskAcceptanceStatus,
    AgentActivity, ActivityStatus, KnowledgeEntity, KnowledgeRelation,
    ModelMetrics, Explanation, LLMConfig, LLMConfigUpdate, LLMProvider,
    CustomControl, CustomControlCreate, CustomControlUpdate, ControlStatus,
    ControlTest, ControlTestCreate, ControlTestUpdate, ControlTestReview, ControlTestStatus,
    ControlGap, ControlCategory, AIRiskCategory,
    AISystem, AISystemCreate, AIControlAssessment, AIControlAssessmentCreate,
    AutomatedTestRun, AutomatedTestConfig, AutomatedTestConfigCreate, AutomatedTestType, EvidenceSource,
    GapRemediation, GapRemediationCreate, RemediationPriority, RemediationAction, ControlRecommendation
)
from services.auth import (
    verify_password, create_token, get_current_user, 
    hash_password, init_demo_users, security
)
from services.llm_client import LLMClientFactory
from agents import AssessmentOrchestrator, AutomatedControlTestingAgent, GapRemediationAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="RiskShield - Technology Risk & Control Platform",
    description="AI-powered multi-agent system for technology risk assessment and control testing",
    version="2.0.0"
)

# Main API router
api_router = APIRouter(prefix="/api")


# ============ AUTH ROUTES ============

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login and get JWT token"""
    user_doc = await db.users.find_one({"email": request.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(request.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_doc.pop("password")
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    user = User(**user_doc)
    token = create_token(user)
    
    return TokenResponse(access_token=token, user=user)


@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user


# ============ LLM CONFIGURATION ROUTES ============

def _safe_llm_config(config: LLMConfig) -> Dict[str, Any]:
    """Return LLM config with api_key masked (never expose the raw key)."""
    data = config.model_dump()
    raw_key = data.pop("api_key", None)
    data["api_key_set"] = bool(raw_key)
    data["api_key_last4"] = raw_key[-4:] if raw_key and len(raw_key) >= 4 else None
    return data


@api_router.get("/llm/config")
async def get_llm_config(current_user: User = Depends(get_current_user)):
    """Get current LLM configuration (api_key is masked)."""
    return _safe_llm_config(LLMClientFactory.get_current_config())


@api_router.put("/llm/config")
async def update_llm_config(
    config_update: LLMConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update LLM configuration (Admin/LOD2 only). Accepts user-supplied api_key."""
    if current_user.role not in [UserRole.ADMIN, UserRole.LOD2_USER]:
        raise HTTPException(status_code=403, detail="Only Admin or LOD2 users can update LLM configuration")

    current_config = LLMClientFactory.get_current_config()

    update_data = config_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is None:
            continue
        setattr(current_config, key, value)

    if current_config.provider in (LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GEMINI):
        if not current_config.api_key:
            raise HTTPException(
                status_code=400,
                detail=f"{current_config.provider.value} provider requires an api_key.",
            )

    LLMClientFactory.update_config(current_config)
    await LLMClientFactory.save_to_db(current_config)

    return _safe_llm_config(current_config)


@api_router.delete("/llm/config/api-key")
async def clear_llm_api_key(current_user: User = Depends(get_current_user)):
    """Remove the stored user-supplied API key."""
    if current_user.role not in [UserRole.ADMIN, UserRole.LOD2_USER]:
        raise HTTPException(status_code=403, detail="Only Admin or LOD2 users can modify LLM configuration")

    cfg = LLMClientFactory.get_current_config()
    cfg.api_key = None
    LLMClientFactory.update_config(cfg)
    await LLMClientFactory.save_to_db(cfg)
    return _safe_llm_config(cfg)


@api_router.get("/llm/providers")
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
                "id": LLMProvider.MOCK.value,
                "name": "Mock (Development)",
                "description": "Mock LLM for development and testing.",
                "requires_credentials": False,
            },
        ]
    }


@api_router.get("/llm/health")
async def check_llm_health(current_user: User = Depends(get_current_user)):
    """Check health of current LLM configuration"""
    return await LLMClientFactory.health_check()


@api_router.post("/llm/test")
async def test_llm(
    prompt: str = "Hello, are you working?",
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Test the current LLM configuration"""
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
                "completion": result.get("completion_tokens", 0)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": LLMClientFactory.get_current_config().provider.value
        }


# ============ REGULATION ROUTES ============

@api_router.get("/regulations")
async def list_regulations(current_user: User = Depends(get_current_user)):
    """List all regulations"""
    regs = await db.regulations.find({}, {"_id": 0, "content": 0}).to_list(1000)
    for reg in regs:
        if isinstance(reg.get('uploaded_at'), str):
            reg['uploaded_at'] = datetime.fromisoformat(reg['uploaded_at'])
    return regs


from pydantic import BaseModel

class RegulationUploadRequest(BaseModel):
    name: str
    framework: str
    content: str
    file_name: Optional[str] = None


@api_router.post("/regulations/upload")
async def upload_regulation(
    request: RegulationUploadRequest,
    current_user: User = Depends(get_current_user)
):
    """Upload a regulation document to the Regulations library."""
    regulation = Regulation(
        name=request.name,
        framework=request.framework,
        file_name=request.file_name or f"{request.name}.txt",
        content=request.content,
        uploaded_by=current_user.id,
        chunk_count=max(1, len(request.content) // 500)
    )

    doc = regulation.model_dump()
    doc['uploaded_at'] = doc['uploaded_at'].isoformat()
    await db.regulations.insert_one(doc)

    return {"message": "Regulation uploaded successfully", "id": regulation.id, "regulation": {
        "id": regulation.id,
        "name": regulation.name,
        "framework": regulation.framework,
        "file_name": regulation.file_name,
        "chunk_count": regulation.chunk_count,
    }}


@api_router.post("/regulations/upload-file")
async def upload_regulation_file(
    file: UploadFile = File(...),
    name: str = Form(...),
    framework: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a regulation directly from a PDF or text file. Extracts the text
    (PyMuPDF for PDFs, UTF-8 decode for everything else) and persists it to the
    Regulations library in one call.
    """
    raw = await file.read()
    filename = file.filename or "regulation"
    content = ""

    if filename.lower().endswith(".pdf"):
        try:
            from services.pdf_parser import PDFParserService
            parsed = PDFParserService().parse_pdf_bytes(raw, filename)
            content = (parsed.text_content or "").strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF parsing failed: {e}")
    else:
        content = raw.decode("utf-8", errors="ignore").strip()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file has no extractable text")

    regulation = Regulation(
        name=name,
        framework=framework,
        file_name=filename,
        content=content,
        uploaded_by=current_user.id,
        chunk_count=max(1, len(content) // 500),
    )
    doc = regulation.model_dump()
    doc['uploaded_at'] = doc['uploaded_at'].isoformat()
    await db.regulations.insert_one(doc)

    return {
        "message": "Regulation uploaded successfully",
        "id": regulation.id,
        "char_count": len(content),
        "regulation": {
            "id": regulation.id,
            "name": regulation.name,
            "framework": regulation.framework,
            "file_name": regulation.file_name,
            "chunk_count": regulation.chunk_count,
        }
    }


@api_router.post("/regulations/{regulation_id}/reanalyze")
async def reanalyze_regulation(
    regulation_id: str,
    tenant_id: str = "default",
    current_user: User = Depends(get_current_user)
):
    """Re-run LLM requirement extraction and control mapping for a saved regulation."""
    reg = await db.regulations.find_one({"id": regulation_id}, {"_id": 0})
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")

    from services.control_analysis_service import ControlAnalysisService
    service = ControlAnalysisService(tenant_id=tenant_id)
    result = await service.map_to_regulation(
        reg.get("content", ""),
        reg.get("framework", reg.get("name", "")),
    )
    return {
        "regulation_id": regulation_id,
        "framework": reg.get("framework"),
        "compliance_score": result.get("compliance_score"),
        "total_requirements": result.get("total_requirements"),
        "coverage_summary": result.get("coverage_summary"),
        "gaps": result.get("gaps", []),
        "parser_used": result.get("parser_used"),
    }


@api_router.delete("/regulations/{regulation_id}")
async def delete_regulation(
    regulation_id: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only Admin can delete regulations")
    res = await db.regulations.delete_one({"id": regulation_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Regulation not found")
    return {"deleted": True, "id": regulation_id}


@api_router.get("/controls")
async def list_controls(current_user: User = Depends(get_current_user)):
    """List sample controls library"""
    return [
        {"id": "1", "name": "Multi-Factor Authentication", "framework": "NIST CSF, ISO 27001"},
        {"id": "2", "name": "Encryption at Rest", "framework": "ISO 27001, PCI-DSS"},
        {"id": "3", "name": "Security Event Logging", "framework": "SOC2, GDPR"},
        {"id": "4", "name": "Vulnerability Scanning", "framework": "NIST CSF, Basel III"},
        {"id": "5", "name": "Access Review Process", "framework": "NIST CSF, ISO 27001"}
    ]


# ============ ASSESSMENT ROUTES ============

@api_router.post("/assessments", response_model=Assessment)
async def create_assessment(
    request: AssessmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Create a new assessment. The multi-agent AI orchestration runs in the
    background so the HTTP request returns immediately (<1s) with status
    IN_PROGRESS. Clients poll GET /api/assessments/{id} or the list endpoint
    to watch the status transition to COMPLETED / FAILED."""
    assessment = Assessment(
        **request.model_dump(),
        created_by=current_user.id
    )
    assessment.status = AssessmentStatus.IN_PROGRESS

    # Save initial assessment
    doc = assessment.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('completed_at'):
        doc['completed_at'] = doc['completed_at'].isoformat()
    await db.assessments.insert_one(doc)

    # Kick off orchestration in the background so we don't block the request.
    background_tasks.add_task(_run_assessment_async, assessment.id)

    return assessment


async def _run_assessment_async(assessment_id: str):
    """Background worker: runs the multi-agent orchestrator and persists the
    final assessment. Any failure flips status to FAILED with an error note."""
    try:
        doc = await db.assessments.find_one({"id": assessment_id}, {"_id": 0})
        if not doc:
            logging.getLogger(__name__).warning(
                "assessment %s vanished before background run", assessment_id
            )
            return
        if isinstance(doc.get('created_at'), str):
            doc['created_at'] = datetime.fromisoformat(doc['created_at'])
        if doc.get('completed_at') and isinstance(doc['completed_at'], str):
            doc['completed_at'] = datetime.fromisoformat(doc['completed_at'])
        assessment = Assessment(**doc)

        orchestrator = AssessmentOrchestrator()
        assessment = await orchestrator.run_assessment(assessment)

        update_doc = assessment.model_dump()
        update_doc['created_at'] = update_doc['created_at'].isoformat()
        if update_doc.get('completed_at'):
            update_doc['completed_at'] = update_doc['completed_at'].isoformat()
        await db.assessments.replace_one({"id": assessment.id}, update_doc)

        # Fire workflow triggers after the run completes.
        try:
            triggered_workflows = await evaluate_workflow_triggers(assessment)
            for workflow in triggered_workflows:
                await execute_workflow(workflow, assessment)
        except Exception as wf_err:  # workflow errors must not poison the assessment
            logging.getLogger(__name__).error(
                "workflow trigger failed for %s: %s", assessment.id, wf_err
            )
    except Exception as e:
        logging.getLogger(__name__).exception(
            "assessment %s orchestration failed", assessment_id
        )
        await db.assessments.update_one(
            {"id": assessment_id},
            {"$set": {
                "status": AssessmentStatus.FAILED.value,
                "summary": {"error": str(e)[:500]},
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }},
        )


@api_router.get("/assessments", response_model=List[Assessment])
async def list_assessments(current_user: User = Depends(get_current_user)):
    """List assessments"""
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
    """Get assessment by ID"""
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
    """Manually trigger workflows for an assessment"""
    assessment_doc = await db.assessments.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment_doc:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    if isinstance(assessment_doc.get('created_at'), str):
        assessment_doc['created_at'] = datetime.fromisoformat(assessment_doc['created_at'])
    if assessment_doc.get('completed_at') and isinstance(assessment_doc['completed_at'], str):
        assessment_doc['completed_at'] = datetime.fromisoformat(assessment_doc['completed_at'])
    
    assessment = Assessment(**assessment_doc)
    
    triggered = await evaluate_workflow_triggers(assessment)
    runs = []
    for workflow in triggered:
        run = await execute_workflow(workflow, assessment)
        runs.append(run.model_dump())
    
    return {"triggered_count": len(runs), "runs": runs}


# ============ WORKFLOW ROUTES ============

async def evaluate_workflow_triggers(assessment: Assessment) -> List[Workflow]:
    """Evaluate which workflows should be triggered"""
    workflows_cursor = db.workflows.find({"active": True}, {"_id": 0})
    workflows = await workflows_cursor.to_list(1000)
    
    triggered = []
    for wf_dict in workflows:
        if isinstance(wf_dict.get('created_at'), str):
            wf_dict['created_at'] = datetime.fromisoformat(wf_dict['created_at'])
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


async def execute_workflow(workflow: Workflow, assessment: Assessment) -> WorkflowRun:
    """Execute a workflow"""
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


@api_router.post("/workflows", response_model=Workflow)
async def create_workflow(
    workflow: Workflow,
    current_user: User = Depends(get_current_user)
):
    """Create a new workflow (LOD2/Admin only)"""
    if current_user.role not in [UserRole.LOD2_USER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only LOD2 users can create workflows")
    
    workflow.created_by = current_user.id
    doc = workflow.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.workflows.insert_one(doc)
    
    return workflow


@api_router.get("/workflows", response_model=List[Workflow])
async def list_workflows(current_user: User = Depends(get_current_user)):
    """List all workflows"""
    workflows = await db.workflows.find({}, {"_id": 0}).to_list(1000)
    for wf in workflows:
        if isinstance(wf.get('created_at'), str):
            wf['created_at'] = datetime.fromisoformat(wf['created_at'])
    return workflows


# ============ ANALYTICS ROUTES ============

@api_router.get("/analytics/summary")
async def analytics_summary(current_user: User = Depends(get_current_user)):
    """Get analytics summary"""
    total_assessments = await db.assessments.count_documents({})
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
    """Get analytics trends"""
    return {
        "quarters": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"],
        "risk_scores": [65, 68, 72, 75],
        "compliance_scores": [70, 73, 75, 78],
        "assessments_count": [12, 15, 18, 21]
    }


# ============ ISSUE MANAGEMENT ROUTES ============

@api_router.post("/issues", response_model=Issue)
async def create_issue(
    issue_data: IssueCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new issue"""
    issue = Issue(**issue_data.model_dump(), created_by=current_user.id)
    
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
    """List issues"""
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
    """Get issue by ID"""
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
    """Update an issue"""
    issue_doc = await db.issues.find_one({"id": issue_id}, {"_id": 0})
    if not issue_doc:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    for key, value in updates.items():
        if key in issue_doc and key not in ['id', 'issue_number', 'created_by', 'created_at']:
            issue_doc[key] = value
    
    for date_field in ['created_at', 'due_date', 'closed_at']:
        if issue_doc.get(date_field) and isinstance(issue_doc[date_field], datetime):
            issue_doc[date_field] = issue_doc[date_field].isoformat()
    
    await db.issues.replace_one({"id": issue_id}, issue_doc)
    
    for date_field in ['created_at', 'due_date', 'closed_at']:
        if issue_doc.get(date_field) and isinstance(issue_doc[date_field], str):
            issue_doc[date_field] = datetime.fromisoformat(issue_doc[date_field])
    
    return Issue(**issue_doc)


# ============ REMEDIATION PLAN ROUTES ============

@api_router.post("/remediation-plans", response_model=RemediationPlan)
async def create_remediation_plan(
    plan_data: RemediationPlanCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a remediation plan"""
    plan = RemediationPlan(**plan_data.model_dump(), created_by=current_user.id)
    
    doc = plan.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('approved_at'):
        doc['approved_at'] = doc['approved_at'].isoformat()
    if doc.get('target_completion'):
        doc['target_completion'] = doc['target_completion'].isoformat()
    if doc.get('actual_completion'):
        doc['actual_completion'] = doc['actual_completion'].isoformat()
    
    for step in doc.get('steps', []):
        if step.get('target_date') and isinstance(step['target_date'], datetime):
            step['target_date'] = step['target_date'].isoformat()
        if step.get('completion_date') and isinstance(step['completion_date'], datetime):
            step['completion_date'] = step['completion_date'].isoformat()
    
    await db.remediation_plans.insert_one(doc)
    
    await db.issues.update_one(
        {"id": plan.issue_id},
        {"$set": {"remediation_plan_id": plan.id}}
    )
    
    return plan


@api_router.get("/remediation-plans", response_model=List[RemediationPlan])
async def list_remediation_plans(current_user: User = Depends(get_current_user)):
    """List remediation plans"""
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
        
        for step in plan.get('steps', []):
            if step.get('target_date') and isinstance(step['target_date'], str):
                step['target_date'] = datetime.fromisoformat(step['target_date'])
            if step.get('completion_date') and isinstance(step['completion_date'], str):
                step['completion_date'] = datetime.fromisoformat(step['completion_date'])
    
    return plans


# ============ RISK ACCEPTANCE ROUTES ============

@api_router.post("/risk-acceptance", response_model=RiskAcceptance)
async def create_risk_acceptance(
    acceptance_data: RiskAcceptanceCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a risk acceptance request"""
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
    """List risk acceptances"""
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
    """Approve a risk acceptance (LOD2/Admin only)"""
    if current_user.role not in [UserRole.LOD2_USER, UserRole.ADMIN]:
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


# ============ AGENT ACTIVITY & OBSERVABILITY ROUTES ============

@api_router.get("/agent-activities/{session_id}")
async def get_agent_activities(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get agent activities for a session"""
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
    """Get model metrics for a session"""
    metrics = await db.model_metrics.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    for metric in metrics:
        if isinstance(metric.get('timestamp'), str):
            metric['timestamp'] = datetime.fromisoformat(metric['timestamp'])
    
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
    """Get AI explanations for a session"""
    explanations = await db.explanations.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    
    for exp in explanations:
        if isinstance(exp.get('created_at'), str):
            exp['created_at'] = datetime.fromisoformat(exp['created_at'])
    
    return explanations


# ============ KNOWLEDGE GRAPH ROUTES ============

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
    
    entity_ids = [e['id'] for e in entities]
    
    relations = await db.knowledge_relations.find(
        {
            "$or": [
                {"source_entity_id": {"$in": entity_ids}},
                {"target_entity_id": {"$in": entity_ids}}
            ]
        },
        {"_id": 0}
    ).to_list(1000)
    
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
            "entity_count": len(entities),
            "relation_count": len(relations),
            "entity_types": list(set(e.get('entity_type') for e in entities if e.get('entity_type')))
        }
    }


@api_router.get("/knowledge-graph/query")
async def query_knowledge_graph(
    entity_name: str,
    depth: int = 2,
    current_user: User = Depends(get_current_user)
):
    """Query knowledge graph by entity name"""
    entity = await db.knowledge_entities.find_one(
        {"name": {"$regex": entity_name, "$options": "i"}},
        {"_id": 0}
    )
    
    if not entity:
        return {"root_entity": None, "related_entities": [], "relations": []}
    
    relations = await db.knowledge_relations.find(
        {
            "$or": [
                {"source_entity_id": entity['id']},
                {"target_entity_id": entity['id']}
            ]
        },
        {"_id": 0}
    ).to_list(1000)
    
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


# ============ OBSERVABILITY DASHBOARD ============

@api_router.get("/observability/dashboard")
async def get_observability_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get observability dashboard data"""
    recent_metrics = await db.model_metrics.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(100).to_list(100)
    
    total_requests = len(recent_metrics)
    total_tokens = sum(m.get('total_tokens', 0) for m in recent_metrics)
    total_cost = sum(m.get('cost_usd', 0) for m in recent_metrics)
    avg_latency = sum(m.get('latency_ms', 0) for m in recent_metrics) / total_requests if total_requests > 0 else 0
    success_rate = sum(1 for m in recent_metrics if m.get('success', True)) / total_requests if total_requests > 0 else 1.0
    
    recent_activities = await db.agent_activities.find(
        {},
        {"_id": 0}
    ).sort("started_at", -1).limit(50).to_list(50)
    
    completed_activities = sum(1 for a in recent_activities if a.get('status') == 'COMPLETED')
    failed_activities = sum(1 for a in recent_activities if a.get('status') == 'FAILED')
    
    entity_count = await db.knowledge_entities.count_documents({})
    relation_count = await db.knowledge_relations.count_documents({})
    
    # Get current LLM config
    llm_config = LLMClientFactory.get_current_config()
    
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
        "llm_config": {
            "provider": llm_config.provider.value,
            "model_name": llm_config.model_name
        },
        "recent_metrics": recent_metrics[:10],
        "recent_activities": recent_activities[:10]
    }


# ============ GDPR COMPLIANCE ============

@api_router.post("/gdpr/reset-history")
async def reset_history(
    current_user: User = Depends(get_current_user)
):
    """Reset user history for GDPR compliance (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can reset history")
    
    # Anonymize agent activities
    await db.agent_activities.update_many(
        {},
        {"$set": {"inputs": {}, "outputs": {}, "metadata": {}}}
    )
    
    # Anonymize explanations
    await db.explanations.update_many(
        {},
        {"$set": {"supporting_facts": [], "alternative_considerations": []}}
    )
    
    return {"message": "History anonymized for GDPR compliance"}


# ============ CUSTOM CONTROL LIBRARY ROUTES ============

@api_router.post("/controls/library", response_model=CustomControl)
async def create_custom_control(
    control_data: CustomControlCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a custom control (LOD1 creates, LOD2 approves)"""
    control = CustomControl(**control_data.model_dump(), created_by=current_user.id)
    
    # LOD2/Admin controls are auto-approved
    if current_user.role in [UserRole.LOD2_USER, UserRole.ADMIN]:
        control.status = ControlStatus.APPROVED
        control.approved_by = current_user.id
        control.approved_at = datetime.now(timezone.utc)
    
    doc = control.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('approved_at'):
        doc['approved_at'] = doc['approved_at'].isoformat()
    
    await db.custom_controls.insert_one(doc)
    return control


@api_router.get("/controls/library", response_model=List[CustomControl])
async def list_custom_controls(
    framework: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    is_ai_control: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """List custom controls from library"""
    query = {}
    if framework:
        query["frameworks"] = framework
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    if is_ai_control is not None:
        query["is_ai_control"] = is_ai_control
    
    controls = await db.custom_controls.find(query, {"_id": 0}).to_list(1000)
    
    for ctrl in controls:
        if isinstance(ctrl.get('created_at'), str):
            ctrl['created_at'] = datetime.fromisoformat(ctrl['created_at'])
        if ctrl.get('approved_at') and isinstance(ctrl['approved_at'], str):
            ctrl['approved_at'] = datetime.fromisoformat(ctrl['approved_at'])
        if ctrl.get('last_tested') and isinstance(ctrl['last_tested'], str):
            ctrl['last_tested'] = datetime.fromisoformat(ctrl['last_tested'])
        if ctrl.get('next_test_due') and isinstance(ctrl['next_test_due'], str):
            ctrl['next_test_due'] = datetime.fromisoformat(ctrl['next_test_due'])
    
    return controls


@api_router.get("/controls/library/quality")
async def get_library_quality(current_user: User = Depends(get_current_user)):
    """Quality metrics over the Controls Library collection (custom_controls)."""
    controls = await db.custom_controls.find({}, {"_id": 0}).to_list(10000)
    total = len(controls)

    missing_testing_procedure = sum(1 for c in controls if not (c.get("testing_procedure") or "").strip())
    missing_evidence = sum(1 for c in controls if not c.get("evidence_requirements"))
    missing_implementation = sum(1 for c in controls if not (c.get("implementation_guidance") or "").strip())
    missing_regulatory = sum(1 for c in controls if not c.get("regulatory_references"))

    pending_review = sum(1 for c in controls if (c.get("status") or "").upper() == "PENDING_REVIEW")
    approved = sum(1 for c in controls if (c.get("status") or "").upper() == "APPROVED")
    ai_controls = sum(1 for c in controls if c.get("is_ai_control"))

    framework_dist: Dict[str, int] = {}
    for c in controls:
        for fw in (c.get("frameworks") or []):
            framework_dist[fw] = framework_dist.get(fw, 0) + 1

    category_dist: Dict[str, int] = {}
    for c in controls:
        cat = c.get("category") or "UNCATEGORIZED"
        category_dist[cat] = category_dist.get(cat, 0) + 1

    completeness = 0.0
    if total:
        weak = missing_testing_procedure + missing_evidence + missing_implementation + missing_regulatory
        completeness = max(0.0, 100.0 - (weak / (total * 4)) * 100.0)

    return {
        "total": total,
        "approved": approved,
        "pending_review": pending_review,
        "ai_controls": ai_controls,
        "missing_testing_procedure": missing_testing_procedure,
        "missing_evidence_requirements": missing_evidence,
        "missing_implementation_guidance": missing_implementation,
        "missing_regulatory_references": missing_regulatory,
        "completeness_score": round(completeness, 2),
        "framework_distribution": framework_dist,
        "category_distribution": category_dist,
    }


@api_router.get("/controls/library/{control_id}", response_model=CustomControl)
async def get_custom_control(
    control_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get custom control by ID"""
    ctrl = await db.custom_controls.find_one({"id": control_id}, {"_id": 0})
    if not ctrl:
        raise HTTPException(status_code=404, detail="Control not found")
    
    if isinstance(ctrl.get('created_at'), str):
        ctrl['created_at'] = datetime.fromisoformat(ctrl['created_at'])
    if ctrl.get('approved_at') and isinstance(ctrl['approved_at'], str):
        ctrl['approved_at'] = datetime.fromisoformat(ctrl['approved_at'])
    
    return CustomControl(**ctrl)


@api_router.put("/controls/library/{control_id}", response_model=CustomControl)
async def update_custom_control(
    control_id: str,
    updates: CustomControlUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a custom control"""
    ctrl = await db.custom_controls.find_one({"id": control_id}, {"_id": 0})
    if not ctrl:
        raise HTTPException(status_code=404, detail="Control not found")
    
    update_data = updates.model_dump(exclude_unset=True)
    changed: Dict[str, Any] = {}
    for key, value in update_data.items():
        if value is not None:
            new_value = value if not isinstance(value, Enum) else value.value
            if ctrl.get(key) != new_value:
                changed[key] = {"from": ctrl.get(key), "to": new_value}
            ctrl[key] = new_value
    
    await db.custom_controls.replace_one({"id": control_id}, ctrl)

    if changed:
        from routes.audit import record_audit
        await record_audit(
            "custom_control", control_id, "update",
            current_user.email, current_user.role,
            {"changed_fields": list(changed.keys()), "changes": changed},
        )
    
    if isinstance(ctrl.get('created_at'), str):
        ctrl['created_at'] = datetime.fromisoformat(ctrl['created_at'])
    if ctrl.get('approved_at') and isinstance(ctrl['approved_at'], str):
        ctrl['approved_at'] = datetime.fromisoformat(ctrl['approved_at'])
    
    return CustomControl(**ctrl)


@api_router.post("/controls/library/{control_id}/approve")
async def approve_custom_control(
    control_id: str,
    current_user: User = Depends(get_current_user)
):
    """Approve a custom control (LOD2/Admin only)"""
    if current_user.role not in [UserRole.LOD2_USER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only LOD2 users can approve controls")
    
    await db.custom_controls.update_one(
        {"id": control_id},
        {
            "$set": {
                "status": ControlStatus.APPROVED.value,
                "approved_by": current_user.id,
                "approved_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )

    from routes.audit import record_audit
    await record_audit(
        "custom_control", control_id, "approve",
        current_user.email, current_user.role,
    )
    
    return {"message": "Control approved successfully"}


@api_router.post("/controls/library/{control_id}/reject")
async def reject_custom_control(
    control_id: str,
    reason: str,
    current_user: User = Depends(get_current_user)
):
    """Reject a custom control (LOD2/Admin only)"""
    if current_user.role not in [UserRole.LOD2_USER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only LOD2 users can reject controls")
    
    await db.custom_controls.update_one(
        {"id": control_id},
        {
            "$set": {
                "status": ControlStatus.REJECTED.value,
                "approved_by": current_user.id,
                "approved_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )

    from routes.audit import record_audit
    await record_audit(
        "custom_control", control_id, "reject",
        current_user.email, current_user.role,
        {"reason": reason},
    )
    
    return {"message": "Control rejected", "reason": reason}


# ---- Bulk approve / reject for Controls Library -------------------------
class BulkControlReviewRequest(BaseModel):
    control_ids: List[str]
    reason: Optional[str] = None


@api_router.post("/controls/library/bulk/approve")
async def bulk_approve_custom_controls(
    request: BulkControlReviewRequest,
    current_user: User = Depends(get_current_user),
):
    """Bulk approve multiple controls in one action (LOD2 / Admin)."""
    if current_user.role not in [UserRole.LOD2_USER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only LOD2 users can approve controls")
    if not request.control_ids:
        return {"approved": 0, "control_ids": []}

    now_iso = datetime.now(timezone.utc).isoformat()
    res = await db.custom_controls.update_many(
        {"id": {"$in": request.control_ids}},
        {"$set": {
            "status": ControlStatus.APPROVED.value,
            "approved_by": current_user.id,
            "approved_at": now_iso,
        }},
    )
    from routes.audit import record_audit
    for cid in request.control_ids:
        await record_audit(
            "custom_control", cid, "bulk_approve",
            current_user.email, current_user.role,
            {"batch_size": len(request.control_ids)},
        )
    return {"approved": res.modified_count, "control_ids": request.control_ids}


@api_router.post("/controls/library/bulk/reject")
async def bulk_reject_custom_controls(
    request: BulkControlReviewRequest,
    current_user: User = Depends(get_current_user),
):
    """Bulk reject multiple controls in one action (LOD2 / Admin)."""
    if current_user.role not in [UserRole.LOD2_USER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only LOD2 users can reject controls")
    if not request.control_ids:
        return {"rejected": 0, "control_ids": []}

    now_iso = datetime.now(timezone.utc).isoformat()
    res = await db.custom_controls.update_many(
        {"id": {"$in": request.control_ids}},
        {"$set": {
            "status": ControlStatus.REJECTED.value,
            "approved_by": current_user.id,
            "approved_at": now_iso,
        }},
    )
    from routes.audit import record_audit
    for cid in request.control_ids:
        await record_audit(
            "custom_control", cid, "bulk_reject",
            current_user.email, current_user.role,
            {"reason": request.reason or "", "batch_size": len(request.control_ids)},
        )
    return {"rejected": res.modified_count, "control_ids": request.control_ids}


# ============ CONTROL TESTING ROUTES ============

@api_router.post("/control-tests", response_model=ControlTest)
async def create_control_test(
    test_data: ControlTestCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new control test (LOD1 tests)"""
    # Get control details
    ctrl = await db.custom_controls.find_one({"id": test_data.control_id}, {"_id": 0})
    if not ctrl:
        raise HTTPException(status_code=404, detail="Control not found")
    
    test = ControlTest(
        **test_data.model_dump(),
        control_name=ctrl['name'],
        tester=current_user.id,
        tester_role=current_user.role.value,
        status=ControlTestStatus.IN_PROGRESS
    )
    
    doc = test.model_dump()
    doc['test_date'] = doc['test_date'].isoformat()
    
    await db.control_tests.insert_one(doc)
    return test


@api_router.get("/control-tests", response_model=List[ControlTest])
async def list_control_tests(
    control_id: Optional[str] = None,
    status: Optional[str] = None,
    pending_review: bool = False,
    current_user: User = Depends(get_current_user)
):
    """List control tests"""
    query = {}
    
    if control_id:
        query["control_id"] = control_id
    if status:
        query["status"] = status
    if pending_review:
        query["status"] = ControlTestStatus.PENDING_REVIEW.value
    
    # LOD1 sees their own tests, LOD2 sees all
    if current_user.role == UserRole.LOD1_USER:
        query["tester"] = current_user.id
    
    tests = await db.control_tests.find(query, {"_id": 0}).to_list(1000)
    
    for test in tests:
        if isinstance(test.get('test_date'), str):
            test['test_date'] = datetime.fromisoformat(test['test_date'])
        if test.get('review_date') and isinstance(test['review_date'], str):
            test['review_date'] = datetime.fromisoformat(test['review_date'])
    
    return tests


@api_router.put("/control-tests/{test_id}", response_model=ControlTest)
async def update_control_test(
    test_id: str,
    updates: ControlTestUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a control test (LOD1 submits results)"""
    test_doc = await db.control_tests.find_one({"id": test_id}, {"_id": 0})
    if not test_doc:
        raise HTTPException(status_code=404, detail="Test not found")
    
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            test_doc[key] = value if not isinstance(value, Enum) else value.value
    
    await db.control_tests.replace_one({"id": test_id}, test_doc)
    
    if isinstance(test_doc.get('test_date'), str):
        test_doc['test_date'] = datetime.fromisoformat(test_doc['test_date'])
    
    return ControlTest(**test_doc)


@api_router.post("/control-tests/{test_id}/submit")
async def submit_control_test(
    test_id: str,
    current_user: User = Depends(get_current_user)
):
    """Submit a control test for LOD2 review"""
    await db.control_tests.update_one(
        {"id": test_id},
        {"$set": {"status": ControlTestStatus.PENDING_REVIEW.value}}
    )
    
    return {"message": "Test submitted for review"}


@api_router.post("/control-tests/{test_id}/review")
async def review_control_test(
    test_id: str,
    review: ControlTestReview,
    current_user: User = Depends(get_current_user)
):
    """Review a control test (LOD2/Admin only)"""
    if current_user.role not in [UserRole.LOD2_USER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only LOD2 users can review tests")
    
    new_status = ControlTestStatus.APPROVED.value if review.review_status == "APPROVED" else ControlTestStatus.FAILED.value
    
    await db.control_tests.update_one(
        {"id": test_id},
        {
            "$set": {
                "status": new_status,
                "reviewer": current_user.id,
                "reviewer_role": current_user.role.value,
                "review_date": datetime.now(timezone.utc).isoformat(),
                "review_comments": review.review_comments,
                "review_status": review.review_status
            }
        }
    )
    
    # Update control's last_tested date if approved
    if review.review_status == "APPROVED":
        test_doc = await db.control_tests.find_one({"id": test_id}, {"_id": 0})
        if test_doc:
            await db.custom_controls.update_one(
                {"id": test_doc['control_id']},
                {
                    "$set": {
                        "last_tested": datetime.now(timezone.utc).isoformat(),
                        "effectiveness": test_doc.get('effectiveness_rating', 'NOT_TESTED')
                    }
                }
            )
    
    return {"message": f"Test review completed: {review.review_status}"}


# ============ GAP ANALYSIS ROUTES ============

@api_router.post("/gap-analysis/run")
async def run_gap_analysis(
    assessment_id: str,
    framework: str,
    current_user: User = Depends(get_current_user)
):
    """Run gap analysis for an assessment against a framework"""
    # Get assessment
    assessment_doc = await db.assessments.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment_doc:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Get all approved controls
    controls = await db.custom_controls.find(
        {"status": ControlStatus.APPROVED.value, "frameworks": framework},
        {"_id": 0}
    ).to_list(1000)
    
    # Framework requirements (expanded)
    framework_requirements = get_framework_requirements(framework)
    
    # Identify gaps
    gaps = []
    control_names = [c['name'].lower() for c in controls]
    
    for req in framework_requirements:
        # Check if any control addresses this requirement
        covered = any(
            req['keyword'].lower() in cn for cn in control_names
        ) or any(
            req['id'] in c.get('regulatory_references', []) for c in controls
        )
        
        if not covered:
            gap = ControlGap(
                framework=framework,
                requirement=req['description'],
                requirement_id=req['id'],
                gap_description=f"No control mapped to requirement: {req['description']}",
                risk_if_unaddressed=req.get('risk', 'Potential compliance violation'),
                severity=RiskSeverity(req.get('severity', 'MEDIUM')),
                current_state="No control implemented",
                target_state=f"Implement control for {req['description']}",
                recommended_controls=req.get('recommended_controls', []),
                estimated_effort=req.get('effort', 'Medium'),
                business_unit=assessment_doc.get('business_unit', 'Unknown'),
                identified_by=current_user.id
            )
            
            doc = gap.model_dump()
            doc['identified_at'] = doc['identified_at'].isoformat()
            await db.control_gaps.insert_one(doc)
            gaps.append(gap)
    
    return {
        "assessment_id": assessment_id,
        "framework": framework,
        "total_requirements": len(framework_requirements),
        "gaps_identified": len(gaps),
        "coverage_percentage": round((len(framework_requirements) - len(gaps)) / len(framework_requirements) * 100, 2),
        "gaps": [g.model_dump() for g in gaps]
    }


@api_router.get("/gap-analysis")
async def list_control_gaps(
    framework: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List control gaps"""
    query = {}
    if framework:
        query["framework"] = framework
    if status:
        query["status"] = status
    
    gaps = await db.control_gaps.find(query, {"_id": 0}).to_list(1000)
    
    for gap in gaps:
        if isinstance(gap.get('identified_at'), str):
            gap['identified_at'] = datetime.fromisoformat(gap['identified_at'])
        if gap.get('target_date') and isinstance(gap['target_date'], str):
            gap['target_date'] = datetime.fromisoformat(gap['target_date'])
        if gap.get('closed_at') and isinstance(gap['closed_at'], str):
            gap['closed_at'] = datetime.fromisoformat(gap['closed_at'])
    
    return gaps


# ============ AI SYSTEM ROUTES ============

@api_router.post("/ai-systems", response_model=AISystem)
async def register_ai_system(
    system_data: AISystemCreate,
    current_user: User = Depends(get_current_user)
):
    """Register an AI system for compliance tracking"""
    ai_system = AISystem(**system_data.model_dump(), created_by=current_user.id)
    
    # Set next assessment due based on risk category
    days_map = {"UNACCEPTABLE": 0, "HIGH": 30, "LIMITED": 90, "MINIMAL": 365}
    ai_system.next_assessment_due = datetime.now(timezone.utc) + timedelta(
        days=days_map.get(system_data.risk_category.value, 90)
    )
    
    doc = ai_system.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('next_assessment_due'):
        doc['next_assessment_due'] = doc['next_assessment_due'].isoformat()
    
    await db.ai_systems.insert_one(doc)
    return ai_system


@api_router.get("/ai-systems", response_model=List[AISystem])
async def list_ai_systems(
    risk_category: Optional[str] = None,
    deployment_status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List registered AI systems"""
    query = {}
    if risk_category:
        query["risk_category"] = risk_category
    if deployment_status:
        query["deployment_status"] = deployment_status
    
    systems = await db.ai_systems.find(query, {"_id": 0}).to_list(1000)
    
    for sys in systems:
        if isinstance(sys.get('created_at'), str):
            sys['created_at'] = datetime.fromisoformat(sys['created_at'])
        if sys.get('last_assessment_date') and isinstance(sys['last_assessment_date'], str):
            sys['last_assessment_date'] = datetime.fromisoformat(sys['last_assessment_date'])
        if sys.get('next_assessment_due') and isinstance(sys['next_assessment_due'], str):
            sys['next_assessment_due'] = datetime.fromisoformat(sys['next_assessment_due'])
    
    return systems


@api_router.get("/ai-systems/{system_id}", response_model=AISystem)
async def get_ai_system(
    system_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get AI system details"""
    sys = await db.ai_systems.find_one({"id": system_id}, {"_id": 0})
    if not sys:
        raise HTTPException(status_code=404, detail="AI System not found")
    
    if isinstance(sys.get('created_at'), str):
        sys['created_at'] = datetime.fromisoformat(sys['created_at'])
    if sys.get('next_assessment_due') and isinstance(sys['next_assessment_due'], str):
        sys['next_assessment_due'] = datetime.fromisoformat(sys['next_assessment_due'])
    
    return AISystem(**sys)


# ============ AI CONTROL ASSESSMENT ROUTES ============

@api_router.post("/ai-assessments", response_model=AIControlAssessment)
async def create_ai_control_assessment(
    assessment_data: AIControlAssessmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Create an AI control assessment and run LLM evaluation in background"""
    ai_sys = await db.ai_systems.find_one({"id": assessment_data.ai_system_id}, {"_id": 0})
    if not ai_sys:
        raise HTTPException(status_code=404, detail="AI System not found")

    controls = await get_ai_framework_controls(assessment_data.framework, ai_sys.get('risk_category', 'HIGH'))

    control_results = []
    required_actions = []

    for ctrl in controls:
        result = {
            "control_id": ctrl['id'],
            "control_name": ctrl['name'],
            "category": ctrl['category'],
            "requirement": ctrl['requirement'],
            "status": "NOT_ASSESSED",
            "evidence_required": ctrl.get('evidence_required', []),
            "guidance": ctrl.get('guidance', '')
        }
        control_results.append(result)
        if ctrl.get('mandatory', False):
            required_actions.append(f"Assess mandatory control: {ctrl['name']}")

    assessment = AIControlAssessment(
        **assessment_data.model_dump(),
        ai_system_name=ai_sys['name'],
        assessor=current_user.id,
        control_results=control_results,
        findings=[],
        recommendations=[],
        required_actions=required_actions
    )

    doc = assessment.model_dump()
    doc['assessment_date'] = doc['assessment_date'].isoformat()
    await db.ai_control_assessments.insert_one(doc)

    # Run LLM evaluation in background
    background_tasks.add_task(_run_ai_assessment_async, assessment.id)

    return assessment

async def _run_ai_assessment_async(assessment_id: str):
    """Background worker: uses LLM to evaluate each AI control and complete the assessment."""
    try:
        doc = await db.ai_control_assessments.find_one({"id": assessment_id}, {"_id": 0})
        if not doc:
            logger.warning("AI assessment %s not found for background run", assessment_id)
            return

        ai_sys = await db.ai_systems.find_one({"id": doc["ai_system_id"]}, {"_id": 0})
        system_context = {
            "name": ai_sys.get("name", "Unknown"),
            "description": ai_sys.get("description", ""),
            "purpose": ai_sys.get("purpose", ""),
            "ai_type": ai_sys.get("ai_type", ""),
            "deployment_status": ai_sys.get("deployment_status", ""),
            "risk_category": ai_sys.get("risk_category", "HIGH"),
            "decision_impact": ai_sys.get("decision_impact", ""),
            "human_oversight_level": ai_sys.get("human_oversight_level", ""),
            "data_types": ai_sys.get("data_types_processed", []),
        } if ai_sys else {}

        # Try LLMClientFactory (admin panel config) first, fall back to llm_evaluator (env var)
        try:
            llm_client = LLMClientFactory.get_client()
            async def _llm_generate(prompt: str) -> str:
                result = await llm_client.generate(prompt)
                return result.get("response", "{}")
        except Exception:
            from services.llm_evaluator import _call_gemini
            async def _llm_generate(prompt: str) -> str:
                return await _call_gemini("You are an AI compliance expert. Respond with JSON only.", prompt)

        control_results = []
        findings = []
        recommendations = []

        for ctrl in doc.get("control_results", []):
            prompt = f"""You are an AI compliance expert assessing an AI system against {doc['framework']}.

AI System Context:
{system_context}

Evaluate this control:
- Control: {ctrl['control_name']}
- Category: {ctrl['category']}
- Requirement: {ctrl['requirement']}
- Guidance: {ctrl.get('guidance', '')}
- Evidence Required: {', '.join(ctrl.get('evidence_required', []))}

Based on the AI system context, assess this control and respond in this exact JSON format:
{{
  "status": "COMPLIANT" | "PARTIALLY_COMPLIANT" | "NON_COMPLIANT",
  "confidence": 0.0-1.0,
  "finding": "one sentence finding about this control",
  "recommendation": "one sentence recommendation if not fully compliant, else null",
  "evidence_gaps": ["list of missing evidence items"]
}}

Respond with JSON only, no other text."""

            try:
                raw = await _llm_generate(prompt)
                # Strip markdown code fences if present
                raw = raw.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                import json
                parsed = json.loads(raw.strip())

                ctrl["status"] = parsed.get("status", "NOT_ASSESSED")
                ctrl["confidence"] = parsed.get("confidence", 0.5)
                ctrl["findings"] = parsed.get("finding", "")
                ctrl["evidence_gaps"] = parsed.get("evidence_gaps", [])

                if parsed.get("finding"):
                    findings.append(f"{ctrl['control_name']}: {parsed['finding']}")
                if parsed.get("recommendation"):
                    recommendations.append(parsed["recommendation"])

            except Exception as ctrl_err:
                logger.warning("LLM eval failed for control %s: %s", ctrl['control_id'], ctrl_err)
                ctrl["status"] = "NOT_ASSESSED"

            control_results.append(ctrl)

        # Calculate compliance score
        total = len(control_results)
        compliant = sum(1 for c in control_results if c.get("status") == "COMPLIANT")
        partial = sum(1 for c in control_results if c.get("status") == "PARTIALLY_COMPLIANT")
        compliance_pct = (compliant + partial * 0.5) / total * 100 if total > 0 else 0

        if compliance_pct >= 90:
            overall = "COMPLIANT"
        elif compliance_pct >= 70:
            overall = "PARTIALLY_COMPLIANT"
        else:
            overall = "NON_COMPLIANT"

        await db.ai_control_assessments.update_one(
            {"id": assessment_id},
            {"$set": {
                "status": "COMPLETED",
                "control_results": control_results,
                "findings": findings,
                "recommendations": recommendations,
                "overall_compliance": overall,
                "compliance_percentage": round(compliance_pct, 2),
            }}
        )

        # Update AI system last assessed date
        await db.ai_systems.update_one(
            {"id": doc["ai_system_id"]},
            {"$set": {"last_assessment_date": datetime.now(timezone.utc).isoformat()}}
        )

        logger.info("AI assessment %s completed — %s (%.1f%%)", assessment_id, overall, compliance_pct)

    except Exception as e:
        logger.exception("AI assessment %s failed", assessment_id)
        await db.ai_control_assessments.update_one(
            {"id": assessment_id},
            {"$set": {"status": "FAILED"}}
        )
@api_router.get("/ai-assessments", response_model=List[AIControlAssessment])
async def list_ai_control_assessments(
    ai_system_id: Optional[str] = None,
    framework: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List AI control assessments"""
    query = {}
    if ai_system_id:
        query["ai_system_id"] = ai_system_id
    if framework:
        query["framework"] = framework
    
    assessments = await db.ai_control_assessments.find(query, {"_id": 0}).to_list(1000)
    
    for assess in assessments:
        if isinstance(assess.get('assessment_date'), str):
            assess['assessment_date'] = datetime.fromisoformat(assess['assessment_date'])
        if assess.get('review_date') and isinstance(assess['review_date'], str):
            assess['review_date'] = datetime.fromisoformat(assess['review_date'])
    
    return assessments


@api_router.put("/ai-assessments/{assessment_id}/control/{control_id}")
async def update_ai_control_result(
    assessment_id: str,
    control_id: str,
    status: str,
    evidence: List[str] = [],
    findings: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update a specific control result in AI assessment"""
    assessment = await db.ai_control_assessments.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    for ctrl in assessment.get('control_results', []):
        if ctrl['control_id'] == control_id:
            ctrl['status'] = status
            ctrl['evidence_provided'] = evidence
            if findings:
                ctrl['findings'] = findings
            break
    
    await db.ai_control_assessments.update_one(
        {"id": assessment_id},
        {"$set": {"control_results": assessment['control_results']}}
    )
    return {"message": "Control result updated"}


@api_router.post("/ai-assessments/{assessment_id}/control/{control_id}/evidence")
async def upload_control_evidence(
    assessment_id: str,
    control_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload an evidence document for a specific control in an AI assessment."""
    assessment = await db.ai_control_assessments.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    content = await file.read()
    text = ""
    if file.filename.endswith(".pdf"):
        try:
            import pdfplumber, io
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception:
            text = content.decode("utf-8", errors="ignore")
    else:
        text = content.decode("utf-8", errors="ignore")

    # Find the control
    ctrl_doc = next((c for c in assessment.get("control_results", []) if c["control_id"] == control_id), None)
    if not ctrl_doc:
        raise HTTPException(status_code=404, detail="Control not found in assessment")

    # Use LLM to evaluate the evidence against the control requirement
    from services.llm_evaluator import _call_gemini
    prompt = f"""You are an AI compliance auditor. A document has been uploaded as evidence for a control.

Control: {ctrl_doc['control_name']}
Requirement: {ctrl_doc['requirement']}
Evidence required: {', '.join(ctrl_doc.get('evidence_required', []))}

Document content (first 3000 chars):
{text[:3000]}

Evaluate whether this document satisfies the control requirement. Respond in this exact JSON format:
{{
  "status": "COMPLIANT" | "PARTIALLY_COMPLIANT" | "NON_COMPLIANT",
  "confidence": 0.0-1.0,
  "finding": "one sentence assessment of whether this evidence satisfies the requirement",
  "satisfied_items": ["list of evidence_required items this document satisfies"],
  "remaining_gaps": ["list of evidence_required items still missing"]
}}
Respond with JSON only."""

    try:
        raw = await _call_gemini("You are an AI compliance auditor. Respond with JSON only.", prompt)
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        import json
        evaluated = json.loads(raw)
    except Exception:
        evaluated = {"status": "PARTIALLY_COMPLIANT", "confidence": 0.5, "finding": f"Document '{file.filename}' uploaded but could not be automatically evaluated.", "satisfied_items": [], "remaining_gaps": ctrl_doc.get("evidence_required", [])}

    # Store the evidence record and update control status
    evidence_record = {
        "filename": file.filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": current_user.id,
        "evaluation": evaluated
    }

    for ctrl in assessment["control_results"]:
        if ctrl["control_id"] == control_id:
            ctrl["status"] = evaluated.get("status", ctrl["status"])
            ctrl["findings"] = evaluated.get("finding", "")
            ctrl["evidence_gaps"] = evaluated.get("remaining_gaps", [])
            ctrl["confidence"] = evaluated.get("confidence", 0.5)
            if "evidence_documents" not in ctrl:
                ctrl["evidence_documents"] = []
            ctrl["evidence_documents"].append(evidence_record)
            break

    await db.ai_control_assessments.update_one(
        {"id": assessment_id},
        {"$set": {"control_results": assessment["control_results"]}}
    )

    return {"message": "Evidence evaluated", "evaluation": evaluated, "filename": file.filename}


@api_router.delete("/ai-assessments/{assessment_id}")
async def delete_ai_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an AI control assessment."""
    result = await db.ai_control_assessments.delete_one({"id": assessment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"deleted": True, "id": assessment_id}


@api_router.delete("/ai-systems/{system_id}")
async def delete_ai_system(
    system_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an AI system and all its assessments."""
    sys_result = await db.ai_systems.delete_one({"id": system_id})
    if sys_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="AI system not found")
    # Cascade delete assessments
    deleted = await db.ai_control_assessments.delete_many({"ai_system_id": system_id})
    return {"deleted": True, "id": system_id, "assessments_deleted": deleted.deleted_count}




@api_router.post("/ai-assessments/{assessment_id}/complete")
async def complete_ai_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Complete an AI control assessment and calculate compliance"""
    assessment = await db.ai_control_assessments.find_one({"id": assessment_id}, {"_id": 0})
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Calculate compliance
    total = len(assessment.get('control_results', []))
    compliant = sum(1 for c in assessment.get('control_results', []) if c.get('status') == 'COMPLIANT')
    partial = sum(1 for c in assessment.get('control_results', []) if c.get('status') == 'PARTIALLY_COMPLIANT')
    
    compliance_percentage = (compliant + partial * 0.5) / total * 100 if total > 0 else 0
    
    if compliance_percentage >= 90:
        overall = "COMPLIANT"
    elif compliance_percentage >= 70:
        overall = "PARTIALLY_COMPLIANT"
    else:
        overall = "NON_COMPLIANT"
    
    await db.ai_control_assessments.update_one(
        {"id": assessment_id},
        {
            "$set": {
                "status": "COMPLETED",
                "overall_compliance": overall
            }
        }
    )
    
    # Update AI system compliance status
    await db.ai_systems.update_one(
        {"id": assessment['ai_system_id']},
        {
            "$set": {
                "last_assessment_date": datetime.now(timezone.utc).isoformat(),
                f"{assessment['framework'].lower().replace(' ', '_').replace('-', '_')}_compliant": overall == "COMPLIANT"
            }
        }
    )
    
    return {
        "assessment_id": assessment_id,
        "overall_compliance": overall,
        "compliance_percentage": round(compliance_percentage, 2),
        "compliant_controls": compliant,
        "partial_controls": partial,
        "non_compliant_controls": total - compliant - partial
    }


@api_router.get("/ai-frameworks")
async def get_ai_frameworks(current_user: User = Depends(get_current_user)):
    """Get available AI compliance frameworks from MongoDB."""
    frameworks = await db.ai_frameworks.find({"active": True}, {"_id": 0}).to_list(100)
    return {"frameworks": frameworks}


@api_router.post("/ai-frameworks")
async def create_ai_framework(
    framework: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Create a new AI compliance framework (admin only)."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    if not framework.get("id") or not framework.get("name"):
        raise HTTPException(status_code=400, detail="id and name are required")
    existing = await db.ai_frameworks.find_one({"id": framework["id"]})
    if existing:
        raise HTTPException(status_code=409, detail=f"Framework {framework['id']} already exists")
    framework.setdefault("active", True)
    framework.setdefault("categories", [])
    framework.setdefault("color", "#475569")
    framework.setdefault("bg_color", "#f1f5f9")
    framework.setdefault("flag", "🌐")
    framework["created_by"] = current_user.id
    framework["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.ai_frameworks.insert_one(framework)
    framework.pop("_id", None)
    return framework


@api_router.put("/ai-frameworks/{framework_id}")
async def update_ai_framework(
    framework_id: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update an AI framework (admin only)."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    existing = await db.ai_frameworks.find_one({"id": framework_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Framework not found")
    updates.pop("id", None)
    updates.pop("_id", None)
    updates["updated_by"] = current_user.id
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.ai_frameworks.update_one({"id": framework_id}, {"$set": updates})
    updated = await db.ai_frameworks.find_one({"id": framework_id}, {"_id": 0})
    return updated


@api_router.delete("/ai-frameworks/{framework_id}")
async def delete_ai_framework(
    framework_id: str,
    current_user: User = Depends(get_current_user)
):
    """Deactivate (soft-delete) an AI framework. Controls are preserved."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.ai_frameworks.update_one(
        {"id": framework_id}, {"$set": {"active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Framework not found")
    ctrl_count = await db.ai_framework_controls.count_documents({"framework": framework_id})
    return {"deactivated": True, "id": framework_id, "controls_preserved": ctrl_count}



@api_router.get("/ai-framework-controls")
async def list_ai_framework_controls(
    framework: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List all AI framework controls. Optionally filter by framework or category."""
    query: Dict[str, Any] = {}
    if framework:
        query["framework"] = framework
    if category:
        query["category"] = category
    controls = await db.ai_framework_controls.find(query, {"_id": 0}).to_list(500)
    return controls


@api_router.get("/ai-framework-controls/{control_id}")
async def get_ai_framework_control(
    control_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a single AI framework control by id."""
    control = await db.ai_framework_controls.find_one({"id": control_id}, {"_id": 0})
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@api_router.post("/ai-framework-controls")
async def create_ai_framework_control(
    control: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Create a new AI framework control (admin only)."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    if not control.get("id") or not control.get("framework"):
        raise HTTPException(status_code=400, detail="id and framework are required")
    existing = await db.ai_framework_controls.find_one({"id": control["id"]})
    if existing:
        raise HTTPException(status_code=409, detail=f"Control {control['id']} already exists")
    control["created_by"] = current_user.id
    control["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.ai_framework_controls.insert_one(control)
    control.pop("_id", None)
    return control


@api_router.put("/ai-framework-controls/{control_id}")
async def update_ai_framework_control(
    control_id: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update an AI framework control (admin only)."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    existing = await db.ai_framework_controls.find_one({"id": control_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Control not found")
    updates.pop("id", None)
    updates.pop("_id", None)
    updates["updated_by"] = current_user.id
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.ai_framework_controls.update_one({"id": control_id}, {"$set": updates})
    updated = await db.ai_framework_controls.find_one({"id": control_id}, {"_id": 0})
    return updated


@api_router.delete("/ai-framework-controls/{control_id}")
async def delete_ai_framework_control(
    control_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an AI framework control (admin only)."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.ai_framework_controls.delete_one({"id": control_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Control not found")
    return {"deleted": True, "id": control_id}




# ============ HELPER FUNCTIONS ============

def get_framework_requirements(framework: str) -> List[Dict]:
    """Get requirements for a framework"""
    requirements = {
        "NIST CSF": [
            {"id": "PR.AC-1", "description": "Identity and credential management", "keyword": "identity", "severity": "HIGH", "recommended_controls": ["MFA", "IAM Policy"], "effort": "Medium"},
            {"id": "PR.AC-4", "description": "Least privilege access management", "keyword": "privilege", "severity": "HIGH", "recommended_controls": ["RBAC", "Access Review"], "effort": "Medium"},
            {"id": "PR.DS-1", "description": "Data-at-rest protection", "keyword": "encryption", "severity": "HIGH", "recommended_controls": ["Encryption at Rest"], "effort": "High"},
            {"id": "PR.DS-2", "description": "Data-in-transit protection", "keyword": "transit", "severity": "HIGH", "recommended_controls": ["TLS", "VPN"], "effort": "Medium"},
            {"id": "PR.IP-12", "description": "Vulnerability management", "keyword": "vulnerability", "severity": "MEDIUM", "recommended_controls": ["Vulnerability Scanning"], "effort": "Medium"},
            {"id": "DE.CM-8", "description": "Vulnerability scanning", "keyword": "scanning", "severity": "MEDIUM", "recommended_controls": ["Automated Scanning"], "effort": "Low"},
        ],
        "ISO 27001": [
            {"id": "A.9.2.1", "description": "User registration and de-registration", "keyword": "registration", "severity": "MEDIUM", "recommended_controls": ["User Lifecycle Management"], "effort": "Medium"},
            {"id": "A.10.1.1", "description": "Cryptographic controls policy", "keyword": "cryptographic", "severity": "HIGH", "recommended_controls": ["Encryption Policy"], "effort": "Low"},
            {"id": "A.12.6.1", "description": "Technical vulnerability management", "keyword": "vulnerability", "severity": "HIGH", "recommended_controls": ["Patch Management"], "effort": "Medium"},
        ],
        "EU_AI_ACT": [
            {"id": "ART-6", "description": "Risk classification system", "keyword": "classification", "severity": "CRITICAL", "recommended_controls": ["AI Risk Assessment"], "effort": "High"},
            {"id": "ART-9", "description": "Risk management system", "keyword": "risk management", "severity": "HIGH", "recommended_controls": ["AI Risk Monitoring"], "effort": "High"},
            {"id": "ART-10", "description": "Data governance", "keyword": "data governance", "severity": "HIGH", "recommended_controls": ["Data Quality Controls"], "effort": "High"},
            {"id": "ART-13", "description": "Transparency and information", "keyword": "transparency", "severity": "HIGH", "recommended_controls": ["AI Transparency Docs"], "effort": "Medium"},
            {"id": "ART-14", "description": "Human oversight", "keyword": "human oversight", "severity": "HIGH", "recommended_controls": ["Human-in-the-Loop"], "effort": "High"},
            {"id": "ART-15", "description": "Accuracy, robustness, cybersecurity", "keyword": "accuracy", "severity": "HIGH", "recommended_controls": ["Model Validation"], "effort": "High"},
        ],
        "NIST_AI_RMF": [
            {"id": "GOVERN-1", "description": "Policies and processes for AI risk management", "keyword": "governance", "severity": "HIGH", "recommended_controls": ["AI Governance Policy"], "effort": "Medium"},
            {"id": "MAP-1", "description": "Context for AI system is established", "keyword": "context", "severity": "MEDIUM", "recommended_controls": ["AI System Documentation"], "effort": "Medium"},
            {"id": "MAP-3", "description": "AI capabilities, targeted usage documented", "keyword": "capabilities", "severity": "MEDIUM", "recommended_controls": ["Capability Assessment"], "effort": "Low"},
            {"id": "MEASURE-1", "description": "AI risks and impacts are characterized", "keyword": "measure", "severity": "HIGH", "recommended_controls": ["Risk Assessment Process"], "effort": "High"},
            {"id": "MEASURE-2", "description": "AI systems evaluated for trustworthiness", "keyword": "trustworthy", "severity": "HIGH", "recommended_controls": ["Trustworthiness Evaluation"], "effort": "High"},
            {"id": "MANAGE-1", "description": "AI risks are prioritized and acted upon", "keyword": "prioritize", "severity": "HIGH", "recommended_controls": ["Risk Treatment Plan"], "effort": "Medium"},
            {"id": "MANAGE-4", "description": "AI risk treatment documented and monitored", "keyword": "treatment", "severity": "MEDIUM", "recommended_controls": ["Risk Register"], "effort": "Medium"},
        ]
    }
    return requirements.get(framework, [])


async def get_ai_framework_controls(framework: str, risk_category: str) -> List[Dict]:
    """
    Fetch AI framework controls from MongoDB (seeded from seeds/ai_framework_controls.py).
    Filters by framework and applies risk_category_filter so only relevant controls
    are included in the assessment. Falls back to empty list if collection is empty.
    """
    query: Dict[str, Any] = {"framework": framework}
    controls = await db.ai_framework_controls.find(query, {"_id": 0}).to_list(200)

    # Filter by risk category — controls tagged ["ALL"] always apply
    def applies(control: Dict) -> bool:
        cat_filter = control.get("risk_category_filter", ["ALL"])
        return "ALL" in cat_filter or risk_category in cat_filter

    return [c for c in controls if applies(c)]


# ============ AUTOMATED CONTROL TESTING ROUTES ============

@api_router.post("/automated-tests/config", response_model=AutomatedTestConfig)
async def create_automated_test_config(
    config_data: AutomatedTestConfigCreate,
    current_user: User = Depends(get_current_user)
):
    """Create automated test configuration for a control"""
    # Verify control exists
    ctrl = await db.custom_controls.find_one({"id": config_data.control_id}, {"_id": 0})
    if not ctrl:
        raise HTTPException(status_code=404, detail="Control not found")
    
    config = AutomatedTestConfig(
        **config_data.model_dump(),
        created_by=current_user.id
    )
    
    doc = config.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.automated_test_configs.insert_one(doc)
    return config


@api_router.get("/automated-tests/config")
async def list_automated_test_configs(
    control_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List automated test configurations"""
    query = {}
    if control_id:
        query["control_id"] = control_id
    
    configs = await db.automated_test_configs.find(query, {"_id": 0}).to_list(1000)
    
    for cfg in configs:
        if isinstance(cfg.get('created_at'), str):
            cfg['created_at'] = datetime.fromisoformat(cfg['created_at'])
    
    return configs


@api_router.post("/automated-tests/run/{control_id}")
async def run_automated_test(
    control_id: str,
    test_type: str = "CONFIGURATION_CHECK",
    current_user: User = Depends(get_current_user)
):
    """Run an automated test for a control"""
    # Get control
    ctrl = await db.custom_controls.find_one({"id": control_id}, {"_id": 0})
    if not ctrl:
        raise HTTPException(status_code=404, detail="Control not found")
    
    # Get test config if exists
    config = await db.automated_test_configs.find_one(
        {"control_id": control_id, "test_type": test_type},
        {"_id": 0}
    )
    
    # Create test run
    test_run = AutomatedTestRun(
        control_id=control_id,
        control_name=ctrl['name'],
        test_type=AutomatedTestType(test_type),
        triggered_by=current_user.id,
        trigger_reason="Manual",
        evidence_sources=config.get('evidence_sources', ['AWS_CONFIG', 'IAM_EXPORT']) if config else ['AWS_CONFIG', 'IAM_EXPORT']
    )
    
    # Run the test
    agent = AutomatedControlTestingAgent()
    result = await agent.run_automated_test(
        control_id=control_id,
        control_name=ctrl['name'],
        control_description=ctrl.get('description', ''),
        test_type=test_type,
        evidence_sources=test_run.evidence_sources,
        test_parameters=config.get('test_parameters', {}) if config else {},
        pass_criteria=config.get('pass_criteria', {}) if config else {}
    )
    
    # Update test run with results
    test_run.completed_at = datetime.now(timezone.utc)
    test_run.status = "COMPLETED"
    test_run.evidence_collected = result['evidence_collected']
    test_run.ai_analysis = result['ai_analysis']
    test_run.effectiveness_rating = result['effectiveness_rating']
    test_run.confidence_score = result['confidence_score']
    test_run.findings = result['findings']
    test_run.recommendations = result['recommendations']
    test_run.auto_generated_report = result['auto_generated_report']
    test_run.requires_human_review = result['confidence_score'] < 0.9 or result['effectiveness_rating'] != 'EFFECTIVE'
    
    # Save test run
    doc = test_run.model_dump()
    doc['started_at'] = doc['started_at'].isoformat()
    doc['completed_at'] = doc['completed_at'].isoformat()
    
    await db.automated_test_runs.insert_one(doc)
    
    # Update control's effectiveness if confidence is high
    if test_run.confidence_score >= 0.8:
        await db.custom_controls.update_one(
            {"id": control_id},
            {
                "$set": {
                    "effectiveness": test_run.effectiveness_rating,
                    "last_tested": datetime.now(timezone.utc).isoformat()
                }
            }
        )
    
    return {
        "test_run_id": test_run.id,
        "run_id": test_run.run_id,
        "status": test_run.status,
        "effectiveness_rating": test_run.effectiveness_rating,
        "confidence_score": test_run.confidence_score,
        "findings": test_run.findings,
        "recommendations": test_run.recommendations,
        "requires_human_review": test_run.requires_human_review,
        "report": test_run.auto_generated_report
    }


@api_router.get("/automated-tests/runs")
async def list_automated_test_runs(
    control_id: Optional[str] = None,
    status: Optional[str] = None,
    requires_review: bool = False,
    current_user: User = Depends(get_current_user)
):
    """List automated test runs"""
    query = {}
    if control_id:
        query["control_id"] = control_id
    if status:
        query["status"] = status
    if requires_review:
        query["requires_human_review"] = True
        query["reviewed_by"] = None
    
    runs = await db.automated_test_runs.find(query, {"_id": 0}).sort("started_at", -1).to_list(1000)
    
    for run in runs:
        if isinstance(run.get('started_at'), str):
            run['started_at'] = datetime.fromisoformat(run['started_at'])
        if run.get('completed_at') and isinstance(run['completed_at'], str):
            run['completed_at'] = datetime.fromisoformat(run['completed_at'])
    
    return runs


@api_router.get("/automated-tests/runs/{run_id}")
async def get_automated_test_run(
    run_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get automated test run details"""
    run = await db.automated_test_runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    if isinstance(run.get('started_at'), str):
        run['started_at'] = datetime.fromisoformat(run['started_at'])
    if run.get('completed_at') and isinstance(run['completed_at'], str):
        run['completed_at'] = datetime.fromisoformat(run['completed_at'])
    
    return run


@api_router.post("/automated-tests/runs/{run_id}/review")
async def review_automated_test(
    run_id: str,
    outcome: str,  # CONFIRMED, OVERRIDDEN, ESCALATED
    comments: Optional[str] = None,
    override_effectiveness: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Review an automated test result (LOD2/Admin)"""
    if current_user.role not in [UserRole.LOD2_USER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only LOD2 users can review automated tests")
    
    update_data = {
        "reviewed_by": current_user.id,
        "review_date": datetime.now(timezone.utc).isoformat(),
        "review_outcome": outcome,
        "requires_human_review": False
    }
    
    if comments:
        update_data["review_comments"] = comments
    
    if outcome == "OVERRIDDEN" and override_effectiveness:
        update_data["effectiveness_rating"] = override_effectiveness
        
        # Update control effectiveness
        run = await db.automated_test_runs.find_one({"id": run_id}, {"_id": 0})
        if run:
            await db.custom_controls.update_one(
                {"id": run['control_id']},
                {"$set": {"effectiveness": override_effectiveness}}
            )
    
    await db.automated_test_runs.update_one({"id": run_id}, {"$set": update_data})
    
    return {"message": f"Test review completed: {outcome}"}


@api_router.get("/automated-tests/evidence-sources")
async def list_evidence_sources(current_user: User = Depends(get_current_user)):
    """List available evidence sources"""
    return {
        "sources": [
            {"id": "AWS_CONFIG", "name": "AWS Config", "type": "Cloud Configuration", "description": "AWS configuration compliance data"},
            {"id": "AZURE_POLICY", "name": "Azure Policy", "type": "Cloud Configuration", "description": "Azure policy compliance status"},
            {"id": "GCP_SECURITY", "name": "GCP Security Command Center", "type": "Cloud Configuration", "description": "GCP security findings"},
            {"id": "SPLUNK", "name": "Splunk SIEM", "type": "Log Analysis", "description": "Security event log analysis"},
            {"id": "CLOUDWATCH", "name": "AWS CloudWatch", "type": "Monitoring", "description": "AWS monitoring and logs"},
            {"id": "IAM_EXPORT", "name": "IAM Policy Export", "type": "Access Control", "description": "Identity and access management data"},
            {"id": "VULNERABILITY_SCANNER", "name": "Vulnerability Scanner", "type": "Security Scanning", "description": "Vulnerability scan results"},
            {"id": "SIEM", "name": "Generic SIEM", "type": "Log Analysis", "description": "Security information and event management"},
            {"id": "GRC_SYSTEM", "name": "GRC System", "type": "Compliance", "description": "Data from integrated GRC tools"},
            {"id": "AI_ANALYSIS", "name": "AI Model Analysis", "type": "AI Testing", "description": "AI bias, fairness, and explainability testing"}
        ]
    }


@api_router.get("/automated-tests/test-types")
async def list_test_types(current_user: User = Depends(get_current_user)):
    """List available automated test types"""
    return {
        "test_types": [
            {"id": "CONFIGURATION_CHECK", "name": "Configuration Check", "description": "Verify system configurations against policy"},
            {"id": "LOG_ANALYSIS", "name": "Log Analysis", "description": "Analyze security logs for anomalies"},
            {"id": "ACCESS_REVIEW", "name": "Access Review", "description": "Review access permissions and entitlements"},
            {"id": "VULNERABILITY_SCAN", "name": "Vulnerability Scan", "description": "Check for known vulnerabilities"},
            {"id": "POLICY_COMPLIANCE", "name": "Policy Compliance", "description": "Verify compliance with defined policies"},
            {"id": "DATA_QUALITY", "name": "Data Quality", "description": "Assess data quality and integrity"},
            {"id": "AI_BIAS_CHECK", "name": "AI Bias Check", "description": "Test AI models for bias"},
            {"id": "AI_FAIRNESS", "name": "AI Fairness", "description": "Evaluate AI model fairness metrics"},
            {"id": "AI_EXPLAINABILITY", "name": "AI Explainability", "description": "Assess AI model interpretability"}
        ]
    }


# ============ GAP REMEDIATION ROUTES ============

@api_router.post("/gap-remediation", response_model=GapRemediation)
async def create_gap_remediation(
    remediation_data: GapRemediationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a gap remediation plan with AI recommendations"""
    # Get gap details
    gap = await db.control_gaps.find_one({"id": remediation_data.gap_id}, {"_id": 0})
    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")
    
    # Get existing controls for context
    existing_controls = await db.custom_controls.find(
        {"status": "APPROVED"},
        {"_id": 0}
    ).to_list(100)
    
    # Generate AI recommendations
    agent = GapRemediationAgent()
    recommendations = await agent.generate_recommendations(
        gap_description=gap['gap_description'],
        framework=gap['framework'],
        requirement_id=gap['requirement_id'],
        current_controls=[{"name": c['name'], "category": c.get('category', 'TECHNICAL')} for c in existing_controls],
        business_context={"business_unit": gap.get('business_unit', 'Unknown')}
    )
    
    # Create remediation plan
    remediation = GapRemediation(
        gap_id=gap['id'],
        gap_description=gap['gap_description'],
        framework=gap['framework'],
        requirement_id=gap['requirement_id'],
        priority=remediation_data.priority,
        ai_recommended_controls=recommendations.get('recommended_controls', []),
        ai_implementation_plan=recommendations.get('implementation_plan', ''),
        ai_effort_estimate=recommendations.get('effort_estimate', 'Medium'),
        ai_risk_if_delayed=recommendations.get('risk_if_delayed', ''),
        created_by=current_user.id,
        target_completion=remediation_data.target_completion
    )
    
    doc = remediation.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('target_completion'):
        doc['target_completion'] = doc['target_completion'].isoformat()
    
    await db.gap_remediations.insert_one(doc)
    
    # Update gap status
    await db.control_gaps.update_one(
        {"id": gap['id']},
        {"$set": {"status": "IN_PROGRESS"}}
    )
    
    return remediation


@api_router.get("/gap-remediation")
async def list_gap_remediations(
    status: Optional[str] = None,
    framework: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List gap remediation plans"""
    query = {}
    if status:
        query["status"] = status
    if framework:
        query["framework"] = framework
    
    remediations = await db.gap_remediations.find(query, {"_id": 0}).to_list(1000)
    
    for rem in remediations:
        if isinstance(rem.get('created_at'), str):
            rem['created_at'] = datetime.fromisoformat(rem['created_at'])
        if rem.get('approved_at') and isinstance(rem['approved_at'], str):
            rem['approved_at'] = datetime.fromisoformat(rem['approved_at'])
        if rem.get('target_completion') and isinstance(rem['target_completion'], str):
            rem['target_completion'] = datetime.fromisoformat(rem['target_completion'])
    
    return remediations


@api_router.get("/gap-remediation/{remediation_id}")
async def get_gap_remediation(
    remediation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get gap remediation details"""
    rem = await db.gap_remediations.find_one({"id": remediation_id}, {"_id": 0})
    if not rem:
        raise HTTPException(status_code=404, detail="Remediation plan not found")
    
    if isinstance(rem.get('created_at'), str):
        rem['created_at'] = datetime.fromisoformat(rem['created_at'])
    
    return rem


@api_router.put("/gap-remediation/{remediation_id}/select-approach")
async def select_remediation_approach(
    remediation_id: str,
    approach: str,  # IMPLEMENT, COMPENSATING, ACCEPT_RISK
    selected_control_ids: List[str] = [],
    compensating_controls: List[str] = [],
    current_user: User = Depends(get_current_user)
):
    """Select remediation approach and controls"""
    rem = await db.gap_remediations.find_one({"id": remediation_id}, {"_id": 0})
    if not rem:
        raise HTTPException(status_code=404, detail="Remediation plan not found")
    
    # Generate action items based on approach
    actions = []
    
    if approach == "IMPLEMENT":
        agent = GapRemediationAgent()
        selected_controls = [c for c in rem.get('ai_recommended_controls', []) 
                          if c.get('name') in selected_control_ids or True]  # Use all if none selected
        actions = await agent.create_implementation_plan(
            selected_controls[:3],  # Limit to 3 controls
            rem.get('priority', 'MEDIUM'),
            rem.get('target_completion')
        )
    elif approach == "COMPENSATING":
        for comp in compensating_controls:
            actions.append({
                "action_id": str(uuid.uuid4()),
                "action_type": "COMPENSATING_CONTROL",
                "description": f"Implement compensating control: {comp}",
                "assigned_to": None,
                "target_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "status": "PENDING"
            })
    elif approach == "ACCEPT_RISK":
        actions.append({
            "action_id": str(uuid.uuid4()),
            "action_type": "ACCEPT_RISK",
            "description": "Document risk acceptance with justification",
            "assigned_to": None,
            "target_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "status": "PENDING"
        })
    
    await db.gap_remediations.update_one(
        {"id": remediation_id},
        {
            "$set": {
                "selected_approach": approach,
                "selected_controls": selected_control_ids,
                "compensating_controls": compensating_controls,
                "actions": actions,
                "status": "APPROVED" if approach == "ACCEPT_RISK" else "IN_PROGRESS"
            }
        }
    )
    
    return {"message": f"Approach selected: {approach}", "actions_created": len(actions)}


@api_router.put("/gap-remediation/{remediation_id}/action/{action_id}")
async def update_remediation_action(
    remediation_id: str,
    action_id: str,
    status: str,
    notes: Optional[str] = None,
    evidence: List[str] = [],
    current_user: User = Depends(get_current_user)
):
    """Update a remediation action status"""
    rem = await db.gap_remediations.find_one({"id": remediation_id}, {"_id": 0})
    if not rem:
        raise HTTPException(status_code=404, detail="Remediation plan not found")
    
    actions = rem.get('actions', [])
    for action in actions:
        if action.get('action_id') == action_id:
            action['status'] = status
            if notes:
                action['notes'] = notes
            if evidence:
                action['evidence'] = evidence
            if status == "COMPLETED":
                action['completion_date'] = datetime.now(timezone.utc).isoformat()
            break
    
    # Calculate progress
    total = len(actions)
    completed = sum(1 for a in actions if a.get('status') == 'COMPLETED')
    progress = int(completed / total * 100) if total > 0 else 0
    
    await db.gap_remediations.update_one(
        {"id": remediation_id},
        {"$set": {"actions": actions, "progress_percentage": progress}}
    )
    
    return {"message": "Action updated", "progress": progress}


@api_router.post("/gap-remediation/{remediation_id}/approve")
async def approve_gap_remediation(
    remediation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Approve a gap remediation plan (LOD2/Admin)"""
    if current_user.role not in [UserRole.LOD2_USER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only LOD2 users can approve remediation plans")
    
    await db.gap_remediations.update_one(
        {"id": remediation_id},
        {
            "$set": {
                "status": "APPROVED",
                "approved_by": current_user.id,
                "approved_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Remediation plan approved"}


@api_router.post("/gap-remediation/{remediation_id}/complete")
async def complete_gap_remediation(
    remediation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark gap remediation as complete and trigger verification"""
    rem = await db.gap_remediations.find_one({"id": remediation_id}, {"_id": 0})
    if not rem:
        raise HTTPException(status_code=404, detail="Remediation plan not found")
    
    # Check all actions are complete
    actions = rem.get('actions', [])
    incomplete = [a for a in actions if a.get('status') != 'COMPLETED']
    
    if incomplete:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot complete: {len(incomplete)} actions still pending"
        )
    
    await db.gap_remediations.update_one(
        {"id": remediation_id},
        {
            "$set": {
                "status": "COMPLETED",
                "actual_completion": datetime.now(timezone.utc).isoformat(),
                "progress_percentage": 100
            }
        }
    )
    
    # Update gap status
    await db.control_gaps.update_one(
        {"id": rem['gap_id']},
        {"$set": {"status": "REMEDIATED", "closed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Gap remediation completed", "verification_required": rem.get('verification_required', True)}


@api_router.post("/gap-remediation/{remediation_id}/verify")
async def verify_gap_remediation(
    remediation_id: str,
    verification_method: str,
    verification_result: str,  # PASSED, FAILED
    comments: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Verify gap remediation (LOD2/Admin)"""
    if current_user.role not in [UserRole.LOD2_USER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only LOD2 users can verify remediation")
    
    update_data = {
        "verification_method": verification_method,
        "verified_by": current_user.id,
        "verified_at": datetime.now(timezone.utc).isoformat()
    }
    
    if verification_result == "PASSED":
        update_data["status"] = "VERIFIED"
    else:
        update_data["status"] = "VERIFICATION_FAILED"
    
    await db.gap_remediations.update_one({"id": remediation_id}, {"$set": update_data})
    
    return {"message": f"Verification result: {verification_result}"}


@api_router.get("/gap-remediation/recommendations/{gap_id}")
async def get_control_recommendations(
    gap_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get AI-generated control recommendations for a gap"""
    gap = await db.control_gaps.find_one({"id": gap_id}, {"_id": 0})
    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")
    
    existing_controls = await db.custom_controls.find(
        {"status": "APPROVED"},
        {"_id": 0}
    ).to_list(100)
    
    agent = GapRemediationAgent()
    recommendations = await agent.generate_recommendations(
        gap_description=gap['gap_description'],
        framework=gap['framework'],
        requirement_id=gap['requirement_id'],
        current_controls=[{"name": c['name'], "category": c.get('category', 'TECHNICAL')} for c in existing_controls],
        business_context={"business_unit": gap.get('business_unit', 'Unknown')}
    )
    
    return {
        "gap_id": gap_id,
        "framework": gap['framework'],
        "requirement_id": gap['requirement_id'],
        "recommendations": recommendations
    }


# ============ STARTUP & SHUTDOWN ============

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    await init_demo_users()
    await init_indexes()
    # Seed AI framework controls into MongoDB (idempotent — only inserts new controls)
    from seeds.ai_framework_controls import seed_ai_framework_controls
    await seed_ai_framework_controls()
    from seeds.ai_frameworks import seed_ai_frameworks
    await seed_ai_frameworks()
    # Load persisted LLM config (provider + model + user-supplied api_key)
    await LLMClientFactory.load_from_db()
    # Load persisted ServiceNow integration credentials (Basic or API token)
    try:
        from routes.servicenow import load_persisted_config as _sn_load
        await _sn_load()
    except Exception as _e:
        logger.warning(f"ServiceNow config rehydrate skipped: {_e}")
    
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
    
    logger.info("RiskShield platform started successfully")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await close_connection()


# Include main router
app.include_router(api_router)

# Include new feature routers
from routes.documents import api_router as documents_router
from routes.trends import api_router as trends_router
from routes.servicenow import api_router as servicenow_router
from routes.tenants import api_router as tenants_router
from routes.tech_risk import api_router as tech_risk_router
from routes.issue_management import api_router as issue_mgmt_router
from routes.control_analysis import api_router as control_analysis_router
from routes.system import api_router as system_router
from routes.my_work import api_router as my_work_router
from routes.audit import api_router as audit_router

app.include_router(documents_router, prefix="/api/rag", tags=["RAG & Documents"])
app.include_router(trends_router, prefix="/api/trends", tags=["Trend Analytics"])
app.include_router(servicenow_router, prefix="/api/servicenow", tags=["ServiceNow Integration"])
app.include_router(tenants_router, prefix="/api/tenants", tags=["Multi-Tenancy"])
app.include_router(tech_risk_router, prefix="/api/tech-risk", tags=["Tech Risk Assessment"])
app.include_router(issue_mgmt_router, prefix="/api/issue-management", tags=["Issue Management"])
app.include_router(control_analysis_router, prefix="/api/control-analysis", tags=["Control Analysis"])
app.include_router(system_router, prefix="/api/system", tags=["System Health & Usage"])
app.include_router(my_work_router, prefix="/api/my-work", tags=["My Work Inbox"])
app.include_router(audit_router, prefix="/api/audit", tags=["Audit Trail"])

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)