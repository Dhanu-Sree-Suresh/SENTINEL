import { createFileRoute, Link } from "@tanstack/react-router";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
  Bar,
} from "recharts";
import { Card, Kicker, Tag } from "@/components/ui/primitives";
import { ClientChart } from "@/components/charts/client-chart";
import { useChartColors } from "@/components/charts/theme";
import { MEASURED } from "@/lib/results";
import { useApp } from "@/lib/store";
import { fmt } from "@/lib/utils";

export const Route = createFileRoute("/")({ component: Dashboard });

function Dashboard() {
  const c = useChartColors();
  const queries = useApp((s) => s.queries);
  const entities = useApp((s) => s.entities);
  const events = useApp((s) => s.events);
  const last = queries[queries.length - 1];
  const allowed = queries.filter((q) => q.decision === "ALLOWED").length;
  const blocked = queries.filter((q) => q.decision === "BLOCKED").length;
  const connected = entities.filter((e) => e.connected).length;

  const sweep = MEASURED.sweep.map((s) => ({
    name: s.label,
    auc: Number((s.auc * 100).toFixed(2)),
    eps: s.eps ?? 64,
  }));
  const models = MEASURED.models.map((m) => ({ name: m.name.replace("Hist. ", "HGB "), roc: m.roc }));
  const poison = MEASURED.poisoning.map((p) => ({
    attack: p.attack,
    mean: p.mean,
    median: p.median,
    trim: p.trim,
  }));

  return (
    <div>
      <div className="mb-5">
        <Kicker>Government privacy operations</Kicker>
        <h1 className="mt-1 max-w-3xl text-3xl font-semibold tracking-tight">
          Privacy-preserving analytics for sensitive government data.
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Five entities collaborate on an insider-threat classifier and population
          statistics without pooling raw records. Federated learning, DP-SGD, secure
          aggregation, a privacy kill-chain, and a live attack lab — one control plane.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link to="/console" className="inline-flex min-h-11 items-center rounded-lg bg-accent px-4 text-sm font-semibold text-white">
            Open analyst console
          </Link>
          <Link to="/attacklab" className="inline-flex min-h-11 items-center rounded-lg border border-border bg-surface-2 px-4 text-sm font-semibold">
            Run attack lab
          </Link>
          <Link to="/guided" className="inline-flex min-h-11 items-center rounded-lg border border-border px-4 text-sm font-semibold">
            Guided demo
          </Link>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <div className="text-[11px] tracking-wide text-muted uppercase">Entities</div>
          <div className="num mt-1 text-3xl text-accent-2">{connected}</div>
          <p className="text-xs text-muted">Connected silos · {MEASURED.records.toLocaleString()} records</p>
        </Card>
        <Card>
          <div className="text-[11px] tracking-wide text-muted uppercase">Protected requests</div>
          <div className="num mt-1 text-3xl text-ok">{allowed}</div>
          <p className="text-xs text-muted">Policy-approved analytics</p>
        </Card>
        <Card>
          <div className="text-[11px] tracking-wide text-muted uppercase">Blocked</div>
          <div className="num mt-1 text-3xl text-danger">{blocked}</div>
          <p className="text-xs text-muted">Individual-level refusals</p>
        </Card>
        <Card>
          <div className="text-[11px] tracking-wide text-muted uppercase">Raw records shared</div>
          <div className="num mt-1 text-3xl text-ok">0</div>
          <p className="text-xs text-muted">Never in the private path</p>
        </Card>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Privacy posture · SOC</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            <Tag tone="ok">FL + DP-SGD</Tag>
            <Tag>ε ≈ 4 · δ = 1e-5</Tag>
            <Tag tone="ok">SecAgg on</Tag>
            <Tag tone="warn">Kill-chain armed</Tag>
          </div>
          <p className="mt-3 text-sm text-muted">
            {last
              ? `Last activity: “${last.q}” · ${last.decision}.`
              : "No analyst activity yet. Run a safe aggregate query to see the control plane respond."}
          </p>
        </Card>
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Entity reputation</h3>
          <div className="mt-2 space-y-1.5">
            {MEASURED.entityReputation.map((e) => (
              <div key={e.id} className="flex items-center justify-between text-sm">
                <span>{e.name}</span>
                <Tag
                  tone={
                    e.tier === "normal" ? "ok" : e.tier === "elevated" ? "warn" : "danger"
                  }
                >
                  {e.tier.replace("_", " ")}
                </Tag>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="mt-8">
        <Kicker>Evidence — measured experiment</Kicker>
        <h2 className="mt-1 text-xl font-semibold">Naïve vs private, attacks, ML, kill-chain</h2>
        <p className="mt-1 text-sm text-muted">
          All figures below are from the executed SENTINEL run (32k records, 5 entities, 3 seeds). Interactive — hover for values.
        </p>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <Card>
          <h3 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">Model utility vs ε</h3>
          <ClientChart>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={sweep}>
                <CartesianGrid stroke={c.grid} strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke={c.muted} fontSize={11} />
                <YAxis domain={[58, 60]} stroke={c.muted} fontSize={11} />
                <Tooltip contentStyle={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }} />
                <Line type="monotone" dataKey="auc" name="ROC-AUC ×100" stroke={c.accent} strokeWidth={2} dot />
              </LineChart>
            </ResponsiveContainer>
          </ClientChart>
          <p className="mt-1 text-xs text-muted">Naïve centralized {fmt(MEASURED.naiveAuc)} · FL+DP ε≈4 {fmt(MEASURED.flDp4Auc)}</p>
        </Card>
        <Card>
          <h3 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">Centralized model families</h3>
          <ClientChart>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={models}>
                <CartesianGrid stroke={c.grid} strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke={c.muted} fontSize={10} interval={0} />
                <YAxis domain={[0.45, 0.65]} stroke={c.muted} fontSize={11} />
                <Tooltip contentStyle={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }} />
                <Bar dataKey="roc" name="ROC-AUC" fill={c.accent2} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ClientChart>
          <p className="mt-1 text-xs text-muted">Logistic regression is competitive on this weak, imbalanced signal — and admits exact per-example gradients.</p>
        </Card>
        <Card>
          <h3 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">Gradient inversion</h3>
          <div className="mb-3 grid grid-cols-2 gap-2">
            <div>
              <div className="text-xs text-muted">Raw cosine</div>
              <div className="num text-2xl text-danger">1.000</div>
            </div>
            <div>
              <div className="text-xs text-muted">DP cosine</div>
              <div className="num text-2xl text-ok">{MEASURED.giDp.toFixed(4)}</div>
            </div>
          </div>
          <ClientChart>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={[{ name: "Raw", v: 1 }, { name: "DP-SGD", v: MEASURED.giDp }]}>
                <XAxis dataKey="name" stroke={c.muted} fontSize={11} />
                <YAxis stroke={c.muted} fontSize={11} />
                <Tooltip />
                <Bar dataKey="v" name="cosine similarity" fill={c.danger} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ClientChart>
        </Card>
        <Card>
          <h3 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">Poisoning defenses</h3>
          <ClientChart>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={poison}>
                <CartesianGrid stroke={c.grid} strokeDasharray="3 3" />
                <XAxis dataKey="attack" stroke={c.muted} fontSize={11} />
                <YAxis domain={[0.57, 0.6]} stroke={c.muted} fontSize={11} />
                <Legend />
                <Tooltip />
                <Bar dataKey="mean" fill={c.danger} />
                <Bar dataKey="median" fill={c.ok} />
                <Bar dataKey="trim" fill={c.accent2} />
              </BarChart>
            </ResponsiveContainer>
          </ClientChart>
        </Card>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-3">
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Membership inference AUC</h3>
          <table className="mt-2 w-full text-sm">
            <tbody>
              {[
                ["Naïve", MEASURED.miNaive],
                ["FL no DP", MEASURED.miFl],
                ["FL+DP ε4", MEASURED.miDp],
              ].map(([k, v]) => (
                <tr key={String(k)} className="border-b border-border">
                  <td className="py-2 text-muted">{k}</td>
                  <td className="num py-2 text-right">{fmt(Number(v))}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-muted">Honest: MI advantage is already limited on this task. Gradient inversion is the stronger empirical demo.</p>
        </Card>
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Kill-chain</h3>
          <div className="num mt-2 text-3xl">{MEASURED.killChainAlerts}</div>
          <p className="text-sm text-muted">
            alerts from {MEASURED.killChainQueries} probing queries. Max stage{" "}
            <span className="text-danger">{MEASURED.maxStage}</span>. {events.length} session events logged.
          </p>
        </Card>
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Collective intelligence</h3>
          <p className="mt-2 text-sm text-muted">
            Campaign-linked positives ranked at percentile {MEASURED.collectiveLocal.toFixed(3)} locally vs{" "}
            {MEASURED.collectiveFed.toFixed(3)} federated — collaboration surfaces a weak cross-entity signal without pooling rows.
          </p>
        </Card>
      </div>
    </div>
  );
}
