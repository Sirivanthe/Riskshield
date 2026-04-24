# LLM Evaluator Service — rewritten to use Gemini REST API directly (no emergentintegrations)
import os
import json
import logging
import uuid
import re
import httpx
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")


def _get_api_key() -> str:
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY is not configured in backend/.env")
    return key


async def _call_gemini(system_message: str, prompt: str) -> str:
    api_key = _get_api_key()
    model = DEFAULT_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    full_prompt = f"{system_message}\n\n{prompt}"
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            url,
            json={"contents": [{"parts": [{"text": full_prompt}]}]}
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


def _extract_json(text: str) -> Dict[str, Any]:
    """Best-effort JSON extraction from an LLM response."""
    if not text:
        return {}
    # Strip code fences if present
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text

    # Find first {...} block
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {"raw": text}

    try:
        return json.loads(candidate[start:end + 1])
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM JSON response; returning raw text")
        return {"raw": text}


async def evaluate_evidence(
    control: Dict[str, Any],
    evidence_text: str,
    evidence_filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluate uploaded evidence against a control's test script.
    Returns: {status, confidence, reasoning, gaps, recommendations, tested_attributes}
    """
    system_message = (
        "You are a senior banking technology auditor evaluating audit evidence "
        "against control test scripts. You are rigorous, skeptical, and concise. "
        "Respond ONLY with valid JSON matching the requested schema."
    )

    prompt = f"""Evaluate whether the uploaded evidence validates the following control per its test script.

CONTROL:
- Control ID: {control.get('control_id', 'N/A')}
- Name: {control.get('name', '')}
- Description: {control.get('description', '')}
- Domain: {control.get('domain', '')}
- Type: {control.get('type', '')}
- Category: {control.get('category', '')}
- Frameworks: {', '.join(control.get('frameworks', []) or [])}

TEST SCRIPT / PROCEDURE:
{control.get('test_procedure', '(none provided)')}

EVIDENCE (file: {evidence_filename or 'unknown'}):
{evidence_text[:8000]}

Respond with JSON in EXACTLY this schema:
{{
  "status": "PASS" | "FAIL" | "PARTIAL" | "INSUFFICIENT",
  "confidence": 0-100,
  "effectiveness": "EFFECTIVE" | "PARTIALLY_EFFECTIVE" | "INEFFECTIVE" | "NOT_TESTED",
  "reasoning": "concise 2-4 sentence justification",
  "tested_attributes": ["list of attributes/aspects the evidence covers"],
  "gaps": ["specific gaps or missing evidence items"],
  "recommendations": ["specific actionable remediation recommendations"],
  "audit_opinion": "one-sentence overall opinion"
}}"""

    try:
        response = await _call_gemini(system_message, prompt)
        result = _extract_json(response)
        result.setdefault("status", "INSUFFICIENT")
        result.setdefault("confidence", 0)
        result.setdefault("effectiveness", "NOT_TESTED")
        result.setdefault("reasoning", "")
        result.setdefault("tested_attributes", [])
        result.setdefault("gaps", [])
        result.setdefault("recommendations", [])
        result.setdefault("audit_opinion", "")
        return result
    except Exception as e:
        logger.error(f"LLM evaluate_evidence failed: {e}")
        return {
            "status": "ERROR",
            "confidence": 0,
            "effectiveness": "NOT_TESTED",
            "reasoning": f"LLM evaluation failed: {str(e)}",
            "tested_attributes": [],
            "gaps": ["LLM evaluation unavailable"],
            "recommendations": ["Retry evaluation or perform manual review"],
            "audit_opinion": "Unable to generate opinion due to LLM error",
            "error": str(e),
        }


async def generate_5w1h(
    control: Dict[str, Any],
    evaluation: Optional[Dict[str, Any]] = None,
    evidence_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a 5W1H audit narrative for a control and its most recent evaluation."""
    system_message = (
        "You are a banking audit report writer. Produce an accurate, concise, "
        "professional 5W1H narrative (Who, What, When, Where, Why, How). "
        "Respond ONLY with valid JSON."
    )

    prompt = f"""Produce a 5W1H audit narrative for this control and its evidence evaluation.

CONTROL:
- ID: {control.get('control_id', 'N/A')}
- Name: {control.get('name', '')}
- Description: {control.get('description', '')}
- Owner: {control.get('owner', 'N/A')}
- Domain: {control.get('domain', 'N/A')}
- Test Procedure: {control.get('test_procedure', 'N/A')}
- Frameworks: {', '.join(control.get('frameworks', []) or [])}

EVALUATION OUTCOME:
{json.dumps(evaluation or {}, indent=2)[:2000]}

EVIDENCE EXCERPT:
{(evidence_text or '')[:3000]}

Respond with JSON in EXACTLY this schema:
{{
  "who": "parties involved (owners, reviewers, testers)",
  "what": "what control does and what was tested",
  "when": "timing/frequency and when the test was performed",
  "where": "systems/locations/environments covered",
  "why": "regulatory/business rationale for the control",
  "how": "how the control operates and how evidence was validated",
  "summary": "2-3 sentence executive summary",
  "audit_conclusion": "one-sentence formal conclusion"
}}"""

    try:
        response = await _call_gemini(system_message, prompt)
        result = _extract_json(response)
        for k in ["who", "what", "when", "where", "why", "how", "summary", "audit_conclusion"]:
            result.setdefault(k, "")
        return result
    except Exception as e:
        logger.error(f"LLM generate_5w1h failed: {e}")
        return {
            "who": "", "what": "", "when": "", "where": "", "why": "", "how": "",
            "summary": f"5W1H generation failed: {str(e)}",
            "audit_conclusion": "",
            "error": str(e),
        }


async def uplift_control_language(control: Dict[str, Any]) -> Dict[str, Any]:
    """Use LLM to rewrite control description and test procedure into precise audit language."""
    system_message = (
        "You are a control language editor for a global bank. Rewrite control text so it is "
        "specific, testable, measurable, uses mandatory language (must/shall), and avoids "
        "weak qualifiers (may, consider, periodically, as needed). Preserve intent. "
        "Respond ONLY with valid JSON."
    )

    prompt = f"""Improve this control's language.

ORIGINAL:
- Name: {control.get('name', '')}
- Description: {control.get('description', '')}
- Test Procedure: {control.get('test_procedure', '')}

Respond with JSON in EXACTLY this schema:
{{
  "improved_name": "<=80 char concise name",
  "improved_description": "precise, mandatory-language description",
  "improved_test_procedure": "clear verifiable step-by-step test procedure",
  "changes_summary": ["bullet list of key changes made"],
  "recommendations": ["additional improvements the owner should consider"]
}}"""

    try:
        response = await _call_gemini(system_message, prompt)
        result = _extract_json(response)
        result.setdefault("improved_name", control.get("name", ""))
        result.setdefault("improved_description", control.get("description", ""))
        result.setdefault("improved_test_procedure", control.get("test_procedure", ""))
        result.setdefault("changes_summary", [])
        result.setdefault("recommendations", [])
        return result
    except Exception as e:
        logger.error(f"LLM uplift_control_language failed: {e}")
        return {
            "improved_name": control.get("name", ""),
            "improved_description": control.get("description", ""),
            "improved_test_procedure": control.get("test_procedure", ""),
            "changes_summary": [],
            "recommendations": [f"LLM uplift failed: {str(e)}"],
            "error": str(e),
        }


async def parse_regulation_requirements(
    content: str,
    framework: str,
    max_requirements: int = 80,
) -> Dict[str, Any]:
    """
    Use an LLM to extract structured requirements from raw regulation text.
    Returns {"requirements": [{id, requirement_text, type, rationale, keywords}]}
    where type is MANDATORY | RECOMMENDED | GOOD_TO_HAVE.
    """
    system_message = (
        "You are a regulatory analyst. Extract each distinct requirement from regulation text "
        "and classify it as MANDATORY (must/shall/required), RECOMMENDED (should/expected), or "
        "GOOD_TO_HAVE (may/consider). Deduplicate near-identical items. "
        "Respond ONLY with valid JSON."
    )

    prompt = f"""Framework: {framework}

Regulation text:
\"\"\"
{content[:12000]}
\"\"\"

Extract up to {max_requirements} distinct requirements. Respond with JSON in EXACTLY this schema:
{{
  "requirements": [
    {{
      "id": "{framework}-REQ-001",
      "requirement_text": "concise requirement statement",
      "type": "MANDATORY" | "RECOMMENDED" | "GOOD_TO_HAVE",
      "rationale": "1-sentence why the classification was chosen",
      "keywords": ["3-6 key terms a control must address to satisfy this requirement"]
    }}
  ]
}}"""

    try:
        response = await _call_gemini(system_message, prompt)
        result = _extract_json(response)
        reqs = result.get("requirements") or []
        cleaned = []
        for i, r in enumerate(reqs[:max_requirements], start=1):
            cleaned.append({
                "id": r.get("id") or f"{framework}-REQ-{i:03d}",
                "requirement_text": r.get("requirement_text", ""),
                "type": (r.get("type") or "GOOD_TO_HAVE").upper(),
                "rationale": r.get("rationale", ""),
                "keywords": r.get("keywords", []) or [],
            })
        return {"requirements": cleaned}
    except Exception as e:
        logger.error(f"LLM parse_regulation_requirements failed: {e}")
        return {"requirements": [], "error": str(e)}


async def analyze_test_procedure(control: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a control's test procedure for coverage gaps against the control
    description/risk. Returns:
      {adequacy_score, adequate, gaps, evidence_requirements[], suggested_improvement}
    """
    system_message = (
        "You are a senior IT audit manager reviewing the test script for a control. "
        "Be rigorous. Flag any step that is vague, unverifiable, unsampled, or misses a "
        "risk sub-aspect. Respond ONLY with valid JSON."
    )

    prompt = f"""Evaluate the adequacy of this control's test procedure against the control's stated purpose and the evidence that would be required.

CONTROL:
- Control ID: {control.get('control_id', 'N/A')}
- Name: {control.get('name', '')}
- Description / Risk: {control.get('description', '')}
- Domain: {control.get('domain', '')}
- Type / Category: {control.get('type', '')} / {control.get('category', '')}
- Frameworks: {', '.join(control.get('frameworks', []) or [])}

CURRENT TEST PROCEDURE:
{control.get('test_procedure', '(none provided)')}

Respond with JSON in EXACTLY this schema:
{{
  "adequacy_score": 0-100,
  "adequate": true | false,
  "gaps": ["specific gap 1", "gap 2", ...],
  "evidence_requirements": [
    {{"item": "what to obtain", "why": "why it matters", "type": "screenshot|log|report|policy|config|other"}}
  ],
  "suggested_improvement": "rewritten test procedure in precise, verifiable, mandatory language",
  "reasoning": "2-3 sentence justification of the score"
}}"""

    try:
        response = await _call_gemini(system_message, prompt)
        result = _extract_json(response)
        result.setdefault("adequacy_score", 0)
        result.setdefault("adequate", False)
        result.setdefault("gaps", [])
        result.setdefault("evidence_requirements", [])
        result.setdefault("suggested_improvement", control.get("test_procedure", ""))
        result.setdefault("reasoning", "")
        return result
    except Exception as e:
        logger.error(f"LLM analyze_test_procedure failed: {e}")
        return {
            "adequacy_score": 0,
            "adequate": False,
            "gaps": [f"LLM analysis failed: {str(e)}"],
            "evidence_requirements": [],
            "suggested_improvement": control.get("test_procedure", ""),
            "reasoning": "",
            "error": str(e),
        }


async def extract_controls_from_text(text: str, source_hint: str = "") -> Dict[str, Any]:
    """Extract structured controls from unstructured text (e.g. a PDF control register
    or regulation document). Returns {"controls": [{control_id, name, description, domain,
    owner, type, category, test_procedure, frameworks}]}.
    """
    system_message = (
        "You are an expert technology risk analyst. Extract distinct internal controls "
        "from the provided text. Be precise. Deduplicate. If a section describes a risk, "
        "infer the matching preventive/detective control. Respond ONLY with valid JSON."
    )

    prompt = f"""Extract controls from this text.
Source hint: {source_hint or 'PDF / unstructured document'}

TEXT:
\"\"\"
{text[:15000]}
\"\"\"

Return JSON in EXACTLY this schema:
{{
  "controls": [
    {{
      "control_id": "CTRL-### or document-derived id",
      "name": "<=80 char control name",
      "description": "mandatory-language description of the control",
      "domain": "Access Control | Data Protection | Vendor Risk | Incident Mgmt | Change Mgmt | Third Party | Business Continuity | AI Governance | Other",
      "owner": "role or function responsible, if stated (else empty string)",
      "type": "TECHNICAL | ADMINISTRATIVE | PHYSICAL",
      "category": "PREVENTIVE | DETECTIVE | CORRECTIVE",
      "test_procedure": "verifiable step-by-step test procedure",
      "frameworks": ["list of regulations/frameworks the control satisfies"]
    }}
  ]
}}"""

    try:
        response = await _call_gemini(system_message, prompt)
        result = _extract_json(response)
        controls = result.get("controls") or []
        cleaned = []
        for i, c in enumerate(controls[:200], start=1):
            cleaned.append({
                "control_id": c.get("control_id") or f"CTRL-PDF-{i:03d}",
                "name": c.get("name", "")[:200],
                "description": c.get("description", ""),
                "domain": c.get("domain", "Other"),
                "owner": c.get("owner", ""),
                "type": c.get("type", "ADMINISTRATIVE"),
                "category": c.get("category", "PREVENTIVE"),
                "test_procedure": c.get("test_procedure", ""),
                "frameworks": c.get("frameworks", []) or [],
            })
        return {"controls": cleaned}
    except Exception as e:
        logger.error(f"LLM extract_controls_from_text failed: {e}")
        return {"controls": [], "error": str(e)}