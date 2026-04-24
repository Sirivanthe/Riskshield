# Tech Risk Assessment API Routes
# Endpoints for application risk assessments with intelligent questionnaire

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import io

from services.tech_risk_assessment import TechRiskAssessmentService
from services.pdf_report_generator import PDFReportGenerator

logger = logging.getLogger(__name__)
api_router = APIRouter()

# Request/Response Models
class CreateAssessmentRequest(BaseModel):
    app_name: str
    description: Optional[str] = None
    business_unit: Optional[str] = None
    cmdb_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ApplicationContext(BaseModel):
    app_name: str
    description: Optional[str] = None
    business_unit: Optional[str] = None
    data_classification: Optional[str] = None  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    deployment_type: Optional[str] = None  # ON_PREM, CLOUD, HYBRID
    cloud_provider: Optional[str] = None
    hosting_location: Optional[str] = None
    internet_facing: Optional[bool] = False
    processes_pii: Optional[bool] = False
    processes_financial_data: Optional[bool] = False
    user_count: Optional[int] = 0
    criticality: Optional[str] = None  # CRITICAL, HIGH, MEDIUM, LOW
    integrations: Optional[List[str]] = []
    technologies: Optional[List[str]] = []
    last_pen_test: Optional[str] = None
    last_assessment: Optional[str] = None

class UpdateContextRequest(BaseModel):
    context: ApplicationContext

class QuestionnaireResponse(BaseModel):
    responses: Dict[str, Any]

class CreateIssuesRequest(BaseModel):
    risk_ids: Optional[List[str]] = None  # If None, create for all risks


@api_router.post("/assessments")
async def create_assessment(
    request: CreateAssessmentRequest,
    assessor_id: str = Query(...),
    assessor_name: str = Query(...)
):
    """
    Create a new tech risk assessment.
    
    Optionally provide CMDB ID to auto-populate context from CMDB.
    """
    try:
        service = TechRiskAssessmentService()
        
        # Build initial context
        context = request.context or {}
        context["description"] = request.description
        context["business_unit"] = request.business_unit
        
        # Try to get context from CMDB if ID provided
        if request.cmdb_id:
            cmdb_context = await service.get_context_from_cmdb(request.cmdb_id)
            if cmdb_context:
                context.update(cmdb_context)
                context["cmdb_id"] = request.cmdb_id
        
        # Try to get context from prior assessments
        prior_context = await service.get_context_from_prior_assessments(request.app_name)
        if prior_context:
            # Merge, preferring new context
            for key, value in prior_context.items():
                if key not in context or not context[key]:
                    context[key] = value
        
        # Try to get context from documents
        doc_context = await service.get_context_from_documents(request.app_name)
        if doc_context:
            context["document_context"] = doc_context.get("document_context")
        
        assessment = await service.create_assessment(
            app_name=request.app_name,
            assessor_id=assessor_id,
            assessor_name=assessor_name,
            context=context
        )
        
        return assessment
        
    except Exception as e:
        logger.error(f"Error creating assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/assessments")
async def list_assessments(
    status: Optional[str] = None,
    app_name: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """List tech risk assessments with optional filters."""
    try:
        service = TechRiskAssessmentService()
        assessments = await service.list_assessments(status, app_name, limit)
        return {"total": len(assessments), "assessments": assessments}
    except Exception as e:
        logger.error(f"Error listing assessments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/assessments/{assessment_id}")
async def get_assessment(assessment_id: str):
    """Get assessment details."""
    try:
        service = TechRiskAssessmentService()
        assessment = await service.get_assessment(assessment_id)
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        return assessment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/assessments/{assessment_id}/context")
async def update_context(assessment_id: str, request: UpdateContextRequest):
    """Update application context for an assessment."""
    try:
        from db import db
        
        context = request.context.dict(exclude_none=True)
        
        result = await db.tech_risk_assessments.update_one(
            {"id": assessment_id},
            {"$set": {"context": context, "updated_at": datetime.utcnow().isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        service = TechRiskAssessmentService()
        return await service.get_assessment(assessment_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/assessments/{assessment_id}/questions")
async def get_questions(assessment_id: str):
    """
    Get intelligent questionnaire based on application context.
    
    Questions are tailored based on:
    - Data classification
    - Deployment type
    - Criticality
    - Integrations
    """
    try:
        service = TechRiskAssessmentService()
        assessment = await service.get_assessment(assessment_id)
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        questions = await service.get_assessment_questions(
            assessment_id,
            assessment.get("context", {})
        )
        
        # Check which questions need answers
        existing_responses = assessment.get("questionnaire_responses", {})
        questions["answered_count"] = len(existing_responses)
        questions["context"] = assessment.get("context", {})
        
        return questions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/assessments/{assessment_id}/questionnaire")
async def submit_questionnaire(assessment_id: str, request: QuestionnaireResponse):
    """
    Submit questionnaire responses.
    
    Triggers:
    - Risk identification
    - Control recommendations
    - Overall risk rating calculation
    """
    try:
        service = TechRiskAssessmentService()
        result = await service.submit_questionnaire(assessment_id, request.responses)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting questionnaire: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/assessments/{assessment_id}/complete")
async def complete_assessment(
    assessment_id: str,
    reviewer_id: str = Query(...),
    reviewer_name: str = Query(...),
    review_comments: Optional[str] = None
):
    """Complete and finalize an assessment."""
    try:
        service = TechRiskAssessmentService()
        assessment = await service.complete_assessment(
            assessment_id,
            reviewer_id,
            reviewer_name,
            review_comments
        )
        return assessment
    except Exception as e:
        logger.error(f"Error completing assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/assessments/{assessment_id}/create-issues")
async def create_issues_from_assessment(
    assessment_id: str,
    request: CreateIssuesRequest,
    creator_id: str = Query(...),
    creator_name: str = Query(...)
):
    """Create issues from identified risks."""
    try:
        service = TechRiskAssessmentService()
        issues = await service.create_issues_from_risks(
            assessment_id,
            request.risk_ids
        )
        return {"issues_created": len(issues), "issues": issues}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/assessments/{assessment_id}/report")
async def download_report(
    assessment_id: str,
    include_recommendations: bool = Query(default=True),
    include_questionnaire: bool = Query(default=False)
):
    """
    Download risk assessment report as PDF.
    
    Report includes:
    - Executive summary
    - Overall risk rating
    - Identified risks with ratings
    - Control recommendations
    - Questionnaire responses (optional)
    """
    try:
        service = TechRiskAssessmentService()
        assessment = await service.get_assessment(assessment_id)
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Generate PDF
        generator = PDFReportGenerator()
        pdf_bytes = generator.generate_risk_assessment_report(
            assessment,
            include_recommendations=include_recommendations,
            include_questionnaire=include_questionnaire
        )
        
        # Return as downloadable file
        filename = f"risk_assessment_{assessment['assessment_id']}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/cmdb/{cmdb_id}")
async def get_cmdb_context(cmdb_id: str):
    """Fetch application context from CMDB."""
    try:
        service = TechRiskAssessmentService()
        context = await service.get_context_from_cmdb(cmdb_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="CMDB entry not found")
        
        return {"cmdb_id": cmdb_id, "context": context}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching CMDB context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/risk-categories")
async def get_risk_categories():
    """Get available risk categories."""
    return {
        "categories": [
            {"id": "SECURITY", "name": "Security", "description": "Information security risks"},
            {"id": "AVAILABILITY", "name": "Availability", "description": "System availability and resilience risks"},
            {"id": "DATA_INTEGRITY", "name": "Data Integrity", "description": "Data accuracy and protection risks"},
            {"id": "COMPLIANCE", "name": "Compliance", "description": "Regulatory and policy compliance risks"},
            {"id": "OPERATIONAL", "name": "Operational", "description": "Operational process risks"},
            {"id": "THIRD_PARTY", "name": "Third Party", "description": "Vendor and third-party risks"},
            {"id": "CHANGE_MANAGEMENT", "name": "Change Management", "description": "Change and release risks"},
            {"id": "ACCESS_CONTROL", "name": "Access Control", "description": "Identity and access management risks"}
        ]
    }


@api_router.get("/risk-ratings")
async def get_risk_ratings():
    """Get risk rating definitions."""
    return {
        "ratings": [
            {"id": "CRITICAL", "name": "Critical", "score": 4, "description": "Immediate action required", "color": "#dc2626"},
            {"id": "HIGH", "name": "High", "score": 3, "description": "Urgent attention needed", "color": "#ea580c"},
            {"id": "MEDIUM", "name": "Medium", "score": 2, "description": "Action within defined timeframe", "color": "#fbbf24"},
            {"id": "LOW", "name": "Low", "score": 1, "description": "Monitor and address as resources permit", "color": "#16a34a"}
        ],
        "likelihood_scale": ["ALMOST_CERTAIN", "LIKELY", "POSSIBLE", "UNLIKELY", "RARE"],
        "impact_scale": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NEGLIGIBLE"]
    }
