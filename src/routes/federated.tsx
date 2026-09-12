import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Btn, Card, PageHead, Tag } from "@/components/ui/primitives";
import { ClientChart } from "@/components/charts/client-chart";
import { useChartColors } from "@/components/charts/theme";
import { ARCH_STAGES, MEASURED } from "@/lib/results";
import { useApp } from "@/lib/store";
import { cn, fmt } from "@/lib/utils";

export const Route = createFileRoute("/federated")({ component: Federated });

function Federated() {
  const entities = useApp((s) => s.entities);
  const epoch = useApp((s) => s.epoch);
  const run = useApp((s) => s.runFederatedRound);
  const [sel, setSel] = useState("train");
  const c = useChartColors();
  const stage = ARCH_STAGES.find((s) => s.id === sel) ?? ARCH_STAGES[1];
  const sweep = MEASURED.sweep.map((s) => ({ name: s.label, auc: s.auc, sigma: s.sigma }));

  return (
    <div>
      <PageHead
        kicker="Collaborative ML"
        title="Federated learning with DP-SGD"
        lead="Each entity trains locally. Only clipped, noised, optionally masked updates leave the silo."
        extra={<Btn variant="primary" onClick={run}>Run training round</Btn>}
      />
      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <div className="text-xs text-muted">Naïve AUC</div>
          <div className="num text-3xl">{fmt(MEASURED.naiveAuc)}</div>
        </Card>
        <Card>
          <div className="text-xs text-muted">FL (no DP)</div>
          <div className="num text-3xl text-accent-2">{fmt(MEASURED.flNoDpAuc)}</div>
        </Card>
        <Card>
          <div className="text-xs text-muted">FL + DP ε≈4</div>
          <div className="num text-3xl text-ok">{fmt(MEASURED.flDp4Auc)}</div>
        </Card>
      </div>

      <h2 className="mt-8 text-lg font-semibold">Architecture — click a stage</h2>
      <p className="text-sm text-muted">AEGIS-style inspectable pipeline.</p>
      <div className="mt-3 flex flex-col gap-2">
        {ARCH_STAGES.map((s, i) => (
          <button
            key={s.id}
            onClick={() => setSel(s.id)}
            className={cn(
              "arch-node flex items-start gap-3 rounded-xl border p-3 text-left",
              sel === s.id ? "active border-accent bg-accent/10" : "border-border bg-surface",
            )}
          >
            <div className="num w-8 text-accent">{i + 1}</div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold">{s.title}</span>
                <Tag tone={s.tag === "RISK" ? "danger" : "ok"}>{s.tag}</Tag>
              </div>
              {sel === s.id ? <p className="mt-1 text-sm text-muted">{s.desc}</p> : null}
            </div>
          </button>
        ))}
      </div>
      <p className="mt-2 text-xs text-muted">Selected: {stage.title}</p>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {entities.map((e) => (
          <Card key={e.id}>
            <div className="text-xs text-muted">{e.name}</div>
            <div className="num text-xl">{e.records.toLocaleString()}</div>
            <Tag tone={e.connected ? "ok" : "warn"}>{e.connected ? "connected" : "offline"}</Tag>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-2">
              <div className="h-full bg-accent" style={{ width: `${Math.min(100, (e.epochs / 40) * 100)}%` }} />
            </div>
            <div className="mt-1 text-[11px] text-muted">Epoch {e.epochs}</div>
          </Card>
        ))}
      </div>
      <Card className="mt-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Secure aggregator</h3>
          <Tag tone="ok">Global model v{(1 + epoch / 10).toFixed(1)}</Tag>
        </div>
        <p className="mt-2 text-sm text-muted">Raw records transferred: 0. Hyperparameters: clip C=1.5, FedProx μ=0.01, 15 rounds, lr=0.5.</p>
      </Card>
      <Card className="mt-4">
        <h3 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">ε sweep (measured ROC-AUC)</h3>
        <ClientChart>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={sweep}>
              <CartesianGrid stroke={c.grid} strokeDasharray="3 3" />
              <XAxis dataKey="name" stroke={c.muted} fontSize={11} />
              <YAxis domain={[0.585, 0.6]} stroke={c.muted} fontSize={11} />
              <Tooltip />
              <Line type="monotone" dataKey="auc" stroke={c.accent} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </ClientChart>
      </Card>
    </div>
  );
}
