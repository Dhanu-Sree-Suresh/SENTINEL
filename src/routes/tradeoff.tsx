import { createFileRoute } from "@tanstack/react-router";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, PageHead } from "@/components/ui/primitives";
import { ClientChart } from "@/components/charts/client-chart";
import { useChartColors } from "@/components/charts/theme";
import { MEASURED } from "@/lib/results";
import { useApp } from "@/lib/store";

export const Route = createFileRoute("/tradeoff")({ component: Tradeoff });

function Tradeoff() {
  const eps = useApp((s) => s.eps);
  const setEps = useApp((s) => s.setEps);
  const c = useChartColors();
  const t = Math.min(1, eps / 8);
  const acc = Math.round(64 + 31 * Math.min(1, eps / 4));
  const attack = Math.round(8 + 50 * t);
  const prot = eps < 0.5 ? "MAXIMUM" : eps < 2 ? "STRONG" : eps < 6 ? "BALANCED" : "LIGHT";
  const noise = eps < 0.5 ? "HIGH" : eps < 2 ? "MODERATE" : "LOW";
  const data = MEASURED.sweep.map((s) => ({
    name: s.label,
    auc: s.auc,
    attack: s.eps == null ? 0.51 : 0.5 + 0.01 * Math.log2((s.eps || 0.5) + 0.1),
  }));

  return (
    <div>
      <PageHead
        kicker="Trade-off"
        title="Privacy protection vs utility"
        lead="Move ε. Smaller ε means stronger formal privacy and more noise. Do not treat any single value as universally secure."
      />
      <Card>
        <div className="flex justify-between text-sm">
          <span>Privacy budget ε</span>
          <b className="font-mono">{eps.toFixed(2)}</b>
        </div>
        <input
          type="range"
          min={0.1}
          max={16}
          step={0.1}
          value={eps}
          onChange={(e) => setEps(+e.target.value)}
          className="mt-2 w-full"
        />
        <div className="mt-4 grid gap-3 sm:grid-cols-4">
          <div>
            <div className="text-xs text-muted">Protection</div>
            <div className="num text-xl text-ok">{prot}</div>
          </div>
          <div>
            <div className="text-xs text-muted">Answer precision (illustrative)</div>
            <div className="num text-xl">{acc}%</div>
          </div>
          <div>
            <div className="text-xs text-muted">Noise</div>
            <div className="num text-xl text-warn">{noise}</div>
          </div>
          <div>
            <div className="text-xs text-muted">Modeled attack conf.</div>
            <div className="num text-xl text-danger">{attack}%</div>
          </div>
        </div>
      </Card>
      <Card className="mt-4">
        <h3 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">Measured FL ROC-AUC across ε</h3>
        <ClientChart>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={data}>
              <CartesianGrid stroke={c.grid} strokeDasharray="3 3" />
              <XAxis dataKey="name" stroke={c.muted} fontSize={11} />
              <YAxis domain={[0.48, 0.62]} stroke={c.muted} fontSize={11} />
              <Tooltip />
              <Line type="monotone" dataKey="auc" name="ROC-AUC" stroke={c.ok} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </ClientChart>
        <p className="mt-2 text-sm text-muted">
          Utility stays nearly flat on this task. The decisive privacy win is gradient inversion (cosine 1.0 → 0.0003),
          not a large MI gap.
        </p>
      </Card>
    </div>
  );
}
