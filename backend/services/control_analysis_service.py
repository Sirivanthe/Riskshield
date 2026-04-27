# Control Analysis Service
# Comprehensive control register analysis, quality assessment, and regulatory mapping

import os
import io
import asyncio
import logging
import uuid
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
from collections import Counter
import re
import difflib

from db import db
from services import llm_evaluator

logger = logging.getLogger(__name__)

class ControlCategory(str, Enum):
    PREVENTIVE = "PREVENTIVE"
    DETECTIVE = "DETECTIVE"
    CORRECTIVE = "CORRECTIVE"
    COMPENSATING = "COMPENSATING"

class ControlType(str, Enum):
    TECHNICAL = "TECHNICAL"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    PHYSICAL = "PHYSICAL"
    OPERATIONAL = "OPERATIONAL"

class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class RequirementType(str, Enum):
    MANDATORY = "MANDATORY"
    RECOMMENDED = "RECOMMENDED"
    GOOD_TO_HAVE = "GOOD_TO_HAVE"

@dataclass
class ControlQualityMetrics:
    """Metrics for control quality assessment."""
    total_controls: int
    duplicates_found: int
    missing_descriptions: int
    missing_owners: int
    missing_test_procedures: int
    weak_controls: int
    strong_controls: int
    quality_score: float
    completeness_score: float
    uniqueness_score: float
    strength_score: float
    domain_coverage: Dict[str, int]
    control_type_distribution: Dict[str, int]

@dataclass 
class RegulatoryMapping:
    """Mapping between controls and regulatory requirements."""
    requirement_id: str
    requirement_text: str
    framework: str
    requirement_type: str  # MANDATORY, RECOMMENDED, GOOD_TO_HAVE
    mapped_controls: List[str]
    coverage_status: str  # COVERED, PARTIALLY_COVERED, NOT_COVERED
    gap_description: str

class ControlAnalysisService:
    """
    Service for comprehensive control analysis including:
    - Control register import (CSV, Excel, ServiceNow)
    - Quality analysis and duplicate detection
    - Regulatory compliance mapping
    - Coverage analysis by domain
    - AI-powered control language improvement
    """
    
    # Common control domains
    CONTROL_DOMAINS = [
        "Access Control", "Data Protection", "Network Security", "Application Security",
        "Change Management", "Incident Response", "Business Continuity", "Vendor Management",
        "Physical Security", "Compliance", "Audit", "Risk Management", "Identity Management",
        "Encryption", "Logging & Monitoring", "Configuration Management"
    ]
    
    # Keywords for control strength assessment
    STRONG_CONTROL_KEYWORDS = [
        "automated", "enforced", "mandatory", "real-time", "continuous", "encrypted",
        "multi-factor", "segregated", "verified", "validated"
    ]
    
    WEAK_CONTROL_KEYWORDS = [
        "manual", "periodic", "when possible", "as needed", "best effort",
        "should", "may", "consider", "encouraged"
    ]
    
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
    
    async def import_from_csv(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Import controls from CSV file."""
        try:
            df = pd.read_csv(io.BytesIO(file_content))
            return await self._process_import(df, filename, "CSV")
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            raise ValueError(f"Failed to parse CSV: {str(e)}")
    
    async def import_from_excel(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Import controls from Excel file."""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            return await self._process_import(df, filename, "EXCEL")
        except Exception as e:
            logger.error(f"Error importing Excel: {e}")
            raise ValueError(f"Failed to parse Excel: {str(e)}")
    
    async def import_from_servicenow(self, table: str = "sn_compliance_control") -> Dict[str, Any]:
        """Import controls from ServiceNow CMDB."""
        # Mock ServiceNow data - in production, this would call ServiceNow API
        mock_controls = [
            {
                "control_id": "CTRL-SN-001",
                "name": "Multi-Factor Authentication",
                "description": "MFA enforcement for all privileged accounts",
                "domain": "Access Control",
                "owner": "security-team@bank.com",
                "type": "TECHNICAL",
                "category": "PREVENTIVE",
                "test_procedure": "Verify MFA is enabled for 100% of admin accounts",
                "frameworks": ["NIST CSF", "ISO 27001", "PCI-DSS"]
            },
            {
                "control_id": "CTRL-SN-002",
                "name": "Data Encryption at Rest",
                "description": "All sensitive data encrypted using AES-256",
                "domain": "Data Protection",
                "owner": "data-team@bank.com",
                "type": "TECHNICAL",
                "category": "PREVENTIVE",
                "test_procedure": "Verify encryption is enabled on all databases",
                "frameworks": ["NIST CSF", "ISO 27001", "GDPR"]
            },
            {
                "control_id": "CTRL-SN-003",
                "name": "Change Advisory Board",
                "description": "All production changes require CAB approval",
                "domain": "Change Management",
                "owner": "change-mgmt@bank.com",
                "type": "ADMINISTRATIVE",
                "category": "PREVENTIVE",
                "test_procedure": "Review CAB meeting minutes and approval records",
                "frameworks": ["ISO 27001", "SOC2"]
            }
        ]
        
        df = pd.DataFrame(mock_controls)
        return await self._process_import(df, "ServiceNow Import", "SERVICENOW")
    
    async def _process_import(self, df: pd.DataFrame, source: str, source_type: str) -> Dict[str, Any]:
        """Process imported DataFrame and store controls."""
        # Normalize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Map common column variations
        column_mapping = {
            'control_name': 'name',
            'control_owner': 'owner',
            'control_title': 'name',
            'control_reference': 'control_id',
            'control_description': 'description',
            'control_type': 'type',
            'sub_domain': 'category',
            'classification': 'domain',
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        df = df.loc[:, ~df.columns.duplicated()]  
        imported_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                control = {
                    "id": str(uuid.uuid4()),
                    "control_id": row.get('control_id', f"CTRL-{idx+1:04d}"),
                    "name": row.get('name', ''),
                    "description": row.get('description', ''),
                    "domain": row.get('domain', 'General'),
                    "owner": row.get('owner', ''),
                    "type": row.get('type', 'TECHNICAL'),
                    "category": row.get('category', 'PREVENTIVE'),
                    "test_procedure": row.get('test_procedure', ''),
                    "frameworks": self._parse_frameworks(row.get('frameworks', '')),
                    "effectiveness": row.get('effectiveness', 'NOT_TESTED'),
                    "source": source_type,
                    "source_file": source,
                    "imported_at": datetime.now(timezone.utc).isoformat(),
                    "tenant_id": self.tenant_id
                }
                
                # Skip if no name
                if not control["name"]:
                    continue
                
                await db.control_register.insert_one(control)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {idx+1}: {str(e)}")
        
        return {
            "source": source,
            "source_type": source_type,
            "total_rows": len(df),
            "imported": imported_count,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _parse_frameworks(self, frameworks_str) -> List[str]:
        """Parse frameworks from string or list."""
        if isinstance(frameworks_str, list):
            return frameworks_str
        if pd.isna(frameworks_str) or not frameworks_str:
            return []
        return [f.strip() for f in str(frameworks_str).split(',')]
    
    async def analyze_control_quality(self) -> ControlQualityMetrics:
        """Perform comprehensive control quality analysis."""
        controls = await db.control_register.find(
            {"tenant_id": self.tenant_id},
            {"_id": 0}
        ).to_list(10000)
        
        if not controls:
            return ControlQualityMetrics(
                total_controls=0, duplicates_found=0, missing_descriptions=0,
                missing_owners=0, missing_test_procedures=0, weak_controls=0,
                strong_controls=0, quality_score=0.0,
                completeness_score=0.0, uniqueness_score=0.0, strength_score=0.0,
                domain_coverage={},
                control_type_distribution={}
            )
        
        # Duplicate detection
        names = [c.get('name', '').lower().strip() for c in controls]
        name_counts = Counter(names)
        duplicates = sum(count - 1 for count in name_counts.values() if count > 1)
        
        # Missing fields
        missing_desc = sum(1 for c in controls if not c.get('description'))
        missing_owner = sum(1 for c in controls if not c.get('owner'))
        missing_test = sum(1 for c in controls if not c.get('test_procedure'))
        
        # Control strength assessment
        weak = 0
        strong = 0
        for c in controls:
            text = f"{c.get('description', '')} {c.get('test_procedure', '')}".lower()
            if any(kw in text for kw in self.STRONG_CONTROL_KEYWORDS):
                strong += 1
            elif any(kw in text for kw in self.WEAK_CONTROL_KEYWORDS):
                weak += 1
        
        # Domain coverage
        domain_coverage = Counter(c.get('domain', 'Unknown') for c in controls)
        
        # Control type distribution
        type_distribution = Counter(c.get('type', 'Unknown') for c in controls)
        
        # Calculate quality score (0-100)
        total = len(controls)
        completeness = ((total - missing_desc) + (total - missing_owner) + (total - missing_test)) / (total * 3)
        uniqueness = (total - duplicates) / total if total > 0 else 0
        strength = strong / total if total > 0 else 0
        
        # Effectiveness component
        effective_count = len([c for c in controls if c.get('effectiveness') in ('EFFECTIVE', 'PARTIALLY_EFFECTIVE')])
        effectiveness = effective_count / total if total > 0 else 0
        
        quality_score = (completeness * 30 + uniqueness * 25 + strength * 20 + effectiveness * 25)
        
        return ControlQualityMetrics(
            total_controls=total,
            duplicates_found=duplicates,
            missing_descriptions=missing_desc,
            missing_owners=missing_owner,
            missing_test_procedures=missing_test,
            weak_controls=weak,
            strong_controls=strong,
            quality_score=round(quality_score, 2),
            completeness_score=round(completeness * 100, 2),
            uniqueness_score=round(uniqueness * 100, 2),
            strength_score=round(strength * 100, 2),
            domain_coverage=dict(domain_coverage),
            control_type_distribution=dict(type_distribution)
        )
    
    async def detect_duplicates(self, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Detect duplicate or similar controls."""
        controls = await db.control_register.find(
            {"tenant_id": self.tenant_id},
            {"_id": 0}
        ).to_list(10000)
        
        duplicates = []
        checked = set()
        
        for i, c1 in enumerate(controls):
            for j, c2 in enumerate(controls[i+1:], i+1):
                pair_key = (c1['id'], c2['id'])
                if pair_key in checked:
                    continue
                
                # Compare names
                name_similarity = difflib.SequenceMatcher(
                    None, 
                    c1.get('name', '').lower(), 
                    c2.get('name', '').lower()
                ).ratio()
                
                # Compare descriptions
                desc_similarity = difflib.SequenceMatcher(
                    None,
                    c1.get('description', '').lower(),
                    c2.get('description', '').lower()
                ).ratio()
                
                avg_similarity = (name_similarity + desc_similarity) / 2
                
                if avg_similarity >= similarity_threshold:
                    duplicates.append({
                        "control_1": {
                            "id": c1['id'],
                            "control_id": c1.get('control_id'),
                            "name": c1.get('name')
                        },
                        "control_2": {
                            "id": c2['id'],
                            "control_id": c2.get('control_id'),
                            "name": c2.get('name')
                        },
                        "similarity_score": round(avg_similarity, 3),
                        "recommendation": "MERGE" if avg_similarity > 0.9 else "REVIEW"
                    })
                
                checked.add(pair_key)
        
        return duplicates
    
    async def map_to_regulation(
        self,
        regulation_content: str,
        framework_name: str,
        use_llm_parser: bool = True,
    ) -> Dict[str, Any]:
        """Map controls to regulatory requirements.

        When ``use_llm_parser`` is True (default) the regulation text is parsed with the
        LLM so requirements are classified more accurately and enriched with keywords.
        Falls back to the regex parser automatically if the LLM call fails or returns empty.
        """
        controls = await db.control_register.find(
            {"tenant_id": self.tenant_id},
            {"_id": 0}
        ).to_list(10000)

        requirements: List[Dict] = []
        parser_used = "regex"
        parser_error: Optional[str] = None

        if use_llm_parser:
            llm_result = await llm_evaluator.parse_regulation_requirements(
                regulation_content, framework_name
            )
            llm_reqs = llm_result.get("requirements", [])
            if llm_reqs:
                requirements = llm_reqs
                parser_used = "llm"
            else:
                parser_error = llm_result.get("error", "LLM returned no requirements")

        if not requirements:
            requirements = self._parse_regulation_requirements(
                regulation_content, framework_name
            )
            parser_used = "regex" if parser_used != "llm" else parser_used

        # Persist obligations so other screens (Control Analysis, RCM Testing) can surface them.
        if requirements:
            now_iso = datetime.now(timezone.utc).isoformat()
            await db.regulatory_obligations.delete_many({
                "framework": framework_name, "tenant_id": self.tenant_id
            })
            await db.regulatory_obligations.insert_many([{
                "id": req["id"],
                "framework": framework_name,
                "tenant_id": self.tenant_id,
                "requirement_text": req["requirement_text"],
                "type": req.get("type", "GOOD_TO_HAVE"),
                "keywords": req.get("keywords", []),
                "rationale": req.get("rationale", ""),
                "persisted_at": now_iso,
            } for req in requirements])
        
        mappings = []
        covered_count = 0
        partially_covered_count = 0
        not_covered_count = 0
        
        for req in requirements:
            # Find matching controls
            matching_controls = []
            for control in controls:
                if self._control_matches_requirement(control, req):
                    matching_controls.append(control['control_id'])
            
            if len(matching_controls) >= 2:
                status = "COVERED"
                covered_count += 1
                gap = ""
            elif len(matching_controls) == 1:
                status = "PARTIALLY_COVERED"
                partially_covered_count += 1
                gap = "Only one control addresses this requirement. Consider additional controls."
            else:
                status = "NOT_COVERED"
                not_covered_count += 1
                gap = f"No controls found for requirement: {req['requirement_text'][:100]}"
            
            mappings.append(RegulatoryMapping(
                requirement_id=req['id'],
                requirement_text=req['requirement_text'],
                framework=framework_name,
                requirement_type=req['type'],
                mapped_controls=matching_controls,
                coverage_status=status,
                gap_description=gap
            ))
        
        total_reqs = len(requirements)
        compliance_score = (covered_count + 0.5 * partially_covered_count) / total_reqs * 100 if total_reqs > 0 else 0
        
        # Group by requirement type
        mandatory = [m for m in mappings if m.requirement_type == "MANDATORY"]
        recommended = [m for m in mappings if m.requirement_type == "RECOMMENDED"]
        good_to_have = [m for m in mappings if m.requirement_type == "GOOD_TO_HAVE"]
        
        return {
            "framework": framework_name,
            "parser_used": parser_used,
            "parser_error": parser_error,
            "total_requirements": total_reqs,
            "compliance_score": round(compliance_score, 2),
            "coverage_summary": {
                "covered": covered_count,
                "partially_covered": partially_covered_count,
                "not_covered": not_covered_count
            },
            "by_requirement_type": {
                "mandatory": {
                    "total": len(mandatory),
                    "covered": len([m for m in mandatory if m.coverage_status == "COVERED"]),
                    "gaps": [asdict(m) for m in mandatory if m.coverage_status == "NOT_COVERED"]
                },
                "recommended": {
                    "total": len(recommended),
                    "covered": len([m for m in recommended if m.coverage_status == "COVERED"])
                },
                "good_to_have": {
                    "total": len(good_to_have),
                    "covered": len([m for m in good_to_have if m.coverage_status == "COVERED"])
                }
            },
            "all_mappings": [asdict(m) for m in mappings],
            "gaps": [asdict(m) for m in mappings if m.coverage_status == "NOT_COVERED"]
        }
    
    def _parse_regulation_requirements(self, content: str, framework: str) -> List[Dict]:
        """Parse regulation content into requirements."""
        # Simplified parsing - in production use NLP or structured formats
        requirements = []
        
        # Split by common requirement patterns
        lines = content.split('\n')
        req_num = 1
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 20:
                continue
            
            # Determine requirement type
            line_lower = line.lower()
            if any(kw in line_lower for kw in ['must', 'shall', 'required', 'mandatory']):
                req_type = "MANDATORY"
            elif any(kw in line_lower for kw in ['should', 'recommended', 'expected']):
                req_type = "RECOMMENDED"
            else:
                req_type = "GOOD_TO_HAVE"
            
            requirements.append({
                "id": f"{framework}-REQ-{req_num:03d}",
                "requirement_text": line,
                "type": req_type
            })
            req_num += 1
        
        return requirements[:50]  # Limit for demo
    
    def _control_matches_requirement(self, control: Dict, requirement: Dict) -> bool:
        """Check if a control addresses a requirement.

        When the requirement was extracted by the LLM it may include a curated
        ``keywords`` list – we prefer those for matching. Otherwise we fall back
        to naive tokenization of the requirement text.
        """
        control_text = f"{control.get('name', '')} {control.get('description', '')}".lower()

        keywords = [str(k).lower() for k in (requirement.get("keywords") or []) if k]
        if not keywords:
            req_text = requirement['requirement_text'].lower()
            keywords = [w for w in req_text.split() if len(w) > 4][:10]

        if not keywords:
            return False

        matches = sum(1 for kw in keywords if kw in control_text)
        # LLM keywords are curated – one strong match is enough.
        threshold = 1 if requirement.get("keywords") else 2
        return matches >= threshold
    
    async def get_domain_coverage(self) -> Dict[str, Any]:
        """Get control coverage breakdown by domain."""
        controls = await db.control_register.find(
            {"tenant_id": self.tenant_id},
            {"_id": 0}
        ).to_list(10000)
        
        domain_stats = {}
        
        # Include both predefined domains and any custom domains from actual controls
        actual_domains = list(set(c.get('domain', 'Unknown') for c in controls))
        all_domains = list(set(self.CONTROL_DOMAINS + actual_domains))
        for domain in all_domains:
            domain_controls = [c for c in controls if c.get('domain') == domain]
            
            if domain_controls:
                effective = len([c for c in domain_controls if c.get('effectiveness') == 'EFFECTIVE'])
                partial = len([c for c in domain_controls if c.get('effectiveness') == 'PARTIALLY_EFFECTIVE'])
                ineffective = len([c for c in domain_controls if c.get('effectiveness') == 'INEFFECTIVE'])
                not_tested = len([c for c in domain_controls if c.get('effectiveness') == 'NOT_TESTED'])
                
                total = len(domain_controls)
                coverage_score = (effective + 0.5 * partial) / total * 100 if total > 0 else 0
                
                domain_stats[domain] = {
                    "total_controls": total,
                    "effective": effective,
                    "partially_effective": partial,
                    "ineffective": ineffective,
                    "not_tested": not_tested,
                    "coverage_score": round(coverage_score, 2)
                }
            else:
                domain_stats[domain] = {
                    "total_controls": 0,
                    "coverage_score": 0
                }
        
        return {
            "domains": domain_stats,
            "total_controls": len(controls),
            "covered_domains": len([d for d, s in domain_stats.items() if s['total_controls'] > 0]),
            "total_domains": len(all_domains)
        }
    
    async def uplift_control_language(self, control_id: str) -> Dict[str, Any]:
        """Use a real LLM (Emergent key) to improve control language."""
        control = await db.control_register.find_one(
            {"id": control_id, "tenant_id": self.tenant_id},
            {"_id": 0}
        )

        if not control:
            raise ValueError("Control not found")

        llm_result = await llm_evaluator.uplift_control_language(control)

        original_desc = control.get('description', '')
        original_test = control.get('test_procedure', '')
        original_name = control.get('name', '')

        improved_desc = llm_result.get("improved_description", original_desc)
        improved_test = llm_result.get("improved_test_procedure", original_test)
        improved_name = llm_result.get("improved_name", original_name)

        # Persist uplift history
        uplift_record = {
            "id": str(uuid.uuid4()),
            "control_id": control_id,
            "tenant_id": self.tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "original": {
                "name": original_name,
                "description": original_desc,
                "test_procedure": original_test,
            },
            "improved": {
                "name": improved_name,
                "description": improved_desc,
                "test_procedure": improved_test,
            },
            "changes_summary": llm_result.get("changes_summary", []),
            "recommendations": llm_result.get("recommendations", []),
        }
        await db.control_uplifts.insert_one(uplift_record.copy())

        return {
            "control_id": control_id,
            "original": {
                "name": original_name,
                "description": original_desc,
                "test_procedure": original_test,
            },
            "improved": {
                "name": improved_name,
                "description": improved_desc,
                "test_procedure": improved_test,
            },
            "changes": {
                "name_changed": original_name != improved_name,
                "description_changed": original_desc != improved_desc,
                "test_procedure_changed": original_test != improved_test,
            },
            "changes_summary": llm_result.get("changes_summary", []),
            "recommendations": llm_result.get("recommendations", []) or self._get_improvement_recommendations(control),
            "error": llm_result.get("error"),
        }
    
    def _improve_control_text(self, text: str, field_type: str) -> str:
        """Improve control text to be more precise and actionable."""
        if not text:
            return text
        
        improved = text
        
        # Replace weak language with strong language
        replacements = {
            'should be': 'must be',
            'may be': 'shall be',
            'as needed': 'according to defined schedule',
            'when possible': 'at all times',
            'periodically': 'on a quarterly basis',
            'regularly': 'on a monthly basis',
            'consider': 'implement',
            'attempt to': '',
            'try to': ''
        }
        
        for weak, strong in replacements.items():
            improved = re.sub(weak, strong, improved, flags=re.IGNORECASE)
        
        # Add specificity for test procedures
        if field_type == "test_procedure" and not any(word in improved.lower() for word in ['verify', 'review', 'inspect', 'confirm', 'validate']):
            improved = f"Verify that {improved.lower()}"
        
        return improved.strip()
    
    def _get_improvement_recommendations(self, control: Dict) -> List[str]:
        """Get recommendations for improving a control."""
        recommendations = []
        
        if not control.get('description'):
            recommendations.append("Add a detailed description of the control objective and implementation")
        
        if not control.get('test_procedure'):
            recommendations.append("Add a test procedure with specific steps to verify control effectiveness")
        
        if not control.get('owner'):
            recommendations.append("Assign a control owner responsible for maintenance and testing")
        
        desc = control.get('description', '').lower()
        if any(kw in desc for kw in self.WEAK_CONTROL_KEYWORDS):
            recommendations.append("Replace weak language (should, may, consider) with strong language (must, shall, required)")
        
        if not control.get('frameworks'):
            recommendations.append("Map control to relevant compliance frameworks")
        
        return recommendations
    
    async def update_control(self, control_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a control in the register."""
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        await db.control_register.update_one(
            {"id": control_id, "tenant_id": self.tenant_id},
            {"$set": updates}
        )
        
        return await db.control_register.find_one(
            {"id": control_id},
            {"_id": 0}
        )
    
    def _compute_strength_score(self, control: Dict[str, Any]) -> float:
        """Heuristic strength score 0–100 combining completeness + effectiveness."""
        weights = {
            "name": 10,
            "description": 20,
            "owner": 10,
            "test_procedure": 20,
            "frameworks": 10,
            "type": 5,
            "category": 5,
        }
        score = 0.0
        for field, w in weights.items():
            val = control.get(field)
            if field == "frameworks":
                if val and isinstance(val, list):
                    score += w
            elif field == "description":
                text = (val or "")
                if len(text) >= 80:
                    score += w
                elif text:
                    score += w * 0.5
            elif field == "test_procedure":
                text = (val or "")
                if len(text) >= 60:
                    score += w
                elif text:
                    score += w * 0.5
            elif val:
                score += w

        # Effectiveness multiplier (up to +20)
        eff = (control.get("effectiveness") or "NOT_TESTED").upper()
        eff_bonus = {
            "EFFECTIVE": 20,
            "PARTIALLY_EFFECTIVE": 10,
            "INEFFECTIVE": 0,
            "NOT_TESTED": 5,
        }.get(eff, 5)
        return min(100.0, score + eff_bonus)

    async def get_obligations_for_control(self, control: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find regulatory obligations that this control (likely) addresses."""
        obligations = await db.regulatory_obligations.find(
            {"tenant_id": self.tenant_id}, {"_id": 0}
        ).to_list(5000)
        matched: List[Dict[str, Any]] = []
        for ob in obligations:
            keywords = ob.get("keywords") or []
            fake_req = {
                "id": ob.get("id"),
                "requirement_text": ob.get("requirement_text", ""),
                "type": ob.get("type", "GOOD_TO_HAVE"),
                "keywords": keywords,
            }
            if self._control_matches_requirement(control, fake_req):
                matched.append(ob)
        return matched

    async def import_from_pdf(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extract controls from a PDF using an LLM and insert into the register."""
        try:
            import fitz  # PyMuPDF
            texts = []
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page in doc:
                    texts.append(page.get_text())
            text = "\n".join(texts)
        except Exception as e:
            logger.error(f"PDF parse failed: {e}")
            text = file_bytes.decode("utf-8", errors="ignore")

        if not text.strip():
            raise ValueError("PDF appears to be empty or unreadable")

        result = await llm_evaluator.extract_controls_from_text(text, source_hint=filename)
        extracted = result.get("controls") or []
        if not extracted:
            return {
                "source": "pdf", "filename": filename,
                "imported": 0, "total_rows": 0, "errors": [result.get("error", "No controls extracted by the LLM")],
            }

        now_iso = datetime.now(timezone.utc).isoformat()
        docs = []
        for c in extracted:
            docs.append({
                "id": str(uuid.uuid4()),
                "control_id": c.get("control_id"),
                "name": c.get("name", ""),
                "description": c.get("description", ""),
                "domain": c.get("domain", "Other"),
                "owner": c.get("owner", ""),
                "type": c.get("type", "ADMINISTRATIVE"),
                "category": c.get("category", "PREVENTIVE"),
                "test_procedure": c.get("test_procedure", ""),
                "frameworks": c.get("frameworks", []),
                "effectiveness": "NOT_TESTED",
                "source": "PDF_IMPORT",
                "source_file": filename,
                "imported_at": now_iso,
                "tenant_id": self.tenant_id,
            })
        if docs:
            await db.control_register.insert_many(docs)
        return {
            "source": "pdf", "filename": filename,
            "imported": len(docs), "total_rows": len(docs), "errors": [],
        }

    async def find_similar_controls(self, control_id: str, threshold: float = 0.45) -> List[Dict[str, Any]]:
        """Find controls similar to the given one (lower threshold than duplicates)."""
        import difflib
        target = await self.get_control(control_id)
        if not target:
            return []
        others = await db.control_register.find(
            {"tenant_id": self.tenant_id, "id": {"$ne": control_id}}, {"_id": 0}
        ).to_list(10000)
        target_text = f"{target.get('name', '')} {target.get('description', '')}".lower()
        scored = []
        for o in others:
            o_text = f"{o.get('name', '')} {o.get('description', '')}".lower()
            if not o_text:
                continue
            sim = difflib.SequenceMatcher(None, target_text, o_text).ratio()
            if sim >= threshold:
                scored.append({
                    "id": o["id"], "control_id": o.get("control_id"),
                    "name": o.get("name", ""), "domain": o.get("domain", ""),
                    "similarity_score": round(sim, 3),
                })
        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:10]

    async def get_controls(
        self,
        domain: str = None,
        framework: str = None,
        effectiveness: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get controls with filters and pagination.

        Returns {"total": <int>, "controls": [...], "limit": int, "offset": int}.
        """
        query = {"tenant_id": self.tenant_id}

        if domain:
            query["domain"] = domain
        if framework:
            query["frameworks"] = framework
        if effectiveness:
            query["effectiveness"] = effectiveness

        total = await db.control_register.count_documents(query)
        cursor = (
            db.control_register
            .find(query, {"_id": 0})
            .sort("imported_at", -1)
            .skip(max(offset, 0))
            .limit(max(limit, 1))
        )
        controls = await cursor.to_list(limit)

        # Enrich each control with strength_score and obligations_count so the register UI
        # can render scores and regulatory coverage without extra round-trips.
        obligations = await db.regulatory_obligations.find(
            {"tenant_id": self.tenant_id}, {"_id": 0}
        ).to_list(5000)

        for c in controls:
            c["strength_score"] = round(self._compute_strength_score(c), 1)
            ob_hits = 0
            for ob in obligations:
                fake_req = {
                    "id": ob.get("id"),
                    "requirement_text": ob.get("requirement_text", ""),
                    "type": ob.get("type", "GOOD_TO_HAVE"),
                    "keywords": ob.get("keywords") or [],
                }
                if self._control_matches_requirement(c, fake_req):
                    ob_hits += 1
            c["obligations_count"] = ob_hits

        # Distinct domains (across entire register, not just page) for filter dropdown
        domains = await db.control_register.distinct("domain", {"tenant_id": self.tenant_id})
        domains = [d for d in domains if d]

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "controls": controls,
            "domains": sorted(domains),
        }


    async def get_control(self, control_id: str) -> Optional[Dict[str, Any]]:
        """Get a single control by its internal id."""
        return await db.control_register.find_one(
            {"id": control_id, "tenant_id": self.tenant_id},
            {"_id": 0}
        )

    async def delete_control(self, control_id: str) -> bool:
        result = await db.control_register.delete_one(
            {"id": control_id, "tenant_id": self.tenant_id}
        )
        return result.deleted_count > 0

    async def evaluate_evidence(
        self,
        control_id: str,
        evidence_text: str,
        evidence_filename: Optional[str] = None,
        uploaded_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate evidence against a control's test script using a real LLM."""
        control = await self.get_control(control_id)
        if not control:
            raise ValueError("Control not found")

        # Run evidence evaluation and a preliminary 5W1H draft in parallel.
        # The narrative can be drafted from control + evidence even before the
        # evaluation verdict is finalised; this roughly halves wall-clock time.
        evaluation, narrative = await asyncio.gather(
            llm_evaluator.evaluate_evidence(control, evidence_text, evidence_filename),
            llm_evaluator.generate_5w1h(control, None, evidence_text),
        )

        record = {
            "id": str(uuid.uuid4()),
            "control_id": control_id,
            "control_code": control.get("control_id"),
            "tenant_id": self.tenant_id,
            "evidence_filename": evidence_filename,
            "evidence_excerpt": (evidence_text or "")[:2000],
            "evaluation": evaluation,
            "narrative_5w1h": narrative,
            "uploaded_by": uploaded_by,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.evidence_evaluations.insert_one(record.copy())

        # Update control effectiveness from evaluation
        effectiveness = evaluation.get("effectiveness", "NOT_TESTED")
        await db.control_register.update_one(
            {"id": control_id, "tenant_id": self.tenant_id},
            {"$set": {
                "effectiveness": effectiveness,
                "last_tested": datetime.now(timezone.utc).isoformat(),
                "last_evaluation_id": record["id"],
            }}
        )

        return {
            "evaluation_id": record["id"],
            "control_id": control_id,
            "control": control,
            "evaluation": evaluation,
            "narrative_5w1h": narrative,
            "created_at": record["created_at"],
        }

    async def list_evaluations(
        self,
        control_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"tenant_id": self.tenant_id}
        if control_id:
            query["control_id"] = control_id
        evaluations = await (
            db.evidence_evaluations
            .find(query, {"_id": 0})
            .sort("created_at", -1)
            .limit(limit)
            .to_list(limit)
        )
        return evaluations

    async def get_evaluation(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        return await db.evidence_evaluations.find_one(
            {"id": evaluation_id, "tenant_id": self.tenant_id},
            {"_id": 0}
        )

    async def generate_5w1h_report(self, control_id: str) -> Dict[str, Any]:
        """Generate (or regenerate) a 5W1H audit narrative for a control using latest evaluation."""
        control = await self.get_control(control_id)
        if not control:
            raise ValueError("Control not found")

        latest = await (
            db.evidence_evaluations
            .find({"control_id": control_id, "tenant_id": self.tenant_id}, {"_id": 0})
            .sort("created_at", -1)
            .limit(1)
            .to_list(1)
        )
        latest_eval = latest[0].get("evaluation") if latest else None
        latest_evidence = latest[0].get("evidence_excerpt") if latest else None

        narrative = await llm_evaluator.generate_5w1h(
            control, latest_eval, latest_evidence
        )
        return {
            "control_id": control_id,
            "control": control,
            "evaluation": latest_eval,
            "narrative_5w1h": narrative,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def build_workpaper_data(
        self,
        control_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Assemble workpaper dataset for PDF/Excel generation."""
        query: Dict[str, Any] = {"tenant_id": self.tenant_id}
        if control_ids:
            query["id"] = {"$in": control_ids}

        controls = await db.control_register.find(query, {"_id": 0}).to_list(10000)

        # Attach latest evaluation per control
        enriched: List[Dict[str, Any]] = []
        for c in controls:
            latest = await (
                db.evidence_evaluations
                .find(
                    {"control_id": c["id"], "tenant_id": self.tenant_id},
                    {"_id": 0}
                )
                .sort("created_at", -1)
                .limit(1)
                .to_list(1)
            )
            enriched.append({
                **c,
                "latest_evaluation": latest[0] if latest else None,
            })

        # Quality overview for the set
        metrics = await self.analyze_control_quality()

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tenant_id": self.tenant_id,
            "controls": enriched,
            "total_controls": len(enriched),
            "quality": asdict(metrics) if hasattr(metrics, "__dataclass_fields__") else metrics,
        }
