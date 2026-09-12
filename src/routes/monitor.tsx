import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Pie, PieChart, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis } from "recharts";
import { Btn, Card, PageHead, Select, Tag } from "@/components/ui/primitives";
import { ClientChart } from "@/components/charts/client-chart";
import { useChartColors } from "@/components/charts/theme";
import { useApp } from "@/lib/store";

export const Route = createFileRoute("/monitor")({ component: Monitor });

const BRAIN = [
  { k: "Intent", v: "aggregate vs membership" },
  { k: "Risk fusion", v: "six signals → score" },
  { k: "Behavior", v: "session suspicion counter" },
  { k: "Privacy", v: "ε ledger + Laplace/Gaussian" },
  { k: "Policy", v: "deterministic allow/deny" },
  { k: "Copilot", v: "rule-based rationale" },
];

function Monitor() {
  const live = useApp((s) => s.live);
  const queries = useApp((s) => s.queries);
  const [filter, setFilter] = useState("All activity");
  const c = useChartColors();
  const [denied, setDenied] = useState(false);

  const filtered = useMemo(() => {
    if (filter === "Safe") return queries.filter((q) => q.risk === "LOW");
    if (filter === "High risk") return queries.filter((q) => q.risk === "HIGH");
    if (filter === "Blocked") return queries.filter((q) => q.decision === "BLOCKED");
    return queries;
  }, [filter, queries]);

  const donut = [
    { name: "Allowed", v: queries.filter((q) => q.decision === "ALLOWED").length || 1 },
    { name: "Blocked", v: queries.filter((q) => q.decision === "BLOCKED").length },
  ];

  return (
    <div>
      <PageHead
        kicker="Live monitor"
        title="AEGIS security brain"
        lead="Real-time, privacy-preserving telemetry. User content never enters the developer-queryable store."
      />
      <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {BRAIN.map((b) => (
          <Card key={b.k} className="p-3">
            <div className="text-[11px] font-bold text-accent">{b.k}</div>
            <div className="mt-1 text-xs text-muted">{b.v}</div>
          </Card>
        ))}
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Telemetry stream</h3>
          <div className="mt-2 max-h-72 space-y-2 overflow-y-auto font-mono text-[11px]">
            {live.length === 0 ? <p className="text-muted">Waiting for heartbeat…</p> : null}
            {live.map((e) => (
              <div key={e.id} className="flex gap-2 border-b border-border py-1">
                <Tag tone={e.severity === "HIGH" ? "danger" : e.severity === "MEDIUM" ? "warn" : "ok"}>
                  {e.severity}
                </Tag>
                <span className="text-muted">{new Date(e.ts).toLocaleTimeString()}</span>
                <span>
                  {e.type}: {e.detail}
                </span>
              </div>
            ))}
          </div>
        </Card>
        <Card>
          <h3 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">Threat mix</h3>
          <ClientChart height={200}>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={donut} dataKey="v" nameKey="name" innerRadius={48} outerRadius={72}>
                  <Cell fill={c.ok} />
                  <Cell fill={c.danger} />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </ClientChart>
          <ClientChart height={160}>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart
                data={[
                  { n: "LOW", v: queries.filter((q) => q.risk === "LOW").length },
                  { n: "MED", v: queries.filter((q) => q.risk === "MEDIUM").length },
                  { n: "HIGH", v: queries.filter((q) => q.risk === "HIGH").length },
                ]}
              >
                <XAxis dataKey="n" stroke={c.muted} fontSize={11} />
                <YAxis stroke={c.muted} fontSize={11} allowDecimals={false} />
                <Bar dataKey="v" fill={c.accent2} />
              </BarChart>
            </ResponsiveContainer>
          </ClientChart>
        </Card>
      </div>

      <Card className="mt-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Query activity</h3>
          <Select value={filter} onChange={(e) => setFilter(e.target.value)} className="max-w-48">
            {["All activity", "Safe", "High risk", "Blocked"].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </Select>
        </div>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] text-muted">
                <th className="py-2">Time</th>
                <th>Actor</th>
                <th>Decision</th>
                <th>Request</th>
                <th>Risk</th>
              </tr>
            </thead>
            <tbody>
              {filtered
                .slice()
                .reverse()
                .slice(0, 20)
                .map((q) => (
                  <tr key={q.id} className="border-t border-border">
                    <td className="py-2">{new Date(q.ts).toLocaleTimeString()}</td>
                    <td>{q.actor}</td>
                    <td className={q.decision === "BLOCKED" ? "text-danger" : "text-ok"}>{q.decision}</td>
                    <td className="max-w-[280px] truncate">{q.q}</td>
                    <td>{q.risk}</td>
                  </tr>
                ))}
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-4 text-muted">
                    No matching activity. Use the Analyst Console to generate traffic.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="mt-4">
        <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Developer privacy boundary</h3>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-danger/30 bg-danger/5 p-3 text-xs text-muted">
            USER CONTENT — redacted; never written to developer telemetry.
          </div>
          <div className="rounded-lg border border-ok/30 bg-ok/5 p-3 font-mono text-xs">
            Attack type: session-scoped · see Attack Lab
            <br />
            Risk / action: policy-gated
          </div>
        </div>
        <Btn variant="danger" className="mt-3" onClick={() => setDenied(true)}>
          Attempt to access raw user content
        </Btn>
        {denied ? (
          <p className="mt-2 text-sm text-danger">
            ACCESS DENIED — privacy boundary prevents raw user content from entering developer telemetry, by construction.
          </p>
        ) : null}
      </Card>
    </div>
  );
}
