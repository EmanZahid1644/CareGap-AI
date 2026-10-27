# CareGap-AI — API Specification

**Document ID:** CGA-API-004  
**Version:** 1.0  
**Status:** Proposed API Contract  
**API Prefix:** `/api/v1`  
**Backend:** FastAPI  
**Request/Response Format:** JSON, except file uploads and file downloads  
**Authentication:** Secure, server-validated authentication  
**Primary Consumers:** React Hospital Mode and Patient Mode

---

## 1. Purpose

This document defines the REST API contract for CareGap-AI.

The API supports:

- Authentication and user profiles.
- Hospital organization management.
- Hospital dashboards and encounter workflows.
- Controlled dataset imports.
- Readmission-risk predictions.
- Care-gap evaluation and review.
- Patient-owned health records.
- Private medical document management.
- Appointments, medication records, and care-plan tasks.
- Patient-controlled sharing.
- Evidence-grounded AI assistance.
- Reporting, audit events, and system health checks.

All endpoint definitions in this document are proposed contracts. They become authoritative only after implementation, testing, and corresponding updates to the API schemas.

## 2. API Design Principles

1. All routes use the `/api/v1` prefix unless explicitly identified as operational health endpoints.
2. JSON is the default request and response format.
3. File uploads use `multipart/form-data`.
4. File downloads must pass through an authorization-checked mechanism.
5. Protected endpoints require an authenticated identity.
6. Authorization is enforced on the backend.
7. Patient resources are owner-scoped by default.
8. Hospital operational records are organization-scoped.
9. Sharing grants provide narrowly scoped access rather than blanket access.
10. All request data is validated.
11. Sensitive values must not appear unnecessarily in error messages or logs.
12. Long-running operations return a trackable job identifier.
13. Paginated endpoints use a consistent response structure.
14. API schemas must be documented through FastAPI's generated OpenAPI specification.

## 3. Authentication Strategy

The initial implementation will use a secure authentication mechanism selected during implementation.

If cookie-based sessions are used, appropriate cookie protections and CSRF controls must be implemented.

If bearer tokens are used, token expiration, refresh, revocation, storage, and transport protections must be explicitly defined.

The endpoint examples below use generic authenticated-session semantics and do not mandate a particular token format.

### 3.1 Authentication endpoints

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| POST | `/auth/register` | Create an account | Public |
| POST | `/auth/login` | Authenticate a user | Public |
| POST | `/auth/logout` | End the current session | Authenticated |
| GET | `/auth/me` | Get the current user | Authenticated |
| POST | `/auth/forgot-password` | Start account recovery | Public |
| POST | `/auth/reset-password` | Complete account recovery | Recovery flow |

Registration must validate the input, prevent duplicate accounts, and avoid exposing whether a sensitive account exists through unnecessarily detailed recovery responses.

### 3.2 Example: current user

**Request**

```http
GET /api/v1/auth/me
```

**Example response**

```json
{
  "id": "user-uuid",
  "display_name": "Demo User",
  "account_status": "active",
  "available_modes": [
    "patient",
    "hospital"
  ]
}
```

The example values are illustrative. Actual mode availability must be determined from the authenticated user's account and permissions.

The response must not expose password hashes, session secrets, or internal security data.

## 4. Authorization Model

Authorization depends on the authenticated user, resource ownership, active organization memberships, assigned permissions, and applicable sharing grants.

### 4.1 Hospital roles

- `organization_admin`
- `quality_analyst`
- `care_reviewer`
- `read_only_viewer`

### 4.2 Patient permissions

Patients may access their own personal records and perform permitted actions on those records.

Access by another person or organization requires an explicitly authorized workflow.

### 4.3 Access rules

- A user cannot access a resource simply because they know its UUID.
- Hospital organization IDs supplied by the frontend do not independently establish authorization.
- Every hospital record request must validate the user's organization membership and role.
- Every patient resource request must validate ownership or an applicable authorized delegation.
- Every shared-resource request must validate the recipient, resource scope, grant status, expiration, and permitted action.
- Frontend route guards do not replace backend authorization.

Unauthorized access must not reveal protected record contents.

## 5. Standard Response Formats

### 5.1 Successful response

A successful request returns the endpoint's documented response schema and an appropriate HTTP status code.

### 5.2 Error response

Proposed standard format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data.",
    "details": [],
    "request_id": "request-uuid"
  }
}
```

The `details` field may contain safe field-level validation information. It must not contain secrets or sensitive record contents.

### 5.3 Pagination

Paginated list endpoints should use a consistent structure:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

Pagination limits must be enforced by the backend.

## 6. HTTP Status Codes

| Status | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Resource created |
| 202 | Accepted for asynchronous processing |
| 204 | Successful request with no response body |
| 400 | Invalid request or invalid workflow state |
| 401 | Authentication required or invalid |
| 403 | Authenticated user lacks permission |
| 404 | Resource unavailable or not found, depending on the disclosure policy |
| 409 | Conflict with current resource state |
| 413 | Upload exceeds the configured size limit |
| 415 | Unsupported media type |
| 422 | Request schema or field validation failure |
| 429 | Rate limit exceeded |
| 500 | Unexpected internal error |
| 503 | Required service temporarily unavailable |

The implementation should use consistent error codes and must not expose stack traces in production responses.

## 7. Hospital Organization APIs

### 7.1 Organization endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/organizations` | List organizations available to the user |
| POST | `/organizations` | Create an organization, if enabled |
| GET | `/organizations/{organization_id}` | View an authorized organization |
| PATCH | `/organizations/{organization_id}` | Update permitted settings |
| GET | `/organizations/{organization_id}/members` | List authorized members |
| POST | `/organizations/{organization_id}/members` | Add or invite a member |
| PATCH | `/organizations/{organization_id}/members/{membership_id}` | Update a membership |
| DELETE | `/organizations/{organization_id}/members/{membership_id}` | Remove or deactivate a membership |

Organization creation and membership management require explicit permission checks.

Membership changes should generate audit events.

### 7.2 Hospital dashboard

**Endpoint**

`GET /api/v1/hospital/dashboard/summary`

**Access:** Authorized hospital users.

**Example response**

```json
{
  "organization_id": "organization-uuid",
  "period": {
    "start": "2026-01-01",
    "end": "2026-01-31"
  },
  "encounter_count": 0,
  "prediction_count": 0,
  "open_review_tasks": 0,
  "care_gap_summary": {
    "documented": 0,
    "not_documented": 0,
    "conflicting": 0,
    "unknown": 0,
    "not_applicable": 0
  },
  "data_source": "synthetic_demo"
}
```

The values above are placeholders, not measured results.

Dashboard summaries must use only records the requesting user is authorized to access. The system must not imply that a missing record represents a failed clinical action.

## 8. Data Import APIs

### 8.1 Create import

**Endpoint**

`POST /api/v1/organizations/{organization_id}/imports`

**Access:** Hospital users with import permission.

**Content type:** `multipart/form-data`

Example fields:

- `file`: CSV file.
- `dataset_type`: Supported import type.

Expected behavior:

1. Authenticate the caller.
2. Verify organization membership and import permission.
3. Validate the file size, type, and contents.
4. Create an import job.
5. Queue processing if necessary.
6. Return the job identifier.

**Example response — HTTP 202**

```json
{
  "job_id": "job-uuid",
  "status": "queued",
  "message": "The import has been queued for processing."
}
```

### 8.2 Get import status

`GET /api/v1/organizations/{organization_id}/imports/{job_id}`

Returns the current job status, safe error summary, and processing counts.

### 8.3 List imports

`GET /api/v1/organizations/{organization_id}/imports`

Returns paginated imports visible to the requesting user.

### 8.4 Import constraints

- File and row limits must be configurable.
- CSV values must never be executed as code.
- Invalid rows must be reported safely.
- Import jobs must remain scoped to the authorized organization.
- Duplicate processing must be handled according to a documented idempotency policy.
- Direct identifiers must be excluded from model training unless their use is justified and authorized.

## 9. Encounter APIs

### 9.1 List encounters

`GET /api/v1/organizations/{organization_id}/encounters`

Supported query parameters may include:

- `page`
- `page_size`
- `start_date`
- `end_date`
- `review_status`
- `data_quality_status`

The backend must validate filter values and enforce organization-level access.

### 9.2 Get encounter

`GET /api/v1/organizations/{organization_id}/encounters/{encounter_id}`

Returns the permitted encounter details and data-quality information.

### 9.3 Update permitted encounter metadata

`PATCH /api/v1/organizations/{organization_id}/encounters/{encounter_id}`

Only explicitly editable fields may be updated. Imported source values and derived fields should not be silently overwritten.

### 9.4 Encounter access requirements

The backend must verify that the encounter belongs to the requested organization and that the authenticated user has the necessary permissions.

## 10. Readmission Prediction APIs

### 10.1 Request prediction

`POST /api/v1/organizations/{organization_id}/encounters/{encounter_id}/predictions`

**Access:** Authorized hospital users or internal workflows with prediction permission.

Example request:

```json
{
  "model_version": "baseline-v1"
}
```

The server must load the model from a trusted, configured artifact registry or storage location. It must not accept an arbitrary model path from the caller.

**Example response**

```json
{
  "prediction_id": "prediction-uuid",
  "encounter_id": "encounter-uuid",
  "prediction_target": "readmission_within_defined_horizon",
  "prediction_horizon": "configured_and_documented",
  "risk_estimate": 0.0,
  "model_version": "baseline-v1",
  "input_quality_status": "valid",
  "generated_at": "2026-01-01T12:00:00Z",
  "interpretation": "Research estimate; not a clinical determination."
}
```

The risk value is illustrative. The actual target, horizon, and output semantics must be defined by the ML specification.

### 10.2 Get prediction

`GET /api/v1/organizations/{organization_id}/predictions/{prediction_id}`

Returns the prediction and permitted explanation metadata.

### 10.3 List predictions

`GET /api/v1/organizations/{organization_id}/predictions`

Supports pagination and approved filters.

### 10.4 Prediction requirements

- Every prediction must reference a model version.
- The input must satisfy the model's documented schema.
- Unsupported inputs must be rejected or explicitly marked unusable.
- Model limitations must remain accessible to the user.
- Predictions must not be treated as diagnoses or treatment instructions.

## 11. Care-Gap APIs

### 11.1 Evaluate care gaps

`POST /api/v1/organizations/{organization_id}/encounters/{encounter_id}/care-gaps/evaluate`

Runs the applicable approved care-gap rules.

For large batches, the request may instead create a background job.

### 11.2 List care-gap results

`GET /api/v1/organizations/{organization_id}/encounters/{encounter_id}/care-gaps`

Returns the applicable results, statuses, rule versions, and supporting evidence references.

### 11.3 Review a result

`PATCH /api/v1/organizations/{organization_id}/care-gaps/{result_id}`

Allows an authorized reviewer to submit a permitted review status or resolution.

The system should preserve the original evaluation and record the review as a separate event or version where appropriate.

### 11.4 Care-gap result example

```json
{
  "result_id": "care-gap-uuid",
  "rule_key": "follow_up_documentation",
  "rule_version": 1,
  "status": "unknown",
  "evidence": [],
  "explanation": "The available record does not provide enough information to determine the follow-up status."
}
```

This example demonstrates that insufficient information must remain unknown rather than being automatically classified as missed care.

## 12. Review Task APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/organizations/{organization_id}/review-tasks` | List authorized review tasks |
| POST | `/organizations/{organization_id}/review-tasks` | Create a task |
| GET | `/organizations/{organization_id}/review-tasks/{task_id}` | Retrieve a task |
| PATCH | `/organizations/{organization_id}/review-tasks/{task_id}` | Update permitted task fields |
| POST | `/organizations/{organization_id}/review-tasks/{task_id}/notes` | Add a review note |
| GET | `/organizations/{organization_id}/review-tasks/{task_id}/notes` | List permitted notes |

Task updates must validate the workflow transition, organization scope, and assigned user's permissions.

Where notes require immutable history, corrections must be recorded rather than silently erasing the original record.

## 13. Patient Profile APIs

Patient endpoints use the authenticated user's identity to determine the default patient profile.

### 13.1 Retrieve personal profile

`GET /api/v1/patients/me/profile`

Returns the current patient's permitted profile fields.

### 13.2 Create or update personal profile

`PUT /api/v1/patients/me/profile`

Creates or replaces the permitted profile representation according to the documented schema.

Alternatively, a `PATCH` endpoint may be used for partial updates. The chosen semantics must remain consistent.

### 13.3 Personal timeline

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/patients/me/health-events` | List personal health events |
| POST | `/patients/me/health-events` | Add an event |
| PATCH | `/patients/me/health-events/{event_id}` | Update an owned event |
| DELETE | `/patients/me/health-events/{event_id}` | Delete an owned event where permitted |

All requests must verify that the resource belongs to the authenticated patient.

## 14. Medical Document APIs

### 14.1 Upload document

`POST /api/v1/patients/me/documents`

**Content type:** `multipart/form-data`

Fields may include:

- `file`
- `document_type`
- `document_date`

The server validates the file, stores it privately, creates metadata, and queues extraction if supported.

**Example response**

```json
{
  "document_id": "document-uuid",
  "processing_status": "queued",
  "document_type": "lab_report"
}
```

### 14.2 List documents

`GET /api/v1/patients/me/documents`

Returns paginated metadata for documents owned by the authenticated patient.

### 14.3 Get document metadata

`GET /api/v1/patients/me/documents/{document_id}`

Returns metadata and processing status after verifying ownership.

### 14.4 Download document

`GET /api/v1/patients/me/documents/{document_id}/content`

Streams the file or uses another appropriately authorized retrieval mechanism.

The backend must check access on every request. A document storage key must not be treated as a public download URL.

### 14.5 Delete document

`DELETE /api/v1/patients/me/documents/{document_id}`

Deletes or schedules deletion according to the defined retention policy.

The operation must account for associated extracted text, indexes, and other derived copies where applicable.

### 14.6 Extraction status

`GET /api/v1/patients/me/documents/{document_id}/processing`

Returns the extraction status, safe error details, and supported metadata.

## 15. Appointment APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/patients/me/appointments` | List personal appointments |
| POST | `/patients/me/appointments` | Create an appointment |
| GET | `/patients/me/appointments/{appointment_id}` | Retrieve an owned appointment |
| PATCH | `/patients/me/appointments/{appointment_id}` | Update an owned appointment |
| DELETE | `/patients/me/appointments/{appointment_id}` | Cancel or remove an appointment |

Appointments should support validated timestamps and appropriate timezone handling.

The API must distinguish a reminder schedule from confirmation that an appointment occurred.

## 16. Medication APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/patients/me/medications` | List patient-maintained medication entries |
| POST | `/patients/me/medications` | Create an entry |
| GET | `/patients/me/medications/{medication_id}` | Retrieve an owned entry |
| PATCH | `/patients/me/medications/{medication_id}` | Update an owned entry |
| DELETE | `/patients/me/medications/{medication_id}` | Remove an entry where permitted |

These endpoints manage recorded information and reminders. They do not prescribe medication or authorize AI-generated changes to a treatment plan.

The API must preserve the distinction between user-entered details and information extracted from an uploaded document.

## 17. Personal Care-Plan APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/patients/me/care-plan-items` | List personal tasks |
| POST | `/patients/me/care-plan-items` | Create a task |
| GET | `/patients/me/care-plan-items/{item_id}` | Retrieve a task |
| PATCH | `/patients/me/care-plan-items/{item_id}` | Update task status or permitted fields |
| DELETE | `/patients/me/care-plan-items/{item_id}` | Remove a task where permitted |

Initial task statuses:

- `pending`
- `completed`
- `cancelled`
- `needs_confirmation`

The system must not infer clinical completion or non-completion solely from a missing task record.

## 18. Patient Sharing APIs

### 18.1 Create a sharing grant

`POST /api/v1/patients/me/sharing`

Example request:

```json
{
  "recipient_user_id": "recipient-user-uuid",
  "resource_type": "medical_document",
  "resource_id": "document-uuid",
  "purpose": "Share a report for an upcoming appointment",
  "permission_scope": [
    "view"
  ],
  "expires_at": "2026-12-31T23:59:59Z"
}
```

This is an illustrative schema. Recipient identity verification, allowed scope, and expiration rules must be finalized during implementation.

The backend must verify resource ownership and ensure the recipient is eligible to receive the information.

### 18.2 List sharing grants

`GET /api/v1/patients/me/sharing`

Returns the patient's own sharing grants and their statuses.

### 18.3 Retrieve a sharing grant

`GET /api/v1/patients/me/sharing/{grant_id}`

Returns the details of an owned grant.

### 18.4 Revoke a grant

`POST /api/v1/patients/me/sharing/{grant_id}/revoke`

Revocation must prevent future access through the grant after the revocation is committed.

### 18.5 Retrieve a shared resource

A separate recipient-facing endpoint may be implemented after the recipient authorization model is defined.

It must validate the authenticated recipient, grant status, resource scope, permitted action, and any additional conditions.

The API must not assume that creating a grant makes the resource public.

## 19. AI Copilot APIs

The application will support different assistant contexts while reusing a common orchestration layer.

### 19.1 Patient document explanation

`POST /api/v1/copilot/patient/document-explanation`

Example request:

```json
{
  "document_id": "document-uuid",
  "question": "Can you explain the medical terms in this report?"
}
```

The backend must verify document ownership before retrieving content.

### 19.2 Patient health assistant

`POST /api/v1/copilot/patient/ask`

Example request:

```json
{
  "question": "Help me prepare questions for my next appointment."
}
```

The assistant may use only the patient's authorized information and approved educational sources.

### 19.3 Hospital copilot

`POST /api/v1/organizations/{organization_id}/copilot/ask`

Example request:

```json
{
  "encounter_id": "encounter-uuid",
  "question": "Which documented factors contributed to this model estimate?"
}
```

The backend must validate the caller's organization membership and access to the encounter before retrieving evidence.

### 19.4 Example AI response

```json
{
  "run_id": "copilot-run-uuid",
  "answer": "The available record contains the following relevant information...",
  "sources": [
    {
      "source_type": "document",
      "source_id": "document-uuid",
      "reference": "Relevant extracted section"
    }
  ],
  "limitations": [
    "This explanation is based only on the available information."
  ],
  "status": "completed"
}
```

The answer and source references are illustrative.

The backend must ensure that source references correspond to authorized evidence actually retrieved for the request.

### 19.5 AI safety requirements

- Reject empty or excessively long requests.
- Enforce request and inference timeouts.
- Avoid unrestricted database queries generated by an LLM.
- Treat retrieved documents as untrusted input.
- Do not permit the model to override access-control rules.
- Validate structured model output where required.
- Report insufficient evidence rather than inventing an answer.
- Avoid retaining raw prompts and outputs unless justified and appropriately protected.
- Provide safe error responses when the model is unavailable.

## 20. Reports and Model Evaluation APIs

### Hospital reports

- `GET /api/v1/organizations/{organization_id}/reports/summary`
- `GET /api/v1/organizations/{organization_id}/reports/care-gaps`
- `GET /api/v1/organizations/{organization_id}/reports/review-workload`

### Model evaluation

- `GET /api/v1/organizations/{organization_id}/models`
- `GET /api/v1/organizations/{organization_id}/models/{model_version_id}`
- `GET /api/v1/organizations/{organization_id}/models/{model_version_id}/evaluation`

Model evaluation endpoints should expose documented metrics, evaluation dataset information, model versions, and limitations.

Training jobs should use a separately controlled administrative or development workflow rather than allowing arbitrary users to trigger unrestricted model training through the public API.

## 21. Audit APIs

### List audit events

`GET /api/v1/organizations/{organization_id}/audit-events`

**Access:** Specifically authorized administrative or audit roles.

The response must be paginated and limited to the requesting user's permitted organizational scope.

Audit endpoints must not allow users to modify or delete existing audit events through ordinary API operations.

Patient-facing sharing history may be provided through a separate endpoint that returns only the patient's permitted sharing information, not unrestricted internal security logs.

## 22. Operational Endpoints

### Health

`GET /health`

Indicates whether the application process is running.

### Readiness

`GET /ready`

Indicates whether the application has the required dependencies to serve requests.

Operational endpoints must not expose secrets, environment variables, database credentials, or detailed infrastructure information to unauthorized users.

## 23. Rate Limits and Resource Controls

Apply appropriate request limits to:

- Authentication and account recovery.
- File uploads.
- Document extraction.
- AI assistant requests.
- Batch prediction and import jobs.
- Resource-intensive report generation.

Limits should be configurable and enforced at the appropriate layer.

Large operations should use background jobs rather than keeping HTTP requests open indefinitely.

## 24. API Testing Requirements

### Authentication tests

- Unauthenticated requests cannot access protected endpoints.
- Expired or revoked sessions are rejected.
- Disabled accounts cannot perform protected actions.

### Hospital authorization tests

- Users cannot access other organizations' encounters.
- Users cannot assign tasks to unauthorized members.
- Read-only users cannot modify restricted resources.
- Organization membership changes take effect correctly.

### Patient privacy tests

- A patient cannot retrieve another patient's document by changing its ID.
- A patient cannot edit another patient's appointments or care-plan items.
- A sharing grant cannot expose resources outside its scope.
- Revoked or expired grants do not authorize new access.
- Shared-resource access checks cannot be bypassed through alternate endpoints.

### AI tests

- The assistant cannot retrieve records outside its authorized scope.
- Unreadable documents do not produce fabricated summaries.
- Evidence references match the retrieved content.
- Unsupported clinical questions receive appropriate limitations.
- Provider failures and timeouts are handled safely.

### Validation tests

- Invalid dates and enum values are rejected.
- Oversized files are rejected.
- Malformed JSON is rejected.
- Pagination parameters are bounded.
- Duplicate or conflicting requests follow documented behavior.

## 25. OpenAPI and Documentation

FastAPI should generate an OpenAPI schema for the implemented endpoints.

The project should document:

- Authentication requirements.
- Request and response schemas.
- Endpoint permissions.
- Error codes.
- File upload limits.
- Pagination behavior.
- Idempotency behavior where relevant.
- Important safety and privacy limitations.

The generated OpenAPI schema must reflect implemented behavior rather than merely copying proposed endpoint definitions.

## 26. Implementation Order

Recommended API development sequence:

1. Health and readiness endpoints.
2. Authentication and current-user endpoints.
3. Organization and membership endpoints.
4. Patient profile and ownership endpoints.
5. Private document upload and retrieval.
6. Consent and sharing endpoints.
7. Appointment, medication, and care-plan endpoints.
8. Hospital imports and encounters.
9. Prediction and care-gap endpoints.
10. Review task workflows.
11. AI assistant endpoints.
12. Reports and audit endpoints.
13. Integration and security testing.
14. OpenAPI review and API contract updates.

Authorization foundations must be tested before sensitive endpoints are made available to the frontend.

## 27. Definition of Completion

The API specification is ready for implementation when:

- Every required feature has a defined endpoint group.
- Request and response schemas are documented.
- Authentication and authorization requirements are explicit.
- Patient and hospital data boundaries are defined.
- File handling and sharing workflows are specified.
- Long-running tasks have a tracking mechanism.
- Error formats and status codes are consistent.
- AI assistant endpoints have evidence and safety requirements.
- Security and integration tests cover the main access boundaries.
- OpenAPI documentation will be generated from the actual implementation.

---

**End of Document 04 — API Specification**
