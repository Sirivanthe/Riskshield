# Multi-Agent System for Technology Risk and Control Assessment
import json
import re
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from db import db
from models import (
    Risk, Control, Evidence, Assessment, AssessmentStatus,
    RiskSeverity, ControlEffectiveness, AgentActivity, ActivityStatus,
    ModelMetrics, Explanation, ExplanationType, KnowledgeEntity, KnowledgeRelation,
    EntityType, RelationType, LLMConfig
)
from services.llm_client import LLMClientFactory, BaseLLMClient

logger = logging.getLogger(__name__)


def _parse_json_block(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort JSON extraction from an LLM response (handles ```json fences)."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(candidate[start:end + 1])
    except json.JSONDecodeError:
        return None


class RAGAgent:
    """Regulation & Knowledge Agent - handles regulatory document retrieval"""
    
    def __init__(self, llm_client: BaseLLMClient = None):
        self.llm = llm_client or LLMClientFactory.get_client()
        self.vector_store = {}  # In production, use FAISS or similar
    
    async def ingest_document(self, content: str, framework: str, metadata: Dict = None):
        """Ingest a document into the knowledge base"""
        # In production: chunk, embed, and store in FAISS
        chunks = self._chunk_text(content, chunk_size=500)
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{framework}_{i}"
            self.vector_store[chunk_id] = {
                "content": chunk,
                "framework": framework,
                "metadata": metadata or {}
            }
        
        return len(chunks)
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks if chunks else [text]
    
    async def query(self, question: str, frameworks: List[str]) -> str:
        """Query the knowledge base for relevant regulatory context"""
        # In production: embed question, search FAISS, return top-k results
        context_parts = []
        
        # Simulated retrieval based on frameworks
        framework_knowledge = {
            "NIST CSF": [
                "PR.AC-1: Identities and credentials are managed for authorized devices and users",
                "PR.AC-4: Access permissions are managed, incorporating the principles of least privilege",
                "PR.IP-12: A vulnerability management plan is developed and implemented",
                "DE.CM-8: Vulnerability scans are performed"
            ],
            "ISO 27001": [
                "A.9.2.1: User registration and de-registration",
                "A.10.1.1: Policy on the use of cryptographic controls",
                "A.12.6.1: Management of technical vulnerabilities",
                "A.18.1.3: Protection of records"
            ],
            "SOC2": [
                "CC6.1: Security software, infrastructure, and architectures are managed",
                "CC6.6: Logical access security measures are implemented",
                "CC7.2: System monitoring and security incident response",
                "CC8.1: Change management process"
            ],
            "PCI-DSS": [
                "Req 3.4: Render PAN unreadable anywhere it is stored",
                "Req 8.2: Strong authentication for users",
                "Req 10.2: Automated audit trails for security events",
                "Req 11.2: Run vulnerability scans quarterly"
            ],
            "GDPR": [
                "Article 25: Data protection by design and by default",
                "Article 32: Security of processing",
                "Article 33: Notification of data breach",
                "Article 35: Data protection impact assessment"
            ],
            "Basel III": [
                "BCBS 239: Principles for effective risk data aggregation",
                "Operational risk capital requirements",
                "Risk governance and oversight requirements"
            ]
        }
        
        for framework in frameworks:
            if framework in framework_knowledge:
                context_parts.append(f"\n{framework} Requirements:")
                for req in framework_knowledge[framework]:
                    context_parts.append(f"  - {req}")
        
        return "\n".join(context_parts) if context_parts else f"Relevant requirements for {', '.join(frameworks)}"


class RiskAssessmentAgent:
    """Identifies and assesses technology risks"""
    
    SYSTEM_PROMPT = """You are an expert technology risk assessor for banking and financial institutions.
Your role is to identify potential technology risks based on the system being assessed and relevant regulatory frameworks.
For each risk, provide:
1. A clear title
2. Detailed description
3. Severity rating (CRITICAL, HIGH, MEDIUM, LOW)
4. Applicable framework references
5. Likelihood assessment
6. Impact assessment
7. Recommended mitigation

Return your response as valid JSON with a "risks" array."""

    def __init__(self, llm_client: BaseLLMClient = None, rag_agent: RAGAgent = None):
        self.llm = llm_client or LLMClientFactory.get_client()
        self.rag = rag_agent or RAGAgent(self.llm)
    
    async def assess(self, system_name: str, frameworks: List[str], description: str) -> List[Risk]:
        """Assess risks for a given system"""
        # Get regulatory context from RAG
        regulatory_context = await self.rag.query(f"technology risks for {system_name}", frameworks)
        
        prompt = f"""Analyze the following system for technology risks:

System Name: {system_name}
Description: {description}
Frameworks: {', '.join(frameworks)}

Regulatory Context:
{regulatory_context}

Identify 3-5 key technology risks with proper severity ratings and mitigation recommendations.
Return as JSON with a "risks" array containing objects with: title, description, severity, framework, likelihood, impact, mitigation, regulatory_reference"""

        try:
            result = await self.llm.generate(prompt, regulatory_context, self.SYSTEM_PROMPT)
            response_text = result.get("response", "{}")

            data = _parse_json_block(response_text) or {}
            risks_data = data.get("risks") or self._generate_mock_risks(system_name, frameworks)
            
            risks = []
            for r in risks_data[:5]:  # Limit to 5 risks
                risks.append(Risk(
                    title=r.get("title", "Unknown Risk"),
                    description=r.get("description", ""),
                    severity=RiskSeverity(r.get("severity", "MEDIUM")),
                    framework=r.get("framework", frameworks[0] if frameworks else "NIST CSF"),
                    likelihood=r.get("likelihood", "Medium"),
                    impact=r.get("impact", "Medium"),
                    mitigation=r.get("mitigation", "Implement appropriate controls"),
                    regulatory_reference=r.get("regulatory_reference")
                ))
            
            return risks if risks else self._generate_default_risks(frameworks)
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return self._generate_default_risks(frameworks)
    
    def _generate_mock_risks(self, system_name: str, frameworks: List[str]) -> List[Dict]:
        """Generate mock risks for demo purposes"""
        return [
            {
                "title": "Inadequate Identity and Access Management",
                "description": f"IAM policies for {system_name} do not enforce MFA and principle of least privilege",
                "severity": "HIGH",
                "framework": "NIST CSF, ISO 27001",
                "likelihood": "High",
                "impact": "Critical",
                "mitigation": "Implement MFA, role-based access controls, and periodic access reviews",
                "regulatory_reference": "NIST CSF PR.AC-1, ISO 27001 A.9.2.1"
            },
            {
                "title": "Insufficient Data Encryption",
                "description": "Data at rest and in transit not encrypted with industry-standard algorithms",
                "severity": "MEDIUM",
                "framework": "ISO 27001, PCI-DSS",
                "likelihood": "Medium",
                "impact": "High",
                "mitigation": "Enable AES-256 encryption for all data stores and TLS 1.3 for transit",
                "regulatory_reference": "ISO 27001 A.10.1.1, PCI-DSS Req 3.4"
            },
            {
                "title": "Weak Audit Logging and Monitoring",
                "description": "Insufficient logging of security events and access attempts",
                "severity": "MEDIUM",
                "framework": "SOC2, GDPR",
                "likelihood": "Medium",
                "impact": "Medium",
                "mitigation": "Implement comprehensive logging with SIEM integration",
                "regulatory_reference": "SOC2 CC7.2, GDPR Article 32"
            },
            {
                "title": "Unpatched Vulnerabilities",
                "description": "Critical security patches not applied within SLA",
                "severity": "CRITICAL",
                "framework": "NIST CSF, Basel III",
                "likelihood": "High",
                "impact": "Critical",
                "mitigation": "Establish patch management process with automated scanning",
                "regulatory_reference": "NIST CSF PR.IP-12, Basel BCBS 239"
            }
        ]
    
    def _generate_default_risks(self, frameworks: List[str]) -> List[Risk]:
        """Generate default risks as fallback"""
        mock_data = self._generate_mock_risks("System", frameworks)
        return [Risk(
            title=r["title"],
            description=r["description"],
            severity=RiskSeverity(r["severity"]),
            framework=r["framework"],
            likelihood=r["likelihood"],
            impact=r["impact"],
            mitigation=r["mitigation"],
            regulatory_reference=r["regulatory_reference"]
        ) for r in mock_data[:3]]


class ControlTestingAgent:
    """Tests control effectiveness based on identified risks"""
    
    SYSTEM_PROMPT = """You are an expert control testing agent for banking technology risk management.
Your role is to evaluate controls that address identified risks and determine their effectiveness.
For each control, assess:
1. Control name and description
2. Effectiveness (EFFECTIVE, PARTIALLY_EFFECTIVE, INEFFECTIVE, NOT_TESTED)
3. Test results and observations
4. Framework alignment

Return your response as valid JSON with a "controls" array."""

    def __init__(self, llm_client: BaseLLMClient = None):
        self.llm = llm_client or LLMClientFactory.get_client()
    
    async def test_controls(self, risks: List[Risk], frameworks: List[str]) -> List[Control]:
        """Test controls for the given risks"""
        risk_summary = "\n".join([f"- {r.title}: {r.severity.value}" for r in risks])
        
        prompt = f"""Based on the following identified risks, evaluate the controls that should be in place:

Risks:
{risk_summary}

Frameworks: {', '.join(frameworks)}

For each risk, identify 1-2 relevant controls and assess their effectiveness.
Return as JSON with a "controls" array containing: name, description, effectiveness, test_result, framework"""

        try:
            result = await self.llm.generate(prompt, "", self.SYSTEM_PROMPT)
            response_text = result.get("response", "{}")

            data = _parse_json_block(response_text) or {}
            controls_data = data.get("controls") or self._generate_mock_controls(risks, frameworks)
            
            controls = []
            for c in controls_data:
                controls.append(Control(
                    name=c.get("name", "Unknown Control"),
                    description=c.get("description", ""),
                    effectiveness=ControlEffectiveness(c.get("effectiveness", "NOT_TESTED")),
                    test_result=c.get("test_result"),
                    framework=c.get("framework", frameworks[0] if frameworks else "NIST CSF"),
                    last_tested=datetime.now(timezone.utc)
                ))
            
            return controls if controls else self._generate_default_controls(frameworks)
            
        except Exception as e:
            logger.error(f"Control testing error: {e}")
            return self._generate_default_controls(frameworks)
    
    def _generate_mock_controls(self, risks: List[Risk], frameworks: List[str]) -> List[Dict]:
        """Generate mock controls"""
        return [
            {
                "name": "Multi-Factor Authentication (MFA)",
                "description": "MFA enforced for all privileged accounts",
                "effectiveness": "PARTIALLY_EFFECTIVE",
                "test_result": "MFA enabled but not enforced for 15% of admin accounts",
                "framework": "NIST CSF, ISO 27001"
            },
            {
                "name": "Encryption at Rest",
                "description": "AES-256 encryption for all databases",
                "effectiveness": "EFFECTIVE",
                "test_result": "All databases encrypted with AES-256. Key rotation: 90 days",
                "framework": "ISO 27001, PCI-DSS"
            },
            {
                "name": "Security Event Logging",
                "description": "Comprehensive audit trail for security events",
                "effectiveness": "INEFFECTIVE",
                "test_result": "Logging incomplete. Missing events: password changes, privilege escalation",
                "framework": "SOC2, GDPR"
            },
            {
                "name": "Vulnerability Scanning",
                "description": "Automated weekly vulnerability scans",
                "effectiveness": "PARTIALLY_EFFECTIVE",
                "test_result": "Scans running but 23 critical vulnerabilities unresolved >30 days",
                "framework": "NIST CSF, Basel III"
            },
            {
                "name": "Access Review Process",
                "description": "Quarterly access rights review",
                "effectiveness": "EFFECTIVE",
                "test_result": "Process documented and executed on schedule. 5% access revoked last quarter",
                "framework": "NIST CSF, ISO 27001"
            }
        ]
    
    def _generate_default_controls(self, frameworks: List[str]) -> List[Control]:
        """Generate default controls as fallback"""
        mock_data = self._generate_mock_controls([], frameworks)
        return [Control(
            name=c["name"],
            description=c["description"],
            effectiveness=ControlEffectiveness(c["effectiveness"]),
            test_result=c["test_result"],
            framework=c["framework"],
            last_tested=datetime.now(timezone.utc)
        ) for c in mock_data]


class EvidenceCollectionAgent:
    """Collects evidence from various sources to support control assessments"""
    
    def __init__(self, llm_client: BaseLLMClient = None):
        self.llm = llm_client or LLMClientFactory.get_client()
    
    async def collect(self, controls: List[Control]) -> List[Evidence]:
        """Collect evidence for the given controls"""
        evidence_items = [
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
        
        return evidence_items


class ReportingAgent:
    """Generates reports and summaries from assessment data"""
    
    def __init__(self, llm_client: BaseLLMClient = None):
        self.llm = llm_client or LLMClientFactory.get_client()
    
    def generate_summary(self, assessment: Assessment) -> Dict[str, Any]:
        """Generate assessment summary"""
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
    
    def __init__(self, llm_config: LLMConfig = None):
        self.llm_config = llm_config
        self.llm = LLMClientFactory.get_client(llm_config)
        self.rag_agent = RAGAgent(self.llm)
        self.risk_agent = RiskAssessmentAgent(self.llm, self.rag_agent)
        self.control_agent = ControlTestingAgent(self.llm)
        self.evidence_agent = EvidenceCollectionAgent(self.llm)
        self.reporting_agent = ReportingAgent(self.llm)
    
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
        # Cost calculation (example rates)
        cost_per_1k_prompt = 0.0015
        cost_per_1k_completion = 0.002
        
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
                    "severity": risk.severity.value,
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
                    "effectiveness": control.effectiveness.value,
                    "framework": control.framework
                }
            )
            entities.append(control_entity)
            
            # Relation: Control -> Mitigates -> Risk
            if assessment.risks:
                relation = KnowledgeRelation(
                    source_entity_id=control_entity.id,
                    target_entity_id=assessment.risks[0].id,
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
        """Run the full assessment workflow"""
        session_id = assessment.id
        start_time = datetime.now(timezone.utc)
        config = LLMClientFactory.get_current_config()
        
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
            
            await self.log_model_metrics(
                session_id, config.model_name, "risk_assessment",
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
                        f"Severity rated as {risk.severity.value} based on likelihood and impact matrix"
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
            
            await self.log_model_metrics(
                session_id, config.model_name, "control_testing",
                prompt_tokens=380, completion_tokens=290,
                latency_ms=step_duration
            )
            
            # Log explanations for controls
            for control in controls:
                await self.log_explanation(
                    session_id, "CONTROL_RATED",
                    control.id, control.name,
                    f"Control effectiveness rated as {control.effectiveness.value}. {control.test_result}",
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



class AutomatedControlTestingAgent:
    """AI-powered automated control testing with evidence collection"""
    
    SYSTEM_PROMPT = """You are an expert control testing agent for enterprise risk management.
Your role is to analyze evidence and determine control effectiveness.
Provide:
1. Clear effectiveness rating (EFFECTIVE, PARTIALLY_EFFECTIVE, INEFFECTIVE)
2. Confidence score (0.0 to 1.0)
3. Key findings from evidence analysis
4. Recommendations for improvement
5. Detailed reasoning for your assessment

Return your response as valid JSON."""

    def __init__(self, llm_client: BaseLLMClient = None):
        self.llm = llm_client or LLMClientFactory.get_client()
    
    async def run_automated_test(
        self,
        control_id: str,
        control_name: str,
        control_description: str,
        test_type: str,
        evidence_sources: List[str],
        test_parameters: Dict[str, Any] = None,
        pass_criteria: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Run an automated control test"""
        
        # Add appropriate sources based on test type
        test_type_sources = {
            "CONFIGURATION_CHECK": ["AWS_CONFIG", "IAM_EXPORT"],
            "LOG_ANALYSIS": ["SPLUNK", "CLOUDWATCH"],
            "ACCESS_REVIEW": ["IAM_EXPORT", "AWS_CONFIG"],
            "VULNERABILITY_SCAN": ["VULNERABILITY_SCANNER"],
            "POLICY_COMPLIANCE": ["AWS_CONFIG", "GRC_SYSTEM"],
            "DATA_QUALITY": ["AWS_CONFIG"],
            "AI_BIAS_CHECK": ["AI_ANALYSIS"],
            "AI_FAIRNESS": ["AI_ANALYSIS"],
            "AI_EXPLAINABILITY": ["AI_ANALYSIS"]
        }
        
        # Use test-type specific sources if none provided
        if not evidence_sources or evidence_sources == ['AWS_CONFIG', 'IAM_EXPORT']:
            evidence_sources = test_type_sources.get(test_type, ['AWS_CONFIG', 'IAM_EXPORT'])
        
        # Simulate evidence collection from sources
        collected_evidence = await self._collect_evidence(evidence_sources, test_type)

        # Analyze evidence using the real LLM. Falls back to heuristic analysis
        # automatically (inside _analyze_evidence) if the LLM call fails or the
        # response is not valid JSON.
        analysis_result = await self._analyze_evidence(
            control_name=control_name,
            control_description=control_description,
            test_type=test_type,
            evidence=collected_evidence,
            pass_criteria=pass_criteria or {},
        )
        
        return {
            "evidence_collected": collected_evidence,
            "ai_analysis": analysis_result,
            "effectiveness_rating": analysis_result.get("effectiveness", "NOT_TESTED"),
            "confidence_score": analysis_result.get("confidence", 0.0),
            "findings": analysis_result.get("findings", []),
            "recommendations": analysis_result.get("recommendations", []),
            "auto_generated_report": self._generate_report(control_name, test_type, collected_evidence, analysis_result)
        }
    
    async def _collect_evidence(self, sources: List[str], test_type: str) -> List[Dict[str, Any]]:
        """Collect evidence from specified sources (simulated)"""
        evidence = []
        
        source_data = {
            "AWS_CONFIG": {
                "source": "AWS Config",
                "type": "Configuration Snapshot",
                "data": {
                    "mfa_enabled_accounts": 85,
                    "total_accounts": 100,
                    "encryption_enabled": True,
                    "logging_enabled": True,
                    "compliant_resources": 247,
                    "non_compliant_resources": 12
                },
                "collected_at": datetime.now(timezone.utc).isoformat()
            },
            "IAM_EXPORT": {
                "source": "IAM Policy Export",
                "type": "Access Configuration",
                "data": {
                    "users_with_mfa": 85,
                    "privileged_accounts": 15,
                    "service_accounts": 23,
                    "last_access_review": "2026-02-15",
                    "orphan_accounts": 3
                },
                "collected_at": datetime.now(timezone.utc).isoformat()
            },
            "VULNERABILITY_SCANNER": {
                "source": "Vulnerability Scanner",
                "type": "Scan Results",
                "data": {
                    "critical_vulnerabilities": 5,
                    "high_vulnerabilities": 23,
                    "medium_vulnerabilities": 67,
                    "low_vulnerabilities": 142,
                    "scan_coverage": 98.5,
                    "last_scan": datetime.now(timezone.utc).isoformat()
                },
                "collected_at": datetime.now(timezone.utc).isoformat()
            },
            "SPLUNK": {
                "source": "Splunk SIEM",
                "type": "Log Analysis",
                "data": {
                    "security_events_24h": 1523,
                    "failed_logins": 47,
                    "privilege_escalations": 3,
                    "data_exfiltration_alerts": 0,
                    "log_coverage": 95.2
                },
                "collected_at": datetime.now(timezone.utc).isoformat()
            },
            "AI_ANALYSIS": {
                "source": "AI Model Analysis",
                "type": "Bias & Fairness Check",
                "data": {
                    "bias_score": 0.12,
                    "fairness_metrics": {
                        "demographic_parity": 0.92,
                        "equalized_odds": 0.88,
                        "calibration": 0.95
                    },
                    "explainability_score": 0.78,
                    "model_drift_detected": False
                },
                "collected_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        for source in sources:
            if source in source_data:
                evidence.append(source_data[source])
            else:
                evidence.append({
                    "source": source,
                    "type": "Generic Evidence",
                    "data": {"status": "collected", "timestamp": datetime.now(timezone.utc).isoformat()},
                    "collected_at": datetime.now(timezone.utc).isoformat()
                })
        
        return evidence
    
    async def _analyze_evidence(
        self,
        control_name: str,
        control_description: str,
        test_type: str,
        evidence: List[Dict[str, Any]],
        pass_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze collected evidence using AI"""
        
        evidence_summary = json.dumps(evidence, indent=2, default=str)
        
        prompt = f"""Analyze the following evidence for control effectiveness:

Control: {control_name}
Description: {control_description}
Test Type: {test_type}
Pass Criteria: {json.dumps(pass_criteria)}

Collected Evidence:
{evidence_summary}

Evaluate the control's effectiveness based on the evidence and provide:
1. effectiveness: EFFECTIVE, PARTIALLY_EFFECTIVE, or INEFFECTIVE
2. confidence: score from 0.0 to 1.0
3. findings: list of key observations
4. recommendations: list of improvement suggestions
5. reasoning: explanation for your assessment

Return as JSON."""

        try:
            result = await self.llm.generate(prompt, "", self.SYSTEM_PROMPT)
            response_text = result.get("response", "{}")

            analysis = _parse_json_block(response_text)
            if not analysis or not isinstance(analysis, dict):
                analysis = self._generate_mock_analysis(evidence, test_type)
            else:
                # Ensure required keys
                analysis.setdefault("effectiveness", "NOT_TESTED")
                analysis.setdefault("confidence", 0.0)
                analysis.setdefault("findings", [])
                analysis.setdefault("recommendations", [])
                analysis.setdefault("reasoning", "")

            return analysis

        except Exception as e:
            logger.error(f"Evidence analysis error: {e}")
            return self._generate_mock_analysis(evidence, test_type)
    
    def _generate_mock_analysis(self, evidence: List[Dict], test_type: str) -> Dict[str, Any]:
        """Generate mock analysis when LLM is unavailable"""
        
        # Simple heuristic-based analysis
        effectiveness = "PARTIALLY_EFFECTIVE"
        confidence = 0.75
        findings = []
        recommendations = []
        
        for ev in evidence:
            data = ev.get("data", {})
            
            if "mfa_enabled_accounts" in data:
                mfa_rate = data["mfa_enabled_accounts"] / data.get("total_accounts", 100)
                if mfa_rate >= 0.95:
                    effectiveness = "EFFECTIVE"
                    findings.append(f"MFA adoption rate is excellent at {mfa_rate*100:.1f}%")
                elif mfa_rate >= 0.80:
                    findings.append(f"MFA adoption rate is good at {mfa_rate*100:.1f}% but below target of 95%")
                    recommendations.append("Enforce MFA for remaining accounts within 30 days")
                else:
                    effectiveness = "INEFFECTIVE"
                    findings.append(f"MFA adoption rate is insufficient at {mfa_rate*100:.1f}%")
                    recommendations.append("Immediately mandate MFA for all accounts")
            
            if "critical_vulnerabilities" in data:
                crit = data["critical_vulnerabilities"]
                if crit == 0:
                    findings.append("No critical vulnerabilities detected")
                elif crit <= 5:
                    findings.append(f"{crit} critical vulnerabilities require immediate attention")
                    recommendations.append("Patch critical vulnerabilities within 24 hours per SLA")
                else:
                    effectiveness = "INEFFECTIVE"
                    findings.append(f"{crit} critical vulnerabilities detected - exceeds threshold")
                    recommendations.append("Initiate emergency patching protocol")
            
            if "bias_score" in data:
                bias = data["bias_score"]
                if bias <= 0.1:
                    findings.append(f"Model bias score of {bias} is within acceptable limits")
                elif bias <= 0.2:
                    findings.append(f"Model bias score of {bias} is elevated but manageable")
                    recommendations.append("Review model training data for potential bias sources")
                else:
                    effectiveness = "INEFFECTIVE"
                    findings.append(f"Model bias score of {bias} exceeds acceptable threshold")
                    recommendations.append("Immediate model retraining required with bias mitigation")
        
        if not findings:
            findings.append("Evidence collected and analyzed")
            
        if not recommendations:
            recommendations.append("Continue regular monitoring")
        
        return {
            "effectiveness": effectiveness,
            "confidence": confidence,
            "findings": findings,
            "recommendations": recommendations,
            "reasoning": f"Analysis based on {len(evidence)} evidence sources for {test_type} test"
        }
    
    def _generate_report(
        self,
        control_name: str,
        test_type: str,
        evidence: List[Dict],
        analysis: Dict[str, Any]
    ) -> str:
        """Generate automated test report"""
        
        report = f"""# Automated Control Test Report

## Control: {control_name}
## Test Type: {test_type}
## Test Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

---

### Overall Assessment
- **Effectiveness Rating**: {analysis.get('effectiveness', 'NOT_TESTED')}
- **Confidence Score**: {analysis.get('confidence', 0) * 100:.1f}%

---

### Evidence Collected
"""
        for ev in evidence:
            report += f"\n#### {ev.get('source', 'Unknown Source')}\n"
            report += f"- Type: {ev.get('type', 'Unknown')}\n"
            report += f"- Collected: {ev.get('collected_at', 'N/A')}\n"
        
        report += "\n---\n\n### Key Findings\n"
        for finding in analysis.get('findings', []):
            report += f"- {finding}\n"
        
        report += "\n---\n\n### Recommendations\n"
        for rec in analysis.get('recommendations', []):
            report += f"- {rec}\n"
        
        report += f"\n---\n\n### Analysis Reasoning\n{analysis.get('reasoning', 'N/A')}\n"
        
        return report


class GapRemediationAgent:
    """AI-powered control gap remediation with recommendations"""
    
    SYSTEM_PROMPT = """You are an expert GRC consultant specializing in control gap remediation.
Your role is to analyze control gaps and recommend appropriate remediation strategies.
Consider:
1. Regulatory requirements and compliance obligations
2. Implementation effort and cost
3. Effectiveness of proposed controls
4. Risk if the gap remains unaddressed
5. Alternative compensating controls

Provide practical, actionable recommendations with clear implementation guidance."""

    def __init__(self, llm_client: BaseLLMClient = None):
        self.llm = llm_client or LLMClientFactory.get_client()
    
    async def generate_recommendations(
        self,
        gap_description: str,
        framework: str,
        requirement_id: str,
        current_controls: List[Dict[str, Any]],
        business_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate AI-powered remediation recommendations.

        Calls the configured LLM (Emergent key by default) and falls back to
        the framework-specific mock library if the LLM call fails or returns
        an unparseable response.
        """
        current_controls_summary = json.dumps(
            [{"name": c.get("name"), "effectiveness": c.get("effectiveness")}
             for c in (current_controls or [])][:20],
            default=str,
        )
        business_context_summary = json.dumps(business_context or {}, default=str)

        prompt = f"""Propose remediation for a control gap.

Framework: {framework}
Requirement ID: {requirement_id}
Gap Description: {gap_description}
Current Controls: {current_controls_summary}
Business Context: {business_context_summary}

Respond with JSON in EXACTLY this schema:
{{
  "recommended_controls": [
    {{
      "name": "...",
      "description": "...",
      "category": "TECHNICAL | ADMINISTRATIVE | PHYSICAL | AI_GOVERNANCE | AI_OPERATIONAL | AI_TECHNICAL",
      "implementation_effort": "Low | Medium | High",
      "effectiveness_estimate": "Low | Medium | High",
      "cost_estimate": "Low | Medium | High",
      "time_to_implement": "e.g. 4-6 weeks",
      "prerequisites": ["..."],
      "regulatory_coverage": ["regulation or clause ids"],
      "ai_confidence": 0.0
    }}
  ],
  "implementation_plan": "markdown-formatted phased plan",
  "effort_estimate": "Low | Medium | High",
  "risk_if_delayed": "concise paragraph",
  "compensating_controls": ["..."],
  "timeline": "overall timeline"
}}"""

        try:
            result = await self.llm.generate(prompt, "", self.SYSTEM_PROMPT)
            response_text = result.get("response", "") or ""
            parsed = _parse_json_block(response_text)
            if parsed and isinstance(parsed, dict) and parsed.get("recommended_controls"):
                # Fill missing optional keys from the mock library so the
                # downstream contract (used by the remediation route / UI) is stable.
                fallback = self._generate_mock_recommendations(framework, requirement_id, gap_description)
                for key in ("implementation_plan", "effort_estimate", "risk_if_delayed",
                            "compensating_controls", "timeline"):
                    parsed.setdefault(key, fallback.get(key))
                return parsed
            logger.warning("GapRemediation LLM returned unusable response; falling back to mock")
        except Exception as e:
            logger.error(f"GapRemediation LLM error: {e}")

        return self._generate_mock_recommendations(framework, requirement_id, gap_description)
    
    def _generate_mock_recommendations(
        self,
        framework: str,
        requirement_id: str,
        gap_description: str
    ) -> Dict[str, Any]:
        """Generate mock recommendations based on framework"""
        
        # Framework-specific control recommendations
        framework_controls = {
            "NIST CSF": [
                {
                    "name": "Identity and Access Management Enhancement",
                    "description": "Implement comprehensive IAM with MFA, RBAC, and automated provisioning",
                    "category": "TECHNICAL",
                    "implementation_effort": "Medium",
                    "effectiveness_estimate": "High",
                    "cost_estimate": "Medium",
                    "time_to_implement": "4-6 weeks",
                    "prerequisites": ["Identity provider selection", "Role definition"],
                    "regulatory_coverage": ["NIST CSF PR.AC-1", "ISO 27001 A.9.2.1"],
                    "ai_confidence": 0.88
                },
                {
                    "name": "Continuous Vulnerability Management",
                    "description": "Automated vulnerability scanning with risk-based prioritization",
                    "category": "TECHNICAL",
                    "implementation_effort": "Medium",
                    "effectiveness_estimate": "High",
                    "cost_estimate": "Low",
                    "time_to_implement": "2-3 weeks",
                    "prerequisites": ["Scanner deployment", "Asset inventory"],
                    "regulatory_coverage": ["NIST CSF PR.IP-12", "PCI-DSS 11.2"],
                    "ai_confidence": 0.92
                }
            ],
            "EU_AI_ACT": [
                {
                    "name": "AI Risk Classification Framework",
                    "description": "Implement systematic AI risk classification per EU AI Act Article 6",
                    "category": "AI_GOVERNANCE",
                    "implementation_effort": "High",
                    "effectiveness_estimate": "High",
                    "cost_estimate": "Medium",
                    "time_to_implement": "6-8 weeks",
                    "prerequisites": ["AI inventory", "Risk assessment methodology"],
                    "regulatory_coverage": ["EU AI Act Art. 6", "EU AI Act Art. 9"],
                    "ai_confidence": 0.85
                },
                {
                    "name": "AI Transparency Documentation",
                    "description": "Comprehensive technical documentation for high-risk AI systems",
                    "category": "AI_GOVERNANCE",
                    "implementation_effort": "Medium",
                    "effectiveness_estimate": "High",
                    "cost_estimate": "Low",
                    "time_to_implement": "3-4 weeks",
                    "prerequisites": ["Documentation templates", "Model documentation"],
                    "regulatory_coverage": ["EU AI Act Art. 11", "EU AI Act Art. 13"],
                    "ai_confidence": 0.90
                },
                {
                    "name": "Human Oversight Mechanism",
                    "description": "Implement human-in-the-loop controls for high-risk AI decisions",
                    "category": "AI_OPERATIONAL",
                    "implementation_effort": "High",
                    "effectiveness_estimate": "High",
                    "cost_estimate": "High",
                    "time_to_implement": "8-12 weeks",
                    "prerequisites": ["Process redesign", "Training program"],
                    "regulatory_coverage": ["EU AI Act Art. 14"],
                    "ai_confidence": 0.82
                }
            ],
            "NIST_AI_RMF": [
                {
                    "name": "AI Risk Management Policy",
                    "description": "Establish organizational AI risk management governance",
                    "category": "AI_GOVERNANCE",
                    "implementation_effort": "Medium",
                    "effectiveness_estimate": "High",
                    "cost_estimate": "Low",
                    "time_to_implement": "3-4 weeks",
                    "prerequisites": ["Executive sponsorship", "Risk appetite definition"],
                    "regulatory_coverage": ["NIST AI RMF GOVERN-1", "GOVERN-2"],
                    "ai_confidence": 0.91
                },
                {
                    "name": "AI Trustworthiness Evaluation",
                    "description": "Framework for evaluating AI system trustworthiness characteristics",
                    "category": "AI_TECHNICAL",
                    "implementation_effort": "High",
                    "effectiveness_estimate": "High",
                    "cost_estimate": "Medium",
                    "time_to_implement": "6-8 weeks",
                    "prerequisites": ["Evaluation criteria", "Testing methodology"],
                    "regulatory_coverage": ["NIST AI RMF MEASURE-2.1"],
                    "ai_confidence": 0.87
                }
            ]
        }
        
        # Get controls for framework or use defaults
        controls = framework_controls.get(framework, framework_controls.get("NIST CSF", []))
        
        return {
            "recommended_controls": controls,
            "implementation_plan": f"""## Implementation Plan for {framework} Gap Remediation

### Phase 1: Assessment & Planning (Week 1-2)
1. Review current control environment
2. Identify resource requirements
3. Define success criteria
4. Obtain stakeholder approval

### Phase 2: Implementation (Week 3-8)
1. Deploy selected controls
2. Configure monitoring
3. Develop operational procedures
4. Train personnel

### Phase 3: Validation (Week 9-10)
1. Test control effectiveness
2. Document evidence
3. Conduct gap re-assessment
4. Obtain sign-off""",
            "effort_estimate": "Medium",
            "risk_if_delayed": f"Delayed remediation of {framework} {requirement_id} increases exposure to compliance violations, potential regulatory action, and reputational damage. Risk escalates over time.",
            "compensating_controls": [
                "Enhanced monitoring and alerting",
                "Manual review processes",
                "Increased audit frequency",
                "Management attestation"
            ],
            "timeline": "8-10 weeks for full implementation"
        }
    
    async def create_implementation_plan(
        self,
        selected_controls: List[Dict[str, Any]],
        priority: str,
        target_completion: datetime = None
    ) -> List[Dict[str, Any]]:
        """Create detailed implementation action items"""
        
        actions = []
        current_date = datetime.now(timezone.utc)
        
        for i, control in enumerate(selected_controls):
            effort = control.get("implementation_effort", "Medium")
            
            # Calculate target date based on effort
            days_map = {"Low": 14, "Medium": 42, "High": 84}
            target_days = days_map.get(effort, 42)
            
            if target_completion:
                target_date = target_completion
            else:
                target_date = current_date + timedelta(days=target_days)
            
            actions.append({
                "action_id": str(uuid.uuid4()),
                "action_type": "IMPLEMENT_CONTROL",
                "description": f"Implement: {control.get('name', 'Control')}",
                "details": control.get("description", ""),
                "assigned_to": None,
                "target_date": target_date.isoformat(),
                "status": "PENDING",
                "prerequisites": control.get("prerequisites", []),
                "effort": effort
            })
            
            # Add validation action
            actions.append({
                "action_id": str(uuid.uuid4()),
                "action_type": "VALIDATE_CONTROL",
                "description": f"Validate effectiveness of: {control.get('name', 'Control')}",
                "details": "Test control effectiveness and collect evidence",
                "assigned_to": None,
                "target_date": (target_date + timedelta(days=7)).isoformat(),
                "status": "PENDING",
                "prerequisites": [f"Complete implementation of {control.get('name', 'Control')}"],
                "effort": "Low"
            })
        
        return actions
