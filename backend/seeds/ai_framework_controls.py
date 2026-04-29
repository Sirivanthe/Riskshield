# AI Framework Controls — seed data
# Loaded once on startup into MongoDB (ai_framework_controls collection)
# Admins can add/edit/delete via API — this is the baseline set
#
# risk_category_filter: list of risk categories this control applies to
#   ["ALL"] = applies to every system regardless of risk
#   ["HIGH", "UNACCEPTABLE"] = only strict-risk systems
#   ["MINIMAL", "LIMITED", "HIGH", "UNACCEPTABLE"] = explicit full list
#
# version: which version of the regulation this control maps to
# effective_date: when this article/requirement came into force

AI_FRAMEWORK_CONTROLS = [

    # ══════════════════════════════════════════════════════════════════
    # EU AI ACT  (Regulation 2024/1689 — in force 1 Aug 2024)
    # ══════════════════════════════════════════════════════════════════

    # ── Article 5 — Prohibited AI Practices ──
    {
        "id": "EU-AI-001",
        "framework": "EU_AI_ACT",
        "name": "Prohibited AI Practices Check",
        "category": "Risk Classification",
        "article": "Article 5",
        "requirement": "Article 5 — Prohibition of certain AI practices (subliminal manipulation, social scoring, real-time biometric surveillance in public spaces, exploitation of vulnerabilities)",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": [
            "Prohibited use case screening documentation",
            "Legal sign-off confirming system does not fall under Article 5",
            "Use-case exclusion checklist"
        ],
        "guidance": "Before deployment, confirm the system does not perform subliminal manipulation, exploit vulnerabilities of individuals, conduct social scoring of natural persons, or perform real-time remote biometric identification in public spaces (unless specific law enforcement exceptions apply).",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["prohibited", "pre-deployment"]
    },

    # ── Article 6 — Risk Classification ──
    {
        "id": "EU-AI-002",
        "framework": "EU_AI_ACT",
        "name": "High-Risk Classification Assessment",
        "category": "Risk Classification",
        "article": "Article 6",
        "requirement": "Article 6 — Classification rules for high-risk AI systems (Annex I & III use cases)",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": [
            "Risk classification documentation",
            "Annex I / Annex III use case mapping",
            "Fundamental rights impact assessment (where applicable)",
            "Legal counsel sign-off"
        ],
        "guidance": "Determine if the AI system falls under Annex I (product safety legislation) or Annex III (high-risk categories including credit scoring, employment, education, law enforcement, migration). Document the classification rationale. Credit scoring models are explicitly listed under Annex III point 5(b).",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["classification", "annex-iii"]
    },

    # ── Article 9 — Risk Management ──
    {
        "id": "EU-AI-003",
        "framework": "EU_AI_ACT",
        "name": "Risk Management System",
        "category": "Risk Management",
        "article": "Article 9",
        "requirement": "Article 9 — Establish and maintain a risk management system throughout the AI system lifecycle",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Risk management policy for AI",
            "Risk register with identified risks",
            "Risk mitigation plans and residual risk acceptance",
            "Periodic review records"
        ],
        "guidance": "Implement continuous risk identification, analysis, evaluation, and mitigation. The risk management system must be iterative and updated throughout the AI system lifecycle. Residual risks must be communicated to deployers.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["risk-management", "lifecycle"]
    },

    # ── Article 10 — Data Governance ──
    {
        "id": "EU-AI-004",
        "framework": "EU_AI_ACT",
        "name": "Data Governance Framework",
        "category": "Data Governance",
        "article": "Article 10",
        "requirement": "Article 10 — Data and data governance: training, validation, and testing data requirements",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Data quality assessment report",
            "Training/validation/test dataset documentation",
            "Data provenance and lineage records",
            "Bias and representativeness analysis",
            "Data governance policy"
        ],
        "guidance": "Training, validation, and testing datasets must be relevant, representative, free of errors, and complete. Document data collection methodology, labelling processes, and data cleaning steps. Datasets must be examined for possible biases that could affect fundamental rights.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["data", "bias", "quality"]
    },

    # ── Article 11 — Technical Documentation ──
    {
        "id": "EU-AI-005",
        "framework": "EU_AI_ACT",
        "name": "Technical Documentation (Annex IV)",
        "category": "Documentation",
        "article": "Article 11",
        "requirement": "Article 11 — Technical documentation as per Annex IV must be drawn up and kept up to date",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "General system description and intended purpose",
            "Algorithm and model architecture documentation",
            "Training methodology and hyperparameters",
            "Validation and testing results",
            "Known limitations and foreseeable misuse",
            "Annex IV checklist completion"
        ],
        "guidance": "Maintain comprehensive technical documentation covering: general description, elements and development process, information on monitoring/functioning/control, description of the risk management system, and changes made throughout lifecycle. Must be available to market surveillance authorities on request.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["documentation", "annex-iv"]
    },

    # ── Article 12 — Record Keeping ──
    {
        "id": "EU-AI-006",
        "framework": "EU_AI_ACT",
        "name": "Automatic Event Logging",
        "category": "Logging",
        "article": "Article 12",
        "requirement": "Article 12 — Record-keeping: automatic logging of events throughout the operational lifetime",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Audit log samples (minimum 90 days)",
            "Decision logs with input/output records",
            "Performance degradation alerts",
            "Log retention and access control policy"
        ],
        "guidance": "High-risk AI systems must automatically log events sufficient to ensure traceability of results throughout their operational lifetime. Logs must be kept for at least the period expected by the intended purpose or 6 months minimum.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["logging", "audit-trail"]
    },

    # ── Article 13 — Transparency ──
    {
        "id": "EU-AI-007",
        "framework": "EU_AI_ACT",
        "name": "Transparency and User Information",
        "category": "Transparency",
        "article": "Article 13",
        "requirement": "Article 13 — Transparency and provision of information to deployers",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Instructions for use document (Annex IV point 2(d))",
            "Capability and limitation disclosure",
            "Expected level of accuracy and robustness metrics",
            "Human oversight guidance for deployers"
        ],
        "guidance": "High-risk AI systems must be accompanied by instructions for use in an appropriate digital format. Instructions must include: identity of provider, system capabilities and limitations, performance metrics, foreseeable misuse, human oversight measures, and expected lifetime.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["transparency", "user-information"]
    },

    # ── Article 13(3)(b) — Deployer Transparency (credit decisions) ──
    {
        "id": "EU-AI-008",
        "framework": "EU_AI_ACT",
        "name": "Natural Person Notification (AI Decision)",
        "category": "Transparency",
        "article": "Article 13(3)(b)",
        "requirement": "Article 13(3)(b) — Where AI makes decisions affecting natural persons, individuals must be notified they are subject to an AI decision",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Customer disclosure statement",
            "AI decision notification process documentation",
            "Sample notification (letter/email/app screen)",
            "Right-to-explanation procedure"
        ],
        "guidance": "For credit scoring and similar applications: customers must be informed when a consequential decision about them is made using AI. They must be able to obtain an explanation of the decision logic and contest automated decisions. Links to GDPR Article 22 obligations.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["transparency", "gdpr", "credit", "explainability"]
    },

    # ── Article 14 — Human Oversight ──
    {
        "id": "EU-AI-009",
        "framework": "EU_AI_ACT",
        "name": "Human Oversight Measures",
        "category": "Human Oversight",
        "article": "Article 14",
        "requirement": "Article 14 — Human oversight: appropriate measures enabling human oversight during use period",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Human-in-the-loop process documentation",
            "Override/intervention procedure",
            "Staff training records on AI oversight",
            "Escalation protocol for AI failures"
        ],
        "guidance": "High-risk AI systems must be designed to allow natural persons to oversee their operation. The system must allow operators to interrupt, override, or stop the system. Individuals assigned oversight must have the competence, authority, and means to exercise such oversight.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["human-oversight", "override"]
    },

    # ── Article 15 — Accuracy and Robustness ──
    {
        "id": "EU-AI-010",
        "framework": "EU_AI_ACT",
        "name": "Accuracy, Robustness and Cybersecurity",
        "category": "Technical",
        "article": "Article 15",
        "requirement": "Article 15 — Accuracy, robustness, and cybersecurity requirements",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Model accuracy metrics (precision, recall, F1, AUC)",
            "Robustness / adversarial testing results",
            "Cybersecurity assessment or penetration test",
            "Resilience against errors and inconsistencies documentation"
        ],
        "guidance": "Systems must achieve appropriate levels of accuracy throughout their lifecycle. Accuracy metrics and variations must be declared in the instructions for use. Systems must be resilient against attempts to alter their use or performance by third parties.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["accuracy", "robustness", "cybersecurity"]
    },

    # ── Article 17 — Quality Management System ──
    {
        "id": "EU-AI-011",
        "framework": "EU_AI_ACT",
        "name": "Quality Management System",
        "category": "Governance",
        "article": "Article 17",
        "requirement": "Article 17 — Quality management system covering the entire AI system lifecycle",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "QMS policy document",
            "AI development and testing procedures",
            "Change management process",
            "Supplier and vendor qualification records",
            "Post-market monitoring procedures"
        ],
        "guidance": "Providers must implement a quality management system covering: compliance strategy, design and development procedures, verification and validation procedures, incident reporting, post-market monitoring, and data management practices.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["quality-management", "governance"]
    },

    # ── Article 27 — FRIA ──
    {
        "id": "EU-AI-012",
        "framework": "EU_AI_ACT",
        "name": "Fundamental Rights Impact Assessment",
        "category": "Risk Classification",
        "article": "Article 27",
        "requirement": "Article 27 — Fundamental rights impact assessment before deployment by deployers of certain high-risk AI systems",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Fundamental Rights Impact Assessment (FRIA) document",
            "Affected groups identification",
            "Mitigation measures for identified impacts",
            "DPO/Legal sign-off"
        ],
        "guidance": "Deployers of high-risk AI systems listed under Annex III (including credit scoring) must conduct a FRIA before putting the system into service. The assessment must identify the categories of natural persons affected and the impact on their fundamental rights.",
        "version": "2024/1689",
        "effective_date": "2025-08-02",
        "tags": ["fundamental-rights", "impact-assessment", "deployer"]
    },

    # ── Article 43 — Conformity Assessment ──
    {
        "id": "EU-AI-013",
        "framework": "EU_AI_ACT",
        "name": "Conformity Assessment",
        "category": "Compliance",
        "article": "Article 43",
        "requirement": "Article 43 — Conformity assessment before placing on the market or putting into service",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Conformity assessment report",
            "CE marking documentation (EU providers)",
            "Declaration of conformity",
            "Third-party audit report (where required)"
        ],
        "guidance": "Before market placement, providers must carry out conformity assessment. For most Annex III systems this can be self-assessment against Annex VI checklist. For biometric systems a notified body is required. Keep assessment updated when substantial modifications are made.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["conformity", "certification"]
    },

    # ── Article 49 — Registration ──
    {
        "id": "EU-AI-014",
        "framework": "EU_AI_ACT",
        "name": "EU Database Registration",
        "category": "Compliance",
        "article": "Article 49",
        "requirement": "Article 49 — Registration of high-risk AI systems in EU database before deployment",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "EU AI Act database registration confirmation",
            "Registration ID / reference number",
            "Submitted registration data record"
        ],
        "guidance": "Providers must register standalone high-risk AI systems in the EU database maintained by the Commission before placing them on the market. The database is publicly accessible at ai-act-database.eu.",
        "version": "2024/1689",
        "effective_date": "2025-08-02",
        "tags": ["registration", "database", "pre-deployment"]
    },

    # ── Article 50 — GPAI Transparency ──
    {
        "id": "EU-AI-015",
        "framework": "EU_AI_ACT",
        "name": "GPAI Model Obligations (if applicable)",
        "category": "Transparency",
        "article": "Article 50-51",
        "requirement": "Article 50-51 — General purpose AI model obligations where system is built on or integrates a GPAI model (e.g. GPT, Gemini, Claude)",
        "mandatory": False,
        "risk_category_filter": ["ALL"],
        "evidence_required": [
            "GPAI model identification and provider documentation",
            "GPAI provider compliance documentation (Article 53)",
            "Integration risk assessment",
            "Usage policy compliance confirmation"
        ],
        "guidance": "If the AI system is built on top of a general-purpose AI model (LLM), the deployer must verify the GPAI model provider complies with Article 53 obligations. Disclose GPAI model use in technical documentation.",
        "version": "2024/1689",
        "effective_date": "2025-08-02",
        "tags": ["gpai", "llm", "third-party"]
    },

    # ── Article 72 — Post-Market Monitoring ──
    {
        "id": "EU-AI-016",
        "framework": "EU_AI_ACT",
        "name": "Post-Market Monitoring System",
        "category": "Monitoring",
        "article": "Article 72",
        "requirement": "Article 72 — Post-market monitoring by providers of high-risk AI systems",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Post-market monitoring plan",
            "Performance KPIs and drift thresholds",
            "Model retraining triggers and records",
            "Periodic monitoring reports"
        ],
        "guidance": "Providers must actively monitor the performance of high-risk AI systems after deployment. This includes collecting and analysing data on system performance, identifying any safety risks, and taking corrective action. Monitoring plan must cover: data collection method, frequency, and metrics.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["post-market", "monitoring", "drift"]
    },

    # ── Article 73 — Incident Reporting ──
    {
        "id": "EU-AI-017",
        "framework": "EU_AI_ACT",
        "name": "Serious Incident Reporting",
        "category": "Incident Management",
        "article": "Article 73",
        "requirement": "Article 73 — Reporting of serious incidents to market surveillance authorities",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Incident classification procedure",
            "Incident reporting process to national authority",
            "Log of past incidents (if any)",
            "Incident response runbook"
        ],
        "guidance": "Providers must report serious incidents (those causing or likely to cause: death, serious health impact, significant property damage, or serious breach of fundamental rights) to the market surveillance authority immediately and in any case within 15 days.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["incident", "reporting", "regulator"]
    },

    # ── Recital 47 / Article 10 — Bias ──
    {
        "id": "EU-AI-018",
        "framework": "EU_AI_ACT",
        "name": "Bias Detection and Mitigation",
        "category": "Fairness",
        "article": "Recital 47 / Article 10",
        "requirement": "Recital 47 & Article 10(2)(f) — Bias prevention: training data examined for potential biases, mitigation measures applied",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Bias audit report (demographic parity, equalised odds, etc.)",
            "Fairness metrics by protected group",
            "Bias mitigation measures documentation",
            "Independent fairness review (recommended)"
        ],
        "guidance": "Training datasets must be examined for possible biases. Credit scoring models must not discriminate based on protected characteristics (gender, race, ethnicity, disability, etc.). Document fairness metrics and corrective actions taken. Reference RBI Circular on Fair Lending for Indian deployments.",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "tags": ["bias", "fairness", "protected-characteristics"]
    },


    # ══════════════════════════════════════════════════════════════════
    # NIST AI RMF 1.0  (January 2023)
    # Full 4-function structure: GOVERN → MAP → MEASURE → MANAGE
    # ══════════════════════════════════════════════════════════════════

    # ── GOVERN ──
    {
        "id": "NIST-GOV-001",
        "framework": "NIST_AI_RMF",
        "name": "AI Risk Management Policy",
        "category": "GOVERN",
        "article": "GOVERN 1.1",
        "requirement": "GOVERN 1.1 — Legal and regulatory requirements involving AI are understood, managed, and documented",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["AI policy document", "Regulatory mapping", "Legal review sign-off"],
        "guidance": "Establish a formal AI risk management policy that identifies applicable legal and regulatory requirements. For banking: include RBI directives, EU AI Act (if applicable), and data protection regulations.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["governance", "policy"]
    },
    {
        "id": "NIST-GOV-002",
        "framework": "NIST_AI_RMF",
        "name": "Accountability and Roles",
        "category": "GOVERN",
        "article": "GOVERN 2.1",
        "requirement": "GOVERN 2.1 — Roles and responsibilities and lines of communication related to AI risk are documented and communicated",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["RACI matrix for AI systems", "Role definitions", "Model owner designation"],
        "guidance": "Define clear accountability for AI system ownership, model validation, deployment approval, and ongoing monitoring. Include escalation paths.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["governance", "accountability"]
    },
    {
        "id": "NIST-GOV-003",
        "framework": "NIST_AI_RMF",
        "name": "Organisational Risk Culture",
        "category": "GOVERN",
        "article": "GOVERN 3.1",
        "requirement": "GOVERN 3.1 — Organisational teams are committed to a culture that considers and communicates AI risk",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["AI risk training completion records", "Awareness programme evidence", "Board/senior management briefings"],
        "guidance": "Foster an organisational culture where AI risk is treated as a first-class risk. Senior management must be briefed on material AI risks. Training must be role-appropriate.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["governance", "culture", "training"]
    },
    {
        "id": "NIST-GOV-004",
        "framework": "NIST_AI_RMF",
        "name": "Organisational Risk Tolerance for AI",
        "category": "GOVERN",
        "article": "GOVERN 4.1",
        "requirement": "GOVERN 4.1 — Organisational teams document the risk tolerance for AI systems",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["AI risk appetite statement", "Risk tolerance thresholds", "Board approval of AI risk appetite"],
        "guidance": "Define and document acceptable risk levels for AI systems. Distinguish between acceptable automation of low-stakes decisions vs. human-required oversight for high-stakes decisions such as credit refusals.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["governance", "risk-appetite"]
    },
    {
        "id": "NIST-GOV-005",
        "framework": "NIST_AI_RMF",
        "name": "AI Policies and Procedures (Workforce)",
        "category": "GOVERN",
        "article": "GOVERN 5.1",
        "requirement": "GOVERN 5.1 — Organisational policies and practices are in place to address AI risks for workforce",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["AI acceptable use policy", "Workforce AI guidelines", "HR policy updates for AI use"],
        "guidance": "Policies must address appropriate and inappropriate uses of AI by staff, confidentiality obligations when using third-party AI tools, and procedures for raising concerns about AI outputs.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["governance", "workforce", "policy"]
    },

    # ── MAP ──
    {
        "id": "NIST-MAP-001",
        "framework": "NIST_AI_RMF",
        "name": "AI System Context Documentation",
        "category": "MAP",
        "article": "MAP 1.1",
        "requirement": "MAP 1.1 — Context is established for the AI system's risks through the system's intended purpose and deployment context",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["System purpose statement", "Use case documentation", "Deployment environment description"],
        "guidance": "Document the AI system's intended context: what problem it solves, who operates it, who is affected by its outputs, and in what environment it will run.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["map", "context"]
    },
    {
        "id": "NIST-MAP-002",
        "framework": "NIST_AI_RMF",
        "name": "Affected Communities Impact Analysis",
        "category": "MAP",
        "article": "MAP 1.5 / MAP 3.5",
        "requirement": "MAP 1.5 / MAP 3.5 — Stakeholders identified and impacts to affected communities documented",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["Stakeholder register", "Affected groups analysis", "Community impact assessment"],
        "guidance": "Identify all stakeholders including those indirectly affected by AI decisions. For credit scoring: include declined applicants, marginalised groups, and communities with historical lending disparities.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["map", "stakeholders", "community-impact"]
    },
    {
        "id": "NIST-MAP-003",
        "framework": "NIST_AI_RMF",
        "name": "AI Risk Identification",
        "category": "MAP",
        "article": "MAP 2.1",
        "requirement": "MAP 2.1 — Scientific findings and AI risks are identified and documented",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["AI risk inventory", "Threat and failure mode analysis", "Known limitations register"],
        "guidance": "Systematically identify AI-specific risks: model drift, data poisoning, adversarial attacks, feedback loops, and emergent behaviours. Reference published failure modes for the specific AI technique used.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["map", "risk-identification"]
    },
    {
        "id": "NIST-MAP-004",
        "framework": "NIST_AI_RMF",
        "name": "Third-Party AI Risk",
        "category": "MAP",
        "article": "MAP 5.1",
        "requirement": "MAP 5.1 — Likelihood and magnitude of each risk identified in the Map function is estimated",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["Third-party AI vendor risk assessment", "Supply chain AI risk register", "Vendor AI compliance questionnaire"],
        "guidance": "For AI systems that use third-party components (pre-trained models, APIs, datasets), assess and document the risks introduced by those dependencies. Include data privacy, model quality, and supply chain risks.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["map", "third-party", "supply-chain"]
    },

    # ── MEASURE ──
    {
        "id": "NIST-MEA-001",
        "framework": "NIST_AI_RMF",
        "name": "AI Risk Metrics and Measurement",
        "category": "MEASURE",
        "article": "MEASURE 1.1",
        "requirement": "MEASURE 1.1 — Approaches and metrics for measuring AI risks are established",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["AI KRI/KPI definitions", "Measurement methodology", "Baseline metrics documentation"],
        "guidance": "Define quantitative metrics for AI risks: model accuracy degradation thresholds, bias drift alerts, decision override rates, customer complaint rates related to AI decisions.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["measure", "metrics", "kri"]
    },
    {
        "id": "NIST-MEA-002",
        "framework": "NIST_AI_RMF",
        "name": "Trustworthiness Evaluation",
        "category": "MEASURE",
        "article": "MEASURE 2.1",
        "requirement": "MEASURE 2.1 — Test, evaluation, validation, and verification (TEVV) of AI systems is conducted",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["Model validation report", "Independent testing results", "Out-of-sample performance evidence"],
        "guidance": "Conduct rigorous TEVV including: holdout dataset performance, stress testing, backtesting on historical data, and red-team adversarial testing where relevant.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["measure", "validation", "testing"]
    },
    {
        "id": "NIST-MEA-003",
        "framework": "NIST_AI_RMF",
        "name": "AI Explainability Assessment",
        "category": "MEASURE",
        "article": "MEASURE 2.5",
        "requirement": "MEASURE 2.5 — AI system to be deployed is demonstrated to be valid and reliable through explainability techniques",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": ["Explainability methodology (SHAP, LIME, etc.)", "Feature importance documentation", "Sample explanation outputs", "Explainability user testing results"],
        "guidance": "For high-impact decisions (credit approvals/refusals), the model must be able to produce human-interpretable explanations. Document the explainability approach and validate that explanations are meaningful to affected individuals.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["measure", "explainability", "xai"]
    },
    {
        "id": "NIST-MEA-004",
        "framework": "NIST_AI_RMF",
        "name": "Bias and Fairness Assessment",
        "category": "MEASURE",
        "article": "MEASURE 2.7",
        "requirement": "MEASURE 2.7 — AI system to be deployed is assessed for bias and fairness",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["Fairness metrics by demographic group", "Disparate impact analysis", "Protected characteristic testing", "Bias audit report"],
        "guidance": "Measure demographic parity, equalised odds, and calibration across protected groups. For credit scoring: analyse approval rates, interest rate distributions, and default prediction accuracy by gender, age group, and geography.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["measure", "bias", "fairness"]
    },
    {
        "id": "NIST-MEA-005",
        "framework": "NIST_AI_RMF",
        "name": "Environmental and Privacy Impact",
        "category": "MEASURE",
        "article": "MEASURE 2.9",
        "requirement": "MEASURE 2.9 — Privacy risk of the AI system is evaluated and documented",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["Privacy Impact Assessment (PIA)", "Data minimisation evidence", "Anonymisation/pseudonymisation measures"],
        "guidance": "Assess privacy risks of the AI system including: re-identification risk from model outputs, inference attacks, and training data memorisation. Link to DPDP Act 2023 (India) or GDPR obligations.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["measure", "privacy", "dpdp", "gdpr"]
    },

    # ── MANAGE ──
    {
        "id": "NIST-MAN-001",
        "framework": "NIST_AI_RMF",
        "name": "AI Risk Prioritisation and Treatment",
        "category": "MANAGE",
        "article": "MANAGE 1.1 / MANAGE 2.1",
        "requirement": "MANAGE 1.1 / 2.1 — AI risks are prioritised and treatment strategies are implemented",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["Prioritised risk treatment plan", "Risk acceptance decisions", "Implementation evidence for mitigations"],
        "guidance": "Prioritise identified AI risks by likelihood and impact. For each material risk, document the chosen treatment: accept, mitigate, transfer, or avoid. Track implementation of mitigations.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["manage", "risk-treatment"]
    },
    {
        "id": "NIST-MAN-002",
        "framework": "NIST_AI_RMF",
        "name": "AI Incident and Error Management",
        "category": "MANAGE",
        "article": "MANAGE 3.2",
        "requirement": "MANAGE 3.2 — AI risks and errors are tracked and managed",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["AI incident log", "Error tracking system", "Root cause analysis records", "Corrective action evidence"],
        "guidance": "Maintain a log of AI errors, unexpected outputs, and near-misses. Conduct root cause analysis for material incidents. Track corrective actions to closure. For credit scoring: log cases where AI decision was overridden by human reviewer and analyse patterns.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["manage", "incidents", "errors"]
    },
    {
        "id": "NIST-MAN-003",
        "framework": "NIST_AI_RMF",
        "name": "Continuous Monitoring and Model Refresh",
        "category": "MANAGE",
        "article": "MANAGE 4.1",
        "requirement": "MANAGE 4.1 — Risks identified in the MEASURE function are monitored on an ongoing basis",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": ["Monitoring dashboard or reports", "Model drift alerts configuration", "Retraining schedule", "Performance review records"],
        "guidance": "Establish continuous monitoring for model drift, data distribution shift, and performance degradation. Define thresholds that trigger model review or retraining. For credit scoring: monitor population stability index (PSI) monthly.",
        "version": "NIST AI RMF 1.0",
        "effective_date": "2023-01-26",
        "tags": ["manage", "monitoring", "drift", "psi"]
    },


    # ══════════════════════════════════════════════════════════════════
    # RBI MODEL RISK MANAGEMENT
    # RBI Master Direction on IT (2023) + Circular on Digital Lending
    # RBI Guidance Note on Model Risk Management (2023)
    # ══════════════════════════════════════════════════════════════════

    {
        "id": "RBI-MRM-001",
        "framework": "RBI_MODEL_RISK",
        "name": "Model Inventory and Classification",
        "category": "Governance",
        "article": "RBI MRM Guidance — Section 3",
        "requirement": "RBI Guidance Note on Model Risk Management — All models must be inventoried and classified by materiality",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": [
            "Model inventory register",
            "Model materiality classification (Low / Medium / High)",
            "Model owner and validator assignments"
        ],
        "guidance": "Maintain a complete inventory of all models used across the institution. Classify each model by materiality based on: financial impact, regulatory capital implications, and reputational risk. Credit scoring models are typically High materiality.",
        "version": "RBI MRM 2023",
        "effective_date": "2023-04-01",
        "tags": ["rbi", "model-risk", "inventory"]
    },
    {
        "id": "RBI-MRM-002",
        "framework": "RBI_MODEL_RISK",
        "name": "Independent Model Validation",
        "category": "Validation",
        "article": "RBI MRM Guidance — Section 5",
        "requirement": "RBI MRM — Independent validation of material models by a function separate from model development",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Independent model validation report",
            "Validator independence confirmation",
            "Validation findings and remediation tracking",
            "Board/Risk Committee approval of validation findings"
        ],
        "guidance": "Material AI/ML models must be validated by a team independent of model developers. Validation must cover: conceptual soundness, data quality, model performance, and ongoing monitoring adequacy. Validation must be repeated after significant model changes.",
        "version": "RBI MRM 2023",
        "effective_date": "2023-04-01",
        "tags": ["rbi", "model-validation", "independence"]
    },
    {
        "id": "RBI-MRM-003",
        "framework": "RBI_MODEL_RISK",
        "name": "Model Development Documentation",
        "category": "Documentation",
        "article": "RBI MRM Guidance — Section 4",
        "requirement": "RBI MRM — Comprehensive model documentation covering development, assumptions, and limitations",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": [
            "Model development document (MDD)",
            "Assumptions and limitations register",
            "Data sources and feature engineering documentation",
            "Model selection rationale"
        ],
        "guidance": "Every model must have a Model Development Document (MDD) covering: business purpose, methodology, data inputs, feature selection, model selection rationale, assumptions, known limitations, and out-of-scope uses. MDD must be updated when the model changes materially.",
        "version": "RBI MRM 2023",
        "effective_date": "2023-04-01",
        "tags": ["rbi", "documentation", "mdd"]
    },
    {
        "id": "RBI-MRM-004",
        "framework": "RBI_MODEL_RISK",
        "name": "Ongoing Model Performance Monitoring",
        "category": "Monitoring",
        "article": "RBI MRM Guidance — Section 6",
        "requirement": "RBI MRM — Ongoing monitoring of model performance including stability, discriminatory power, and calibration",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": [
            "Monthly/quarterly model monitoring reports",
            "Population Stability Index (PSI) trends",
            "Gini coefficient / AUROC trends",
            "Calibration monitoring results",
            "Remediation actions for breached thresholds"
        ],
        "guidance": "Monitor credit scoring models monthly for: Population Stability Index (PSI < 0.25 alert, > 0.25 breach), Gini coefficient stability, default rate calibration. Trigger model review when thresholds are breached. Report to risk committee quarterly.",
        "version": "RBI MRM 2023",
        "effective_date": "2023-04-01",
        "tags": ["rbi", "monitoring", "psi", "gini"]
    },
    {
        "id": "RBI-MRM-005",
        "framework": "RBI_MODEL_RISK",
        "name": "Model Governance and Approval",
        "category": "Governance",
        "article": "RBI MRM Guidance — Section 3.4",
        "requirement": "RBI MRM — Formal model approval process with Risk Committee or Board oversight for material models",
        "mandatory": True,
        "risk_category_filter": ["HIGH", "UNACCEPTABLE"],
        "evidence_required": [
            "Model Governance Committee (MGC) minutes",
            "Model approval decision record",
            "Risk Committee or Board paper",
            "Conditions of approval and outstanding actions"
        ],
        "guidance": "Material models must be approved by a Model Governance Committee before deployment. The MGC should include: CRO, Head of Model Risk, Independent Validator, and business owner. Board/Risk Committee must be informed of material model approvals.",
        "version": "RBI MRM 2023",
        "effective_date": "2023-04-01",
        "tags": ["rbi", "governance", "approval", "committee"]
    },
    {
        "id": "RBI-MRM-006",
        "framework": "RBI_MODEL_RISK",
        "name": "Fair Lending and Algorithmic Bias (RBI Digital Lending)",
        "category": "Fairness",
        "article": "RBI Digital Lending Guidelines 2022 / Fair Practices Code",
        "requirement": "RBI Digital Lending — AI/ML models used in lending must not discriminate and must be explainable to borrowers",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": [
            "Fair lending compliance certificate",
            "Bias testing across borrower segments (gender, geography, religion)",
            "Explainability statement for declined applications",
            "Customer grievance mechanism for AI decisions"
        ],
        "guidance": "RBI's Digital Lending Guidelines require: (1) AI/ML credit decisions must be explainable to borrowers on request; (2) models must not discriminate on prohibited grounds; (3) lenders must disclose use of AI in credit assessment; (4) a grievance redressal mechanism must exist for AI-driven decisions.",
        "version": "RBI DL Guidelines 2022",
        "effective_date": "2022-08-10",
        "tags": ["rbi", "digital-lending", "fair-lending", "explainability"]
    },
    {
        "id": "RBI-MRM-007",
        "framework": "RBI_MODEL_RISK",
        "name": "Model Risk Reporting to Board",
        "category": "Governance",
        "article": "RBI MRM Guidance — Section 3.5",
        "requirement": "RBI MRM — Periodic model risk reporting to senior management and Board",
        "mandatory": True,
        "risk_category_filter": ["ALL"],
        "evidence_required": [
            "Quarterly model risk report to Risk Committee",
            "Annual model risk report to Board",
            "Model risk appetite metrics vs actual",
            "Material model changes and new model approvals summary"
        ],
        "guidance": "The CRO or Head of Model Risk must report model risk metrics to the Risk Committee quarterly and to the Board annually. Reports must include: inventory summary, validation backlog, models in breach of thresholds, and emerging model risks.",
        "version": "RBI MRM 2023",
        "effective_date": "2023-04-01",
        "tags": ["rbi", "reporting", "board", "cro"]
    },
]


async def seed_ai_framework_controls():
    """
    Idempotent seed: inserts controls that don't exist yet (matched by id + framework).
    Existing controls are NOT overwritten — admin edits are preserved.
    New controls added to this file ARE inserted on next restart.
    """
    from db import db
    inserted = 0
    for control in AI_FRAMEWORK_CONTROLS:
        existing = await db.ai_framework_controls.find_one(
            {"id": control["id"], "framework": control["framework"]},
            {"_id": 0}
        )
        if not existing:
            await db.ai_framework_controls.insert_one({**control})
            inserted += 1
    if inserted:
        import logging
        logging.getLogger(__name__).info(
            f"AI framework controls seeded: {inserted} new controls added"
        )