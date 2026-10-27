# 08 — Development Roadmap

## 1. Purpose

This document defines the implementation sequence, milestones, deliverables, dependencies, and acceptance criteria for CareGap-AI.

CareGap-AI is a dual-mode healthcare SaaS prototype with:

- Hospital Intelligence Mode.
- Personal Health Mode.
- Readmission-risk prediction.
- Deterministic care-gap detection.
- Medical document understanding.
- Grounded AI assistance.
- Appointment, medication, and follow-up tracking.
- Consent-based information sharing.
- Security, privacy, and audit controls.

The development strategy prioritizes a working, testable foundation before adding advanced AI capabilities.

## 2. Development Principles

1. Build one working vertical slice at a time.
2. Establish authentication and authorization before implementing sensitive workflows.
3. Use synthetic data for UI development, testing, and demonstrations.
4. Keep patient-owned records isolated from hospital records.
5. Build deterministic business logic before adding LLM-based automation.
6. Establish a measurable ML baseline before comparing complex models.
7. Test each module before integrating the next.
8. Keep documentation synchronized with implementation.
9. Prefer free or low-cost development tools where practical.
10. Avoid building unnecessary infrastructure before the MVP requires it.

## 3. MVP Definition

The MVP is complete when a user can demonstrate both application modes through a reliable end-to-end workflow.

### Hospital Intelligence Mode

- Secure login and organization-scoped access.
- Hospital dashboard with synthetic data.
- Encounter listing and detail views.
- Readmission-risk predictions from a documented prototype model.
- Prediction explanations and model-version metadata.
- Deterministic care-gap results.
- Review-task management.
- Basic analytics and audit events.

### Personal Health Mode

- Secure personal account.
- Personal health profile and timeline.
- Private document upload.
- Document text extraction and review.
- Grounded AI document explanation.
- Appointment and medication record management.
- Follow-up and care-plan task tracking.
- Explicitly scoped document sharing.
- Sharing-grant revocation.
- Personal data export.

### Platform Foundation

- React and TypeScript frontend.
- FastAPI backend.
- PostgreSQL database.
- Database migrations.
- Authentication and resource-level authorization.
- Private file storage.
- Automated tests.
- Environment-based configuration.
- CI checks.
- Setup and deployment documentation.

The MVP is a portfolio prototype, not a clinically validated healthcare product.

## 4. Proposed Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React, TypeScript, Vite | Application UI |
| UI styling | Tailwind CSS or an equivalent consistent styling system | Responsive interface |
| Backend | Python, FastAPI | REST API and application services |
| Database | PostgreSQL | Relational and transactional data |
| ORM | SQLAlchemy | Database interaction |
| Migrations | Alembic | Schema versioning |
| ML | pandas, scikit-learn | Data processing and prediction |
| Explanations | SHAP or an appropriate model-specific method | Model interpretation |
| AI integration | Provider-independent adapter | LLM access and testing |
| Local LLM | Ollama, if suitable for the machine | Optional local inference |
| Testing | pytest, Vitest, React Testing Library | Automated tests |
| Browser tests | Playwright | End-to-end workflows |
| Version control | Git and GitHub | Source control |
| CI | GitHub Actions | Automated checks |
| Local services | Docker Compose, if practical | Repeatable service setup |

Select exact dependency versions during implementation and preserve them in lockfiles.

## 5. Phase Overview

| Phase | Name | Main outcome |
|---|---|---|
| 0 | Repository and environment | Reproducible development setup |
| 1 | Product shell and UI system | Shared app shell and separate modes |
| 2 | Backend and database foundation | API, migrations, configuration |
| 3 | Authentication and access control | Secure account and organization boundaries |
| 4 | Core data workflows | Encounters and personal records |
| 5 | ML baseline | Reproducible prediction pipeline |
| 6 | Care-gap engine | Versioned deterministic rules |
| 7 | Documents and AI assistant | Private uploads and grounded explanations |
| 8 | Consent and audit | Scoped sharing and traceability |
| 9 | Testing and hardening | Integrated, tested workflows |
| 10 | Portfolio deployment | Demonstration-ready release |

The phases may overlap when dependencies allow, but security and data-model foundations must not be skipped.

## 6. Phase 0 — Repository and Environment

### Objectives

Establish a clean repository, local environment, and repeatable development workflow.

### Tasks

- Create the project repository.
- Create the documentation directory.
- Initialize Git.
- Add `.gitignore`.
- Add `.env.example`.
- Configure Python virtual environment.
- Initialize the frontend project.
- Confirm the backend can start.
- Confirm the frontend can start.
- Add a health endpoint.
- Record environment requirements.

### Deliverables

- Working repository.
- Frontend development server.
- Backend development server.
- Initial health endpoint.
- README with setup instructions.

### Acceptance Criteria

- A fresh local setup can start the application.
- Secrets are not committed.
- Dependencies are documented.
- Frontend and backend can be developed independently.

## 7. Phase 1 — Product Shell and UI System

### Objectives

Build the visual foundation for both application modes.

### Tasks

- Create a shared application shell.
- Create Hospital Mode navigation.
- Create Patient Mode navigation.
- Implement route structure.
- Establish typography, spacing, and reusable components.
- Build loading, empty, error, and success states.
- Add responsive layouts.
- Create synthetic placeholder dashboards.

### Suggested Hospital Pages

- Overview dashboard.
- Encounters.
- Risk predictions.
- Care-gap review.
- Review tasks.
- Analytics.
- Audit activity.

### Suggested Patient Pages

- Personal overview.
- Health timeline.
- Documents.
- Document explanation.
- Appointments.
- Medications.
- Care plan.
- Sharing and consent.
- Settings and export.

### Acceptance Criteria

- Navigation between modes works.
- The two modes are visually distinct but consistent.
- Layouts work on common desktop and mobile sizes.
- Placeholder data is clearly synthetic.
- No frontend-only restriction is mistaken for backend authorization.

## 8. Phase 2 — Backend and Database Foundation

### Objectives

Establish the API structure and persistence layer.

### Tasks

- Initialize FastAPI.
- Configure SQLAlchemy.
- Configure PostgreSQL.
- Initialize Alembic.
- Implement settings and environment configuration.
- Add request and response schemas.
- Add centralized error handling.
- Add structured logging.
- Create initial database migrations.
- Implement `/health` and `/ready` endpoints.

### Acceptance Criteria

- The backend starts with valid configuration.
- Database connections work.
- Migrations create the expected schema.
- Invalid configuration produces useful errors.
- Health endpoints do not expose secrets or sensitive internal details.
- Unit tests run against the backend.

## 9. Phase 3 — Authentication and Authorization

### Objectives

Implement security before sensitive records are introduced.

### Tasks

- Implement user registration or controlled account creation.
- Implement login and logout.
- Use secure password hashing if password authentication is selected.
- Implement session protection.
- Create organization membership models.
- Implement role and permission checks.
- Implement personal-record ownership checks.
- Create audit-event foundations.
- Add rate limiting where appropriate.

### Acceptance Criteria

- Protected routes reject unauthenticated requests.
- Organization access is enforced server-side.
- Users cannot retrieve another user's personal records.
- Hospital users cannot access patient-owned data without an appropriate grant.
- Negative authorization tests pass.

## 10. Phase 4 — Core Data Workflows

### Objectives

Make both modes useful before introducing advanced AI features.

### Hospital Tasks

- Create organization-scoped encounter records.
- Implement encounter search and filtering.
- Build encounter detail views.
- Add review-task creation and updates.
- Display audit activity.
- Build initial dashboard aggregations.

### Patient Tasks

- Create personal health profile.
- Add timeline events.
- Implement appointments.
- Implement medication records.
- Implement care-plan and follow-up tasks.
- Add edit and completion workflows.

### Acceptance Criteria

- Data persists correctly.
- CRUD operations respect authorization.
- Invalid input is rejected.
- The frontend handles empty and error states.
- Automated tests cover important workflows.

## 11. Phase 5 — Readmission-Risk ML Baseline

### Objectives

Build a reproducible and defensible ML pipeline.

### Tasks

- Review suitable dataset documentation and access requirements.
- Confirm the target definition is supported by the dataset.
- Create a data-quality report.
- Identify leakage-prone fields.
- Implement a reproducible split strategy.
- Create a DummyClassifier baseline.
- Train a Logistic Regression baseline.
- Evaluate additional models only when justified.
- Report discrimination and calibration metrics where applicable.
- Save model artifacts and metadata.
- Implement a validated inference service.

### Acceptance Criteria

- Dataset provenance is documented.
- Training is reproducible within documented limits.
- Test data is isolated from model selection.
- Leakage-sensitive checks are performed.
- Evaluation results include metrics beyond accuracy.
- Predictions identify their model version.
- Failure to load the model does not produce fabricated scores.

The initial model must be labeled as a research prototype and must not be presented as clinically validated.

## 12. Phase 6 — Care-Gap Detection

### Objectives

Implement transparent, testable rules for identifying items that may need review.

### Tasks

- Define the initial rules and their evidence requirements.
- Add rule identifiers and versions.
- Implement deterministic evaluation.
- Add positive, negative, missing-data, and boundary tests.
- Add insufficient-information states.
- Display the supporting evidence.
- Allow authorized reviewers to record a decision.

### Acceptance Criteria

- Each rule has documented behavior.
- Missing documentation is not automatically treated as proof of missed care.
- Results can be traced to a rule version and available evidence.
- Review decisions are stored with appropriate authorization and audit metadata.

## 13. Phase 7 — Documents and Grounded AI Assistant

### Objectives

Allow patients to upload personal documents and obtain evidence-based explanations.

### Tasks

- Implement private document storage.
- Validate upload types and sizes.
- Implement PDF and DOCX extraction where feasible.
- Add OCR only when necessary and supported.
- Store extraction status and provenance.
- Add an AI provider adapter.
- Implement permission-aware retrieval.
- Build a document explanation interface.
- Display source references where feasible.
- Handle missing evidence and provider failures.
- Test prompt injection and sensitive-data leakage.

### Acceptance Criteria

- Uploaded files are not publicly accessible.
- Extraction failures are represented clearly.
- The assistant only receives authorized evidence.
- Unsupported claims are not presented as source facts.
- Missing evidence produces an uncertainty response.
- External provider use is controlled by documented configuration and data-handling decisions.

## 14. Phase 8 — Consent, Sharing, and Audit

### Objectives

Support explicitly authorized sharing between personal and hospital workflows.

### Tasks

- Implement sharing-grant creation.
- Define resource scope and allowed actions.
- Add optional expiry.
- Implement grant revocation.
- Enforce grants in backend access checks.
- Audit sharing and revocation events.
- Add the patient sharing interface.
- Add authorized recipient access.
- Add export controls.

### Acceptance Criteria

- A user can share a specific permitted resource.
- The grant does not expose unrelated records.
- Expired and revoked grants block future access.
- Read-only grants cannot be used for writes.
- Sharing and revocation events are auditable.

## 15. Phase 9 — Testing and Hardening

### Objectives

Verify that the integrated application behaves correctly and safely.

### Tasks

- Expand backend unit tests.
- Expand frontend component tests.
- Add API integration tests.
- Add privacy-isolation tests.
- Add ML pipeline tests.
- Add AI grounding tests.
- Add end-to-end user journeys.
- Run dependency and secret scans.
- Review environment configuration.
- Test migrations and error handling.
- Fix critical and high-severity defects.

### Acceptance Criteria

- Critical authorization tests pass.
- Core workflows have automated coverage.
- Model evaluation is reproducible.
- AI failure states are handled safely.
- No known critical security defect remains unresolved.
- Known limitations are documented.

## 16. Phase 10 — Portfolio Deployment

### Objectives

Prepare a reliable, understandable demonstration of the project.

### Tasks

- Configure the selected hosting environment.
- Configure production environment variables.
- Apply database migrations.
- Configure private document storage.
- Configure HTTPS.
- Verify health checks.
- Configure logs and operational monitoring.
- Run smoke tests after deployment.
- Prepare synthetic demonstration accounts and data.
- Add screenshots and a demonstration walkthrough.
- Update the README and architecture documentation.

### Acceptance Criteria

- A reviewer can understand the product quickly.
- Setup and architecture are documented.
- The deployed application uses synthetic demo data.
- Sensitive files are not publicly accessible.
- The main workflows can be demonstrated reliably.
- Limitations are clearly communicated.

Deployment must not be described as production healthcare readiness.

## 17. Prioritization Framework

Use three priority levels.

### P0 — Essential

- Repository setup.
- Backend and frontend foundations.
- Authentication and authorization.
- Personal and hospital data isolation.
- Core database models.
- Basic encounter and patient workflows.
- ML baseline.
- Care-gap rules.
- Automated tests for critical boundaries.

### P1 — Important

- Document extraction.
- Grounded AI explanations.
- Consent-based sharing.
- Audit trail.
- Review workflows.
- Evaluation reports.
- CI pipeline.

### P2 — Later Enhancements

- Advanced analytics.
- More sophisticated model comparisons.
- Enhanced OCR.
- Additional AI providers.
- Richer reporting.
- Background-worker scaling.
- Advanced observability.
- Additional deployment automation.

Priorities may change if a technical dependency or important security risk requires earlier implementation.

## 18. Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Scope grows too quickly | Delayed MVP | Build one complete workflow at a time |
| Dataset does not support the target | Invalid ML experiment | Verify schema and target feasibility before training |
| Data leakage inflates metrics | Misleading model performance | Review features and use appropriate splits |
| Cross-user data exposure | Severe privacy failure | Centralized authorization and negative tests |
| LLM invents medical details | Unsafe or misleading output | Grounded retrieval, source references, uncertainty handling |
| External AI costs increase | Budget pressure | Mock providers, limit usage, evaluate local options |
| Document parsing fails | Broken patient workflow | Controlled errors and supported-format limits |
| Deployment configuration is insecure | Data exposure | Secret management and deployment review |
| UI work delays core logic | Incomplete functionality | Prioritize backend workflows and acceptance criteria |

## 19. Definition of Done

A phase is complete only when:

- Its planned functionality is implemented.
- Acceptance criteria are met.
- Relevant tests pass.
- Security and authorization implications are reviewed.
- Documentation is updated.
- Known limitations are recorded.
- Changes are committed to version control.

A visually complete page with non-functional controls does not count as a completed feature.

## 20. Progress Tracking

Maintain a simple progress log in the repository.

Suggested fields:

- Phase.
- Task.
- Status.
- Dependencies.
- Test status.
- Known issue.
- Next action.

Use the following statuses:

- Not Started.
- In Progress.
- Blocked.
- Testing.
- Complete.

Mark work complete only when the acceptance criteria are met.

## 21. Final Milestone

The primary milestone is a working, testable CareGap-AI prototype that demonstrates:

- A shared application with separate hospital and patient experiences.
- Secure, role-aware access.
- Synthetic encounter data and a reproducible ML baseline.
- Explainable prototype predictions.
- Deterministic care-gap rules.
- Private medical-document handling.
- Grounded AI document explanations.
- Explicitly scoped information sharing.
- Automated tests and documented limitations.

The goal is to demonstrate practical software engineering, applied machine learning, responsible AI integration, and privacy-aware architecture in one cohesive project.
