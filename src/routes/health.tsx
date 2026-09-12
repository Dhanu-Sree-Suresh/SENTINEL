import { createFileRoute } from "@tanstack/react-router";
import { Card, PageHead, Tag } from "@/components/ui/primitives";
import { useApp } from "@/lib/store";

export const Route = createFileRoute("/health")({ component: Health });

function Health() {
  const entities = useApp((s) => s.entities);
  const queries = useApp((s) => s.queries);
  const events = useApp((s) => s.events);
  const connected = entities.filter((e) => e.connected).length;
  const blocked = queries.filter((q) => q.decision === "BLOCKED").length;
  const checks = [
    ["Secure aggregator", connected ? "Operational" : "Degraded", connected ? 96 : 62],
    ["Privacy engine", "Operational", 91],
    ["Access control", blocked ? "Monitor activity" : "Operational", Math.max(55, 100 - blocked * 8)],
    ["Threat monitor", blocked >= 3 ? "Review" : "Operational", blocked >= 3 ? 72 : 97],
    ["Audit stream", events.length ? "Receiving events" : "Waiting", Math.min(100, 70 + events.length)],
    ["Entity links", `${connected}/${entities.length} connected`, Math.round((connected / Math.max(1, entities.length)) * 100)],
  ] as const;

  return (
    <div>
      <PageHead
        kicker="Operations"
        title="System health"
        lead="Control-plane vitality: aggregator, DP engine, policy, threat monitor, audit, entity links."
      />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {checks.map((x) => (
          <Card key={x[0]}>
            <h3 className="font-semibold">{x[0]}</h3>
            <p className="text-sm text-muted">{x[1]}</p>
            <Tag tone={x[2] >= 90 ? "ok" : x[2] >= 75 ? "warn" : "danger"}>
              {x[2] >= 90 ? "healthy" : x[2] >= 75 ? "monitor" : "review"}
            </Tag>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-2">
              <div className="h-full bg-ok" style={{ width: `${x[2]}%` }} />
            </div>
            <div className="mt-1 text-xs text-muted">{x[2]}%</div>
          </Card>
        ))}
      </div>
      <Card className="mt-4">
        <h3 className="font-semibold">Recommended action</h3>
        <p className="mt-2 text-sm text-muted">
          {blocked >= 3
            ? "Review recent high-risk requests, inspect Threat / Kill-chain, and verify privacy-budget pressure before further sensitive analytics."
            : "System is healthy: maintain monitoring, validate policy changes, keep the demonstration reproducible."}
        </p>
      </Card>
    </div>
  );
}
