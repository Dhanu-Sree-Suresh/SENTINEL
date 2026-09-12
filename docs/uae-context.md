# UAE Governance Context — SENTINEL · PPA-GOV

## 1. Relevance to the UAE

SENTINEL's Privacy Security Control Plane pattern is relevant to the UAE
because it addresses the intersection of:

- Cybersecurity (insider-threat detection)
- Privacy (differential privacy, query governance)
- Government data governance (per-entity data locality)
- Resilience (secure aggregation with drop handling)
- Secure data exchange across government entities
- Critical infrastructure protection (modeled as "Dept. C · Critical infra")
- Inter-organisational collaboration without centralisation

## 2. UAE Personal Data Protection Law (PDPL)

The UAE Personal Data Protection Law (Federal Decree-Law No. 45 of 2021)
establishes a framework for personal-data governance and addresses
cross-border data transfers.

- PDPL has significant exclusions, including:
  - Government data
  - Government entities acting as controllers or processors
  - Security and judicial authorities
  - Health personal data (governed by Federal Law No. 2 of 2019 on ICT in
    Health Fields, with strict localisation requirements — directly
    relevant to SENTINEL's synthetic "Dept. D · Health services" entity)
  - Banking and credit personal data (subject to separate regimes)
  - Entities in free zones with their own data-protection legislation
    (DIFC, ADGM)

- Health data in particular is subject to residency rules: storage,
  processing and transfer outside the UAE are restricted except under
  specific ministerial exceptions.
- Cross-border transfers under PDPL are permitted to jurisdictions with
  adequate protection or under other authorised mechanisms (contracts,
  consent, etc.).
- Executive regulations clarifying aspects of the law have been
  long-awaited; organisations must continue to apply the decree carefully.

Compliance remains dependent on factors including:

- Controller / processor relationship
- Processing purpose
- Lawful basis
- Data classification
- Transfer arrangements
- Retention
- Access controls
- Applicable sector-specific requirements

SENTINEL, as built, is a **technical demonstration** that could support
organisational privacy objectives in a production form; it is not itself
a substitute for a complete legal and governance programme, and it
currently runs on synthetic data with auth disabled (see `limitations.md`).

## 3. Cross-Border Data Considerations

- Where PDPL applies, transfers outside the UAE require adequacy or
  alternative safeguards.
- Sector-specific rules (especially health, and critical infrastructure
  data) impose stronger localisation requirements — two of SENTINEL's five
  modeled entities (health services, critical infrastructure) sit
  precisely in these stricter categories.
- Even where legal exemptions exist for government entities, operational,
  political and reputational constraints often still discourage
  unrestricted centralisation of sensitive telemetry.
- SENTINEL's federated design keeps raw records inside each entity's
  security boundary by construction, reducing the need for cross-entity or
  cross-border raw-data movement in a production deployment.

## 4. Government Data Governance & Sovereign Cloud

- UAE National Cloud Security Policy and related guidance emphasise data
  location awareness and sovereign / partial-sovereign controls for
  higher-classification data.
- Highly sensitive or classified government and critical-infrastructure
  data is expected to remain under strong sovereign control.
- A realistic production deployment of SENTINEL would place the control
  plane and secure aggregator in a government-controlled or sovereign
  cloud environment, while each participating entity retains its own
  private environment for raw data and local training — matching the
  trust-boundary diagram in `architecture.md`.

## 5. Dubai / UAE Cybersecurity Alignment

SENTINEL aligns conceptually with Dubai's and the UAE's cybersecurity
environment because it addresses:

- Protection of government data
- Protection of information systems
- Critical infrastructure security
- Secure data storage and exchange
- Privacy
- Resilience
- Collaboration between government entities

The collaborative insider-threat model is therefore positioned not simply
as an ML demo, but as **infrastructure supporting secure cooperation**
between government entities.

## 6. Zero-Trust Positioning

SENTINEL's architecture follows a Zero-Trust-oriented principle:

> No participant should automatically be trusted simply because it belongs
> to the federation.

In this prototype, access decisions already depend on:

- Requested operation (query classification — `classifyQuery()`)
- Privacy budget availability (per-entity ledger)
- Current entity risk level (reputation tier: normal / elevated /
  suspected_attack)
- Security and privacy policy (`/policy`)

A production successor would additionally need:

- Verified identity (auth is off by default in this build)
- Organisational membership and role enforcement
- Device / workload trust posture

This gap is named directly rather than glossed over: a legitimate
federation participant may still become compromised, and a prototype with
auth disabled cannot demonstrate continuous identity verification — only
the query-and-budget half of Zero-Trust is implemented here.

## 7. Audit and Accountability

SENTINEL generates an auditable event for:

- Federation connect/disconnect (`/infrastructure`)
- Training rounds and model version changes (`/federated`)
- Privacy-budget consumption (`/ledger`)
- Analytical queries and their risk scores (`/console`, `/decisions`)
- Attack-lab scenario runs (`/attacklab`)
- Kill-chain stage escalations (`/threat`, `/monitor`)
- Policy decisions — ALLOWED / BLOCKED (`/decisions`)

The audit trail supports the chain:

**Accountability → Investigation → Incident Response → Governance**

In this prototype, audit data lives in client-side app state and is not
tamper-resistant or persisted beyond the running process — a production
deployment would need immutable, retained storage per organisational
policy (see `compliance.md`).

## 8. Production Deployment Architecture

A realistic production deployment would use a sovereign or
government-controlled cloud environment for the control plane and secure
aggregator, while allowing each participating entity to retain full
control over its local data and training environment.

**Potential production controls** (named as roadmap items, not built in
this prototype):

- Private / sovereign cloud
- Kubernetes
- Mutual TLS (mTLS)
- Real federation identity (replacing the currently-disabled auth stub)
- Hardware-backed keys / HSM / KMS
- RBAC / ABAC
- Network segmentation
- Real SIEM integration (the current `/audit` and `/monitor` views are the
  UI pattern this would feed)
- Immutable audit storage
- Workload attestation where appropriate
