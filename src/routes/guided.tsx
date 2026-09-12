import { createFileRoute, Link } from "@tanstack/react-router";
import { Card, PageHead } from "@/components/ui/primitives";

export const Route = createFileRoute("/guided")({ component: Guided });

const STEPS = [
  ["Business problem", "/", "Agencies cannot pool raw records under PDPL / residency rules."],
  ["Entities", "/overview", "Five silos. Raw data local."],
  ["Naïve baseline + ML", "/ml", "Centralized ROC-AUC ≈ 0.60 and model-family comparison."],
  ["Attack naïve", "/attacklab", "MI + gradient inversion + poisoning."],
  ["Enable privacy", "/federated", "FL + DP-SGD + SecAgg architecture."],
  ["Trade-off", "/tradeoff", "ε vs utility vs attack confidence."],
  ["Live monitor", "/monitor", "Kill-chain telemetry as SOC signal."],
  ["Audit evidence", "/audit", "Query decisions, privacy spend, and operator trail."],
];

function Guided() {
  return (
    <div>
      <PageHead
        kicker="Jury path"
        title="Guided demonstration"
        lead="Eight steps from problem to evidence. Use the floating button on any page, or jump from here."
      />
      <div className="space-y-2">
        {STEPS.map((s, i) => (
          <Link key={s[0]} to={s[1]} className="block">
            <Card className="flex items-start gap-3 hover:border-accent">
              <div className="flex size-8 items-center justify-center rounded-full bg-accent/15 text-sm font-bold text-accent">
                {i + 1}
              </div>
              <div>
                <div className="font-semibold">{s[0]}</div>
                <p className="text-sm text-muted">{s[2]}</p>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
