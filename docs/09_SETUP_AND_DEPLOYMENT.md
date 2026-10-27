# 09 — Setup and Deployment Guide

## 1. Purpose

This document explains how to configure, run, test, and prepare CareGap-AI for deployment.

CareGap-AI is a dual-mode healthcare SaaS prototype containing Hospital Intelligence Mode and Personal Health Mode.

The development environment prioritizes reproducibility, security, and low-cost tooling. Deployment instructions must be updated to reflect the actual implementation and hosting provider selected by the project.

The application is a portfolio prototype and is not clinically validated or approved for real-world clinical decision-making.

## 2. Technology Requirements

The planned stack includes:

| Component | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Database migrations | Alembic |
| ML | pandas, scikit-learn |
| Model explanations | SHAP, if appropriate |
| Testing | pytest, Vitest, React Testing Library |
| Optional browser testing | Playwright |
| Version control | Git |
| Optional local services | Docker Compose |
| Optional local LLM | Ollama |

Exact supported versions must be selected during implementation and recorded in dependency files.

## 3. Development Environment

The initial development target is Windows 11.

Recommended tools:

- Git.
- Python.
- Node.js LTS compatible with the selected Vite version.
- npm.
- PostgreSQL, installed locally or provided through Docker.
- A code editor such as Visual Studio Code.
- A terminal such as PowerShell.

Docker is optional for the first development milestone. If Docker Desktop is unavailable, PostgreSQL can be installed and run locally.

Use the project's actual dependency files as the source of truth for required versions.

## 4. Repository Structure

The repository is expected to evolve toward the following structure:

```text
CareGap-AI/
  docs/
    01_PRODUCT_REQUIREMENTS.md
    02_SYSTEM_ARCHITECTURE.md
    03_DATABASE_DESIGN.md
    04_API_SPECIFICATION.md
    05_AI_ML_DESIGN.md
    06_SECURITY_AND_PRIVACY.md
    07_TESTING_STRATEGY.md
    08_DEVELOPMENT_ROADMAP.md
    09_SETUP_AND_DEPLOYMENT.md

  frontend/
    src/
    public/
    package.json
    package-lock.json
    vite.config.ts

  backend/
    app/
      core/
      db/
      modules/
      main.py
    ml/
    tests/
    requirements.txt
    alembic.ini

  .env.example
  .gitignore
  README.md
```

This is the intended structure, not a requirement to create every file and folder immediately. The structure should be adjusted as implementation decisions are finalized.

## 5. Repository Setup

Open PowerShell and navigate to the project directory:

```powershell
cd D:\Projects\CareGap-AI
```

If the directory does not yet exist:

```powershell
New-Item -ItemType Directory -Path "D:\Projects\CareGap-AI" -Force
cd D:\Projects\CareGap-AI
```

Initialize Git if it has not already been initialized:

```powershell
git init
```

Verify the working directory:

```powershell
Get-Location
```

Check Git status:

```powershell
git status
```

Do not initialize a second repository inside an existing project repository.

## 6. Backend Setup

### 6.1 Create the Backend Environment

From the project root:

```powershell
New-Item -ItemType Directory -Path backend -Force
cd backend
```

Create a Python virtual environment:

```powershell
py -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the following command in the current terminal session only, if permitted by your environment:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Alternatively, invoke the environment's Python executable directly without activation.

### 6.2 Install Dependencies

Create and maintain a dependency file that records the selected packages and compatible versions.

The initial package set is expected to include:

- FastAPI.
- Uvicorn.
- SQLAlchemy.
- Alembic.
- psycopg, using a suitable installation option.
- Pydantic settings support.
- pytest.
- HTTPX.
- pandas.
- scikit-learn.
- python-multipart for supported multipart uploads.

Additional packages may be added when authentication, document processing, migrations, and other features are implemented.

Install the dependencies from the project's maintained dependency file:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Do not install unneeded packages simply because they appear in this list. The dependency file must reflect the actual application.

### 6.3 Start the Backend

Once the application entry point exists, start the development server from the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

Expected local address:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is normally available at:

```text
http://127.0.0.1:8000/docs
```

The documentation endpoint must not be assumed to be enabled in every deployment configuration.

## 7. Frontend Setup

Open a second PowerShell terminal.

Navigate to the project root:

```powershell
cd D:\Projects\CareGap-AI
```

Create the Vite project only if the `frontend` directory has not already been initialized:

```powershell
npm create vite@latest frontend -- --template react-ts
```

Navigate into the frontend directory:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Start the development server:

```powershell
npm run dev
```

Vite will print the actual local URL, commonly:

```text
http://localhost:5173
```

Keep the frontend and backend running in separate terminals during development.

If the frontend directory already contains a project, do not overwrite it by running the project-creation command again.

## 8. Environment Configuration

Create a root `.env.example` file containing placeholder values only.

Example:

```dotenv
APP_ENV=development
APP_NAME=CareGap-AI
APP_DEBUG=true

DATABASE_URL=postgresql+psycopg://caregap_user:CHANGE_ME@localhost:5432/caregap_db

SESSION_SECRET=REPLACE_WITH_A_RANDOM_SECRET
FRONTEND_ORIGIN=http://localhost:5173

UPLOAD_DIRECTORY=./storage/uploads
MAX_UPLOAD_SIZE_MB=10

AI_PROVIDER=mock
AI_MODEL=
AI_API_KEY=

MODEL_ARTIFACT_PATH=./ml/artifacts
```

These values illustrate configuration names; they must be aligned with the implemented settings and application code.

The application must not silently treat placeholder credentials as valid production configuration.

### Environment Security Rules

- Keep real secrets in a local `.env` file or an appropriate secret manager.
- Add `.env` to `.gitignore`.
- Never commit API keys, database passwords, or session secrets.
- Generate a strong, unpredictable session secret.
- Use separate credentials for development and deployment.
- Disable debug mode in deployed environments.
- Do not expose private uploads through a public static directory.
- Do not place server-side AI credentials in frontend environment variables.
- Treat frontend variables as public if the build tool exposes them to browser code.

## 9. PostgreSQL Setup

CareGap-AI requires PostgreSQL for the planned relational data model.

Create a dedicated database and a dedicated application role using an appropriate local PostgreSQL administration method.

Conceptual SQL:

```sql
CREATE ROLE caregap_user
WITH LOGIN PASSWORD 'REPLACE_WITH_A_STRONG_PASSWORD';

CREATE DATABASE caregap_db
OWNER caregap_user;
```

Run administrative SQL only through a trusted PostgreSQL administration session. Replace placeholder credentials before use.

The runtime role should receive only the permissions needed by the application. Production deployments should separate runtime credentials from migration and administrative credentials where practical.

Configure the application's database URL using the actual local connection details.

### Database Verification

Verify that:

- PostgreSQL is running.
- The database exists.
- The application role can connect.
- The configured database URL is correct.
- Network and firewall settings permit only intended connections.

Do not expose the database directly to the public internet for a portfolio deployment.

## 10. Database Migrations

Alembic will manage schema changes.

Once the migration environment and initial migration exist, apply migrations from the `backend` directory:

```powershell
alembic upgrade head
```

Check the current migration:

```powershell
alembic current
```

Create a migration after a reviewed model change:

```powershell
alembic revision --autogenerate -m "describe_schema_change"
```

Review autogenerated migration files before applying them. Autogeneration can miss or incorrectly represent certain changes.

Do not use an unreviewed destructive migration on a database containing important data.

## 11. Running Tests

### Backend

From the `backend` directory, with the virtual environment active:

```powershell
python -m pytest
```

For a coverage report, once pytest-cov is installed:

```powershell
python -m pytest --cov=app --cov-report=term-missing
```

### Frontend

From the `frontend` directory:

```powershell
npm run test
```

The exact command depends on the configured test scripts in `package.json`. If a test script has not been added yet, configure it before using this command.

### Production Build Check

Build the frontend:

```powershell
npm run build
```

Run lint checks if they are configured:

```powershell
npm run lint
```

A successful build does not replace unit, integration, security, or end-to-end testing.

## 12. Local AI Configuration

CareGap-AI should support a mock AI provider for predictable development and testing.

A provider-independent adapter should isolate application code from specific LLM vendors.

Possible modes:

- `mock`: deterministic responses for tests and UI development.
- `local`: a local model provider, if configured and suitable.
- `external`: an approved external provider, if configured and reviewed.

The mock provider must be clearly identified as a development/testing mode. It must not fabricate real medical evidence or be presented as an actual model inference result.

If Ollama is selected, install it separately, obtain an appropriate model, and verify that local inference works before integrating it into the application.

Local inference does not automatically guarantee security or clinical correctness.

Do not transmit real patient records to an external provider during development without an explicitly reviewed and authorized data-handling decision.

## 13. Model Artifact Management

The ML training pipeline should save model artifacts and corresponding metadata separately from ordinary application source code when practical.

Record:

- Model version.
- Feature schema version.
- Dataset reference.
- Target definition.
- Training configuration.
- Evaluation metrics.
- Training timestamp.
- Artifact location.

Do not commit restricted datasets, private health records, credentials, or unnecessarily large artifacts to a public repository.

The inference service must validate artifact availability and compatibility before making predictions.

If an artifact is unavailable or invalid, return a controlled error rather than generating a placeholder risk score.

## 14. Local Development Workflow

A normal development session should follow this sequence:

1. Open the repository.
2. Activate the backend virtual environment.
3. Confirm PostgreSQL is available.
4. Apply pending database migrations.
5. Start the backend.
6. Start the frontend in a second terminal.
7. Run the relevant automated tests.
8. Test the workflow using synthetic records.
9. Review application logs for errors and sensitive-data leakage.
10. Commit completed, tested changes to Git.

Before starting a new feature, review its dependencies and acceptance criteria in `08_DEVELOPMENT_ROADMAP.md`.

## 15. Deployment Preparation

Before selecting a hosting provider, determine:

- Whether the provider supports the required Python runtime.
- Whether PostgreSQL is available and appropriately managed.
- How private files will be stored.
- How environment variables and secrets are configured.
- How migrations will run.
- Whether background jobs are required.
- Whether the provider supports the expected workload.
- What the free-tier limitations are.
- What data processing and retention terms apply.

Do not assume that a free hosting plan supports persistent storage, background workers, or unrestricted inference.

The deployment architecture should be selected based on verified provider capabilities and the application's actual resource requirements.

## 16. Deployment Architecture

The intended deployment includes:

- A frontend hosting service.
- A backend application service.
- A managed or separately hosted PostgreSQL database.
- Private document storage.
- Optional background-worker infrastructure.
- An approved AI inference provider or local inference environment.

Conceptual architecture:

```text
User Browser
    |
    v
Frontend Hosting
    |
    v
HTTPS API
    |
    +------> Backend Services
    |             |
    |             +----> PostgreSQL
    |             |
    |             +----> Private File Storage
    |             |
    |             +----> ML Inference
    |             |
    |             +----> Approved AI Provider
    |
    +------> Authentication and Session Handling
```

This is a logical diagram. Actual network routing, authentication, and hosting boundaries depend on the selected deployment.

## 17. Deployment Security Checklist

Before making a deployed instance available:

- [ ] HTTPS is configured.
- [ ] Debug mode is disabled.
- [ ] Production secrets are configured securely.
- [ ] Database credentials are restricted.
- [ ] Database access is not publicly exposed unnecessarily.
- [ ] CORS permits only intended frontend origins.
- [ ] Authentication and authorization tests pass.
- [ ] Personal and hospital data isolation is verified.
- [ ] Uploaded documents are stored privately.
- [ ] Upload size and type restrictions are active.
- [ ] Sensitive content is not written to routine logs.
- [ ] AI-provider configuration has been reviewed.
- [ ] Database migrations have been tested.
- [ ] Health and readiness checks behave correctly.
- [ ] Backup and recovery expectations are documented.
- [ ] Synthetic demonstration data is used.
- [ ] No credentials or private datasets are committed.

## 18. Health Checks and Observability

The backend should expose separate health and readiness checks where appropriate.

### Health

Indicates whether the application process is responsive.

### Readiness

Indicates whether the service can handle requests based on essential dependencies and configuration.

Do not expose credentials, internal configuration values, database URLs, or sensitive diagnostics through health endpoints.

Use structured operational logs and request correlation identifiers where practical.

Logs should help diagnose errors without unnecessarily storing private document content, AI prompts, tokens, or secrets.

## 19. Backup and Recovery

Before handling persistent user data, define:

- Backup frequency.
- Backup encryption.
- Backup access permissions.
- Retention periods.
- Recovery procedures.
- Restoration testing.
- Expected recovery time and acceptable data loss.

Backups must receive protections comparable to the source database and file storage.

The portfolio prototype must clearly document which backup and recovery features are implemented and which remain planned.

## 20. Troubleshooting

### Backend Does Not Start

Check:

- The virtual environment is active.
- Dependencies are installed.
- The command is run from the correct directory.
- The `app.main` module exists.
- Environment variables are valid.
- The configured port is available.

### Database Connection Fails

Check:

- PostgreSQL is running.
- The database exists.
- The application role is valid.
- The database URL matches the environment.
- Network access is configured correctly.
- Migrations have been applied.

Do not solve a connection problem by unnecessarily opening PostgreSQL to public network access.

### Frontend Cannot Reach the API

Check:

- The backend is running.
- The API base URL is correct.
- CORS permits the development origin.
- The frontend configuration uses the intended environment.
- The API request and response schemas match.

### File Upload Fails

Check:

- The file type is supported.
- The upload size is within the configured limit.
- The upload directory or storage provider is accessible.
- The backend has appropriate permissions.
- Extraction dependencies are installed.
- The error is recorded without leaking document content.

### AI Requests Fail

Check:

- The selected provider is configured.
- The model is available.
- The provider credentials are valid, if required.
- Network connectivity is available where required.
- Timeouts and request limits are configured.
- The application returns a controlled failure state.

Never display fabricated medical explanations as a fallback for a failed model request.

## 21. Git and Release Workflow

Use Git to track implementation changes.

Recommended workflow:

1. Create a focused feature branch where appropriate.
2. Implement a small, coherent change.
3. Run relevant tests.
4. Review the diff.
5. Check for secrets and unintended files.
6. Commit the change with a descriptive message.
7. Merge only after required checks pass.
8. Tag meaningful releases when appropriate.

Do not commit:

- `.env` files containing secrets.
- Virtual environments.
- Private datasets.
- Uploaded patient documents.
- Database dumps containing private data.
- Unreviewed model artifacts.
- Temporary logs containing sensitive information.

## 22. Portfolio Demonstration

The demonstration should showcase complete workflows rather than isolated screenshots.

Recommended demonstration sequence:

1. Introduce the product and its two modes.
2. Open the Hospital Intelligence dashboard.
3. Inspect a synthetic encounter.
4. Show a prototype readmission prediction and its limitations.
5. Review a care-gap result and its supporting evidence.
6. Switch to a synthetic patient account.
7. Upload a sample document.
8. Show extracted text and a grounded explanation.
9. Demonstrate a limited sharing grant and its revocation.
10. Show relevant tests, architecture, and model evaluation results.

Clearly label synthetic records and AI-generated content.

Do not present a model's test metrics as proof of clinical effectiveness.

## 23. Final Readiness Criteria

CareGap-AI is ready for a portfolio demonstration when:

- The frontend and backend can be started using documented instructions.
- Database migrations run successfully.
- Core workflows function end to end.
- Automated tests pass.
- Sensitive resources are protected by backend authorization.
- Personal and hospital data boundaries are enforced.
- Private documents are not publicly exposed.
- ML outputs include appropriate context and limitations.
- AI responses are grounded in available evidence.
- Deployment configuration does not expose secrets.
- Synthetic demo data is available.
- Known limitations are documented.

Deployment to a public URL is optional until the local implementation is reliable.

## 24. Production Disclaimer

CareGap-AI is a portfolio and research prototype, not a clinically validated or production-approved healthcare service.

Before processing real patient information or supporting clinical workflows, the project would require appropriate legal and privacy review, threat modeling, clinical validation where relevant, operational security controls, provider assessments, and any applicable regulatory safeguards.

A successful local setup or public demonstration does not establish production readiness.
