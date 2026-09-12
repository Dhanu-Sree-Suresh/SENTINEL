import { createFileRoute } from "@tanstack/react-router";
import { Card, PageHead, Tag } from "@/components/ui/primitives";
import { useApp } from "@/lib/store";

export const Route = createFileRoute("/policy")({ component: Policy });

const CARDS = [
  { k: "aggregate" as const, t: "Population-level analytics", d: "Counts, rates, prevalence, trends" },
  { k: "model" as const, t: "Protected model updates", d: "Federated updates after clip/noise/mask" },
  { k: "demographic" as const, t: "Demographic ranges", d: "Generalized age, region bands" },
  { k: "individual" as const, t: "Individual-level access", d: "Records, diagnoses, names, identifiers" },
];

function Policy() {
  const policy = useApp((s) => s.policy);
  const setPolicy = useApp((s) => s.setPolicy);
  const log = useApp((s) => s.log);

  return (
    <div>
      <PageHead
        kicker="Authorization"
        title="Privacy & policy engine"
        lead="Deterministic rules. Authorization is never delegated to a generative model."
      />
      <div className="grid gap-3 sm:grid-cols-2">
        {CARDS.map((c) => {
          const on = policy[c.k];
          return (
            <Card key={c.k}>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-semibold">{c.t}</h3>
                  <p className="text-sm text-muted">{c.d}</p>
                </div>
                <Tag tone={on ? "ok" : "danger"}>{on ? "releasable" : "blocked"}</Tag>
              </div>
              <label className="mt-3 flex min-h-11 items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={on}
                  onChange={(e) => {
                    setPolicy({ [c.k]: e.target.checked });
                    log("Release policy", `${c.k} = ${e.target.checked}`, "INFO");
                  }}
                />
                Permit this category
              </label>
            </Card>
          );
        })}
      </div>
      <Card className="mt-4 text-sm text-muted">
        Individual-level access remains {policy.individual ? "enabled" : "blocked"}. Changes apply to new Analyst Console
        evaluations. Threat model: curious aggregator, malicious participant, membership/inversion/differencing attacker.
        SecAgg ≠ DP. Finite budget.
      </Card>
    </div>
  );
}
