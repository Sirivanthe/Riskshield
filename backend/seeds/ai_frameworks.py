# AI Frameworks — seed data
# Loaded once on startup into MongoDB (ai_frameworks collection)
# Admins can add/edit/delete frameworks entirely from the UI.
# Adding a new framework here + adding controls in ai_framework_controls.py
# is all that's needed — zero frontend code changes required.

AI_FRAMEWORKS = [
    {
        "id": "EU_AI_ACT",
        "name": "EU AI Act",
        "short_label": "EU",
        "flag": "🇪🇺",
        "color": "#1e40af",
        "bg_color": "#eff6ff",
        "description": "European Union Artificial Intelligence Act (Regulation 2024/1689) — comprehensive binding AI regulation in force from August 2024.",
        "jurisdiction": "European Union",
        "effective_date": "2024-08-01",
        "categories": [
            "Risk Classification",
            "Transparency",
            "Human Oversight",
            "Data Governance",
            "Documentation",
            "Logging",
            "Fairness",
            "Technical",
            "Compliance",
            "Governance",
            "Monitoring",
            "Incident Management"
        ],
        "risk_categories": ["UNACCEPTABLE", "HIGH", "LIMITED", "MINIMAL"],
        "active": True
    },
    {
        "id": "NIST_AI_RMF",
        "name": "NIST AI Risk Management Framework",
        "short_label": "NIST",
        "flag": "🇺🇸",
        "color": "#0f766e",
        "bg_color": "#f0fdfa",
        "description": "NIST AI RMF 1.0 (January 2023) — voluntary framework for managing AI risks across the full AI lifecycle through GOVERN, MAP, MEASURE, and MANAGE functions.",
        "jurisdiction": "United States (voluntary, globally adopted)",
        "effective_date": "2023-01-26",
        "categories": ["GOVERN", "MAP", "MEASURE", "MANAGE"],
        "risk_categories": ["ALL"],
        "active": True
    },
    {
        "id": "RBI_MODEL_RISK",
        "name": "RBI Model Risk Management",
        "short_label": "RBI",
        "flag": "🇮🇳",
        "color": "#7c2d12",
        "bg_color": "#fff7ed",
        "description": "Reserve Bank of India Guidance Note on Model Risk Management (2023) and Digital Lending Guidelines (2022) — mandatory for Indian banks and NBFCs.",
        "jurisdiction": "India",
        "effective_date": "2023-04-01",
        "categories": ["Governance", "Validation", "Documentation", "Monitoring", "Fairness"],
        "risk_categories": ["HIGH", "UNACCEPTABLE", "LIMITED", "MINIMAL"],
        "active": True
    },
]


async def seed_ai_frameworks():
    """
    Idempotent seed: inserts frameworks that don't exist yet (matched by id).
    Existing frameworks are NOT overwritten — admin edits are preserved.
    """
    from db import db
    inserted = 0
    for fw in AI_FRAMEWORKS:
        existing = await db.ai_frameworks.find_one({"id": fw["id"]}, {"_id": 0})
        if not existing:
            await db.ai_frameworks.insert_one({**fw})
            inserted += 1
    if inserted:
        import logging
        logging.getLogger(__name__).info(f"AI frameworks seeded: {inserted} new frameworks added")