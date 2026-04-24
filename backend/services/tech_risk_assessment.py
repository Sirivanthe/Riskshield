# Tech Risk Assessment Service
# Intelligent risk assessment with context gathering and control recommendations

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from db import db

logger = logging.getLogger(__name__)

class RiskCategory(str, Enum):
    SECURITY = "SECURITY"
    AVAILABILITY = "AVAILABILITY"
    DATA_INTEGRITY = "DATA_INTEGRITY"
    COMPLIANCE = "COMPLIANCE"
    OPERATIONAL = "OPERATIONAL"
    THIRD_PARTY = "THIRD_PARTY"
    CHANGE_MANAGEMENT = "CHANGE_MANAGEMENT"
    ACCESS_CONTROL = "ACCESS_CONTROL"

class RiskRating(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class AssessmentStatus(str, Enum):
    DRAFT = "DRAFT"
    QUESTIONNAIRE = "QUESTIONNAIRE"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_REVIEW = "PENDING_REVIEW"
    COMPLETED = "COMPLETED"

@dataclass
class ApplicationContext:
    """Context information about the application being assessed."""
    app_name: str
    app_id: str
    description: str
    business_unit: str
    data_classification: str  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    deployment_type: str  # ON_PREM, CLOUD, HYBRID
    cloud_provider: Optional[str]
    hosting_location: str
    internet_facing: bool
    processes_pii: bool
    processes_financial_data: bool
    user_count: int
    criticality: str  # CRITICAL, HIGH, MEDIUM, LOW
    integrations: List[str]
    technologies: List[str]
    last_pen_test: Optional[str]
    last_assessment: Optional[str]
    cmdb_id: Optional[str]
    additional_context: Dict[str, Any]

@dataclass
class IdentifiedRisk:
    """A risk identified during assessment."""
    risk_id: str
    title: str
    description: str
    category: str
    likelihood: str  # ALMOST_CERTAIN, LIKELY, POSSIBLE, UNLIKELY, RARE
    impact: str  # CRITICAL, HIGH, MEDIUM, LOW, NEGLIGIBLE
    inherent_rating: str
    current_controls: List[str]
    control_effectiveness: str
    residual_rating: str
    recommended_controls: List[Dict[str, Any]]
    risk_response: str  # MITIGATE, ACCEPT, TRANSFER, AVOID
    owner: str
    due_date: Optional[str]

class TechRiskAssessmentService:
    """
    Service for conducting technology and application risk assessments.
    
    Features:
    - Intelligent questionnaire based on application context
    - Control suggestions from existing library
    - AI-powered risk identification
    - PDF report generation
    - Integration with CMDB and prior assessments
    """
    
    # Risk assessment questions by category
    ASSESSMENT_QUESTIONS = {
        "general": [
            {"id": "q1", "question": "What is the primary business function of this application?", "type": "text", "required": True},
            {"id": "q2", "question": "Who are the primary users of this application?", "type": "text", "required": True},
            {"id": "q3", "question": "What is the business impact if this application is unavailable for 4+ hours?", "type": "select", "options": ["Critical - Major financial/reputational impact", "High - Significant business disruption", "Medium - Moderate impact", "Low - Minimal impact"], "required": True},
        ],
        "data": [
            {"id": "q4", "question": "What types of sensitive data does this application process?", "type": "multiselect", "options": ["PII", "Financial Data", "Health Records", "Payment Card Data", "Intellectual Property", "None"], "required": True},
            {"id": "q5", "question": "Where is data stored at rest?", "type": "text", "required": True},
            {"id": "q6", "question": "Is data encrypted at rest and in transit?", "type": "select", "options": ["Yes, both", "Only in transit", "Only at rest", "No encryption"], "required": True},
        ],
        "access": [
            {"id": "q7", "question": "What authentication method is used?", "type": "multiselect", "options": ["SSO/SAML", "MFA", "Password only", "Certificate-based", "API Keys"], "required": True},
            {"id": "q8", "question": "How is access provisioned and deprovisioned?", "type": "text", "required": True},
            {"id": "q9", "question": "Are privileged access accounts separately managed?", "type": "select", "options": ["Yes, with PAM solution", "Yes, manually tracked", "No separate management"], "required": True},
        ],
        "infrastructure": [
            {"id": "q10", "question": "What is the disaster recovery strategy?", "type": "select", "options": ["Active-Active", "Active-Passive", "Backup/Restore", "None"], "required": True},
            {"id": "q11", "question": "What is the Recovery Time Objective (RTO)?", "type": "text", "required": True},
            {"id": "q12", "question": "When was the last vulnerability scan performed?", "type": "date", "required": False},
        ],
        "compliance": [
            {"id": "q13", "question": "Which regulatory frameworks apply to this application?", "type": "multiselect", "options": ["PCI-DSS", "GDPR", "SOX", "HIPAA", "SOC2", "ISO 27001", "NIST", "None specific"], "required": True},
            {"id": "q14", "question": "Are there any known compliance gaps?", "type": "text", "required": False},
            {"id": "q15", "question": "When was the last compliance audit?", "type": "date", "required": False},
        ],
        "third_party": [
            {"id": "q16", "question": "Does this application integrate with third-party services?", "type": "select", "options": ["Yes, critical dependencies", "Yes, non-critical", "No"], "required": True},
            {"id": "q17", "question": "Are third-party vendors assessed for security?", "type": "select", "options": ["Yes, regularly", "Yes, at onboarding only", "No"], "required": False},
        ],
        "change_management": [
            {"id": "q18", "question": "What is the change management process?", "type": "select", "options": ["Formal CAB approval", "Peer review only", "No formal process"], "required": True},
            {"id": "q19", "question": "How frequently are changes deployed?", "type": "select", "options": ["Multiple times daily", "Weekly", "Monthly", "Quarterly or less"], "required": True},
        ]
    }
    
    # Risk identification rules based on responses
    RISK_RULES = [
        {
            "condition": lambda ctx, resp: ctx.get("internet_facing") and "Password only" in resp.get("q7", []),
            "risk": {
                "title": "Weak Authentication for Internet-Facing Application",
                "description": "Internet-facing application uses password-only authentication without MFA, increasing risk of unauthorized access.",
                "category": "ACCESS_CONTROL",
                "likelihood": "LIKELY",
                "impact": "HIGH",
                "inherent_rating": "HIGH"
            }
        },
        {
            "condition": lambda ctx, resp: ctx.get("processes_pii") and resp.get("q6") in ["Only in transit", "No encryption"],
            "risk": {
                "title": "Inadequate Data Encryption for PII",
                "description": "Application processes PII but does not encrypt data at rest, risking data breach and regulatory non-compliance.",
                "category": "DATA_INTEGRITY",
                "likelihood": "POSSIBLE",
                "impact": "CRITICAL",
                "inherent_rating": "CRITICAL"
            }
        },
        {
            "condition": lambda ctx, resp: resp.get("q10") == "None",
            "risk": {
                "title": "No Disaster Recovery Strategy",
                "description": "Application has no disaster recovery strategy, risking extended outages and data loss.",
                "category": "AVAILABILITY",
                "likelihood": "POSSIBLE",
                "impact": "HIGH",
                "inherent_rating": "HIGH"
            }
        },
        {
            "condition": lambda ctx, resp: resp.get("q9") == "No separate management",
            "risk": {
                "title": "Privileged Access Not Separately Managed",
                "description": "Privileged accounts are not separately managed, increasing risk of unauthorized privileged access.",
                "category": "ACCESS_CONTROL",
                "likelihood": "LIKELY",
                "impact": "HIGH",
                "inherent_rating": "HIGH"
            }
        },
        {
            "condition": lambda ctx, resp: resp.get("q18") == "No formal process",
            "risk": {
                "title": "No Formal Change Management Process",
                "description": "Changes are deployed without formal approval process, risking unauthorized or unstable changes.",
                "category": "CHANGE_MANAGEMENT",
                "likelihood": "LIKELY",
                "impact": "MEDIUM",
                "inherent_rating": "MEDIUM"
            }
        },
        {
            "condition": lambda ctx, resp: resp.get("q16") == "Yes, critical dependencies" and resp.get("q17") == "No",
            "risk": {
                "title": "Unassessed Critical Third-Party Dependencies",
                "description": "Application has critical third-party dependencies that are not security assessed.",
                "category": "THIRD_PARTY",
                "likelihood": "POSSIBLE",
                "impact": "HIGH",
                "inherent_rating": "HIGH"
            }
        },
        {
            "condition": lambda ctx, resp: ctx.get("criticality") in ["CRITICAL", "HIGH"] and not ctx.get("last_pen_test"),
            "risk": {
                "title": "No Recent Penetration Test for Critical Application",
                "description": "Critical/high-criticality application has no recent penetration test, unknown vulnerabilities may exist.",
                "category": "SECURITY",
                "likelihood": "POSSIBLE",
                "impact": "HIGH",
                "inherent_rating": "HIGH"
            }
        }
    ]
    
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
    
    async def create_assessment(
        self,
        app_name: str,
        assessor_id: str,
        assessor_name: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new tech risk assessment."""
        assessment_id = str(uuid.uuid4())
        
        assessment = {
            "id": assessment_id,
            "assessment_id": f"TRA-{datetime.now().strftime('%Y%m%d')}-{assessment_id[:8].upper()}",
            "app_name": app_name,
            "status": AssessmentStatus.DRAFT.value,
            "context": context or {},
            "questionnaire_responses": {},
            "identified_risks": [],
            "recommended_controls": [],
            "overall_risk_rating": None,
            "assessor_id": assessor_id,
            "assessor_name": assessor_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "reviewed_by": None,
            "review_comments": None,
            "linked_issues": [],
            "tenant_id": self.tenant_id
        }
        
        await db.tech_risk_assessments.insert_one(assessment)
        logger.info(f"Created tech risk assessment: {assessment['assessment_id']}")
        
        return {k: v for k, v in assessment.items() if k != "_id"}
    
    async def get_context_from_cmdb(self, cmdb_id: str) -> Optional[Dict[str, Any]]:
        """Fetch application context from CMDB integration."""
        # Mock CMDB data - in production, this would call ServiceNow CMDB API
        mock_cmdb_data = {
            "app_name": "Payment Gateway",
            "description": "Core payment processing system",
            "business_unit": "Technology",
            "data_classification": "CONFIDENTIAL",
            "deployment_type": "CLOUD",
            "cloud_provider": "AWS",
            "hosting_location": "us-east-1",
            "internet_facing": True,
            "criticality": "CRITICAL",
            "technologies": ["Java", "PostgreSQL", "Redis", "Kafka"],
            "integrations": ["Core Banking", "Card Network", "Fraud Detection"],
            "owner": "payments-team@bank.com"
        }
        
        return mock_cmdb_data
    
    async def get_context_from_prior_assessments(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Get context from prior assessments."""
        prior = await db.tech_risk_assessments.find_one(
            {"app_name": app_name, "status": AssessmentStatus.COMPLETED.value},
            sort=[("completed_at", -1)]
        )
        
        if prior:
            return prior.get("context", {})
        return None
    
    async def get_context_from_documents(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Search RAG documents for application context."""
        try:
            from services.vector_store import MultiTenantVectorStoreManager
            from services.embedding_service import EmbeddingService
            
            embedding_service = EmbeddingService()
            vector_store = MultiTenantVectorStoreManager.get_store(self.tenant_id)
            
            # Search for relevant documents
            query = f"application {app_name} architecture security requirements"
            embedding = await embedding_service.generate_single_embedding(query)
            
            results = vector_store.search(embedding, k=3)
            
            if results:
                # Extract context from documents
                context_text = " ".join([r[2].get("content", "") for r in results])
                return {"document_context": context_text[:2000]}
        except Exception as e:
            logger.error(f"Error fetching document context: {e}")
        
        return None
    
    async def get_assessment_questions(
        self,
        assessment_id: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get intelligent questionnaire based on context."""
        questions = []
        
        # Add general questions
        questions.extend(self.ASSESSMENT_QUESTIONS["general"])
        
        # Add data questions if processes sensitive data
        if context and (context.get("processes_pii") or context.get("processes_financial_data")):
            questions.extend(self.ASSESSMENT_QUESTIONS["data"])
        else:
            questions.extend(self.ASSESSMENT_QUESTIONS["data"][:2])  # Basic data questions
        
        # Add access questions
        questions.extend(self.ASSESSMENT_QUESTIONS["access"])
        
        # Add infrastructure questions
        questions.extend(self.ASSESSMENT_QUESTIONS["infrastructure"])
        
        # Add compliance questions based on data types
        if context and context.get("data_classification") in ["CONFIDENTIAL", "RESTRICTED"]:
            questions.extend(self.ASSESSMENT_QUESTIONS["compliance"])
        else:
            questions.extend(self.ASSESSMENT_QUESTIONS["compliance"][:1])
        
        # Add third-party questions if integrations exist
        if context and context.get("integrations"):
            questions.extend(self.ASSESSMENT_QUESTIONS["third_party"])
        
        # Add change management questions
        questions.extend(self.ASSESSMENT_QUESTIONS["change_management"])
        
        return {
            "assessment_id": assessment_id,
            "total_questions": len(questions),
            "sections": {
                "General Information": [q for q in questions if q["id"] in ["q1", "q2", "q3"]],
                "Data Security": [q for q in questions if q["id"] in ["q4", "q5", "q6"]],
                "Access Control": [q for q in questions if q["id"] in ["q7", "q8", "q9"]],
                "Infrastructure": [q for q in questions if q["id"] in ["q10", "q11", "q12"]],
                "Compliance": [q for q in questions if q["id"] in ["q13", "q14", "q15"]],
                "Third Party": [q for q in questions if q["id"] in ["q16", "q17"]],
                "Change Management": [q for q in questions if q["id"] in ["q18", "q19"]]
            }
        }
    
    async def submit_questionnaire(
        self,
        assessment_id: str,
        responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit questionnaire responses and trigger risk identification."""
        assessment = await db.tech_risk_assessments.find_one({"id": assessment_id})
        if not assessment:
            raise ValueError("Assessment not found")
        
        # Update responses
        await db.tech_risk_assessments.update_one(
            {"id": assessment_id},
            {
                "$set": {
                    "questionnaire_responses": responses,
                    "status": AssessmentStatus.IN_PROGRESS.value,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Identify risks based on responses
        identified_risks = await self._identify_risks(assessment.get("context", {}), responses)
        
        # Get control recommendations
        recommended_controls = await self._recommend_controls(identified_risks)
        
        # Calculate overall risk rating
        overall_rating = self._calculate_overall_rating(identified_risks)
        
        # Update assessment with risks
        await db.tech_risk_assessments.update_one(
            {"id": assessment_id},
            {
                "$set": {
                    "identified_risks": identified_risks,
                    "recommended_controls": recommended_controls,
                    "overall_risk_rating": overall_rating,
                    "status": AssessmentStatus.PENDING_REVIEW.value,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "assessment_id": assessment_id,
            "risks_identified": len(identified_risks),
            "controls_recommended": len(recommended_controls),
            "overall_risk_rating": overall_rating,
            "status": AssessmentStatus.PENDING_REVIEW.value
        }
    
    async def _identify_risks(
        self,
        context: Dict[str, Any],
        responses: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify risks based on context and questionnaire responses."""
        risks = []
        
        for rule in self.RISK_RULES:
            try:
                if rule["condition"](context, responses):
                    risk = rule["risk"].copy()
                    risk["risk_id"] = f"RSK-{str(uuid.uuid4())[:8].upper()}"
                    risk["current_controls"] = []
                    risk["control_effectiveness"] = "NOT_ASSESSED"
                    risk["residual_rating"] = risk["inherent_rating"]
                    risk["recommended_controls"] = []
                    risk["risk_response"] = "MITIGATE"
                    risk["owner"] = ""
                    risk["due_date"] = None
                    risks.append(risk)
            except Exception as e:
                logger.error(f"Error evaluating risk rule: {e}")
        
        # Add standard risks based on context
        if context.get("internet_facing"):
            risks.append({
                "risk_id": f"RSK-{str(uuid.uuid4())[:8].upper()}",
                "title": "Internet-Facing Application Exposure",
                "description": "Application is internet-facing and subject to external threats.",
                "category": "SECURITY",
                "likelihood": "ALMOST_CERTAIN",
                "impact": "MEDIUM",
                "inherent_rating": "MEDIUM",
                "current_controls": [],
                "control_effectiveness": "NOT_ASSESSED",
                "residual_rating": "MEDIUM",
                "recommended_controls": [],
                "risk_response": "MITIGATE",
                "owner": "",
                "due_date": None
            })
        
        return risks
    
    async def _recommend_controls(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recommend controls from existing library or suggest new ones."""
        recommendations = []
        
        # Get existing controls from library
        existing_controls = await db.custom_controls.find(
            {"status": "APPROVED"},
            {"_id": 0}
        ).to_list(1000)
        
        control_map = {c.get("category", ""): c for c in existing_controls}
        
        # Standard control recommendations by risk category
        control_suggestions = {
            "ACCESS_CONTROL": [
                {"name": "Multi-Factor Authentication", "description": "Implement MFA for all user access", "source": "NEW", "priority": "HIGH"},
                {"name": "Privileged Access Management", "description": "Implement PAM solution for privileged accounts", "source": "NEW", "priority": "HIGH"},
                {"name": "Access Review Process", "description": "Quarterly access reviews for all accounts", "source": "NEW", "priority": "MEDIUM"}
            ],
            "DATA_INTEGRITY": [
                {"name": "Data Encryption at Rest", "description": "Encrypt all sensitive data at rest using AES-256", "source": "NEW", "priority": "CRITICAL"},
                {"name": "Data Loss Prevention", "description": "Implement DLP controls for sensitive data", "source": "NEW", "priority": "HIGH"},
                {"name": "Data Masking", "description": "Mask sensitive data in non-production environments", "source": "NEW", "priority": "MEDIUM"}
            ],
            "AVAILABILITY": [
                {"name": "Disaster Recovery Plan", "description": "Implement and test DR plan with defined RTO/RPO", "source": "NEW", "priority": "HIGH"},
                {"name": "High Availability Architecture", "description": "Implement active-passive or active-active HA", "source": "NEW", "priority": "HIGH"},
                {"name": "Backup and Recovery", "description": "Regular backups with tested recovery procedures", "source": "NEW", "priority": "MEDIUM"}
            ],
            "SECURITY": [
                {"name": "Vulnerability Management", "description": "Regular vulnerability scanning and patching", "source": "NEW", "priority": "HIGH"},
                {"name": "Penetration Testing", "description": "Annual penetration testing by qualified firm", "source": "NEW", "priority": "HIGH"},
                {"name": "Web Application Firewall", "description": "Implement WAF for internet-facing applications", "source": "NEW", "priority": "HIGH"}
            ],
            "THIRD_PARTY": [
                {"name": "Vendor Security Assessment", "description": "Annual security assessment of critical vendors", "source": "NEW", "priority": "HIGH"},
                {"name": "Third-Party Contract Review", "description": "Security requirements in all vendor contracts", "source": "NEW", "priority": "MEDIUM"}
            ],
            "CHANGE_MANAGEMENT": [
                {"name": "Change Advisory Board", "description": "CAB approval for all production changes", "source": "NEW", "priority": "MEDIUM"},
                {"name": "Code Review Process", "description": "Mandatory code review before deployment", "source": "NEW", "priority": "MEDIUM"}
            ],
            "COMPLIANCE": [
                {"name": "Compliance Monitoring", "description": "Continuous compliance monitoring and reporting", "source": "NEW", "priority": "MEDIUM"},
                {"name": "Audit Trail", "description": "Comprehensive audit logging for all actions", "source": "NEW", "priority": "MEDIUM"}
            ]
        }
        
        for risk in risks:
            category = risk.get("category", "")
            suggestions = control_suggestions.get(category, [])
            
            for suggestion in suggestions:
                # Check if control exists in library
                existing = next(
                    (c for c in existing_controls if suggestion["name"].lower() in c.get("name", "").lower()),
                    None
                )
                
                if existing:
                    recommendation = {
                        "control_id": existing.get("id"),
                        "name": existing.get("name"),
                        "description": existing.get("description"),
                        "source": "EXISTING_LIBRARY",
                        "priority": suggestion["priority"],
                        "addresses_risk": risk["risk_id"],
                        "implementation_status": "NOT_STARTED"
                    }
                else:
                    recommendation = {
                        "control_id": f"NEW-{str(uuid.uuid4())[:8].upper()}",
                        "name": suggestion["name"],
                        "description": suggestion["description"],
                        "source": "NEW_RECOMMENDATION",
                        "priority": suggestion["priority"],
                        "addresses_risk": risk["risk_id"],
                        "implementation_status": "NOT_STARTED"
                    }
                
                # Avoid duplicates
                if not any(r["name"] == recommendation["name"] for r in recommendations):
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_overall_rating(self, risks: List[Dict[str, Any]]) -> str:
        """Calculate overall risk rating based on identified risks."""
        if not risks:
            return "LOW"
        
        rating_scores = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        scores = [rating_scores.get(r.get("inherent_rating", "LOW"), 1) for r in risks]
        
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        
        # Overall rating is weighted toward highest risk
        weighted_score = (max_score * 0.6) + (avg_score * 0.4)
        
        if weighted_score >= 3.5:
            return "CRITICAL"
        elif weighted_score >= 2.5:
            return "HIGH"
        elif weighted_score >= 1.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def complete_assessment(
        self,
        assessment_id: str,
        reviewer_id: str,
        reviewer_name: str,
        review_comments: str = None
    ) -> Dict[str, Any]:
        """Complete and finalize the assessment."""
        await db.tech_risk_assessments.update_one(
            {"id": assessment_id},
            {
                "$set": {
                    "status": AssessmentStatus.COMPLETED.value,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "reviewed_by": reviewer_name,
                    "reviewer_id": reviewer_id,
                    "review_comments": review_comments,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        assessment = await db.tech_risk_assessments.find_one(
            {"id": assessment_id},
            {"_id": 0}
        )
        
        return assessment
    
    async def get_assessment(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Get assessment by ID."""
        assessment = await db.tech_risk_assessments.find_one(
            {"id": assessment_id},
            {"_id": 0}
        )
        return assessment
    
    async def list_assessments(
        self,
        status: str = None,
        app_name: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List assessments with optional filters."""
        query = {"tenant_id": self.tenant_id}
        
        if status:
            query["status"] = status
        if app_name:
            query["app_name"] = {"$regex": app_name, "$options": "i"}
        
        assessments = await db.tech_risk_assessments.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return assessments
    
    async def create_issues_from_risks(
        self,
        assessment_id: str,
        risk_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Create issues from identified risks."""
        assessment = await self.get_assessment(assessment_id)
        if not assessment:
            raise ValueError("Assessment not found")
        
        created_issues = []
        risks = assessment.get("identified_risks", [])
        
        if risk_ids:
            risks = [r for r in risks if r["risk_id"] in risk_ids]
        
        for risk in risks:
            issue = {
                "id": str(uuid.uuid4()),
                "issue_id": f"ISS-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}",
                "title": risk["title"],
                "description": risk["description"],
                "type": "RISK_FINDING",
                "severity": risk["inherent_rating"],
                "priority": "P1" if risk["inherent_rating"] in ["CRITICAL", "HIGH"] else "P2",
                "status": "OPEN",
                "source": "TECH_RISK_ASSESSMENT",
                "source_id": assessment_id,
                "source_risk_id": risk["risk_id"],
                "app_name": assessment["app_name"],
                "owner": risk.get("owner", ""),
                "due_date": risk.get("due_date"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "history": [{
                    "action": "CREATED",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "details": f"Created from Tech Risk Assessment {assessment['assessment_id']}"
                }],
                "tenant_id": self.tenant_id
            }
            
            await db.issues.insert_one(issue)
            created_issues.append({k: v for k, v in issue.items() if k != "_id"})
        
        # Link issues to assessment
        issue_ids = [i["id"] for i in created_issues]
        await db.tech_risk_assessments.update_one(
            {"id": assessment_id},
            {"$addToSet": {"linked_issues": {"$each": issue_ids}}}
        )
        
        return created_issues
