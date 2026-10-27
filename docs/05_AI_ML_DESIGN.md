# 05 — AI/ML Design

## 1. Purpose

This document defines the artificial intelligence and machine learning strategy for CareGap-AI.

CareGap-AI combines predictive machine learning, deterministic care-gap rules, document understanding, and a grounded AI assistant. These components have separate responsibilities and must not be treated as interchangeable.

The initial implementation is a portfolio and research prototype. Its outputs are not clinically validated and must not be used as the sole basis for diagnosis, treatment, discharge, or other clinical decisions.

## 2. AI/ML Components

| Component | Approach | Purpose |
|---|---|---|
| Readmission risk | Supervised machine learning | Estimate a defined readmission outcome from historical encounter data |
| Care-gap detection | Deterministic rules | Identify potentially relevant follow-up or documentation items for review |
| Prediction explanations | Model-specific explanations and feature analysis | Explain factors associated with a model output |
| Document extraction | Text extraction and optional OCR | Convert supported medical documents into reviewable text |
| Patient document explainer | Retrieval-grounded LLM | Explain selected document content in plain language |
| Hospital copilot | Retrieval-grounded LLM and authorized tools | Summarize permitted information and help staff navigate workflows |
| Patient follow-up support | Rules, reminders, and grounded language generation | Help users track appointments and care-plan items |

The readmission model, care-gap engine, and LLM assistant must remain separate modules. An LLM must not invent model scores, silently modify model outputs, or independently declare a clinical care gap without an appropriate rule or verified evidence.

## 3. Readmission Risk Prediction

### 3.1 Objective

The prototype will estimate the probability of a clearly defined readmission outcome within a specified time window following an eligible hospital discharge.

The target definition must be finalized before model training.

The initial research question is:

"Among eligible discharged encounters in the selected dataset, can a model estimate whether a qualifying unplanned readmission occurs within 30 days?"

This is a research target, not a validated clinical prediction capability.

### 3.2 Target Definition

Before implementation, document:

- Eligible encounter types.
- Definition of a qualifying discharge.
- Definition of a readmission.
- Prediction time: when the estimate would theoretically be produced.
- Prediction horizon: initially, 30 days after discharge.
- Whether planned readmissions are excluded.
- How transfers, repeated encounters, and incomplete follow-up are handled.
- Dataset-specific limitations and the availability of outcome labels.

The target definition must match what the selected dataset can actually support. If planned versus unplanned readmissions cannot be distinguished reliably, the project must not claim to predict unplanned readmission.

### 3.3 Input Features

Candidate feature groups, subject to dataset availability and data-quality checks:

- Demographics available and appropriate for the research task.
- Encounter type and admission information.
- Length of stay.
- Historical utilization counts calculated before the prediction time.
- Prior encounters and readmissions.
- Diagnoses or diagnosis groupings recorded before prediction.
- Procedures and discharge-related fields, where available.
- Selected laboratory measurements, if their timing and meaning are documented.

Every feature must have a documented definition, source, data type, missing-value strategy, and availability time.

### 3.4 Leakage Prevention

Data leakage can make a model appear much more accurate than it will be in practice.

The following rules are mandatory:

1. Exclude fields created after the prediction time.
2. Exclude direct or indirect copies of the target label.
3. Do not use future encounters to calculate historical utilization.
4. Fit imputers, encoders, scalers, feature selectors, and other learned preprocessing only on training data.
5. Keep test data isolated until final evaluation.
6. Group related encounters by patient when creating splits, where the dataset supports patient identifiers.
7. Consider a chronological test split to assess performance on later encounters.
8. Record all exclusions and feature transformations.

If a field's timing or meaning is uncertain, exclude it until verified.

## 4. Dataset Strategy

### 4.1 Development Data

Use a suitable, lawfully accessible public dataset with documented provenance, permitted use, and appropriate access conditions.

Potential research sources include:

- MIMIC-IV, subject to its access requirements and data-use conditions.
- Other documented public or research datasets, provided they contain the required features and outcome information.

No dataset is considered selected until its access requirements, schema, target suitability, and license or data-use terms have been checked.

### 4.2 Demo Data

Use synthetic data for public product demos, UI development, screenshots, and automated tests.

Synthetic demo records must be visibly identified as synthetic. They must not be presented as real patients or as evidence of clinical performance.

A model trained on synthetic data must not be described as clinically validated or as representative of a real hospital population.

### 4.3 Data Quality Assessment

Before training, generate a data-quality report containing:

- Row and column counts.
- Missingness by feature.
- Duplicate records.
- Target prevalence.
- Invalid or implausible values.
- Unique patient and encounter counts, when available.
- Temporal coverage.
- Class imbalance.
- Potential leakage fields.
- Known dataset limitations.

Document the dataset version and preprocessing decisions.

## 5. Training Pipeline

The training pipeline should be reproducible and independent of the web application.

Recommended stages:

1. Load the approved dataset.
2. Validate the schema and expected columns.
3. Generate the data-quality report.
4. Define eligible encounters and labels.
5. Exclude leakage-prone or unsupported features.
6. Split data into training, validation, and test sets.
7. Build preprocessing pipelines.
8. Train a simple baseline model.
9. Train candidate models.
10. Select a model using validation results and documented criteria.
11. Evaluate the selected model on the held-out test set.
12. Save the model artifact, feature schema, configuration, metrics, and version metadata.
13. Register the model version for inference.

All learned transformations must be fitted using training data only. Test data must not influence model selection or threshold selection.

### 5.1 Candidate Models

Start with interpretable, computationally practical baselines:

- DummyClassifier as a reference baseline.
- Logistic Regression.
- Random Forest.
- Gradient-boosted trees, if appropriate and feasible.

Model complexity must be justified by measurable improvement, calibration, operational cost, and interpretability. A complex model is not automatically better.

### 5.2 Reproducibility

Record:

- Dataset identifier and version.
- Feature list and schema version.
- Target definition.
- Split strategy and random seed.
- Preprocessing configuration.
- Model type and hyperparameters.
- Python and key package versions.
- Evaluation results.
- Training timestamp.
- Model artifact checksum, where practical.

A model must be reproducible from its documented pipeline as far as dataset access and environment constraints permit.

## 6. Model Evaluation

Accuracy alone is insufficient, especially when positive outcomes are uncommon.

Report the following where applicable:

| Metric | Why it matters |
|---|---|
| AUROC | Measures ranking performance across thresholds |
| AUPRC | Useful for evaluating positive-class detection under class imbalance |
| Precision | Fraction of flagged cases that are positive |
| Recall / Sensitivity | Fraction of positive cases detected |
| Specificity | Fraction of negative cases correctly identified |
| F1 score | Combined precision-recall measure at a chosen threshold |
| Brier score | Measures probability prediction error |
| Calibration plot | Compares predicted probabilities with observed outcome rates |
| Confusion matrix | Shows threshold-specific classification counts |

Always compare the model with an appropriate baseline.

Document the selected decision threshold and explain its trade-offs. The threshold must not be presented as clinically appropriate without appropriate validation and stakeholder review.

### 6.1 Evaluation Protocol

- Use a patient-level split where possible to reduce leakage across encounters.
- Consider a chronological holdout for a more realistic temporal assessment.
- Use validation data for model and threshold selection.
- Reserve the test set for final evaluation.
- Report uncertainty and sample sizes where practical.
- Compare performance against a simple baseline.
- Record failed experiments and meaningful changes.

### 6.2 Subgroup Analysis

Where the dataset supports it and sample sizes are sufficient, examine performance across relevant subgroups.

Report sample counts and uncertainty. Avoid strong conclusions from small groups. Identify potential disparities and limitations rather than assuming similar performance across populations.

## 7. Prediction Explanations

The system may use SHAP or another suitable explanation method, depending on the selected model and implementation.

For each prediction, store or make available:

- Model version.
- Prediction timestamp.
- Defined outcome and prediction horizon.
- Predicted probability, if supported by the model.
- Input schema version.
- Relevant explanation values or summarized contributing features.
- Data-quality warnings.

Explanation text must distinguish between model associations and causal claims.

For example:

"Prior encounter count contributed to this model's estimate."

Do not state:

"Prior encounters caused this patient's readmission."

Feature explanations do not prove causation, clinical validity, or that an intervention will change an outcome.

Missing data and out-of-range inputs should be surfaced where relevant. If the model cannot produce a reliable output for the supplied input, the application should return an explicit error or unavailable state rather than inventing a score.

## 8. Care-Gap Detection Engine

Care-gap detection is a separate, versioned rules engine.

### 8.1 Rule Structure

Each rule should define:

- Unique rule identifier.
- Rule version.
- Human-readable title and description.
- Applicable record or encounter type.
- Required evidence and data fields.
- Evaluation logic.
- Evidence freshness requirements, if applicable.
- Output severity or priority, if justified.
- Known limitations.
- Review instructions.
- Test cases.

### 8.2 Evidence States

A care-gap result should distinguish between:

- **Potential gap:** available evidence suggests an item may need review.
- **No gap identified by this rule:** the available evidence does not trigger the rule.
- **Insufficient information:** required evidence is missing or unreliable.
- **Not applicable:** the rule does not apply to the record.
- **Needs human review:** available information is ambiguous or conflicting.

Absence of documentation must not automatically be treated as proof that care was not provided.

Rules must be clinically reviewed before any real-world clinical use. For the portfolio prototype, rule outputs are illustrative and must be labeled accordingly.

### 8.3 Testing

Test each rule with:

- Positive examples.
- Negative examples.
- Missing required fields.
- Conflicting evidence.
- Outdated information.
- Boundary dates.
- Non-applicable encounters.

Keep rules deterministic, version-controlled, and independently testable.

## 9. AI Document Understanding

### 9.1 Supported Inputs

The initial document pipeline may support PDF and DOCX, with OCR for supported scanned documents where feasible.

The pipeline should:

1. Validate file type and size.
2. Store the original file in private storage.
3. Extract text using a suitable parser.
4. Apply OCR when necessary and supported.
5. Record extraction status and metadata.
6. Identify uncertain or incomplete extraction.
7. Make extracted content available only to authorized users.
8. Allow the user to review extracted text and correct errors where appropriate.

Extraction results must not silently overwrite the original document.

### 9.2 Structured Extraction

If the system extracts dates, medications, diagnoses, measurements, or other fields, each extracted value should retain provenance where possible:

- Source document identifier.
- Page or text location.
- Extraction timestamp.
- Extraction method or model version.
- Confidence or uncertainty indicator, if supported.
- Review status.

Low-confidence or ambiguous values should be shown for confirmation rather than automatically treated as verified facts.

## 10. Grounded AI Assistant

### 10.1 Responsibilities

The assistant may:

- Explain selected document text in plain language.
- Summarize authorized records.
- Identify relevant information in retrieved sources.
- Draft questions for a healthcare professional.
- Explain what information appears missing from the available records.
- Help users navigate product workflows.

It must not diagnose conditions, prescribe or modify medications, or replace professional clinical judgment.

### 10.2 Retrieval-Augmented Generation

The assistant should use a retrieval-grounded approach:

1. Authenticate the user.
2. Determine the current mode and authorization scope.
3. Retrieve only records the user is allowed to access.
4. Select relevant document passages or approved knowledge sources.
5. Pass the relevant evidence to the language model.
6. Generate a response grounded in that evidence.
7. Return citations or references to the source documents where feasible.
8. Record appropriate audit metadata without unnecessarily storing sensitive prompt content.

If evidence is insufficient, the assistant must say so instead of filling gaps with guesses.

### 10.3 Hallucination Controls

- Instruct the model to distinguish evidence from inference.
- Require source references for document-specific factual claims where feasible.
- Do not invent values, dates, diagnoses, or medications.
- Do not treat missing documentation as proof that an event never happened.
- Show uncertainty when source text is ambiguous or OCR quality is poor.
- Make it possible to inspect the underlying source.
- Validate structured model outputs against a defined schema.
- Use deterministic application logic for permissions, reminders, and state-changing actions.
- Never let the LLM independently grant itself access to a document or change authorization rules.

### 10.4 Prompt Injection and Untrusted Documents

Uploaded documents and retrieved text must be treated as untrusted content.

Instructions embedded inside documents must not override system policies, authorization checks, or tool restrictions. The assistant must not execute document-supplied commands or expose other users' data because a document requests it.

## 11. Medication and Appointment Support

The patient mode may support reminders and tracking based on user-confirmed records.

- Preserve the original source and confirmation status.
- Allow users to review and edit extracted entries.
- Use explicit time zones and reminder states.
- Distinguish user-entered schedules from extracted text.
- Do not independently recommend dosage changes.
- Do not create a medication schedule from ambiguous text without confirmation.
- Make clear that reminders do not verify whether a medication was taken.

Reminder delivery and state changes must be handled by application services, not by free-form LLM output.

## 12. Inference Architecture

Expose prediction through a dedicated backend service.

Conceptual flow:

1. Authenticate the requesting user.
2. Verify organization membership and access to the requested record.
3. Validate the request against the active feature schema.
4. Apply the versioned preprocessing pipeline.
5. Run the approved model artifact.
6. Validate the output.
7. Persist prediction metadata and model version where appropriate.
8. Return the result with its limitations and explanation metadata.

The inference service must not accept arbitrary model paths or execute user-provided code.

If the model artifact is missing, incompatible, or fails validation, return a controlled error. Never substitute a fabricated prediction.

## 13. Model Versioning and Monitoring

Maintain a registry or equivalent metadata record for each model version.

Record:

- Version identifier.
- Training dataset reference.
- Feature schema.
- Target definition.
- Training configuration.
- Evaluation metrics.
- Artifact location.
- Approval or prototype status.
- Creation timestamp.

Monitor, where feasible:

- Missing or invalid input features.
- Changes in feature distributions.
- Changes in prediction distributions.
- Model errors and latency.
- Performance once reliable outcome labels become available.

A shift in input data is a reason to investigate, not proof that model performance has degraded.

The prototype must not automatically retrain and deploy a model into a clinical workflow. Any future production deployment would require a documented validation, review, approval, and rollback process.

## 14. Privacy and Security Requirements

- Enforce authorization before retrieving records or running patient-specific AI workflows.
- Keep patient-owned data separate from hospital organization data.
- Require explicit sharing grants for access across those boundaries.
- Do not place secrets, credentials, or unnecessary sensitive data in prompts or logs.
- Do not send private records to external model providers without an explicit, reviewed data-handling decision.
- Prefer synthetic data for public demonstrations.
- Restrict access to model artifacts, datasets, and extracted documents.
- Record appropriate access and prediction audit events.
- Apply retention and deletion policies to source files, extracted text, and derived records.

An LLM prompt is not an authorization boundary. Access control must be enforced by the backend.

## 15. Testing Strategy

### Unit Tests
- Feature transformations.
- Schema validation.
- Target construction.
- Metric calculations.
- Care-gap rules.
- Output validation.
- Permission checks.

### ML Pipeline Tests
- Reproducible data splits.
- Leakage-sensitive feature checks.
- Preprocessing fit only on training data.
- Baseline comparisons.
- Model serialization and loading.
- Prediction consistency for fixed test inputs.

### AI Assistant Tests
- Answers supported by retrieved evidence.
- Correct handling of missing evidence.
- Source-reference accuracy.
- Invalid structured output.
- Prompt-injection attempts in uploaded documents.
- Cross-user and cross-organization data-isolation attempts.
- Refusal to perform unauthorized state changes.

### Integration Tests
- Prediction API with an approved model artifact.
- Prediction API failure when the artifact is unavailable.
- Document upload and extraction.
- Consent-aware document retrieval.
- Audit event creation.
- End-to-end synthetic-data workflows.

## 16. Proposed Project Structure

```text
backend/
  app/
    modules/
      predictions/
        schemas.py
        service.py
        repository.py
        router.py
      care_gaps/
        rules.py
        engine.py
        schemas.py
        router.py
      documents/
        extraction.py
        schemas.py
        service.py
      ai_assistant/
        retrieval.py
        prompts.py
        providers.py
        schemas.py
        service.py
  ml/
    data/
    features/
    training/
    evaluation/
    inference/
    artifacts/
    tests/
```

Keep training scripts independent from API route handlers. Do not commit private datasets, credentials, or large model artifacts to the public repository.

## 17. Implementation Phases

### Phase 1 — Foundations
- Define the prediction target.
- Select and document the dataset.
- Build data-quality checks.
- Create synthetic fixtures for tests and demos.

### Phase 2 — Baseline Model
- Implement preprocessing.
- Train DummyClassifier and Logistic Regression baselines.
- Evaluate with held-out data.
- Save metrics and experiment metadata.

### Phase 3 — Candidate Evaluation
- Evaluate additional models if justified.
- Check leakage and calibration.
- Add explanations and documented limitations.
- Version the approved prototype artifact.

### Phase 4 — Care-Gap Engine
- Implement deterministic, versioned rules.
- Add insufficient-evidence states.
- Write rule-level unit tests.
- Label outputs as illustrative until appropriately reviewed.

### Phase 5 — Grounded Assistant
- Add permission-aware retrieval.
- Support document-grounded explanations.
- Add source references and uncertainty handling.
- Test prompt injection and data isolation.

### Phase 6 — Integration
- Connect the backend API to the frontend.
- Add audit metadata and error handling.
- Run integration and end-to-end tests.
- Document reproducibility and demo limitations.

## 18. Acceptance Criteria

The AI/ML implementation is ready for a portfolio demonstration when:

- The target definition and dataset provenance are documented.
- The training pipeline is reproducible.
- A baseline model has been evaluated on held-out data.
- Leakage-sensitive checks are implemented.
- Evaluation results include metrics beyond accuracy.
- Prediction responses identify the model version and relevant limitations.
- Care-gap rules distinguish potential gaps from insufficient evidence.
- Document explanations use authorized, retrievable evidence.
- The assistant can state when information is insufficient.
- Automated tests cover critical AI and authorization failures.
- Public demos use synthetic data.
- Documentation clearly states that the prototype is not clinically validated.

## 19. Explicit Limitations

CareGap-AI is a software engineering and applied ML portfolio project.

A good retrospective test score does not establish clinical utility, generalizability, fairness, regulatory compliance, or safety for real-world clinical use.

Any future clinical deployment would require additional clinical validation, privacy and security review, governance, appropriate regulatory assessment, and oversight by qualified professionals.

## 20. Open Decisions

The following decisions must be resolved and documented before implementation:

- Which dataset will be used for the first readmission experiment?
- Does that dataset support the intended target definition?
- Which features are available at the prediction time?
- What patient-level or temporal split is feasible?
- Which model provides the best justified balance of performance and interpretability?
- Which local or external LLM provider will be used, if any?
- Which document formats and OCR engines will be supported initially?
- Which care-gap rules can be safely demonstrated with synthetic data?

All decisions must be based on verified dataset documentation, actual implementation constraints, and measured results rather than assumptions.
