# Threat Model — Privacy-Preserving Collaborative Cyber-Defence

## 1. Government Collaborative Cyber-Defence Use Case

Government organisations generate large volumes of cybersecurity telemetry, including authentication logs, VPN activity, endpoint events, network anomalies, security alerts, and incident records. Individually, these datasets may reveal sensitive information about government infrastructure, users, security posture, and operational activity.

However, cyber threats frequently cross organisational boundaries. An attack pattern observed in one government entity may provide valuable intelligence for another.

The proposed system enables multiple government organisations to collaboratively learn cyber-threat patterns without centralising their raw cybersecurity data.

**Example entities:**

- **Entity A — Government Services**: authentication, web-access, VPN and privileged-access telemetry.
- **Entity B — Financial/Public Services**: administrative access, transaction metadata and endpoint telemetry.
- **Entity C — Critical Infrastructure**: network, device and OT/ICS-like security events.

Each organisation retains its raw data locally while participating in collaborative machine-learning and analytics. The resulting global model can identify patterns that may not be visible within a single organisation.

**Core principle:**
Government entities jointly learn cyber-threat intelligence while raw records remain inside their own security boundaries.

This use case is stronger than a generic privacy-preserving ML application because it directly connects privacy, cybersecurity, inter-organisational trust and operational defence.

## 2. Why Ordinary Centralised Analytics Is Not Sufficient

A traditional architecture would require participating organisations to send their cybersecurity data to a central repository. This creates several problems:

- A central repository becomes a high-value target for attackers.
- A single breach could expose information belonging to multiple organisations.
- Organisations lose direct control over their raw data.
- Centralisation increases the consequences of insider misuse or compromised credentials.
- Sensitive cybersecurity telemetry may reveal infrastructure and security weaknesses.
- Data-sharing arrangements introduce additional governance and privacy considerations.
- Cross-border or cross-organisation data transfers may create additional compliance requirements.

Therefore, the problem is not simply where data is stored. Centralisation changes the trust model by creating a large, shared trust boundary.

The proposed architecture instead keeps raw records within each organisation and shares only protected computational outputs.

## 3. Assets to Protect

The proposed system must protect the complete collaborative analytics ecosystem, not only the underlying data.

| Asset | Description | Protection Objectives |
|-------|-------------|-----------------------|
| **Sensitive government data and cybersecurity telemetry** | Government information, network logs, endpoint events, authentication activity, alerts and incident records | Confidentiality, integrity, access control, data locality |
| **Individual/user information** | Cybersecurity telemetry that may contain information associated with individual users or their activities | Minimise possibility of individual-level inference from analytical outputs |
| **ML models and model updates** | Local and global models containing learned cybersecurity patterns; updates that cross organisational trust boundaries | Protection against information leakage or manipulation |
| **Encryption keys and credentials** | Keys, certificates, credentials and service identities used to authenticate participants and secure communications | Prevent impersonation or unauthorised participation |
| **Infrastructure** | Federation services, APIs, compute resources, storage, containers, workloads and networking components | Security, availability and resilience |
| **Privacy budget and privacy ledger** | Permitted cumulative privacy loss and records of privacy expenditure | Protection from unauthorised modification or excessive use |
| **Audit logs** | Authentication, training, privacy, security and response events | Integrity and traceability to support accountability and incident investigation |

**Overall protection objective:** Preserve the confidentiality, integrity, privacy, availability and accountability of the collaborative analytics ecosystem.

## 4. Stakeholders

| Stakeholder | Role / Interest |
|-------------|-----------------|
| Government organisations | Retain control of sensitive data while gaining collaborative intelligence |
| Government SOC | Monitor threats, investigate incidents and receive privacy/security alerts |
| Security analysts | Use collaborative threat intelligence and investigate suspicious activity |
| Data owners | Govern access and permissible analytical use of organisational data |
| ML engineers | Develop and maintain collaborative models |
| Privacy/data-governance teams | Ensure appropriate privacy controls and governance |
| System administrators | Maintain infrastructure, identity and operational security |
| Federation operator | Coordinate collaborative analytics without requiring access to raw data |
| Senior government decision-makers | Require security, resilience, accountability and measurable value |
| Auditors/regulators | Require traceability, evidence and governance controls |

## 5. Trust Model

The architecture explicitly separates trust relationships.

### Trusted
- Each organisation's local execution environment
- The organisation controls its own raw data, local processing and local identity environment.

### Partially Trusted
- Federation coordinator
- The coordinator manages the collaborative process but should not automatically be trusted with individual model updates or sensitive analytical information.

### Not Trusted With Individual Updates
- Aggregator
- The architecture assumes that the aggregator may be curious, compromised or otherwise unable to be trusted with individual client updates.

### Potentially Malicious
The threat model considers:
- Compromised government nodes
- Malicious insiders
- Malicious analysts
- Compromised credentials
- Malicious federation participants
- External attackers

### Out of Scope for the First Prototype
- A completely compromised endpoint that already has legitimate plaintext access to its organisation's raw data.

The system is designed to protect against unauthorised inference and compromise across trust boundaries, rather than assuming that privacy technology can protect information from an administrator who already has legitimate access to plaintext data.

## 6. Threat Actors and Threats

| Threat Actor | Threat | Potential Impact |
|--------------|--------|------------------|
| External attacker | Infrastructure compromise | Data exposure, disruption |
| Malicious insider | Unauthorised analytics/querying | Privacy leakage |
| Curious/malicious aggregator | Inspection of model updates | Individual information leakage |
| Malicious participant | Model poisoning | Reduced model reliability |
| Compromised participant | Malicious updates or credentials | Federation compromise |
| Malicious analyst | Repeated/adaptive queries | Membership inference |
| Credential attacker | Identity impersonation | Unauthorised federation participation |
| Privacy attacker | Membership inference / model inference | Individual-level disclosure |
| Sybil / malicious clients | Multiple fake participants | Model manipulation |
| Privileged attacker | Audit-log manipulation | Loss of accountability |

## 7. Attack Assumptions

The system assumes that:

1. Raw government data must not be centrally collected.
2. The federation coordinator may be curious or compromised.
3. Individual model updates may contain information about local training data.
4. The final model may also leak information.
5. Some federation participants may be compromised or malicious.
6. Analysts may intentionally or unintentionally issue repeated privacy-sensitive queries.
7. Credentials or service identities may be compromised.
8. Attackers may attempt membership inference, model inference, poisoning or query abuse.
9. Privacy expenditure must be tracked across repeated analytical operations.
10. Audit records may themselves become a target and therefore require integrity protection.

The architecture therefore does not rely on a single privacy mechanism.
