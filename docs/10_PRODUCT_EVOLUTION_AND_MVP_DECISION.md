# CareGap-AI — Product Evolution & MVP Decision

**Document Version:** 1.0  
**Status:** Proposed Product Baseline  
**Project:** CareGap-AI  
**Primary Market:** Pakistan, with future international expansion  
**Primary Goals:** AI Engineering portfolio project and potential commercial healthcare SaaS

---

## 1. Executive Decision

CareGap-AI will remain a modular healthcare intelligence platform. The original product vision will be preserved, while implementation will proceed through focused, testable releases.

The first release will prioritize a complete hospital follow-up workflow rather than attempting to implement every planned feature simultaneously.

The initial differentiating hypothesis is:

> CareGap-AI transforms discharge instructions and available healthcare records into evidence-linked follow-up requirements, highlights uncertainty and missing information, and enables healthcare staff to review and track those requirements through an auditable workflow.

This is a product hypothesis, not a claim that no competitor offers similar functionality. Competitor research and customer discovery must validate the opportunity before commercial positioning is finalized.

## 2. Product Vision

CareGap-AI aims to help healthcare teams identify, review and manage gaps between documented care plans and recorded follow-up activity.

The platform will eventually support two major modes:

1. **Hospital Intelligence Mode:** Care-gap review, follow-up management, readmission-risk estimation, explainable ML, analytics and a grounded AI copilot.
2. **Personal Health Mode:** Patient-controlled health documents, medical timelines, report explanations, reminders, appointment preparation and permission-based sharing.

Both modes will use shared infrastructure where appropriate, while maintaining strict access boundaries between hospital-managed data and personal health records.

## 3. Product Release Strategy

### Phase 0 — Foundation

Establish the technical foundation before implementing advanced AI functionality.

Scope:
- Repository and development environment.
- React, TypeScript and Vite frontend.
- Python and FastAPI backend.
- PostgreSQL database and database migrations.
- Authentication, roles and authorization.
- Configuration and secrets management.
- Automated testing and development documentation.
- Synthetic demo data and a basic CI workflow.

**Exit criteria:** The application starts reliably, the frontend communicates with the backend, database migrations work, and automated tests verify basic authentication and access-control behavior.

### Phase 1 — CareGap-AI MVP: Follow-up Intelligence

Build one complete workflow from document ingestion to reviewed follow-up tasks.

Scope:
- Upload authorized documents or synthetic sample documents.
- Extract follow-up requirements from supported document types.
- Preserve source-document references and relevant evidence spans.
- Record extraction confidence and uncertainty.
- Allow authorized staff to review, correct, approve or reject extracted requirements.
- Compare documented requirements with available follow-up records.
- Use explicit statuses such as `pending_review`, `pending`, `confirmed`, `overdue` and `unable_to_verify`.
- Create, assign and update follow-up tasks.
- Maintain audit events for relevant actions.
- Provide a dashboard showing review queues, task statuses and outstanding items.

An `overdue` status must require a documented deadline and an appropriate rule for determining whether the requirement remains outstanding. Missing records alone must never establish that a patient missed care.

**Exit criteria:**
- A supported sample document can be uploaded and processed.
- Every extracted requirement links back to its source evidence.
- Low-confidence and conflicting extractions are routed to human review.
- Staff can correct extraction errors and manage follow-up tasks.
- Unauthorized users cannot access restricted records.
- Important actions are auditable.
- Automated tests cover the main workflow and relevant failure cases.

### Phase 1.1 — Hospital Intelligence Expansion

Expand the MVP using the original hospital-intelligence requirements.

Potential scope:
- Care-gap prioritization.
- Hospital dashboards and analytics.
- A readmission-risk baseline model using an appropriately sourced dataset.
- Model evaluation, calibration and explainability.
- A grounded AI copilot that answers questions using authorized records.
- Model limitations and data-quality indicators.

Readmission prediction will be introduced only after the dataset, prediction target, evaluation methodology and limitations have been documented. It must not be represented as clinically validated merely because it achieves a promising offline score.

**Exit criteria:** Each added capability has defined acceptance criteria, tests, documented limitations and a clear separation between predictive outputs and verified clinical facts.

### Phase 2.0 — Personal Health Mode

Introduce patient-facing features after the hospital workflow and security foundation are sufficiently stable.

Potential scope:
- Personal medical-document vault.
- Personal health timeline.
- AI-assisted document explanations with source references.
- Appointment preparation and questions for clinicians.
- Medication and follow-up reminders based on verified user-provided or documented instructions.
- Exportable health summaries.
- Explicit, scoped sharing of selected records.
- Access history and revocation of sharing permissions where supported.

Personal Health Mode must not automatically expose personal records to hospital staff. Sharing must require explicit authorization and be limited to the permitted records and actions.

### Later Releases — Advanced Intelligence

Potential future capabilities:
- Additional document formats and language support.
- More sophisticated clinical NLP.
- Model monitoring and drift detection.
- Interoperability with external systems where access and standards permit.
- Additional organization and deployment options.
- Carefully validated analytics and workflow automation.

These are future possibilities, not commitments for the first release.

## 4. Initial Target Users

### Primary user

A healthcare team member responsible for reviewing discharge instructions and coordinating documented follow-up requirements.

### Secondary users

- Clinical or administrative supervisors.
- Authorized healthcare data reviewers.
- Hospital IT administrators.

### Future users

- Individuals managing personal health documents.
- Caregivers explicitly authorized by the individual.
- Healthcare providers receiving consent-based shared summaries.

Initial customer discovery should focus on a narrow workflow and a specific type of clinic or hospital rather than assuming every healthcare organization has the same needs.

## 5. Product Differentiation Hypotheses

CareGap-AI will investigate whether it can create measurable value through:

1. **Evidence-linked extraction:** Users can trace extracted requirements to the source document.
2. **Explicit uncertainty:** Missing, contradictory or low-confidence information is visible rather than silently guessed.
3. **Reconciliation:** Documented follow-up requirements can be compared with available task and appointment records.
4. **Human-reviewed actions:** AI suggestions do not independently establish clinical facts or execute clinical decisions.
5. **Auditable workflows:** Corrections, assignments and status changes can be traced.
6. **Pakistan-first document evaluation:** English and Urdu documents can be evaluated using a representative, appropriately sourced test set.

These are hypotheses to test against existing products and user workflows. They must not be marketed as unique or superior until evidence supports those claims.

## 6. Explicit MVP Non-Goals

The first release will not attempt to deliver:

- A complete hospital-management or electronic medical record replacement.
- A fully featured personal health app.
- Autonomous diagnosis or treatment recommendations.
- Autonomous medication changes.
- Unreviewed clinical decision-making.
- Claims of clinical safety or effectiveness without appropriate validation.
- Universal integration with every hospital system.
- Production handling of real patient data before appropriate security, privacy, legal and operational requirements are addressed.
- A readmission model presented as production-ready without adequate validation.

The MVP will use synthetic data for public demonstrations and appropriately sourced datasets for offline model development. Any real-data pilot requires separate authorization and safeguards.

## 7. Technical Architecture Principles

The system will begin as a modular monolith with clearly separated responsibilities.

Core components:
- Frontend application.
- FastAPI backend.
- PostgreSQL persistence.
- Authentication and authorization services.
- Document ingestion and processing.
- Follow-up reconciliation and task management.
- AI/ML service layer.
- Audit logging.
- Automated testing and deployment configuration.

The design should allow later modules to reuse stable services without requiring an unnecessary microservices architecture.

Database migrations, API contracts and security boundaries must be maintained as the product evolves. PostgreSQL row-level security may provide an additional safeguard where properly configured and tested, but it does not replace application-level authorization.

## 8. Security and Safety Requirements

- Apply least-privilege access and verify authorization on every protected operation.
- Keep personal health records separate from hospital records unless explicit, scoped sharing is authorized.
- Avoid logging sensitive medical-document contents or credentials.
- Store secrets in environment configuration rather than source control.
- Validate uploaded file types, sizes and processing paths.
- Record source references for extracted information.
- Distinguish source facts, AI-generated interpretations and unverified information.
- Route uncertain or conflicting extractions to human review.
- Do not infer missed care solely from missing records.
- Provide appropriate limitations and escalation guidance for medical questions.
- Define retention, deletion, backup and access-review procedures before handling real patient data.

## 9. Validation and Success Metrics

Before committing to a commercial positioning, investigate:

### Customer discovery
- Interview approximately 8–12 relevant healthcare professionals or administrators.
- Ask how follow-up requirements are recorded, assigned and verified today.
- Identify existing tools, manual workarounds and the consequences of workflow failures.
- Determine whether the problem is frequent and important enough to justify another software tool.

### Technical evaluation
- Measure extraction precision, recall and error patterns on a labeled test set.
- Evaluate source-reference correctness.
- Measure human correction rates and review time.
- Test reconciliation behavior for missing and conflicting records.
- Test role isolation and unauthorized-access attempts.
- Measure end-to-end workflow completion and reliability.

### Commercial evaluation
- Identify the buyer, end user and procurement constraints.
- Test willingness to run a pilot.
- Establish a baseline before claiming time savings or improved outcomes.
- Seek evidence of willingness to pay before investing in broad commercial deployment.

No clinical outcome improvement or commercial demand should be claimed without supporting evidence.

## 10. Documentation Governance

The existing nine documents remain the project's initial documentation baseline:

1. `01_PRODUCT_REQUIREMENTS.md`
2. `02_SYSTEM_ARCHITECTURE.md`
3. `03_DATABASE_DESIGN.md`
4. `04_API_SPECIFICATION.md`
5. `05_AI_ML_DESIGN.md`
6. `06_SECURITY_AND_PRIVACY.md`
7. `07_TESTING_STRATEGY.md`
8. `08_DEVELOPMENT_ROADMAP.md`
9. `09_SETUP_AND_DEPLOYMENT.md`

This document supplements those files; it does not replace them.

When implementation decisions change, update the relevant documents rather than allowing conflicting requirements to accumulate. Changes to scope, database design, API contracts or security boundaries should be documented before they are implemented.

## 11. Immediate Next Steps

1. Inspect the existing project directory and confirm which application files, if any, already exist.
2. Review the existing architecture, database and API documents against this release strategy.
3. Record necessary changes in the relevant documents.
4. Establish the repository and development environment.
5. Implement the first end-to-end follow-up workflow using synthetic documents.
6. Add automated tests and validate the workflow.
7. Conduct customer discovery and competitor validation in parallel.
8. Decide which additional hospital-intelligence capabilities belong in the next release based on evidence.

## Final Decision

CareGap-AI remains a long-term healthcare intelligence platform. The immediate build will focus on a narrow, evidence-linked discharge-to-follow-up workflow that can be demonstrated, tested and evaluated end to end.

The broader hospital-intelligence vision remains in scope for later releases, and Personal Health Mode remains a planned expansion subject to architecture, privacy and user validation.

The project will prioritize demonstrated technical reliability and validated user needs over feature count.