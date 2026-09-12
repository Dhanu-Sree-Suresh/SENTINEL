import { create } from "zustand";
import { DEFAULT_ENTITIES } from "./results";
import {
  type AttackScenario,
  type EventRecord,
  type QueryRecord,
  answerQuery,
  classifyQuery,
} from "./engine";
import { nowId } from "./utils";

export type Entity = {
  id: string;
  name: string;
  records: number;
  connected: boolean;
  epochs: number;
  budget: number;
};

export type Policy = {
  aggregate: boolean;
  model: boolean;
  demographic: boolean;
  individual: boolean;
};

export type ThemeMode = "dark" | "light";

type AppState = {
  theme: ThemeMode;
  setTheme: (t: ThemeMode) => void;
  entities: Entity[];
  policy: Policy;
  eps: number;
  epoch: number;
  queries: QueryRecord[];
  events: EventRecord[];
  incidents: EventRecord[];
  live: EventRecord[];
  lastAttack: { scenario: AttackScenario; naive: number; protected: number } | null;
  setEps: (e: number) => void;
  log: (type: string, detail: string, severity?: EventRecord["severity"]) => void;
  submitQuery: (text: string, actor?: string) => QueryRecord;
  runFederatedRound: () => void;
  spendBudget: (id: string, cost?: number) => void;
  resetEpoch: () => void;
  addEntity: (e: Omit<Entity, "id" | "epochs" | "budget">) => void;
  setPolicy: (p: Partial<Policy>) => void;
  setLastAttack: (a: AppState["lastAttack"]) => void;
  pushLive: (e: Omit<EventRecord, "id" | "ts">) => void;
  clearAudit: () => void;
};

const LIVE_BANK: Omit<EventRecord, "id" | "ts">[] = [
  { type: "FL round", detail: "Entity A local DP-SGD step · update norm within baseline", severity: "INFO" },
  { type: "SecAgg", detail: "Mask exchange OK (5/5 entities)", severity: "INFO" },
  { type: "Query monitor", detail: "Repeated near-identical aggregates from session S-17", severity: "MEDIUM" },
  { type: "Kill-chain", detail: "Stage PROBING · differencing Jaccard 0.89", severity: "HIGH" },
  { type: "Budget", detail: "Entity C remaining ε = 2.14", severity: "MEDIUM" },
  { type: "DP-SGD", detail: "Noise σ applied · RDP accountant updated", severity: "INFO" },
  { type: "Reputation", detail: "Entity C → suspected_attack", severity: "HIGH" },
  { type: "Policy", detail: "Population prevalence ALLOWED · ε cost 0.05", severity: "INFO" },
  { type: "Policy", detail: "Membership-shaped query REFUSED", severity: "MEDIUM" },
  { type: "Model", detail: "Global model broadcast · hold-out ROC-AUC 0.594", severity: "INFO" },
];

export const useApp = create<AppState>()((set, get) => ({
  theme: "dark",
  setTheme: (theme) => {
    set({ theme });
    if (typeof document !== "undefined") {
      document.documentElement.classList.toggle("dark", theme === "dark");
      document.documentElement.classList.toggle("light", theme === "light");
    }
  },
  entities: DEFAULT_ENTITIES,
  policy: { aggregate: true, model: true, demographic: true, individual: false },
  eps: 4,
  epoch: 15,
  queries: [],
  events: [],
  incidents: [],
  live: [],
  lastAttack: null,
  setEps: (eps) => set({ eps: Math.max(0.05, Math.min(32, eps)) }),
  log: (type, detail, severity = "INFO") => {
    const ev: EventRecord = { id: nowId(), ts: Date.now(), type, detail, severity };
    set((s) => ({
      events: [ev, ...s.events].slice(0, 300),
      incidents: severity === "HIGH" ? [ev, ...s.incidents].slice(0, 80) : s.incidents,
    }));
  },
  submitQuery: (text, actor = "analyst-07") => {
    const s = get();
    const nSites = Math.max(1, s.entities.filter((e) => e.connected).length);
    const total = s.entities.filter((e) => e.connected).reduce((a, e) => a + e.records, 0);
    const c = classifyQuery(text, s.policy.individual);
    const cost = c.decision === "ALLOWED" ? 0.05 : 0;
    const answer =
      c.decision === "BLOCKED"
        ? "No answer released. Ask for an aggregate, prevalence, range, or establishment-level statistic."
        : answerQuery(text, total, nSites, s.eps);
    const rec: QueryRecord = {
      id: nowId(),
      q: text,
      decision: c.decision,
      risk: c.risk,
      reason: c.reason,
      answer,
      actor,
      ts: Date.now(),
      epsCost: cost,
      individual: c.individual,
    };
    set((st) => ({
      queries: [...st.queries, rec].slice(-200),
      entities: st.entities.map((e) =>
        e.connected && cost ? { ...e, budget: Math.max(0, e.budget - cost / nSites) } : e,
      ),
    }));
    get().log("Analytics request", `${c.decision} · ${text}`, c.decision === "BLOCKED" ? "HIGH" : "INFO");
    return rec;
  },
  runFederatedRound: () => {
    set((s) => ({
      epoch: Math.min(40, s.epoch + 1),
      entities: s.entities.map((e) => (e.connected ? { ...e, epochs: Math.min(40, e.epochs + 1) } : e)),
    }));
    get().log("Federated training", `Epoch ${get().epoch} · DP-SGD + SecAgg`, "INFO");
  },
  spendBudget: (id, cost = 0.2) => {
    set((s) => ({
      entities: s.entities.map((e) => (e.id === id ? { ...e, budget: Math.max(0, e.budget - cost) } : e)),
    }));
    get().log("Privacy allowance", `${id} consumed ${cost} ε`, "INFO");
  },
  resetEpoch: () => {
    set((s) => ({
      epoch: s.epoch + 1,
      entities: s.entities.map((e) => ({ ...e, epochs: s.epoch + 1, budget: 8 })),
    }));
    get().log("New epoch", "Privacy allowances reset for the new training round", "INFO");
  },
  addEntity: (e) => {
    const id = `${e.name.slice(0, 12).replace(/\s+/g, "_")}-${nowId()}`;
    set((s) => ({
      entities: [...s.entities, { ...e, id, epochs: s.epoch, budget: 8 }],
    }));
    get().log("Infrastructure", `Added ${e.name}`, "INFO");
  },
  setPolicy: (p) => set((s) => ({ policy: { ...s.policy, ...p } })),
  setLastAttack: (lastAttack) => set({ lastAttack }),
  pushLive: (e) => {
    const ev: EventRecord = { id: nowId(), ts: Date.now(), ...e };
    set((s) => ({ live: [ev, ...s.live].slice(0, 40) }));
  },
  clearAudit: () => set({ queries: [], events: [], incidents: [] }),
}));

export function nextLiveTick() {
  const i = Math.floor(Math.random() * LIVE_BANK.length);
  useApp.getState().pushLive(LIVE_BANK[i]);
}
