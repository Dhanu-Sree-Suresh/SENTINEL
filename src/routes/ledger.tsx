import { createFileRoute } from "@tanstack/react-router";
import { Btn, Card, PageHead, Tag } from "@/components/ui/primitives";
import { useApp } from "@/lib/store";

export const Route = createFileRoute("/ledger")({ component: Ledger });

function Ledger() {
  const entities = useApp((s) => s.entities);
  const spend = useApp((s) => s.spendBudget);
  const reset = useApp((s) => s.resetEpoch);
  const epoch = useApp((s) => s.epoch);

  return (
    <div>
      <PageHead
        kicker="Accounting"
        title="Privacy budget ledger"
        lead="Two streams: FL training (RDP) and analyst queries (simple composition). No silent reset. Exhaustion refuses further releases."
        extra={<Btn variant="primary" onClick={reset}>Start new epoch</Btn>}
      />
      <p className="mb-3 text-sm text-muted">Current training epoch {epoch}.</p>
      <div className="grid gap-3 lg:grid-cols-2">
        {entities.map((e) => (
          <Card key={e.id}>
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold">{e.name}</h3>
                <p className="text-xs text-muted">{e.records.toLocaleString()} records</p>
              </div>
              <Tag tone={e.connected ? "ok" : "warn"}>{e.connected ? "connected" : "offline"}</Tag>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <div>
                <div className="text-xs text-muted">Remaining ε</div>
                <div className="num text-2xl">{e.budget.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-xs text-muted">Epochs</div>
                <div className="num text-2xl">{e.epochs}</div>
              </div>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-2">
              <div className="h-full bg-accent" style={{ width: `${Math.min(100, (1 - e.budget / 8) * 100)}%` }} />
            </div>
            <Btn className="mt-3" onClick={() => spend(e.id)}>
              Run protected query (−0.20 ε)
            </Btn>
          </Card>
        ))}
      </div>
    </div>
  );
}
