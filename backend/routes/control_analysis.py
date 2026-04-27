# Control Analysis API Routes
# Endpoints for control register ingestion, quality analysis, regulatory mapping,
# evidence evaluation, 5W1H narratives and audit workpaper generation.

import io
import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.control_analysis_service import ControlAnalysisService
from services.workpaper_generator import WorkpaperGenerator
from services import llm_evaluator

logger = logging.getLogger(__name__)
api_router = APIRouter()


class UpdateControlRequest(BaseModel):
    updates: Dict[str, Any]


class RegulationMapRequest(BaseModel):
    regulation_content: str
    framework_name: str


class EvaluateTextRequest(BaseModel):
    control_id: str
    evidence_text: str
    evidence_filename: Optional[str] = None
    uploaded_by: Optional[str] = None


class CreateControlRequest(BaseModel):
    control_id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    domain: Optional[str] = "General"
    owner: Optional[str] = ""
    type: Optional[str] = "ADMINISTRATIVE"
    category: Optional[str] = "PREVENTIVE"
    test_procedure: Optional[str] = ""
    frameworks: Optional[List[str]] = None
    source: Optional[str] = "MANUAL"
    source_file: Optional[str] = None
    regulatory_references: Optional[List[str]] = None
    requirement_id: Optional[str] = None
    requirement_text: Optional[str] = None


class WorkpaperRequest(BaseModel):
    control_ids: Optional[List[str]] = None


# -------- Ingestion --------
@api_router.post("/controls/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    tenant_id: str = Query("default"),
):
    """Import controls from CSV file."""
    try:
        content = await file.read()
        service = ControlAnalysisService(tenant_id=tenant_id)
        return await service.import_from_csv(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"CSV import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/controls/import/excel")
async def import_excel(
    file: UploadFile = File(...),
    tenant_id: str = Query("default"),
):
    """Import controls from Excel file."""
    try:
        content = await file.read()
        service = ControlAnalysisService(tenant_id=tenant_id)
        return await service.import_from_excel(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Excel import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/controls/import/pdf")
async def import_pdf(
    file: UploadFile = File(...),
    tenant_id: str = Query("default"),
):
    """Extract controls from a PDF using the LLM and import them."""
    try:
        content = await file.read()
        service = ControlAnalysisService(tenant_id=tenant_id)
        return await service.import_from_pdf(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"PDF import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/controls/import/servicenow")
async def import_servicenow(tenant_id: str = Query("default")):
    """Import controls from ServiceNow (mock)."""
    service = ControlAnalysisService(tenant_id=tenant_id)
    return await service.import_from_servicenow()


# -------- Register --------
@api_router.get("/controls")
async def list_controls(
    domain: Optional[str] = None,
    framework: Optional[str] = None,
    effectiveness: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant_id: str = Query("default"),
):
    service = ControlAnalysisService(tenant_id=tenant_id)
    return await service.get_controls(domain, framework, effectiveness, limit, offset)


@api_router.get("/controls/{control_id}")
async def get_control(control_id: str, tenant_id: str = Query("default")):
    service = ControlAnalysisService(tenant_id=tenant_id)
    control = await service.get_control(control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    # Enrich with strength + obligations
    obligations = await service.get_obligations_for_control(control)
    similar = await service.find_similar_controls(control_id)
    control["strength_score"] = round(service._compute_strength_score(control), 1)
    return {
        "control": control,
        "obligations": obligations,
        "similar_controls": similar,
    }


@api_router.get("/controls/{control_id}/obligations")
async def get_control_obligations(control_id: str, tenant_id: str = Query("default")):
    service = ControlAnalysisService(tenant_id=tenant_id)
    control = await service.get_control(control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    obligations = await service.get_obligations_for_control(control)
    return {"total": len(obligations), "obligations": obligations}


@api_router.get("/controls/{control_id}/similar")
async def get_control_similar(control_id: str, tenant_id: str = Query("default"), threshold: float = 0.45):
    service = ControlAnalysisService(tenant_id=tenant_id)
    similar = await service.find_similar_controls(control_id, threshold)
    return {"total": len(similar), "similar": similar}


@api_router.post("/controls")
async def create_control(
    request: CreateControlRequest,
    tenant_id: str = Query("default"),
):
    """Create a single control in the register (used by Regulatory Analysis
    to turn a gap into a draft control). When the control originates from a
    regulatory gap it is also mirrored into the central Controls Library
    (``db.custom_controls``) so it appears there tagged with the source
    framework and requirement ID."""
    import uuid
    from datetime import datetime, timezone
    from db import db

    control = {
        "id": str(uuid.uuid4()),
        "control_id": request.control_id or f"CTRL-{uuid.uuid4().hex[:8].upper()}",
        "name": request.name,
        "description": request.description or "",
        "domain": request.domain or "General",
        "owner": request.owner or "",
        "type": request.type or "ADMINISTRATIVE",
        "category": request.category or "PREVENTIVE",
        "test_procedure": request.test_procedure or "",
        "frameworks": request.frameworks or [],
        "effectiveness": "NOT_TESTED",
        "source": request.source or "MANUAL",
        "source_file": request.source_file,
        "regulatory_references": request.regulatory_references or (
            [request.requirement_id] if request.requirement_id else []
        ),
        "requirement_id": request.requirement_id,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "tenant_id": tenant_id,
    }
    await db.control_register.insert_one(control.copy())
    control.pop("_id", None)

    # Mirror into the Controls Library so auditors can see gap-sourced
    # controls alongside the rest of the library, tagged with the regulation.
    mirrored_library_control = None
    if (request.source or "").upper() == "REGULATORY_GAP":
        try:
            # Map to the ControlCategory enum used by the Controls Library
            # ({TECHNICAL, ADMINISTRATIVE, PHYSICAL, OPERATIONAL, AI_*}).
            # The incoming `type` is already one of these, whereas `category`
            # on the register carries PREVENTIVE/DETECTIVE/CORRECTIVE which
            # the library does not accept.
            valid_lib_cats = {
                "TECHNICAL", "ADMINISTRATIVE", "PHYSICAL", "OPERATIONAL",
                "AI_GOVERNANCE", "AI_TECHNICAL", "AI_OPERATIONAL",
            }
            raw_cat = (request.type or "ADMINISTRATIVE").upper()
            library_category = raw_cat if raw_cat in valid_lib_cats else "ADMINISTRATIVE"

            library_doc = {
                "id": str(uuid.uuid4()),
                "control_id": control["control_id"],
                "name": request.name,
                "description": request.description or request.requirement_text or "",
                "category": library_category,
                "frameworks": control["frameworks"],
                "regulatory_references": control["regulatory_references"],
                "implementation_guidance": (
                    f"Draft control created from regulatory gap in "
                    f"{request.source_file or 'uploaded regulation'}. "
                    "Refine the implementation guidance before approval."
                ),
                "testing_procedure": request.test_procedure or "",
                "evidence_requirements": [],
                "frequency": "Annual",
                "owner": request.owner or "",
                "status": "DRAFT",
                "created_by": "regulatory-analysis",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "effectiveness": "NOT_TESTED",
                "is_ai_control": False,
                "source": "REGULATORY_GAP",
                "source_file": request.source_file,
            }
            await db.custom_controls.insert_one(library_doc.copy())
            library_doc.pop("_id", None)
            mirrored_library_control = library_doc
        except Exception as e:
            logger.warning(f"Failed to mirror control into Controls Library: {e}")

    if mirrored_library_control:
        control["library_mirror"] = {
            "id": mirrored_library_control["id"],
            "control_id": mirrored_library_control["control_id"],
        }
    return control


@api_router.put("/controls/{control_id}")
async def update_control(
    control_id: str,
    request: UpdateControlRequest,
    tenant_id: str = Query("default"),
):
    service = ControlAnalysisService(tenant_id=tenant_id)
    result = await service.update_control(control_id, request.updates)
    if not result:
        raise HTTPException(status_code=404, detail="Control not found")
    return result


@api_router.delete("/controls/{control_id}")
async def delete_control(control_id: str, tenant_id: str = Query("default")):
    service = ControlAnalysisService(tenant_id=tenant_id)
    ok = await service.delete_control(control_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Control not found")
    return {"deleted": True, "control_id": control_id}


# -------- Quality / Coverage / Duplicates --------
@api_router.get("/quality")
async def quality(tenant_id: str = Query("default")):
    service = ControlAnalysisService(tenant_id=tenant_id)
    metrics = await service.analyze_control_quality()
    return asdict(metrics) if hasattr(metrics, "__dataclass_fields__") else metrics


@api_router.get("/duplicates")
async def duplicates(
    similarity_threshold: float = Query(0.8, ge=0.1, le=1.0),
    tenant_id: str = Query("default"),
):
    service = ControlAnalysisService(tenant_id=tenant_id)
    dups = await service.detect_duplicates(similarity_threshold)
    return {"total": len(dups), "duplicates": dups}


@api_router.get("/coverage")
async def coverage(tenant_id: str = Query("default")):
    service = ControlAnalysisService(tenant_id=tenant_id)
    return await service.get_domain_coverage()


# -------- Regulatory mapping --------
@api_router.get("/obligations")
async def list_obligations(
    framework: Optional[str] = None,
    tenant_id: str = Query("default"),
):
    """List all persisted regulatory obligations (from prior regulatory analysis runs)."""
    from db import db
    query: Dict[str, Any] = {"tenant_id": tenant_id}
    if framework:
        query["framework"] = framework
    obligations = await db.regulatory_obligations.find(query, {"_id": 0}).to_list(10000)
    frameworks = await db.regulatory_obligations.distinct("framework", {"tenant_id": tenant_id})
    return {
        "total": len(obligations),
        "frameworks": sorted(frameworks),
        "obligations": obligations,
    }


@api_router.post("/regulation/map")
async def map_regulation(
    request: RegulationMapRequest,
    tenant_id: str = Query("default"),
):
    service = ControlAnalysisService(tenant_id=tenant_id)
    return await service.map_to_regulation(request.regulation_content, request.framework_name)


# -------- Language uplift (LLM) --------
@api_router.post("/controls/{control_id}/uplift")
async def uplift_language(control_id: str, tenant_id: str = Query("default")):
    service = ControlAnalysisService(tenant_id=tenant_id)
    try:
        return await service.uplift_control_language(control_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@api_router.post("/controls/{control_id}/analyze-procedure")
async def analyze_procedure(control_id: str, tenant_id: str = Query("default")):
    """LLM gap-check of a single control's test procedure."""
    service = ControlAnalysisService(tenant_id=tenant_id)
    control = await service.get_control(control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    analysis = await llm_evaluator.analyze_test_procedure(control)
    return {
        "control_id": control_id,
        "control": control,
        "analysis": analysis,
    }


class AnalyzeProceduresRequest(BaseModel):
    control_ids: Optional[List[str]] = None
    domain: Optional[str] = None


@api_router.post("/procedures/analyze-batch")
async def analyze_procedures_batch(
    request: AnalyzeProceduresRequest,
    tenant_id: str = Query("default"),
):
    """Batch LLM analysis of test procedures across many controls (for RCM campaigns)."""
    import asyncio as _asyncio
    service = ControlAnalysisService(tenant_id=tenant_id)

    if request.control_ids:
        controls = []
        for cid in request.control_ids[:200]:
            c = await service.get_control(cid)
            if c:
                controls.append(c)
    else:
        query_result = await service.get_controls(domain=request.domain, limit=200)
        controls = query_result.get("controls", [])

    async def _eval(c):
        return {
            "control_id": c.get("id"),
            "control_code": c.get("control_id"),
            "name": c.get("name"),
            "analysis": await llm_evaluator.analyze_test_procedure(c),
        }

    # Run in parallel, but cap concurrency to avoid hammering the LLM provider
    sem = _asyncio.Semaphore(4)

    async def _bound(c):
        async with sem:
            return await _eval(c)

    results = await _asyncio.gather(*[_bound(c) for c in controls])
    adequate = sum(1 for r in results if r["analysis"].get("adequate"))
    avg_score = (
        sum(r["analysis"].get("adequacy_score", 0) for r in results) / len(results)
        if results else 0
    )
    return {
        "total": len(results),
        "adequate": adequate,
        "inadequate": len(results) - adequate,
        "avg_adequacy_score": round(avg_score, 2),
        "results": results,
    }


# -------- Evidence evaluation (LLM) --------
@api_router.post("/evidence/evaluate")
async def evaluate_text(
    request: EvaluateTextRequest,
    tenant_id: str = Query("default"),
):
    service = ControlAnalysisService(tenant_id=tenant_id)
    try:
        return await service.evaluate_evidence(
            request.control_id,
            request.evidence_text,
            request.evidence_filename,
            request.uploaded_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@api_router.post("/evidence/upload")
async def evaluate_upload(
    control_id: str = Form(...),
    uploaded_by: Optional[str] = Form(None),
    file: UploadFile = File(...),
    tenant_id: str = Query("default"),
):
    """Upload evidence file (text, csv, json, md, pdf-text) and evaluate it."""
    try:
        raw = await file.read()
        filename = file.filename or "evidence"
        lower = filename.lower()

        if lower.endswith(".pdf"):
            try:
                import fitz  # PyMuPDF
                text_parts: List[str] = []
                with fitz.open(stream=raw, filetype="pdf") as doc:
                    for page in doc:
                        text_parts.append(page.get_text())
                evidence_text = "\n".join(text_parts)
            except Exception as pdf_err:
                logger.error(f"PDF parse failed, falling back to raw: {pdf_err}")
                evidence_text = raw.decode("utf-8", errors="ignore")
        else:
            evidence_text = raw.decode("utf-8", errors="ignore")

        if not evidence_text.strip():
            raise HTTPException(status_code=400, detail="Evidence file appears to be empty")

        service = ControlAnalysisService(tenant_id=tenant_id)
        return await service.evaluate_evidence(
            control_id, evidence_text, filename, uploaded_by
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Evidence upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/evidence/checklist/{control_id}")
async def get_evidence_checklist(
    control_id: str,
    tenant_id: str = Query("default"),
):
    """Parse the control's test procedure and return required evidence items."""
    service = ControlAnalysisService(tenant_id=tenant_id)
    control = await service.get_control(control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    from services.llm_evaluator import analyze_test_procedure
    result = await analyze_test_procedure(control if isinstance(control, dict) else control.dict())
    
    items = []
    for i, req in enumerate(result.get("evidence_requirements", []), start=1):
        items.append({
            "id": f"EV-{i:03d}",
            "item": req.get("item", ""),
            "why": req.get("why", ""),
            "type": req.get("type", "other"),
            "status": "pending",
            "evaluation": None,
        })
    
    return {
        "control_id": control_id,
        "control_name": control.get("name", "") if isinstance(control, dict) else control.name,
        "adequacy_score": result.get("adequacy_score", 0),
        "adequate": result.get("adequate", False),
        "gaps": result.get("gaps", []),
        "evidence_items": items,
        "suggested_improvement": result.get("suggested_improvement", ""),
    }


@api_router.post("/evidence/upload-item")
async def evaluate_evidence_item(
    control_id: str = Form(...),
    item_id: str = Form(...),
    item_description: str = Form(...),
    uploaded_by: Optional[str] = Form(None),
    file: UploadFile = File(...),
    tenant_id: str = Query("default"),
):
    """Evaluate a single evidence item against its specific requirement."""
    try:
        raw = await file.read()
        filename = file.filename or "evidence"
        lower = filename.lower()
        if lower.endswith(".pdf"):
            try:
                import fitz
                text_parts = []
                with fitz.open(stream=raw, filetype="pdf") as doc:
                    for page in doc:
                        text_parts.append(page.get_text())
                evidence_text = "\n".join(text_parts)
            except Exception:
                evidence_text = raw.decode("utf-8", errors="ignore")
        else:
            evidence_text = raw.decode("utf-8", errors="ignore")

        if not evidence_text.strip():
            raise HTTPException(status_code=400, detail="Evidence file appears to be empty")

        service = ControlAnalysisService(tenant_id=tenant_id)
        control = await service.get_control(control_id)
        if not control:
            raise HTTPException(status_code=404, detail="Control not found")

        # Evaluate just this item against its specific requirement
        from services.llm_evaluator import evaluate_evidence
        control_dict = control if isinstance(control, dict) else control.dict()
        control_dict["test_procedure"] = f"Evaluate ONLY this evidence requirement: {item_description}"
        
        result = await evaluate_evidence(control_dict, evidence_text, filename)
        result["item_id"] = item_id
        result["item_description"] = item_description
        result["filename"] = filename
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/evaluations")
async def list_evaluations(
    control_id: Optional[str] = None,
    limit: int = Query(100, le=500),
    tenant_id: str = Query("default"),
):
    service = ControlAnalysisService(tenant_id=tenant_id)
    items = await service.list_evaluations(control_id, limit)
    return {"total": len(items), "evaluations": items}


@api_router.get("/evaluations/{evaluation_id}")
async def get_evaluation(evaluation_id: str, tenant_id: str = Query("default")):
    service = ControlAnalysisService(tenant_id=tenant_id)
    item = await service.get_evaluation(evaluation_id)
    if not item:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return item


@api_router.get("/controls/{control_id}/5w1h")
async def five_w_one_h(control_id: str, tenant_id: str = Query("default")):
    service = ControlAnalysisService(tenant_id=tenant_id)
    try:
        return await service.generate_5w1h_report(control_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -------- Workpapers --------
@api_router.post("/workpaper/pdf")
async def workpaper_pdf(
    request: WorkpaperRequest,
    tenant_id: str = Query("default"),
):
    service = ControlAnalysisService(tenant_id=tenant_id)
    data = await service.build_workpaper_data(request.control_ids)
    pdf_bytes = WorkpaperGenerator().generate_pdf(data)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=control_workpaper.pdf"},
    )


@api_router.post("/workpaper/excel")
async def workpaper_excel(
    request: WorkpaperRequest,
    tenant_id: str = Query("default"),
):
    service = ControlAnalysisService(tenant_id=tenant_id)
    data = await service.build_workpaper_data(request.control_ids)
    xlsx_bytes = WorkpaperGenerator().generate_excel(data)
    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=control_workpaper.xlsx"},
    )


@api_router.get("/workpaper/pdf")
async def workpaper_pdf_get(tenant_id: str = Query("default")):
    """Convenience GET for downloading the full-register PDF workpaper."""
    return await workpaper_pdf(WorkpaperRequest(control_ids=None), tenant_id)


@api_router.get("/workpaper/excel")
async def workpaper_excel_get(tenant_id: str = Query("default")):
    """Convenience GET for downloading the full-register Excel workpaper."""
    return await workpaper_excel(WorkpaperRequest(control_ids=None), tenant_id)
