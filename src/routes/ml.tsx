import { createFileRoute } from "@tanstack/react-router";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, PageHead } from "@/components/ui/primitives";
import { ClientChart } from "@/components/charts/client-chart";
import { useChartColors } from "@/components/charts/theme";
import { MEASURED } from "@/lib/results";

export const Route = createFileRoute("/ml")({ component: ML });

function ML() {
  const c = useChartColors();
  return (
    <div>
      <PageHead
        kicker="Machine learning"
        title="Insider-threat classifier laboratory"
        lead="The measurable task is binary classification of synthetic insider-threat risk. Logistic regression is the FL/DP backbone because it admits exact per-example gradients and is competitive with larger families on this weak, imbalanced signal."
      />
      <div className="grid gap-3 lg:grid-cols-2">
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Task</h3>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-muted">
            <li>Target: insider_threat (positive rate ~4.06%)</li>
            <li>Features: 18 behavioural / operational attributes (auth timing, access breadth, volume, privilege…)</li>
            <li>Split: 24k train / 8k test, no leakage of campaign_id or synthetic_id</li>
            <li>Metrics: ROC-AUC (primary), PR-AUC, F1</li>
            <li>FL: FedProx, 15 rounds, 5 clients, non-IID</li>
            <li>DP-SGD: per-example clip 1.5 + Gaussian noise, RDP accountant, δ=1e-5, no subsampling amplification claimed</li>
          </ul>
        </Card>
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Why logistic regression</h3>
          <p className="mt-2 text-sm text-muted">
            Extra capacity (RF / HGB / MLP) overfits the minority class. MLP falls below chance (0.492). LR is not a
            convenience sacrifice — it is the best of the five families here and enables closed-form gradient inversion experiments.
          </p>
        </Card>
      </div>
      <Card className="mt-4">
        <h3 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">Centralized model comparison (naïve pooled data)</h3>
        <ClientChart>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={MEASURED.models}>
              <CartesianGrid stroke={c.grid} strokeDasharray="3 3" />
              <XAxis dataKey="name" stroke={c.muted} fontSize={10} interval={0} />
              <YAxis stroke={c.muted} fontSize={11} />
              <Tooltip />
              <Bar dataKey="roc" name="ROC-AUC" fill={c.accent2} />
              <Bar dataKey="pr" name="PR-AUC" fill={c.accent} />
            </BarChart>
          </ResponsiveContainer>
        </ClientChart>
      </Card>
      <Card className="mt-4">
        <h3 className="text-xs font-bold tracking-wide text-muted uppercase">MI attack sanity (overfit control)</h3>
        <p className="mt-2 text-sm text-muted">
          The attack implementation is capable of detecting membership when n_train is small. Near-random AUC on the
          full 24k model is therefore genuine generalization, not a broken attack.
        </p>
        <table className="mt-3 w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-muted">
              <th className="py-2">n_train</th>
              <th>Test ROC-AUC</th>
              <th>MI AUC</th>
            </tr>
          </thead>
          <tbody>
            {MEASURED.miByN.map((r) => (
              <tr key={r.n} className="border-t border-border">
                <td className="py-2">{r.n.toLocaleString()}</td>
                <td>{r.test.toFixed(3)}</td>
                <td>{r.mi.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
