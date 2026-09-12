import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Card, PageHead, Tag } from "@/components/ui/primitives";
import { ARCH_STAGES, MEASURED } from "@/lib/results";
import { useApp } from "@/lib/store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/overview")({ component: Overview });

function Overview() {
  const [sel, setSel] = useState(ARCH_STAGES[0].id);
  const stage = ARCH_STAGES.find((s) => s.id === sel)!;
  const entities = useApp((s) => s.entities);
  const queries = useApp((s) => s.queries);
  const blocked = queries.filter((q) => q.decision === "BLOCKED").length;
  const threat = blocked >= 5 ? "CRITICAL" : blocked >= 2 ? "ELEVATED" : "LOW";

  return (
    <div>
      <PageHead
        kicker="System"
        title="Multi-entity privacy architecture"
        lead="Raw personal records never leave their silo. Click a stage to inspect the control boundary."
      />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <div className="text-xs text-muted">Connected custodians</div>
          <div className="num text-3xl">{entities.filter((e) => e.connected).length}</div>
        </Card>
        <Card>
          <div className="text-xs text-muted">Raw records shared</div>
          <div className="num text-3xl text-ok">0</div>
        </Card>
        <Card>
          <div className="text-xs text-muted">Privacy engine</div>
          <div className="num text-2xl">ACTIVE</div>
        </Card>
        <Card>
          <div className="text-xs text-muted">Threat level</div>
          <div className={cn("num text-2xl", threat === "LOW" ? "text-ok" : "text-warn")}>{threat}</div>
        </Card>
      </div>
      <div className="mt-6 flex flex-wrap gap-2">
        {ARCH_STAGES.map((s, i) => (
          <button
            key={s.id}
            onClick={() => setSel(s.id)}
            className={cn(
              "arch-node min-h-11 rounded-lg border px-3 py-2 text-left text-sm",
              sel === s.id ? "active border-accent bg-accent/10" : "border-border bg-surface",
            )}
          >
            <div className="text-[10px] text-muted">{String(i + 1).padStart(2, "0")}</div>
            <div className="font-semibold">{s.title}</div>
          </button>
        ))}
      </div>
      <Card className="mt-4">
        <Tag tone="accent">{stage.tag}</Tag>
        <h3 className="mt-2 text-lg font-semibold">{stage.title}</h3>
        <p className="mt-2 text-sm text-muted">{stage.desc}</p>
      </Card>
      <Card className="mt-4">
        <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Dataset (synthetic)</h3>
        <p className="mt-2 text-sm text-muted">
          {MEASURED.records.toLocaleString()} records across 5 non-IID government-style entities. Insider-threat
          positive rate ~4%. 18 features. Campaign_id is ground truth only — never a model feature. Missingness,
          outliers and 1% label noise injected. No real PII.
        </p>
      </Card>
    </div>
  );
}
