import { createFileRoute } from "@tanstack/react-router";
import { Card, PageHead, Tag } from "@/components/ui/primitives";
import { MEASURED } from "@/lib/results";
import { useApp } from "@/lib/store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/threat")({ component: Threat });

const STAGES = [
  "RECONNAISSANCE",
  "PROBING",
  "DIFFERENCING",
  "AGGREGATION",
  "INFERENCE",
  "EXTRACTION_ATTEMPT",
];

function Threat() {
  const events = useApp((s) => s.events);
  const incidents = useApp((s) => s.incidents);
  const queries = useApp((s) => s.queries);
  const blocked = queries.filter((q) => q.decision === "BLOCKED").length;
  const score = Math.max(12, 92 - blocked * 8 - incidents.length * 3);
  const status = score >= 80 ? "DEFENDED" : score >= 55 ? "WATCH" : "DEGRADED";
  const log = useApp((s) => s.log);

  const breakdown = [
    { k: "Policy engine", v: 96 },
    { k: "DP noise", v: 88 },
    { k: "Kill-chain", v: 74 },
    { k: "Budget health", v: 81 },
    { k: "SecAgg", v: 90 },
  ];

  return (
    <div>
      <PageHead
        kicker="Security posture"
        title="AEGIS posture + SENTINEL kill-chain"
        lead="Composite demonstration metric plus measured kill-chain from the research engine. Tiers are behavioural, never outcome-based."
      />
      <div className="grid gap-3 lg:grid-cols-2">
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Security posture</h3>
          <div className="mt-4 flex items-center gap-4">
            <svg width="88" height="88" viewBox="0 0 42 42">
              <circle cx="21" cy="21" r="15.9" fill="transparent" stroke="var(--color-border)" strokeWidth="5" />
              <circle
                cx="21"
                cy="21"
                r="15.9"
                fill="transparent"
                stroke="var(--color-ok)"
                strokeWidth="5"
                strokeDasharray={`${(score / 100) * 100} 100`}
                transform="rotate(-90 21 21)"
                strokeLinecap="round"
              />
            </svg>
            <div>
              <div className="num text-4xl">{score}</div>
              <div className="text-sm text-muted">
                out of 100 · <span className="text-ok">{status}</span>
              </div>
            </div>
          </div>
          <div className="mt-4 space-y-2">
            {breakdown.map((b) => (
              <div key={b.k}>
                <div className="flex justify-between text-xs text-muted">
                  <span>{b.k}</span>
                  <span>{b.v}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
                  <div className="h-full bg-accent-2" style={{ width: `${b.v}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Kill-chain stages</h3>
          <p className="mt-1 text-xs text-muted">
            Measured: {MEASURED.killChainAlerts} alerts / {MEASURED.killChainQueries} queries · max {MEASURED.maxStage}
          </p>
          <div className="mt-3 space-y-2">
            {STAGES.map((s, i) => {
              const reached = STAGES.indexOf(MEASURED.maxStage) >= i;
              return (
                <div
                  key={s}
                  className={cn(
                    "flex items-center justify-between rounded-lg border px-3 py-2 text-sm",
                    reached ? "border-danger/40 bg-danger/5" : "border-border",
                  )}
                >
                  <span>{s.replace("_", " ")}</span>
                  {reached ? <Tag tone="danger">reached</Tag> : <Tag>idle</Tag>}
                </div>
              );
            })}
          </div>
        </Card>
      </div>
      <Card className="mt-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Incident center</h3>
          <button
            className="text-xs text-accent"
            onClick={() => log("Threat sensor", "Synthetic high-risk pattern injected", "HIGH")}
          >
            Generate event
          </button>
        </div>
        <div className="mt-2 max-h-72 space-y-2 overflow-y-auto">
          {incidents.length === 0 ? (
            <p className="text-sm text-muted">No incidents yet — launch an attack in the Attack Lab or block a query.</p>
          ) : (
            incidents.map((e) => (
              <div key={e.id} className="flex flex-wrap gap-2 border-b border-border py-2 text-sm">
                <Tag tone="danger">{e.severity}</Tag>
                <b>{e.type}</b>
                <span className="text-muted">{e.detail}</span>
              </div>
            ))
          )}
        </div>
      </Card>
      <Card className="mt-4">
        <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Entity reputation (measured)</h3>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {MEASURED.entityReputation.map((e) => (
            <div key={e.id} className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm">
              <span>{e.name}</span>
              <Tag tone={e.tier === "normal" ? "ok" : e.tier === "elevated" ? "warn" : "danger"}>{e.tier}</Tag>
            </div>
          ))}
        </div>
      </Card>
      <p className="mt-3 text-[11px] text-muted">{events.length} audit/security events in this session.</p>
    </div>
  );
}
