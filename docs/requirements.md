# Security & Privacy Requirements — Privacy-Preserving Collaborative Cyber-Defence

## 1. Security Requirements

The system shall:

### SR-01 — Data Locality
Keep raw organisational cybersecurity data within its originating security boundary.

### SR-02 — Strong Identity
Authenticate organisations, services and authorised analysts before allowing participation or analytical access.

### SR-03 — Least Privilege
Restrict access according to role, organisational authority and analytical purpose.

### SR-04 — Update Protection
Prevent the aggregator from directly inspecting individual model updates.

### SR-05 — Model Integrity
Protect local and global models against unauthorised modification.

### SR-06 — Malicious-Client Detection
Detect or constrain suspicious federation participants and anomalous updates.

### SR-07 — Infrastructure Security
Protect APIs, workloads, containers, storage, compute and networking infrastructure.

### SR-08 — Availability and Resilience
Maintain collaborative analytics despite expected failures or participant dropouts.

### SR-09 — Auditability
Record security-relevant events in a traceable and tamper-resistant manner.

### SR-10 — Incident Response
Enable suspicious privacy or federation activity to generate security alerts and appropriate containment actions.

## 2. Privacy Requirements

### PR-01 — Data Minimisation
Only information necessary for the analytical objective should be processed or released.

### PR-02 — User-Level Protection
The privacy unit should be the individual rather than a single event where repeated events can be linked to the same person.

### PR-03 — Formal Privacy Accounting
Privacy expenditure must be mathematically accounted for rather than treated as an informal noise parameter.

### PR-04 — Controlled Privacy Budget
Repeated analytical operations must contribute to a cumulative privacy budget.

### PR-05 — Query Governance
Sensitive or repeated queries must be monitored and controlled.

### PR-06 — Output Protection
The final model and analytical outputs must be considered potential privacy-leakage channels.

### PR-07 — Privacy Attack Detection
Repeated or suspicious analytical behaviour should be detectable.

### PR-08 — Privacy Auditability
Privacy-related decisions and expenditure should be recorded for investigation and governance.

## 3. Design Principle

The research specifically distinguishes **data confidentiality**, **privacy**, **model security** and **participant security** because these are separate problems requiring different controls.

| Concern | Primary Controls |
|---------|------------------|
| Data confidentiality | Locality, encryption, access control |
| Privacy (individual inference) | Differential privacy, formal accounting, query governance |
| Model security | Integrity protection, secure aggregation, robust aggregation |
| Participant security | Strong identity, malicious-client detection, least privilege |
