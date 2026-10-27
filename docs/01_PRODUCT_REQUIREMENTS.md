# CareGap-AI — Product Requirements Document (PRD)

**Version:** 1.0  
**Status:** Initial product specification  
**Product type:** Dual-mode healthcare SaaS  
**Primary capabilities:** AI/ML, readmission risk research, care-gap tracking, personal health records, and grounded AI assistance

---

## 1. Product Overview

CareGap-AI is a healthcare intelligence platform designed for two distinct user groups: healthcare organizations and individual patients.

The platform provides two connected but permission-separated experiences:

1. **Hospital Intelligence Mode:** Helps authorized healthcare teams review readmission-risk estimates, identify missing or conflicting care documentation, track follow-up workflows, and analyze aggregated quality metrics.
2. **Personal Health Mode:** Helps patients organize their health information, understand medical documents, manage personal follow-up reminders, prepare for appointments, and track their own care plans.

CareGap-AI combines conventional software workflows, machine-learning models, deterministic rules, and a retrieval-grounded AI assistant.

The initial release is a research and portfolio prototype using synthetic demonstration data and appropriately sourced public datasets for offline model development. It is not a clinically validated medical device or a replacement for healthcare professionals.

## 2. Problem Statement

### 2.1 Problems faced by healthcare organizations

Healthcare teams may face difficulties with:

- Reviewing large numbers of patient encounters.
- Identifying patients who may require additional follow-up.
- Finding incomplete, missing, or conflicting care documentation.
- Tracking review assignments and outstanding tasks.
- Understanding why a model assigned a particular risk estimate.
- Producing consistent quality reports.
- Accessing relevant evidence without searching multiple disconnected records.

CareGap-AI aims to organize these activities into a structured review workflow.

### 2.2 Problems faced by patients

Patients may struggle to:

- Keep medical reports and prescriptions organized.
- Remember appointments and follow-up tasks.
- Understand terminology used in medical documents.
- Prepare useful questions for their doctors.
- Maintain a personal timeline of healthcare events.
- Know which information is recorded and which details still need confirmation.
- Share selected health documents with a healthcare provider.

CareGap-AI aims to give patients a convenient, understandable, and privacy-conscious place to manage their own health information.

## 3. Product Vision

To make healthcare information easier to understand, review, and act upon by connecting hospital-level care intelligence with patient-controlled personal health management.

## 4. Target Users and Personas

### 4.1 Hospital organization administrator

Responsible for organization settings, staff access, role assignments, and operational oversight.

### 4.2 Quality analyst

Reviews aggregate readmission-related metrics, model performance, trends, and care-gap summaries.

### 4.3 Care reviewer

Reviews individual encounters, examines supporting evidence, verifies documentation gaps, and manages assigned follow-up tasks.

### 4.4 Read-only hospital viewer

Views authorized dashboards and reports without permission to modify clinical review records.

### 4.5 Individual patient

Maintains a personal health profile, organizes uploaded records, manages reminders, tracks follow-up tasks, and uses the AI assistant to understand documents.

### 4.6 Future authorized clinician

May access specifically shared patient information through an explicitly authorized workflow. This role is not assumed to have unrestricted access to the patient's personal account.

## 5. Product Modes

### 5.1 Hospital Intelligence Mode

The hospital experience focuses on reviewing information and managing operational workflows.

Core modules:

1. Hospital overview dashboard.
2. Secure data import and validation.
3. Readmission-risk research model.
4. Risk explanation and supporting factors.
5. Care-gap rule engine.
6. Encounter review worklist.
7. Review assignments and task tracking.
8. Grounded AI copilot.
9. Model evaluation and monitoring.
10. Reports, organization settings, and audit logs.

### 5.2 Personal Health Mode

The patient experience focuses on personal organization, understanding, and follow-up.

Core modules:

1. Personal health dashboard.
2. Health profile and relevant history.
3. Personal medical document vault.
4. Medical report and prescription explainer.
5. Medication list and reminder management.
6. Appointment calendar and reminders.
7. Personal care-plan checklist.
8. Follow-up tracker.
9. Health timeline.
10. Appointment preparation and questions for clinicians.
11. Selective document sharing and consent management.
12. Personal data export and account controls.

Patients enter or upload their own information. Where information is unavailable, the platform must communicate that limitation rather than inventing details.

## 6. Functional Requirements

### 6.1 Authentication and accounts

- Users must be able to register or sign in through supported authentication flows.
- The backend must identify the authenticated user for every protected request.
- Access permissions must be enforced on the server, not merely hidden in the interface.
- Hospital memberships and patient-owned resources must have separate authorization rules.
- Sensitive account actions must be auditable.
- The system must support secure logout and account recovery through the selected authentication implementation.

### 6.2 Hospital dashboard

- Display permitted aggregate statistics.
- Show encounter counts, review workload, and care-gap status summaries.
- Provide filters for supported date ranges and organizational segments.
- Clearly distinguish demonstration data from real operational data.
- Prevent users from viewing records outside their authorized organization and role.

### 6.3 Data import and validation

- Accept supported CSV files through an authenticated import workflow.
- Validate file structure, field types, required columns, and permitted values.
- Report invalid rows and explain validation failures.
- Enforce file-size and row-count limits.
- Prevent imported content from bypassing authorization or executing as code.
- Record import status and relevant audit events.
- Avoid importing direct identifiers into model-training datasets unless specifically necessary and authorized.

### 6.4 Readmission-risk model

- Produce a research-oriented estimate of readmission risk for supported encounters.
- Document the prediction target, prediction horizon, inclusion criteria, and exclusions.
- Display the model version and relevant data-quality warnings.
- Provide explanations using a supported explainability method.
- Report uncertainty and evaluation limitations.
- Support offline training, validation, testing, and reproducible evaluation.
- Never present a prototype score as a definitive clinical prediction or an autonomous treatment decision.

### 6.5 Care-gap detection

- Evaluate available encounter information against versioned, documented rules.
- Support statuses such as documented, not documented, conflicting, unknown, and not applicable.
- Show the evidence or source fields supporting each result.
- Allow authorized reviewers to verify or correct findings.
- Track assignments, review status, and resolution notes.
- Preserve a distinction between missing documentation and an actual missed clinical action.

### 6.6 Hospital AI copilot

- Answer questions using only authorized encounter information and approved supporting sources.
- Reference the evidence used to produce an answer.
- State when evidence is insufficient or contradictory.
- Avoid fabricating diagnoses, treatments, procedures, or patient history.
- Respect the user's organization and record-level permissions.
- Never execute arbitrary SQL or privileged operations based on natural-language requests.
- Treat uploaded text and retrieved documents as untrusted data.

### 6.7 Personal health profile

- Allow patients to manage basic profile details and optional health information.
- Allow patients to record relevant history and healthcare contacts.
- Show when information was entered or last updated where feasible.
- Distinguish patient-entered information from verified clinical information.
- Allow corrections and deletion according to applicable retention and legal requirements.

### 6.8 Personal document vault

- Support agreed document formats, initially PDF and common image formats.
- Store documents privately with appropriate access controls.
- Allow patients to view, organize, and remove their own documents where permitted.
- Associate documents with optional categories and dates.
- Prevent other patients from accessing a user's files.
- Avoid making uploaded documents publicly accessible through predictable URLs.
- Scan and validate uploads where supported by the implementation.

### 6.9 Patient AI document explainer

- Explain medical terminology in accessible language.
- Summarize information actually present in an uploaded document.
- Identify unclear, unreadable, or missing information.
- Distinguish document content from general educational explanations.
- Reference the document section or extracted text supporting important statements where possible.
- Encourage the patient to confirm clinically important uncertainties with an appropriate healthcare professional.
- Never independently diagnose a condition or recommend starting, stopping, or changing medication.

### 6.10 Medication and appointment reminders

- Allow patients to manually enter medication details and reminder schedules.
- Allow patients to create, update, complete, or cancel personal appointment reminders.
- Clearly label manually entered information as unverified when appropriate.
- Do not generate prescription instructions from an uncertain document extraction.
- Provide a clear method to edit or disable reminders.
- Explain that reminders do not confirm that a medication was taken or an appointment was attended.

### 6.11 Personal care-plan and follow-up tracker

- Allow patients to create or record follow-up tasks.
- Track pending, completed, cancelled, and needs-confirmation states.
- Display the source of a task when known, such as patient entry or a shared document.
- Avoid asserting that a care step was missed solely because no record exists.
- Allow patients to prepare questions when a follow-up detail is unclear.

### 6.12 Selective sharing

- Allow patients to select which supported documents or information they want to share.
- Identify the intended recipient and scope of the share.
- Record consent, sharing status, and relevant access events.
- Support revocation where technically and legally applicable.
- Ensure that revocation prevents future access through the sharing mechanism, while explaining that it cannot undo information already viewed or downloaded.
- Never grant a hospital organization blanket access to a patient's private account by default.

### 6.13 Audit and reporting

- Record relevant authentication, data access, sharing, administrative, and review actions.
- Restrict audit access to authorized roles.
- Avoid placing passwords, authentication tokens, or unnecessary sensitive content in logs.
- Provide aggregate reports only within the requesting user's authorized scope.

## 7. Privacy and Authorization Principles

CareGap-AI will follow these principles:

1. **Least privilege:** Users receive only the access necessary for their tasks.
2. **Tenant isolation:** Hospital organizations cannot access one another's protected records.
3. **Patient isolation:** Patients can access only their own records and information explicitly shared with them.
4. **Explicit sharing:** Hospital access to patient-owned information requires a defined authorization and sharing workflow.
5. **Server-side enforcement:** Every protected operation checks the requesting user's identity and permissions.
6. **Data minimization:** Collect only the information needed for a defined feature.
7. **Auditability:** Sensitive access and changes are logged.
8. **Secure defaults:** New documents and records are private unless an authorized sharing action changes their access.
9. **Transparent provenance:** The interface distinguishes patient-entered, imported, model-generated, and verified information.

A prototype implementation must use synthetic data for public demonstrations. Real patient information must not be used without appropriate authorization, safeguards, and review of applicable privacy and legal requirements.

## 8. AI Safety and Clinical Boundaries

CareGap-AI is a decision-support and personal-information management prototype.

It must not:

- Replace a licensed healthcare professional.
- Make autonomous diagnosis or treatment decisions.
- Prescribe medication or independently modify medication instructions.
- Claim that an undocumented action was definitely missed.
- Present a risk score as certainty.
- Fabricate information to fill gaps in a record.
- Suggest that a prototype has been clinically validated when it has not.

For potentially urgent symptoms, the patient experience should direct users to appropriate local emergency or urgent medical services rather than relying on the AI assistant.

All generated clinical explanations must be treated as potentially fallible and require appropriate verification.

## 9. Non-Functional Requirements

### Security

- Secure password handling or a trusted authentication provider.
- Protected transport using HTTPS in deployment.
- Secure secret management.
- Server-side authorization and tenant-isolation tests.
- Input validation and safe file handling.
- Appropriate protection against common web vulnerabilities.

### Reliability

- Predictable error responses.
- Health and readiness endpoints.
- Structured logging without unnecessary sensitive information.
- Database migrations and backup guidance.
- Safe handling of interrupted imports and failed AI requests.

### Performance

- Paginated record lists.
- Bounded import operations.
- Efficient database queries and appropriate indexes.
- Configurable timeouts for model inference and AI requests.

### Maintainability

- Modular application structure.
- Documented API contracts.
- Automated tests.
- Version-controlled model artifacts and care-gap rules.
- Reproducible model-training procedures.
- Clear setup instructions for local development.

### Accessibility and usability

- Clear navigation between hospital and patient experiences.
- Responsive layouts.
- Readable error messages.
- Accessible form labels and keyboard navigation.
- Plain-language explanations for non-technical patients.

## 10. Initial Technology Direction

The proposed stack is:

- **Frontend:** React and TypeScript.
- **Backend:** Python and FastAPI.
- **Database:** PostgreSQL.
- **Machine learning:** Python, pandas, and scikit-learn, with additional libraries justified by evaluation.
- **Explainability:** SHAP or an appropriate model-specific explanation method.
- **AI assistant:** A provider-independent interface supporting a local LLM through Ollama where practical.
- **Testing:** Pytest and frontend testing tools.
- **Deployment:** Docker Compose for local services, with CI through GitHub Actions.

The stack remains subject to technical design and feasibility testing. The MVP should prioritize maintainability, reproducibility, and zero-cost local development where possible.

## 11. MVP Scope

### Included

- Separate Hospital and Patient experiences.
- Authentication and role-based authorization.
- Hospital dashboard using synthetic demonstration data.
- CSV validation and controlled import.
- Offline readmission-model training and evaluation.
- Risk explanations and documented model limitations.
- Deterministic care-gap rules.
- Encounter review and task tracking.
- Patient health profile and private document vault.
- Patient report explanation with evidence grounding.
- Personal appointments, reminders, and follow-up tracking.
- Patient-controlled document sharing.
- Audit logging and automated tests.
- Local development instructions and a portfolio-ready demonstration.

### Excluded from the initial MVP

- Integration with live hospital EHR systems.
- Autonomous clinical decision-making.
- Production clinical deployment.
- Claims of regulatory approval or clinical validation.
- Automated prescribing or medication changes.
- Insurance claims processing.
- Billing and payments.
- Real-time medical-device integrations.
- Unrestricted hospital access to patient accounts.
- Emergency diagnosis or triage by AI.

## 12. Success Criteria

The MVP will be considered technically complete when:

- Both modes can be accessed through the intended authentication and navigation flows.
- Hospital organization boundaries and patient ownership are enforced by backend checks.
- The model can be trained and evaluated reproducibly using documented data.
- Model performance is reported with appropriate metrics and limitations.
- Care-gap results include traceable rules and supporting evidence.
- Missing data is not automatically treated as proof of a missed care action.
- Patient documents remain private unless explicitly shared.
- The patient assistant grounds its explanations in available document evidence and communicates uncertainty.
- Appointment and follow-up reminders can be managed by the patient.
- Automated tests cover critical permissions, sharing, and core workflows.
- The application can be started locally using documented instructions.
- The repository includes architecture, setup, API, data, testing, and safety documentation.

## 13. Key Product Principle

**CareGap-AI should help healthcare teams review information more consistently and help patients understand and organize their own information, without pretending that incomplete records are complete or that AI-generated outputs are verified clinical decisions.**
