# Security & Privacy Requirements — SENTINEL · PPA-GOV

## 1. Security Requirements

The system shall:

### SR-01 — Data Locality
Keep raw entity records within their originating security boundary.
*Status: implemented conceptually — no route or store path in this
prototype moves raw records off an entity; only aggregates and model
updates cross the boundary.*

### SR-02 — Strong Identity
Authenticate entities, services and authorised analysts before allowing
participation or analytical access.
*Status: not implemented in this prototype. Auth is off by default (see
`limitations.md`) — a production successor requires this.*

### SR-03 — Least Privilege
Restrict access according to role, organisational authority and
analytical purpose.
*Status: not implemented; no role model exists in this prototype.*

### SR-04 — Update Protection
Prevent the aggregator from directly inspecting individual entity model
updates.
*Status: implemented as a protocol simulation — pairwise-masking secure
aggregation in `src/lib/store.ts`.*

### SR-05 — Model Integrity
Protect local and global models against unauthorised modification.
*Status: partially implemented via robust aggregation (coordinate-median /
trimmed-mean) against poisoning updates; not compatible with SR-04 in the
same round (see `limitations.md`).*

### SR-06 — Malicious-Client Detection
Detect or constrain suspicious federation participants and anomalous
updates.
*Status: implemented as entity reputation scoring and tiering
(normal / elevated / suspected_attack), visible in
`src/lib/results.ts: MEASURED.entityReputation` and the `/infrastructure`
and `/threat` views.*

### SR-07 — Infrastructure Security
Protect APIs, workloads, containers, storage, compute and networking
infrastructure.
*Status: out of scope for this prototype — it is a client-heavy web app
with no production infrastructure hardening included.*

### SR-08 — Availability and Resilience
Maintain collaborative analytics despite expected failures or participant
dropouts.
*Status: modeled at the protocol level (secure-aggregation drop handling);
not load- or failure-tested as a deployed service.*

### SR-09 — Auditability
Record security-relevant events in a traceable manner.
*Status: implemented as an in-app audit trail (`/audit`) covering queries,
attacks and rounds; not tamper-resistant or persisted beyond the process
(see `compliance.md`).*

### SR-10 — Incident Response
Enable suspicious privacy or federation activity to generate security
alerts and appropriate containment actions.
*Status: implemented as the kill-chain monitor (`/monitor`, `/threat`)
with stages up to `EXTRACTION_ATTEMPT`, and blockable decisions
(`/decisions`).*

## 2. Privacy Requirements

### PR-01 — Data Minimisation
Only information necessary for the analytical objective should be
processed or released.
*Status: implemented — analyst queries return aggregate/protected results
only (`answerQuery()`); individual-level asks are blocked before reaching
the answer path.*

### PR-02 — User-Level Protection
The privacy unit should be the individual rather than a single event,
where repeated events can be linked to the same person.
*Status: implemented under this prototype's one-record-per-individual
synthetic-data construction, where record-level DP-SGD coincides with
user-level protection (see `privacy_model.md` for the exact condition
under which this holds).*

### PR-03 — Formal Privacy Accounting
Privacy expenditure must be mathematically accounted for rather than
treated as an informal noise parameter.
*Status: implemented via an RDP accountant for DP-SGD training rounds,
with ε swept from "No DP" to 32 and an operating point at ε ≈ 4.*

### PR-04 — Controlled Privacy Budget
Repeated analytical operations must contribute to a cumulative privacy
budget.
*Status: implemented — each entity starts with a fixed budget
(`DEFAULT_ENTITIES: budget`) that is drawn down by queries and training
rounds, visible in `/ledger`.*

### PR-05 — Query Governance
Sensitive or repeated queries must be monitored and controlled.
*Status: implemented — `classifyQuery()` scores every query LOW / MEDIUM /
HIGH / CRITICAL and blocks individual-level asks; repeated and
rare-subgroup query patterns are named attack scenarios in `/attacklab`.*

### PR-06 — Output Protection
The final model and analytical outputs must be considered potential
privacy-leakage channels.
*Status: implemented — gradient-inversion and membership-inference attacks
are measured against both the model update and the trained model itself,
not just against raw queries.*

### PR-07 — Privacy Attack Detection
Repeated or suspicious analytical behaviour should be detectable.
*Status: implemented — kill-chain stages (`/monitor`, `/threat`) surface
probing behaviour as SOC-style alerts.*

### PR-08 — Privacy Auditability
Privacy-related decisions and expenditure should be recorded for
investigation and governance.
*Status: implemented in-app (`/audit`, `/ledger`, `/decisions`); not
production-grade persistence (see `compliance.md`).*

## 3. Design Principle

SENTINEL specifically distinguishes **data confidentiality**, **privacy**,
**model security** and **participant security**, because these are
separate problems requiring different controls — and the prototype's own
measured results make the distinction concrete (e.g. FL-without-DP still
carries meaningful membership-inference risk, showing that data locality
alone is not privacy).

| Concern | Primary Controls | Where in this app |
|---------|-------------------|---------------------|
| Data confidentiality | Locality, no raw-record transfer | `/prevalence`, `/pipeline` |
| Privacy (individual inference) | DP-SGD, RDP accounting, query governance | `/federated`, `/console`, `/ledger` |
| Model security | Robust aggregation, secure aggregation | `/federated`, `/attacklab` (poisoning) |
| Participant security | Entity reputation, kill-chain monitor | `/infrastructure`, `/threat`, `/monitor` |
