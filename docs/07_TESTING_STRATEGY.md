# 07 — Testing Strategy

## 1. Purpose

This document defines the testing strategy for CareGap-AI, including frontend testing, backend testing, database integrity, AI/ML evaluation, security, privacy, and end-to-end workflows.

The objective is to detect defects early, protect sensitive data boundaries, verify system behavior, and make releases reproducible.

CareGap-AI is initially a portfolio prototype. Passing automated tests demonstrates that specified software behaviors work under tested conditions; it does not establish clinical validity, regulatory compliance, or production readiness.

## 2. Testing Principles

The project follows these principles:

1. Test critical behavior before visual polish.
2. Automate repeatable checks.
3. Test successful and unsuccessful paths.
4. Test authorization at the resource level.
5. Use synthetic data for automated tests and public demos.
6. Keep ML model evaluation separate from ordinary software correctness.
7. Test AI outputs against evidence and safety requirements.
8. Avoid tests that depend on external services when a deterministic mock is sufficient.
9. Keep test data isolated from development and production data.
10. Record known limitations and unresolved failures honestly.

## 3. Testing Pyramid

The project will use four complementary levels.

| Level | Purpose | Examples |
|---|---|---|
| Unit tests | Verify individual functions and components | Feature transformations, validation, care-gap rules |
| Integration tests | Verify interactions between modules | API, database, permissions, document storage |
| End-to-end tests | Verify complete user journeys | Login, upload, review, export |
| AI/ML evaluations | Measure model and AI behavior | Classification metrics, groundedness, leakage checks |

Unit tests should form the largest group because they are fast and easier to diagnose. Critical privacy and user workflows must also receive integration and end-to-end coverage.

## 4. Proposed Testing Stack

### Backend

- `pytest` — test runner.
- `pytest-cov` — coverage reports.
- FastAPI `TestClient` or HTTPX — API tests.
- SQLAlchemy-supported test database setup.
- Factory functions or fixtures — repeatable test records.
- Mocking utilities — isolated external-service tests.

### Frontend

- Vitest — test runner.
- React Testing Library — component behavior.
- `@testing-library/user-event` — simulated user interactions.
- Playwright — browser-level end-to-end tests, introduced after the main workflows stabilize.

### ML and AI

- scikit-learn evaluation metrics.
- Deterministic synthetic fixtures.
- Fixed test cases for preprocessing and inference.
- Mock LLM providers for predictable automated tests.
- A separate evaluation dataset for measuring model performance.

Exact dependency versions should be pinned or managed through the project's lockfiles.

## 5. Test Environment

### 5.1 Environment Separation

Maintain separate environments for:

- Local development.
- Automated tests.
- Demo or staging.
- Production, if introduced later.

Tests must not use production credentials or modify production records.

### 5.2 Test Database

Use an isolated test database or a disposable database instance.

Each test must begin with a known state and clean up its changes. Database migrations should be tested against a fresh database as well as an upgraded database when practical.

SQLite may be convenient for isolated unit tests, but it must not be assumed to reproduce all PostgreSQL behavior. Tests involving PostgreSQL-specific features, row-level security, constraints, or transaction behavior should use PostgreSQL.

### 5.3 Synthetic Fixtures

Create reusable fixtures for:

- Two unrelated personal accounts.
- Two separate hospital organizations.
- Hospital users with different roles.
- Patients and encounters.
- Medical documents with synthetic content.
- Sharing grants in active, expired, and revoked states.
- Model predictions and care-gap results.
- Appointments, medication entries, and care-plan tasks.

All fixture records must be clearly synthetic and contain no real patient information.

## 6. Backend Unit Testing

### 6.1 Validation

Test:

- Required fields.
- Invalid identifier formats.
- Invalid date and time values.
- Unsupported enum values.
- Excessive string lengths.
- Invalid numeric ranges.
- Malformed structured AI outputs.
- Unsupported file types.
- Oversized uploads.

Invalid input should produce a controlled error rather than an unhandled exception.

### 6.2 Business Logic

Test:

- Organization membership checks.
- Permission evaluation.
- Sharing-grant validity.
- Grant expiry and revocation.
- Encounter eligibility.
- Prediction request validation.
- Care-gap rule evaluation.
- Appointment reminder state.
- Document extraction status.
- Data export eligibility.

### 6.3 Error Handling

Verify that failures:

- Do not expose stack traces to ordinary clients.
- Do not disclose secrets.
- Do not leak another user's information.
- Return appropriate HTTP status codes.
- Leave the database in a consistent state.
- Generate safe operational logs.

## 7. API Integration Testing

API tests must verify the interaction among routing, authentication, authorization, service logic, persistence, and error handling.

### 7.1 Authentication

Test:

- Successful login.
- Invalid credentials.
- Missing authentication.
- Expired or invalid sessions.
- Logout and session invalidation.
- Password-reset token expiry and reuse prevention, if password reset is implemented.
- Rate limiting where configured.

### 7.2 Organization Workflows

Test:

- Creating or accessing an organization with appropriate permissions.
- Adding authorized members.
- Rejecting unauthorized membership changes.
- Retrieving only records within the permitted organization.
- Rejecting requests for unrelated organizations.

### 7.3 Prediction Workflows

Test:

- A valid prediction request returns the documented response schema.
- Invalid input is rejected.
- Missing model artifacts produce a controlled error.
- Model-version metadata is returned where required.
- Prediction records are persisted only when the workflow requires persistence.
- Unauthorized users cannot access prediction records.
- Audit events are generated for the defined sensitive actions.

### 7.4 Document Workflows

Test:

- Upload authorization.
- File validation.
- Private storage behavior.
- Extraction success and failure.
- Document ownership checks.
- Authorized downloads.
- Rejection of unauthorized downloads.
- Correct handling of revoked sharing grants.

### 7.5 Patient Workflows

Test:

- Creating and updating a personal profile.
- Adding appointments and reminders.
- Managing medication records.
- Tracking follow-up tasks.
- Reviewing extracted document values.
- Exporting permitted personal data.
- Preventing access to another account's data.

## 8. Security and Privacy Testing

Security tests are release-blocking for critical access-control failures.

### 8.1 Cross-User Isolation

Given two personal accounts, verify that Account A cannot read, update, delete, export, or infer private records belonging to Account B.

Test access using:

- Direct API requests.
- Modified URL identifiers.
- Modified request-body identifiers.
- Search and filtering parameters.
- Pagination and export endpoints.
- Background-job references.

### 8.2 Cross-Organization Isolation

Given two hospital organizations, verify that users from Organization A cannot access Organization B's encounters, predictions, review tasks, documents, or reports without an explicitly permitted relationship.

### 8.3 Consent Testing

Verify that:

- No grant means no cross-boundary access.
- A grant permits only its specified resources and actions.
- Expired grants are rejected.
- Revoked grants are rejected.
- A read-only grant does not allow modification.
- A document grant does not expose unrelated documents.
- Authorization is rechecked when a background job retrieves shared information.

### 8.4 Common Web Vulnerabilities

Include appropriate tests and reviews for:

- Insecure direct object references.
- SQL injection.
- Cross-site scripting.
- Cross-site request forgery where applicable.
- Insecure CORS configuration.
- Broken authentication.
- Excessive request sizes.
- Unrestricted file uploads.
- Information disclosure through errors.
- Rate-limit bypasses.

Automated tests should be supplemented by dependency scanning and a manual security review.

## 9. Frontend Testing

Frontend tests must focus on observable behavior rather than implementation details.

### 9.1 Component Tests

Test:

- Form validation.
- Loading indicators.
- Error messages.
- Empty states.
- Pagination.
- Search and filtering.
- Modal open and close behavior.
- Confirmation before destructive actions.
- Accessible labels and keyboard navigation.
- Responsive layout behavior where practical.

### 9.2 Role-Based UI

Verify that the UI displays the correct capabilities for each role.

However, frontend visibility is not authorization. Corresponding backend tests must independently verify that unauthorized actions fail.

### 9.3 Patient Mode

Test:

- Personal document list and upload states.
- Document-explanation loading and error states.
- Appointment and reminder management.
- Follow-up task completion.
- Sharing-grant creation and revocation interfaces.
- Clear presentation of AI limitations and uncertainty.

### 9.4 Hospital Mode

Test:

- Dashboard loading.
- Encounter search and filters.
- Prediction display.
- Model limitation labels.
- Care-gap evidence and insufficient-information states.
- Review-task updates.
- Report generation and access restrictions.

## 10. End-to-End Testing

Playwright tests should simulate important user journeys in a browser against a controlled test environment.

### Journey A — Hospital Review

1. Log in as an authorized hospital reviewer.
2. Open an eligible synthetic encounter.
3. Request or view its existing prediction.
4. Inspect the model version and explanation.
5. Review a potential care-gap result.
6. Record a review decision.
7. Verify persistence and audit metadata.
8. Confirm that an unauthorized user cannot access the same record.

### Journey B — Patient Document Explanation

1. Log in as a synthetic patient.
2. Upload a supported test document.
3. Wait for extraction to finish.
4. Review extracted text and uncertainty indicators.
5. Request an explanation of the document.
6. Verify that the response references available evidence.
7. Confirm that another account cannot retrieve the document.

### Journey C — Consent-Based Sharing

1. Log in as a synthetic patient.
2. Select one document for sharing.
3. Create a grant with limited scope.
4. Access the document through the authorized recipient.
5. Attempt to access a different document.
6. Confirm the unrelated document remains inaccessible.
7. Revoke the grant.
8. Confirm subsequent access is denied.

### Journey D — Failure Handling

1. Submit invalid input.
2. Simulate a missing model artifact.
3. Simulate an AI provider timeout.
4. Simulate document extraction failure.
5. Verify that the application presents safe, useful error states.
6. Confirm that failures do not create false predictions or unauthorized records.

## 11. Machine Learning Testing

ML testing has two distinct goals:

1. Verify that the software pipeline behaves correctly.
2. Evaluate whether the model performs adequately on the selected dataset.

Passing pipeline tests does not establish model quality.

### 11.1 Data Validation

Test:

- Required columns exist.
- Data types match the expected schema.
- Target labels are valid.
- Duplicate records are handled according to policy.
- Missingness checks run successfully.
- Feature ranges and category values are checked.
- Ineligible encounters are excluded.
- Dataset versions are recorded.

### 11.2 Leakage Prevention

Test and review:

- No direct target-label feature enters training.
- Post-prediction information is excluded.
- Historical features use only information available at prediction time.
- Preprocessing is fitted on training data only.
- Test data is not used for model or threshold selection.
- Related patient encounters are grouped appropriately where possible.

Some leakage risks require domain review and cannot be ruled out by a single automated test.

### 11.3 Metrics

Generate a versioned evaluation report containing, where applicable:

- AUROC.
- AUPRC.
- Precision.
- Recall or sensitivity.
- Specificity.
- F1 score.
- Brier score.
- Calibration information.
- Confusion matrix.
- Test sample size.
- Positive outcome count.
- Baseline comparison.

Document the threshold used for threshold-dependent metrics.

Do not rely on accuracy alone when the target is imbalanced.

### 11.4 Reproducibility

For fixed inputs and a fixed model artifact, verify that inference produces valid and consistent outputs within the documented numerical tolerance.

Record the training configuration, dataset reference, feature schema, model version, and evaluation metrics.

## 12. Care-Gap Rule Testing

Each care-gap rule must have dedicated tests.

For every rule, test:

- A case that should trigger the rule.
- A case that should not trigger it.
- Missing required evidence.
- Conflicting information.
- Outdated information.
- Boundary conditions.
- An inapplicable record.
- Invalid source data.

Verify that missing documentation can produce an insufficient-information result rather than an unsupported claim that care was missed.

Rules must be deterministic for the same normalized inputs and rule version.

## 13. AI Assistant Evaluation

LLM behavior may vary between runs and providers. Testing must therefore include both deterministic checks and broader quality evaluation.

### 13.1 Groundedness

Create test cases where the expected answer is supported by supplied synthetic source text.

Evaluate whether the assistant:

- Uses the relevant evidence.
- Preserves dates and values accurately.
- Distinguishes source facts from interpretations.
- Includes source references where required.
- Acknowledges insufficient evidence.
- Avoids invented diagnoses, medications, or results.

### 13.2 Adversarial Tests

Include prompts and documents that attempt to:

- Override system instructions.
- Request another user's information.
- Induce unauthorized tool use.
- Obtain secrets.
- Generate unsupported clinical claims.
- Treat missing information as proof of absence.
- Trigger unauthorized record modification.

Expected security behavior must be enforced by backend controls, not solely by model instructions.

### 13.3 Mocked Provider Tests

Use a mocked LLM provider for routine unit and integration tests.

Test:

- Successful responses.
- Timeouts.
- Provider errors.
- Rate-limit errors.
- Invalid structured outputs.
- Empty responses.
- Excessively long responses.

Live-provider evaluations may be run separately when access, cost, and data-handling policies permit.

## 14. File Processing Tests

Verify that:

- Supported PDFs and DOCX files are processed correctly.
- Unsupported formats are rejected.
- Corrupted documents fail safely.
- Oversized files are rejected.
- OCR failures are represented clearly.
- Empty extracted text is handled.
- Original files remain unchanged.
- Extracted text retains the correct document association.
- Unauthorized users cannot access extracted text.

Test representative document structures rather than assuming every medical document follows the same format.

## 15. Performance and Reliability Testing

Performance testing should be introduced after core workflows are functional.

Measure:

- API response latency.
- Database query latency.
- Prediction inference time.
- Document extraction time.
- AI response latency.
- Memory use during file processing.
- Behavior under concurrent requests.

Use synthetic datasets and realistic request patterns.

Define numerical performance targets only after establishing a baseline on the intended development environment.

Slow AI calls and document extraction should not unnecessarily block unrelated API requests. Where appropriate, use background jobs with explicit status tracking, retry policies, and safe failure states.

## 16. Database and Migration Testing

Test:

- Creation of the schema from a clean database.
- Application of migrations in sequence.
- Foreign-key constraints.
- Unique constraints.
- Required fields.
- Transaction rollback behavior.
- Relationship integrity.
- Deletion and retention workflows.
- Database behavior under concurrent updates where relevant.

If PostgreSQL Row-Level Security is used, run dedicated tests using the same class of database role and connection setup intended for the application.

## 17. Accessibility and Usability Testing

The application should support:

- Keyboard navigation.
- Clear focus indicators.
- Accessible labels for controls.
- Appropriate contrast.
- Understandable validation messages.
- Readable error and empty states.
- Responsive layouts.
- Clear distinction between AI-generated explanations and verified source data.

Important security, consent, and AI-limitation messages must not rely on color alone.

## 18. Coverage and Quality Gates

Code coverage is a useful indicator but is not proof of correctness.

Initial goals:

- Aim for at least 80% line coverage for core backend business logic once the main modules stabilize.
- Require dedicated tests for authentication, authorization, consent, and data-isolation rules.
- Test critical care-gap rules individually.
- Test ML preprocessing and inference independently.
- Include frontend tests for major workflows.
- Add end-to-end coverage for the most important user journeys.

Coverage percentages should not encourage testing trivial lines while ignoring high-risk behavior.

## 19. Continuous Integration

The CI pipeline should run on pull requests and relevant pushes.

Recommended sequence:

1. Install locked dependencies.
2. Run formatting and lint checks.
3. Run backend unit tests.
4. Run frontend unit tests.
5. Run integration tests using the appropriate test database.
6. Run ML pipeline tests.
7. Run dependency and secret scanning where configured.
8. Generate coverage reports.
9. Build the frontend and backend artifacts.
10. Run selected end-to-end tests when the environment supports them.

Critical test failures should block merging.

Tests that require unavailable external services should use mocks or run in a separately controlled evaluation workflow.

## 20. Defect Severity

### Critical
Examples: unauthorized cross-user access, cross-organization data leakage, exposed secrets, or an authorization bypass.

Action: block release and prioritize immediate remediation.

### High
Examples: incorrect ownership checks, corruption of sensitive records, invalid consent enforcement, or fabricated predictions presented as genuine outputs.

Action: block affected functionality until fixed.

### Medium
Examples: incorrect filters, recoverable workflow errors, or inaccurate non-critical summaries.

Action: prioritize according to impact and affected workflows.

### Low
Examples: minor visual inconsistencies or non-blocking layout issues.

Action: schedule for routine correction.

Severity should reflect real impact rather than how easy a defect is to fix.

## 21. Test Directory Structure

```text
CareGap-AI/
  backend/
    tests/
      unit/
      integration/
      security/
      api/
      fixtures/
    ml/
      tests/
        test_data_validation.py
        test_preprocessing.py
        test_training_pipeline.py
        test_inference.py
        test_evaluation.py
  frontend/
    src/
      components/
      features/
    tests/
      unit/
      integration/
    e2e/
      hospital-review.spec.ts
      patient-documents.spec.ts
      consent-sharing.spec.ts
```

Adapt this structure to the actual repository layout rather than creating empty folders for every possible future test.

## 22. Initial Implementation Order

### Phase 1 — Foundation
- Configure pytest and Vitest.
- Create synthetic fixtures.
- Set up an isolated test database.
- Test schemas and basic service functions.

### Phase 2 — Security-Critical Tests
- Test authentication and sessions.
- Test resource-level authorization.
- Test personal and hospital data isolation.
- Test consent expiry and revocation.

### Phase 3 — ML and Rules
- Test feature validation.
- Test leakage-sensitive transformations.
- Build baseline evaluation reports.
- Test care-gap rules and insufficient-information states.

### Phase 4 — AI and Documents
- Test upload validation.
- Test extraction and failure handling.
- Test grounded responses with synthetic documents.
- Test prompt injection and unauthorized retrieval.

### Phase 5 — End-to-End and CI
- Automate the principal user journeys.
- Add quality gates.
- Generate test and coverage reports.
- Document known failures and deferred coverage.

## 23. Definition of Done

A feature is considered complete when:

- Its expected behavior is documented.
- Input validation is implemented.
- Authentication and authorization are enforced where required.
- Success and failure paths are tested.
- Sensitive-data boundaries are preserved.
- Relevant automated tests pass.
- Errors are handled safely.
- The feature is documented.
- Any known limitations are recorded.

AI features additionally require evidence-grounding checks, documented limitations, and appropriate evaluation results.

## 24. Final Testing Policy

CareGap-AI must distinguish between:

- Software correctness.
- Security and privacy controls.
- ML predictive performance.
- AI response quality.
- Clinical validity.

These are different evaluation dimensions.

A successful test suite does not prove that a prediction is clinically useful or that an AI explanation is medically correct. The project must communicate those limitations clearly in its documentation and demonstration.
