import { seedHash } from "./utils";
import { MEASURED } from "./results";

export type Decision = "ALLOWED" | "BLOCKED";
export type Risk = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type QueryRecord = {
  id: string;
  q: string;
  decision: Decision;
  risk: Risk;
  reason: string;
  answer: string;
  actor: string;
  ts: number;
  epsCost: number;
  individual: boolean;
};

export type EventRecord = {
  id: string;
  ts: number;
  type: string;
  detail: string;
  severity: "INFO" | "MEDIUM" | "HIGH";
};

const INDIVIDUAL =
  /(?:\bmrn\b|\bssn\b|\bemirates id\b|\bdate of birth\b|\bdob\b|\bnamed patient\b|\bspecific (?:patient|person|individual)\b|\bone person\b|\bidentify (?:the )?(?:patient|person)\b|\bexact record\b|\bjohn smith\b|\bwas (?:a |this )?(?:specific )?(?:patient|person|individual)\b|\bdiagnosis of\b|\bmedical condition of\b|\bwas .* present\b|\bmembership\b)/i;

export function classifyQuery(text: string, allowIndividual: boolean) {
  const individual = INDIVIDUAL.test(text);
  const blocked = individual && !allowIndividual;
  const risky = /rare|small|exact|single|named|identify/i.test(text);
  const decision: Decision = blocked ? "BLOCKED" : "ALLOWED";
  const risk: Risk = blocked ? "HIGH" : risky ? "MEDIUM" : "LOW";
  const reason = blocked
    ? "Blocked: the request could reveal information about an identifiable person."
    : "Approved: aggregate or generalized result — no individual record released.";
  return { decision, risk, individual, reason };
}

export function answerQuery(text: string, totalRecords: number, nSites: number, eps: number) {
  const low = text.toLowerCase();
  const seed = seedHash(text + totalRecords);
  const pct = 8 + (seed % 120) / 10;
  const noise = 0.25 / Math.max(0.05, eps);
  const count = Math.max(1, Math.round((totalRecords * pct) / 100));
  if (/diabetes/.test(low))
    return `Protected result: diabetes prevalence ≈ ${(pct + (seed % 5 - 2) * noise).toFixed(1)}% across ${nSites} entities (${count.toLocaleString()} modeled records). Raw rows remain local.`;
  if (/hypertension/.test(low))
    return `Protected result: ≈ ${Math.round(totalRecords * 0.154).toLocaleString()} hypertension cases in the selected scope (Laplace noise σ≈${noise.toFixed(2)} pp).`;
  if (/age/.test(low))
    return `Protected result: modeled population concentrates in ages 40–60; protected mean age ≈ ${41 + (seed % 17)} years.`;
  if (/respiratory|asthma/.test(low))
    return `Protected result: respiratory illness ≈ ${(7 + (seed % 55) / 10).toFixed(1)}% of the protected population.`;
  if (/how many records|held/.test(low))
    return `Protected result: connected entities collectively hold ${totalRecords.toLocaleString()} records. Zero raw rows transferred.`;
  if (/insider|risk rate|threat/.test(low))
    return `Protected result: pooled insider-threat positive rate ≈ 4.06% (SENTINEL synthetic). Federated model ROC-AUC ${MEASURED.flDp4Auc.toFixed(3)} at ε≈4.`;
  if (/recovery/.test(low))
    return `Protected result: mean modeled recovery window ≈ ${12 + (seed % 9)} days (aggregate only).`;
  return `Protected aggregate: ≈ ${count.toLocaleString()} modeled records match the requested scope. ε cost charged. Raw rows remain local.`;
}

export type AttackScenario =
  | "Membership inference"
  | "Gradient inversion"
  | "Differencing attack"
  | "Rare subgroup reconstruction"
  | "Repeated query attack"
  | "Model poisoning";

export function attackConfidence(opts: {
  scenario: AttackScenario;
  size: number;
  obs: number;
  signal: number;
  eps: number;
}) {
  const { scenario, size, obs, signal, eps } = opts;
  const boost: Record<AttackScenario, number> = {
    "Membership inference": 6,
    "Differencing attack": 12,
    "Rare subgroup reconstruction": 16,
    "Repeated query attack": 10,
    "Gradient inversion": 20,
    "Model poisoning": 24,
  };
  const exposure = (obs / (obs + 4)) * (signal / 100);
  const sizeFactor = Math.min(1.4, 30 / Math.max(2, size));
  const naive = Math.round(Math.min(99, 12 + exposure * 58 + boost[scenario] + sizeFactor * 8));
  const protection = scenario === "Model poisoning" ? 0.48 : 0.22 + 0.06 * Math.min(2, eps);
  const protectedC = Math.round(
    Math.max(1, Math.min(95, naive * protection - signal * 0.08 + Math.min(8, eps * 1.2))),
  );
  return { naive, protected: protectedC, gap: naive - protectedC };
}

export function measuredAnchor(scenario: AttackScenario) {
  if (scenario === "Membership inference") {
    return `Measured SENTINEL MI (high-risk subgroup, loss-threshold): naïve AUC ${MEASURED.miNaive.toFixed(3)} · FL+DP ε≈4 AUC ${MEASURED.miDp.toFixed(3)}. Advantage is modest on this weak-signal task — reported honestly.`;
  }
  if (scenario === "Gradient inversion") {
    return `Measured gradient inversion: raw cosine similarity ${MEASURED.giRaw.toFixed(6)} → DP-protected ${MEASURED.giDp.toFixed(6)}. Near-perfect reconstruction without DP; near-zero with noise.`;
  }
  if (scenario === "Model poisoning") {
    return `Measured 10× update-scale: plain mean ROC-AUC 0.585 vs coordinate-median 0.594 (recovers clean utility).`;
  }
  return `Interactive estimate plus SENTINEL kill-chain: ${MEASURED.killChainAlerts} alerts from ${MEASURED.killChainQueries} probing queries, max stage ${MEASURED.maxStage}.`;
}

export const ATTACK_PAYLOADS: Record<AttackScenario, string> = {
  "Membership inference":
    "Was synthetic individual X (age=47, region=DXB, high_risk=1) in Entity C training set?",
  "Gradient inversion":
    "Reconstruct features from unaggregated per-example gradients of the last FL round.",
  "Differencing attack":
    "Q1: count(region=Dubai). Q2: count(region=Dubai ∧ ¬id=X). Difference isolates X.",
  "Rare subgroup reconstruction":
    "Release exact count for age=71 ∧ rare_flag=1 ∧ entity=D (n≈3).",
  "Repeated query attack":
    "Replay the same prevalence query 40 times to average out Laplace noise.",
  "Model poisoning":
    "Entity C sends sign-flipped 10×-scaled update during FedAvg.",
};
