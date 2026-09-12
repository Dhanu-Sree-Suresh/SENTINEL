import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Btn, Card, Field, Input, PageHead, Select, Tag } from "@/components/ui/primitives";
import { ClientChart } from "@/components/charts/client-chart";
import { useChartColors } from "@/components/charts/theme";
import {
  ATTACK_PAYLOADS,
  type AttackScenario,
  attackConfidence,
  measuredAnchor,
} from "@/lib/engine";
import { useApp } from "@/lib/store";
import { MEASURED } from "@/lib/results";
import { seeded } from "@/lib/utils";

export const Route = createFileRoute("/attacklab")({ component: AttackLab });

const SCENARIOS: AttackScenario[] = [
  "Membership inference",
  "Gradient inversion",
  "Differencing attack",
  "Rare subgroup reconstruction",
  "Repeated query attack",
  "Model poisoning",
];

const PIPE = ["ATTACK", "DETECT", "UNDERSTAND", "PREDICT", "DEFEND"];

function AttackLab() {
  const [scenario, setScenario] = useState<AttackScenario>("Membership inference");
  const [size, setSize] = useState(20);
  const [obs, setObs] = useState(6);
  const [signal, setSignal] = useState(50);
  const [mode, setMode] = useState<"naive" | "protected" | null>(null);
  const [step, setStep] = useState(0);
  const eps = useApp((s) => s.eps);
  const log = useApp((s) => s.log);
  const setLast = useApp((s) => s.setLastAttack);
  const c = useChartColors();

  const m = attackConfidence({ scenario, size, obs, signal, eps });
  const shown = mode === "naive" ? m.naive : mode === "protected" ? m.protected : null;

  function run(which: "naive" | "protected") {
    setMode(which);
    setStep(0);
    let i = 0;
    const t = setInterval(() => {
      i += 1;
      setStep(i);
      if (i >= PIPE.length) clearInterval(t);
    }, 280);
    setLast({ scenario, naive: m.naive, protected: m.protected });
    log(
      "Attack simulation",
      `${scenario} · ${which} · naïve ${m.naive}% · protected ${m.protected}%`,
      which === "naive" ? "HIGH" : "INFO",
    );
  }

  const dots = useMemo(() => {
    const rnd = seeded(size * 13 + obs * 17 + signal);
    const n = Math.min(80, Math.max(16, obs * 5));
    return Array.from({ length: n }, (_, i) => ({
      x: 4 + rnd() * 92,
      y: 8 + rnd() * 80,
      o: mode === "protected" ? 0.2 + rnd() * 0.25 : 0.45 + rnd() * 0.4,
    }));
  }, [size, obs, signal, mode]);

  return (
    <div>
      <PageHead
        kicker="Security"
        title="Attack lab"
        lead="Launch a controlled red-team scenario against naïve exact releases and the privacy-preserving path. Interactive confidence plus measured SENTINEL anchors."
        extra={<Tag tone={mode === "naive" ? "danger" : mode ? "ok" : "neutral"}>{mode ? mode : "ready"}</Tag>}
      />
      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Red team simulator</h3>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Field label="Scenario">
              <Select value={scenario} onChange={(e) => setScenario(e.target.value as AttackScenario)}>
                {SCENARIOS.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </Select>
            </Field>
            <Field label="Target population size">
              <Input type="number" min={2} value={size} onChange={(e) => setSize(+e.target.value || 2)} />
            </Field>
            <Field label="Observed query count">
              <Input type="number" min={1} value={obs} onChange={(e) => setObs(+e.target.value || 1)} />
            </Field>
            <Field label="Attack observation %">
              <Input type="number" min={0} max={100} value={signal} onChange={(e) => setSignal(+e.target.value || 0)} />
            </Field>
          </div>
          <pre className="mt-3 overflow-auto rounded-lg bg-surface-2 p-3 font-mono text-[11px] text-muted">
            {ATTACK_PAYLOADS[scenario]}
          </pre>
          <div className="mt-3 flex flex-wrap gap-2">
            <Btn variant="danger" onClick={() => run("naive")}>
              Launch naïve attack
            </Btn>
            <Btn variant="primary" onClick={() => run("protected")}>
              Launch protected attack
            </Btn>
            <Btn
              onClick={() => {
                setScenario(SCENARIOS[Math.floor(Math.random() * SCENARIOS.length)]);
                setSize(5 + Math.floor(Math.random() * 80));
                setObs(2 + Math.floor(Math.random() * 18));
                setSignal(5 + Math.floor(Math.random() * 95));
                setMode(null);
              }}
            >
              Random scenario
            </Btn>
          </div>
        </Card>
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Pipeline</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {PIPE.map((p, i) => (
              <Tag key={p} tone={step > i ? "ok" : "neutral"}>
                {p}
              </Tag>
            ))}
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div>
              <div className="text-xs text-muted">Naïve confidence</div>
              <div className="num text-3xl text-danger">{m.naive}%</div>
            </div>
            <div>
              <div className="text-xs text-muted">Protected confidence</div>
              <div className="num text-3xl text-ok">{m.protected}%</div>
            </div>
          </div>
          {shown != null ? (
            <p className="mt-2 text-sm text-muted">
              Last run ({mode}): {shown}% · reduction {m.gap} pp
            </p>
          ) : (
            <p className="mt-2 text-sm text-muted">Launch an attack to animate the pipeline.</p>
          )}
        </Card>
      </div>

      <Card className="mt-4">
        <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Observation field</h3>
        <div className="relative mt-2 h-56 overflow-hidden rounded-lg border border-border bg-surface-2">
          {dots.map((d, i) => (
            <i
              key={i}
              className="absolute size-2 rounded-full bg-accent"
              style={{ left: `${d.x}%`, top: `${d.y}%`, opacity: d.o }}
            />
          ))}
        </div>
      </Card>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <Card>
          <h3 className="mb-2 text-xs font-bold tracking-wide text-muted uppercase">Live battle (this configuration)</h3>
          <ClientChart>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={[{ name: "Naïve", v: m.naive }, { name: "Protected", v: m.protected }]}>
                <CartesianGrid stroke={c.grid} strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke={c.muted} />
                <YAxis domain={[0, 100]} stroke={c.muted} />
                <Tooltip />
                <Bar dataKey="v" name="attack confidence %" fill={c.accent} radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ClientChart>
        </Card>
        <Card>
          <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Measured research anchor</h3>
          <p className="mt-2 text-sm text-muted">{measuredAnchor(scenario)}</p>
          <p className="mt-3 text-xs text-muted">
            Gradient inversion cosine: raw 1.000 vs DP {MEASURED.giDp.toFixed(4)}. MI high-risk AUC naïve{" "}
            {MEASURED.miNaive.toFixed(3)} vs DP {MEASURED.miDp.toFixed(3)}.
          </p>
        </Card>
      </div>
    </div>
  );
}
