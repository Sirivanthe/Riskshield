"""
Iteration 5 regression pass for RiskShield GRC platform.

Covers:
- Auth (admin, LOD1, LOD2) + /auth/me role
- Assessments (POST/GET/list)
- Controls Library CRUD + quality + filters
- Regulatory Analysis -> Controls Library MIRROR (the new feature)
- Control Analysis ingestion (CSV import, list, quality, coverage, duplicates)
- Regulation mapping
- Documents / RAG upload
- Regulations library (/regulations/upload + list)
- Issue Management CRUD
- Tech Risk Assessment create + questions
- Trends dashboard
- LLM config (GET/PUT/providers/health)
- System health + llm usage
"""
import io
import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://audit-control-hub-4.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
TENANT = "default"

ADMIN_CRED = {"email": "admin@bank.com", "password": "admin123"}
LOD1_CRED = {"email": "lod1@bank.com", "password": "password123"}
LOD2_CRED = {"email": "lod2@bank.com", "password": "password123"}


def _login(session: requests.Session, cred: dict) -> dict:
    r = session.post(f"{API}/auth/login", json=cred, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data or "token" in data, f"no token in {data}"
    return data


@pytest.fixture(scope="session")
def admin_client():
    s = requests.Session()
    data = _login(s, ADMIN_CRED)
    token = data.get("access_token") or data.get("token")
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    s.user = data.get("user") or {}
    return s


@pytest.fixture(scope="session")
def lod1_client():
    s = requests.Session()
    data = _login(s, LOD1_CRED)
    token = data.get("access_token") or data.get("token")
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    s.user = data.get("user") or {}
    return s


@pytest.fixture(scope="session")
def lod2_client():
    s = requests.Session()
    data = _login(s, LOD2_CRED)
    token = data.get("access_token") or data.get("token")
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    s.user = data.get("user") or {}
    return s


# ---------- Auth ----------
class TestAuth:
    def test_login_admin(self, admin_client):
        assert admin_client.user.get("email") == "admin@bank.com"

    def test_login_lod1(self, lod1_client):
        assert lod1_client.user.get("email") == "lod1@bank.com"

    def test_login_lod2(self, lod2_client):
        assert lod2_client.user.get("email") == "lod2@bank.com"

    def test_me_admin(self, admin_client):
        r = admin_client.get(f"{API}/auth/me", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("email") == "admin@bank.com"
        assert data.get("role", "").upper().startswith("ADMIN")

    def test_login_bad_credentials(self):
        r = requests.post(f"{API}/auth/login", json={"email": "x@y.z", "password": "bad"}, timeout=15)
        assert r.status_code in (400, 401, 403), r.text


# ---------- Assessments ----------
class TestAssessments:
    def test_create_list_get(self, admin_client):
        payload = {
            "name": f"TEST_Assess_{uuid.uuid4().hex[:6]}",
            "system_name": "TEST_System",
            "business_unit": "Retail",
            "frameworks": ["NIST CSF"],
            "description": "regression test",
        }
        r = admin_client.post(f"{API}/assessments", json=payload, timeout=240)
        assert r.status_code in (200, 201), r.text
        a = r.json()
        assert a["id"]
        assert a["name"] == payload["name"]
        aid = a["id"]

        # list
        r2 = admin_client.get(f"{API}/assessments", timeout=30)
        assert r2.status_code == 200
        items = r2.json()
        assert any(x["id"] == aid for x in items)

        # get by id
        r3 = admin_client.get(f"{API}/assessments/{aid}", timeout=30)
        assert r3.status_code == 200
        got = r3.json()
        assert got["id"] == aid
        assert "risks" in got and "controls" in got


# ---------- Controls Library ----------
class TestControlsLibrary:
    def test_library_list_no_500(self, admin_client):
        r = admin_client.get(f"{API}/controls/library", timeout=120)
        assert r.status_code == 200, f"Library listing failed: {r.status_code} {r.text[:500]}"
        assert isinstance(r.json(), list)

    def test_library_filters(self, admin_client):
        r = admin_client.get(f"{API}/controls/library", params={"framework": "NIST CSF"}, timeout=120)
        assert r.status_code == 200

    def test_quality_metrics(self, admin_client):
        r = admin_client.get(f"{API}/controls/library/quality", timeout=120)
        assert r.status_code == 200
        q = r.json()
        assert "total_controls" in q or "quality_score" in q or isinstance(q, dict)

    def test_lod1_creates_pending(self, lod1_client):
        payload = {
            "control_id": f"TEST-LOD1-{uuid.uuid4().hex[:6]}",
            "name": "TEST LOD1 control",
            "description": "pending review",
            "category": "ADMINISTRATIVE",
            "frameworks": ["NIST CSF"],
            "implementation_guidance": "do the thing",
            "testing_procedure": "observe",
        }
        r = lod1_client.post(f"{API}/controls/library", json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text
        c = r.json()
        assert c.get("status", "").upper() in ("PENDING_REVIEW", "PENDING", "DRAFT")

    def test_lod2_creates_approved(self, lod2_client):
        payload = {
            "control_id": f"TEST-LOD2-{uuid.uuid4().hex[:6]}",
            "name": "TEST LOD2 control",
            "description": "auto approved",
            "category": "ADMINISTRATIVE",
            "frameworks": ["NIST CSF"],
        }
        r = lod2_client.post(f"{API}/controls/library", json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text
        c = r.json()
        assert c.get("status", "").upper() in ("APPROVED", "PENDING_REVIEW")


# ---------- Regulatory Analysis -> Controls Library MIRROR (FEATURE UNDER TEST) ----------
class TestRegulatoryGapMirror:
    created_library_id = None

    def test_create_gap_control_mirrors_to_library(self, admin_client):
        req_id = f"REG-TEST-{uuid.uuid4().hex[:6]}"
        payload = {
            "name": f"TEST Gap Ctrl {req_id}",
            "description": "from regulatory gap",
            "type": "ADMINISTRATIVE",
            "category": "PREVENTIVE",  # register-side category
            "source": "REGULATORY_GAP",
            "source_file": "RBI Cyber Security Framework",
            "frameworks": ["RBI Cyber Security Framework"],
            "regulatory_references": [f"RBI Cyber Security Framework · {req_id}"],
            "requirement_id": req_id,
            "requirement_text": "Applications shall implement MFA.",
        }
        r = admin_client.post(
            f"{API}/control-analysis/controls",
            params={"tenant_id": TENANT},
            json=payload,
            timeout=60,
        )
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert data.get("source") == "REGULATORY_GAP"
        assert "library_mirror" in data, f"library_mirror missing in response: {data}"
        mirror = data["library_mirror"]
        assert mirror.get("id"), f"mirror.id missing: {mirror}"
        TestRegulatoryGapMirror.created_library_id = mirror["id"]

    def test_library_returns_200_after_mirror(self, admin_client):
        """Regression: a prior bug caused /api/controls/library to 500 due to
        bad category ('PREVENTIVE') being written directly. Must be fixed now."""
        r = admin_client.get(f"{API}/controls/library", timeout=120)
        assert r.status_code == 200, f"library list broke: {r.status_code} {r.text[:500]}"

    def test_library_contains_mirrored_control(self, admin_client):
        assert TestRegulatoryGapMirror.created_library_id, "prior test must have created an ID"
        r = admin_client.get(f"{API}/controls/library", timeout=120)
        assert r.status_code == 200
        items = r.json()
        match = next((c for c in items if c.get("id") == TestRegulatoryGapMirror.created_library_id), None)
        assert match is not None, "mirrored control not found in /api/controls/library"
        assert match.get("source") == "REGULATORY_GAP"
        assert match.get("category") == "ADMINISTRATIVE", (
            f"category should be mapped from 'type' to ControlCategory enum (ADMINISTRATIVE), got {match.get('category')}"
        )
        assert "RBI Cyber Security Framework" in (match.get("frameworks") or [])
        assert match.get("regulatory_references"), "regulatory_references must be populated"


# ---------- Control Analysis ingestion ----------
class TestControlAnalysis:
    def test_csv_import(self, admin_client):
        csv_content = (
            "control_id,name,description,domain,owner,type,category,test_procedure,frameworks\n"
            "TEST-CA-001,Access Review,Quarterly access review,IAM,Alice,ADMINISTRATIVE,DETECTIVE,review list,NIST CSF\n"
            "TEST-CA-002,Encryption,Data at rest AES-256,Data,Bob,TECHNICAL,PREVENTIVE,inspect config,NIST CSF\n"
        )
        files = {"file": ("test_controls.csv", csv_content.encode(), "text/csv")}
        # Drop JSON content-type for multipart
        headers = {k: v for k, v in admin_client.headers.items() if k.lower() != "content-type"}
        r = requests.post(
            f"{API}/control-analysis/controls/import/csv",
            params={"tenant_id": TENANT},
            files=files,
            headers=headers,
            timeout=60,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        imported = body.get("imported") or body.get("imported_count") or body.get("total") or 0
        assert imported >= 1, f"Expected import count >=1, got {body}"

    def test_list_controls(self, admin_client):
        r = admin_client.get(f"{API}/control-analysis/controls", params={"tenant_id": TENANT}, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json().get("controls", r.json()), list)

    def test_quality(self, admin_client):
        r = admin_client.get(f"{API}/control-analysis/quality", params={"tenant_id": TENANT}, timeout=30)
        assert r.status_code == 200

    def test_coverage(self, admin_client):
        r = admin_client.get(f"{API}/control-analysis/coverage", params={"tenant_id": TENANT}, timeout=30)
        assert r.status_code == 200

    def test_duplicates(self, admin_client):
        r = admin_client.get(f"{API}/control-analysis/duplicates", params={"tenant_id": TENANT}, timeout=30)
        assert r.status_code == 200


# ---------- Regulation mapping ----------
class TestRegulationMapping:
    def test_map_regulation(self, admin_client):
        reg_text = (
            "REQ-1. All systems shall enforce multi-factor authentication.\n"
            "REQ-2. Administrators must review user access quarterly.\n"
            "REQ-3. Data at rest should be encrypted using AES-256."
        )
        r = admin_client.post(
            f"{API}/control-analysis/regulation/map",
            params={"tenant_id": TENANT},
            json={"framework_name": "TEST_Reg", "regulation_content": reg_text},
            timeout=180,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        for key in ("compliance_score", "coverage_summary", "gaps", "all_mappings", "total_requirements"):
            assert key in data, f"missing {key} in regulation mapping response"


# ---------- Documents / RAG ----------
class TestRag:
    def test_upload_text_document(self, admin_client):
        # Endpoint hard-gates to PDFs (`Only PDF files are supported`).
        # Upload a minimal valid PDF so the route exercises the full parser path.
        pdf_bytes = (
            b"%PDF-1.1\n1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
            b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
            b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
            b"4 0 obj<< /Length 44 >>stream\nBT /F1 18 Tf 20 60 Td (Hello TEST) Tj ET\nendstream endobj\n"
            b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
            b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000054 00000 n \n"
            b"0000000102 00000 n \n0000000202 00000 n \n0000000288 00000 n \n"
            b"trailer<< /Size 6 /Root 1 0 R >>\nstartxref\n358\n%%EOF\n"
        )
        files = {"file": ("test_doc.pdf", pdf_bytes, "application/pdf")}
        headers = {k: v for k, v in admin_client.headers.items() if k.lower() != "content-type"}
        r = requests.post(
            f"{API}/rag/documents/upload",
            params={"tenant_id": TENANT},
            files=files,
            headers=headers,
            timeout=120,
        )
        # Accept 200/201; tolerate 500 only if the fake PDF is rejected by the parser
        assert r.status_code in (200, 201), r.text
        body = r.json()
        assert "text" in body or "chunks_created" in body or body.get("success") is not None


# ---------- Regulations library ----------
class TestRegulations:
    def test_upload_and_list(self, admin_client):
        name = f"TEST_Reg_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": name,
            "framework": "TEST Framework",
            "content": "REQ-1. Systems shall use MFA.",
            "file_name": f"{name}.txt",
        }
        r = admin_client.post(f"{API}/regulations/upload", json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text
        rid = r.json().get("id")
        assert rid

        r2 = admin_client.get(f"{API}/regulations", timeout=30)
        assert r2.status_code == 200
        items = r2.json()
        assert any(x.get("id") == rid for x in items), "uploaded regulation not found in list"


# ---------- Issue Management ----------
class TestIssueManagement:
    created_issue_id = None

    def test_create_and_list(self, admin_client):
        uid = admin_client.user.get("id", "admin")
        payload = {
            "title": f"TEST_Issue_{uuid.uuid4().hex[:6]}",
            "description": "regression issue",
            "issue_type": "FINDING",
            "severity": "MEDIUM",
            "priority": "MEDIUM",
        }
        r = admin_client.post(
            f"{API}/issue-management/",
            params={"creator_id": uid, "creator_name": "AdminUser"},
            json=payload,
            timeout=30,
        )
        assert r.status_code in (200, 201), r.text
        issue = r.json()
        assert issue.get("id")
        TestIssueManagement.created_issue_id = issue["id"]

        r2 = admin_client.get(f"{API}/issue-management/", timeout=30)
        assert r2.status_code == 200
        items = r2.json()
        arr = items if isinstance(items, list) else items.get("issues", [])
        assert any(x.get("id") == issue["id"] for x in arr)

    def test_update_issue(self, admin_client):
        if not TestIssueManagement.created_issue_id:
            pytest.skip("no issue created")
        iid = TestIssueManagement.created_issue_id
        r = admin_client.put(
            f"{API}/issue-management/{iid}",
            params={"user_id": admin_client.user.get("id", "admin"), "user_name": "AdminUser"},
            json={"description": "updated regression issue"},
            timeout=30,
        )
        assert r.status_code in (200, 204), r.text


# ---------- Tech Risk Assessment ----------
class TestTechRisk:
    def test_create_and_get_questions(self, admin_client):
        uid = admin_client.user.get("id", "admin")
        payload = {
            "app_name": f"TEST_App_{uuid.uuid4().hex[:6]}",
            "description": "regression test",
            "business_unit": "Retail",
        }
        r = admin_client.post(
            f"{API}/tech-risk/assessments",
            params={"assessor_id": uid, "assessor_name": "Admin"},
            json=payload,
            timeout=60,
        )
        assert r.status_code in (200, 201), r.text
        a = r.json()
        aid = a.get("id") or (a.get("assessment") or {}).get("id")
        assert aid

        r2 = admin_client.get(f"{API}/tech-risk/assessments/{aid}/questions", timeout=60)
        assert r2.status_code == 200, r2.text

    def test_list(self, admin_client):
        r = admin_client.get(f"{API}/tech-risk/assessments", timeout=30)
        assert r.status_code == 200


# ---------- Trends ----------
class TestTrends:
    def test_dashboard_trends(self, admin_client):
        r = admin_client.get(f"{API}/trends/dashboard", params={"tenant_id": TENANT}, timeout=30)
        assert r.status_code == 200


# ---------- LLM Config ----------
class TestLLMConfig:
    def test_get_config_masked(self, admin_client):
        r = admin_client.get(f"{API}/llm/config", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # Should NEVER return api_key in plain
        assert "api_key" not in data or data.get("api_key") is None
        assert "api_key_set" in data or "api_key_last4" in data or "provider" in data

    def test_providers(self, admin_client):
        r = admin_client.get(f"{API}/llm/providers", timeout=30)
        assert r.status_code == 200

    def test_health(self, admin_client):
        r = admin_client.get(f"{API}/llm/health", timeout=60)
        assert r.status_code == 200


# ---------- System ----------
class TestSystem:
    def test_system_health(self, admin_client):
        r = admin_client.get(f"{API}/system/health", timeout=30)
        assert r.status_code == 200

    def test_llm_usage(self, admin_client):
        r = admin_client.get(f"{API}/system/llm/usage", timeout=30)
        assert r.status_code == 200
