import { createFileRoute } from "@tanstack/react-router";
import { Btn, Card, PageHead, Tag } from "@/components/ui/primitives";
import { useApp } from "@/lib/store";

export const Route = createFileRoute("/audit")({ component: Audit });

function Audit() {
  const events = useApp((s) => s.events);
  const queries = useApp((s) => s.queries);
  const clear = useApp((s) => s.clearAudit);
  const rows = [
    ...events.map((e) => ({ ts: e.ts, type: e.type, severity: e.severity, detail: e.detail })),
    ...queries.map((x) => ({
      ts: x.ts,
      type: "Analytics request",
      severity: x.decision === "BLOCKED" ? "HIGH" : "INFO",
      detail: `${x.q} · ${x.reason}`,
    })),
  ]
    .sort((a, b) => b.ts - a.ts)
    .slice(0, 120);

  return (
    <div>
      <PageHead
        kicker="Provenance"
        title="Audit trail"
        lead="Budget draws, policy decisions, kill-chain transitions and aggregation events."
        extra={<Btn onClick={clear}>Clear session log</Btn>}
      />
      <Card>
        {rows.length === 0 ? (
          <p className="text-sm text-muted">No audit events yet.</p>
        ) : (
          rows.map((e, i) => (
            <div key={`${e.ts}-${i}`} className="flex flex-wrap gap-2 border-b border-border py-2 text-sm">
              <Tag tone={e.severity === "HIGH" ? "danger" : e.severity === "MEDIUM" ? "warn" : "ok"}>
                EVT-{1000 + i}
              </Tag>
              <b>{e.type}</b>
              <span className="text-muted">{e.detail}</span>
              <time className="ml-auto text-xs text-muted">{new Date(e.ts).toLocaleString()}</time>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}
