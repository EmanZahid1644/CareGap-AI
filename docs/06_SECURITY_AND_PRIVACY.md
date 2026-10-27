# 06 — Security and Privacy Design

## 1. Purpose

This document defines the security, privacy, access-control, data-protection, and AI-safety requirements for CareGap-AI.

CareGap-AI contains two distinct operating modes:

1. **Hospital Intelligence Mode:** Supports authorized hospital staff with encounter analysis, readmission-risk predictions, care-gap review, and operational workflows.
2. **Personal Health Mode:** Allows individuals to manage their own health information, documents, appointments, medications, and follow-up tasks.

Because these modes may contain sensitive health information, the system must enforce privacy and authorization at the backend, not merely through frontend navigation or UI restrictions.

The initial application is a portfolio prototype. Security controls must be designed and tested, but their existence does not automatically establish legal compliance, certification, or suitability for production healthcare use.

## 2. Security Objectives

CareGap-AI must aim to provide:

- Confidentiality of private health records.
- Integrity of records, predictions, and audit history.
- Availability of essential application workflows.
- Strong authentication and server-side authorization.
- Isolation between users, hospitals, and personal health accounts.
- Explicit consent for cross-boundary sharing.
- Secure document storage and processing.
- Safe handling of AI-generated content.
- Traceable access to sensitive resources.
- Appropriate retention and deletion controls.
- Protection against common web application vulnerabilities.

## 3. Trust Boundaries

The architecture must distinguish these trust boundaries:

1. Browser and frontend.
2. Public API and backend services.
3. Authenticated user identity.
4. Hospital organization and membership.
5. Patient-owned personal records.
6. Private document storage.
7. AI model and retrieval services.
8. Background jobs and workers.
9. External providers and integrations.
10. Administrative and operational access.

All data crossing a trust boundary must be validated and authorized.

The frontend must never be treated as a trusted security boundary. Hiding a button, route, or record in the UI does not replace backend access control.

## 4. Identity and Authentication

### 4.1 User Accounts

Each account must have a unique internal identifier.

A user may have access to different application capabilities, but access must be granted through explicit account relationships, memberships, permissions, and consent rules.

The system must not assume that a hospital employee is automatically authorized to view every patient's personal account.

### 4.2 Password Security

If password-based authentication is implemented:

- Use a reputable password-hashing algorithm such as Argon2id through a maintained library.
- Never store plaintext passwords.
- Never log passwords or password-reset tokens.
- Validate password-reset requests without unnecessarily revealing whether an account exists.
- Use short-lived, single-use password-reset tokens.
- Invalidate reset tokens after use.
- Apply rate limits to login and password-reset endpoints.
- Provide secure account recovery procedures.

Do not implement custom cryptographic algorithms.

### 4.3 Session Management

The initial web application should prefer server-managed sessions or another well-reviewed session design.

For cookie-based sessions:

- Use `HttpOnly` cookies.
- Use `Secure` cookies in HTTPS environments.
- Set an appropriate `SameSite` policy.
- Apply CSRF protection to state-changing requests where required.
- Rotate session identifiers after authentication and privilege changes.
- Support logout and session invalidation.
- Configure session expiry and inactivity limits.
- Avoid storing long-lived session credentials in browser local storage.

If token-based authentication is selected later, document token storage, expiry, rotation, revocation, and refresh-token protections before implementation.

### 4.4 Multi-Factor Authentication

MFA is a recommended enhancement for privileged hospital and administrative accounts.

For the prototype, document whether MFA is implemented or deferred. Do not claim MFA protection unless it is actually enabled and tested.

## 5. Authorization Model

### 5.1 Authorization Layers

Every protected request must pass the relevant checks:

1. Is the user authenticated?
2. Is the account active?
3. Does the user have the required capability?
4. Is the requested organization or personal resource within the user's access scope?
5. Is the requested action allowed on this specific resource?
6. Is additional consent required?
7. Is that consent valid for this resource and action?

Authorization must be enforced by backend services and database queries.

### 5.2 Role-Based Access Control

Potential hospital roles include:

- Organization Owner.
- Organization Administrator.
- Clinician or Clinical Reviewer.
- Care Coordinator.
- Analyst.
- Read-Only Viewer.

Roles should grant only the permissions required for their responsibilities.

For example, an analyst may be permitted to access approved aggregate reports without automatically receiving permission to read every patient's source documents.

The exact permissions must be defined in a centralized policy and tested.

### 5.3 Resource-Level Authorization

A user must not gain access simply by changing a record ID in a URL or API request.

Every request involving an encounter, document, prediction, review task, or other sensitive resource must verify ownership, organization membership, and applicable consent.

Avoid unrestricted database lookups such as retrieving a resource solely by its public identifier without checking the caller's authorization.

### 5.4 Default Deny

Access must be denied unless an explicit rule permits it.

Missing role information, invalid organization membership, expired consent, and failed authorization checks must not result in broader access.

## 6. Hospital and Patient Data Isolation

This is a core CareGap-AI security requirement.

### 6.1 Hospital Intelligence Mode

Hospital records must be scoped to the correct organization.

A user must not access records belonging to another organization unless an explicitly designed and authorized relationship permits it.

### 6.2 Personal Health Mode

Personal health records must be scoped to the authenticated account or the explicitly authorized personal profile.

The account owner must be able to distinguish their personal information from records imported or made available through a hospital workflow.

### 6.3 Cross-Boundary Access

Hospital staff must not automatically gain access to a patient's personal document vault.

Personal-mode data may be shared with a hospital only through an explicit, documented sharing grant.

A sharing grant should define:

- Grant identifier.
- Granting account or profile.
- Receiving user or organization.
- Permitted resources or resource categories.
- Permitted actions.
- Creation timestamp.
- Expiry, if applicable.
- Revocation status and timestamp.
- Relevant consent-record version.

The backend must verify the grant for every applicable access request.

### 6.4 Isolation Tests

Automated tests must verify that:

- User A cannot access User B's personal records.
- Organization A cannot access Organization B's records.
- A hospital user cannot access a personal document without a valid grant.
- A grant for one document does not authorize access to all documents.
- A read-only grant does not authorize modification.
- An expired or revoked grant no longer permits access.
- Guessing a record identifier does not bypass authorization.
- Background jobs respect the same access boundaries.

## 7. Database Security

### 7.1 Query Scoping

Database access must include the appropriate user, organization, or ownership constraints.

Avoid trusting organization IDs or patient IDs supplied by the client without verifying their relationship to the authenticated user.

Use parameterized queries and maintained ORM functionality. Never concatenate untrusted input into SQL statements.

### 7.2 Database Roles

Use separate database credentials for different environments.

Where practical, the runtime application should use a database role with only the permissions required for normal operation.

Schema migrations and administrative maintenance should use separately controlled credentials.

### 7.3 Row-Level Security

PostgreSQL Row-Level Security (RLS) may provide defense in depth.

If RLS is adopted:

- Define policies explicitly for sensitive tables.
- Set user and organization context securely for each transaction.
- Prevent client-controlled values from being trusted as authorization context.
- Understand connection pooling and transaction boundaries.
- Test behavior under missing or invalid context.
- Verify that application roles cannot bypass intended policies.
- Ensure administrative and migration privileges are carefully separated.

RLS must not be added as a superficial checkbox. Incorrect policies can create false confidence or break legitimate workflows.

## 8. API Security

All sensitive API endpoints must authenticate and authorize the caller.

Required controls include:

- Request schema validation.
- Appropriate HTTP methods and status codes.
- Request-size limits.
- Pagination limits.
- Rate limiting for sensitive or expensive operations.
- Safe error responses.
- Resource-level authorization.
- CORS configuration restricted to approved origins.
- Protection against injection attacks.
- Protection against insecure direct object references.
- Dependency updates and vulnerability checks.
- Request timeouts and controlled failure handling.

Do not return stack traces, database connection strings, filesystem paths, secret values, or internal infrastructure details to clients.

### 8.1 Input Validation

Validate:

- Identifier formats.
- String lengths.
- Numeric ranges.
- Date and time values.
- Enumerated values.
- Uploaded file types and sizes.
- Pagination parameters.
- Structured AI outputs.

Input validation must be paired with authorization; valid input is not necessarily authorized input.

## 9. Document and File Security

Medical documents are sensitive and must be treated as untrusted files.

### 9.1 Upload Controls

For each upload:

1. Authenticate the user.
2. Authorize access to the destination profile or record.
3. Enforce file-size and upload-count limits.
4. Validate allowed extensions.
5. Inspect MIME type and file signatures where feasible.
6. Generate a server-side storage identifier.
7. Store the file in a private location.
8. Record ownership and access metadata.
9. Queue extraction only after the upload passes required checks.
10. Return a safe status to the client.

Do not trust a filename or MIME type supplied by the browser alone.

### 9.2 Storage

- Store uploads outside public web directories.
- Use private object storage or protected local storage.
- Do not expose permanent public URLs for sensitive documents.
- Authorize downloads on the backend.
- Use short-lived signed URLs only where appropriate.
- Avoid predictable filenames and storage paths.
- Restrict access to extraction workers.
- Keep uploaded files separate from executable application code.

For local development, use a dedicated non-public upload directory with appropriate filesystem permissions.

### 9.3 Malware and Parser Risks

Where feasible, scan uploads for malware before processing.

Keep PDF, DOCX, and OCR dependencies updated. Apply file-size, page-count, and processing-time limits to reduce denial-of-service and parser-abuse risks.

Treat macros, embedded files, malformed documents, and archive-based file formats as potentially dangerous.

### 9.4 Extraction Security

Extracted text is untrusted content.

The extraction pipeline must not execute document scripts or embedded commands. Extraction errors should be recorded without exposing sensitive content in general application logs.

The original file should remain unchanged when derived text is generated or corrected.

## 10. AI and LLM Security

### 10.1 Data Minimization

Only send information required for the current task to the model.

Avoid including full patient records when a small, authorized passage is sufficient.

Before selecting an external model provider, review its data retention, processing, training, access, and contractual terms.

Do not assume that a provider is suitable for health information simply because it offers an API.

### 10.2 Provider Isolation

Implement a provider-independent AI adapter where practical.

The adapter should centralize:

- Provider configuration.
- Timeouts.
- Error handling.
- Structured-output validation.
- Token or request limits.
- Redaction and data-minimization controls.
- Logging rules.

API keys must remain server-side and must never be bundled into frontend code.

### 10.3 Local Models

Local inference through a tool such as Ollama may reduce the need to transmit data to an external inference provider.

However, local inference does not automatically make an application secure. Local network access, model logs, filesystem permissions, and other system components still require protection.

### 10.4 Prompt Injection

Uploaded documents, retrieved passages, and user-supplied text may contain instructions intended to manipulate the assistant.

The system must:

- Treat retrieved text as data, not trusted instructions.
- Keep system policy separate from retrieved content.
- Prevent document text from changing authorization rules.
- Restrict available tools to explicitly permitted operations.
- Require backend authorization for every tool call.
- Validate structured outputs before using them.
- Prevent unauthorized cross-user retrieval.
- Avoid allowing the model to execute arbitrary commands or code.

### 10.5 High-Impact Actions

The LLM must not independently:

- Grant access to records.
- Change a user's role.
- Revoke another user's consent.
- Modify the underlying prediction artifact.
- Change a medication dose.
- Make a diagnosis.
- Execute arbitrary SQL.
- Delete sensitive records without a defined, authorized workflow.

State-changing actions must use explicit backend endpoints with authentication, authorization, validation, and audit logging.

### 10.6 Grounded Responses

When explaining a medical document, the assistant should identify the source material used and distinguish direct evidence from interpretation.

If the source is incomplete, ambiguous, or unavailable, the assistant must communicate that limitation.

The assistant must not invent a diagnosis, medication, date, test result, or clinical instruction.

Urgent symptoms should be directed to appropriate local emergency or urgent medical services rather than handled as a routine chatbot conversation.

## 11. Encryption and Secrets

### 11.1 In Transit

Use HTTPS in deployed environments.

Protect communication between application components where required by the deployment architecture and threat model.

### 11.2 At Rest

Use available disk, database, and object-storage encryption controls appropriate to the deployment environment.

Encryption does not replace access control or application-level authorization.

### 11.3 Secrets Management

Secrets include:

- Database passwords.
- Session-signing keys.
- API keys.
- Cloud credentials.
- Encryption keys.
- SMTP credentials.

Requirements:

- Keep secrets out of source control.
- Use environment variables for local development where appropriate.
- Provide an `.env.example` containing placeholders only.
- Add `.env` and secret files to `.gitignore`.
- Rotate exposed credentials immediately.
- Restrict production secret access.
- Never print secrets in logs or error messages.

A committed secret must be considered exposed even if the repository is later made private or the commit is removed.

## 12. Logging and Audit Trail

### 12.1 Application Logs

Application logs should capture operational events without unnecessarily recording sensitive information.

Never log:

- Passwords.
- Session cookies.
- Authentication tokens.
- API keys.
- Full document contents by default.
- Full AI prompts containing sensitive records by default.

Use internal identifiers and structured event fields where possible.

### 12.2 Audit Events

Sensitive actions should generate audit events, including:

- Authentication successes and failures where appropriate.
- Access to protected records.
- Document uploads and downloads.
- Creation and revocation of sharing grants.
- Prediction requests.
- Changes to care-gap review status.
- Sensitive record modifications.
- Privileged administrative actions.
- Data exports and deletion requests.

An audit event should capture, where applicable:

- Event identifier.
- Actor identifier.
- Action.
- Resource type and identifier.
- Organization or account scope.
- Timestamp.
- Outcome.
- Request correlation identifier.
- Relevant reason or context.

Do not include document contents or secrets in audit events.

### 12.3 Audit Integrity

Limit permissions to alter or delete audit events.

For a production deployment, consider append-only storage, tamper detection, and separate audit retention controls.

The portfolio prototype must document any limitations in audit integrity.

## 13. Privacy, Consent, and Data Lifecycle

### 13.1 Data Minimization

Collect only information required for defined product functionality.

Avoid collecting real patient data during development unless there is a clear, authorized, documented need.

### 13.2 Consent

Sharing must be explicit, scoped, and understandable.

The interface should explain:

- What information will be shared.
- Who will receive it.
- What actions are permitted.
- How long access will last, if applicable.
- How access can be revoked.
- What happens to previously created copies or derived records.

Revocation must block future access through the applicable grant. It cannot guarantee deletion of copies that were lawfully exported or retained elsewhere before revocation.

### 13.3 Retention and Deletion

Define retention periods for:

- Accounts.
- Personal health records.
- Uploaded files.
- Extracted document text.
- Prediction records.
- AI-generated summaries.
- Audit events.
- Backups.

Deletion workflows must consider related extracted text, indexes, caches, and derived records.

Where complete immediate deletion is not technically possible, document the lifecycle and expected removal process.

Retention requirements must be reviewed before production use.

### 13.4 Data Export

Before generating an export:

- Authenticate the requester.
- Verify ownership and authorization.
- Restrict the export to permitted records.
- Avoid including other users' information.
- Generate the file in private storage.
- Limit download access and lifetime.
- Audit the export event where appropriate.

## 14. Environment Separation

Maintain separate configurations for:

- Local development.
- Automated testing.
- Demonstration or staging.
- Production, if introduced later.

Development and test environments must use synthetic fixtures by default.

Do not copy production health records into a local machine or public demonstration environment without a separately reviewed and authorized process.

Use separate credentials, storage locations, and databases across environments.

## 15. Backup and Recovery

For environments containing persistent data, define:

- What is backed up.
- Backup frequency.
- Encryption and access controls.
- Retention period.
- Recovery objectives.
- Restoration procedures.
- Restoration test frequency.

Backups must receive protection comparable to the data they contain.

The prototype should document whether automated backups and tested restoration are implemented or deferred.

## 16. Security Testing

### 16.1 Authentication Tests

- Invalid credentials are rejected.
- Expired sessions are rejected.
- Logout invalidates the session.
- Password-reset tokens cannot be reused.
- Login attempts are appropriately rate-limited.

### 16.2 Authorization Tests

- Cross-user access is denied.
- Cross-organization access is denied.
- Unscoped record lookups are rejected.
- Revoked consent blocks future access.
- Read-only roles cannot perform write operations.
- Patient-owned records remain isolated from hospital workflows.
- Export endpoints enforce the same access boundaries as ordinary reads.

### 16.3 File Security Tests

- Unsupported file types are rejected.
- Oversized files are rejected.
- Unauthenticated downloads are denied.
- Unauthorized users cannot download a file by guessing its identifier.
- Malformed documents fail safely.
- Extraction errors do not leak private content.

### 16.4 AI Security Tests

- Prompt injection does not override system policy.
- Retrieved documents cannot grant additional permissions.
- The model cannot invoke unauthorized tools.
- Invalid structured outputs are rejected.
- Missing evidence results in an uncertainty response.
- AI responses do not disclose another user's records.
- Secrets and sensitive content are excluded from routine logs.

### 16.5 Dependency and Configuration Checks

Where feasible, use automated dependency vulnerability checks, secret scanning, formatting, static analysis, and test execution in CI.

Security tools are aids, not proof that the application is secure.

## 17. Incident Response

If a security incident is suspected:

1. Record the time and initial symptoms.
2. Contain the affected account, service, credential, or integration.
3. Preserve relevant logs and evidence.
4. Determine which resources may have been affected.
5. Rotate exposed credentials and invalidate affected sessions where appropriate.
6. Restore secure operation.
7. Document root cause and remediation.
8. Review whether notification or reporting obligations apply.

A real deployment would need an incident-response owner, escalation contacts, communication procedures, and a legally reviewed notification process.

## 18. Development Security Checklist

Before merging a feature:

- [ ] All protected endpoints authenticate the caller.
- [ ] Resource-level authorization is enforced server-side.
- [ ] Organization and personal-account boundaries are preserved.
- [ ] User input is validated.
- [ ] SQL uses parameterized queries or safe ORM operations.
- [ ] Secrets are not committed.
- [ ] Sensitive data is not unnecessarily logged.
- [ ] File operations use private storage and authorization checks.
- [ ] AI retrieval uses only authorized sources.
- [ ] State-changing operations are validated and audited.
- [ ] Tests cover negative and unauthorized cases.
- [ ] Dependencies and configuration changes are reviewed.

## 19. Implementation Priorities

### Phase 1 — Core Protection

- Password hashing and secure authentication.
- Server-side session protection.
- Centralized authorization helpers.
- User and organization resource scoping.
- Private file storage.
- Environment variable and secret handling.
- Basic audit events.

### Phase 2 — Privacy Boundaries

- Sharing-grant schema.
- Consent-aware document retrieval.
- Grant expiry and revocation.
- Cross-user and cross-organization isolation tests.
- Secure data export and deletion workflows.

### Phase 3 — AI Protection

- Provider adapter.
- Data-minimization rules.
- Permission-aware retrieval.
- Prompt-injection tests.
- Structured-output validation.
- Sensitive-log prevention.

### Phase 4 — Operational Hardening

- Rate limiting and request-size limits.
- Dependency and secret scanning.
- Backup and recovery procedures.
- Security review.
- Incident-response documentation.
- Deployment configuration review.

## 20. Prototype Limitations

The initial portfolio implementation must not claim compliance with HIPAA, GDPR, or any other legal or regulatory framework merely because it implements security controls described here.

Applicability depends on the deployment, jurisdiction, organizations involved, data processed, contractual arrangements, and applicable law.

Before processing real patient information, CareGap-AI would require a formal security and privacy assessment, appropriate legal review, verified operational controls, and any applicable contractual or regulatory safeguards.

## 21. Acceptance Criteria

This document's requirements are considered implemented only when supported by code, configuration, tests, or documented operational procedures.

At minimum, the prototype must demonstrate:

- Secure password storage if password authentication is used.
- Server-side authorization on protected endpoints.
- Isolation between personal and hospital data.
- Explicit consent checks for cross-boundary access.
- Private document storage.
- Secure handling of application secrets.
- Sensitive-data minimization in logs.
- Audit events for important protected actions.
- Permission-aware AI retrieval.
- Automated tests for unauthorized access and common failure paths.
- Clear documentation of controls that remain incomplete.

The team must distinguish implemented controls from planned controls in the README and project demonstration.